# Research program: getting the right data

Scoped 2026-08-15, from the session that asked "how do we get more data — the
*right* data?" Each section below is a **self-contained session brief**: a fresh
Claude session with no context should be able to read one and one-shot it.

Read [`../README.md`](../README.md) first for what the project claims. This
document is only about what to do next and why.

---

## Standing decisions

Settled with Aidan 2026-08-16. **Do not re-ask these.** If a session's work makes
one of them look wrong, say so and stop — don't quietly reinterpret it.

**Destination: a paper *and* the site.** Full program as scoped, ~1 month of
sessions, with the site as a byproduct rather than the target. The bar is peer
review, not internal honesty — S3 and S4 have to be defensible to a reviewer who
knows the prior art.

**What that means for the shape of the program.** S0–S5 substantially rebuild
machinery Underwood already published (see S3). **S6 is the contribution** — the
period-reception series is the thing nobody has built, and the paper's claim is
the regression of that series against the textual one. Sessions S0–S5 are
infrastructure serving S6. Scope them accordingly: solid, not gold-plated.

**Drift rule: report and stop.** If a session's numbers disagree with the
published ones, it reports the delta and **halts**. No session adopts a new
ground truth, rationalizes a near-miss, or decides a deviation is acceptable.
Aidan calls it each time, with the numbers in front of him.

**The live site is frozen for the duration.** No session touches
`writing-topology/research/`. It gets updated **once**, at the end, from the
final substrate.

> Accepted risk, logged deliberately: the page currently states figures
> (33 splits / 25 merges / 32 births; 90 real vs 94 ± 15, z = −0.27) that
> **cannot currently be reproduced**, because the corpus behind them is not on
> disk. Aidan has accepted this for the duration rather than churn the page or
> take it down. It is a known state, not an oversight — do not "fix" it.

**Phase 2 is out of scope.** The author-influence work
([`PHASE2_INFLUENCE_NETWORK.md`](PHASE2_INFLUENCE_NETWORK.md)) stays parked,
including its unresolved stylistic-similarity question. It is already honest
about being unresolved; leave it that way.

**When the program concludes, email Stanford's Literary Lab.** Decided 2026-08-18
and deliberately deferred to the end: Aidan writes to Mark Algee-Hewitt
(malgeehe@stanford.edu), director, on one hook — their active *Castle at the
Crossroads: The Gothic and Other Genres* project models the gothic **supervised**,
and our unsupervised run says the gothic is a perennial *mode* (z ≈ 0) while
detective fiction is the one datable birth (z ≈ −3.0). A falsifiable question about
their live work, not a submission — LitLab has no submission path at all. Gated on
S0 (the corpus must be back on disk; the first thing distant reading asks for is
the corpus) and on S6 existing. Full plan and the draft email:
`~/.claude/projects/-Users-aidan-Desktop-writing-topology/memory/litlab-outreach-plan.md`.
Real venues for the paper itself are in that file too — note **CHR 2027's deadline
passed 2026-08-14**, so the next conference cycle is ~Aug 2027.

---

## State of play — read this before scoping any work

> **Updated 2026-08-18 by S0.** Facts 1 and 2 below are now HISTORY — the corpus
> is back on disk and committed. Full report:
> [`S0-CORPUS-RECONSTRUCTION.md`](S0-CORPUS-RECONSTRUCTION.md). What changed:
>
> - **`_data/books.json` exists and is committed**, 343 of the 345 books, plus
>   `_data/canon.json`, every raw catalogue pull, and a 344-row manifest of
>   `(title, author, year, gutenberg_id, sha256, words)`. Phase 1 is now
>   committed like Phase 2.
> - **Detective fiction reproduces exactly** — n = 13, 1878–1926, std 14.9,
>   **z = −3.04**, same six top terms — from published artifacts alone. Fact 3
>   stands, and now has an internal leg to go with S2's external one.
> - **The Louvain event counts do not reproduce and cannot.** Changing only the
>   random seed on a fixed corpus moves the mutation total by **±7.6**
>   (range 74–102), so the published 90 and the reconstruction's 88 are the same
>   number. This makes P3 quantitative — see the note under P3.
> - **Nothing in the repo writes `honest_metrics`**; only
>   `animate_genre_growth.py` reads it. The producer of the null-model figures
>   was missing too, and `null_model.py` is a *reconstruction* of it.
> - **Two defects in the published corpus**, both left in place deliberately:
>   14 works appear twice under two titles (345 books ≈ 331 works), and
>   `n_authors = 166` counts ~157 people because H. G. Wells and six others
>   appear under several spellings — which partly defeats `controls.py`'s
>   one-book-per-author control. Read §B and §C of the S0 report before S1.

