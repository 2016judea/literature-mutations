'''
    Author: Aidan Jude
    Build _data/books.json from REAL data, replacing the dead Goodreads scrape.

    Sources (all free, alive, no API key):
      - Gutendex (gutendex.com): Project Gutenberg catalog -> title, author,
        subjects, bookshelves, and a plain-text download URL (real full text).
      - Open Library: real first-publication YEAR for each title.

    Principle: AI / labels never supply the ground truth here. We pull real
    opening prose (for semantic edges) and a real publication year (for the
    timeline). Subjects/bookshelves are stored ONLY as held-out validation
    labels - the semantic engine never reads them to form edges.

    Built to scale: candidate metadata is paged + cached once, then the slow
    per-book work (Open Library date + text fetch) runs across a thread pool
    with retries, and results are checkpointed to disk so a long harvest is
    resumable (re-run to pick up where it left off; --fresh to start over).

    Run:  python gutenberg_ingest.py --limit 3000 --workers 8
    Out:  _data/books.json  in the schema temporal_network.py expects.
'''

import argparse
import json
import os
import random
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

from constants import shelved_books

GUTENDEX = "https://gutendex.com/books/"
OPENLIB = "https://openlibrary.org/search.json"
UA = {"User-Agent": "literature-mutations/1.0 (research; contact 2016judea)"}
TEXT_HEAD_BYTES = 40000     # how much of each book to fetch for the opening prose
DESC_WORDS = 1200           # words of real prose kept per book as the embedding text

# www.gutenberg.org throttles bulk fetchers (and its /ebooks/<id>.txt.utf-8
# redirect hangs). These mirrors serve the same cache files ~10x faster.
TEXT_MIRRORS = [
    "https://gutenberg.pglaf.org/cache/epub/{id}/pg{id}.txt",
    "http://aleph.gutenberg.org/cache/epub/{id}/pg{id}.txt",
    "https://www.gutenberg.org/cache/epub/{id}/pg{id}.txt",
]

CACHE_DIR = os.path.join(shelved_books, "_cache")
CANDIDATES_FILE = os.path.join(CACHE_DIR, "candidates.json")
BOOKS_FILE = os.path.join(shelved_books, "books.json")
CHECKPOINT_EVERY = 50


# --- low-level HTTP with retry/backoff ---------------------------------------
def _http(url, want_json=True, read_bytes=None, retries=4):
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read() if read_bytes is None else r.read(read_bytes)
            if want_json:
                return json.loads(raw.decode("utf-8", "ignore"))
            return raw.decode("utf-8", "ignore")
        except Exception as e:                       # noqa: BLE001 - transient net
            last = e
            time.sleep(min(2 ** attempt, 8) + random.random())
    raise last


# --- 1. gather candidate metadata (paged, cached) ----------------------------
def text_plain_url(formats):
    for mime, url in formats.items():
        if mime.startswith("text/plain") and not url.endswith(".zip"):
            return url
    return None


def gather_candidates(target):
    '''Page Gutendex once for English fiction; keep books that have a usable
    text URL + author. Cached so re-runs skip the paging.'''
    if os.path.isfile(CANDIDATES_FILE):
        with open(CANDIDATES_FILE, encoding="utf-8") as f:
            cached = json.load(f)
        if len(cached) >= target:
            print(f"Using {len(cached)} cached candidates.")
            return cached[:target]

    cands = []
    url = GUTENDEX + "?" + urllib.parse.urlencode(
        {"languages": "en", "topic": "fiction", "sort": "popular"})
    while url and len(cands) < target:
        page = _http(url)
        for b in page.get("results", []):
            authors = b.get("authors") or []
            txt = text_plain_url(b.get("formats") or {})
            if not (b.get("title") and txt and authors):
                continue
            cands.append({
                "id": b["id"],
                "title": b["title"].strip(),
                "author": authors[0]["name"],
                "birth_year": authors[0].get("birth_year"),
                "text_url": txt,
                "labels": list(dict.fromkeys((b.get("bookshelves") or []) +
                                             (b.get("subjects") or [])))[:8],
            })
        url = page.get("next")
        print(f"  gathered {len(cands)} candidates...", end="\r")
    print(f"\nGathered {len(cands)} candidates.")
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(CANDIDATES_FILE, "w", encoding="utf-8") as f:
        json.dump(cands, f)
    return cands


