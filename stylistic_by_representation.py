'''
    Author: Aidan Jude & Claude
    Is the flat stylistic result a real null, or measurement noise?

    THE OBSERVATION
    Phase 2 reports stylistic similarity as a genuinely open question: not
    significant on the full 130 documented pairs (z = 0.91), but significant on
    both narrower checks - Wikidata's 102 pairs (z = 2.45) and the
    well-represented subset of 46 pairs, authors with >= 4 books (z = 2.97).
    docs/PHASE2 leaves it deliberately unresolved: either the narrow checks are
    small-N noise landing the same lucky direction, or the full-sample null was
    itself an artifact the narrow checks happen to correct.

    There is a third reading the reported z-scores hide. Look at the raw effect
    rather than the z:

        all pairs      (>= 1 book)   real 0.0759  null 0.0728   diff 0.0031
        wikidata       (>= 1 book)   real 0.0823  null 0.0728   diff 0.0095
        well-represented (>= 4)      real 0.1086  null 0.0932   diff 0.0154

    The effect grows about fivefold as more text per author is required. That is
    the signature of ESTIMATION NOISE, not absence of effect: an author's style
    vector cannot be estimated from one book, so pairs built on thin authors
    attenuate the real signal toward zero. If that is what is happening, the
    stylistic effect should rise monotonically with books per author.

    THE CONFOUND THIS MUST AVOID
    null_mean itself rises with book count (0.0728 -> 0.0932 above). More text
    means denser TF-IDF vectors and higher cosine similarity for EVERY pair,
    real or random. So a bin's real_mean cannot be compared against the global
    null - the null must be drawn from pairs with the same book-count profile.
    Every bin below is tested against a null restricted to that same bin.

    CONCEPTUAL SIMILARITY IS THE CONTROL
    It is already strongly significant (z = 9.47). If conceptual rises just as
    steeply across bins, the pattern is a general property of having more text
    and says nothing specific about style. If conceptual stays high and roughly
    flat while stylistic climbs from nothing, the attenuation is specific to the
    stylistic measure - which is the prediction.

    METHOD, matching build_influence_graph.py exactly
    permutation_z: draw random (i, j) pairs respecting forward chronology
    (years[i] < years[j]), same count as the real pairs, 5000 trials,
    z = (real_mean - mean null_means) / sd null_means. The only change is that
    the candidate pool is restricted to the bin.

    DATA PROVENANCE
    _data/influence_graph.json is a checked-in artifact of a real run. Its 2,915
    directed edges cover essentially every forward author pair (77 authors ->
    2,926 possible), so the similarity matrices are reconstructed from it
    exactly rather than recomputed from prose.

    RESULT (2026-08-15): THE HYPOTHESIS IS NOT SUPPORTED.
    First, the machinery is sound - it reproduces the published figures exactly:
    threshold 1 gives stylistic z = 0.90 against a published 0.905, and
    threshold 4 gives 47 authors / 46 pairs / z = 2.97 against a published
    2.972.

    With that validated, sweeping the author threshold t = n_books_used >= t,
    each t tested against a null drawn from the same subset:

        t=1   130 pairs   diff +0.0031   z  0.90
        t=2   116 pairs   diff -0.0024   z -0.70
        t=3    94 pairs   diff +0.0012   z  0.31
        t=4    46 pairs   diff +0.0154   z  2.97
        t=5    39 pairs   diff +0.0130   z  2.29

    That is not monotone. Attenuation by estimation noise predicts a steady
    climb; instead t=2 is NEGATIVE, t=3 is ~0, and the effect appears only at
    t=4. The apparent fivefold growth in the three published numbers came from
    reading three non-nested samples (all / wikidata / well-represented) as if
    they were a series in representation. They are not.

    Conceptual similarity, the control, behaves exactly as a real effect should:
    z = 9.48, 8.64, 8.00, 6.21, 5.49 - declining only as n falls, i.e. losing
    power, never sign. The contrast is the point: the machinery detects a real
    effect cleanly at every threshold, and finds no stable stylistic one.

    So docs/PHASE2's "deliberately unresolved" verdict stands, and this sweep
    tilts it: dropping 48 pairs between t=3 and t=4 flips z from 0.31 to 2.97,
    which is fragility, not signal. The stylistic result is most likely a null.

    Run:  python stylistic_by_representation.py -> stylistic_representation.json
'''

