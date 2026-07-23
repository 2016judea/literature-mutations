Continuing work on `literature-mutations` Phase 2 (author influence network).
Read `docs/PHASE2_INFLUENCE_NETWORK.md` in full first — §7 has the locked
design decisions, §9-10 have the two validated results, §11 has the
visualization build. Don't re-litigate any of it.

**Where things stand:** the pipeline runs end-to-end, has a visualization on
top of it, and that visualization is now live on the personal site — the one
item from last session's pick list that's actually done.
`build_bibliography.py` → 2,411 cross-referenced works across 108 authors.
`build_corpus.py` → 583 resolved to real Gutenberg prose across 77 authors.
`build_influence_graph.py` → 2,915 directed candidate edges, each carrying
two independent similarity scores (stylistic TF-IDF, conceptual embedding),
never merged. Held-out validation against 130 documented influence pairs
(known_influences.json, LLM-enumerated): stylistic z=0.91 (not significant),
conceptual z=9.47 (highly significant). A second, independent, non-LLM
validation source (`fetch_wikidata_influences.py`, Wikidata's P737 property,
102 resolvable pairs) replicated it: stylistic z=2.45 (significant),
conceptual z=7.16 (replicates). A density control confirmed the conceptual
result isn't primarily a density artifact (well-represented subset, n=47:
conceptual z=6.25). `visualize_influence.py` → `influence_network.html` — an
interactive, chronologically-laid-out, dual-signal graph (click an author,
their edges light up, side panel shows both scores per connection plus real
citation notes where documented) — was built and screenshot-verified
(headless Chrome, actual click interaction) 2026-07-23.

**New this session (2026-07-23):** `influence_network.html` is hosted at
`aidanjude.vercel.app/research/literature-mutations.html` and is now that
page's landing hero — the page opens on the interactive graph, with a
pill-tab toggle ("Explore the network" / "Read the paper") to switch to the
full academic writeup (2021 proposal + 2026 postscript, now with a new §9
covering both Phase 2 validation passes and the open stylistic-signal
question). That work lives in the **`writing-topology`** repo
(`/Users/aidan/Desktop/writing-topology`), not this one —
`research/literature-mutations.html` is the page, `research/influence-network.html`
is a **copy** of this repo's `influence_network.html` with two links patched
to point at GitHub instead of relative repo paths (`docs/PHASE2_INFLUENCE_NETWORK.md`
and `README.md`, which don't resolve when hosted standalone). If
`visualize_influence.py` is rerun and regenerates `influence_network.html`,
those two link patches need to be reapplied before recopying to the site —
they will not survive a blind `cp`. `README.md` here was also expanded with
the full Phase 2 results table (both validation sources + density control)
and a link to the live hosted page.

**Open thread, still deliberately unresolved (§10 tail, unchanged since
2026-07-23):** stylistic similarity is non-significant on the full 130-pair
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
  authors. This caught a real problem 2026-07-23: the design doc originally
  proposed parsing Wikipedia's `influences`/`influenced` infobox fields, but
  a live check across all 77 authors first found only 2 populated (the
  fields were deprecated by Wikipedia editors years ago) — caught before any
  pipeline code was built around a dead approach, and pivoted to Wikidata's
  P737 property instead, which had real coverage (44/77 authors).
- The same discipline applies to UI/interaction code, not just data
  pipelines: a real bug in the visualization (a clicked node landing exactly
  under its own detail panel, since the panel overlays the canvas rather
  than participating in layout) was only caught by actually triggering the
  click and screenshotting the result (headless Chrome + a temporary
  URL-param auto-click hook), not by reading the JS and reasoning it should
  work. Don't skip the live check just because there's no interactive
  browser session available — headless screenshot verification is cheap.
  When hosting the artifact elsewhere too, verify the hosted copy the same
  way, not just the repo-local one — this session's iframe embed initially
  clipped the bottom of the page because the guessed container height was
  measured wrong; only caught by screenshotting the actual embedded result.
- When a background script's stdout looks suspiciously silent, check the
  actual output file / process network connections directly rather than
  trust the absence of log lines — Python fully buffers stdout when piped
  through `tee` unless run with `-u`.

**Pick up from here — pick one, or something else entirely:**
1. Chase the open stylistic-signal thread above — a dedicated pass to
   figure out whether it's real or small-N noise (e.g. bootstrap confidence
   intervals on all three samples, or a targeted look at which specific
   pairs drive the narrower checks' significance).
2. Expand past 77 authors for more statistical power (more anchors, or
   loosen the both-model-confirmed threshold in `build_bibliography.py`
   and re-run the corpus resolution step).
3. Iterate on the visualization itself — e.g. a toggle to rank/color edges
   by stylistic instead of conceptual similarity (currently conceptual-only,
   since that's the signal that replicated), or surface the
   same-form/cross-form split (§7.3's other reported finding) more directly
   in the UI rather than just per-edge in the panel. Remember: any change
   here needs to be re-synced to the hosted copy in `writing-topology`
   (see "New this session" above).
4. Something else entirely.

Don't assume any of these is the right call — ask if it's not obvious which
one Aidan wants, the same way §7's, §10's, and §11's decisions — and this
session's website work — were made collaboratively rather than picked
unilaterally.
