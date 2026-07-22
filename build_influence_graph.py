'''
    Author: Aidan Jude
    Phase 2, step 2: the directed author-influence graph itself.

    Node = author, aggregated across their own resolved corpus (not a single
    book - the author-voice confound from Phase 1's controls.py applies here
    even harder, docs/PHASE2_INFLUENCE_NETWORK.md SS4).

    Edge = candidate influence A -> B, permitted ONLY when A's earliest
    resolved work predates B's (real literary chronology, not personal
    reading order). Every candidate edge carries TWO independent similarity
    scores, never merged into one "influence score" (SS7.3):
      - stylistic  - TF-IDF cosine (word choice, syntax) - same tool as
        Phase 1's semantic_edges.py/controls.py, style-drift detrended the
        same way controls.py detrends genre vectors.
      - conceptual - embedding cosine (ideas/themes) - genuinely new; text
        that reads nothing alike at the word level can still be conceptually
        close. Uses Gemini's embedding API (consistent with this project's
        existing lightweight API-call style - no local ML dependency added).

    Form (poetry / prose fiction / philosophy) is classified once via a
    single LLM call enumerating a citeable, verifiable fact (an author's
    primary literary form) - NOT an influence claim - and is reported per
    edge as same-form/cross-form, never split into separate graphs or
    regressed out (SS7.3's fourth control, replacing Phase 1's evidence-tier
    confound).

    Validation (SS4): known_influences.json (377 documented antecedent/
    successor relationships, gathered in build_bibliography.py) is used
    ONLY here, to check whether documented real influence pairs show
    elevated similarity vs random pairs at the same chronological gap -
    a permutation z-test, same spirit as Phase 1's null-model discipline.
    It is never used to build or weight an edge.

    Env:  GEMINI_API_KEY
    Run:  python build_influence_graph.py
    In:   _data/bibliography_books.json, _data/known_influences.json
    Out:  _data/influence_graph.json
'''

import json
import os
import re
import socket
import time
import urllib.request

# Backstop: urllib's per-request timeout doesn't reliably bound DNS-resolution
# hangs on every platform. A global socket timeout catches that case too.
socket.setdefaulttimeout(45)
from collections import defaultdict

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from constants import shelved_books

BOOKS_FILE = os.path.join(shelved_books, "bibliography_books.json")
INFLUENCES_FILE = os.path.join(shelved_books, "known_influences.json")
OUT_FILE = os.path.join(shelved_books, "influence_graph.json")

DIGEST_WORDS_PER_BOOK = 250     # per-book excerpt length in the author digest
MAX_BOOKS_PER_AUTHOR = 6        # earliest N matched books, bounds prolific authors
GEMINI_EMBED_MODEL = "gemini-embedding-001"
CLAUDE_MODEL = "claude-sonnet-4-6"


def load_books():
    return json.load(open(BOOKS_FILE, encoding="utf-8"))["books"]


def surname(author):
    a = author.replace(",", " ").split()
    return a[-1].lower() if a else ""


def aggregate_authors(books):
    '''One digest + one earliest-year per author, built from up to
    MAX_BOOKS_PER_AUTHOR earliest resolved works. Bounds both the embedding
    API's input-length limit and any single prolific author's dominance.'''
    by_author = defaultdict(list)
    for b in books:
        try:
            year = int(b["date_published"])
        except (KeyError, ValueError):
            continue
        by_author[b["author"]].append((year, b["description"] or ""))

    authors = {}
    for author, works in by_author.items():
        works.sort(key=lambda w: w[0])
        chosen = works[:MAX_BOOKS_PER_AUTHOR]
        digest = " ".join(" ".join(text.split()[:DIGEST_WORDS_PER_BOOK])
                          for _, text in chosen)
        authors[author] = {
            "earliest_year": chosen[0][0],
            "n_books_total": len(works),
            "n_books_used": len(chosen),
            "digest": digest,
        }
    return authors


def _extract_array(txt):
    m = re.search(r"\[.*\]", txt, re.DOTALL)
    return json.loads(m.group(0)) if m else []


