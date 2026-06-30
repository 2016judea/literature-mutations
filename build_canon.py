'''
    Author: Aidan Jude
    Step 1 of the canon-first pipeline: assemble the corpus top-down, and make
    canonicity a CROSS-REFERENCED score rather than one model's opinion.

    The corpus is the pre-1929 public-domain English-language novel canon. To
    avoid trusting any single source, every candidate title is checked against:
      - many named lists + era/genre buckets (multi-list support), AND
      - two independent model families (Gemini, grounded in Google Search; and
        Claude) -> cross-model support.
    A title confirmed by several lists and both models is solidly canonical; a
    one-off is flagged with low support. (build_corpus adds a third, fully
    independent check: the book must actually exist on Project Gutenberg.)

    Grounded/LLM search only enumerates real, citeable list membership + verifiable
    facts (title/author/year). It never writes the text we cluster on.

    Env:  GEMINI_API_KEY, ANTHROPIC_API_KEY
    Run:  python build_canon.py
    Out:  _data/canon.json -> [{title, author, year, support, models, n_lists}]
'''

import json
import os
import re
import time
import urllib.request
from collections import Counter, defaultdict

from constants import shelved_books

CANON_FILE = os.path.join(shelved_books, "canon.json")
GEMINI_MODEL = "gemini-2.5-flash"
CLAUDE_MODEL = "claude-sonnet-4-6"

SOURCES = [
    "The Guardian's '100 best novels written in English' (pre-1929 entries)",
    "the Modern Library 100 Best Novels list (pre-1929 entries)",
    "'1001 Books You Must Read Before You Die' (pre-1929 English-language novels)",
    "canonical 18th-century English novels (Defoe, Swift, Richardson, Fielding, Sterne, Smollett, Burney, Radcliffe and peers)",
    "canonical English Romantic-era / early-19th-century novels (1800-1840)",
    "canonical Victorian novels (1837-1901)",
    "canonical late-Victorian and Edwardian English novels (1880-1914)",
    "canonical American novels first published before 1929",
    "foundational Gothic novels in English before 1929",
    "foundational detective and mystery novels in English before 1929",
    "foundational science-fiction novels in English before 1929",
    "foundational adventure and historical-romance novels in English before 1929",
    "canonical early-modernist English-language novels published 1900-1928",
    "the English-language novels that recurrently appear on 4chan /lit/'s 'top 100 books' and 'essential' canon charts (crowd-sourced literary canon)",
]

PROMPT = '''List the major, canonical works that match: {source}.
Return ONLY a JSON array (no prose, no markdown fence) of objects with keys exactly:
  "title"  - canonical book title (no subtitle)
  "author" - author's full name
  "year"   - integer year of FIRST publication in the original language
Rules: English-language novels only, first published strictly BEFORE 1929.
Real, verifiable books only - omit anything you are unsure of.'''


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


def norm(title):
    t = re.sub(r"[^a-z0-9 ]", " ", title.lower())
    t = re.sub(r"^(the|a|an) ", "", t.strip())
    return re.sub(r"\s+", " ", t).strip()


def surname(author):
    a = author.replace(",", " ").split()
    return a[-1].lower() if a else ""


def main():
    # key -> {title, author, years[], models set, lists set}
    canon = defaultdict(lambda: {"title": None, "author": None, "years": [],
                                 "models": set(), "lists": set()})
    providers = [("gemini", _gemini), ("claude", _claude)]

    for src in SOURCES:
        per_src = 0
        for pname, fn in providers:
            for it in fn(PROMPT.format(source=src)):
                try:
                    title, author, year = it["title"], it["author"], int(it["year"])
                except (KeyError, ValueError, TypeError):
                    continue
                if not title or not (1660 <= year < 1929):
                    continue
                key = norm(title) + "|" + surname(author)
                rec = canon[key]
                rec["title"] = rec["title"] or title.strip()
                rec["author"] = rec["author"] or author.strip()
                rec["years"].append(year)
                rec["models"].add(pname)
                rec["lists"].add(src)
                per_src += 1
        print(f"  {src[:54]:54s}  cumulative unique: {len(canon)}")
        time.sleep(0.3)

    records = []
    for rec in canon.values():
        year = Counter(rec["years"]).most_common(1)[0][0]   # consensus year
        records.append({
            "title": rec["title"], "author": rec["author"], "year": year,
            "support": len(rec["lists"]) + len(rec["models"]),  # lists + model agreement
            "models": sorted(rec["models"]),
            "n_lists": len(rec["lists"]),
        })
    records.sort(key=lambda r: (-r["support"], r["year"]))

    os.makedirs(shelved_books, exist_ok=True)
    with open(CANON_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    both = sum(1 for r in records if len(r["models"]) == 2)
    multi = sum(1 for r in records if r["n_lists"] >= 2)
    print(f"\nCanon: {len(records)} unique pre-1929 English novels -> {CANON_FILE}")
    print(f"  cross-model confirmed (both Gemini+Claude): {both}")
    print(f"  multi-list (>=2 sources):                   {multi}")
    per = Counter((r["year"] // 20) * 20 for r in records)
    print("  per 20yr:", {k: per[k] for k in sorted(per)})


if __name__ == "__main__":
    main()
