'''
    Author: Aidan Jude
    S6 slice 3 addendum: is "mystery story" a NEW genre or a RENAMING of
    detective fiction?

    This is the first question a reviewer asks about slice 3's finding, and if
    it cannot be answered the finding is soft. Slice 3 measured that the trade
    press goes from ZERO uses of "mystery story" in 41.8M words (1855-1895) to
    1,605 uses in the following 34 years. A skeptic's obvious reading: the trade
    simply started saying "mystery story" where it used to say "detective
    story", and nothing about genre formation happened at all.

    THREE TESTS, WEAKEST TO STRONGEST

    1. CO-OCCURRENCE (weak). Do the two terms appear in the same annotation? A
       renaming predicts they rarely do. But an annotation is one short line, so
       the absence of "detective" from twenty words is close to no evidence -
       reported, and reported as weak.

    2. SUBSTITUTION vs CO-GROWTH (strong, and it decides the question). A
       renaming predicts detective fiction CEDES GROUND as mystery rises: the
       combined rate should be roughly conserved. Co-growth of both falsifies
       renaming. `love story` runs as the control - if every genre word rises
       together, the test means nothing.

    3. DESCRIBED CONTENT (suggestive only). If the two labels are applied to
       different KINDS of book, the trade is distinguishing rather than
       substituting. Log-odds on the annotation vocabulary.

       Test 3's naive form is dominated by PROPER NOUNS - author and character
       names ("van", "craig", "reilly", "stone"), publisher abbreviations
       ("apltn", "dodd", "doran", "dou") and format debris ("illus", "ser") -
       which is the same trap semantic_edges.py's min_df guard exists for.

       A DISPERSION filter was tried first and failed: Helen Reilly, Craig
       Kennedy and Philo Vance each run for a decade or more, so "reilly",
       "craig" and "van" are as well dispersed as "family" is. What works is
       CASING - a token must appear lower-case in the source at least
       MIN_LOWER of the time to count as a common noun rather than a name.

    Run:  python analyze_term_split.py
    Out:  term_split.json
'''

import collections
import gzip
import json
import math
import os
import re
import statistics as st
import sys

from constants import shelved_books

TABLE = os.path.join(shelved_books, "reception_entries.jsonl.gz")
SERIES = "reception_series.json"
OUT = "term_split.json"

MIN_COUNT = 8          # combined occurrences before a token is scored at all
MIN_LOWER = 0.6        # a token must appear lower-case in the source at least
                       # this often to count as a common noun rather than a
                       # NAME. A dispersion filter was tried first and fails:
                       # Helen Reilly, Craig Kennedy and Philo Vance each run
                       # for a decade or more, so "reilly", "craig" and "van"
                       # are as well dispersed as "family" is.
TOP_N = 12

DETECTIVE = ("detective story", "detective (any)")
MYSTERY = "mystery story"

# Genre words themselves are removed - they are the labels being compared, not
# evidence about what the books are.
STOP = set('''a an the and or of in on to is are was were be been by with for
from as at it its this that his her he she they them which who whom whose but
not no s t d ll m re ve i you we us our their there here when where what how
all any some more most other such own so than too very can will just don now
story stories tale tales novel novels mystery mysteries detective detectives
book books author authors new
illus illustrated ser series por diagrs pap cloth ed edition vols vol'''.split())

CASED_RE = re.compile(r"[A-Za-z']+")


def tokens(s):
    '''Lower-cased content tokens, plus the casing evidence needed to tell a
    common noun from a name.'''
    out, lower = set(), collections.Counter()
    for raw in CASED_RE.findall(s):
        w = raw.lower()
        if w in STOP or len(w) <= 2:
            continue
        out.add(w)
        if raw.islower():
            lower[w] += 1
    return out, lower


def load_rows():
    with gzip.open(TABLE, "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def pearson(x, y):
    mx, my = st.mean(x), st.mean(y)
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    den = (sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y)) ** .5
    return num / den if den else 0.0