def classify_forms(author_names):
    '''One LLM call enumerating a citeable, verifiable fact (primary literary
    form) per author - not an influence claim. See module docstring.'''
    key = os.environ["ANTHROPIC_API_KEY"]
    names = sorted(author_names)
    prompt = (
        "For each author below, give their PRIMARY historical literary form.\n"
        "Return ONLY a JSON array (no prose, no markdown fence) of objects "
        'with keys exactly "author" and "form", where form is exactly one of: '
        '"poetry", "prose_fiction", "philosophy", "drama", "other".\n'
        "Authors:\n" + "\n".join(names)
    )
    body = {"model": CLAUDE_MODEL, "max_tokens": 4000,
            "messages": [{"role": "user", "content": prompt}]}
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=json.dumps(body).encode(),
        headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"})
    for attempt in range(3):
        try:
            r = json.loads(urllib.request.urlopen(req, timeout=60).read())
            items = _extract_array(r["content"][0]["text"])
            forms = {it["author"]: it["form"] for it in items
                     if it.get("author") in author_names}
            missing = author_names - forms.keys()
            for a in missing:
                forms[a] = "other"
            return forms
        except Exception:                            # noqa: BLE001
            time.sleep(2 * (attempt + 1))
    return {a: "other" for a in author_names}


def stylistic_similarity(digests, years):
    '''TF-IDF cosine, style-drift detrended (controls.py's technique - regress
    the linear year trend out before comparing, so era alone can't fake a
    similarity signal).'''
    V = TfidfVectorizer(stop_words="english", max_features=20000,
                        min_df=2, max_df=0.6, sublinear_tf=True)
    X = V.fit_transform(digests).toarray().astype(np.float64)
    yc = years - years.mean()
    denom = yc @ yc
    if denom > 0:
        beta = (X * yc[:, None]).sum(0) / denom
        X = X - np.outer(yc, beta)
    norms = np.clip(np.linalg.norm(X, axis=1, keepdims=True), 1e-9, None)
    X = X / norms
    return X @ X.T


def _gemini_embed_one(text):
    '''Single embedContent call - the Gemini embedding API's REST surface only
    exposes embedContent (sync, one input) and asyncBatchEmbedContent (a job
    API, overkill for 77 calls); verified live before wiring this in.'''
    key = os.environ["GEMINI_API_KEY"]
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{GEMINI_EMBED_MODEL}:embedContent?key={key}")
    body = {"model": f"models/{GEMINI_EMBED_MODEL}",
            "content": {"parts": [{"text": text[:6000]}]}}     # ~ token-limit guard
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    for attempt in range(3):
        try:
            r = json.loads(urllib.request.urlopen(req, timeout=30).read())
            return r["embedding"]["values"]
        except Exception:                            # noqa: BLE001
            time.sleep(2 * (attempt + 1))
    return None


EMBED_CACHE_FILE = os.path.join(shelved_books, "author_embeddings_cache.json")


def conceptual_similarity(names, digests):
    '''Embedding cosine - the cross-form-capable signal (SS7.3): two texts
    can be conceptually close while reading nothing alike at the word level.
    Checkpointed per-author (keyed by name) so a hung/killed run doesn't lose
    already-computed embeddings.'''
    cache = {}
    if os.path.isfile(EMBED_CACHE_FILE):
        cache = json.load(open(EMBED_CACHE_FILE, encoding="utf-8"))

    for i, (name, text) in enumerate(zip(names, digests), 1):
        if name not in cache:
            v = _gemini_embed_one(text)
            if v is None:
                raise RuntimeError(f"Gemini embedding failed for {name!r}")
            cache[name] = v
            if i % 10 == 0:
                json.dump(cache, open(EMBED_CACHE_FILE, "w", encoding="utf-8"))
        if i % 10 == 0 or i == len(names):
            print(f"  embedded {i}/{len(names)} authors", flush=True)
    json.dump(cache, open(EMBED_CACHE_FILE, "w", encoding="utf-8"))

    M = np.array([cache[n] for n in names], dtype=np.float64)
    norms = np.clip(np.linalg.norm(M, axis=1, keepdims=True), 1e-9, None)
    M = M / norms
    return M @ M.T


def build_directed_edges(names, years, forms, styl_sim, conc_sim):
    edges = []
    for i, a in enumerate(names):
        for j, b in enumerate(names):
            if i == j or years[i] >= years[j]:
                continue                              # chronology gate: A must predate B
            edges.append({
                "from": a, "to": b,
                "stylistic": round(float(styl_sim[i, j]), 4),
                "conceptual": round(float(conc_sim[i, j]), 4),
                "same_form": forms.get(a) == forms.get(b),
                "year_gap": int(years[j] - years[i]),
            })
    return edges


