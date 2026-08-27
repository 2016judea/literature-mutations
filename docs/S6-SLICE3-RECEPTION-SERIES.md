# S6 slice 3 — the period reception series

Built 2026-08-26. Brief:
[`S6-SLICE2-TRADE-CATALOGUE.md`](S6-SLICE2-TRADE-CATALOGUE.md) and the program
re-ordering in [`RESEARCH-PROGRAM.md`](RESEARCH-PROGRAM.md) ("The reception side
is now the strong side"). Slices 1 and 2 were go/no-go probes. **This one
builds.**

**3,487 dated issues · 1855–1929 · 128.5M words of OCR · 81,900 trade
annotations extracted · 0 fetch failures.**

---

## The finding

> **"Mystery story" appears ZERO times in 41.8 million words of the American
> book trade across 1,690 issues, 1855–1895 — then 1,605 times in the following
> 34 years.**

First occurrence **1896**. Sustained from **1896**. Take-off **1906–1909**
(a 3-year band across every smoothing width tested). Raw maximum **1920** at
69.6 per million; smoothed peak **1923**; a plateau near 40 per million holds
through 1929.

That is a datable genre formation, measured in period trade evidence, on a
source that never touched the textual corpus. It is the second such event this
project has found and the first one the *reception* side found on its own.

**Not one repeated advertisement.** In 1920, the 169 occurrences are spread
across **45 of 56 issues (80%)**; detective's 155 across 46. The term is in
pervasive weekly use, not concentrated in a house ad running all year.

**It is the trade classifying books, not authors titling them.** Verbatim, from
the Weekly Record's own descriptive line — which *Publishers' Weekly* states in
its section masthead is *"descriptive, not critical; intended to place not to
judge the books"*:

> [1901-10-05] **A mystery story**, based on the theory of the arithmetical
> rhythm of time
>
> [1910-06-11] **A mystery story par excellence**, written around the revival of
> ancient Bacchic rites in a garden in a very modern part of London
>
> [1929-09-07] **A mystery story** with a background of American family life,
> for young people from 12 to 16
>
> [1929-09-07] A young Canadian girl goes to New York to make her way in the
> world. **A mystery story for girls**

"A mystery story for girls" is a shelf label. The trade is not reviewing; it is
placing.

### The second finding: detective fiction, on a third clock

`detective story` — 2,592 occurrences, first 1863, sustained from **1873**,
take-off **1891–1897**, and **still rising when the source ends in 1929**.

S2 dated the name's take-off to **1889** in Google Ngrams. The trade press,
independently, gives 1891–1897. Two sources with nothing in common agree on the
era, and the textual corpus puts the books at 1878–1926. **Three clocks now
agree on detective fiction** — text, general language, and the book trade.

---

## Is it a new genre, or just a renaming?

The first question a reviewer asks, and if it cannot be answered the finding is
soft. A skeptic's reading: the trade simply started saying "mystery story" where
it used to say "detective story", and nothing about genre formation happened.

**It is not a renaming.** A renaming requires detective fiction to cede ground.
It does the opposite — it grows **6.4×** across the same decades:

| decade | detective story | mystery story | combined | love story *(control)* |
|---|---:|---:|---:|---:|
| 1890s | 7.3 | 0.1 | 7.4 | 5.0 |
| 1900s | 19.3 | 3.3 | 22.6 | 79.4 |
| 1910s | 27.6 | 16.4 | 44.0 | 63.3 |
| 1920s | **46.7** | **44.8** | **91.5** | 50.2 |

*(per million words)*

The combined crime vocabulary expands **12×**, from 7.4 to 91.5 per million.
Both terms rise together; neither replaces the other.

**The control is `love story`'s turn, not its direction.** It peaks in the 1900s
and declines through the 1910s and 1920s while both crime terms keep rising — so
the 1920s crime rise is not a general inflation of genre vocabulary. Note it
*does* rise end to end (5.0 → 50.2), so the control is the turning point, not the
sign. Correlations are no use here: r(mystery, detective) = +0.82 but
r(mystery, adventure) = +0.72, because almost everything rises in the 1920s. The
decade means carry this test, not r.

**Two weaker tests, reported as weak.** Only **13 of 179** mystery annotations
(7%) also mention a detective — but an annotation is ~20 words, so the absence of
one word from it is close to no evidence. And the two labels are applied to
visibly different kinds of book:

| | distinctive vocabulary of the annotation |
|---|---|
| **mystery** | girls, boys, people, laid, family, humor, western, known, short, involving, romance, dealing |
| **detective** | being, solves, comes, committed, point, work, plays, methods, falls, clever, chief, solution |

Mystery skews **audience and setting**; detective skews **procedure**. That
matches the verbatim annotations — *"A mystery story for girls"*, *"with a
background of American family life, for young people from 12 to 16"* against
*"A free-lance detective solves the mystery of some gruesome murders"*. But
n = 179 vs 369 at counts of 8–20 is thin, so this is suggestive only.

**Getting test 3 to say anything at all required a filter, and the obvious filter
failed.** The unfiltered list is proper nouns: author and character names (*van*,
*craig*, *reilly*, *stone*), publisher abbreviations (*apltn*, *dodd*, *doran*,
*dou*) and format debris (*illus*, *ser*). A **dispersion** filter — require the
token across many distinct years — does not work, because Helen Reilly, Craig
Kennedy and Philo Vance each ran for a decade or more, so "reilly" is as well
dispersed as "family". What works is **casing**: a token must appear lower-case
in the source at least 60% of the time. 43 tokens are rejected as names by that
rule.

### What stays unsettled

Whether `mystery story` is a **distinct genre** or a **sibling label inside one
expanding crime-fiction category**. Co-growth rules out substitution; it does not
separate those two. The trade press alone cannot, and the paper should say so
rather than choose. The 1921 annotation reading *"Detective-mystery stories based
on real cases solved by Government agents"* — a hyphenated compound — is the
trade itself declining to choose.

---

## What the instrument can and cannot see

Only **five** of eleven terms have a measurable take-off at all. That is the
honest yield, and the reason is a methodological finding in its own right.

### A fraction-of-peak take-off is unusable on a sparse series

A 9-year centered moving average spreads a first spike **backwards** by up to
four years, and the fraction-of-peak threshold is then crossed by the smoothed
shoulder. So the inherited estimator can report a take-off **before the term's
first actual occurrence**. It does exactly that here: `sensation novel`'s first
hit is **1863** and the estimator reports a take-off of **1859**.

Measured across smoothing widths 9 / 5 / 3 / 1:

| term | hits | 1st hit | take-off band | spread |
|---|---:|---:|---|---:|
| mystery story | 1,605 | 1896 | **1906–1909** | **3 y** |
| detective story | 2,592 | 1863 | **1891–1897** | 6 y |
| detective (any) | 7,046 | 1856 | 1876–1882 | 6 y |
| western story | 848 | 1856 | 1886–1894 | 8 y |
| love story | 5,882 | 1855 | 1864–1873 | 9 y |
| adventure story | 2,434 | 1856 | *not measurable* | 19 y |
| sensation novel | 244 | 1863 | *not measurable* | 23 y |
| historical romance | 2,605 | 1855 | *not measurable* | 35 y |
| ghost story | 426 | 1858 | *not measurable* | 60 y |
| **sea story** | 593 | 1856 | *not measurable* | **74 y** |
| scientific romance | 44 | 1889 | *not measurable* | 1 y † |

`sea story`'s take-off moves **seventy-four years** — the whole window — on
nothing but the smoothing width. So the rule is now explicit in code: **a
take-off whose band spans more than 10 years is reported as not measurable**
rather than given a date it cannot support.

† `scientific romance` has a tight band on 44 hits, which is the opposite
failure — too little mass for the band to mean anything. Its first hit is 1889
and it is never sustained; the term is essentially absent from the American
trade, which is itself worth knowing.

**This is a correction to how S2's estimator behaves on this source, not a
criticism of S2.** Ngrams series are dense and smooth and the bias barely bites
there. It bites hard on hard zeros.

**The statistic that does work on a sparse series** is a sustained run — the
first year after which the term appears in 5 of the next 10 years. It cannot
precede the first occurrence, and it rejects an isolated OCR fluke. Reported as
`sustained_from` for every term.

### Right-censoring, explicitly

`detective (any)`, `detective story` and `western story` all peak at **1929**,
the window edge, still rising. Any fraction-of-peak date for those three is
**biased late** and is an upper bound, not an estimate. The source ends at 1929
because Internet Archive's run does.

### The annotation series only exists from 1878

This is the sharp instrument — genre words inside the trade's own descriptive
line — and it has a hard floor. Annotations per issue, measured:

| period | issues | annotations | per issue |
|---|---:|---:|---:|
| 1852–1871 (*American Publishers' Circular*) | 522 | **5** | 0.0 |
| 1872–1876 (*PW*, pre-practice) | 251 | 17 | 0.1 |
| 1877–1881 | 246 | 2,284 | 9.3 |
| 1902–1906 | 260 | 9,073 | 34.9 |
| 1907–1911 | 260 | 15,606 | 60.0 |
| 1922–1926 | 260 | 12,303 | 47.3 |

The *American Publishers' Circular* did not annotate at all, and PW's Weekly
Record only takes up the practice in the late 1870s. So **every annotation
statistic before 1878 measures the practice, not the vocabulary**, and the
annotation window is clamped to 1878–1929 in code. This is exactly why the
parser-free per-million series is the primary one — it carries the early window
that the sharp instrument cannot reach.

**Where both series can see the same thing, they agree — with an offset worth
noticing.** `mystery story` is the only term with a measurable take-off in
*both*: per-million **1906–1909**, per-annotation **1915–1918**. The term enters
the trade's advertising and discussion roughly **nine years before** it enters
the trade's own descriptive classification. Vocabulary reaches the market before
it reaches the catalogue.

---

## The splice, and what it bought

*American Publishers' Circular and Literary Gazette* (1852–1871, 522 issues) was
spliced ahead of *Publishers' Weekly* (1872–1929, 2,965 issues) because slice 2
left three terms left-censored at PW's 1872 start.

**It paid for `mystery story` and it did not pay for `sensation novel`.** The
splice extends the demonstrated absence of `mystery story` back another 17 years
— that is where 41.8M words of proven silence comes from. But `sensation novel`,
which S2 dated to a take-off of 1859 and flagged as *"a dated formation hiding
inside the perennial Gothic cluster"*, is **not confirmed here**: 244 hits, first
1863, a bump in 1886, decay after 1898, and **no measurable take-off** (band
1859–1882). The shape is a real rise-and-fall — a term with a life and a death —
but the trade series cannot date its birth, and reporting 1859 as agreeing with
S2 would have been a false replication off a smoothing artifact.

**No issue in the window is missing:** 3,487 of 3,487 fetched, 0 failures.

---

## Two limits, unchanged from slice 2

1. **It is the American trade.** The Phase 1 corpus is English-language fiction
   including the whole British canon; these two serials record American
   publication. IA's British holding is 24 items of the *Publishers' Circular*.
   Any regression against the textual series is a **US-side** measurement.
2. **1929 is a hard ceiling** on both sides — the textual corpus for
   public-domain reasons, this series because the IA run ends.

---

## What this hands the next slice

1. **`mystery story` 1896/1906–1909 is a testable prediction for S3.** If the
   textual instrument finds a formation event in that window, the project has a
   *second* datable genre and stops resting on 13 books. This is now the single
   highest-value thing S3 can be pointed at.
2. **Report take-off bands, never take-off points.** The rule is in
   `analyze_reception_series.py`; do not reintroduce a bare take-off date.
3. **The annotation extractor's recall is the remaining soft spot.** 81,900
   annotations from 3,487 issues is ~23/issue against a Weekly Record that ran
   to 150+ entries/week by the 1920s. Raising recall sharpens the second series;
   it does not affect the primary one.
4. **Don't re-sweep to re-argue.** `reception_series.json` holds the per-year
   series and `_data/reception_entries.jsonl.gz` the 1,453 genre-bearing
   annotations with their dates. The 69-minute sweep runs once;
   `analyze_reception_series.py` runs as often as the argument needs.

---

## Artifacts

- `build_reception_series.py` — the sweep. 69 minutes, 3,487 issues, both
  normalisations, the per-book table. OCR cached under
  `~/.cache/literature-mutations/` (**not** `/tmp` — the OS cleared 200MB out
  from under the first attempt at this run).
- `analyze_reception_series.py` — the analysis, with the smoothing-sensitivity
  rule that refuses a date the series cannot support.
- `analyze_term_split.py` → `term_split.json` — the renaming test, three tests
  ranked weakest to strongest, with the casing filter that the dispersion filter
  had to be replaced by.
- `reception_series.json` — per-year series, 11 period terms, both
  normalisations, coverage for all 75 years.
- `reception_clock_trade.json` — the dated clock plus the two findings with
  their denominators.
- `_data/reception_entries.jsonl.gz` — **1,453 dated genre-bearing trade
  annotations**, 1878-11-09 to 1929-12-28. The per-book table.