def bag(rows, sel):
    '''(document frequency, distinct years) per token over the selected rows.'''
    df = collections.Counter()
    seen = collections.Counter()
    lower = collections.Counter()
    n = 0
    for r in rows:
        if not sel(r):
            continue
        n += 1
        ts, lo = tokens(r["annotation"])
        df.update(ts)
        for w in ts:
            seen[w] += 1
        lower.update(lo)
    return df, (seen, lower), n


def log_odds(c1, e1, n1, c2, e2, n2):
    (seen1, low1), (seen2, low2) = e1, e2
    out, dropped = [], []
    for w in set(list(c1) + list(c2)):
        a, b = c1[w], c2[w]
        if a + b < MIN_COUNT:
            continue
        occ = seen1[w] + seen2[w]
        low = low1[w] + low2[w]
        frac = low / occ if occ else 0.0
        if frac < MIN_LOWER:
            dropped.append(w)              # a NAME, not content
            continue
        lor = math.log(((a + .5) / (n1 - a + .5)) / ((b + .5) / (n2 - b + .5)))
        out.append({"token": w, "in_group": a, "in_other": b,
                    "lower_case_fraction": round(frac, 2),
                    "log_odds": round(lor, 2)})
    out.sort(key=lambda r: -r["log_odds"])
    return out, sorted(dropped)