import json
import os

import numpy as np

GRAPH = "_data/influence_graph.json"
KNOWN = "_data/known_influences.json"
WIKIDATA = "_data/wikidata_influences.json"
OUT = "stylistic_representation.json"

TRIALS = 5000
N_BINS = 4
SEED = 0


def load_graph():
    g = json.load(open(GRAPH, encoding="utf-8"))
    names = [a["name"] for a in g["authors"]]
    idx = {n: i for i, n in enumerate(names)}
    years = np.array([a["earliest_year"] for a in g["authors"]], dtype=float)
    nbooks = np.array([a["n_books_used"] for a in g["authors"]], dtype=float)

    n = len(names)
    styl = np.full((n, n), np.nan)
    conc = np.full((n, n), np.nan)
    for e in g["edges"]:
        i, j = idx[e["from"]], idx[e["to"]]
        styl[i, j] = styl[j, i] = e["stylistic"]
        conc[i, j] = conc[j, i] = e["conceptual"]
    return names, idx, years, nbooks, styl, conc


def load_pairs(path, idx, years):
    '''Same filter as build_influence_graph.resolve_held_out_pairs.'''
    if not os.path.isfile(path):
        return []
    raw = json.load(open(path, encoding="utf-8"))
    return [(r["from"], r["to"]) for r in raw
            if r["from"] in idx and r["to"] in idx
            and years[idx[r["from"]]] < years[idx[r["to"]]]]


