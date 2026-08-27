# S6 slice 2 — is the trade catalogue a cheaper reception source?

Run 2026-08-26, after slice 1. Brief:
[`S6-SLICE1-BACKMATTER-PROBE.md`](S6-SLICE1-BACKMATTER-PROBE.md), closing
paragraph — *"a cheaper intermediate worth pricing before committing to OCR:
publishers' trade circulars and The Publishers' Circular / The English
Catalogue of Books … carry the same series-and-genre headings in bulk rather
than one novel at a time."*

Still a probe, per [`RESEARCH-PROGRAM.md`](RESEARCH-PROGRAM.md) § S6: the
question is whether a dated bulk period-evidence series is **reachable and at
what cost**, not to build it.

---

## Go/no-go

**GO — but on a different serial than slice 1 named, and on a different
artifact than slice 1 expected.**

- **The two sources slice 1 named both fail.** *The English Catalogue of
  Books* is an alphabetical price list with no genre structure: **2 genre-term
  hits in 318,725 words** (6.3 per million, both of them the generic
  `detective (any)`; no specific genre term fires), and its three caps headings
  are OCR breaks, not genre acts. *The Publishers' Circular* fires **zero** genre
  terms in the 1853 issue tested, and IA holds only **24 items** of it, nearly
  all 1853 — too thin to carry a series regardless of content.
- **Publishers' Weekly works, and nobody named it.** **2,965 dated issues,
  1872–1929**, ~51/year, IA-hosted as **free `_djvu.txt`** with no lending
  restriction. **OCR cost is zero** — the expensive pipeline slice 1 warned
  about is not required. Genre vocabulary runs at **125 hits per million
  words** (1,097 hits over 8.78M, excluding the `detective (any)` superset so
  nothing is counted twice). Like-for-like on the one term that fires in both
  sources, `detective (any)`: **50.8 per million in PW against 6.3 in the
  English Catalogue, 8.1×** — and no *specific* genre term fires in the English
  Catalogue at all.
- **The artifact is not the heading.** It is the **Weekly Record annotation** —
  one dated line per book, in the trade's own words, for every American book
  published. PW states the editorial policy itself, in the section masthead:

  > "The annotations are **descriptive, not critical; intended to place not to
  > judge** the books."

  That is the trade press declaring its own annotation to be *classificatory*.
  It is the sentence that licenses this as period **reception** evidence rather
  than review opinion, and it is why the yield below is measured per entry.

**Measured yield, on a 232-issue sample (8% of the run):** the Weekly Record
section is locatable in **176 of 232 issues (76%)**, holding **13,743 entries**,
of which **1,263 (9.2%)** carry a genre word. Scaled across the 2,965 available
issues that is on the order of **175,000 dated per-book trade entries and
~16,000 genre attributions** — against slice 1's **4** surviving Gutenberg
advertisements.

---

## What was run

`probe_trade_catalogue.py`. 232 issues, **4 per year, evenly spaced,
deterministically picked** (no RNG, so the sample reproduces without a seed),
**8.8M words** of OCR, cached to disk so the detector can be re-run and argued
with without re-downloading.

The estimator is **imported from `analyze_reception_clock`**, not
reimplemented — same 9-year smoothing, same 10-year persistence, same
fraction-of-peak thresholds — so a take-off measured here is directly
comparable to S2's Ngrams take-off rather than merely similar to it.

### Live-fire control, before any genre number is read

Slice 1's five marker families, on the same text. A genre count from a source
that turns out not to be trade material measures nothing.

| family | hits |
|---|---:|
| `trade_format` (Crown 8vo, cloth gilt) | 1,248 |
| `price` (3s. 6d., 6s.) | 1,272 |
| `series_or_list` | 535 |
| `trade_puffery` (NOW READY, PRESS OPINIONS) | 507 |
| `same_author` | 47 |
| **families firing** | **5 / 5** |

All five fire, against 4/5 in the 1890–93 pilot and 1 diagnostic family in
slice 1's entire Gutenberg corpus. This is trade material.

