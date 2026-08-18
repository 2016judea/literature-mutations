Continuing work on `literature-mutations`. **Read
[`docs/RESEARCH-PROGRAM.md`](RESEARCH-PROGRAM.md) in full before touching
anything** — "Standing decisions", "State of play" and "S0" are your brief.
Don't re-litigate the scoping; it was done 2026-08-15 against the real
artifacts, and the four standing decisions were settled with Aidan 2026-08-16.

Phase 2 (author influence) is out of scope — permanently, not just this session.
Its design and results live in
[`docs/PHASE2_INFLUENCE_NETWORK.md`](PHASE2_INFLUENCE_NETWORK.md) and are not
affected by anything here.

**S2 is done** (2026-08-18, [`S2-RECEPTION-CLOCK.md`](S2-RECEPTION-CLOCK.md)) —
don't redo it. What it changed for you is at the bottom of this file. Read that
section before step 2 of the method, not after.

*Prompt last revised 2026-08-18, at the end of the S2 session.*

---

## Your task: S0 — reconstruct the Phase 1 corpus and re-verify the published numbers

**Why this is the blocker.** `_data/books.json` and `_data/canon.json` are absent
from the checkout, and `git ls-files _data` shows they were **never committed** —
only the Phase 2 and S2 files were. Every Phase 1 number in the README, in
`results.json`, and on the live site currently rests on a corpus that exists
nowhere. Four of the seven scoped sessions can't start until it's back.

**Why it's recoverable.** All 345 titles survive in `results.json` →
`communities[].titles` (verified: 345 unique). 166 of them carry author, year,
layout position and community in the `DATA` object embedded in
`genre_network.html`.

### Method

1. Read the 345 titles from `results.json`.
2. Read author + year for the 166 from `genre_network.html`. **Reuse
   `extract_data()` in [`animate_genre_growth.py`](../animate_genre_growth.py)** —
   it already parses that exact embedded object. Do not write a second parser.
3. Re-resolve author + year for the remaining ~179 via Gutendex / Open Library,
   the same path [`gutenberg_ingest.py`](../gutenberg_ingest.py) already uses.
4. Write a reconstructed `_data/canon.json`, then run
   [`build_corpus.py`](../build_corpus.py) to re-fetch real Gutenberg text.
5. Run `analyze.py`. Diff against the checked-in `results.json`.

### Hard rules

- **Do not run `build_canon.py`.** It asks two non-deterministic LLMs to
  enumerate the canon. Re-running it returns a *different* corpus and silently
  invalidates comparison with every published number. The surviving title list
  is the ground truth now. (Both `GEMINI_API_KEY` and `ANTHROPIC_API_KEY` are
  live in `.env` — that is exactly why this rule needs stating.)
- **Log every miss and every substitution.** Gutenberg IDs and editions drift,
  and `build_corpus.py` pulls ~20k words from whatever edition it matches. A
  title that resolves to a different edition is a silent corpus change. Never
  proceed quietly past one.
- **Report and stop on any deviation.** If your numbers disagree with the
  published ones — either direction, any margin — write up the delta and
  **halt**. Do not adopt the reconstruction as the new ground truth, do not
  update the README, do not decide a near-miss is close enough. Aidan calls it
  with the numbers in front of him. A session that rationalizes a 5-book
  shortfall has destroyed the only reproducibility check the project has.
- **Do not touch the live site.** Frozen for the duration.
  `writing-topology/research/index.html` carries three typed stat spans
  (33 splits / 25 merges / 32 births) plus the null model in prose (90 real,
  94 ± 15, z = −0.27). Those figures are currently unreproducible and Aidan has
  **accepted that knowingly** — a logged decision, not an oversight. Don't fix
  it, don't add a disclaimer, don't take it down.
- **Commit the raw pull before you analyse it.** S2's lesson, and S0 is the
  reason the lesson exists: `_data/ngrams_raw.json` is committed so the next
  session verifies rather than re-fetches. Do the same with the resolved
  canon and the fetched text (or its manifest) *as you get it*, not at the end.

### Verification targets

Reproduce these, or document the deviation and its cause:

| figure | published value | source |
|---|---|---|
| corpus size | 345 books / 166 authors | `controls_results.json` |
| null model | 90 real vs 94.1 ± 15.2, z = −0.27 | `results.json.honest_metrics` |
| detective community | n = 13, 1878–1926, std 14.9, **z = −3.04** | `controls_results.json` |
| author confound | 19.5% | `controls_results.json` |
| totals | splits 33 / merges 25 / births 32 | `results.json` |

The eight-community table in `RESEARCH-PROGRAM.md` is the full expected shape.

### Done when

- `_data/books.json` is on disk and the run reproduces the table above, or every
  deviation is documented with its cause.
