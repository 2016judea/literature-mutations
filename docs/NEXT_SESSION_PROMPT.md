Continuing work on `literature-mutations`. Read `docs/PHASE2_INFLUENCE_NETWORK.md`
in full first — §7 has the locked design decisions, §9-10 have the two
validated Phase 2 results, §11 has the visualization build. Don't re-litigate
any of it.

**Where things stand:** both halves of the pipeline (Phase 1 genre recovery,
Phase 2 author-influence) now have hand-styled, click-to-explore
visualizations live on the personal site, in the same visual/interaction
language — this was the one open item left from last session's pick list
(#3, "iterate on the visualization").

`build_bibliography.py` → 2,411 cross-referenced works across 108 authors.
`build_corpus.py` → 583 resolved to real Gutenberg prose across 77 authors
(Phase 2) / 345 canon novels across 166 authors (Phase 1, one book/author
after de-trending). `build_influence_graph.py` → 2,915 directed candidate
edges, two independent similarity scores (stylistic TF-IDF, conceptual
embedding), never merged. Held-out validation against 130 documented
influence pairs: stylistic z=0.91 (not significant), conceptual z=9.47
(highly significant), replicated on Wikidata (z=7.16) and a density-control
subset (z=6.25). `controls.py` → genre communities, controlled for corpus
density, style drift, and author voice: 8 genre clusters recovered, each
matched to a held-out Gutenberg label; exactly one (detective fiction) is
temporally concentrated enough to call a genuine emergence (z≈-3.0); the
rest are perennial modes; a null model can't distinguish real chronology
from shuffled years overall (z=-0.27).

**New this session (2026-07-23):** `visualize_genres.py` was added,
rebuilding Phase 1's old generic two-panel Plotly export
(`visualize.py` → `literary_genres.html`) as a custom interactive page in
the exact visual/interaction grammar of Phase 2's
`visualize_influence.py` → `influence_network.html`: click a novel, or a
genre pill, and its cluster lights up with a side panel (genre name, z-score,
top distinctive vocabulary, member novels) — plus a secondary
temporal-concentration panel (which genre is "born" vs. perennial) that's
also click-linked to the same highlighting. Output: `genre_network.html`.

Data-provenance note, since it's not obvious from the script alone:
`_data/books.json` (the real Gutenberg full-text corpus) isn't present in
this checkout — rebuilding it means re-running `build_canon.py` +
`build_corpus.py` against Gutenberg/LLM APIs, which wasn't necessary this
session. Instead `visualize_genres.py` extracts the already-computed,
already-published per-book layout (title/author/year, x/y position, genre
assignment, edges) straight out of `literary_genres.html`'s embedded Plotly
JSON — that HTML is itself a checked-in, real run — and cross-references
`controls_results.json` for each community's `top_terms` (the one field the
Plotly hover text doesn't carry). **If `visualize.py` is ever rerun against
a fresh corpus, rerun `visualize_genres.py` immediately after** so the two
stay in sync — same caution as the existing note below about
`visualize_influence.py`.

That work lives in the **`writing-topology`** repo
(`/Users/aidan/Desktop/writing-topology`), not this one. The site's
`research/literature-mutations.html` now has three pill-tabs instead of two:
"Explore the genres" (new) / "Explore the network" (Phase 2, still the
default-active tab, unchanged) / "Read the paper". `research/genre-network.html`
is a copy of this repo's `genre_network.html` with the same two relative
links patched to GitHub (`docs/PHASE2_INFLUENCE_NETWORK.md`, `README.md`)
that `influence-network.html` already needed — same reason: they don't
resolve when hosted standalone. It **replaced** the old static Plotly
`genre-network.html` that used to sit there (which was itself an iframe
embedded inline in the paper's old §8 Fig. 4 — that inline embed was removed
and replaced with a link back up to the new "Explore the genres" tab,
mirroring how §9 already links back to "Explore the network" rather than
re-embedding it). If `visualize_genres.py` is rerun and regenerates
`genre_network.html`, the same two link patches need to be reapplied before
recopying to the site.

Both new pieces (the script's output, and the tab-click behavior on the
live page) were screenshot-verified with headless Chrome — including
serving the site over a local HTTP server (not just `file://`) to confirm
the iframe's absolute path (`/research/genre-network.html`) actually
resolves the way it will on Vercel, and clicking through the new tab to
confirm no content clipping at the iframe's fixed height (1480px
desktop/1860px mobile, shared with the Phase 2 iframe — genre-network.html's
real content height is ~1350px, so there's comfortable slack).

**Open thread, still deliberately unresolved (unchanged since 2026-07-23):**
stylistic similarity is non-significant on the full 130-pair
known_influences.json sample (z=0.91) but turns significant in both narrower
independent checks — the Wikidata pairs (z=2.45) and the
well-represented-authors subset (z=2.97). Two honest readings, not
adjudicated: either the full-sample null is genuinely flat and both narrower
checks are small-N noise landing the same lucky direction, or the
full-sample non-significance was itself partly an artifact that both
narrower checks happen to correct. Worth a dedicated pass before claiming or
dismissing a stylistic effect either way.

**Environment setup** (not obvious from the scripts alone): this repo needs
a local venv — `python3 -m venv .venv && .venv/bin/pip install -r
requirements.txt` — because Homebrew's Python blocks global pip installs.
API keys (`GEMINI_API_KEY`, `ANTHROPIC_API_KEY`) go in a local `.env`
(gitignored); source it with `set -a && source .env && set +a` before
running anything that calls Gemini/Claude. Both keys can be copied from
`/Users/aidan/Desktop/bricks/.env` if missing. `fetch_wikidata_influences.py`
needs no key (public Wikidata API), just a descriptive User-Agent header
(Wikidata/Wikipedia etiquette — already set in the script).

**Operational lessons from past sessions, worth keeping in mind:**
- LLM API calls (Gemini/Claude) in this pipeline have hung for 15-30+
  minutes on rare occasions — well past their own retry/timeout budgets
  (looks like DNS-resolution hangs that bypass `urllib`'s timeout param).
  `build_influence_graph.py` sets a global `socket.setdefaulttimeout()`
  backstop and checkpoints its embedding loop per-author
  (`_data/author_embeddings_cache.json`); apply the same pattern to any new
  long LLM-calling loop rather than assuming it'll behave.
- Always verify a new API endpoint/model name — or a design assumption about
  external data — with one live call before wiring it into a loop across all
  authors. This caught a real problem 2026-07-23 (Phase 2 design): the
  design doc originally proposed parsing Wikipedia's `influences`/`influenced`
  infobox fields, but a live check across all 77 authors first found only 2
  populated (the fields were deprecated by Wikipedia editors years ago) —
  caught before any pipeline code was built around a dead approach, and
  pivoted to Wikidata's P737 property instead, which had real coverage
  (44/77 authors).
- The same discipline applies to UI/interaction code, not just data
  pipelines: a real bug in the Phase 2 visualization (a clicked node landing
  exactly under its own detail panel, since the panel overlays the canvas
  rather than participating in layout) was only caught by actually
  triggering the click and screenshotting the result (headless Chrome + a
  temporary URL-param auto-click hook), not by reading the JS and reasoning
  it should work. Don't skip the live check just because there's no
  interactive browser session available — headless screenshot verification
  is cheap. When hosting the artifact elsewhere too, verify the hosted copy
  the same way, not just the repo-local one — the Phase 2 iframe embed
  initially clipped the bottom of the page because the guessed container
  height was measured wrong; only caught by screenshotting the actual
  embedded result. This session repeated the same check for the Phase 1
  genre-network embed, and additionally found that a naive `file://` test of
  the hosted page gives false-negative broken-image icons for its
  absolute-path iframe — serve it over `python3 -m http.server` locally
  instead to test it the way Vercel actually will.
- When a background script's stdout looks suspiciously silent, check the
  actual output file / process network connections directly rather than
  trust the absence of log lines — Python fully buffers stdout when piped
  through `tee` unless run with `-u`.

**Pick up from here — pick one, or something else entirely:**
1. Chase the open stylistic-signal thread above — a dedicated pass to
   figure out whether it's real or small-N noise (e.g. bootstrap confidence
   intervals on all three samples, or a targeted look at which specific
   pairs drive the narrower checks' significance).
2. Expand past 77 authors (Phase 2) / 345 novels (Phase 1) for more
   statistical power (more anchors, or loosen the both-model-confirmed
   threshold in `build_bibliography.py`/`build_canon.py` and re-run corpus
   resolution).
3. Regenerate the Phase 1 corpus from scratch (`build_canon.py` →
   `build_corpus.py` → `controls.py` → `visualize.py` → `visualize_genres.py`)
   so the genre network stops depending on `literary_genres.html` as its
   data source — would also let the two visualizations' book/author counts
   move independently instead of Phase 1 being pinned to whatever the last
   `visualize.py` run happened to produce.
4. Something else entirely.

Don't assume any of these is the right call — ask if it's not obvious which
one Aidan wants, the same way §7's, §10's, and §11's decisions, last
session's website work, and this session's genre-network rebuild were all
made collaboratively rather than picked unilaterally.
