# S0 — Corpus reconstruction and re-verification

Run 2026-08-18. Brief: [`RESEARCH-PROGRAM.md`](RESEARCH-PROGRAM.md) § S0.

---

## Verdict

**Yes for the finding. No for the instrument.**

The one thing the project actually claims — that detective fiction is a datable
genre emergence and the other seven modes are perennial — **reproduces exactly**,
from a corpus rebuilt out of published artifacts on a machine that had lost the
original. Every other published figure is either an arbitrary tie-break or a
number the instrument cannot resolve, and S0 measured how badly.

| figure | published | reconstructed | |
|---|---|---|---|
| **detective n** | 13 | **13** | ✅ |
| **detective years** | 1878–1926 | **1878–1926** | ✅ |
| **detective year_std** | 14.9 | **14.9** | ✅ |
| **detective z** | **−3.04** | **−3.04** | ✅ |
| detective top terms | 6 terms | same 6 | ✅ |
| authors | 166 | 166 | ✅ |
| one-per-author subset | 166 | 166 | ✅ |
| emergent communities (z ≤ −2) | detective only | detective only | ✅ |
| corpus size | 345 | 343 | 2 books short |
| author confound | 19.5 % | 20.7 % | +1.2 pp |
| births / splits / merges | 32 / 33 / 25 | 34 / 31 / 23 | inside seed noise |
| total mutations | 90 | 88 | inside seed noise |
| null model | 90 vs 94.1 ± 15.2, z = −0.27 | 88 vs 102.2 ± 17.5, z = −0.82 | same conclusion, different numbers |

Reproduce with `python verify_s0.py`; the table is written to
`s0_verification.json`.

**Per the drift rule, the numbers stop here.** Nothing in the README, the site or
`results.json` has been changed, and the reconstruction is *not* proposed as a new
ground truth. What follows is the delta and its causes, for Aidan to call.

---

## The one number that matters, and why it is trustworthy

Detective fiction returns `n=13, 1878–1926, std 14.9, z=−3.04` — the published
row to the decimal, with an identical top-terms list.

That is a stronger result than it looks, because it survived a reconstruction
that got other things wrong. Along the way this session filed Haggard's *She*
under Conan Doyle, *The Rainbow* under Samuel Johnson, and eight of the 166
controlled books were briefly the wrong book by the same author. The detective
row was unmoved by the corpus being 2 books short and by 177 of 343 publication
years coming from a different source than the original. A result that indifferent
to its inputs is one worth defending in a paper.

It also now has two independent legs. S2 licensed it externally — the *name*
"detective story" takes off in 1889 against books of 1878–1926
([`S2-RECEPTION-CLOCK.md`](S2-RECEPTION-CLOCK.md)). S0 licenses it internally:
the number regenerates from scratch.

---

## What was actually recoverable, and how

`_data/books.json` and `_data/canon.json` were never committed. Recovered from:

- **`results.json` → `communities[].titles`** — all 345 titles.
- **`genre_network.html` → `const DATA`** — 166 of them with author and year,
  parsed with the existing `extract_data()` per the brief.

**The constraint that made the other 179 tractable.** `controls.py` keeps one book
per author (the earliest), and those 166 books carry 166 *distinct* authors. So
the 166 are a complete cover of the corpus's author set, and every missing title
must be by an author already on that list. Author resolution became constrained
matching rather than open search: **178 of 179 resolved off Gutendex**, and any
result landing outside the 166 was by definition an error rather than a discovery.

`build_canon.py` was never run. Two non-deterministic LLMs would have returned a
different canon.

### Pipeline

```
reconstruct_canon.py   345 titles + 166 known -> _data/canon.json  (343)
build_corpus.py        canon -> real Gutenberg text
retry_missing_text.py  the tail that failed on download, not on matching
harmonize_corpus.py    one work, one date
corpus_manifest.py     sha256 per book + edition-drift measurement
controls.py / analyze.py / null_model.py / seed_sweep.py
verify_s0.py           the diff
```

