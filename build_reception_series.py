'''
    Author: Aidan Jude
    S6 slice 3: the period reception series.

    Slices 1 and 2 were go/no-go probes. This builds. Brief:
    docs/S6-SLICE2-TRADE-CATALOGUE.md, and the decision recorded in
    docs/RESEARCH-PROGRAM.md under "The reception side is now the strong side".

    WHAT THIS MEASURES, AND WHY IT IS TWO SERIES NOT ONE

    The question S6 exists to answer is when the BOOK TRADE, at the time,
    started calling books by a genre name. Two measurements answer it and they
    fail differently, so both ship and neither is blended into the other:

      1. PER MILLION WORDS - every occurrence of a period genre term anywhere
         in the issue, over total OCR words. Parser-free. Cannot be biased by
         how well an entry parser works in one decade versus another, which is
         the one bias that would fake a formation event. This is the PRIMARY
         series and it is the same measurement slice 2 validated.

      2. PER ANNOTATION - occurrences inside the Weekly Record's descriptive
         line only. Publishers' Weekly states the policy in its own section
         masthead: "The annotations are descriptive, not critical; intended to
         PLACE not to judge the books." So an annotation is the trade press
         performing a classification, which a title or an advertisement is not.
         This is the sharper instrument and the novel contribution - and it
         depends on an extractor whose recall varies, so the annotation COUNT
         ships beside every rate and thin years are visible rather than hidden.

    Series 1 is safe and blunt; series 2 is sharp and needs its recall read.
    Reporting one without the other would be dishonest in opposite directions.

    THREE POSITIONS, KEPT APART

    A genre word can sit in an author's TITLE ("The Mystery of Orcival"), in a
    publisher's AD HEADING ("GABORIAU'S DETECTIVE STORIES"), or in the trade's
    ANNOTATION ("A mystery story, based on..."). These are three different
    speakers and only the last two are the trade. Slice 1's rule 3 generalised.

    SOURCES

      Publishers' Weekly              1872-1929   2,965 dated issues
      American Publishers' Circular   1852-1871     532 items
      and Literary Gazette

    Both on Internet Archive as free _djvu.txt - no lending restriction, no OCR
    cost. The splice exists because three of eleven terms are left-censored by
    PW's 1872 start, `sensation novel` (S2 take-off 1859) worst of all.

    Run:  python build_reception_series.py [--per-year 0] [--start 1852] [--end 1929]
          --per-year 0 means EVERY issue. The density is free; spend it.
    Out:  reception_series.json  - per-year series, both normalisations, the
                                   per-book table's summary, and coverage
          _data/reception_entries.jsonl.gz - the dated per-book table itself
'''

import argparse
import gzip
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor

from analyze_reception_clock import (first_attestation, mass_percentiles,
                                     smooth, takeoff_year)
from constants import shelved_books
from probe_trade_catalogue import (GENRE_TERMS, ISSUE_ID_RE, MARKERS, UA,
                                   WORD_RE, genre_acts)

OUT = "reception_series.json"
TABLE = os.path.join(shelved_books, "reception_entries.jsonl.gz")
# Cache lives under the user's home, NOT /tmp. This cache exists so a later
# session verifies rather than re-fetches - the discipline S0 and S2 both
# insisted on - and /tmp defeats exactly that: a 200MB sweep cache was cleared
# out from under a running full-density run on 2026-08-26 and the whole download
# had to be repeated. Override with TRADE_CACHE.
CACHE = os.environ.get("TRADE_CACHE",
                       os.path.expanduser("~/.cache/literature-mutations/ia_trade_text"))

# The two serials, in chronological order. The second is the splice.
SERIALS = [
    ("american-publishers-circular",
     "pub_american-literary-gazette-and-publishers-circular", 1852, 1871),
    ("publishers-weekly", "pub_publishers-weekly", 1872, 1929),
]

