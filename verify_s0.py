'''
    Author: Aidan Jude
    S0, step 4: diff the reconstruction against the published numbers.

    The whole point of S0 is to answer one question - is the published Phase 1
    result reproducible - so this script exists to make the answer checkable
    rather than asserted. It compares, per docs/RESEARCH-PROGRAM.md's table:

      corpus size        345 books / 166 authors     controls_results.json
      null model         90 real vs 94.1 +/- 15.2    results.json.honest_metrics
      detective          n=13, 1878-1926, std 14.9, z=-3.04
      author confound    19.5%
      totals             splits 33 / merges 25 / births 32

    Two rules it follows, both learned the hard way:

    1. Communities are matched by MEMBERSHIP (Jaccard over titles), never by
       held_out_label. S2 established that three of the eight labels name a
       genre their own cluster is not - the one labelled "Science fiction" has
       the vocabulary castle/veil/trembled. Lining runs up by label would
       compare a cluster to a different cluster and call the difference a
       deviation.

    2. The checker prints WHICH published row each reconstructed row matched
       to, and how strongly. S2's verification script reported 19 mismatches
       and then 5, all of them its own scoping bugs and none of them real. A
       checker that cannot show the row it thinks it found has not found it.

    Run:  python verify_s0.py
    Out:  s0_verification.json  + a table on stdout
'''

import json
import os

PUB_RESULTS = "_published_results.json"
PUB_CONTROLS = "_published_controls_results.json"
NEW_RESULTS = "results_recon.json"
NEW_CONTROLS = "controls_results_recon.json"
NULL_MODEL = "null_model.json"
OUT = "s0_verification.json"


def jaccard(a, b):
    a, b = set(a), set(b)
    return len(a & b) / max(len(a | b), 1)


def match(pub_comms, new_comms, key="titles"):
    '''Greedy best-Jaccard pairing, strongest pair first, so one strong match
    cannot be stolen by a weaker row processed earlier.'''
    pairs = []
    for i, p in enumerate(pub_comms):
        for j, n in enumerate(new_comms):
            pairs.append((jaccard(p.get(key, []), n.get(key, [])), i, j))
    pairs.sort(reverse=True)
    used_p, used_n, out = set(), set(), []
    for score, i, j in pairs:
        if i in used_p or j in used_n or score == 0:
            continue
        used_p.add(i)
        used_n.add(j)
        out.append((i, j, score))
    for i in range(len(pub_comms)):
        if i not in used_p:
            out.append((i, None, 0.0))
    return sorted(out)


def fmt(v):
    return "--" if v is None else str(v)


