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

    Run:  python gutenberg_ingest.py --limit 150
    Out:  _data/books.json  in the schema temporal_network.py expects.
'''

import argparse
import json
import os
import re
import time
import urllib.parse
import urllib.request

from constants import shelved_books

GUTENDEX = "https://gutendex.com/books/"
OPENLIB = "https://openlibrary.org/search.json"
UA = {"User-Agent": "literature-mutations/1.0 (research; contact 2016judea)"}
TEXT_HEAD_BYTES = 40000     # how much of each book to fetch for the opening prose
DESC_WORDS = 1200           # words of real prose kept per book as the embedding text


def _get_json(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))


def text_plain_url(formats):
    for mime, url in formats.items():
        if mime.startswith("text/plain") and not url.endswith(".zip"):
            return url
    return None


def fetch_opening_prose(url):
    '''Stream just the head of a Gutenberg text and return ~DESC_WORDS of the
    real opening prose, with the boilerplate header stripped.'''
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read(TEXT_HEAD_BYTES).decode("utf-8", "ignore")
    except Exception:
        return None
    # Drop everything up to Gutenberg's "*** START OF ..." marker if present.
    m = re.search(r"\*\*\*\s*START OF.*?\*\*\*", raw, re.IGNORECASE | re.DOTALL)
    body = raw[m.end():] if m else raw
    words = body.split()
    return " ".join(words[:DESC_WORDS]).strip() or None


def publication_year(title, author, author_birth=None):
    '''Real first-publication year from Open Library.

    Open Library's data is messy: a single title carries reprint editions
    (which inflate the year) AND mis-dated junk records (which deflate it). So
    we pull many matching editions, sort oldest-first, and take the earliest
    year that is still plausible: at or after the author turned ~15. That floor
    kills the garbage early records without trusting a single noisy field.
    '''
    params = {"title": title, "fields": "first_publish_year",
              "limit": "20", "sort": "old"}
    if author:
        params["author"] = author
    floor = max((author_birth or 1385) + 15, 1400)
    try:
        d = _get_json(OPENLIB + "?" + urllib.parse.urlencode(params))
        years = [doc["first_publish_year"] for doc in (d.get("docs") or [])
                 if doc.get("first_publish_year")
                 and doc["first_publish_year"] >= floor]
        if years:
            return min(years)
    except Exception:
        pass
    return None


def harvest(limit):
    books = []
    seen = set()
    url = GUTENDEX + "?" + urllib.parse.urlencode(
        {"languages": "en", "topic": "fiction", "sort": "popular"})

    while url and len(books) < limit:
        page = _get_json(url)
        for b in page.get("results", []):
            if len(books) >= limit:
                break
            title = (b.get("title") or "").strip()
            authors = b.get("authors") or []
            author = authors[0]["name"] if authors else None
            txt_url = text_plain_url(b.get("formats") or {})
            if not title or not txt_url or title in seen:
                continue
            seen.add(title)

            # Open Library surname search is more reliable than "Last, First".
            surname = author.split(",")[0].strip() if author else None
            birth = authors[0].get("birth_year") if authors else None
            year = publication_year(title, surname, birth)
            if year is None and authors:
                # fall back to author's lifespan midpoint as a coarse anchor
                d0, d1 = authors[0].get("birth_year"), authors[0].get("death_year")
                if d0 and d1:
                    year = (d0 + d1) // 2
            if year is None:
                continue

            prose = fetch_opening_prose(txt_url)
            if not prose:
                continue

            books.append({
                "title": title,
                "author": author,
                "date_published": str(year),
                # held-out validation labels only - semantic edges never read these
                "genres": list(dict.fromkeys((b.get("bookshelves") or []) +
                                             (b.get("subjects") or [])))[:8],
                "description": prose,
                "gutenberg_id": b.get("id"),
                "source": "gutenberg+openlibrary",
            })
            print(f"  [{len(books):>4}/{limit}] {year}  {title[:60]}")
            time.sleep(0.25)   # be polite to Open Library

        url = page.get("next")

    return books


def main():
    ap = argparse.ArgumentParser(description="Build _data/books.json from Gutenberg + Open Library")
    ap.add_argument("--limit", type=int, default=150, help="number of books to harvest")
    args = ap.parse_args()

    print(f"Harvesting up to {args.limit} real books (Gutenberg text + Open Library dates)...")
    books = harvest(args.limit)

    os.makedirs(shelved_books, exist_ok=True)
    out = os.path.join(shelved_books, "books.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"books": books}, f, indent=2, ensure_ascii=False)

    years = sorted(int(b["date_published"]) for b in books)
    print(f"\nWrote {len(books)} books to {out}")
    if years:
        print(f"Year span: {years[0]} - {years[-1]}")
    print("Next: python temporal_network.py   (set EDGE_METHOD='semantic')")


if __name__ == "__main__":
    main()