**The genre-act detector's positive control caught a real bug before the corpus
ran.** The first version required a heading to *end* in
SERIES/LIBRARY/NOVELS/STORIES and missed three of five real examples —
including slice 1's best find, "THE NEW MILITARY NOVEL." Detection is now by
heading *shape* (a short full-caps line carrying a genre word), which passes
7 of 8 controls and correctly rejects "BY THE SAME AUTHOR" and "THE LITTLE
WOMEN SERIES" (a series, but no genre word). One known false-positive mode:
hyphen-broken words at line end ("SCOTT'S LIVES OF THE NOVEL-").

**Author artifacts are excluded, never summed in** — slice 1's rule 3.
45 author artifacts vs 630 genre acts in the sample.

---

## The clock, 1872–1929, per million words

| term | hits | peak/M | peak yr | t/o 5% | t/o 10% | t/o 20% | 1st attest |
|---|---:|---:|---:|---:|---:|---:|---:|
| detective story | 142 | 44.2 | 1929 | 1876 | 1879 | **1904** | **1880** |
| detective (any) | 446 | 92.5 | 1929 | 1872 | 1872 | 1876 | 1873 |
| **mystery story** | 124 | 46.9 | 1922 | **1901** | **1903** | 1907 | **1901** |
| historical romance | 140 | 35.9 | 1900 | 1872 | 1872 | 1872 | 1872 |
| adventure story | 156 | 31.3 | 1923 | 1872 | 1872 | 1872 | 1873 |
| love story | 406 | 105.2 | 1905 | 1872 | 1872 | 1873 | 1873 |
| western story | 42 | 15.4 | 1923 | 1881 | 1881 | 1896 | 1894 |
| ghost story | 35 | 9.1 | 1917 | 1880 | 1880 | 1891 | 1903 |
| sea story | 34 | 9.5 | 1873 | 1872 | 1872 | 1872 | 1905 |
| sensation novel | 13 | 6.6 | 1882 | 1876 | 1876 | 1876 | — |
| scientific romance | 5 | 2.0 | 1900 | 1916 | 1916 | 1916 | — |

**`mystery story` is the finding, and it is a clean one.** Zero hits across
**29 consecutive years, 1872–1900**, then first attestation 1901 and sustained
presence rising to a 1920–1923 plateau. A term entering the trade's vocabulary
inside the observation window, dated, in period evidence — which is exactly the
event S6 exists to measure and exactly what a perennial mode does not look
like.

**`detective story` is present from 1880 and consistent with S2.** Its first
attestation is 1880 (Estes & Lauriat advertising Gaboriau); it is sparse and
intermittent to 1907 and sustained from 1908. S2's Ngrams take-off was 1889.
Same era, independent source, and now with the trade's own dated ad pages under
it rather than a general-language corpus.

**Five terms "take off" in 1872 — that is the window opening, not a formation.**
Same shape S2 found when five of eight genre names turned out to be current
before 1800: a perennial mode looks perennial in every source that never
touched the corpus.

### Three censoring facts that bound every number above

1. **Left-censored at 1872.** PW begins there, so anything already current is
   reported as taking off in the first year. `detective story` in particular
   predates the window.
2. **Right-censored at 1929.** `detective (any)` and `detective story` both
   peak at the window edge, still rising. Fraction-of-peak take-off is
   therefore **biased late** for those two — the 20% figure of 1904 is an upper
   bound, not an estimate.
3. **Sampled at 7.8% of available issues.** Most zero-years are 4-issue years
   where the term was not in those 4 issues, not years the term was absent. The
   sparse middle of the `detective story` series is a sampling artifact and the
   fix is free: 13× more issues exist.

---

## The artifact, verbatim

**1. The publisher ad heading — genre formation as a dated marketing act.**
*Publishers' Weekly*, **19 June 1880**, Estes & Lauriat's back page. A house
constituting a genre and recruiting seven titles into it, dated to the week:

> POPULAR NOVELS FOR THE SUMMER SEASON. "MONSIEUR LECOQ." A new, entertaining,
> and intensely dramatic **detective story**, from the pen of EMILE GABORIAU.
> 8vo, paper, 50 cents. … In conception and execution it is as far above your
> ordinary 'detective's story' as the heavens are above the earth …
> **GABORIAU'S DETECTIVE STORIES.** Monsieur Lecoq. The Mystery of Orcival.
> File No. 113. Within an Inch of His Life. The Widow Lerouge. Other People's
> Money. The Clique of Gold. Each complete in one volume … Boston: ESTES &
> LAURIAT, Publishers.

