'''
    Author: Aidan Jude
    S2, step 2: date each genre's NAME and compare against its textual clock.

    docs/RESEARCH-PROGRAM.md SS "S2 - The reception clock". The brief's framing:
    this is a *validator*, not a finding. If the two clocks agree on detective
    fiction, that licenses the instrument. If the seven perennial modes also have
    flat name-curves, "the null becomes a result rather than an absence - which
    is the most valuable outcome available here."

    So there are two numbers per genre, not one:

      TAKE-OFF   when the name entered the language (a date)
      SPREAD     how concentrated its usage mass is  (a width)

    Take-off is the answer for detective fiction. Spread is the answer for the
    other seven, because a perennial mode has no take-off to find - and a width
    is comparable against the textual clock's own width (year_std), which a date
    is not.

    METHOD, and why each choice is the defensible one:

    * Window 1800-1950. Pre-1800 is excluded by the brief ("do not read
      anything pre-1800 as signal") and the data shows why: "Gothic romance"
      peaks in 1776 on a corpus so small the normalized frequency is noise. The
      1950 end is the corpus era (pre-1929) plus 21 years of slack, so a genre
      that formed at the very end of the corpus still has room to be named.

    * 9-year centered moving average, computed here rather than server-side.
      Google's smoothing= parameter is an undocumented transform between source
      and finding; ours is in the repo.

    * Take-off = first year the smoothed curve crosses 10% of its own in-window
      peak AND stays above for 10+ consecutive years. Fraction-of-peak is
      scale-free, which matters because these terms differ by ~3 orders of
      magnitude in absolute frequency. The 10-year persistence requirement is
      what rejects an OCR spike. Reported at 5%/10%/20% so the threshold is
      visible as a sensitivity, not hidden as a constant.

    * Spread = the 25th-75th percentile width of cumulative usage mass in the
      window. Directly analogous to the textual clock's year_std: a name that was
      "born" has narrow mass, a perennial mode's name is spread across the era.

    * Peak measured in-window (<=1950) for the primary number, and over the full
      series (<=2019) as a sensitivity. This matters: "science fiction" and
      "fantasy fiction" are 100x more common in 1990 than 1930, so a peak taken
      over all time pushes their historical take-off artificially late.

    * Controls. Ngrams normalizes per-year token counts but corpus COMPOSITION
      drifts. If era-neutral fiction phrases ("the novel", "a novel") show the
      same late-mass skew as the genre names, the skew is the corpus and no
      per-genre number means anything. This control is the difference between a
      result and an artifact.

    Run:  python analyze_reception_clock.py
    In:   _data/ngrams_raw.json  (pull_ngrams.py)
          controls_results.json  (the textual clock, checked in)
    Out:  reception_clock.json   -> emit_reception_figure.py draws Figs. 6-7
                                    docs/S2-RECEPTION-CLOCK.md reads the table
'''

import json
import os
import statistics

from constants import shelved_books

RAW_FILE = os.path.join(shelved_books, "ngrams_raw.json")
TEXTUAL_FILE = "controls_results.json"
OUT_JSON = "reception_clock.json"
OUT_MD = os.path.join("docs", "S2-RECEPTION-CLOCK.md")

WIN_START, WIN_END = 1800, 1950
SMOOTH = 9                      # centered moving average, years
THRESHOLDS = (0.05, 0.10, 0.20)  # fraction-of-peak, primary is 0.10
PERSIST = 10                    # years a crossing must hold to count


# ---------------------------------------------------------------------------
# series helpers
# ---------------------------------------------------------------------------

def smooth(ts, k=SMOOTH):
    '''Centered moving average. Edges average over the available half-window
    rather than being dropped, so the window boundary does not silently move.'''
    half = k // 2
    out = []
    for i in range(len(ts)):
        lo, hi = max(0, i - half), min(len(ts), i + half + 1)
        out.append(sum(ts[lo:hi]) / (hi - lo))
    return out


def window(ts, year_start, lo=WIN_START, hi=WIN_END):
    i0, i1 = lo - year_start, hi - year_start + 1
    return ts[i0:i1]


def takeoff_year(sm_win, peak, frac, persist=PERSIST):
    '''First year index where the curve crosses frac*peak and holds for
    `persist` consecutive years. Returns None if it never does.'''
    if peak <= 0:
        return None
    thresh = frac * peak
    n = len(sm_win)
    for i in range(n):
        if sm_win[i] < thresh:
            continue
        run = 0
        for j in range(i, min(n, i + persist)):
            if sm_win[j] >= thresh:
                run += 1
            else:
                break
        if run >= min(persist, n - i):
            return i
    return None


