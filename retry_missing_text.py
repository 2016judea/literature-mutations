'''
    Author: Aidan Jude
    S0 addendum: recover the tail of books that matched but whose TEXT fetch
    failed.

    build_corpus.py conflates two very different failures into one silent
    skip. find_on_gutenberg() can fail to identify the book, or it can
    identify it correctly and then fetch_opening_prose() can come back empty.
    Both just drop the title.

    They are not the same problem. Checking the 27 titles missing after the
    first pass, 26 matched Gutendex perfectly - overlap 1.00, plain text
    available, surname present - and failed only on the download. The reason
    is in fetch_opening_prose: at CORPUS_WORDS = 20000 it sets read_bytes to
    None and pulls the WHOLE novel, and it tries each of the three mirrors
    with retries=1. One throttled response per mirror and the book is gone.

    So this is not a coverage limit, it is a politeness limit, and the fix is
    patience rather than a different source. Serial, one book at a time, with
    a real backoff, appending to the existing _data/books.json.

    Run:  python retry_missing_text.py [--rounds 8]
'''

import argparse
import json
import os
import time

import build_corpus as BC
from constants import shelved_books
from gutenberg_ingest import fetch_opening_prose

BOOKS = os.path.join(shelved_books, "books.json")
CANON = os.path.join(shelved_books, "canon.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, default=8)
    args = ap.parse_args()

    canon = {r["title"]: r for r in json.load(open(CANON, encoding="utf-8"))}
    data = json.load(open(BOOKS, encoding="utf-8"))
    have = {b["title"] for b in data["books"]}
    miss = sorted(set(canon) - have)
    print(f"{len(miss)} canon titles have no text yet")

    for t in miss:
        rec = canon[t]
        hit = BC.find_on_gutenberg(rec)
        if not hit:
            print(f"  {t[:42]:42s} NO GUTENDEX MATCH")
            continue
        bid, labels, text_url = hit
        prose = None
        for attempt in range(args.rounds):
            prose = fetch_opening_prose(bid, max_words=BC.CORPUS_WORDS,
                                        fallback_url=text_url)
            if prose:
                break
            time.sleep(min(2 ** attempt, 30))
        if not prose:
            print(f"  {t[:42]:42s} id={bid} TEXT FETCH FAILED")
            continue
        data["books"].append({
            "title": rec["title"], "author": rec["author"],
            "date_published": str(rec["year"]), "genres": labels,
            "description": prose, "gutenberg_id": bid,
            "source": "canon+gutenberg",
            "canon_support": rec.get("support"),
            "canon_lists": rec.get("n_lists"),
            "canon_models": rec.get("models"),
        })
        json.dump(data, open(BOOKS, "w", encoding="utf-8"),
                  indent=2, ensure_ascii=False)
        print(f"  {t[:42]:42s} id={bid} OK ({len(prose.split())} words)")

    print(f"corpus now {len(data['books'])} books")


if __name__ == "__main__":
    main()
