'''
    Author: Aidan Jude
    S6 slice 1: is the cheapest reception source actually there?

    S6 is the paper's contribution and it is weeks of work, so the first slice
    is not the dataset - it is a go/no-go on the cheapest source before
    committing those weeks.

    The claim being tested (RESEARCH-PROGRAM.md S6): publishers' back-matter
    advertisements are genre formation as a DATED MARKETING ACT - the moment a
    house creates "The Detective Series" and starts recruiting into it - and
    those pages are "bound into the Gutenberg and Internet Archive scans
    already being downloaded and discarded." build_corpus.py takes ~20k words
    from the FRONT of each text and throws the rest away, so nobody on this
    project has ever looked at the back matter.

    This fetches the FULL text for a sample of ids the project already holds
    and measures how many carry a publisher advertisement or series list.

    Two things it is careful about:

    1. SEARCH THE REGISTER, NOT A STRING. An advertisement page announces
       itself through a vocabulary - "BY THE SAME AUTHOR", "UNIFORM WITH",
       "CROWN 8vo", "PRESS OPINIONS", British price notation like "3s. 6d." -
       and any single one of those can appear innocently in a novel. So each
       marker is scored separately, position is recorded, and a book counts as
       carrying an ad only on CORROBORATION: two distinct marker families in
       the same region of the file. A count built on one keyword would be a
       measurement of that keyword, not of advertisements.

    2. A NEGATIVE RESULT IS THE POINT AS MUCH AS A POSITIVE ONE. Gutenberg
       transcribers routinely delete publisher ads as not part of the work. If
       they are gone, S6 has to come from Internet Archive page scans instead,
       which is a different and far more expensive pipeline. Establishing that
       in one session is worth more than assuming it either way.

    PERIOD EVIDENCE ONLY, per the S6 rule. Every marker here is language the
    publisher itself set in the book. Nothing modern or retrospective.

    Run:  python probe_backmatter.py [--sample 60] [--seed 0]
    Out:  backmatter_probe.json   (counts, per-marker hits, verbatim excerpts)
'''

import argparse
import json
import os
import random
import re

from constants import shelved_books
from gutenberg_ingest import _http, TEXT_MIRRORS

MANIFEST = os.path.join(shelved_books, "corpus_manifest.json")
OUT = "backmatter_probe.json"
# Full novels are ~700KB each; cache them so the detector can be re-run and
# argued with without re-downloading a hundred books.
CACHE = os.environ.get("BACKMATTER_CACHE", "/tmp/gutenberg_full")

# Marker FAMILIES. A book needs two different families in the same region
# before it is counted, so no single phrase can carry the result on its own.
MARKERS = {
    "same_author": [
        r"BY THE SAME AUTHOR", r"By the same author",
        r"WORKS BY", r"OTHER (?:WORKS|BOOKS) BY",
    ],
    "series_or_list": [
        r"UNIFORM WITH", r"NEW NOVELS?", r"\bNEW BOOKS\b",
        r"(?:CATALOGUE|LIST) OF (?:NEW )?(?:BOOKS|PUBLICATIONS)",
        r"[A-Z][A-Za-z&.,' ]{2,30}'S (?:LIST|CATALOGUE)",
        r"THE .{3,30} SERIES", r"\bSERIES OF NOVELS\b",
    ],
    "trade_format": [
        r"\bCrown 8vo\b", r"\bCROWN 8VO\b", r"\bDemy 8vo\b", r"\bFcap\. 8vo\b",
        r"\bpost 8vo\b", r"\bcloth,? (?:gilt|extra|boards)\b",
    ],
    "price": [
        r"\b\d{1,2}s\.\s*\d{1,2}d\.", r"\b\d{1,2}s\.(?!\w)",
        r"\bprice \d", r"\bnet\.\s*$",
    ],
    "trade_puffery": [
        r"PRESS OPINIONS", r"OPINIONS OF THE PRESS", r"\bNOW READY\b",
        r"\bJUST PUBLISHED\b", r"\bIN THE PRESS\b",
        r"\b(?:Second|Third|Fourth|Fifth|Sixth) Edition\b",
    ],
}

START_RE = re.compile(r"\*\*\*\s*START OF.*?\*\*\*", re.IGNORECASE | re.DOTALL)
END_RE = re.compile(r"\*\*\*\s*END OF.*", re.IGNORECASE | re.DOTALL)


def full_text(book_id):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f"{book_id}.txt")
    if os.path.isfile(path):
        return open(path, encoding="utf-8", errors="ignore").read()
    for tmpl in TEXT_MIRRORS:
        try:
            raw = _http(tmpl.format(id=book_id), want_json=False, retries=2)
            open(path, "w", encoding="utf-8").write(raw)
            return raw
        except Exception:                              # noqa: BLE001
            continue
    return None


def body_of(raw):
    '''The transcribed work, between Gutenberg's own markers. An ad bound into
    the physical book lands INSIDE these; Gutenberg's licence boilerplate is
    outside them and must not be counted as period evidence.'''
    m = START_RE.search(raw)
    body = raw[m.end():] if m else raw
    e = END_RE.search(body)
    return body[:e.start()] if e else body


def scan(text, families=MARKERS):
    hits = {}
    for fam, pats in families.items():
        found = []
        for p in pats:
            for m in re.finditer(p, text, re.MULTILINE):
                found.append({"pattern": p, "at": m.start(),
                              "text": m.group(0)[:60]})
        if found:
            hits[fam] = found
    return hits


def region(body, where):
    n = len(body)
    if where == "front":
        return body[:int(n * 0.04)], 0
    return body[int(n * 0.90):], int(n * 0.90)


