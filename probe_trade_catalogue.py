'''
    Author: Aidan Jude
    S6 slice 2: is the trade catalogue a cheaper reception source than the
    bound-in ad page?

    Slice 1 (docs/S6-SLICE1-BACKMATTER-PROBE.md) came back NO-GO on Gutenberg:
    4 of 343 books carry a publisher advertisement, because Gutenberg
    transcribers strip them. It closed by naming the next thing to price
    BEFORE committing to Internet Archive page-scan OCR:

        "publishers' trade circulars and The Publishers' Circular / The
        English Catalogue of Books were themselves printed serials, many
        already transcribed, and they carry the same series-and-genre headings
        in bulk rather than one novel at a time."

    This prices that claim. It is still a probe, not the dataset (RESEARCH-
    PROGRAM.md S6): the question is whether a dated, bulk, period-evidence
    reception series is REACHABLE and at what cost - not to build the series.

    Three things it is careful about, two inherited from slice 1:

    1. SEARCH THE REGISTER, NOT A STRING - and keep slice 1's five marker
       families as a LIVE-FIRE CONTROL. A genre count from a source that
       turns out not to be trade material is a measurement of nothing. If the
       trade register does not fire, the genre numbers are void.

    2. SEPARATE THE TWO ARTIFACTS UP FRONT. Slice 1's third handoff rule:
       "by the same author" lists are an AUTHOR artifact; "THE NEW MILITARY
       NOVEL" is a GENRE act. Only the second measures genre formation.

    3. PERIOD TERMS, NOT MODERN ONES (S2's rule, and its most expensive
       lesson). "Science fiction" is anachronistic before ~1930; the period
       word is "scientific romance". Reading a modern label back into a
       period source manufactures a fake late emergence.

    The estimator is IMPORTED from analyze_reception_clock, not reimplemented,
    so a take-off date measured here is directly comparable to S2's Ngrams
    take-off rather than merely similar to it.

    Run:  python probe_trade_catalogue.py [--per-year 4] [--start 1872] [--end 1929]
    Out:  trade_catalogue_probe.json   (per-year series, per-issue detail, verdict)
'''

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from analyze_reception_clock import (first_attestation, mass_percentiles,
                                     smooth, takeoff_year)
from probe_backmatter import MARKERS

OUT = "trade_catalogue_probe.json"
# Issues are 150-350KB of OCR each; cache so the detector can be re-run and
# argued with without re-downloading. Slice 1's cache did the same job.
CACHE = os.environ.get("TRADE_CACHE", "/tmp/ia_trade_text")
UA = {"User-Agent": "Mozilla/5.0 (literature-mutations research probe)"}

# The serial. Publishers' Weekly is the US book trade's weekly of record from
# 1872; IA holds it as free OCR text (no lending restriction, no OCR cost),
# one item per dated issue. Its British counterpart, The Publishers' Circular,
# is on IA as 24 items concentrated in 1853 - a run too thin to carry a series,
# which is measured in the coverage step below rather than assumed.
COLLECTION = "pub_publishers-weekly"
ISSUE_ID_RE = re.compile(r"_(\d{4})-(\d{2})-(\d{2})_")   # excludes _index items

# Genre vocabulary, in PERIOD terms. Each entry is (label, [patterns]).
# The eight communities from RESEARCH-PROGRAM.md, plus the two leads S2 handed
# forward: `sensation novel` (take-off 1859, hiding inside the perennial gothic
# cluster) and the detective/mystery pair that is the project's only positive.
GENRE_TERMS = [
    ("detective story", [r"detective (?:stor(?:y|ies)|novels?|tales?|fiction)"]),
    ("detective (any)", [r"\bdetectives?\b"]),
    ("mystery story", [r"mystery (?:stor(?:y|ies)|novels?)"]),
    ("sensation novel", [r"sensation(?:al)? (?:novels?|stor(?:y|ies)|fiction)"]),
    ("scientific romance", [r"scientific romances?"]),
    ("ghost story", [r"ghost stor(?:y|ies)"]),
    ("historical romance", [r"historical (?:romances?|novels?|fiction)"]),
    ("adventure story", [r"(?:stor(?:y|ies)|tales?|novels?) of adventure",
                         r"adventure stor(?:y|ies)"]),
    ("western story", [r"western stor(?:y|ies)", r"stor(?:y|ies) of the west"]),
    ("love story", [r"love stor(?:y|ies)"]),
    ("sea story", [r"sea stor(?:y|ies)", r"nautical (?:tales?|novels?)"]),
]

