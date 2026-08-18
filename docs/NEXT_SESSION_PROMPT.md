Continuing work on `literature-mutations`. **Read
[`docs/RESEARCH-PROGRAM.md`](RESEARCH-PROGRAM.md) in full before touching
anything** — "Standing decisions", "State of play" and "S0" are your brief.
Don't re-litigate the scoping; it was done 2026-08-15 against the real
artifacts, and the four standing decisions were settled with Aidan 2026-08-16.

Phase 2 (author influence) is out of scope — permanently, not just this session.
Its design and results live in
[`docs/PHASE2_INFLUENCE_NETWORK.md`](PHASE2_INFLUENCE_NETWORK.md) and are not
affected by anything here.

---

## Your task: S0 — reconstruct the Phase 1 corpus and re-verify the published numbers

**Why this is the blocker.** `_data/books.json` and `_data/canon.json` are absent
from the checkout, and `git ls-files _data` shows they were **never committed** —
only the Phase 2 files were. Every Phase 1 number in the README, in
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
- **Report and stop on any deviation.** This is a standing decision, not a
  judgment call. If your numbers disagree with the published ones — in either
  direction, by any margin — write up the delta and **halt**. Do not adopt the
  reconstruction as the new ground truth, do not update the README, do not
  decide a near-miss is close enough. Aidan calls it with the numbers in front
  of him. A session that rationalizes a 5-book shortfall has destroyed the only
  reproducibility check the project has.
- **Do not touch the live site.** It is frozen for the duration of the program.
  `writing-topology/research/index.html` carries three typed stat spans
  (33 splits / 25 merges / 32 births) plus the null model in prose (90 real,
  94 ± 15, z = −0.27). Those figures are currently unreproducible and Aidan has
  **accepted that knowingly** for the duration — it is a logged decision, not an
  oversight. Don't fix it, don't add a disclaimer, don't take it down.

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
  `(title, author, year, gutenberg_id, sha256)` is, so the next session can
  verify rather than trust. Phase 2's `_data` is committed; make Phase 1
  consistent so nobody loses a corpus this way again.
- A short written verdict: is the published Phase 1 result reproducible, yes or
  no? The destination is a paper — "probably, roughly" is not an answer a
  reviewer accepts, and it isn't one this session should give either.

---

## S2 is already done — don't redo it

The Google Ngrams reception clock ran 2026-08-18. Findings in
[`S2-RECEPTION-CLOCK.md`](S2-RECEPTION-CLOCK.md); code is `pull_ngrams.py` →
`analyze_reception_clock.py` → `emit_reception_figure.py`, and the raw pull is
committed at `_data/ngrams_raw.json` so nothing needs re-fetching.

**The two clocks agree on detective fiction** (name take-off 1889 against books of
1878–1926, name peaking 1932), and the null holds from the reception side as well.
S2 recomputed **no** published number, so the drift rule was never engaged — the
reproducibility question above is still entirely open and still yours.

Two S2 results change what you should expect downstream:

- **Do not trust `held_out_label` for anything but "this cluster is recognised".**
  Three of eight labels name a genre their cluster is not, and dating a cluster by
  its label instead of its own `top_terms` moves the answer +62 to +142 years.
  `emit_paper_figures.py:70-74` found the same thing independently. If S0's
  reconstruction makes you reach for a label, reach for the vocabulary instead.
- **`sensation novel` looks like a real dated formation (1859, 16 y wide, peak
  1867) hiding inside the "perennial" Gothic cluster.** That is a lead for
  S3/S4, not a result — and it is exactly the kind of thing 166 books cannot
  settle, per the sub-clustering note in the brief.
