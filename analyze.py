'''
    Author: Aidan Jude
    The analysis layer: lock the finding, name the genres, emit results.json.

    Produces everything the visualization and README consume:
      1. Final emergent communities (k-NN + Louvain over description vectors),
         each with: members, top distinctive terms, held-out label agreement,
         a birth year, and an LLM-assigned genre name.
      2. The temporal timeline (genre count + mutation events per year).
      3. A robustness sweep over k to check the ~1890 acceleration isn't an
         artifact of one parameter.
      4. A curve fit: does the genre-mutation rate grow linearly or power-law?

    Env:  ANTHROPIC_API_KEY (for genre naming; skipped if unset)
    Run:  python analyze.py
    Out:  results.json
'''

import json
import os
import re
import urllib.request
from collections import Counter

import numpy as np

import temporal_network as tn
from semantic_edges import attach_embeddings

CLAUDE_MODEL = "claude-sonnet-4-6"
RESULTS = "results.json"


def load_corpus():
    path = os.path.join(tn.shelved_books, "books.json")
    books = json.load(open(path, encoding="utf-8"))["books"]
    for b in books:
        b["genres"] = set(b.get("genres") or [])
    attach_embeddings(books)
    return books


# --- final communities ------------------------------------------------------
def final_communities(books):
    G = tn.build_snapshot(books)
    comms = tn.detect_communities(G)
    by_title = {b["title"]: b for b in books}
    out = []
    for c in comms:
        members = [by_title[t] for t in c if t in by_title]
        if len(members) < 4:
            continue
        years = sorted(int(m["date_published"]) for m in members)
        labels = Counter(g for m in members for g in m["genres"]
                         if not g.startswith("Category:"))
        out.append({
            "members": members,
            "titles": [m["title"] for m in members],
            "size": len(members),
            "year_min": years[0], "year_max": years[-1],
            "birth_year": years[min(3, len(years) - 1)],   # year the 4th member appears
            "held_out_label": labels.most_common(1)[0][0] if labels else None,
        })
    return sorted(out, key=lambda d: d["birth_year"])


def top_terms(members, books):
    from sklearn.feature_extraction.text import TfidfVectorizer
    V = TfidfVectorizer(stop_words="english", max_features=20000,
                        min_df=3, max_df=0.4, sublinear_tf=True)
    X = V.fit_transform([b["description"] for b in books])
    terms = np.array(V.get_feature_names_out())
    idx = [i for i, b in enumerate(books) if b in members]
    centroid = np.asarray(X[idx].mean(axis=0)).ravel()
    return list(terms[np.argsort(-centroid)[:10]])


# --- LLM genre naming -------------------------------------------------------
def name_genre(sample_titles, terms):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    prompt = (f"These early novels cluster together by prose style/content.\n"
              f"Representative titles: {', '.join(sample_titles[:8])}\n"
              f"Distinctive vocabulary: {', '.join(terms)}\n"
              f"Name this literary genre/mode in 1-4 words (e.g. 'Detective fiction', "
              f"'Gothic romance', 'Nautical adventure'). Reply with ONLY the name.")
    body = {"model": CLAUDE_MODEL, "max_tokens": 30,
            "messages": [{"role": "user", "content": prompt}]}
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=json.dumps(body).encode(),
        headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"})
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=40).read())
        return r["content"][0]["text"].strip().strip('."')
    except Exception:                                # noqa: BLE001
        return None


# --- robustness + curve fit -------------------------------------------------
def timeline_for_k(books, k):
    orig = tn.EDGE_KNN
    tn.EDGE_KNN = k
    grouped = tn.books_by_year([_flat(b) for b in books])
    tl = tn.mutation_timeline(grouped)
    tn.EDGE_KNN = orig
    return tl


def _flat(b):
    return {"title": b["title"], "date_published": b["date_published"],
            "genres": list(b["genres"]), "description": b["description"]}


def fit_curves(years, cumulative):
    '''Fit cumulative genre count vs (year - y0). Return R^2 for linear & power.'''
    y = np.array(cumulative, float)
    t = np.array(years, float) - years[0] + 1
    def r2(pred):
        ss_res = np.sum((y - pred) ** 2)
        ss_tot = np.sum((y - y.mean()) ** 2)
        return 1 - ss_res / ss_tot if ss_tot else 0.0
    # linear
    a, b = np.polyfit(t, y, 1)
    lin = r2(a * t + b)
    # power law  y = c * t^p   (fit in log space)
    mask = y > 0
    p, logc = np.polyfit(np.log(t[mask]), np.log(y[mask]), 1)
    powr = r2(np.exp(logc) * t ** p)
    return {"linear_r2": round(lin, 3), "power_r2": round(powr, 3),
            "power_exponent": round(p, 2)}


def main():
    tn.EDGE_METHOD = "semantic"
    books = load_corpus()
    print(f"Corpus: {len(books)} canon novels")

    comms = final_communities(books)
    for c in comms:
        c["top_terms"] = top_terms(c["members"], books)
        sample = [m["title"] for m in sorted(c["members"],
                  key=lambda m: int(m["date_published"]))]
        c["genre_name"] = name_genre(sample, c["top_terms"])
        c.pop("members")
        print(f"  ~{c['birth_year']}  {c['genre_name'] or '?':22s} "
              f"[{c['size']:2d}]  <-> held-out: {c['held_out_label']}")

    # timeline at the default k, plus robustness sweep
    base_tl = timeline_for_k(books, 6)
    years = [r["year"] for r in base_tl]
    cum_genres, seen = [], 0
    for r in base_tl:
        seen = max(seen, r["n_communities"])
        cum_genres.append(seen)

    early = sum(r["mutations"] for r in base_tl if r["year"] < 1890)
    late = sum(r["mutations"] for r in base_tl if r["year"] >= 1890)
    print(f"\nMutations pre-1890: {early}  |  1890-1928: {late}")

    sweep = {}
    for k in (4, 6, 8, 10):
        tl = timeline_for_k(books, k)
        e = sum(r["mutations"] for r in tl if r["year"] < 1890)
        l = sum(r["mutations"] for r in tl if r["year"] >= 1890)
        sweep[k] = {"pre1890": e, "post1890": l,
                    "ratio_per_yr": round((l / 39) / max(e / 230, 1e-9), 2)}
        print(f"  k={k:2d}: pre-1890 {e:3d}, 1890+ {l:3d}  "
              f"(rate x{sweep[k]['ratio_per_yr']} after 1890)")

    fit = fit_curves(years, cum_genres)
    print(f"\nCurve fit (cumulative genres): linear R2={fit['linear_r2']}, "
          f"power R2={fit['power_r2']} (exponent {fit['power_exponent']})")

    json.dump({
        "n_books": len(books),
        "communities": comms,
        "timeline": base_tl,
        "cumulative_genres": list(zip(years, cum_genres)),
        "robustness_sweep": sweep,
        "curve_fit": fit,
    }, open(RESULTS, "w"), indent=2)
    print(f"\nWrote {RESULTS}")


if __name__ == "__main__":
    main()