# --- entry / annotation extraction -----------------------------------------
# Built from the OCR, not guessed at. A Weekly Record entry runs:
#
#   Ehrmann, Max. A fearsome riddle; il. by Virginia Keep. Indianapolis, Ind.,
#   Bowen-Merrill Co., [1901.] c. 441092 p. D. cl., $1.
#   A mystery story, based on the theory of the arithmetical rhythm of time.
#
# so the annotation begins after the bibliographic tail (page count -> size
# letter -> binding -> price) and ends at the next entry head. OCR breaks words
# across lines ("arith- \nmetical"), which must be repaired BEFORE any regex
# runs or every tail spanning a line break is missed - the first version of
# this extractor found 0 annotations in three issues for exactly that reason.
DEHYPH_RE = re.compile(r"([A-Za-z])[-‐‑–]\s*\n\s*([a-z])")
# Digit run is generous on purpose: OCR fuses "4+1092 p." into "441092 p.",
# and a 5-digit bound silently dropped the single clearest annotation in the
# whole probe ("A mystery story, based on the theory of the arithmetical
# rhythm of time", PW 1901-10-05). Found by looking for a known row and not
# finding it - not by reading the regex.
PAGES_RE = re.compile(r"\b\d{1,7}\s*(?:[-+]\s*\d{1,7}\s*)?p\b\.?")
PRICE_RE = re.compile(r"\$\s?[\d.,]+|\b\d{1,3}\s*c\b\.?|\bnet\b|\bapply\b")
NEXT_HEAD_RE = re.compile(r"(?m)^\s{0,4}[A-Z][A-Za-z'’\-]{2,22},\s+[A-Z]")
# The next entry head where OCR did not give it a line of its own: a sentence
# end (or an asterisk, PW's "first book by this author" mark) then a surname.
MID_HEAD_RE = re.compile(r"[.!?]\s*\*?\s*[A-Z][A-Za-z'’\-]{2,22},\s+[A-Z]")
TAIL_WINDOW = 140          # chars after the page count to find a price
ANN_MAX = 400              # chars of annotation kept when no next head lands
# Leading debris an annotation must not start with: leftovers of the tail the
# price regex stopped inside of.
ANN_LEAD_RE = re.compile(r"^(?:[^A-Za-z]|net|apply|cl|pap|bds|lea|hf|c)\b[.,;\s]*",
                         re.I)
MIN_ANN_WORDS = 5

# The trade's own descriptive vocabulary, in PERIOD terms (S2's rule). Shared
# with the slice 2 probe so the two are directly comparable.
GENRE_LABELS = [lab for lab, _ in GENRE_TERMS]
GENRE_PATS = {lab: [re.compile(p, re.I) for p in pats] for lab, pats in GENRE_TERMS}


def normalise(text):
    '''Repair OCR line-break hyphenation. Newlines are KEPT - the entry head
    anchor is line-start, and collapsing them would destroy it.'''
    return DEHYPH_RE.sub(r"\1\2", text)


def annotations(text):
    '''The trade's descriptive lines. Returns list of (annotation, offset).

    Recall is imperfect and varies by era - PW's typography changes three times
    across the run. That is why every rate derived from this is reported beside
    its denominator, and why the parser-free per-million-words series is the
    primary one.

    Three precision rules, each from a defect found by driving it on real
    issues rather than reasoning about it:

      NON-OVERLAPPING. A single entry contains several page-count-like tokens
      ("5+228 p.", "(9 p.)"), so an unguarded scan emitted the SAME annotation
      two and three times and inflated the denominator. Matches before the end
      of the last accepted annotation are skipped.

      CUT AT THE NEXT ENTRY, NOT AT THE NEXT LINE-START ENTRY. OCR does not
      reliably put the next head at a line start - it can follow an asterisk or
      sit mid-line - and an annotation that runs into the following entry
      inherits that book's genre words. The cut is now sentence-end followed by
      a head-shaped name, anywhere.

      DEDUPE WITHIN AN ISSUE. Belt and braces on the first rule; a repeated
      annotation is always an artifact, never two books described identically.
    '''
    out, seen, cursor = [], set(), 0
    for m in PAGES_RE.finditer(text):
        if m.start() < cursor:
            continue                    # inside an entry already consumed
        seg = text[m.end():m.end() + TAIL_WINDOW]
        p = PRICE_RE.search(seg)
        if not p:
            continue
        start = m.end() + p.end()
        rest = text[start:start + 900]
        cut = len(rest[:ANN_MAX])
        for rx in (NEXT_HEAD_RE, MID_HEAD_RE):
            nh = rx.search(rest)
            if nh:
                cut = min(cut, nh.start())
        ann = re.sub(r"\s+", " ", rest[:cut]).strip(" .;,:*")
        ann = ANN_LEAD_RE.sub("", ann).strip(" .;,:*")
        if len(ann.split()) < MIN_ANN_WORDS or not ann[:1].isupper():
            continue                    # a mid-sentence fragment, not a line
        key = ann[:80].lower()
        if key in seen:
            continue
        seen.add(key)
        cursor = start + cut
        out.append((ann, start))
    return out


def genre_hits(s):
    '''{label: count} for one string.'''
    return {lab: sum(len(p.findall(s)) for p in GENRE_PATS[lab])
            for lab in GENRE_LABELS}


# --- fetch -----------------------------------------------------------------