# A GENRE ACT is a publisher or the trade press putting a genre word in a
# HEADING - the dated marketing act S6 is after ("THE NEW MILITARY NOVEL",
# "CHEAP FICTION", "NEW LIBRARY OF STANDARD FICTION"). An AUTHOR ARTIFACT names
# an author's other titles and cannot speak to genre. Slice 1's rule 3; kept as
# two separate counters, never summed.
#
# Detected by heading SHAPE, not by a trailing keyword. An earlier version of
# this required the heading to end in SERIES/LIBRARY/NOVELS/STORIES and missed
# three of the five real examples in the positive control, including slice 1's
# best find - which is why the control runs before the corpus does.
GENRE_WORD_RE = re.compile(
    r"\b(?:DETECTIVE|MYSTERY|ROMANCE|ADVENTURE|WESTERN|SENSATION(?:AL)?"
    r"|FICTION|NOVELS?|TALES?|STORIES)\b")
CAPS_LINE_RE = re.compile(r"^[A-Z0-9][A-Z0-9' &.,\-!?]{5,64}$")
AUTHOR_ARTIFACT_RE = re.compile(
    r"BY THE SAME AUTHOR|By the same author|OTHER (?:WORKS|BOOKS) BY|WORKS BY")


def genre_acts(text):
    '''Heading-shaped lines carrying a genre word. A heading is a short line in
    full caps - the typographic form a publisher's ad heading and a trade
    journal's class heading both take, and one OCR preserves reliably.'''
    out = []
    for line in text.split("\n"):
        s = line.strip()
        if len(s) < 6 or not CAPS_LINE_RE.match(s):
            continue
        if AUTHOR_ARTIFACT_RE.search(s):
            continue                    # author artifact, not a genre act
        if GENRE_WORD_RE.search(s):
            out.append(s)
    return out

WORD_RE = re.compile(r"[A-Za-z']+")


# ---------------------------------------------------------------------------
# fetch
# ---------------------------------------------------------------------------

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


def issues_for_year(year):
    '''Every DATED issue item IA holds for one year, sorted by date. The
    volume `_index` items carry no advertisements and no Weekly Record, so
    they are excluded by identifier shape rather than by guesswork.'''
    params = {"q": f"collection:{COLLECTION} AND year:{year}",
              "fl[]": ["identifier", "date"], "rows": "200",
              "output": "json", "sort[]": "date asc"}
    url = "https://archive.org/advancedsearch.php?" + urllib.parse.urlencode(
        params, doseq=True)
    raw = _get(url, timeout=90)
    if raw is None:
        return []
    docs = json.loads(raw)["response"]["docs"]
    out = []
    for d in docs:
        m = ISSUE_ID_RE.search(d.get("identifier", ""))
        if m:
            out.append({"identifier": d["identifier"],
                        "date": f"{m.group(1)}-{m.group(2)}-{m.group(3)}"})
    out.sort(key=lambda d: d["date"])
    return out


def evenly_spaced(items, n):
    '''Deterministic stratified pick - no RNG, so the sample is reproducible
    without a seed. Picks n items spread across the year.'''
    if not items or n >= len(items):
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


# ---------------------------------------------------------------------------
# measure
# ---------------------------------------------------------------------------

def scan_issue(text):
    words = len(WORD_RE.findall(text))
    genres = {}
    for label, pats in GENRE_TERMS:
        n = sum(len(re.findall(p, text, re.I)) for p in pats)
        genres[label] = n
    register = {fam: sum(len(re.findall(p, text)) for p in pats)
                for fam, pats in MARKERS.items()}
    return {
        "words": words,
        "genres": genres,
        "register": register,
        "register_families_present": sum(1 for v in register.values() if v),
        "genre_acts": len(genre_acts(text)),
        "author_artifacts": len(AUTHOR_ARTIFACT_RE.findall(text)),
        "record": record_yield(text),
    }


# --- the per-book artifact ------------------------------------------------
# The genre term counts above measure whether the vocabulary is in the source.
# They do not measure the DATASET, which is per-book: Publishers' Weekly's
# Weekly Record gives every American book an entry and a one-line annotation,
# dated to the week of publication. PW states its own policy in the section
# masthead - "The annotations are descriptive, not critical; intended to place
# not to judge the books" - which is the trade declaring the annotation to be
# CLASSIFICATORY. That is what makes it period reception evidence rather than
# review opinion, and it is why the yield is measured per ENTRY, not per word.
WR_HEAD_RE = re.compile(r"Weekly Record of New Publications", re.I)
WR_END_RE = re.compile(r"Index to (?:the )?[A-Za-z ]*Weekly Record"
                       r"|INDEX TO ADVERTISERS|Order List", re.I)
