'''
    Author: Aidan Jude
    S0 addendum: is a difference in the event counts a finding, or is it noise?

    The reconstruction returns 82 mutations where the published run returned
    90. Before that can be called a deviation, one thing has to be ruled out:
    that the statistic simply is not stable enough for 82 and 90 to be
    different numbers.

    temporal_network.py re-runs Louvain from scratch on every cumulative
    snapshot and matches communities across years by Jaccard >= 0.3. Louvain
    re-partitions the WHOLE graph, so its random seed decides which
    communities are judged to persist - and therefore how many births, splits
    and merges get counted. The seed was hardcoded to 42, which turned a
    distribution into a point estimate.

    This runs the identical timeline across N seeds on ONE fixed corpus. The
    corpus does not change, so every bit of spread here is the instrument.

    docs/RESEARCH-PROGRAM.md S3 asks for exactly this as a cheap control:
    "if the +/- spread across seeds swamps the 90-vs-94 null-model gap, that
    alone explains the null."

    Run:  python seed_sweep.py [--seeds 12] [--books _data/books.json]
    Out:  seed_sweep.json
'''

import argparse
import json
import os

import numpy as np

import temporal_network as tn
from semantic_edges import attach_embeddings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=12)
    ap.add_argument("--books", default=os.path.join(tn.shelved_books, "books.json"))
    ap.add_argument("--out", default="seed_sweep.json")
    args = ap.parse_args()

    tn.EDGE_METHOD = "semantic"
    books = json.load(open(args.books, encoding="utf-8"))["books"]
    attach_embeddings(books)
    flat = [{"title": b["title"], "date_published": b["date_published"],
             "genres": list(b.get("genres") or []),
             "description": b["description"]} for b in books]
    grouped = tn.books_by_year(flat)
    print(f"{len(books)} books, sweeping {args.seeds} Louvain seeds "
          f"on one fixed corpus")

    rows = []
    for seed in range(args.seeds):
        tn.LOUVAIN_SEED = seed
        tl = tn.mutation_timeline(grouped)
        row = {"seed": seed,
               **{k: sum(r[k] for r in tl)
                  for k in ("births", "splits", "merges", "mutations")},
               "n_communities_final": tl[-1]["n_communities"]}
        rows.append(row)
        print(f"  seed {seed:2d}: births {row['births']:3d}  "
              f"splits {row['splits']:3d}  merges {row['merges']:3d}  "
              f"total {row['mutations']:3d}  "
              f"final communities {row['n_communities_final']}")

    out = {"n_books": len(books), "seeds": args.seeds, "runs": rows}
    for k in ("births", "splits", "merges", "mutations", "n_communities_final"):
        v = np.array([r[k] for r in rows], float)
        out[k] = {"mean": round(float(v.mean()), 1),
                  "std": round(float(v.std()), 1),
                  "min": int(v.min()), "max": int(v.max())}
        print(f"{k:20s} {out[k]['mean']:6.1f} +/- {out[k]['std']:.1f}   "
              f"range {out[k]['min']}-{out[k]['max']}")
    json.dump(out, open(args.out, "w"), indent=2)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
