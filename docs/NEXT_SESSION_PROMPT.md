Continuing work on `literature-mutations`. **Read
[`docs/RESEARCH-PROGRAM.md`](RESEARCH-PROGRAM.md) in full before touching
anything** — "Standing decisions" and "State of play" are your brief. Don't
re-litigate the scoping; it was done 2026-08-15 against the real artifacts, and
the four standing decisions were settled with Aidan 2026-08-16.

Phase 2 (author influence) is out of scope — permanently, not just this session.
Its design and results live in
[`docs/PHASE2_INFLUENCE_NETWORK.md`](PHASE2_INFLUENCE_NETWORK.md) and are not
affected by anything here.

**Three sessions are done; do not redo them.**

| session | verdict | doc |
|---|---|---|
| **S0** — reconstruct the corpus | corpus back on disk and committed; detective reproduces at z = −3.04; Louvain event counts do **not** reproduce and cannot (seed noise ±7.6) | [`S0-CORPUS-RECONSTRUCTION.md`](S0-CORPUS-RECONSTRUCTION.md) |
| **S2** — the reception clock (Ngrams) | the two clocks agree on detective fiction (name take-off 1889); the null holds on both | [`S2-RECEPTION-CLOCK.md`](S2-RECEPTION-CLOCK.md) |
| **S6 slice 1** — Gutenberg back matter | **no-go**: 4 publisher ads in 343 books / 42.2M words | [`S6-SLICE1-BACKMATTER-PROBE.md`](S6-SLICE1-BACKMATTER-PROBE.md) |
| **S6 slice 2** — the trade catalogue | **GO**, and no page-scan OCR needed — read this in full, it is your brief | [`S6-SLICE2-TRADE-CATALOGUE.md`](S6-SLICE2-TRADE-CATALOGUE.md) |

*Prompt last revised 2026-08-26, at the end of the S6 slice 2 session.*

---

## Your task: S6 slice 3 — build the reception series

S6 is the paper's contribution (standing decision: *"S0–S5 substantially rebuild
machinery Underwood already published; S6 is the contribution"*). Slices 1 and 2
were go/no-go probes. This is the first slice that builds.

**What slice 2 established, so you don't re-establish it.** *Publishers' Weekly*,
**2,965 dated issues 1872–1929**, on Internet Archive as free `_djvu.txt` — no
lending restriction, no OCR cost, ~51 issues/year. The register control fires
5/5 on 8.8M words, so it is genuinely trade material. The artifact is the
**Weekly Record annotation**: one dated line per book, and PW's own section
masthead declares the policy — *"The annotations are descriptive, not critical;
intended to place not to judge the books"* — which is the trade calling its own
annotation classificatory. On a 232-issue sample the Weekly Record was locatable
in 176 issues holding 13,743 entries, **1,263 of them (9.2%) genre-bearing**.

### Method

1. **Fix segmentation first — it is the whole cost.** A naive heading match
   locates the Weekly Record in **76%** of issues; 24% lose the heading to OCR.
   Raise that number before spending anything else.
   `record_yield()` in [`probe_trade_catalogue.py`](../probe_trade_catalogue.py)
   is the current 76% version, and its end marker fails often enough that it
   caps the region at 60,000 characters. Both are the target.