def excerpt(body, at, span=420):
    lo = max(0, at - span // 3)
    return re.sub(r"\s+", " ", body[lo:lo + span]).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=60)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()

    man = json.load(open(MANIFEST, encoding="utf-8"))["books"]
    man = [b for b in man if b.get("gutenberg_id")]

    # Stratify by period: bound-in advertising is a Victorian/Edwardian trade
    # practice, so a flat sample would confound "no ads" with "wrong century".
    strata = {"pre-1850": [], "1850-1889": [], "1890-1928": []}
    for b in man:
        y = b["year"]
        k = "pre-1850" if y < 1850 else ("1850-1889" if y < 1890 else "1890-1928")
        strata[k].append(b)
    rng = random.Random(args.seed)
    per = max(1, args.sample // len(strata))
    sample = []
    for k, v in strata.items():
        rng.shuffle(v)
        sample += v[:per]
    print(f"Probing {len(sample)} books "
          f"({ {k: min(per, len(v)) for k, v in strata.items()} })")

    rows = []
    for i, b in enumerate(sample, 1):
        raw = full_text(b["gutenberg_id"])
        if not raw:
            rows.append({**{k: b[k] for k in ("title", "author", "year",
                                              "gutenberg_id")},
                         "fetched": False})
            print(f"  {i:3d}/{len(sample)}  FETCH FAILED  {b['title'][:40]}")
            continue
        body = body_of(raw)
        rec = {**{k: b[k] for k in ("title", "author", "year", "gutenberg_id")},
               "fetched": True,
               "raw_chars": len(raw), "body_chars": len(body),
               "body_words": len(body.split()),
               "regions": {}}
        whole = scan(body)
        rec["whole_body"] = {
            "families": sorted(whole),
            "counts": {f: len(v) for f, v in whole.items()},
            # where in the file each family fires, as a fraction of body length
            "positions": {f: sorted({round(h["at"] / max(len(body), 1), 3)
                                     for h in v})[:8]
                          for f, v in whole.items()},
            "samples": {f: [h["text"] for h in v[:3]] for f, v in whole.items()},
        }
        for where in ("front", "back"):
            seg, off = region(body, where)
            hits = scan(seg)
            fams = sorted(hits)
            rec["regions"][where] = {
                "families": fams,
                "n_families": len(fams),
                "corroborated": len(fams) >= 2,
                "counts": {f: len(v) for f, v in hits.items()},
                "excerpt": (excerpt(body, off + hits[fams[0]][0]["at"])
                            if fams else None),
            }
        rec["carries_ad"] = any(r["corroborated"] for r in rec["regions"].values())
        rec["any_marker_anywhere"] = bool(whole)
        rec["corroborated_anywhere"] = len(whole) >= 2
        rows.append(rec)
        tag = ("AD" if rec["carries_ad"]
               else "??" if rec["corroborated_anywhere"] else "  ")
        print(f"  {i:3d}/{len(sample)}  {tag}  {b['year']}  "
              f"{b['title'][:32]:32s} "
              f"whole={','.join(rec['whole_body']['families']) or '-'}")

    got = [r for r in rows if r.get("fetched")]
    ads = [r for r in got if r["carries_ad"]]
    by_period = {}
    for r in got:
        k = ("pre-1850" if r["year"] < 1850
             else "1850-1889" if r["year"] < 1890 else "1890-1928")
        d = by_period.setdefault(k, {"n": 0, "ads": 0})
        d["n"] += 1
        d["ads"] += bool(r["carries_ad"])

    summary = {
        "sampled": len(rows), "fetched": len(got),
        "carrying_ad": len(ads),
        "rate": round(len(ads) / max(len(got), 1), 3),
        "by_period": by_period,
        "back_only": sum(1 for r in got
                         if r["regions"]["back"]["corroborated"]
                         and not r["regions"]["front"]["corroborated"]),
        "front_only": sum(1 for r in got
                          if r["regions"]["front"]["corroborated"]
                          and not r["regions"]["back"]["corroborated"]),
        "both": sum(1 for r in got
                    if r["regions"]["back"]["corroborated"]
                    and r["regions"]["front"]["corroborated"]),
        # The controls that decide whether a zero is a finding or a broken
        # detector: does ANY marker fire ANYWHERE, in any book?
        "any_marker_anywhere": sum(1 for r in got if r["any_marker_anywhere"]),
        "corroborated_anywhere": sum(1 for r in got
                                     if r["corroborated_anywhere"]),
        "family_totals": {f: sum(r["whole_body"]["counts"].get(f, 0)
                                 for r in got) for f in MARKERS},
        "books_per_family": {f: sum(1 for r in got
                                    if f in r["whole_body"]["counts"])
                             for f in MARKERS},
    }
    json.dump({"summary": summary, "books": rows},
              open(args.out, "w", encoding="utf-8"), indent=1)

    print(f"\n{len(ads)}/{len(got)} fetched books carry a corroborated "
          f"publisher advertisement ({100 * summary['rate']:.0f}%)")
    print(f"detector controls: {summary['any_marker_anywhere']}/{len(got)} books "
          f"fire ANY marker anywhere; "
          f"{summary['corroborated_anywhere']}/{len(got)} fire two families")
    print("  per family (books / total hits): " + ", ".join(
        f"{f} {summary['books_per_family'][f]}/{summary['family_totals'][f]}"
        for f in MARKERS))
    for k, d in sorted(by_period.items()):
        print(f"   {k:10s} {d['ads']}/{d['n']}")
    print(f"   position: back only {summary['back_only']}, "
          f"front only {summary['front_only']}, both {summary['both']}")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