def main():
    report = {"targets": [], "communities": {}, "unmatched": {}}

    def target(name, published, got, tol=0):
        ok = (got is not None
              and abs(float(got) - float(published)) <= tol)
        report["targets"].append({"figure": name, "published": published,
                                  "reconstructed": got, "tolerance": tol,
                                  "reproduced": bool(ok)})
        mark = "MATCH" if ok else "DIFFERS"
        print(f"  {name:34s} published {fmt(published):>10}   "
              f"got {fmt(got):>10}   {mark}")

    pub_r = json.load(open(PUB_RESULTS, encoding="utf-8"))
    pub_c = json.load(open(PUB_CONTROLS, encoding="utf-8"))
    new_r = json.load(open(NEW_RESULTS, encoding="utf-8")) \
        if os.path.isfile(NEW_RESULTS) else None
    new_c = json.load(open(NEW_CONTROLS, encoding="utf-8")) \
        if os.path.isfile(NEW_CONTROLS) else None
    null = json.load(open(NULL_MODEL, encoding="utf-8")) \
        if os.path.isfile(NULL_MODEL) else None

    print("\n=== headline figures ===")
    target("corpus size (books)", pub_c["n_books"],
           new_c["n_books"] if new_c else None)
    target("corpus size (authors)", pub_c["n_authors"],
           new_c["n_authors"] if new_c else None)
    target("one-per-author subset", pub_c["n_one_per_author"],
           new_c["n_one_per_author"] if new_c else None)
    target("author confound %", pub_c["author_confound_pct"],
           new_c["author_confound_pct"] if new_c else None)

    if new_r:
        for k in ("births", "splits", "merges"):
            target(f"timeline {k}", sum(t[k] for t in pub_r["timeline"]),
                   sum(t[k] for t in new_r["timeline"]))
        target("timeline mutations (total)",
               sum(t["mutations"] for t in pub_r["timeline"]),
               sum(t["mutations"] for t in new_r["timeline"]))

    nm = pub_r["honest_metrics"]["null_model"]
    if null:
        target("null: real mutations", nm["real_total_mutations"],
               null["real_total_mutations"])
        target("null: shuffled mean", nm["shuffled_mean"], null["shuffled_mean"])
        target("null: shuffled std", nm["shuffled_std"], null["shuffled_std"])
        target("null: z", nm["z"], null["z"])

    # --- the controlled communities, matched by membership -------------------
    if new_c:
        print("\n=== controlled communities (matched by title overlap) ===")
        print(f"  {'published':38s} -> {'reconstructed':38s}  jacc")
        pairs = match(pub_c["communities"], new_c["communities"])
        rows = []
        for i, j, s in pairs:
            p = pub_c["communities"][i]
            n = new_c["communities"][j] if j is not None else None
            plabel = f"z={p['concentration_z']:+.2f} n={p['n']:>2} " \
                     f"{p['year_min']}-{p['year_max']} std={p['year_std']}"
            nlabel = (f"z={n['concentration_z']:+.2f} n={n['n']:>2} "
                      f"{n['year_min']}-{n['year_max']} std={n['year_std']}"
                      if n else "NO MATCH")
            print(f"  {plabel:38s} -> {nlabel:38s}  {s:.2f}")
            print(f"      {str(p['held_out_label'])[:34]:34s}     "
                  f"{str(n['held_out_label'])[:34] if n else '':34s}")
            rows.append({
                "published": {k: p.get(k) for k in
                              ("n", "year_min", "year_max", "year_std",
                               "concentration_z", "held_out_label", "top_terms")},
                "reconstructed": ({k: n.get(k) for k in
                                   ("n", "year_min", "year_max", "year_std",
                                    "concentration_z", "held_out_label",
                                    "top_terms")} if n else None),
                "title_jaccard": round(s, 3),
            })
        report["communities"]["controls"] = rows

        det = [r for r in pub_c["communities"]
               if r["held_out_label"] == "Detective and mystery stories"]
        if det:
            i = pub_c["communities"].index(det[0])
            j = next((j for a, j, _ in pairs if a == i), None)
            m = new_c["communities"][j] if j is not None else None
            print("\n=== the one positive result ===")
            target("detective n", det[0]["n"], m["n"] if m else None)
            target("detective year_min", det[0]["year_min"],
                   m["year_min"] if m else None)
            target("detective year_max", det[0]["year_max"],
                   m["year_max"] if m else None)
            target("detective year_std", det[0]["year_std"],
                   m["year_std"] if m else None)
            target("detective z", det[0]["concentration_z"],
                   m["concentration_z"] if m else None)

    # --- the final communities from results.json -----------------------------
    if new_r:
        print("\n=== results.json communities (matched by title overlap) ===")
        pairs = match(pub_r["communities"], new_r["communities"])
        rows = []
        for i, j, s in pairs:
            p = pub_r["communities"][i]
            n = new_r["communities"][j] if j is not None else None
            print(f"  [{p['size']:>3}] {str(p['genre_name'])[:26]:26s} "
                  f"{p['year_min']}-{p['year_max']} -> "
                  f"{('[' + str(n['size']).rjust(3) + '] ' + str(n['year_min']) + '-' + str(n['year_max'])) if n else 'NO MATCH':22s}"
                  f"  jacc {s:.2f}")
            rows.append({"published_size": p["size"],
                         "published_label": p["held_out_label"],
                         "reconstructed_size": n["size"] if n else None,
                         "title_jaccard": round(s, 3)})
        report["communities"]["results"] = rows

    n_ok = sum(1 for t in report["targets"] if t["reproduced"])
    print(f"\n{n_ok}/{len(report['targets'])} headline figures reproduced exactly.")
    json.dump(report, open(OUT, "w", encoding="utf-8"), indent=2)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
