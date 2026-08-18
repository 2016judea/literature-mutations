'''
    Author: Aidan Jude
    S0 addendum: rebuild the null model, because the code that produced it is
    not in this repository.

    results.json carries an `honest_metrics` block - the per-book rate by era
    and the shuffled null (90 real events vs 94.1 +/- 15.2, z = -0.27). That
    block is the basis of the README's central negative claim and of the null
    figures typed onto the live site. But `grep -rn honest_metrics *.py` finds
    only a READER (animate_genre_growth.py:195). No script in the checkout
    writes it. So the corpus was not the only thing missing: the script that
    produced two of the five published headline numbers is gone too.

    This is a RECONSTRUCTION of that procedure, not a recovery of it. The
    procedure is forced by the numbers it has to produce:

      * real_total_mutations = 90. That is exactly sum(timeline.mutations) in
        the published results.json (births 32 + splits 33 + merges 25), so the
        real arm is just analyze.py's timeline, summed.
      * the null shuffles CHRONOLOGY and nothing else. The claim being tested
        is "mutation events are driven by when books were published"; the
        matching null therefore permutes publication years across books,
        holding the texts and the corpus size fixed, and re-runs the identical
        timeline. Any other shuffle (of texts, or of community labels) would
        be testing a different sentence.

    Because it is a reconstruction, agreement with 94.1 +/- 15.2 is evidence
    that this is the original procedure; disagreement is NOT evidence that the
    original was wrong. Reported both ways in docs/S0-CORPUS-RECONSTRUCTION.md.

    Run:  python null_model.py [--trials 200] [--out null_model.json]
'''

import argparse
import json
import os

import numpy as np

import temporal_network as tn
from semantic_edges import attach_embeddings


def flat(b):
    return {"title": b["title"], "date_published": b["date_published"],
            "genres": list(b.get("genres") or []), "description": b["description"]}


def total_mutations(books):
    grouped = tn.books_by_year([flat(b) for b in books])
    tl = tn.mutation_timeline(grouped)
    return (sum(r["mutations"] for r in tl),
            {k: sum(r[k] for r in tl) for k in ("births", "splits", "merges")})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=200)
    ap.add_argument("--books", default=os.path.join(tn.shelved_books, "books.json"))
    ap.add_argument("--out", default="null_model.json")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    tn.EDGE_METHOD = "semantic"
    books = json.load(open(args.books, encoding="utf-8"))["books"]
    attach_embeddings(books)
    print(f"Corpus: {len(books)} books")

    real, parts = total_mutations(books)
    print(f"Real: {real} mutations  {parts}")

    years = [b["date_published"] for b in books]
    rng = np.random.default_rng(args.seed)
    draws = []
    for i in range(args.trials):
        perm = rng.permutation(len(books))
        shuffled = []
        for b, j in zip(books, perm):
            c = dict(b)
            c["date_published"] = years[j]      # chronology permuted, text fixed
            shuffled.append(c)
        t, _ = total_mutations(shuffled)
        draws.append(t)
        print(f"  trial {i + 1}/{args.trials}: {t}   "
              f"running mean {np.mean(draws):.1f}", end="\r")

    mean, std = float(np.mean(draws)), float(np.std(draws))
    z = (real - mean) / std if std else 0.0
    out = {
        "real_total_mutations": real,
        "real_parts": parts,
        "shuffled_mean": round(mean, 1),
        "shuffled_std": round(std, 1),
        "z": round(z, 2),
        "trials": args.trials,
        "shuffled_draws": draws,
        "note": "Reconstructed procedure - the original producer of "
                "results.json.honest_metrics is not in the repository.",
    }
    json.dump(out, open(args.out, "w"), indent=2)
    print(f"\nReal {real} vs shuffled {mean:.1f} +/- {std:.1f}  z = {z:+.2f}")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
