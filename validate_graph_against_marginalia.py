'''
    Author: Aidan Jude

    S7b — a THIRD held-out validation source for the Phase 2 influence
    graph, and the first one that is not an interpretation.

    build_influence_graph.py already validates its author-similarity graph
    against two held-out sources, and both answer the same question —
    *who does the record say influenced whom*:

        known_influences.json      377 relationships, LLM-enumerated,
                                   130 pairs land in the graph
        wikidata_influences.json   350 Wikidata P737 claims,
                                   102 pairs land in the graph

    vendor/marginalia answers a different question — *who demonstrably read
    whom* — from physical marks in surviving copies. Same permutation
    z-test, same null (random pairs at the same chronological gap), so the
    three are directly comparable.

    THE CONFOUND THAT INVALIDATES THE NAIVE VERSION, found 2026-08-27 by
    printing the pairs instead of trusting the z. Against the graph-wide
    null the numbers looked excellent — reference edges z = 4.73, beating
    both existing sources. Then: **all 21 reference pairs are
    Nietzsche->X, and all 6 heavy-mark pairs are Melville->X.** The whole
    "finding" was one author's position in the graph. That is Phase 1's
    author-voice confound with a single endpoint instead of a prolific one,
    and a graph-wide null cannot see it.

    So the reported test is WITHIN-READER: hold the reader fixed and ask
    whether the authors he demonstrably read are more similar to him than
    the authors in the same graph he did not. Every pair in both the real
    set and the null then shares one endpoint, which removes the reader's
    global position, the German-philosophy register, and the density bias
    (reference pairs average 4.95 books/author against 4.2 graph-wide) in
    one move. The graph-wide numbers are still emitted, labelled
    `graph_wide_null_CONFOUNDED`, so the contrast is on the record.

    THE HONEST HEADLINE IS THE SAMPLE SIZE. The graph has 77 authors; the
    marginalia corpus has 2,139. Their intersection is small, so only a
    couple of dozen marginalia edges have BOTH ends in the graph. This test
    is therefore underpowered by construction and reported as such. That is
    not a defect in the corpus — it is the graph's 77-author corpus that
    binds, and this measurement is the argument for widening it.

    In:   _data/influence_graph.json, vendor/marginalia/_data/edges.json
    Out:  _data/marginalia_validation.json
'''

import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
GRAPH = os.path.join(HERE, "_data", "influence_graph.json")
EDGES = os.path.join(HERE, "vendor", "marginalia", "_data", "edges.json")
OUT = os.path.join(HERE, "_data", "marginalia_validation.json")
SEED = 20260827
N_NULL = 2000
GAP_TOL = 25          # years; the null draws pairs at a comparable gap


def within_reader(reader, read_authors, sims, years, rng, key):
    '''
        THE valid test. Fix the reader; the null is every other author in
        the graph that this same reader could have read and did not, drawn
        to the same sample size. Both sides share one endpoint, so the
        reader's own position in the graph cancels.
    '''
    def edge(a, b):
        lo, hi = (a, b) if years[a] <= years[b] else (b, a)
        return sims.get((lo, hi))

    real = [edge(reader, a)[key] for a in read_authors if edge(reader, a)]
    if len(real) < 5:
        return None
    pool = [a for a in years
            if a != reader and a not in read_authors and edge(reader, a)]
    if len(pool) < len(real) * 2:
        return None
    real_mean = sum(real) / len(real)
    nulls = []
    for _ in range(N_NULL):
        pick = rng.sample(pool, len(real))
        nulls.append(sum(edge(reader, a)[key] for a in pick) / len(pick))
    mu = sum(nulls) / len(nulls)
    sd = (sum((x - mu) ** 2 for x in nulls) / max(1, len(nulls) - 1)) ** 0.5
    return dict(reader=reader, n_read=len(real), n_not_read=len(pool),
                read_mean=round(real_mean, 4), not_read_mean=round(mu, 4),
                null_std=round(sd, 4),
                z=round((real_mean - mu) / sd, 3) if sd else None,
                p=round((sum(1 for x in nulls if x >= real_mean) + 1) / (len(nulls) + 1), 4))