def permutation_z(real_vals, cand_i, cand_j, sim, rng, trials=TRIALS):
    '''build_influence_graph.permutation_z, with a restricted candidate pool.'''
    real_vals = np.asarray([v for v in real_vals if not np.isnan(v)], float)
    if len(real_vals) == 0 or len(cand_i) == 0:
        return None
    pool = sim[cand_i, cand_j]
    pool = pool[~np.isnan(pool)]
    if len(pool) == 0:
        return None
    real_mean = float(real_vals.mean())
    null_means = np.array([pool[rng.choice(len(pool), size=len(real_vals),
                                           replace=True)].mean()
                           for _ in range(trials)])
    z = (real_mean - null_means.mean()) / (null_means.std() + 1e-12)
    return {"real_mean": round(real_mean, 4),
            "null_mean": round(float(null_means.mean()), 4),
            "null_std": round(float(null_means.std()), 4),
            "diff": round(real_mean - float(null_means.mean()), 4),
            "z": round(float(z), 3), "n_pairs": int(len(real_vals))}


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    os.chdir(here)
    names, idx, years, nbooks, styl, conc = load_graph()
    rng = np.random.default_rng(SEED)

    pairs = load_pairs(KNOWN, idx, years)
    wd = load_pairs(WIKIDATA, idx, years)
    print(f"authors: {len(names)}   documented pairs in graph: {len(pairs)}"
          f"   wikidata pairs: {len(wd)}")
    print(f"books per author (n_books_used): min {nbooks.min():.0f} "
          f"median {np.median(nbooks):.0f} max {nbooks.max():.0f}\n")

    # forward-chronology candidate pool, as in the original test
    ci, cj = np.where(years[:, None] < years[None, :])
    cand_min = np.minimum(nbooks[ci], nbooks[cj])

    pair_i = np.array([idx[a] for a, _ in pairs])
    pair_j = np.array([idx[b] for _, b in pairs])
    pair_min = np.minimum(nbooks[pair_i], nbooks[pair_j])

    # Bins are equal-count quantiles of the DOCUMENTED pairs' representation,
    # fixed before any z is computed, so bin edges cannot be tuned to a result.
    qs = np.quantile(pair_min, np.linspace(0, 1, N_BINS + 1))
    edges = sorted(set(np.round(qs).astype(int).tolist()))
    print(f"bin edges on min(n_books_used): {edges}\n")

    report = {"meta": {"n_authors": len(names), "n_pairs": len(pairs),
                       "trials": TRIALS, "bin_edges": edges}, "bins": []}

    hdr = (f"{'bin (min books)':<18}{'n':>5}   "
           f"{'STYLISTIC real':>15}{'null':>9}{'diff':>9}{'z':>8}   "
           f"{'CONCEPTUAL diff':>16}{'z':>8}")
    print(hdr); print("-" * len(hdr))

    for lo, hi in zip(edges[:-1], edges[1:]):
        last = hi == edges[-1]
        sel = (pair_min >= lo) & (pair_min <= hi if last else pair_min < hi)
        pool = (cand_min >= lo) & (cand_min <= hi if last else cand_min < hi)
        if sel.sum() < 5:
            continue
        row = {"lo": int(lo), "hi": int(hi), "n_pairs": int(sel.sum())}
        for key, sim in (("stylistic", styl), ("conceptual", conc)):
            vals = sim[pair_i[sel], pair_j[sel]]
            row[key] = permutation_z(vals, ci[pool], cj[pool], sim, rng)
        s, c = row["stylistic"], row["conceptual"]
        label = f"{lo}-{hi}" if not last else f"{lo}+"
        print(f"{label:<18}{row['n_pairs']:>5}   "
              f"{s['real_mean']:>15.4f}{s['null_mean']:>9.4f}"
              f"{s['diff']:>9.4f}{s['z']:>8.2f}   "
              f"{c['diff']:>16.4f}{c['z']:>8.2f}")
        report["bins"].append(row)

    # --- the threshold sweep -------------------------------------------------
    # The primary result. Restrict AUTHORS to n_books_used >= t and draw the
    # null from that same subset - build_influence_graph.restrict_to_subset's
    # exact shape, so t=1 and t=4 must reproduce the published z-scores. If they
    # ever stop reproducing, this file is wrong, not the paper.
    print(f"\n{'t':>3}{'authors':>9}{'pairs':>7}   {'STYL diff':>10}{'z':>8}"
          f"   {'CONC diff':>10}{'z':>8}")
    print("-" * 62)
    sweep = []
    for t in range(1, int(nbooks.max()) + 1):
        keep = nbooks >= t
        ok = keep[pair_i] & keep[pair_j]
        if ok.sum() < 5:
            continue
        pool = keep[ci] & keep[cj]
        row = {"threshold": t, "n_authors": int(keep.sum()),
               "n_pairs": int(ok.sum())}
        for key, sim in (("stylistic", styl), ("conceptual", conc)):
            row[key] = permutation_z(sim[pair_i[ok], pair_j[ok]],
                                     ci[pool], cj[pool], sim, rng)
        s, c = row["stylistic"], row["conceptual"]
        print(f"{t:>3}{row['n_authors']:>9}{row['n_pairs']:>7}   "
              f"{s['diff']:>10.4f}{s['z']:>8.2f}   {c['diff']:>10.4f}{c['z']:>8.2f}")
        sweep.append(row)
    report["threshold_sweep"] = sweep

    # Continuous check, free of any binning choice: does a pair's stylistic
    # excess over its own book-count baseline grow with representation?
    base = {}
    for m in np.unique(cand_min):
        v = styl[ci[cand_min == m], cj[cand_min == m]]
        v = v[~np.isnan(v)]
        base[m] = v.mean() if len(v) else np.nan
    excess = np.array([styl[i, j] - base.get(m, np.nan)
                       for i, j, m in zip(pair_i, pair_j, pair_min)])
    ok = ~np.isnan(excess)
    from scipy.stats import spearmanr
    rho, p = spearmanr(pair_min[ok], excess[ok])
    print(f"\ncontinuous: Spearman(min books, stylistic excess over its own "
          f"baseline) rho={rho:.3f} p={p:.3f} n={ok.sum()}")
    report["continuous"] = {"spearman_rho": round(float(rho), 3),
                            "p": round(float(p), 4), "n": int(ok.sum())}

    json.dump(report, open(OUT, "w"), indent=1)
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