def _get(url, retries=3, timeout=120):
    for attempt in range(retries):
        try:
            return urllib.request.urlopen(
                urllib.request.Request(url, headers=UA), timeout=timeout).read()
        except Exception:                              # noqa: BLE001
            if attempt == retries - 1:
                return None
            time.sleep(2 * (attempt + 1))
    return None


def issues_for_year(collection, year):
    params = {"q": f"collection:{collection} AND year:{year}",
              "fl[]": ["identifier", "date"], "rows": "400",
              "output": "json", "sort[]": "date asc"}
    raw = _get("https://archive.org/advancedsearch.php?"
               + urllib.parse.urlencode(params, doseq=True), timeout=90)
    if raw is None:
        return []
    out = []
    for d in json.loads(raw)["response"]["docs"]:
        m = ISSUE_ID_RE.search(d.get("identifier", ""))
        if m:
            out.append({"identifier": d["identifier"],
                        "date": f"{m.group(1)}-{m.group(2)}-{m.group(3)}"})
    out.sort(key=lambda d: d["date"])
    return out


def evenly_spaced(items, n):
    if not n or n >= len(items):
        return items
    step = len(items) / n
    return [items[int(i * step)] for i in range(n)]


def issue_text(identifier):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f"{identifier}.txt")
    if os.path.isfile(path):
        return open(path, encoding="utf-8", errors="ignore").read()
    raw = _get(f"https://archive.org/download/{identifier}/"
               f"{identifier}_djvu.txt")
    if raw is None:
        return None
    text = raw.decode("utf-8", "ignore")
    open(path, "w", encoding="utf-8").write(text)
    return text


# --- per-issue work --------------------------------------------------------

def scan_issue(item):
    raw = issue_text(item["identifier"])
    if raw is None:
        return {**item, "ok": False}
    text = normalise(raw)
    words = len(WORD_RE.findall(text))
    whole = genre_hits(text)

    anns = annotations(text)
    ann_hits = Counter()
    rows = []
    for ann, off in anns:
        h = genre_hits(ann)
        present = [lab for lab, n in h.items() if n]
        for lab in present:
            ann_hits[lab] += h[lab]
        if present:
            rows.append({"date": item["date"], "serial": item["serial"],
                         "issue": item["identifier"], "offset": off,
                         "genres": present, "annotation": ann[:400]})

    acts = genre_acts(text)
    register = {fam: sum(len(re.findall(p, text)) for p in pats)
                for fam, pats in MARKERS.items()}
    return {**item, "ok": True, "words": words, "whole": whole,
            "annotations": len(anns), "ann_hits": dict(ann_hits),
            "ann_rows": rows, "genre_acts": len(acts),
            "register_families": sum(1 for v in register.values() if v)}