def permutation(pairs, sims, years, rng, key):
    '''
        Mirrors build_influence_graph.py's held-out check: compare the mean
        similarity of the real pairs against random pairs drawn at a
        comparable chronological gap, so a result cannot be an artifact of
        authors simply being close in time.
    '''
    real = [sims[p][key] for p in pairs if p in sims]
    if len(real) < 3:
        return None
    real_mean = sum(real) / len(real)
    gaps = [abs(years[a] - years[b]) for a, b in pairs if (a, b) in sims]
    allpairs = list(sims)
    nulls = []
    for _ in range(N_NULL):
        draw = []
        for g in gaps:
            pool = [p for p in allpairs if abs(abs(years[p[0]] - years[p[1]]) - g) <= GAP_TOL]
            if pool:
                draw.append(sims[rng.choice(pool)][key])
        if draw:
            nulls.append(sum(draw) / len(draw))
    mu = sum(nulls) / len(nulls)
    sd = (sum((x - mu) ** 2 for x in nulls) / max(1, len(nulls) - 1)) ** 0.5
    return dict(n_pairs=len(real), real_mean=round(real_mean, 4),
                null_mean=round(mu, 4), null_std=round(sd, 4),
                z=round((real_mean - mu) / sd, 3) if sd else None,
                p=round((sum(1 for x in nulls if x >= real_mean) + 1) / (len(nulls) + 1), 4))