Every raw pull is committed — `recon_raw_gutendex.json`,
`recon_raw_openlibrary.json`, `recon_raw_ol_title.json`, `recon_overrides.json` —
so the next session verifies rather than re-fetches. Phase 1 is now committed like
Phase 2, which closes the housekeeping item in the brief.

---

## Every deviation, with its cause

### 1. Two books short (343 vs 345)

- **`Death Comes for the Archbishop`** — Gutenberg has it (id 69730), but Open
  Library dates it **1732** for a novelist born in 1873. No prescribed source
  yields a usable year. Left out rather than hand-typed.
- **`The Singing Bone`** — Open Library returns 1900 against R. Austin Freeman's
  earliest-in-corpus 1907, which is provably impossible (see §3). Dropped rather
  than admitted with a year known to be wrong.

Both are logged in `_data/recon_log.json`.

### 2. Years are the weak seam — 64.8 % exact, mean |error| 2.5 years

The 166 known years double as a calibration set for the source used on the other
177. Open Library reproduces them **exactly 64.8 % of the time**, within 2 years
79.6 %, mean absolute error 2.5 years.

That is the honest ceiling of the method the brief prescribes, and the reason is
not a bug: `build_canon.py` took its years from **LLM consensus on "first
publication"**, while Open Library reports `first_publish_year` from its edition
records. Different quantities. No configuration of Open Library will reproduce
the original years.

It began far worse — mean error **16.9 years**, with *Treasure Island* at 1781 and
*The Jungle Book* at 1740 — because the first pass floored the year search at 1660
instead of at the author's birth + 15, which is what `gutenberg_ingest.py` already
did. Restoring the reference implementation's floor and adding three filters
(title must match, collected-works records dropped, an exact century loses to any
non-round candidate) took it to 2.5 years. Each filter was measured against the
166 before adoption; details in `pick_year()`.

### 3. The controlled subset: 160 of 166 exact, 6 arbitrary ties

`n_one_per_author` is 166 on the nose, and 160 of the titles are the published
ones. **All six differences are exact-year ties** broken by iteration order —
and three of those are the same text under two titles:

| published | reconstructed | why |
|---|---|---|
| Frankenstein; or, The Modern Prometheus (1818) | Frankenstein (1818) | same book, both titles in the published 345 |
| The Adventures of Roderick Random (1748) | Roderick Random (1748) | same book, ditto |
| Wieland; or, The Transformation (1798) | Wieland (1798) | same book, ditto |
| Agnes Grey (1847) | The Tenant of Wildfell Hall (1847) | tie |
| Clementina (1901) | The Four Feathers (1901) | tie |
| This Side of Paradise (1920) | The Great Gatsby (1920) | tie |

The published pick is as arbitrary as ours in every row.

**This only worked after adding a floor that the published data proves.** Because
the 166 are the earliest book per author, no other book by that author can
predate it. Open Library's error skews *early*, so without that floor the
too-early years displaced the real earliest book — Huckleberry Finn came back as
1875 and took *Tom Sawyer*'s place as Twain's earliest, Jekyll and Hyde as 1875
took *Treasure Island*'s, Kenilworth as 1798 took *Waverley*'s. **Eight of the
166 controlled books were the wrong book for that reason alone**, and the
detective row still came out at z = −2.97 while they were. With the floor it is
−3.04.

### 4. The Louvain counts differ, and cannot not differ

Published 32/33/25 (90 total); reconstructed 34/31/23 (88 total).

`seed_sweep.py` settles whether that is a finding. Changing **only the Louvain
random seed**, on **one fixed corpus**:

| statistic | mean ± std | range |
|---|---|---|
| births | 34.1 ± 4.8 | 27–43 |
| splits | 28.2 ± 4.0 | 20–34 |
| merges | 25.4 ± 4.4 | 17–32 |
| **mutations** | **87.8 ± 7.6** | **74–102** |
| final communities | 9.5 ± 0.6 | 9–11 |