# --- main ------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-year", type=int, default=0,
                    help="issues per year; 0 = every issue (default)")
    ap.add_argument("--start", type=int, default=1852)
    ap.add_argument("--end", type=int, default=1929)
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    # --- enumerate ---------------------------------------------------------
    jobs, coverage = [], {}
    for name, coll, lo, hi in SERIALS:
        years = [y for y in range(max(lo, args.start), min(hi, args.end) + 1)]
        if not years:
            continue
        print(f"Enumerating {name} {years[0]}-{years[-1]} ...", flush=True)
        with ThreadPoolExecutor(max_workers=8) as ex:
            found = dict(zip(years, ex.map(
                lambda y: issues_for_year(coll, y), years)))
        for y in years:
            coverage[y] = coverage.get(y, 0) + len(found[y])
            for it in evenly_spaced(found[y], args.per_year):
                jobs.append({**it, "year": y, "serial": name})
        print(f"  {sum(len(v) for v in found.values())} dated issues")

    print(f"\nScanning {len(jobs)} issues "
          f"({'every issue' if not args.per_year else f'{args.per_year}/yr'})",
          flush=True)

    results = []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for i, r in enumerate(ex.map(scan_issue, jobs), 1):
            results.append(r)
            if i % 100 == 0 or i == len(jobs):
                el = time.time() - t0
                print(f"  {i}/{len(jobs)}  {el / 60:.1f}m elapsed, "
                      f"~{el / i * (len(jobs) - i) / 60:.1f}m left", flush=True)

    ok = [r for r in results if r.get("ok")]
    misses = [r["identifier"] for r in results if not r.get("ok")]
    words = sum(r["words"] for r in ok)
    n_ann = sum(r["annotations"] for r in ok)
    print(f"\n{len(ok)} issues read, {words / 1e6:.1f}M words, "
          f"{n_ann:,} annotations extracted"
          f"{f', {len(misses)} misses' if misses else ''}")

    # --- the dated per-book table -----------------------------------------
    rows = [row for r in ok for row in r["ann_rows"]]
    rows.sort(key=lambda r: (r["date"], r["offset"]))
    os.makedirs(shelved_books, exist_ok=True)
    with gzip.open(TABLE, "wt", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    print(f"wrote {TABLE}  ({len(rows):,} genre-bearing annotations)")

    # --- per-year series, both normalisations ------------------------------
    years = sorted(set(r["year"] for r in ok))
    by_year = {}
    for y in years:
        rs = [r for r in ok if r["year"] == y]
        w = sum(r["words"] for r in rs)
        a = sum(r["annotations"] for r in rs)
        by_year[y] = {
            "issues": len(rs), "words": w, "annotations": a,
            "serial": rs[0]["serial"],
            "whole_raw": {lab: sum(r["whole"][lab] for r in rs)
                          for lab in GENRE_LABELS},
            "ann_raw": {lab: sum(r["ann_hits"].get(lab, 0) for r in rs)
                        for lab in GENRE_LABELS},
            "genre_acts": sum(r["genre_acts"] for r in rs),
        }
        by_year[y]["per_million"] = {
            lab: (by_year[y]["whole_raw"][lab] * 1e6 / w) if w else 0.0
            for lab in GENRE_LABELS}
        by_year[y]["per_1k_annotations"] = {
            lab: (by_year[y]["ann_raw"][lab] * 1e3 / a) if a else 0.0
            for lab in GENRE_LABELS}

    def clock(key):
        out = {}
        for lab in GENRE_LABELS:
            series = [by_year[y][key][lab] for y in years]
            sm = smooth(series)
            peak = max(sm) if sm else 0.0
            row = {"peak": peak,
                   "peak_year": years[sm.index(peak)] if peak > 0 else None,
                   "total": sum(by_year[y][
                       "whole_raw" if key == "per_million" else "ann_raw"][lab]
                       for y in years),
                   "first_attestation": first_attestation(
                       series, year_lo=years[0])}
            for frac in (0.05, 0.10, 0.20):
                i = takeoff_year(sm, peak, frac)
                row[f"takeoff_{int(frac * 100)}pct"] = (
                    years[0] + i if i is not None else None)
            p25, p50, p75, iqr = mass_percentiles(series, year_lo=years[0])
            row.update({"mass_p25": p25, "mass_p50": p50, "mass_p75": p75,
                        "mass_iqr": iqr})
            # longest run of zero years before the first nonzero - the shape
            # that separates a formation from a perennial mode
            lead = 0
            for v in series:
                if v > 0:
                    break
                lead += 1
            row["zero_years_before_first_hit"] = lead
            out[lab] = row
        return out

    clocks = {"per_million": clock("per_million"),
              "per_1k_annotations": clock("per_1k_annotations")}

    for key in clocks:
        print(f"\n=== {key} ===")
        print(f"{'term':20s} {'total':>7} {'peak':>8} {'pkyr':>5} "
              f"{'t/o5':>5} {'t/o10':>6} {'t/o20':>6} {'attest':>6} {'lead0':>6}")
        for lab in GENRE_LABELS:
            c = clocks[key][lab]
            print(f"{lab:20s} {c['total']:>7} {c['peak']:>8.2f} "
                  f"{str(c['peak_year']):>5} {str(c['takeoff_5pct']):>5} "
                  f"{str(c['takeoff_10pct']):>6} {str(c['takeoff_20pct']):>6} "
                  f"{str(c['first_attestation']):>6} "
                  f"{c['zero_years_before_first_hit']:>6}")

    payload = {
        "built": "S6 slice 3 - period reception series",
        "sources": [{"name": n, "collection": c, "window": [lo, hi]}
                    for n, c, lo, hi in SERIALS],
        "coverage_issues_available": {str(k): v for k, v in coverage.items()},
        "issues_scanned": len(ok), "issues_missed": misses,
        "words_ocr": words, "annotations_extracted": n_ann,
        "genre_bearing_annotations": len(rows),
        "table": TABLE,
        "by_year": {str(y): by_year[y] for y in years},
        "clocks": clocks,
        "estimator": {"imported_from": "analyze_reception_clock",
                      "smooth_years": 9, "persist_years": 10,
                      "thresholds": [0.05, 0.10, 0.20]},
        "caveats": [
            "per_million is parser-free and is the PRIMARY series.",
            "per_1k_annotations isolates the trade's own classificatory act "
            "but depends on an extractor whose recall varies by era; the "
            "annotation count per year ships beside it for exactly that "
            "reason.",
            "Fraction-of-peak take-off is biased late for any term still "
            "rising at the 1929 window edge - read peak_year first.",
            "Publishers' Weekly records AMERICAN publication. Any regression "
            "against the textual series is a US-side measurement.",
        ],
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1)
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