WR_MAX = 60000                  # cap when the end marker does not OCR
ENTRY_RE = re.compile(r"(?m)^([A-Z][A-Za-z'’\-]{2,20}, "
                      r"[A-Z][A-Za-z.'’ \-]{1,28}[.,])")
ENTRY_GENRE_RE = re.compile(
    r"detective|myster|romance|adventure|western|sensation|love story"
    r"|ghost story|sea story|historical nove|scientific romance", re.I)


def record_yield(text):
    '''Entries in the Weekly Record and how many carry a genre word.

    Returns None when the section heading does not OCR - which happens, and is
    itself the finding: SECTION SEGMENTATION, not OCR and not access, is the
    engineering cost of building this dataset.'''
    m = WR_HEAD_RE.search(text)
    if not m:
        return None
    seg = text[m.end():]
    e = WR_END_RE.search(seg, 200)
    seg = seg[:e.start()] if e else seg[:WR_MAX]
    parts = ENTRY_RE.split(seg)[1:]
    entries = [parts[i] + parts[i + 1] for i in range(0, len(parts) - 1, 2)]
    with_genre = [x for x in entries if ENTRY_GENRE_RE.search(x)]
    return {"region_chars": len(seg), "entries": len(entries),
            "entries_with_genre": len(with_genre),
            "end_marker_found": e is not None}


def sample(text, pattern, width=200, limit=3):
    out = []
    for m in re.finditer(pattern, text, re.I):
        lo = max(0, m.start() - width)
        out.append(re.sub(r"\s+", " ", text[lo:m.end() + width]).strip())
        if len(out) >= limit:
            break
    return out


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

# The two sources slice 1 actually named, both tested and both rejected here.
# Kept runnable (--alternatives) so the next session verifies rather than
# re-discovers, and so the rejection carries its own numbers.
ALTERNATIVES = [
    ("The English Catalogue of Books 1914", "englishcatalogue1914unse"),
    ("The Publishers' Circular 1853-01-17", "publishers_circular_18530117"),
]