- The corpus is **committed** — or, if too large, a manifest of
  `(title, author, year, gutenberg_id, sha256)` — so the next session can verify
  rather than trust. Make Phase 1 consistent with Phase 2 so nobody loses a
  corpus this way again.
- A short written verdict: is the published Phase 1 result reproducible, yes or
  no? The destination is a paper — "probably, roughly" is not an answer a
  reviewer accepts, and it isn't one this session should give either.

---

## What "report and stop" does and does not mean

Read this before you hit a deviation, because you probably will: ~179 titles need
re-resolving against a Gutenberg whose editions have drifted since the original
run, and a clean reproduction of all five figures would be the lucky case.

**Halt applies to the numbers, not to the session.** You stop *interpreting*: no
new ground truth, no README edit, no "close enough", no rerunning `build_canon.py`
to make it match. Write the delta up with its cause and hand it to Aidan.

**Then keep working** — on the branch below, not on the thing you just halted.
Idling because a rule fired is a misreading of the rule. What you must not do is
quietly convert a halt into a judgment call.

## If S0 halts (or finishes early): S6 slice 1 — is the cheapest reception source actually there?

S6 is the paper's contribution and the brief is blunt that "starting last puts it
on the critical path." It is weeks of work, so the first slice is not the dataset —
it is a **go/no-go on the cheapest source before committing those weeks.**

The brief's cheapest S6 source is publishers' back-matter advertisements: genre
formation as a dated marketing act, on pages "bound into the Gutenberg and
Internet Archive scans already being downloaded and discarded." `build_corpus.py`
takes ~20k words from the front of each text and throws the rest away, so nobody
here has ever looked at the back matter.

**The probe.** Take a sample of Gutenberg IDs already known to the project, fetch
the **full** text rather than the 20k-word slice, and measure how many carry a
publisher advertisement or series list. Search for the register, not a fixed
string: `BY THE SAME AUTHOR`, `UNIFORM WITH`, `NEW NOVELS`, `<PUBLISHER>'S LIST`,
`CROWN 8vo`, and British price notation (`3s. 6d.`, `6s.`).

**Expect it to possibly fail, and say so if it does.** Gutenberg transcribers
routinely delete publisher ads as not part of the work. A negative result is a
real finding: it means S6 must come from Internet Archive page scans of the
physical book, which is a different and more expensive pipeline. Determining that
in one session is worth far more than assuming it either way.

**Done when.** A count out of N, a couple of verbatim examples if any survive, and
a one-line go/no-go on whether Gutenberg back matter can carry S6 — or whether
Internet Archive is required. Do not start building the reception series itself.

**The rule that governs S6 governs the probe:** period evidence only. A modern
retrospective label reintroduces exactly the circularity of P1.

---

## What S2 established that changes your expectations

**1. Do not trust `held_out_label` for anything but "this cluster is
recognised".** Three of eight labels name a genre their own cluster is not — the
one labelled "Science fiction" has the vocabulary *castle, veil, trembled*, and
"Best Books Ever Listings" is a popularity shelf. Dating a cluster by its label
instead of its own `top_terms` moves the answer **+62 to +142 years** and invents
20th-century emergences for modes named before 1800.
[`emit_paper_figures.py:70-74`](../emit_paper_figures.py#L70-L74) found the same
mismatch independently. **If S0's reconstruction makes you reach for a label,
reach for the vocabulary instead.**

**2. The detective result is now externally licensed.** Its name takes off in 1889
(1883/1897 at 5 %/20 % of peak) against books of 1878–1926, peaking 1932. That is
independent of the text pipeline, so if your S0 reconstruction breaks detective
specifically, the reconstruction is the suspect — not the finding.

**3. The null holds on both clocks.** Five of eight genre names were already
current before 1800. A perennial mode looks perennial in a source that never saw
the corpus.

**4. `sensation novel` (take-off 1859, 16 y wide, peak 1867) is a dated formation
hiding inside the "perennial" Gothic cluster.** A lead for S3/S4, not a result,
and exactly the kind of thing 166 books cannot settle — see the sub-clustering
note in the brief.

**5. A verification script is not automatically right.** The S2 doc's typed tables
were checked against the JSON by a script that reported 19 mismatches, then 5 —
all of them the checker's own scoping bugs, none of them real. Confirm the checker
finds the row it thinks it found before believing what it says about the data.
This matters more in S0 than it did in S2: there, a false "matches published" is
the one failure the whole session exists to prevent.

**6. The site's figure idiom, if you end up emitting one.** Inline SVG with the
classes `.ed .ax .nd .ln .ac .acs .acd .band .lbl` at `viewBox` width 680, bound
to `--ink2 / --faint / --accent` so it adapts to light and dark for free. Never a
PNG. `emit_reception_figure.py` is the current example and writes a standalone
preview page so figures can be inspected while the site stays frozen.