def permutation_z(real_pairs, all_names, name_idx, years, sim, trials=5000, rng=None):
    '''Do documented (from, to) pairs show elevated similarity vs random pairs
    respecting the same forward-chronology constraint? Never used to build
    edges - held-out validation only (module docstring / doc SS4).'''
    rng = rng or np.random.default_rng(0)
    real_vals = [sim[name_idx[a], name_idx[b]] for a, b in real_pairs]
    if not real_vals:
        return None
    real_mean = float(np.mean(real_vals))

    n = len(all_names)
    candidate_i, candidate_j = np.where(years[:, None] < years[None, :])
    if len(candidate_i) == 0:
        return None
    null_means = []
    for _ in range(trials):
        pick = rng.choice(len(candidate_i), size=len(real_vals), replace=True)
        null_means.append(sim[candidate_i[pick], candidate_j[pick]].mean())
    null_means = np.array(null_means)
    z = (real_mean - null_means.mean()) / (null_means.std() + 1e-12)
    return {"real_mean": round(real_mean, 4), "null_mean": round(float(null_means.mean()), 4),
            "null_std": round(float(null_means.std()), 4), "z": round(float(z), 3),
            "n_pairs": len(real_vals)}


def main():
    books = load_books()
    authors = aggregate_authors(books)
    names = sorted(authors.keys())
    years = np.array([authors[a]["earliest_year"] for a in names], dtype=np.float64)
    digests = [authors[a]["digest"] for a in names]
    print(f"{len(names)} authors, {len(books)} resolved works")

    forms = classify_forms(set(names))
    print(f"Form classification: {json.dumps({f: sum(1 for v in forms.values() if v==f) for f in set(forms.values())})}")

    styl_sim = stylistic_similarity(digests, years)
    print("Stylistic (TF-IDF) similarity matrix built")

    conc_sim = conceptual_similarity(names, digests)
    print("Conceptual (embedding) similarity matrix built")

    edges = build_directed_edges(names, years, forms, styl_sim, conc_sim)
    same_form_n = sum(1 for e in edges if e["same_form"])
    print(f"{len(edges)} directed candidate edges "
          f"({same_form_n} same-form, {len(edges)-same_form_n} cross-form)")

    signal_corr = float(np.corrcoef(
        [e["stylistic"] for e in edges], [e["conceptual"] for e in edges])[0, 1])
    print(f"Correlation between stylistic and conceptual signal across all edges: "
          f"{signal_corr:.3f}")

    name_idx = {a: i for i, a in enumerate(names)}
    known = json.load(open(INFLUENCES_FILE, encoding="utf-8")) if os.path.isfile(INFLUENCES_FILE) else []
    real_pairs = [(r["from"], r["to"]) for r in known
                  if r["from"] in name_idx and r["to"] in name_idx
                  and years[name_idx[r["from"]]] < years[name_idx[r["to"]]]]
    print(f"Held-out known_influences.json pairs resolvable in this graph: {len(real_pairs)}")

    rng = np.random.default_rng(0)
    styl_val = permutation_z(real_pairs, names, name_idx, years, styl_sim, rng=rng)
    rng = np.random.default_rng(0)
    conc_val = permutation_z(real_pairs, names, name_idx, years, conc_sim, rng=rng)
    print(f"Stylistic validation:  {styl_val}")
    print(f"Conceptual validation: {conc_val}")

    out = {
        "n_authors": len(names),
        "n_edges": len(edges),
        "signal_correlation": round(signal_corr, 3),
        "same_form_pct": round(100 * same_form_n / len(edges), 1) if edges else None,
        "authors": [{"name": a, "earliest_year": int(years[i]), "form": forms.get(a),
                    "n_books_used": authors[a]["n_books_used"],
                    "n_books_total": authors[a]["n_books_total"]}
                   for i, a in enumerate(names)],
        "edges": edges,
        "held_out_validation": {
            "n_known_pairs_in_graph": len(real_pairs),
            "stylistic": styl_val,
            "conceptual": conc_val,
        },
    }
    os.makedirs(shelved_books, exist_ok=True)
    json.dump(out, open(OUT_FILE, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"\nWrote {OUT_FILE}")


if __name__ == "__main__":
    main()
