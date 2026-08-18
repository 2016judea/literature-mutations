'''
    Author: Aidan Jude
    S0, step 3: make the corpus checkable instead of trusted.

    _data/books.json holds ~20k words per book and is far too large to read in
    review. This writes the small thing that stands in for it - one row per
    book of (title, author, year, gutenberg_id, sha256 of the extracted text,
    word count) - so a later session can prove it is looking at the same
    corpus without re-fetching a line.

    It also measures EDITION DRIFT, which is the quiet way a reconstruction
    goes wrong. build_corpus.py takes ~20k words from whatever edition
    Gutendex matches TODAY; ids and transcriptions change. There is exactly
    one contemporaneous control available: _data/bibliography_books.json was
    fetched 2026-07-21 by this same build_corpus.py, days after the Phase 1
    run, and 29 of its books are also in the Phase 1 title list. Same code,
    same week, so any disagreement on those 29 is drift in Gutenberg rather
    than a difference in method.

    Run:  python corpus_manifest.py
    Out:  _data/corpus_manifest.json
'''

import hashlib
import json
import os

from constants import shelved_books

BOOKS = os.path.join(shelved_books, "books.json")
PHASE2 = os.path.join(shelved_books, "bibliography_books.json")
OUT = os.path.join(shelved_books, "corpus_manifest.json")
CANON = os.path.join(shelved_books, "canon.json")


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main():
    books = json.load(open(BOOKS, encoding="utf-8"))["books"]
    canon = {c["title"]: c for c in json.load(open(CANON, encoding="utf-8"))}

    rows = []
    for b in books:
        rows.append({
            "title": b["title"],
            "author": b["author"],
            "year": int(b["date_published"]),
            "gutenberg_id": b.get("gutenberg_id"),
            "sha256": sha(b["description"]),
            "words": len(b["description"].split()),
            "n_labels": len(b.get("genres") or []),
            "recon": canon.get(b["title"], {}).get("recon", {}),
        })
    rows.sort(key=lambda r: (r["year"], r["title"]))

    # --- edition drift against the contemporaneous Phase 2 fetch ---
    drift = {"compared": 0, "same_id_same_text": 0, "same_id_diff_text": 0,
             "diff_id": [], "text_changed": []}
    if os.path.isfile(PHASE2):
        p2 = {b["title"]: b for b in
              json.load(open(PHASE2, encoding="utf-8"))["books"]}
        by_title = {r["title"]: r for r in rows}
        text_now = {b["title"]: b["description"] for b in books}
        for t, old in p2.items():
            new = by_title.get(t)
            if not new:
                continue
            drift["compared"] += 1
            if old.get("gutenberg_id") != new["gutenberg_id"]:
                drift["diff_id"].append(
                    {"title": t, "then": old.get("gutenberg_id"),
                     "now": new["gutenberg_id"]})
                continue
            if sha(old["description"]) == new["sha256"]:
                drift["same_id_same_text"] += 1
            else:
                drift["same_id_diff_text"] += 1
                a, b_ = old["description"], text_now[t]
                drift["text_changed"].append(
                    {"title": t, "gutenberg_id": new["gutenberg_id"],
                     "words_then": len(a.split()), "words_now": len(b_.split()),
                     "shared_prefix_words": _prefix(a, b_)})

    out = {
        "n_books": len(rows),
        "n_authors": len({r["author"] for r in rows}),
        "year_min": rows[0]["year"] if rows else None,
        "year_max": rows[-1]["year"] if rows else None,
        "edition_drift_vs_phase2_2026_07_21": drift,
        "books": rows,
    }
    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1)
    print(f"{len(rows)} books / {out['n_authors']} authors, "
          f"{out['year_min']}-{out['year_max']}")
    print(f"Edition drift vs the 2026-07-21 Phase 2 fetch: "
          f"{drift['compared']} comparable, "
          f"{drift['same_id_same_text']} byte-identical, "
          f"{drift['same_id_diff_text']} same id but changed text, "
          f"{len(drift['diff_id'])} matched to a different Gutenberg id")
    for d in drift["diff_id"]:
        print(f"   id changed: {d['title'][:44]:44s} {d['then']} -> {d['now']}")
    for d in drift["text_changed"][:10]:
        print(f"   text changed: {d['title'][:40]:40s} "
              f"{d['words_then']} -> {d['words_now']} words, "
              f"shared prefix {d['shared_prefix_words']}")
    print(f"Wrote {OUT}")


def _prefix(a, b):
    aw, bw = a.split(), b.split()
    n = 0
    for x, y in zip(aw, bw):
        if x != y:
            break
        n += 1
    return n


if __name__ == "__main__":
    main()