2. **Splice the window back to 1852** before computing any take-off. IA holds
   **532 items** of *The American Publishers' Circular and Literary Gazette*
   (227 in 1852–59, 260 in 1860–69), same collection shape, same free OCR, and
   its 1856 issues already carry genre-act headings ("CHEAP FICTION.", "NEW
   LIBRARY OF STANDARD FICTION"). Three of eleven terms are left-censored by the
   1872 boundary, `sensation novel` (S2 take-off 1859) worst of all.
3. **Spend the sample density — it is free.** Slice 2 read 4 issues/year (7.8%
   of the run) and the series was too sparse to date anything but
   `mystery story`. Go to every issue, or state what you dropped and why.
4. **Parse to entries, not to word counts.** The deliverable is a dated per-book
   table — `(date, author, title, publisher, price, annotation, genre_terms)` —
   not a frequency curve. The curve is derived from the table afterwards.
5. **Then, and only then, the series.** Per-genre, per-year, from entries.
   Regress it against the textual series when S3 exists.

### Hard rules

- **Period evidence only.** The S6 rule, and the reason the whole program
  exists: a modern retrospective label reintroduces exactly the circularity of
  P1. Everything in PW is period by construction — keep it that way, and do not
  join a modern genre label onto an entry to "help".
- **Separate the two artifacts.** Slice 1's rule 3, still binding: *"by the same
  author"* lists are an **author** artifact; "GABORIAU'S DETECTIVE STORIES" is a
  **genre** act. Only the second measures genre formation. Never sum them.
- **Reuse the estimator, do not reimplement it.** `smooth`, `takeoff_year`,
  `mass_percentiles` and `first_attestation` come from
  [`analyze_reception_clock.py`](../analyze_reception_clock.py). A take-off
  measured with the same estimator is *comparable* to S2's; one measured with a
  new estimator is merely similar to it.
- **Do not read `detective story`'s 20% take-off of 1904 as a date.** It is
  right-censored: the term peaks at 1929, the window edge, still rising.
  Re-measure after the splice.
- **Controls before counts.** Slice 2's genre-act detector shipped a real bug
  that the positive control caught first — the original required a heading to
  *end* in SERIES/LIBRARY/NOVELS/STORIES and missed three of five real examples,
  including slice 1's best find. Run the control before you believe a number.
  And S2's lesson 5: a verification script is not automatically right.
- **Commit the raw pull before you analyse it.** S0's and S2's lesson. The
  identifiers are in `trade_catalogue_probe.json`; the OCR cache at
  `/tmp/ia_trade_text` is not committed (~59MB and re-fetchable), but a full-run
  cache will be much larger — commit a manifest, not the text.
- **Do not touch the live site.** Frozen for the duration of the program, by
  standing decision. `writing-topology/research/index.html` carries figures that
  are knowingly unreproducible; that is a logged decision, not an oversight.
- **Report and stop on any deviation** from a published number. You write up the
  delta and halt; Aidan calls it with the numbers in front of him. Halt applies
  to the *numbers*, not to the session — then keep working on the branch below.

### Done when

- A dated per-book table from the Weekly Record, spanning at least 1872–1929 and
  ideally 1852–1929, with segmentation coverage stated as a percentage.
- A per-genre annual series derived from that table, with left- and
  right-censoring stated per term.
- **A stated verdict on `mystery story`.** Slice 2 found it absent for 29
  consecutive years and first attested 1901 at 4 issues/year. At full density,
  does that hold? It is the project's best chance at a *second* datable genre,
  and the only positive result currently rests on 13 books.
- Raw pull or manifest committed, so the next session verifies rather than
  re-fetches.

### Two limits to carry into the write-up, not to solve

- **It is the American trade.** The Phase 1 corpus is English-language fiction
  including the whole British canon; PW records American publication. IA's
  British holding is 24 items of the *Publishers' Circular*. Any regression of a
  PW-derived series against the textual series is a **US-side** measurement and
  the paper has to say so.
- **PW never subdivides Fiction.** Its monthly `CLASS SYNOPSIS` classifies
  (Biography / Description, Geography, Travel / Domestic and Social / Education,
  Language / Fiction) but Fiction is one undivided class throughout. The formal
  classification therefore cannot date a genre. The annotation can. Do not go
  looking for a fiction sub-class; it is not there.

---

## If S6 slice 3 halts (or finishes early): S1 — the provenance audit

Unblocked since S0, an afternoon's work, and it addresses **P1** — the only
surviving positive result was drawn from a sampling frame that recruited partly
*by genre*. Full brief in [`RESEARCH-PROGRAM.md`](RESEARCH-PROGRAM.md) § S1. The
one-line permanent fix at `build_canon.py:147-149` (persist `"lists"` alongside
the count) **must land regardless of what the audit finds**.

**Do not run `build_canon.py`.** Two non-deterministic LLMs return a different
canon and silently invalidate comparison with every published number. S1 step 2
re-runs *only the four genre-bucket prompts*, read-only, and must not overwrite
`_data/canon.json` or `_data/books.json`.