**1. ~~The Phase 1 corpus does not exist on disk.~~** *Resolved by S0.*
`_data/books.json` and `_data/canon.json` were absent and had never been
committed; the published Phase 1 results were unreproducible until 2026-08-18.

**2. The corpus identity survives.** `results.json` → `communities[].titles`
holds **all 345 titles**, unique and complete. `genre_network.html` → the
embedded `DATA` object holds the 166 author-controlled books with
title/author/year/community. That is what S0 rebuilt from, without re-running
the LLM enumeration — because re-running `build_canon.py` produces a
**different** corpus (two LLMs, non-deterministic) and would silently break
comparability with every published number. **The rule still stands for every
later session: do not run `build_canon.py`.**

**3. The surviving positive finding rests on 13 books.** `controls_results.json`
→ detective fiction: n = 13, 1878–1926, year_std 14.9, z = −3.04.

### The eight controlled communities, for reference

| n | years | std | z | held-out label | had a genre bucket? |
|---:|---|---:|---:|---|---|
| 13 | 1878–1926 | 14.9 | **−3.04** | Detective and mystery stories | **yes** |
| 35 | 1726–1925 | 44.6 | −1.24 | Best Books Ever Listings | no |
| 5 | 1820–1907 | 33.0 | −0.60 | Fantasy fiction | no |
| 13 | 1748–1921 | 47.4 | −0.30 | Historical Fiction | **yes** |
| 31 | 1678–1928 | 54.3 | +0.20 | Domestic fiction | no |
| 29 | 1764–1925 | 54.3 | +0.21 | Science fiction | **yes** |
| 10 | 1719–1919 | 55.8 | +0.43 | Adventure stories | **yes** |
| 30 | 1719–1923 | 63.3 | +1.45 | Bildungsromans | no |

---

## The three problems, ranked

### P1 — The genre system is in the sampling frame