def main():
    rows = load_rows()
    d = json.load(open(SERIES, encoding="utf-8"))
    by = d["by_year"]

    # --- test 1: co-occurrence -------------------------------------------
    det = {i for i, r in enumerate(rows)
           if any(g in r["genres"] for g in DETECTIVE)}
    mys = {i for i, r in enumerate(rows) if MYSTERY in r["genres"]}
    both = det & mys
    print(f"Test 1 - co-occurrence (WEAK)")
    print(f"  detective annotations {len(det)}, mystery {len(mys)}, "
          f"both {len(both)} = {len(both) / max(1, len(mys)):.0%} of mystery")
    print("  Weak by construction: an annotation is ~20 words, so the absence "
          "of\n  'detective' from one is close to no evidence.")

    # --- test 2: substitution vs co-growth -------------------------------
    yrs = [y for y in sorted(by, key=int) if 1890 <= int(y) <= 1929]
    ser = {lab: [by[y]["per_million"][lab] for y in yrs]
           for lab in ("detective story", MYSTERY, "love story",
                       "adventure story")}
    print(f"\nTest 2 - substitution vs co-growth (DECIDES IT)")
    print(f"  {'decade':8s} {'detective':>10} {'mystery':>8} {'sum':>7} "
          f"{'love (ctrl)':>12}")
    decades = {}
    for lo in (1890, 1900, 1910, 1920):
        ix = [i for i, y in enumerate(yrs) if lo <= int(y) < lo + 10]
        m = {lab: st.mean(ser[lab][i] for i in ix) for lab in ser}
        decades[lo] = {k: round(v, 1) for k, v in m.items()}
        decades[lo]["crime_sum"] = round(m["detective story"] + m[MYSTERY], 1)
        print(f"  {str(lo) + 's':8s} {m['detective story']:>10.1f} "
              f"{m[MYSTERY]:>8.1f} "
              f"{m['detective story'] + m[MYSTERY]:>7.1f} "
              f"{m['love story']:>12.1f}")
    d90, d20 = decades[1890], decades[1920]
    growth = d20["detective story"] / max(1e-9, d90["detective story"])
    renaming = d20["detective story"] < d90["detective story"]
    print(f"\n  detective fiction grows {growth:.1f}x across the span in which "
          f"mystery goes\n  {d90[MYSTERY]} -> {d20[MYSTERY]} per million. "
          f"A renaming requires detective to CEDE ground.")
    print(f"  VERDICT: {'RENAMING' if renaming else 'NOT A RENAMING'}.")
    lv = [decades[k]["love story"] for k in (1890, 1900, 1910, 1920)]
    print(f"  Control - love story: {lv[0]} -> {lv[1]} -> {lv[2]} -> {lv[3]}. "
          f"It PEAKS in the 1900s and\n  declines through the 1910s and 1920s "
          f"while detective and mystery both keep\n  rising, so the 1920s "
          f"crime rise is not a general rise in genre vocabulary.\n  (It is "
          f"NOT the case that love story falls across the whole span - it "
          f"rises\n  {lv[0]} -> {lv[3]} end to end. The control is its TURN, "
          f"not its direction.)")
    print(f"  r(mystery, detective) = {pearson(ser[MYSTERY], ser['detective story']):+.2f}, "
          f"r(mystery, adventure) = {pearson(ser[MYSTERY], ser['adventure story']):+.2f} "
          f"- both high because\n  everything rises in the 1920s, which is why "
          f"the decade means decide this and not r.")

    # --- test 3: described content ---------------------------------------
    mc, my_, mn = bag(rows, lambda r: MYSTERY in r["genres"])
    dc, dy, dn = bag(rows, lambda r: any(g in r["genres"] for g in DETECTIVE)
                     and MYSTERY not in r["genres"])
    m_dist, m_names = log_odds(mc, my_, mn, dc, dy, dn)
    d_dist, _ = log_odds(dc, dy, dn, mc, my_, mn)
    print(f"\nTest 3 - described content (SUGGESTIVE ONLY, n={mn} vs {dn})")
    print(f"  distinctive of MYSTERY:   "
          f"{', '.join(r['token'] for r in m_dist[:TOP_N])}")
    print(f"  distinctive of DETECTIVE: "
          f"{', '.join(r['token'] for r in d_dist[:TOP_N])}")
    print(f"  Filtered: >={MIN_COUNT} combined uses AND lower-case in the "
          f"source >={MIN_LOWER:.0%} of\n  the time. Names rejected by that "
          f"rule: {', '.join(m_names[:14])}")

    payload = {
        "question": "is 'mystery story' a new genre or a renaming of detective "
                    "fiction?",
        "test1_cooccurrence": {
            "strength": "weak - an annotation is ~20 words",
            "detective_annotations": len(det), "mystery_annotations": len(mys),
            "both": len(both),
            "both_share_of_mystery": round(len(both) / max(1, len(mys)), 3),
        },
        "test2_substitution": {
            "strength": "strong - this decides it",
            "window": [int(yrs[0]), int(yrs[-1])],
            "decade_means_per_million": decades,
            "detective_growth_1890s_to_1920s": round(growth, 2),
            "is_renaming": bool(renaming),
            "control": "love story, which PEAKS in the 1900s and declines "
                       "through the 1910s-20s while both crime terms keep "
                       "rising. Its end-to-end direction is up, so the control "
                       "is its turning point, not its sign.",
            "r_mystery_detective": round(
                pearson(ser[MYSTERY], ser["detective story"]), 2),
            "r_mystery_adventure": round(
                pearson(ser[MYSTERY], ser["adventure story"]), 2),
            "note": "both r are high because everything rises in the 1920s; "
                    "the decade means, not r, carry this test",
        },
        "test3_content": {
            "strength": "suggestive only - thin counts",
            "n_mystery": mn, "n_detective_only": dn,
            "min_count": MIN_COUNT, "min_lower_case_fraction": MIN_LOWER,
            "rejected_as_names": m_names,
            "distinctive_of_mystery": m_dist[:TOP_N],
            "distinctive_of_detective": d_dist[:TOP_N],
        },
        "verdict": {
            "settled": "It is NOT a renaming. Detective fiction grows rather "
                       "than ceding ground across the same decades.",
            "unsettled": "Whether 'mystery story' is a distinct genre or a "
                         "sibling label inside one expanding crime-fiction "
                         "category. The trade series alone cannot separate "
                         "those two, and test 3 is too thin to settle it.",
        },
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1)
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