def mass_percentiles(win, year_lo=WIN_START):
    '''Percentiles of cumulative usage mass. Returns (p25, p50, p75, iqr).
    Uses the RAW in-window series - smoothing would blur the mass distribution
    we are trying to measure.'''
    total = sum(win)
    if total <= 0:
        return (None, None, None, None)
    targets = [0.25, 0.50, 0.75]
    hits = []
    acc = 0.0
    ti = 0
    for i, v in enumerate(win):
        acc += v
        while ti < len(targets) and acc / total >= targets[ti]:
            hits.append(year_lo + i)
            ti += 1
    while len(hits) < 3:
        hits.append(year_lo + len(win) - 1)
    return (hits[0], hits[1], hits[2], hits[2] - hits[0])


def first_attestation(win, year_lo=WIN_START, need=5, span=10):
    '''First in-window year with a nonzero frequency that is followed by at
    least `need` nonzero years within `span`. Rejects isolated OCR hits.'''
    n = len(win)
    for i in range(n):
        if win[i] <= 0:
            continue
        nz = sum(1 for v in win[i : min(n, i + span)] if v > 0)
        if nz >= min(need, n - i):
            return year_lo + i
    return None


def describe(series_list, year_start, full_peak=False):
    '''Metrics for one term or for a summed set of terms.'''
    # sum across terms: these are normalized frequencies of distinct ngrams, so
    # the sum is the frequency of naming the genre by any of its names
    n = len(series_list[0])
    total = [sum(s[i] for s in series_list) for i in range(n)]

    sm = smooth(total)
    sm_win = window(sm, year_start)
    raw_win = window(total, year_start)

    peak_win = max(sm_win) if sm_win else 0.0
    peak_full_idx = max(range(len(sm)), key=lambda i: sm[i]) if sm else 0
    peak_full = sm[peak_full_idx] if sm else 0.0

    out = {
        "peak_freq_in_window": peak_win,
        "peak_year_in_window": WIN_START + sm_win.index(peak_win) if peak_win > 0 else None,
        "peak_freq_all_time": peak_full,
        "peak_year_all_time": year_start + peak_full_idx if peak_full > 0 else None,
        "first_attestation": first_attestation(raw_win),
        "total_mass_in_window": sum(raw_win),
    }
    p25, p50, p75, iqr = mass_percentiles(raw_win)
    out.update({"mass_p25": p25, "mass_median": p50, "mass_p75": p75, "mass_iqr": iqr})

    for frac in THRESHOLDS:
        i = takeoff_year(sm_win, peak_win, frac)
        out[f"takeoff_{int(frac*100)}pct"] = (WIN_START + i) if i is not None else None
    # sensitivity: same rule, peak taken over the whole series instead
    i = takeoff_year(sm_win, peak_full, 0.10)
    out["takeoff_10pct_vs_alltime_peak"] = (WIN_START + i) if i is not None else None
    return out


# ---------------------------------------------------------------------------