[`build_canon.py`](../build_canon.py) recruits from 14 buckets, four of which
name a genre ("foundational detective and mystery novels in English before
1929", and the same for Gothic, science fiction, adventure/historical romance).
A project whose claim is that genre structure is recoverable *from prose alone*
partly selected its corpus **by genre**.

**Calibration, from this repo's own data:** three of those four buckets produced
perennial communities (sf +0.21, adventure +0.43, historical −0.30). A genre
bucket does **not** mechanically manufacture temporal concentration. So P1 is a
real hole in the argument's hygiene, not a likely explanation of the detective
result. Audit it because n = 13, not because it is probably wrong.

**Blocker:** [`build_canon.py:147-149`](../build_canon.py#L147-L149) writes
`n_lists` as a *count* and discards which lists a title came from. The
provenance needed to run the audit is thrown away at write time.

### P2 — Canon is survivorship-filtered, and genres form in the books that didn't survive

166 author-controlled books over 250 years is **0.66 books/year**. A year-by-year
process cannot be observed at less than one observation per year. Worse, canon is
filtered *by the outcome*: a genre becomes a genre when it gets formulaic enough
for hacks to mass-produce, and those books are exactly the ones canon discards.
Detective fiction may be the only datable emergence because it is the only
formation violent enough to leak through canonization.

### P3 — The instrument is noisy regardless of corpus size

> **Measured by S0, 2026-08-18.** On ONE fixed corpus, changing only the Louvain
> seed: mutations **87.8 ± 7.6** (range 74–102), births 34.1 ± 4.8, splits
> 28.2 ± 4.0, merges 25.4 ± 4.4, final communities 9.5 ± 0.6. The published null
> model's entire effect — 90 real vs 94.1 shuffled, a gap of **4.1** — is
> roughly half the instrument's own seed noise. The README's negative claim
> survives; its stated reason does not. `seed_sweep.py`, and the seed is now
> `LOUVAIN_SEED` instead of a hardcoded 42.

[`temporal_network.py:134`](../temporal_network.py#L134) re-runs Louvain from
scratch on every cumulative snapshot and matches communities by Jaccard ≥ 0.3.
Louvain re-partitions the **whole** graph, so one added book can renumber
communities and manufacture a "split" that is an artifact of the algorithm. The
README already concedes this ("the rate question isn't dead, the *instrument*
is"). No amount of data repairs a statistic this unstable.

---

## Dependency order

```
S6 (reception) ──────────────────── START EARLY. Weeks long, depends on
                                    nothing, and it is the paper's actual
                                    contribution. Finishing last is fine;
                                    starting last puts it on the critical path.
S2 (Ngrams) ─────────────────────── DONE 2026-08-18. Detective agrees on both
                                    clocks; the null holds on both too.

S0 (reconstruct) ──┬── S1 (provenance audit)     DONE 2026-08-18. Corpus is on
                   │                            disk and committed; detective
                   │                            reproduces at z = -3.04.
                   └── S3 (instrument) ── S4 (NovelTM) ── S5 (HathiTrust EF)
```

S0 is done, so S1/S3/S4/S5 are unblocked. S3 gained the strongest possible
argument for itself: S0 measured the old instrument's seed noise and it swamps
the null-model effect the README rests on.

S6 blocks nothing and is blocked by nothing, which is exactly why it is easy to
defer until it becomes the reason the paper is late.

---

## S0 — Reconstruct the corpus and re-verify the published numbers

> **DONE 2026-08-18 — full report in
> [`S0-CORPUS-RECONSTRUCTION.md`](S0-CORPUS-RECONSTRUCTION.md).** Detective
> fiction reproduces exactly (n=13, 1878-1926, std 14.9, z=-3.04); the Louvain
> event counts do not and cannot, because seed noise alone is +/-7.6 mutations.
> Corpus, canon, raw pulls and a sha256 manifest are committed. Deviations are
> reported, not adopted — the drift rule applies and Aidan calls it.

**Blocks:** S1, S3, S4, S5. Do this first.
**Effort:** half a day, most of it waiting on Gutenberg fetches.

**Goal.** Put `_data/books.json` back on disk, containing the *same* 345 books
that produced the published results, and prove it by reproducing them.

**Method.**
1. Read the 345 titles from `results.json` → `communities[].titles`.
2. Read author + year for 166 of them from the `DATA` object embedded in
   `genre_network.html` (see `extract_data()` in
   [`animate_genre_growth.py`](../animate_genre_growth.py) — it already parses
   this exact object; reuse it, do not write a second parser).
3. Re-resolve author + year for the remaining ~179 via Gutendex/Open Library —
   the same path [`gutenberg_ingest.py`](../gutenberg_ingest.py) already uses.
4. Write a reconstructed `_data/canon.json`, then run
   [`build_corpus.py`](../build_corpus.py) to re-fetch real Gutenberg text.
5. Run `analyze.py` and diff against the checked-in `results.json`.

**Rules.**
- **Do not run `build_canon.py`.** Two non-deterministic LLMs will return a
  different canon and silently invalidate comparison with every published
  number. The title list is the ground truth now.
- Expect drift: Gutenberg IDs and editions change, and `build_corpus.py` pulls
  ~20k words from whatever edition it matches. Some titles will not re-resolve.
  **Log every miss and every substitution** rather than quietly proceeding.
- Commit the corpus this time, or if it is too large, commit a manifest of
  (title, author, year, gutenberg_id, sha256 of the extracted text) so the next
  session can verify rather than trust.

**Done when.** `analyze.py` reproduces n_books = 345, null model z = −0.27, and
detective z = −3.04, or the deviation is documented with its cause. Corpus or
manifest committed.

---

## S1 — Provenance audit of the sampling frame

**Depends on:** S0. **Effort:** an afternoon.
**Addresses:** P1.

**Goal.** Answer one question: does detective fiction's z = −3.04 survive
removing the books that entered the corpus *only* through a genre-named bucket?

**Method.**
1. Fix [`build_canon.py:147-149`](../build_canon.py#L147-L149) to persist
   `"lists": sorted(rec["lists"])` alongside the count. One line. This is the
   permanent fix and it must land regardless of what the audit finds.
2. For the *existing* corpus, recover provenance without perturbing it: re-run
   **only the four genre-bucket prompts** and intersect the returned titles
   against the known 345. Tag each book `genre_bucket_reachable: true/false`.
3. Re-run the concentration test excluding titles reachable *only* via a genre
   bucket, and report all eight communities before/after.

**Rules.**
- Step 2 must not overwrite `_data/canon.json` or `books.json`. It is a
  read-only tagging pass over a fixed corpus.
- Report the three counter-examples honestly: sf, adventure and historical
  fiction all had buckets and all came out perennial. If detective survives, say
  so plainly — this audit is as likely to harden the finding as to kill it.
- With n = 13, removing even 4 books moves z materially. Report the z **as a
  function of how many were removed**, not a single after-number.

**Done when.** A before/after table over the eight communities, plus a one-line
verdict on whether the project's only surviving positive result is sampling-
independent.

---

## S2 — The reception clock (Google Ngrams)

> **DONE 2026-08-18 — findings in [`S2-RECEPTION-CLOCK.md`](S2-RECEPTION-CLOCK.md).**
> The two clocks **agree on detective fiction**: name take-off 1889 (1883/1897 at
> 5 %/20 % of peak) against books of 1878–1926, name peaking 1932. The instrument
> is externally licensed on the one positive result. The null also holds from the
> reception side — five of eight genre names were already current before the
> readable window opens, which is what a perennial mode looks like in a source
> that never touched the corpus.
>
> Two things it handed downstream, neither of them in this brief's original scope:
> **(a)** dating a cluster by its held-out label instead of its own vocabulary
> moves the answer +62 to +142 years and invents 20th-century emergences — a
> methods caution for the paper, drawn as Fig. 7; **(b)** `sensation novel`
> take-off 1859, mass width 16 y, peak 1867 sits *inside* the "perennial" Gothic
> cluster, which is a concrete target for S3/S4 rather than a result.
>
> Code: `pull_ngrams.py` → `analyze_reception_clock.py` → `emit_reception_figure.py`.
> The raw pull is committed (`_data/ngrams_raw.json`) so the next session verifies
> rather than re-fetches.

**Depends on:** nothing. Can start immediately, in parallel with S0.
**Effort:** an afternoon. **Addresses:** validates the instrument externally.

**Goal.** Date each genre by when its *name* entered the language, using a source
with zero dependence on the text pipeline — then check whether the two clocks
agree.

**Verified working** (2026-08-15, no auth, 320 years returned):

```
https://books.google.com/ngrams/json?content=detective+story,science+fiction
  &year_start=1700&year_end=2019&corpus=en-2019&smoothing=3
```

Send a browser User-Agent. Response is a JSON array of
`{ngram, timeseries[320]}`.

**Method.** Pull curves for the genre vocabulary — "detective story", "science
fiction", "sensation novel", "ghost story", "historical romance", "adventure
story", "domestic novel", "Bildungsroman" and their plausible period variants
("scientific romance" matters more than "science fiction" before ~1930). For
each, extract a take-off year (first sustained rise above baseline). Tabulate
against the textual `year_min` from the table above.

**Rules.**
- Google Books' corpus composition drifts over time. Use the normalized
  frequencies Ngrams returns, and **do not read anything pre-1800** as signal.
- Period terms, not modern ones. "Science fiction" is anachronistic for Verne
  and Wells; the period word is "scientific romance". Getting this wrong
  produces a fake late emergence.
- This is a *validator*, not a finding. If the clocks agree on detective fiction,
  that licenses the instrument. If the seven perennial modes also have flat
  name-curves, the null becomes a result rather than an absence — which is the
  most valuable outcome available here.

**Done when.** One figure plus a table of textual-emergence vs name-adoption per
genre, and a stated verdict on whether the two clocks agree on detective fiction.

---

## S3 — Replace the instrument

**Depends on:** S0. **Effort:** 2–3 days. **Addresses:** P3.

**Goal.** Stop counting Louvain births/splits/merges. Measure per-genre
**coherence over time** instead, so the statistic is stable enough to survive a
100× larger corpus.

**Read first.** Underwood, *The Life Cycles of Genres*, Journal of Cultural
Analytics 2016 — <https://culturalanalytics.org/article/1209>, data and scripts
at <https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/XKQOQM>.
This is the same question, already done, with a supervised per-genre approach
rather than clustering-event counting. *(The journal sits behind an Anubis
challenge; fetch the Dataverse copy or the Semantic Scholar PDF.)*

**Method.** For each genre, train a period-windowed classifier and track its
accuracy/coherence across windows; a genre that "consolidates" becomes more
predictable from its own vocabulary over time. Validate on the existing 345-book
corpus, where detective fiction is the known-positive control.

**Also do, as a cheap control on the old instrument:** run the existing Louvain
timeline across N seeds and report event counts as a **distribution**, not a
point estimate. If the ±spread across seeds swamps the 90-vs-94 null-model gap,
that alone explains the null and is worth stating in the README.

**Done when.** The new statistic recovers detective fiction's consolidation on
the same corpus and returns a defensible number for the other seven; the
seed-sweep spread on the old statistic is quantified.

---

## S4 — Re-sample from NovelTM instead of from canon

**Depends on:** S3 (runnable before it, but the results are only trustworthy with
the new instrument). **Effort:** ~1 week. **Addresses:** P1, P2.

**Goal.** Replace a canon-selected sample with a sampling *frame*, and measure
how much of the answer was canon.

**Data.** [`tedunderwood/noveltmmeta`](https://github.com/tedunderwood/noveltmmeta)
— 210,305 HathiTrust volumes identified as English-language fiction, 1700–2009,
MIT-licensed TSVs in `/metadata`. Ships seven subsets, including
`frequently_reprinted_subset` (canon-like) and `gender_balanced_subset`.

**Method.** Draw a year-stratified random sample from the full frame, resolve to
text with [`gutenberg_ingest.py`](../gutenberg_ingest.py) (already built, already
scales, already has **no** canon filter — it was superseded by the canon-first
approach, which for the *temporal* question was backwards). Run the S3
instrument. Then run the identical pipeline on `frequently_reprinted_subset`.

**The experiment is the delta between those two runs.** That is the direct
measurement of P2 and it is the single most valuable number this program can
produce.

**Rules.**
- Target the pre-1929 Gutenberg-resolvable overlap first (a few thousand
  volumes); do not wait for HathiTrust text to start.
- Keep one-book-per-author. The 19.5% author confound does not go away at scale.
- Note the upstream caveat: NovelTM is an explicitly frozen 2019 snapshot its
  authors do not intend to correct or maintain.

**Done when.** The same statistic reported at two canonicity levels, with the
delta stated and interpreted.

---

## S5 — Break the 1929 ceiling with HathiTrust Extracted Features

**Depends on:** S4. **Effort:** ~1 week. **Addresses:** P2, and the README's
"pre-1929 ceiling" limitation.

**Data.** [Extracted Features
v2.0](https://htrc.atlassian.net/wiki/spaces/COM/pages/43295914/Extracted+Features+v.2.0)
— 17.1M volumes, page-level POS-tagged token counts, **public domain and
in-copyright**, non-consumptive, rsync-able, MARC-derived metadata.

**Why it fits this pipeline specifically.** [`semantic_edges.py`](../semantic_edges.py)
builds TF-IDF over prose. EF ships per-page *token counts* — already the bag of
words TF-IDF wants. No full text required, which is the entire reason the
dataset can include in-copyright works. The adaptation is a loader change, not a
method change.

**Done when.** The instrument runs on in-copyright volumes and the genre timeline
extends past 1929 — cyberpunk, modern fantasy, postmodernism become reachable
for the first time.

---

## S6 — The period reception dataset

**Depends on:** nothing. **Effort:** weeks. **Start this early — it is the
paper's contribution, not its appendix.**

Everything else in this program rebuilds instrumentation that already exists in
the literature. This is the part that doesn't. If only one session survives a
change of plan, it should be this one.

**Why it is worth the most.** The README lists this as honest next step #3. It is
also, by his own account, the thing the leading prior art did *not* do:
Underwood defines genre membership with **modern retrospective labels** and names
that as a limitation. Genre also lives in how period readers, critics, publishers
and librarians classified books *at the time* — and nobody has built that series.

> **Slice 1 done 2026-08-18 — [`S6-SLICE1-BACKMATTER-PROBE.md`](S6-SLICE1-BACKMATTER-PROBE.md).**
> The go/no-go on the cheapest source came back **NO-GO for Gutenberg**: across
> all 343 books and 42.2M words of FULL text, only **4** carry a publisher
> advertisement, and one of the five flagged is a false positive. `Crown 8vo`
> appears in 4 of 343 novels. Gutenberg transcribers strip the ads, exactly as
> this brief predicted.
>
> The artifact itself is worth what was hoped, though — John Lane's 1904
> back-matter ad in *The Napoleon of Notting Hill* is headed **"THE NEW MILITARY
> NOVEL"**, a publisher naming a genre in a dated recruitment ad, and Alcott 1868
> constitutes "THE LITTLE WOMEN SERIES" in back matter. So the source is
> Internet Archive page scans, not Gutenberg text — and tellingly, the one
> Gutenberg text that kept its trade list was transcribed *from IA scans*.
>
> Two things that probe hands S6: ads sit above 98% or below 1% of the volume
> (a strong page-position prior for OCR cost), and **"by the same author" lists
> are a different artifact from genre-series ads** — only the second measures
> genre formation, and conflating them would inflate the series with data that
> cannot speak to genre. The doc also names a cheaper intermediate worth pricing
> first: the trade catalogues (*Publishers' Circular*, *English Catalogue of
> Books*), which concentrate the same headings in bulk.

> **Slice 2 done 2026-08-26 — [`S6-SLICE2-TRADE-CATALOGUE.md`](S6-SLICE2-TRADE-CATALOGUE.md).**
> **GO, and the page-scan OCR pipeline is not needed.** But on a different
> serial than slice 1 named and a different artifact than it expected:
>
> - **Both sources slice 1 named fail, measured.** *The English Catalogue of
>   Books* is an alphabetical price list — 2 generic genre-term hits in 318,725
>   words, no specific genre term at all. IA holds 24 items of *The Publishers'
>   Circular*, nearly all 1853, and the issue tested fires zero genre terms.
> - **Publishers' Weekly is the source: 2,965 dated issues, 1872–1929,
>   free `_djvu.txt`, no lending restriction, no OCR cost.** Register control
>   fires 5/5 on 8.8M words.
> - **The artifact is the Weekly Record annotation, not the heading** — one
>   dated line per book, and PW's own masthead says the annotations are
>   "descriptive, not critical; intended to place not to judge the books,"
>   i.e. classificatory. PW's formal `CLASS SYNOPSIS` never subdivides Fiction,
>   so the class list cannot date a genre; the annotation can.
> - **Yield: Weekly Record locatable in 176/232 sampled issues (76%), 13,743
>   entries, 1,263 (9.2%) genre-bearing** → order of 175,000 dated per-book
>   entries and ~16,000 genre attributions across the run, against slice 1's 4.
> - **New finding: `mystery story` is absent for 29 consecutive years
>   (1872–1900), first attested 1901, sustained after.** A dated formation in
>   period trade evidence, and a testable prediction for S3/S4 — if the textual
>   instrument finds it too, the positive result stops resting on 13 books.
> - **`detective story` first attested 1880, sustained from 1908** — same era as
>   S2's 1889 Ngrams take-off, independent source. Do **not** read its 20%
>   take-off of 1904 as a date: it is right-censored at the 1929 window edge.
> - **The real cost is section segmentation** (24% of issues lose the Weekly
>   Record heading to OCR), and the window is cheaply extendable back to 1852 by
>   splicing IA's 532 items of *The American Publishers' Circular*.

**Sources, ascending cost.**
- **Publishers' series labels and back-matter advertisements.** Genre formation
  as a dated marketing act: the moment a publisher creates "The Detective
  Series" and starts recruiting into it. These ad pages are **bound into the
  Gutenberg and Internet Archive scans already being downloaded and discarded.**
  Cheapest real reception signal available, and nobody is mining it.
  *Measured 2026-08-18: bound into the IA scans, yes; into the Gutenberg
  transcriptions, almost never (4/343).*
- **Circulating-library catalogues** (Mudie's, W.H. Smith) — classification at
  the point of consumption, dated.
- **Periodical reviews** (*Athenaeum*, *Spectator*, *Publishers' Weekly*) —
  where a critic first writes "one of those detective stories". First attestation
  plus diffusion rate is a direct measurement of genre formation.

**Rule.** Period evidence only. Modern retrospective reviews back-project today's
categories and would reintroduce exactly the circularity of P1.

**Done when.** A dated reception series per genre that can be regressed against
the textual series from S3/S4.

---

## Housekeeping found while scoping

- **README number mismatch.** The README says detective fiction is "concentrated
  in ~1840s–1920s"; `controls_results.json` says **1878–1926**. If the 1840s
  refers to Poe as literary-historical context rather than to the corpus, say so
  explicitly — as written it reads as a corpus figure and is wrong by ~35 years.
- **~~`_data/` is committed for Phase 2 but not Phase 1.~~** Fixed by S0
  2026-08-18: `books.json`, `canon.json`, every raw catalogue pull and a
  `(title, author, year, gutenberg_id, sha256)` manifest are committed.
- **New, from S0 — three things to fix once Aidan has ruled on the report.**
  (a) 14 works are in the corpus twice under two titles, because
  `build_canon.py` dedups on `norm(title) + surname` and a subtitle survives
  that key; (b) `n_authors = 166` counts ~157 people, because H. G. Wells and
  six others appear under several spellings, which partly defeats
  `controls.py`'s one-book-per-author control; (c) nothing in the repo writes
  `results.json.honest_metrics` — the null-model producer is missing, and
  `null_model.py` is a reconstruction of it, not a recovery.
