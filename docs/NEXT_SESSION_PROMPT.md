Continuing work on `literature-mutations` Phase 2 (author influence network).
Read `docs/PHASE2_INFLUENCE_NETWORK.md` in full first — §7 has the locked
design decisions, §9 has the first validated result, §10 has two follow-ups
closed out 2026-07-23. Don't re-litigate any of it; all three are settled.

**Where things stand:** the pipeline runs end-to-end. `build_bibliography.py`
→ 2,411 cross-referenced works across 108 authors. `build_corpus.py` → 583
resolved to real Gutenberg prose across 77 authors. `build_influence_graph.py`
→ 2,915 directed candidate edges, each carrying two independent similarity
scores (stylistic TF-IDF, conceptual embedding), never merged. Held-out
validation against 130 documented influence pairs (known_influences.json,
LLM-enumerated): stylistic z=0.91 (not significant), conceptual z=9.47
(highly significant). A second, fully independent, non-LLM validation source
was added — `fetch_wikidata_influences.py` pulls Wikidata's structured P737
"influenced by" property (110 pairs, 102 resolvable): stylistic z=2.45
(significant), conceptual z=7.16 (replicates the headline finding). A
density control confirmed the conceptual result isn't primarily a density
artifact (well-represented-authors subset, n=47: conceptual z=6.25). Real
results, not null ones — the dual-signal design is what made this visible.
Everything is committed to `master` and pushed, including the data
(`_data/*.json`, ~59MB total, committed on purpose for posterity).

**Open thread, deliberately left unresolved (§10 tail):** stylistic
similarity is non-significant on the full 130-pair known_influences.json
sample (z=0.91) but turns significant in both narrower independent checks —
the Wikidata pairs (z=2.45) and the well-represented-authors subset (z=2.97).
Two honest readings, not adjudicated: either the full-sample null is
genuinely flat and both narrower checks are small-N noise landing the same
lucky direction, or the full-sample non-significance was itself partly an
artifact that both narrower checks happen to correct. Worth a dedicated pass
before claiming or dismissing a stylistic effect either way.

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
- When a background script's stdout looks suspiciously silent, check the
  actual output file / process network connections directly rather than
  trust the absence of log lines — Python fully buffers stdout when piped
  through `tee` unless run with `-u`.

**Pick up from here — pick one, or something else entirely:**
1. Build the visualization (deliberately deferred until validated data
   existed — it now does, twice over. §6 of the doc has the intended
   interaction pattern, borrowed from `/influences.html` as UI inspiration
   only).
2. Expand past 77 authors for more statistical power (more anchors, or
   loosen the both-model-confirmed threshold in `build_bibliography.py`
   and re-run the corpus resolution step).
3. Chase the open stylistic-signal thread above — a dedicated pass to
   figure out whether it's real or small-N noise (e.g. bootstrap confidence
   intervals on all three samples, or a targeted look at which specific
   pairs drive the narrower checks' significance).
4. Something else entirely.

Don't assume any of these is the right call — ask if it's not obvious which
one Aidan wants, the same way §7's and §10's decisions were made
collaboratively rather than picked unilaterally.
