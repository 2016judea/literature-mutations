'''
    Author: Aidan Jude
    S6 slice 3, analysis half: read reception_series.json and date the genres.

    Deliberately separate from build_reception_series.py, which spends 69
    minutes and 128.5M words of OCR to produce the series. S2 split its pull
    from its analysis for the same reason and it is why S2 could be argued with
    afterwards: the expensive half runs once, the cheap half runs as often as
    the argument needs.

    THE FINDING THIS SCRIPT EXISTS TO REPORT, AND THE ONE IT EXISTS TO REFUSE

    A take-off date from a fraction-of-peak threshold on a SMOOTHED series is
    only meaningful if the series is dense. On a sparse series with hard zeros,
    a 9-year centered moving average spreads a first spike BACKWARDS by up to
    four years and the threshold is crossed by the smoothed shoulder - so the
    reported take-off can precede the first actual occurrence.

    Measured here, not assumed: `sensation novel`'s first hit is 1863 and the
    inherited estimator reports a take-off of 1859. `sea story` moves from 1855
    to 1929 - SEVENTY-FOUR YEARS - as the smoothing width goes from 9 to 1.

    So every take-off is reported with its SENSITIVITY BAND across smoothing
    widths 9/5/3/1, and a term whose band spans more than TOLERANCE years is
    reported as having NO MEASURABLE TAKE-OFF rather than being given a date it
    cannot support. This is a correction to how S2's estimator behaves on this
    kind of source, not a criticism of S2 - Ngrams series are dense and smooth
    and the bias barely bites there.

    Run:  python analyze_reception_series.py
    Out:  reception_clock_trade.json
'''

import json
import sys

from analyze_reception_clock import first_attestation, takeoff_year

IN = "reception_series.json"
OUT = "reception_clock_trade.json"
SMOOTH_WIDTHS = (9, 5, 3, 1)     # 9 is what S2 uses; 1 is unsmoothed
PRIMARY_FRAC = 0.10
TOLERANCE = 10                   # years of spread a take-off may span
# Annotations do not exist before this year: the American Publishers' Circular
# did not annotate, and Publishers' Weekly's Weekly Record only begins doing so
# in the late 1870s. Measured: 5 annotations across 522 pre-1872 issues, 17
# across 1872-76, then 2,284 in 1877-81. Any statistic from the annotation
# series before this year is measuring the practice, not the vocabulary.
ANNOTATION_FLOOR = 1878


def smooth_k(ts, k):
    if k <= 1:
        return list(ts)
    half = k // 2
    out = []
    for i in range(len(ts)):
        lo, hi = max(0, i - half), min(len(ts), i + half + 1)
        out.append(sum(ts[lo:hi]) / (hi - lo))
    return out


def sustained_run(raw, years, need=5, span=10):
    '''First year after which the term is present in `need` of the next `span`
    years. Unlike a fraction-of-peak crossing this cannot precede the first
    occurrence, and unlike a bare first-hit it rejects an isolated OCR fluke.'''
    for i, y in enumerate(years):
        if raw[i] <= 0:
            continue
        window = raw[i:i + span]
        if sum(1 for v in window if v > 0) >= min(need, len(window)):
            return y
    return None


def describe(series, raw, years):
    y0 = years[0]
    nz = [y for y, n in zip(years, raw) if n > 0]
    band = []
    for k in SMOOTH_WIDTHS:
        sm = smooth_k(series, k)
        peak = max(sm) if sm else 0.0
        i = takeoff_year(sm, peak, PRIMARY_FRAC)
        band.append(y0 + i if i is not None else None)
    known = [v for v in band if v is not None]
    spread = (max(known) - min(known)) if len(known) > 1 else None
    measurable = bool(known) and len(known) == len(band) and spread is not None \
        and spread <= TOLERANCE
    sm9 = smooth_k(series, 9)
    peak = max(sm9) if sm9 else 0.0
    return {
        "total_hits": sum(raw),
        "first_hit": nz[0] if nz else None,
        "years_with_a_hit": len(nz),
        "leading_zero_years": (nz[0] - y0) if nz else len(years),
        "first_attestation": first_attestation(series, year_lo=y0),
        "sustained_from": sustained_run(raw, years),
        "peak": round(peak, 2),
        "peak_year": years[sm9.index(peak)] if peak > 0 else None,
        "peak_at_window_edge": bool(peak > 0
                                    and years[sm9.index(peak)] >= years[-1] - 1),
        "takeoff_band": dict(zip([f"smooth_{k}" for k in SMOOTH_WIDTHS], band)),
        "takeoff_spread_years": spread,
        "takeoff_measurable": measurable,
        "takeoff": (f"{min(known)}-{max(known)}" if measurable else None),
    }