def main():
    rng = random.Random(SEED)
    g = json.load(open(GRAPH))
    years = {a["name"]: a["earliest_year"] for a in g["authors"]}
    sims = {}
    for e in g["edges"]:
        sims[(e["from"], e["to"])] = dict(stylistic=e["stylistic"], conceptual=e["conceptual"])

    d = json.load(open(EDGES))
    known = set(years)

    def in_graph(pairs):
        # The graph permits an edge only when the earlier author's first work
        # predates the later's, so orient each reading pair by chronology
        # rather than by who did the reading.
        out = []
        for a, b in pairs:
            if a not in known or b not in known or a == b:
                continue
            lo, hi = (a, b) if years[a] <= years[b] else (b, a)
            if (lo, hi) in sims:
                out.append((lo, hi))
        return sorted(set(out))

    mark_pairs = in_graph([(e["source_author"], e["reader"]) for e in d["edges"]])
    ref_pairs = in_graph([(e["target_author"], e["reader"]) for e in d["reference_edges"]])
    heavy = in_graph([(e["source_author"], e["reader"]) for e in d["edges"]
                      if e["n_marks"] >= 50])

    # ---- the valid test: one reader at a time ----
    read_by = {}
    for e in d["edges"]:
        if e["reader"] in known and e["source_author"] in known:
            read_by.setdefault(e["reader"], set()).add(e["source_author"])
    named_by = {}
    for e in d["reference_edges"]:
        if e["reader"] in known and e["target_author"] in known:
            named_by.setdefault(e["reader"], set()).add(e["target_author"])

    per_reader = {}
    for label, table in (("marked", read_by), ("named", named_by)):
        for reader, authors in sorted(table.items()):
            for key in ("stylistic", "conceptual"):
                r = within_reader(reader, authors, sims, years, rng, key)
                if r:
                    per_reader.setdefault(f"{reader} :: {label}", {})[key] = r

    payload = dict(
        note=("A third held-out source for Phase 2, and the only non-interpretive one. "
              "Same permutation test as build_influence_graph.py's two existing checks, "
              "so the three z-scores are comparable."),
        seed=SEED, n_null=N_NULL, gap_tolerance_years=GAP_TOL,
        graph_authors=len(known),
        marginalia_source_authors=len({e["source_author"] for e in d["edges"]}),
        overlap_readers=sorted({e["reader"] for e in d["edges"]} & known),
        power_caveat=("Underpowered by construction. The graph has 77 authors against the "
                      "corpus's 2,139, so only a couple of dozen reading edges have both "
                      "ends in the graph. Compare n_pairs against the 130 and 102 of the "
                      "existing two sources before reading anything into a z."),
        existing_for_comparison=dict(
            llm_enumerated=g["held_out_validation"],
            wikidata_p737=g["held_out_validation_wikidata"],
        ),
        within_reader=per_reader,
        within_reader_note=("THE VALID TEST. Reader held fixed; the null is authors in "
                            "the same graph that reader did not read. Removes the "
                            "single-reader artifact that made the graph-wide numbers "
                            "below look strong."),
        graph_wide_null_CONFOUNDED=("Every pair in marginalia_references is "
                                    "Nietzsche->X and every pair in "
                                    "marginalia_marks_50_plus is Melville->X, so these "
                                    "z-scores measure one author's position in the "
                                    "graph, not the evidence class. Kept for contrast."),
        marginalia_marks=dict(n_pairs_found=len(mark_pairs), pairs=mark_pairs,
                              stylistic=permutation(mark_pairs, sims, years, rng, "stylistic"),
                              conceptual=permutation(mark_pairs, sims, years, rng, "conceptual")),
        marginalia_marks_50_plus=dict(
            n_pairs_found=len(heavy), pairs=heavy,
            note="only pairs with 50+ marks -- attribution has no weight, this does",
            stylistic=permutation(heavy, sims, years, rng, "stylistic"),
            conceptual=permutation(heavy, sims, years, rng, "conceptual")),
        marginalia_references=dict(n_pairs_found=len(ref_pairs), pairs=ref_pairs,
                                   stylistic=permutation(ref_pairs, sims, years, rng, "stylistic"),
                                   conceptual=permutation(ref_pairs, sims, years, rng, "conceptual")),
    )
    json.dump(payload, open(OUT, "w"), indent=1)

    print(f'graph authors {len(known)}  |  marginalia readers in graph: '
          f'{", ".join(payload["overlap_readers"])}\n')
    print("WITHIN-READER (the valid test): are the authors a reader demonstrably")
    print("read more similar to him than the graph authors he did not read?\n")
    print(f'{"reader :: evidence":<34} {"read":>5} {"not":>5} {"styl z":>8} {"styl p":>8} '
          f'{"conc z":>8} {"conc p":>8}')
    for k, v in sorted(per_reader.items()):
        st, co = v.get("stylistic", {}), v.get("conceptual", {})
        print(f'{k:<34} {st.get("n_read", "-"):>5} {st.get("n_not_read", "-"):>5} '
              f'{str(st.get("z")):>8} {str(st.get("p")):>8} '
              f'{str(co.get("z")):>8} {str(co.get("p")):>8}')
    print("\nGRAPH-WIDE null -- CONFOUNDED, single-reader; kept only for contrast:")
    rows = [("LLM-enumerated (existing)", g["held_out_validation"]),
            ("Wikidata P737 (existing)", g["held_out_validation_wikidata"]),
            ("marginalia: marks", payload["marginalia_marks"]),
            ("marginalia: 50+ marks", payload["marginalia_marks_50_plus"]),
            ("marginalia: references", payload["marginalia_references"])]
    print(f'{"evidence source":<28} {"n":>4} {"styl z":>8} {"styl p":>8} {"conc z":>8} {"conc p":>8}')
    for name, r in rows:
        st, co = r.get("stylistic") or {}, r.get("conceptual") or {}
        print(f'{name:<28} {st.get("n_pairs", 0):>4} {str(st.get("z")):>8} '
              f'{str(st.get("p", "-")):>8} {str(co.get("z")):>8} {str(co.get("p", "-")):>8}')


if __name__ == "__main__":
    main()
