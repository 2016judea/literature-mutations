'''
    Author: Aidan Jude
    Step 2 of the canon-first pipeline: go FIND the books we chose.

    For each title in canon.json, search Project Gutenberg, confirm it's the
    right book (title + author match), and pull the real ~1000-word opening
    prose from a fast mirror. Publication year comes from the canon list (the
    grounded-search year we verified is accurate). Gutenberg subjects are kept
    only as held-out validation labels - never read by the semantic engine.

    Books not digitized on Gutenberg are skipped (logged) - that's an honest,
    visible gap, not silently-fabricated data.

    Run:  python build_corpus.py [--workers 8]
    In:   _data/canon.json
    Out:  _data/books.json   (schema temporal_network.py expects)
'''

import argparse
import json
import os
import re
import time
import urllib.parse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

from constants import shelved_books
from gutenberg_ingest import _http, fetch_opening_prose, text_plain_url

CANON_FILE = os.path.join(shelved_books, "canon.json")
BOOKS_FILE = os.path.join(shelved_books, "books.json")
GUTENDEX = "https://gutendex.com/books/"
CHECKPOINT_EVERY = 25
# Genre vocabulary saturates well before a novel ends; ~20k words (~first third)
# captures nearly all the TF-IDF signal at a fraction of full-novel storage.
CORPUS_WORDS = 20000


def norm(s):
    s = re.sub(r"[^a-z0-9 ]", " ", s.lower())
    s = re.sub(r"^(the|a|an) ", "", s.strip())
    return set(re.sub(r"\s+", " ", s).split())


def surname(author):
    a = author.replace(",", " ").split()
    return a[-1].lower() if a else ""


def find_on_gutenberg(rec):
    '''Return (gutenberg_id, subjects) for the best matching English text, or None.'''
    q = f"{rec['title']} {surname(rec['author'])}"
    url = GUTENDEX + "?" + urllib.parse.urlencode({"search": q, "languages": "en"})
    try:
        results = _http(url).get("results", [])
    except Exception:                                # noqa: BLE001
        return None
    want_title = norm(rec["title"])
    want_sur = surname(rec["author"])
    for b in results[:6]:
        if not text_plain_url(b.get("formats") or {}):
            continue
        got_title = norm(b.get("title", ""))
        overlap = len(want_title & got_title) / max(len(want_title), 1)
        authors_blob = " ".join(a.get("name", "") for a in (b.get("authors") or [])).lower()
        if overlap >= 0.5 and (want_sur in authors_blob or not want_sur):
            labels = list(dict.fromkeys((b.get("bookshelves") or []) +
                                        (b.get("subjects") or [])))[:8]
            return b["id"], labels
    return None


def resolve(rec):
    hit = find_on_gutenberg(rec)
    if not hit:
        return None
    book_id, labels = hit
    prose = fetch_opening_prose(book_id, max_words=CORPUS_WORDS)
    if not prose:
        return None
    return {
        "title": rec["title"],
        "author": rec["author"],
        "date_published": str(rec["year"]),
        "genres": labels,                # held-out validation only
        "description": prose,
        "gutenberg_id": book_id,
        "source": "canon+gutenberg",
        # cross-reference provenance, carried through for analysis thresholds
        "canon_support": rec.get("support"),
        "canon_lists": rec.get("n_lists"),
        "canon_models": rec.get("models"),
    }


def load_done():
    if not os.path.isfile(BOOKS_FILE):
        return [], set()
    books = json.load(open(BOOKS_FILE, encoding="utf-8")).get("books", [])
    return books, {b["title"] for b in books if b.get("source") == "canon+gutenberg"}


def save(books):
    tmp = BOOKS_FILE + ".tmp"
    json.dump({"books": books}, open(tmp, "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    os.replace(tmp, BOOKS_FILE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--fresh", action="store_true")
    args = ap.parse_args()

    canon = json.load(open(CANON_FILE, encoding="utf-8"))
    books, done = ([], set()) if args.fresh else load_done()
    todo = [r for r in canon if r["title"] not in done]
    print(f"Canon {len(canon)}; {len(done)} already matched; resolving {len(todo)}...")

    found = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(resolve, r): r for r in todo}
        for i, fut in enumerate(as_completed(futs), 1):
            try:
                r = fut.result()
            except Exception:                        # noqa: BLE001
                r = None
            if r:
                books.append(r)
                found += 1
            if i % CHECKPOINT_EVERY == 0:
                save(books)
                print(f"  {i}/{len(todo)} processed, {found} matched", end="\r")

    save(books)
    matched = [b for b in books if b.get("source") == "canon+gutenberg"]
    print(f"\nMatched {len(matched)}/{len(canon)} canon titles to Gutenberg text "
          f"-> {BOOKS_FILE}")
    per = Counter((int(b["date_published"]) // 20) * 20 for b in books)
    print("Per 20yr:", {k: per[k] for k in sorted(per)})


if __name__ == "__main__":
    main()