# --- 2. resolve one candidate (date + prose), the slow parallel part ---------
def publication_year(title, author, author_birth):
    '''Earliest plausible first-publication year from Open Library.
    OL mixes late reprints with mis-dated junk, so take the oldest edition at
    or after the author turned ~15 - drops both failure modes.'''
    params = {"title": title, "author": author or "",
              "fields": "first_publish_year", "limit": "20", "sort": "old"}
    floor = max((author_birth or 1385) + 15, 1400)
    try:
        d = _http(OPENLIB + "?" + urllib.parse.urlencode(params))
        years = [doc["first_publish_year"] for doc in (d.get("docs") or [])
                 if doc.get("first_publish_year")
                 and doc["first_publish_year"] >= floor]
        if years:
            return min(years)
    except Exception:                                # noqa: BLE001
        pass
    return None


def fetch_opening_prose(book_id, max_words=DESC_WORDS):
    '''Pull real prose from the first mirror that responds, strip Gutenberg's
    header AND license footer, and return up to `max_words` of it.

    max_words=DESC_WORDS keeps the dense opening (fast, neural-friendly).
    max_words large (e.g. 20000) gives TF-IDF the fuller genre vocabulary;
    max_words=None returns the entire novel body.'''
    # A small head suffices for the opening; otherwise download the whole file.
    read_bytes = TEXT_HEAD_BYTES if (max_words and max_words <= DESC_WORDS) else None
    raw = None
    for tmpl in TEXT_MIRRORS:
        try:
            raw = _http(tmpl.format(id=book_id), want_json=False,
                        read_bytes=read_bytes, retries=1)
            break
        except Exception:                            # noqa: BLE001
            continue
    if not raw:
        return None
    # Strip Gutenberg boilerplate: everything before "*** START" and after "*** END".
    m = re.search(r"\*\*\*\s*START OF.*?\*\*\*", raw, re.IGNORECASE | re.DOTALL)
    body = raw[m.end():] if m else raw
    e = re.search(r"\*\*\*\s*END OF.*", body, re.IGNORECASE | re.DOTALL)
    if e:
        body = body[:e.start()]
    words = body.split()
    if max_words:
        words = words[:max_words]
    return " ".join(words).strip() or None


def resolve(c):
    surname = c["author"].split(",")[0].strip() if c["author"] else None
    year = publication_year(c["title"], surname, c["birth_year"])
    if year is None and c["birth_year"]:
        year = c["birth_year"] + 30   # coarse fallback anchor
    if year is None:
        return None
    prose = fetch_opening_prose(c["id"])
    if not prose:
        return None
    return {
        "title": c["title"],
        "author": c["author"],
        "date_published": str(year),
        "genres": c["labels"],          # held-out validation labels only
        "description": prose,
        "gutenberg_id": c["id"],
        "source": "gutenberg+openlibrary",
    }


# --- checkpointing -----------------------------------------------------------
def load_existing():
    if not os.path.isfile(BOOKS_FILE):
        return [], set()
    with open(BOOKS_FILE, encoding="utf-8") as f:
        books = json.load(f).get("books", [])
    return books, {b.get("gutenberg_id") for b in books}


def save(books):
    os.makedirs(shelved_books, exist_ok=True)
    tmp = BOOKS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"books": books}, f, indent=2, ensure_ascii=False)
    os.replace(tmp, BOOKS_FILE)


# --- driver ------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=3000)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--fresh", action="store_true", help="ignore prior books.json/cache")
    args = ap.parse_args()

    if args.fresh:
        for p in (BOOKS_FILE, CANDIDATES_FILE):
            if os.path.isfile(p):
                os.remove(p)

    candidates = gather_candidates(args.limit)
    books, done = load_existing()
    todo = [c for c in candidates if c["id"] not in done]
    print(f"{len(books)} already done, {len(todo)} to resolve "
          f"with {args.workers} workers...")

    start = time.time()
    completed = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(resolve, c): c for c in todo}
        for fut in as_completed(futs):
            completed += 1
            try:
                r = fut.result()
            except Exception:                        # noqa: BLE001
                r = None
            if r:
                books.append(r)
            if completed % CHECKPOINT_EVERY == 0:
                save(books)
                rate = completed / max(time.time() - start, 1)
                print(f"  resolved {completed}/{len(todo)}  kept {len(books)}  "
                      f"{rate:.1f}/s", end="\r")

    save(books)
    years = sorted(int(b["date_published"]) for b in books)
    print(f"\nDone. {len(books)} books in {BOOKS_FILE}")
    if years:
        import collections
        per = collections.Counter((y // 20) * 20 for y in years)
        print(f"Year span: {years[0]} - {years[-1]}")
        print("Per 20yr:", dict(sorted(per.items())))


if __name__ == "__main__":
    main()
