'''
    Author: Aidan Jude
    Phase 2, step 1: build a real, dated bibliography for the author-influence
    network, cross-referenced the same way build_canon.py cross-referenced the
    genre corpus (multiple source framings + two independent model families +
    a support score) - so no single source/model's opinion decides what's real.

    Two passes:
      1. WORKS   - for each of the ~17 PD-safe anchor authors (docs/PHASE2_
         INFLUENCE_NETWORK.md SS3/SS7.1), enumerate their own major works with
         real first-publication years.
      2. EXPAND  - for each anchor, enumerate real, historically-documented
         antecedent/successor authors (citeable fact: "X is documented as a
         direct influence on/of Y"), restricted to authors whose relevant work
         predates 1929 so the corpus pipeline stays PD-only (SS7.1). This grows
         the NODE set only - it never assigns an edge weight. The edge itself
         is measured later, from real prose (semantic_edges.py / the new
         conceptual-embedding step), never from this citation. Newly-discovered
         expansion authors get a WORKS pass too (one hop only - this is node
         discovery, not open-ended graph growth).

    The EXPAND pass's documented relationships are ALSO exactly the held-out
    validation set docs/PHASE2_INFLUENCE_NETWORK.md SS4 calls for ("a curated
    known-influences list... used only to check emergent edges after the
    fact"). They're written to a separate file for that reason and must never
    be merged back into the measured graph as edges.

    LLMs here only enumerate citeable list membership and verifiable facts
    (titles, years, documented influence relationships) - never write or
    originate the text analyzed, and never originate the influence CLAIM this
    project measures. See docs/PHASE2_INFLUENCE_NETWORK.md SS8.

    Env:  GEMINI_API_KEY, ANTHROPIC_API_KEY
    Run:  python build_bibliography.py
    Out:  _data/bibliography.json      -> [{title, author, year, support,
                                             models, n_lists, role}]
          _data/known_influences.json  -> [{from, to, support, models, notes}]
                                           VALIDATION ONLY - never build edges
                                           from this file.
'''

import json
import os
import re
import time
import urllib.request
from collections import defaultdict

from constants import shelved_books

BIBLIOGRAPHY_FILE = os.path.join(shelved_books, "bibliography.json")
INFLUENCES_FILE = os.path.join(shelved_books, "known_influences.json")
GEMINI_MODEL = "gemini-2.5-flash"
CLAUDE_MODEL = "claude-sonnet-4-6"

# The ~17 PD-safe seed authors identified in docs/PHASE2_INFLUENCE_NETWORK.md
# SS3 (§7.1 locks this in as the corpus-access strategy: PD-only for this
# phase). Joyce/Eliot are "early" only in the doc's framing - the year<1929
# filter below enforces that per-work rather than by author label.
ANCHORS = [
    "Herman Melville", "Plato", "Friedrich Nietzsche", "Marcus Aurelius",
    "Walt Whitman", "Thomas Paine", "John Muir", "Friedrich Hölderlin",
    "Ralph Waldo Emerson", "Percy Bysshe Shelley", "Homer", "G.W.F. Hegel",
    "Edgar Allan Poe", "Alexander Hamilton", "Numa Denis Fustel de Coulanges",
    "James Joyce", "T.S. Eliot",
]

WORKS_PROMPT = '''List the major, real works written by {author}.
Return ONLY a JSON array (no prose, no markdown fence) of objects with keys exactly:
  "title"  - canonical work title (no subtitle)
  "author" - author's full name, exactly "{author}"
  "year"   - integer year of FIRST publication/composition (original language).
             Use a NEGATIVE integer for BCE (e.g. -380 for 380 BCE).
Rules: only works first composed/published strictly BEFORE 1929 CE. Real,
verifiable works only - omit anything you are unsure of. Include philosophical,
poetic, and historical works, not only novels.'''

EXPAND_PROMPT = '''{author} is a node in a literary-influence network study.
List real, historically-documented authors in ONE of these two relations to {author}:
  - authors widely documented as a direct influence ON {author} (antecedents)
  - authors {author} is widely documented to have directly influenced (successors)
Return ONLY a JSON array (no prose, no markdown fence) of objects with keys exactly:
  "name"     - the other author's full name
  "relation" - exactly "antecedent" or "successor" (relative to {author})
  "note"     - one short citeable basis (a documented statement, dedication,
               biographical fact, or well-known critical consensus) - not your
               own opinion
Rules: only include authors whose relevant/most significant work was first
published strictly BEFORE 1929, so the resulting text is public domain. Real,
verifiable, well-documented relationships only - omit anything speculative.'''


