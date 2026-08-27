# S1 — does the sampling frame explain detective fiction?

Run 2026-08-26. Brief: [`RESEARCH-PROGRAM.md`](RESEARCH-PROGRAM.md) § S1,
addressing **P1** — `build_canon.py` recruits from 14 buckets, four of which
name a genre, so a project claiming genre structure is recoverable *from prose
alone* partly selected its corpus **by genre**.

---

## Verdict

**Detective fiction's concentration is sampling-independent up to 4 of its 13
books removed adversarially. P1 cannot explain the finding.**

At **k = 4** the *worst possible* removal still gives **z = −2.15**, clearing the
−2.0 emergence threshold by **3.3 Monte-Carlo sigma** of the estimator's own
noise. The worst case first crosses at **k = 5** (z = −1.97, a margin of −0.03,
i.e. −0.7σ) — and even there **99% of the 1,287 possible 5-book removals still
survive**. So the k = 5 failure is a single adversarial corner, not the typical
outcome.

Since only **one** of the four genre-named buckets is the detective bucket, a
removal large enough to break the finding would require that bucket to have
been the sole route of entry for 5 of the 13 books *and* for those 5 to be
exactly the worst-case set. That is a much stronger claim than P1 makes.

**Drift check: passes, no halt.** The published z = −3.04 sits **0.7σ** from the
20-seed mean of **−3.011 ± 0.045**. The number reproduces.

| k removed | combinations | z worst case | margin to −2.0 | in MC σ | z median | z best |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 1 | −2.96 | 0.96 | 21.2 | −2.96 | −2.96 |
| 1 | 13 | −2.81 | 0.81 | 17.9 | −2.84 | −3.08 |
| 2 | 78 | −2.62 | 0.62 | 13.7 | −2.70 | −3.11 |
| 3 | 286 | −2.41 | 0.41 | 9.1 | −2.54 | −3.13 |
| **4** | **715** | **−2.15** | **0.15** | **3.3** | −2.32 | −2.92 |
| 5 | 1,287 | −1.97 | −0.03 | −0.7 | −2.21 | −2.82 |
| 6 | 1,716 | −1.74 | −0.26 | −5.8 | −2.02 | −2.70 |

### The worst case runs *against* P1's own mechanism

The 5-book removal that breaks the finding is not an arbitrary set. It is:

> *The Red Thumb Mark* (1907), *The Mystery of the Yellow Room* (1907),
> *The Circular Staircase* (1908), *Trent's Last Case* (1913), *The Cask* (1920)

— five of the six **latest** books in the community, whose full range is
1878–1926. Deleting the 20th-century tail widens the year spread, which is
mechanically the fastest way to destroy concentration.

But P1's mechanism points the other way. A bucket asking for *"foundational
detective and mystery novels in English before 1929"* recruits the **early**
canonical ones — *The Leavenworth Case* (1878), *A Study in Scarlet* (1887),
*The Big Bow Mystery* (1892) — not Freeman, Leroux, Bentley and Crofts. So the
removal that would break the result is close to the **opposite** of the removal
the sampling bias would actually produce. The adversarial bound is therefore
conservative here by a wide margin: it reports the worst case while the
plausible case is better still.

---

## Why this does not follow the brief's method

The brief's step 2 recovers provenance by re-running the four genre-bucket
prompts against two non-deterministic LLMs and intersecting the returned titles
with the known 345. Sound, and it was the right plan when written. It has three
costs:

1. **It spends money** on two model families.
2. **It is not reproducible.** Two non-deterministic LLMs return a different
   answer next time, so the audit could not be re-run to check.
3. **It measures today's models, not the ones that built the corpus.** A title
   the current models omit would read as "did not enter via a genre bucket" when
   it may well have. The false-negative direction *flatters* the finding, which
   is the worst direction for an audit to be wrong in.