88 and 90 are the same number. The seed was hardcoded to 42, which presented a
distribution as a point estimate; it is now `LOUVAIN_SEED`.

**The consequence is larger than S0's own question.** The published null model
compares 90 real events against 94.1 shuffled — a gap of **4.1**, against an
instrument whose seed noise alone is **±7.6**. The headline null result
(z = −0.27) is well inside the noise of re-running the identical analysis with a
different random seed. The README's negative claim survives, but its stated
reason does not: this is not evidence that mutation rate is unrelated to
chronology, it is an instrument that cannot resolve a difference that size. That
is P3 in the brief, now quantified, and it is the strongest available argument
for doing S3.

### 5. Author confound 20.7 % vs 19.5 %

Computed over all 343 books, so it inherits the year noise and the two missing
books. Direction and magnitude are intact; it is not a headline figure.

---

## Things found while reconstructing that are defects in the published work

These are properties of the **published** corpus and code, not of the
reconstruction. None were fixed in a way that changes the corpus, because that
would defeat the comparison.

### A. Nothing in the repository produces the null model

`results.json` carries an `honest_metrics` block, and the README's central
negative claim plus two of the three figures typed on the live site come from it.
`grep -rn honest_metrics *.py` finds **only a reader**
(`animate_genre_growth.py:195`). No script writes it.

So the corpus was not the only thing missing — the script behind two published
headline numbers is gone too. `null_model.py` reconstructs the procedure (the
real arm is exactly `sum(timeline.mutations)`; the null permutes publication
years and holds the texts fixed). It returns 88 vs 102.2 ± 17.5, z = −0.82 where
the original reported 90 vs 94.1 ± 15.2, z = −0.27. Same conclusion. **Agreement
would have been evidence this is the original procedure; disagreement is not
evidence the original was wrong**, and given §4 neither number means much.

### B. 14 works are in the corpus twice, under two titles each

`build_canon.py` keys its dedup on `norm(title) + surname`, and a subtitle
survives that key. So one novel entered as two books: *Tom Jones* / *History of
Tom Jones*, *Cecilia* / *Cecilia; or, Memoirs of an Heiress*, *The Sign of Four* /
*The Sign of the Four*, and eleven more. Both members of all 14 pairs are in the
published 345.

Two consequences worth a line in the paper. `n_books = 345` counts about **331
distinct works**. And byte-identical twins are guaranteed to be each other's
nearest neighbour, so they form maximum-strength 2-cliques that the community
detector then reads as structure.

Left in place — removing them would stop reproducing the published run. Recorded
in `_data/harmonize_log.json`.

### C. `n_authors = 166` counts about 157 people

The author list contains spelling variants of the same person: **H. G. Wells
appears three times** ('H.G. Wells', 'H. G. Wells', 'Herbert George Wells'), and
Haggard, Thackeray, Forster, Burney, Lawrence, Scott and Le Fanu twice each.

`controls.py` groups the one-book-per-author control on the **exact author
string**, so Wells contributed three books to the "one per author" subset, not
one. The control that exists to remove author voice is partly defeated in the
published numbers. *Cecilia* compounds it with (B): the same text appears under
both 'Fanny Burney' and 'Frances Burney' and is kept twice.

Detective fiction is unaffected — Doyle, Christie, Freeman, Green and Chesterton
each appear under one spelling.

Preserved deliberately: correcting it would change `n_authors` and the controlled
subset, i.e. would stop reproducing the published result. It should be fixed
*after* Aidan rules on this report, and S1 will want it.

### D. Two live bugs in the fetch path

Found by refusing to write off 27 titles as "not digitized". Both are fixed,
because neither affects the identity of the corpus — only whether a book is
retrievable at all.