def _extract_array(txt):
    m = re.search(r"\[.*\]", txt, re.DOTALL)
    return json.loads(m.group(0)) if m else []


def _gemini(prompt):
    key = os.environ["GEMINI_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={key}"
    body = {"contents": [{"parts": [{"text": "Use web search. " + prompt}]}],
            "tools": [{"google_search": {}}],
            "generationConfig": {"temperature": 0}}
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    for attempt in range(3):
        try:
            r = json.loads(urllib.request.urlopen(req, timeout=90).read())
            cand = r["candidates"][0]
            if "content" not in cand:
                return []
            return _extract_array(cand["content"]["parts"][0]["text"])
        except Exception:                            # noqa: BLE001
            time.sleep(2 * (attempt + 1))
    return []


def _claude(prompt):
    key = os.environ["ANTHROPIC_API_KEY"]
    body = {"model": CLAUDE_MODEL, "max_tokens": 3000,
            "messages": [{"role": "user", "content": prompt}]}
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=json.dumps(body).encode(),
        headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"})
    for attempt in range(3):
        try:
            r = json.loads(urllib.request.urlopen(req, timeout=90).read())
            return _extract_array(r["content"][0]["text"])
        except Exception:                            # noqa: BLE001
            time.sleep(2 * (attempt + 1))
    return []


PROVIDERS = [("gemini", _gemini), ("claude", _claude)]


def norm(title):
    t = re.sub(r"[^a-z0-9 ]", " ", title.lower())
    t = re.sub(r"^(the|a|an) ", "", t.strip())
    return re.sub(r"\s+", " ", t).strip()


def surname(author):
    a = author.replace(",", " ").split()
    return a[-1].lower() if a else ""


JUNK_NAME_TERMS = {"bible", "anonymous", "unknown", "various", "encyclopedia",
                   "the koran", "the quran", "the talmud", "folklore", "oral tradition"}


def looks_like_a_person(name):
    '''Filter modeling artifacts ("The Bible", "Anonymous") out of the node set.'''
    if norm(name) in JUNK_NAME_TERMS:
        return False
    return bool(re.match(r"^[A-Za-z.\-' ]+$", name.strip()))


def fetch_works(author, role, seen_titles):
    '''Cross-referenced (title, author, year) records for one author's own bibliography.'''
    records = []
    for pname, fn in PROVIDERS:
        t0 = time.time()
        print(f"    [{pname}] WORKS {author} ...", end="", flush=True)
        result = fn(WORKS_PROMPT.format(author=author))
        print(f" {len(result)} items ({time.time() - t0:.1f}s)", flush=True)
        for it in result:
            try:
                title, year = it["title"], int(it["year"])
            except (KeyError, ValueError, TypeError):
                continue
            if not title or not (-800 <= year < 1929):   # -800: covers Homer (~8th c. BCE)
                continue
            key = norm(title) + "|" + surname(author)
            rec = seen_titles[key]
            rec["title"] = rec["title"] or title.strip()
            rec["author"] = rec["author"] or author
            rec["years"].append(year)
            rec["models"].add(pname)
            rec["role"] = role
    return records  # unused return, seen_titles mutated in place; kept for clarity


def fetch_expansions(author, seen_expansions):
    '''Cross-referenced candidate antecedent/successor authors - node discovery only.'''
    for pname, fn in PROVIDERS:
        t0 = time.time()
        print(f"    [{pname}] EXPAND {author} ...", end="", flush=True)
        result = fn(EXPAND_PROMPT.format(author=author))
        print(f" {len(result)} items ({time.time() - t0:.1f}s)", flush=True)
        for it in result:
            name, relation, note = it.get("name"), it.get("relation"), it.get("note")
            if not name or relation not in ("antecedent", "successor"):
                continue
            if not looks_like_a_person(name):
                continue
            key = surname(name) + "|" + norm(name)
            rec = seen_expansions[key]
            rec["name"] = rec["name"] or name.strip()
            rec["models"].add(pname)
            rec["anchors"].add(author)
            direction = (author, name) if relation == "successor" else (name, author)
            rec["edges"].add(direction)
            rec["notes"].append(f"{author} <-> {name} ({relation}): {note}")


# Only candidates confirmed by BOTH models get a (expensive) one-hop works
# pass - cuts noise (single-model guesses, near-misses) and keeps runtime sane.
EXPANSION_SUPPORT_THRESHOLD = 2


def dump(works_by_title, expansions):
    '''Checkpoint - safe to call repeatedly, always leaves valid JSON on disk.'''
    bibliography = []
    for rec in works_by_title.values():
        if not rec["title"] or not rec["years"]:
            continue
        year = sorted(rec["years"])[len(rec["years"]) // 2]  # median of model-reported years
        bibliography.append({
            "title": rec["title"], "author": rec["author"], "year": year,
            "support": len(rec["models"]),
            "models": sorted(rec["models"]),
            "n_lists": 1,          # kept for build_corpus.py field compatibility
            "role": rec["role"],
        })
    bibliography.sort(key=lambda r: (r["author"], r["year"]))

    known_influences = []
    for rec in expansions.values():
        for frm, to in rec["edges"]:
            known_influences.append({
                "from": frm, "to": to,
                "support": len(rec["models"]),
                "models": sorted(rec["models"]),
                "notes": rec["notes"],
            })

    os.makedirs(shelved_books, exist_ok=True)
    tmp = BIBLIOGRAPHY_FILE + ".tmp"
    json.dump(bibliography, open(tmp, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    os.replace(tmp, BIBLIOGRAPHY_FILE)
    tmp = INFLUENCES_FILE + ".tmp"
    json.dump(known_influences, open(tmp, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    os.replace(tmp, INFLUENCES_FILE)
    return bibliography, known_influences


def main():
    works_by_title = defaultdict(lambda: {"title": None, "author": None,
                                          "years": [], "models": set(), "role": "anchor"})
    expansions = defaultdict(lambda: {"name": None, "models": set(),
                                      "anchors": set(), "edges": set(), "notes": []})

    for author in ANCHORS:
        before = len(works_by_title)
        fetch_works(author, "anchor", works_by_title)
        print(f"  anchor works: {author:30s} +{len(works_by_title) - before} titles")
        time.sleep(0.3)
    dump(works_by_title, expansions)
    print(f"  checkpoint: {len(works_by_title)} anchor works saved -> {BIBLIOGRAPHY_FILE}")

    for author in ANCHORS:
        fetch_expansions(author, expansions)
        time.sleep(0.3)
    dump(works_by_title, expansions)
    confirmed = [r for r in expansions.values()
                 if r["name"] and len(r["models"]) >= EXPANSION_SUPPORT_THRESHOLD]
    print(f"\nCandidate expansion authors: {len(expansions)} total, "
          f"{len(confirmed)} confirmed by both models (threshold={EXPANSION_SUPPORT_THRESHOLD}) "
          f"-> will get a one-hop works pass")

    # One-hop works pass, restricted to both-model-confirmed candidates only.
    for i, rec in enumerate(confirmed, 1):
        before = len(works_by_title)
        fetch_works(rec["name"], "expansion", works_by_title)
        added = len(works_by_title) - before
        if added:
            print(f"  expansion works: {rec['name']:30s} +{added} titles")
        if i % 10 == 0:
            dump(works_by_title, expansions)
            print(f"  checkpoint: {i}/{len(confirmed)} expansion authors processed")
        time.sleep(0.3)

    bibliography, known_influences = dump(works_by_title, expansions)
    anchors_n = sum(1 for r in bibliography if r["role"] == "anchor")
    expansion_n = sum(1 for r in bibliography if r["role"] == "expansion")
    print(f"\nBibliography: {len(bibliography)} works "
          f"({anchors_n} anchor, {expansion_n} expansion) -> {BIBLIOGRAPHY_FILE}")
    print(f"Known influences (VALIDATION ONLY, never edges): "
          f"{len(known_influences)} -> {INFLUENCES_FILE}")


if __name__ == "__main__":
    main()