def check_alternatives():
    print("Alternatives named by slice 1:")
    for label, ident in ALTERNATIVES:
        t = issue_text(ident)
        if t is None:
            print(f"  {label}: could not fetch")
            continue
        words = len(WORD_RE.findall(t))
        hits = {lab: sum(len(re.findall(p, t, re.I)) for p in pats)
                for lab, pats in GENRE_TERMS}
        acts = genre_acts(t)
        print(f"  {label} ({ident})")
        print(f"    {words:,} words | genre-term hits "
              f"{sum(hits.values())} | genre-act headings {len(acts)}")
        print(f"    {', '.join(f'{k}={v}' for k, v in hits.items() if v) or 'no genre term fires'}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-year", type=int, default=4)
    ap.add_argument("--start", type=int, default=1872)
    ap.add_argument("--end", type=int, default=1929)
    ap.add_argument("--alternatives", action="store_true",
                    help="measure the two sources slice 1 named, and stop")
    args = ap.parse_args()

    if args.alternatives:
        return check_alternatives()

    years = list(range(args.start, args.end + 1))

    print(f"Enumerating {COLLECTION} issues, {args.start}-{args.end} ...")
    with ThreadPoolExecutor(max_workers=8) as ex:
        per_year_all = dict(zip(years, ex.map(issues_for_year, years)))

    coverage = {y: len(v) for y, v in per_year_all.items()}
    total_issues = sum(coverage.values())
    print(f"  {total_issues} dated issues across {len(years)} years "
          f"({total_issues / max(1, len(years)):.1f}/yr)")

    picked = []
    for y in years:
        for it in evenly_spaced(per_year_all[y], args.per_year):
            picked.append({**it, "year": y})
    print(f"Sampling {len(picked)} issues ({args.per_year}/yr, evenly spaced)")

    def work(it):
        t = issue_text(it["identifier"])
        if t is None:
            return {**it, "ok": False}
        return {**it, "ok": True, **scan_issue(t)}

    results = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        for i, r in enumerate(ex.map(work, picked), 1):
            results.append(r)
            if i % 25 == 0 or i == len(picked):
                print(f"  scanned {i}/{len(picked)}", flush=True)

    ok = [r for r in results if r.get("ok")]
    misses = [r["identifier"] for r in results if not r.get("ok")]
    total_words = sum(r["words"] for r in ok)
    print(f"\n{len(ok)} issues read, {total_words / 1e6:.1f}M words OCR"
          f"{f', {len(misses)} misses' if misses else ''}")

    # --- live-fire control: is this trade material at all? ------------------
    reg_totals = defaultdict(int)
    for r in ok:
        for fam, n in r["register"].items():
            reg_totals[fam] += n
    fams_firing = sum(1 for v in reg_totals.values() if v)
    print("\nRegister control (slice 1's five families):")
    for fam in MARKERS:
        print(f"  {fam:16s} {reg_totals[fam]:>8,}")
    print(f"  families firing: {fams_firing}/5")

    # --- per-year series, per million words --------------------------------
    labels = [lab for lab, _ in GENRE_TERMS]
    by_year = {}
    for y in years:
        rows = [r for r in ok if r["year"] == y]
        w = sum(r["words"] for r in rows)
        by_year[y] = {
            "issues": len(rows), "words": w,
            "per_million": {lab: (sum(r["genres"][lab] for r in rows) * 1e6 / w
                                  if w else 0.0) for lab in labels},
            "raw": {lab: sum(r["genres"][lab] for r in rows) for lab in labels},
            "genre_acts": sum(r["genre_acts"] for r in rows),
            "author_artifacts": sum(r["author_artifacts"] for r in rows),
        }

    # --- take-off, using S2's estimator on S2's terms ----------------------
    clock = {}
    for lab in labels:
        series = [by_year[y]["per_million"][lab] for y in years]
        sm = smooth(series)
        peak = max(sm) if sm else 0.0
        row = {
            "peak_per_million": peak,
            "peak_year": years[sm.index(peak)] if peak > 0 else None,
            "total_hits": sum(by_year[y]["raw"][lab] for y in years),
            "first_attestation": first_attestation(series, year_lo=args.start),
        }
        for frac in (0.05, 0.10, 0.20):
            i = takeoff_year(sm, peak, frac)
            row[f"takeoff_{int(frac * 100)}pct"] = (
                args.start + i if i is not None else None)
        p25, p50, p75, iqr = mass_percentiles(series, year_lo=args.start)
        row.update({"mass_p25": p25, "mass_p50": p50, "mass_p75": p75,
                    "mass_iqr": iqr})
        clock[lab] = row

    print(f"\n{'term':22s} {'hits':>6} {'peak/M':>8} {'peak':>6} "
          f"{'t/o 5%':>7} {'t/o 10%':>8} {'t/o 20%':>8} {'attest':>7}")
    for lab in labels:
        c = clock[lab]
        print(f"{lab:22s} {c['total_hits']:>6} {c['peak_per_million']:>8.2f} "
              f"{str(c['peak_year']):>6} {str(c['takeoff_5pct']):>7} "
              f"{str(c['takeoff_10pct']):>8} {str(c['takeoff_20pct']):>8} "
              f"{str(c['first_attestation']):>7}")

    # --- per-book yield in the Weekly Record -------------------------------
    recs = [r["record"] for r in ok if r.get("record")]
    seg_found = len(recs)
    ent = sum(r["entries"] for r in recs)
    ent_g = sum(r["entries_with_genre"] for r in recs)
    print(f"\nWeekly Record: section located in {seg_found}/{len(ok)} issues "
          f"({seg_found / max(1, len(ok)):.0%})")
    print(f"  entries {ent:,}  with a genre word {ent_g:,} "
          f"({ent_g / max(1, ent):.1%})")

    acts = sum(by_year[y]["genre_acts"] for y in years)
    auth = sum(by_year[y]["author_artifacts"] for y in years)
    print(f"\ngenre acts (caps heading / series name): {acts:,}")
    print(f"author artifacts (excluded from genre):   {auth:,}")

    payload = {
        "probe": "S6 slice 2 - trade catalogue",
        "source": {"collection": COLLECTION, "window": [args.start, args.end],
                   "issues_available": coverage,
                   "issues_available_total": total_issues,
                   "issues_sampled": len(ok), "issues_missed": misses,
                   "words_ocr": total_words, "ocr_cost": "none - IA ships "
                   "_djvu.txt free for this collection, no lending restriction"},
        "register_control": {"totals": dict(reg_totals),
                             "families_firing": fams_firing},
        "by_year": {str(y): by_year[y] for y in years},
        "clock": clock,
        "record_yield": {"issues_with_section": seg_found,
                         "issues_scanned": len(ok), "entries": ent,
                         "entries_with_genre": ent_g,
                         "rate": (ent_g / ent) if ent else None},
        "genre_acts_total": acts,
        "author_artifacts_total": auth,
        "estimator": {"imported_from": "analyze_reception_clock",
                      "smooth_years": 9, "persist_years": 10,
                      "thresholds": [0.05, 0.10, 0.20]},
        "issues": sorted(ok, key=lambda r: r["date"]),
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1)
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