- **`text_plain_url()` accepted Gutenberg side files.** Ids 9344 (*Almayer's
  Folly*) and 9341 (*Chance*) publish **only** `<id>-readme.txt` under
  `text/plain`, so `find_on_gutenberg` preferred a README record over the actual
  novel sitting lower in the same result list. It failed loudly here only by
  luck — the guessed cache URL 404s. Had that file existed, **a Gutenberg readme
  would have entered the corpus as the novel's prose** and been clustered as
  fiction. The current corpus was audited and is clean.
- **`fetch_opening_prose()` guessed the URL.** It only ever tried
  `cache/epub/<id>/pg<id>.txt` and discarded the URL Gutendex actually returned,
  making every legacy id published as `/files/<id>/<id>-0.txt` unreachable.

Plus: `find_on_gutenberg` now retries without a leading article, because Gutendex
ranks `"The Man in Lower Ten rinehart"` below thirteen unrelated books and finds
the novel instantly as `"Man in Lower Ten"`. Those three changes turned 27 misses
into 1.

---

## Is it the same *text*?

Measured, not assumed. `_data/bibliography_books.json` was fetched **2026-07-21**
by this same `build_corpus.py`, days after the Phase 1 run, and shares 29 books
with the Phase 1 title list:

- **28 of 29 byte-identical**
- **0 resolved to a different Gutenberg id**
- 1 (*Pierre*) differs by a single stray `</pre>` token

Gutenberg text is stable over this interval, so the reconstruction is very likely
running on the same prose the published numbers were computed from. The corpus is
committed, plus `_data/corpus_manifest.json` — 344 rows of
`(title, author, year, gutenberg_id, sha256, words)` — so this is checkable
without opening a 38 MB file.

---

## Three traps this session walked into, for whoever runs S1

Each produced a *clean-looking* result that was wrong. All three are the same
mistake: a check that shared an assumption with the thing it checked.

1. **A guard that matched less than the rule it named.** Gutendex's search is
   fuzzy enough that one-word titles match anything — `"She"` returns ten
   Sherlock Holmes volumes. The first guard allowed substring matching on short
   titles and so passed the exact three misattributions it existed to catch
   (`" rainbow "` matched "Roster of the Rainbow division").
2. **A guard that assumed its own conclusion.** The second version checked
   whether Gutendex files a title under the assigned author — while treating that
   assigned author as established. It confirmed the bug. The fix was to make the
   two catalogues *disagree* before trusting either.
3. **A verification script that reported a catastrophe.** `verify_s0.py`'s first
   run announced that all eight controlled communities had vanished and the
   detective result was gone. The published `controls_results.json` simply has no
   `titles` field, so every Jaccard scored 0.0 — `controls.py` had printed
   z = −3.0 on screen moments earlier. **This is exactly the S2 lesson**: confirm
   the checker found the row it thinks it found before believing what it says
   about the data. It now prints the matched row and the key it matched on.

---

## What S0 unblocks, and what it changes downstream

**S1, S3, S4, S5 can start** — the corpus is on disk and committed.

For **S1** (provenance audit): the corpus is 343 books and `controls.py` now
records per-community membership (`titles`), which the audit needs. Note (C)
first: the author-spelling duplicates should probably be resolved as part of S1,
since they defeat the same control the audit is testing.

For **S3** (replace the instrument): §4 is the argument, already quantified. The
seed-spread is ±7.6 mutations against a null-model effect of 4.1. `seed_sweep.py`
and `LOUVAIN_SEED` exist; the "cheap control on the old instrument" the brief
asks for is done.

For the **paper**: (B) and (C) are methods-section material — 345 books is ~331
works by ~157 people — and the detective result's exact reproduction from
published artifacts alone is a reproducibility claim worth making explicitly.

**For the live site: still frozen, and still knowingly wrong.** The three typed
stat spans (33 splits / 25 merges / 32 births) and the null-model prose
(90 real, 94 ± 15, z = −0.27) now have a reconstruction behind them that says
31 / 23 / 34 and 88 vs 102.2 ± 17.5. Not touched, per the standing decision. When
the page is finally updated from the final substrate, §4 says the event counts
should be reported as a **distribution across seeds**, not as three integers.