def main():
    d = json.load(open(IN, encoding="utf-8"))
    by = d["by_year"]
    years = sorted((int(y) for y in by), key=int)
    labels = list(by[str(years[0])]["per_million"])

    out = {"source": IN,
           "window": [years[0], years[-1]],
           "issues": d["issues_scanned"], "words_ocr": d["words_ocr"],
           "annotations": d["annotations_extracted"],
           "annotation_floor_year": ANNOTATION_FLOOR,
           "estimator": {
               "primary_fraction_of_peak": PRIMARY_FRAC,
               "smooth_widths_tested": list(SMOOTH_WIDTHS),
               "tolerance_years": TOLERANCE,
               "rule": "a take-off whose band spans more than TOLERANCE years "
                       "across smoothing widths is reported as NOT MEASURABLE; "
                       "a fraction-of-peak crossing on a smoothed sparse series "
                       "can precede the first actual occurrence",
           },
           "series": {}}

    for norm, key, floor in (("per_million", "whole_raw", years[0]),
                             ("per_1k_annotations", "ann_raw",
                              ANNOTATION_FLOOR)):
        ys = [y for y in years if y >= floor]
        block = {}
        for lab in labels:
            s = [by[str(y)][norm][lab] for y in ys]
            raw = [by[str(y)][key][lab] for y in ys]
            block[lab] = describe(s, raw, ys)
        out["series"][norm] = {"window": [ys[0], ys[-1]], "terms": block}

    for norm in out["series"]:
        blk = out["series"][norm]
        print(f"\n=== {norm}  ({blk['window'][0]}-{blk['window'][1]}) ===")
        print(f"{'term':20s} {'hits':>6} {'1st':>5} {'lead0':>6} {'sust':>5} "
              f"{'peak yr':>8} {'take-off':>10} {'spread':>7}")
        for lab, r in sorted(blk["terms"].items(),
                             key=lambda kv: -kv[1]["total_hits"]):
            edge = "*" if r["peak_at_window_edge"] else " "
            print(f"{lab:20s} {r['total_hits']:>6} {str(r['first_hit']):>5} "
                  f"{r['leading_zero_years']:>6} {str(r['sustained_from']):>5} "
                  f"{str(r['peak_year']) + edge:>8} "
                  f"{str(r['takeoff'] or 'not measurable'):>10} "
                  f"{str(r['takeoff_spread_years']):>7}")
    print("\n* peak sits at the window edge: the term is still rising when the "
          "source ends, so any fraction-of-peak date is biased late.")

    # --- the two findings, stated with their denominators -------------------
    pm = out["series"]["per_million"]["terms"]

    def words(a, b):
        return sum(by[str(y)]["words"] for y in years if a <= y <= b)

    def issues(a, b):
        return sum(by[str(y)]["issues"] for y in years if a <= y <= b)

    findings = []
    for lab in ("mystery story", "detective story"):
        r = pm[lab]
        if r["first_hit"] is None:
            continue
        pre_hi = r["first_hit"] - 1
        findings.append({
            "term": lab,
            "absent_window": [years[0], pre_hi],
            "absent_words": words(years[0], pre_hi),
            "absent_issues": issues(years[0], pre_hi),
            "present_window": [r["first_hit"], years[-1]],
            "present_hits": r["total_hits"],
            "sustained_from": r["sustained_from"],
            "takeoff": r["takeoff"],
            "peak_year": r["peak_year"],
            "still_rising_at_window_edge": r["peak_at_window_edge"],
        })
        print(f"\n{lab}: ZERO occurrences in {r['first_hit'] - years[0]} years "
              f"({years[0]}-{pre_hi}), across "
              f"{words(years[0], pre_hi) / 1e6:.1f}M words and "
              f"{issues(years[0], pre_hi):,} issues. Then {r['total_hits']:,} "
              f"occurrences {r['first_hit']}-{years[-1]}. "
              f"Sustained from {r['sustained_from']}, take-off "
              f"{r['takeoff'] or 'not measurable'}, peak {r['peak_year']}"
              f"{' (still rising)' if r['peak_at_window_edge'] else ''}.")
    out["findings"] = findings

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