**2. The Weekly Record annotation — the trade classifying one book, dated.**
*Publishers' Weekly*, **5 October 1901**. The first `mystery story` attestation
in the whole series, and it is the trade's own descriptive line, not a review:

> Ehrmann, Max. A fearsome riddle; il. by Virginia Keep. Indianapolis, Ind.,
> Bowen-Merrill Co., [1901.] … D. cl., $1. **A mystery story**, based on the
> theory of the arithmetical rhythm of time.

**3. The class heading — present, but fiction is never subdivided.** PW's
monthly `CLASS SYNOPSIS` does classify: *Biography, Correspondence* /
*Description, Geography, Travel* / *Domestic and Social* / *Education,
Language* / **Fiction**. Fiction is one undivided class throughout. So the
trade's *formal* classification cannot date a genre — which is why the
annotation and the ad heading, not the class list, are the artifact.

---

## Cost, stated honestly

**Free and already transcribed** — no OCR, no lending restriction, no page-image
pipeline. That is the whole point of this slice and it holds.

**The real engineering cost is section segmentation, not text.** The Weekly
Record heading fails to OCR in **56 of 232 issues (24%)**, and the section's end
marker fails often enough that the probe caps the region at 60,000 characters.
Building the dataset means locating a section reliably across 58 years of
changing typography — which is a solvable text problem, not an OCR budget.

**Two limits that bound the claim and must be in the paper.**

1. **It is the American trade.** The Phase 1 corpus is English-language fiction
   including the whole British canon, and PW records American publication. The
   British counterpart is not reachable at this cost: IA's *Publishers'
   Circular* holding is 24 items. Any regression of a PW-derived reception
   series against the textual series is a **US-side** measurement and has to say
   so.
2. **The window starts 1872**, which is after detective fiction's textual
   emergence begins (corpus range 1878–1926, but Poe→Collins is earlier) and
   well after the `sensation novel` take-off S2 dated to 1859.

**The window is extendable, and cheaply.** IA holds **532 items** of *The
American Publishers' Circular and Literary Gazette* — **227 in 1852–1859, 260
in 1860–1869** — same collection shape, same free OCR, and its 1856 issues
already carry genre-act headings ("CHEAP FICTION.", "NEW LIBRARY OF STANDARD
FICTION"). Splicing it to PW gives a continuous **1852–1929** US trade series
that covers the sensation-novel lead and detective fiction's birth. Two serials,
one splice, no new cost class.

---

## What this hands the next slice

1. **Build the series from the annotation, not the heading.** Per-book, dated,
   ~9.2% genre-bearing, and PW's own masthead says the annotations are
   classificatory.
2. **Section segmentation is the work.** 76% located by a naive heading match;
   that number is the thing to raise before anything else.
3. **Splice in the American Publishers' Circular** for 1852–1871 before
   computing any take-off, because three of the eleven terms are left-censored
   by the 1872 boundary.
4. **Sample density is free — spend it.** 4 issues/year produced a series too
   sparse to date anything but `mystery story`. All 2,965 issues are available.
5. **`mystery story` 1901 is a testable prediction for S3/S4.** If the textual
   instrument finds a formation event in that window on the US side, the two
   clocks agree on a *second* genre — and the project's positive result stops
   resting on 13 books.
6. **Do not read `detective story`'s 20% take-off of 1904 as a date.** It is
   right-censored at the window edge. Re-measure after the splice.

**Not started:** the reception series itself, per the brief.

---

## Artifacts

- `probe_trade_catalogue.py` — the probe, with the live-fire register control,
  the genre-act positive control, and `--alternatives` to re-measure the two
  sources slice 1 named.
- `trade_catalogue_probe.json` — per-year series for 11 period terms, per-issue
  detail for all 232 issues, coverage per year for all 58 years, and the
  Weekly Record yield. Committed so the next session re-reads rather than
  re-fetches.
- OCR cached at `~/.cache/literature-mutations/ia_trade_text` (not committed —
  ~60MB, re-fetchable from the identifiers in the JSON). It was originally under
  `/tmp`, which the OS cleared out from under a running full-density sweep on
  2026-08-26; a cache whose purpose is "the next session re-reads rather than
  re-fetches" cannot live somewhere the OS empties.