**The adversarial bound answers the same question and has none of those costs.**
If the concentration survives the worst possible removal of k member books, it
survives *every actual provenance assignment* of k books, because the worst case
dominates all of them. The conclusion is reached without ever learning the
provenance. The community has 13 members, so every removal up to k = 6 is
enumerated **exhaustively** — 1,716 combinations at k = 6, no sampling, no seed,
no model.

**The permanent fix landed anyway**, as the brief requires regardless of what
the audit found: [`build_canon.py:154`](../build_canon.py#L154) now persists
`"lists": sorted(rec["lists"])` alongside the count. The set was being built at
line 137 and thrown away at write time, which is exactly why the audit could not
be run directly — and the reconstructed `_data/canon.json` carries no provenance
at all, because S0 rebuilt from the surviving title list rather than from lists.

---

## Two methodological choices, both stated

**Membership removal, not a full corpus re-run.** The brief says "re-run the
concentration test excluding" those titles, which admits two readings:

- **(a) Done here.** Drop the books from the community and recompute z against a
  frame that also loses them — a removed book leaves both the numerator and the
  null's denominator. Leaving it in the denominator would flatter the result.
- **(b) Not done.** Drop from the corpus and rebuild the k-NN graph and Louvain
  partition. S0 measured that changing *only* the Louvain seed on a **fixed**
  corpus moves the mutation total by ±7.6 and renumbers communities. A 4-book
  perturbation would therefore mostly measure Louvain noise, not sampling.
  Reported as uninterpretable rather than run and believed.

**That (b) is uninterpretable is itself an argument for S3.** The instrument
cannot currently answer a question this small.

**The estimator's own noise is measured, not assumed.** `concentration_z` is a
Monte-Carlo statistic over 3,000 random same-size draws. A bound clearing the
threshold by less than the estimator's noise has not cleared it. Over 20 seeds on
the full community: **mean −3.011, sd 0.045**. Every row above therefore reports
its margin in MC sigma, and the failure rule is *worst case crosses −2.0 **or**
its margin falls under 2σ* — which is why the verdict says k = 4 and not k = 5.

**Identified by vocabulary, never by label.** S2's lesson 1: three of the eight
held-out labels name a genre their own cluster is not, and dating a cluster by
its label instead of its `top_terms` moves the answer +62 to +142 years. The
detective community is located here by `detective inspector murderer police`.
If no community had carried detective vocabulary the script reports and stops
rather than substituting the label.

---

## The eight controlled communities, as reproduced

| z | n | years | top terms |
|---:|---:|---|---|
| **−3.04** | 13 | 1878–1926 | detective inspector murderer police |
| −1.72 | 19 | 1759–1925 | ain dollars em rifle |
| −0.83 | 18 | 1794–1923 | incredible humanity laboratory dr |
| −0.59 | 25 | 1740–1928 | mary em baby aunt |
| −0.23 | 25 | 1764–1925 | madame castle prince duke |
| +0.39 | 15 | 1719–1915 | deck voyage mate sail |
| +0.59 | 24 | 1678–1915 | mountain mountains rock tribes |
| +0.98 | 27 | 1719–1923 | ladyship madam aunt lordship |

Note the calibration the brief already flagged and this run confirms: **three of
the four genre-named buckets produced perennial communities** — the
science-fiction-vocabulary cluster at −0.83, the sea/adventure cluster at +0.39,
the historical/aristocratic cluster at −0.23. A genre bucket does not
mechanically manufacture temporal concentration. P1 was worth auditing because
n = 13, not because it was likely to be the explanation.

---

## Artifacts

- `s1_provenance_bound.py` — the bound, importing `controls.py`'s own `tfidf`,
  `detrend_years`, `knn_graph` and `concentration_z` so the numbers are the
  published ones rather than a near-miss.
- `s1_provenance_bound.json` — the full bound, all eight communities, the MC
  noise measurement, and the worst-case title set at every k.
- [`build_canon.py:154`](../build_canon.py#L154) — provenance now persisted for
  every future corpus build.