def main():
    with open(RAW_FILE) as fh:
        raw = json.load(fh)
    with open(TEXTUAL_FILE) as fh:
        textual = json.load(fh)

    year_start = raw["year_start"]
    series = raw["series"]
    n_years = len(next(v for v in series.values() if v))
    zeros = [0.0] * n_years

    def get(term):
        v = series.get(term)
        return v if v else zeros

    # match the textual communities by held_out_label, not by list position -
    # index order is not a contract and two_city-style silent misalignment is
    # exactly how a plausible wrong number ships
    by_label = {c["held_out_label"]: c for c in textual["communities"]}

    rows = []
    for comm in raw["communities"]:
        label = comm["held_out_label"]
        if label not in by_label:
            raise SystemExit(
                f"held_out_label {label!r} not found in {TEXTUAL_FILE}. "
                "The textual clock and the vocabulary pairing have drifted apart; "
                "reconcile them before trusting any number below."
            )
        t = by_label[label]

        vocab = describe([get(x) for x in comm["terms"]], year_start)
        row = {
            "key": comm["key"],
            "vocab_reading": comm["vocab_reading"],
            "held_out_label": label,
            "label_agrees_with_vocab": comm["label_agrees"],
            "terms": comm["terms"],
            "label_terms": comm["label_terms"],
            # textual clock
            "n_books": t["n"],
            "year_min": t["year_min"],
            "year_max": t["year_max"],
            "year_std": t["year_std"],
            "concentration_z": t["concentration_z"],
            # name clock, from the vocabulary terms
            "name": vocab,
            # per-term breakdown so no single term is load-bearing invisibly
            "per_term": {x: describe([get(x)], year_start) for x in comm["terms"]},
        }
        if comm["label_terms"]:
            row["name_from_label_terms"] = describe(
                [get(x) for x in comm["label_terms"]], year_start
            )
            row["per_label_term"] = {
                x: describe([get(x)], year_start) for x in comm["label_terms"]
            }
        rows.append(row)

    controls = {
        term: describe([get(term)], year_start) for term in raw["control_terms"]
    }
    controls["_ALL_CONTROLS"] = describe(
        [get(t) for t in raw["control_terms"]], year_start
    )

    # ---- the two cross-clock comparisons -------------------------------------
    # 1. does the name take-off track the textual onset?
    # 2. does the name's spread track the textual spread?
    pairs_takeoff = [
        (r["year_min"], r["name"]["takeoff_10pct"])
        for r in rows
        if r["name"]["takeoff_10pct"] is not None
    ]
    pairs_spread = [
        (r["year_std"], r["name"]["mass_iqr"])
        for r in rows
        if r["name"]["mass_iqr"] is not None
    ]

    def pearson(xy):
        if len(xy) < 3:
            return None
        xs, ys = [p[0] for p in xy], [p[1] for p in xy]
        mx, my = statistics.fmean(xs), statistics.fmean(ys)
        num = sum((x - mx) * (y - my) for x, y in xy)
        dx = sum((x - mx) ** 2 for x in xs) ** 0.5
        dy = sum((y - my) ** 2 for y in ys) ** 0.5
        return num / (dx * dy) if dx and dy else None

    result = {
        "generated_from": {
            "ngrams": RAW_FILE,
            "textual_clock": TEXTUAL_FILE,
            "corpus": raw["corpus"],
        },
        "method": {
            "window": [WIN_START, WIN_END],
            "smoothing_years": SMOOTH,
            "takeoff_thresholds": list(THRESHOLDS),
            "takeoff_persistence_years": PERSIST,
            "pairing": (
                "Communities are paired to Ngrams terms by their distinctive "
                "vocabulary (top_terms), not by held_out_label. Three of eight "
                "labels disagree with their own community's vocabulary; see "
                "pull_ngrams.py. Label-derived terms are reported alongside."
            ),
        },
        "communities": rows,
        "controls": controls,
        "cross_clock": {
            "r_year_min_vs_name_takeoff": pearson(pairs_takeoff),
            "n_takeoff": len(pairs_takeoff),
            "r_year_std_vs_name_mass_iqr": pearson(pairs_spread),
            "n_spread": len(pairs_spread),
        },
    }

    with open(OUT_JSON, "w") as fh:
        json.dump(result, fh, indent=1)
    print(f"wrote {OUT_JSON}")

    # ---- console table -------------------------------------------------------
    print(f"\n{'genre (from vocab)':<34} {'n':>3} {'txt_min':>7} {'txt_std':>7} "
          f"{'z':>6} | {'name_takeoff':>12} {'attest':>7} {'mass_iqr':>8}")
    print("-" * 108)
    for r in sorted(rows, key=lambda x: x["concentration_z"]):
        nm = r["name"]
        print(f"{r['vocab_reading']:<34} {r['n_books']:>3} {r['year_min']:>7} "
              f"{r['year_std']:>7.1f} {r['concentration_z']:>6.2f} | "
              f"{str(nm['takeoff_10pct']):>12} {str(nm['first_attestation']):>7} "
              f"{str(nm['mass_iqr']):>8}")
    print("-" * 108)
    c = controls["_ALL_CONTROLS"]
    print(f"{'CONTROL (era-neutral phrases)':<34} {'-':>3} {'-':>7} {'-':>7} "
          f"{'-':>6} | {str(c['takeoff_10pct']):>12} "
          f"{str(c['first_attestation']):>7} {str(c['mass_iqr']):>8}")

    cc = result["cross_clock"]
    print(f"\ncross-clock: r(year_min, name_takeoff) = "
          f"{cc['r_year_min_vs_name_takeoff']} over n={cc['n_takeoff']}")
    print(f"             r(year_std, name_mass_iqr) = "
          f"{cc['r_year_std_vs_name_mass_iqr']} over n={cc['n_spread']}")

    print("\nlabel-term contrast (where the held-out label disagrees with vocab):")
    for r in rows:
        if r["label_agrees_with_vocab"] or "name_from_label_terms" not in r:
            continue
        a, b = r["name"], r["name_from_label_terms"]
        print(f"  {r['vocab_reading']:<32} vocab takeoff {str(a['takeoff_10pct']):>6} "
              f"| label ({r['held_out_label']}) takeoff {str(b['takeoff_10pct']):>6}")


if __name__ == "__main__":
    main()
