Continuing work on `literature-mutations` Phase 2 (author influence network).
Read `docs/PHASE2_INFLUENCE_NETWORK.md` in full first — §7 has the locked
design decisions, §9 has the first validated result. Don't re-litigate
either; both are settled.

**Where things stand:** the pipeline runs end-to-end. `build_bibliography.py`
→ 2,411 cross-referenced works across 108 authors. `build_corpus.py` → 583
resolved to real Gutenberg prose across 77 authors. `build_influence_graph.py`
→ 2,915 directed candidate edges, each carrying two independent similarity
scores (stylistic TF-IDF, conceptual embedding), never merged. Held-out
validation against 130 documented influence pairs: stylistic z=0.91 (not
significant), conceptual z=9.47 (highly significant). Real result, not a
null one — the dual-signal design is what made it visible. Everything is
committed to `master` and pushed, including the data (`_data/*.json`, ~59MB
total, committed on purpose for posterity — see git log for the reasoning).

**Environment setup** (not obvious from the scripts alone): this repo needs
a local venv — `python3 -m venv .venv && .venv/bin/pip install -r
requirements.txt` — because Homebrew's Python blocks global pip installs.
API keys (`GEMINI_API_KEY`, `ANTHROPIC_API_KEY`) go in a local `.env`
(gitignored); source it with `set -a && source .env && set +a` before
running anything that calls Gemini/Claude. Both keys can be copied from
`/Users/aidan/Desktop/bricks/.env` if missing.

**Operational lessons from last session, worth keeping in mind:**
- LLM API calls (Gemini/Claude) in this pipeline have hung for 15-30+
  minutes on rare occasions — well past their own retry/timeout budgets
  (looks like DNS-resolution hangs that bypass `urllib`'s timeout param).
  `build_influence_graph.py` now sets a global `socket.setdefaulttimeout()`
  backstop and checkpoints its embedding loop per-author
  (`_data/author_embeddings_cache.json`); apply the same pattern to any new
  long LLM-calling loop rather than assuming it'll behave.
- Always verify a new API endpoint/model name with one live test call before
  wiring it into a loop — wrong model names or endpoint shapes fail in ways
  that aren't always an obvious error (one attempt cost 27 minutes hung on
  a bad assumption about Gemini's batch-embedding endpoint).
- When a background script's stdout looks suspiciously silent, check the
  actual output file / process network connections directly rather than
  trust the absence of log lines — Python fully buffers stdout when piped
  through `tee` unless run with `-u`.

**Pick up from here — pick one, or something else entirely:**
1. Build the visualization (deliberately deferred until validated data
   existed — it now does; §6 of the doc has the intended interaction
   pattern, borrowed from `/influences.html` as UI inspiration only).
2. Expand past 77 authors for more statistical power (more anchors, or
   loosen the both-model-confirmed threshold in `build_bibliography.py`
   and re-run the corpus resolution step).
3. A second, independent held-out validation source beyond the LLM-
   enumerated `known_influences.json` (real literary-criticism citations,
   e.g. Wikipedia infobox "influenced by" fields) to strengthen §9's result.
4. Port over the corpus-density control (§5 point 1) that wasn't explicitly
   done for Phase 2 — noted as a gap at the end of §9.

Don't assume any of these is the right call — ask if it's not obvious which
one Aidan wants, the same way §7's decisions were made collaboratively
last session rather than picked unilaterally.
