# Phase 2 — Author Influence Network

**Status:** first real, validated result landed 2026-07-22 (see §9); an
independent validation source and a density control closed out 2026-07-23
(see §10). Design decided 2026-07-21 (§7); built end-to-end same week.
The visualization deferred in §6 was built 2026-07-23 — see §11.
**Author of this doc:** Claude, at Aidan's request, 2026-07-21.

---

## 0. Why this exists

The 2021 proposal ([`docs/PROPOSAL.md`](PROPOSAL.md)) wanted to trace how literature's
forms *mutate and influence each other* over time. The 2026 rebuild (this repo,
see main [`README.md`](../README.md)) delivered a rigorous pipeline and two honest
results — genres are recoverable from prose alone (robust), and there is no
global "mutation rate" (null). Both results are about **genre**, at the
**corpus** level, capped at the pre-1929 public-domain ceiling.

Aidan's read of it, in his own words: *"I think this was the true aspiration of
my research back then."* Not genre clustering — **tracing influence between
specific authors, across time.** That's what this phase is.

It reuses the interaction language of `/influences.html` on the personal site
(a small graph: trunk nodes descending into root nodes, click to traverse, shared
roots merge) as UI inspiration only. Everything else about that page is the
opposite of this project and must **not** carry over. See §1.

---

## 1. Non-goals — read this before writing any code

`/influences.html` was a personal, hand-curated artifact: six quotes Aidan
likes, traced to roots via (a) his own Goodreads read-dates and (b) citations
to literary critics ("Harold Bloom says McCarthy descends from Melville and
Faulkner"). That was fine for a personal page. **None of it is a valid method
for this project:**

- **No read-dates, no personal reading history, no "which quote Aidan likes
  more."** His Quotes DB is used for exactly one thing — see §2 — and nothing
  else about him enters the research.
- **No citation-as-edge.** "A critic said X influenced Y" is a fine *validation*
  check (the same role Gutenberg subject-labels played in Phase 1 — held out,
  never used to build edges), but it is not measured evidence and must never be
  the primary signal. The whole discipline of this repo is "the signal is
  always real authorial prose" (README, verbatim) — that rule is the point of
  redoing this properly instead of just extending the `influences.html` graph.
- **Not a rehash of the genre question.** This is author-to-author, directed,
  and time-constrained (§4) — structurally a different graph than Phase 1's
  undirected genre-similarity graph.

---

## 2. Seed authors

Pulled live from Aidan's Notion "Quotes DB" (284 rows, see the `quotes-db`
memory in his assistant's memory store for provenance) on 2026-07-21. This is
**only a seed list** — a way to pick an author set that's actually interesting
to Aidan, not a dataset the analysis depends on. 57 distinct authors:

| Author | Quotes | Author | Quotes |
|---|---|---|---|
| Cormac McCarthy | 57 | Ralph Waldo Emerson | 1 |
| Raymond Chandler | 20 | Percy Bysshe Shelley | 1 |
| F. Scott Fitzgerald | 18 | Kurt Vonnegut | 1 |
| Ayn Rand | 17 | Ken Kesey | 1 |
| Herman Melville | 14 | John Williams | 1 |
| Jack Kerouac | 13 | Jay McInerney | 1 |
| Denis Johnson | 10 | James Joyce | 1 |
| Bret Easton Ellis | 9 | J. D. Vance | 1 |
| John Fante | 8 | Iain Banks | 1 |
| Joan Didion | 8 | Homer | 1 |
| Hunter S. Thompson | 8 | G.W.F. Hegel | 1 |
| Albert Camus | 7 | Edgar Allan Poe | 1 |
| Friedrich Nietzsche | 6 | Daphne du Maurier | 1 |
| Plato | 5 | Chuck Palahniuk | 1 |
| John Steinbeck | 5 | Christopher Paolini | 1 |
| William Faulkner | 4 | Carlos Ruiz Zafón | 1 |
| Virginia Woolf | 4 | Alexander Hamilton | 1 |
| Richard Brautigan | 4 | William H. Gass | 1 |
| Dan Simmons | 4 | William Gay | 1 |
| Dalton Trumbo | 4 | William Gass | 1 |
| Sam Harris | 3 | Wendell Berry | 1 |
| Numa Denis Fustel de Coulanges | 3 | Walker Percy | 1 |
| David Foster Wallace | 3 | Vincent Bugliosi | 1 |
| Anthony Bourdain | 3 | T.S. Eliot | 1 |
| Walt Whitman | 2 | | |
| Thomas Wolfe | 2 | | |
| Thomas Paine | 2 | | |
| Marcus Aurelius | 2 | | |
| John Muir | 2 | | |
| Friedrich Hölderlin | 2 | | |
| Ernest Hemingway | 2 | | |
| E.E. Cummings | 2 | | |
| Don Carpenter | 2 | | |
| Charles Simic | 2 | | |

**Reading it:** heavy skew to a personal core (McCarthy alone is a fifth of the
whole DB), a long tail of one-quote authors, and a span from antiquity (Plato,
Marcus Aurelius, Homer) through 2016 (J.D. Vance). The center of mass is
**mid-to-late-20th-century American prose** — Southern Gothic, hardboiled noir,
Lost Generation, Beat — which is the entire problem in §3.

To re-pull this list fresh (Notion state may have changed):
```sql
SELECT Author, COUNT(*) as n FROM "collection://4323abdb-2dd0-4244-aea7-4c7b8b4178d7"
GROUP BY Author ORDER BY n DESC
```
via the Notion MCP `query-data-sources` tool, or ask Claude to re-run it.

---

## 3. The central problem: most of these authors are not public domain

Phase 1's entire corpus strategy (`build_canon.py` → `build_corpus.py`) leans
on the US public-domain cutoff (~1929 and rolling) via Project Gutenberg. The
existing README already names the consequence as an open problem: *"Pre-1929
ceiling... postmodernism are out of reach without a licensed-text or excerpt
source."* This phase runs straight into that wall, because Aidan's actual
favorite authors are exactly the authors it excludes.

Rough triage of the 57 (verify per-work, not per-author — publication *year*
is what matters, not author death-year; an author can straddle the line, e.g.
Fitzgerald: *Gatsby* 1925 is PD, *Tender Is the Night* 1934 is not):

- **Safely pre-1929 / PD:** Melville, Plato, Nietzsche, Marcus Aurelius,
  Whitman, Paine, Muir, Hölderlin, Emerson, Shelley, Homer, Hegel, Poe,
  Hamilton, Fustel de Coulanges, early Joyce, early Eliot. ≈15–17 authors —
  and note this subset skews philosophy/poetry/antiquity, **not** the prose
  fiction core that actually anchors Aidan's taste.
- **Not PD (the other ~40):** McCarthy, Chandler, Rand, Kerouac, Denis Johnson,
  Ellis, Fante, Didion, Thompson, Steinbeck (mixed), Faulkner (mixed), Woolf
  (mixed), Wallace, DFW, Vonnegut, Palahniuk, Vance, and most of the rest.

**Four options, not mutually exclusive:**

**A — PD-only scope.** Restrict to the ~15–17 safely-PD authors, extend the
existing pipeline outward from them (their real historical antecedents/
successors, also PD) exactly as-is. Rigorous, cheap, reuses Phase 1 almost
unchanged. Cost: leaves out the authors Aidan actually cares about.

**B — Fair-use / short-excerpt corpus for non-PD authors.** Build a much
smaller per-author feature set from legitimately obtainable short text:
publisher preview snippets (Google Books "search inside"), interview
transcripts, reviews/criticism that quote brief passages, properly-bounded
fair-use excerpts for research/criticism purposes. Sparse and noisy — good
enough for coarse stylometrics (sentence length, function-word rates,
punctuation), not for full TF-IDF-over-novel the way Phase 1 does it.

**C — Secondary-text proxy.** Study influence via what's *written about* these
authors instead of their prose directly — a citation network built from
literary criticism, Wikipedia "influenced / influenced by" infobox fields,
LitLab-style secondary sources. This is a legitimately different, still-real
research question (what do critics/scholars say vs. what does the text show)
— it just isn't the same claim as Phase 1's "signal is always real authorial
prose," and the writeup must say so plainly.

**D — Hybrid, tiered, and labeled (recommended).** PD-tier authors get the
full Phase 1 treatment (real prose, TF-IDF, k-NN). Non-PD-tier authors get
option B or C, clearly and permanently marked as a different evidence tier —
never silently merged into one undifferentiated "influence score." This is
the same instinct as Phase 1's "held-out validation, never fabricate signal"
discipline, applied to a new place it could go wrong: two tiers of evidence
quality must never be presented as one.

**Decide this before writing any pipeline code — it determines almost
everything downstream.**

---

## 4. Reframed research question

**Not this** (already asked, already null, do not re-ask): *"What is the
genre mutation rate?"*

**This instead:** *Does textual/stylistic influence between authors correlate
with chronological precedence, beyond what a shuffled-timeline null model
would produce — and can a real influence-network structure be recovered from
prose (plus clearly-labeled secondary evidence where prose is unavailable)?*

Concretely:
- **Node** = author, aggregated across their own corpus (not a single book —
  Phase 1's author-voice confound applies here even harder, since single-book
  "author fingerprints" are noisy).
- **Edge** = candidate influence A → B, directed, permitted only when A's
  earliest relevant publication predates B's — the real version of the
  forward/backward framing `influences.html` used playfully with Aidan's own
  read-order. Here it's actual literary chronology, not personal biography.
- **Signal** = two independent aggregate-text similarity scores per edge,
  never merged: *stylistic* (TF-IDF, Phase 1's tool — word choice, syntax,
  rhythm) and *conceptual* (semantic embeddings — ideas, imagery, themes).
  See §7.3 for why these must stay separate rather than becoming one
  "influence score."
- **Validation** = (a) a null model — shuffle each author's active-years,
  check whether "high similarity + correct time order" edges beat the
  shuffled baseline, same spirit as Phase 1's z = −0.27 result; (b) a
  held-out check against real, independently-documented influence claims
  (a curated "known influences" list — e.g. McCarthy's own stated debt to
  Faulkner and Melville is publicly documented) — used only to *check*
  emergent edges after the fact, exactly the role Gutenberg subject labels
  played in Phase 1. Never build edges from this list.

---

## 5. Method — extending the existing pipeline, not replacing it

- **Bibliography step** (new): reuse `build_canon.py`'s cross-referencing
  pattern (multiple sources + two independent model families + a support
  score) but retarget it — instead of "find the pre-1929 canon," build a
  real, dated bibliography *per seed author* (every notable work + real
  publication year). This is the backbone the directed time-graph depends on.
- **Corpus:** `build_corpus.py` / `gutenberg_ingest.py`, unchanged, scoped to
  the ~15–17 PD-safe seed authors plus their real PD-era antecedents/
  successors (§7.1 — PD-only scope; the non-PD tier from the original draft
  is out of scope for this phase, not built).
- **Vectors, dual and never merged:**
  - *stylistic* — `semantic_edges.py`'s existing TF-IDF approach, unchanged.
  - *conceptual* — new: sentence/passage-level semantic embeddings
    (aggregated per author), a genuinely new component, not a Phase 1 reuse.
- **Graph:** unlike Phase 1's undirected k-NN genre graph, this is a
  **directed** graph constrained by real publication chronology (§4). New
  code, not a reuse of `temporal_network.py` as-is.
- **Controls** (extend `controls.py`'s three-confound discipline with a
  fourth):
  1. Corpus density (per-book, not per-year) — same as Phase 1.
  2. Style drift (regress out the year trend) — same as Phase 1.
  3. Author voice (aggregate per author, one signal per author, not per book)
     — same idea as Phase 1, adapted since nodes are already authors here.
  4. **Form confound (new, replaces the draft's evidence-tier confound —
     moot under PD-only scope, §7.1):** form (poetry/prose/philosophy)
     correlates heavily with the stylistic signal by construction. Report
     same-form vs. cross-form edge rates separately for both signals
     (§7.3) rather than letting form differences read as influence
     differences.
- **Output:** `analyze.py`/`visualize.py`'s pattern (JSON results +
  interactive HTML), but the primary object is the directed influence graph
  itself, not a community-detection genre map.

---

## 6. Visualization — later phase, deliberately deferred

The `influences.html` trunk/root interaction (small graph, click a node to
traverse, shared roots merge into one node, right-side detail panel) is a
genuinely good reusable **interface** pattern for exploring the eventual real
network. But it should not be built before the data is validated — that
ordering (compelling UI first, curated-not-measured data under it) is exactly
what made the original page a personal artifact instead of research. Once
real, validated edges exist: likely home is a new page under `/research/` on
the personal site (a sibling to `literature-mutations.html`), or a
`visualize.py`-style standalone HTML output the same way `literary_genres.html`
works today.

Built 2026-07-23 — see §11 for what changed from the plan above and why.

---

## 7. Decisions (settled 2026-07-21, follow-up session)

1. **Corpus-access strategy: A — PD-only scope.** Build real-prose corpora
   only for the ~15–17 seed authors that are safely public domain (§3), then
   extend outward from them to their *actual* historical antecedents/
   successors (also PD, not necessarily in the original 57 — e.g. Melville's
   real antecedents, Nietzsche's real antecedents). The ~40 non-PD seed
   authors (McCarthy, Chandler, DFW, etc.) are **not** built into this phase's
   pipeline — they stay in §2's seed list as context/wishlist, explicitly out
   of scope, not silently dropped.
2. **Scope: keep all 57** seed authors in §2 as the record of what motivated
   this phase — the 1-quote long tail isn't trimmed from the list, it's just
   that most of it falls outside PD-only scope per decision 1. (This
   supersedes the either/or framing of the original open question — the
   seed list and the buildable set are no longer the same set, and that's
   fine as long as it's explicit.)
3. **Form-mixing: one graph, dual signal, form reported not split.**
   Discussion note (worth preserving — this is the real design turn from the
   original draft): "influence" was collapsing two different things.
   *Surface/stylistic echo* (word choice, syntax, rhythm — TF-IDF's actual
   measurement) is almost tautologically bound by form: a philosophy text's
   word frequencies resemble other philosophy far more than any poem,
   regardless of real influence. *Conceptual/thematic echo* (ideas, imagery,
   worldview surfacing later — semantic embeddings' actual measurement) is
   the cross-form case that actually matters (e.g. Nietzsche's ideas
   surfacing in later prose) and TF-IDF will never find it. Resolution:
   **compute both signals on every directed candidate edge, never merge them
   into one score.** A PD-safe example within this phase's actual scope:
   Nietzsche → later PD-era prose stylists he predates, checked for
   conceptual similarity (ideas/themes) independently of stylistic
   similarity (word/syntax patterns). Report both per edge:
   - high-stylistic + high-conceptual → strongest influence claim
   - high-conceptual + low-stylistic → idea-influence without prose imitation
   - high-stylistic + low-conceptual → shared form/genre convention, weaker
     influence claim
   - the correlation between the two signals *across the whole graph* is
     itself a reported result (same discipline as Phase 1's null-model
     check: are these secretly one signal, or genuinely orthogonal?)
   Form (poetry/prose/philosophy) is tracked per edge as a reported variable
   — same-form vs. cross-form edge rates are a *finding*, not something
   decided by splitting the graph in advance or regressed out as a nuisance
   confound (regressing out a variable this correlated with the stylistic
   signal would gut it).
4. **LLM usage boundary** — restated, unchanged from the original draft:
   *"No model ever writes the text we analyze. LLMs only enumerate citeable
   list membership and verifiable facts; the signal is always real authorial
   prose."* (README, verbatim.) LLMs may enumerate bibliographies and label
   results after real signal is found — never originate the influence claim
   itself from parametric/trained knowledge.
5. **Repo:** continue in `2016judea/literature-mutations` as Phase 2.

---

## 8. The one rule that must survive the handoff

> No model ever writes the text we analyze. LLMs only enumerate citeable list
> membership and verifiable facts; the signal is always real authorial prose.

That's Phase 1's README, unchanged, and it's the whole reason this is worth
doing properly instead of just adding more nodes to the `influences.html`
graph.

---

## 9. Result — the first real, validated finding (2026-07-22)

Built end-to-end same week as the design decision: `build_bibliography.py`
produced 2,411 cross-referenced works across 108 authors (17 PD-safe
anchors + 91 both-model-confirmed antecedents/successors); `build_corpus.py`
resolved 583 of those to real Gutenberg prose across 77 authors (Homer,
~780 BCE, through the 1920s); `build_influence_graph.py` built the directed,
dual-signal graph (2,915 candidate edges) exactly as designed in §5/§7.3.

**Held-out validation** (§4, `known_influences.json` — 130 of the 377
documented relationships resolvable among these 77 authors; a permutation
z-test against random same-chronology-direction pairs, never used to build
edges):

| signal | real mean | null mean | z |
|---|---|---|---|
| stylistic (TF-IDF) | 0.076 | 0.073 | **0.91** — not significant |
| conceptual (embedding) | 0.682 | 0.647 | **9.47** — highly significant |

**This is a real result, not a null one** — unlike Phase 1's genre-mutation
rate. Documented, independently-verified influence relationships (Pound on
Eliot, Coleridge and Byron on Shelley, Emerson on Thoreau, Hawthorne on
Melville, Wagner on Nietzsche) show no detectable elevation in word-choice/
syntax similarity, but a strong, statistically robust elevation in
conceptual/embedding similarity. The §7.3 design bet paid off directly: had
this project used only Phase 1's TF-IDF signal (the "just extend the
existing pipeline" path), the result would have come back null, masking a
real effect that only the embedding signal can see.

The effect is **not** an artifact of same-form pairs dragging the average
up — cross-form documented pairs (conceptual mean 0.676, n=70) score almost
identically to same-form pairs (0.688, n=60), including genuine cross-form
cases like Wagner (music/drama) → Nietzsche (philosophy).

**Honest scope/limits:**
- n=77 authors, 130 held-out pairs - a real but modest-scale result, not a
  sweeping claim about "literary influence" in general.
- The held-out list itself was LLM-enumerated (citeable critical consensus,
  §2/§7.4 discipline) - a second, independent scholarly source list would
  strengthen this further but wasn't required to see the effect.
- "Conceptual similarity" here means Gemini embedding cosine on a bounded
  author digest (≤6 works × 250 words) - a specific, reproducible
  operationalization, not a claim to have measured "ideas" directly.

**Not yet done (as of 2026-07-22):** the corpus-density control (§5 point 1,
direct Phase-1 analogue) wasn't ported over explicitly - author-level
aggregation already subsumes the author-voice control (point 3), and
style-drift detrending (point 2) and the form confound (point 4) are both
implemented in `build_influence_graph.py`. Visualization remains
deliberately deferred per §6 until/unless this result is extended further.

---

## 10. Two follow-ups closed out (2026-07-23)

Both addressed §9's honest limits directly rather than expanding scope.

**Independent validation source.** The originally proposed method - parsing
Wikipedia's `influences`/`influenced` infobox fields - was checked live
against all 77 authors before any pipeline code was written, and found
non-viable: only 2 of 77 (Arthur Conan Doyle, Jules Verne) have those fields
populated. Wikipedia deprecated them as unsourced/POV-prone years ago and
stripped them from most articles - the design doc's proposal in §3 was
written without knowing this, and the check disproved it before it cost any
build time. **Pivoted to Wikidata's P737 ("influenced by") property**
instead - a separate, still-actively-maintained structured store, unrelated
to the infobox display. Coverage: 44/77 authors, 350 raw claims, 110 unique
pairs resolving inside this graph (`fetch_wikidata_influences.py` →
`_data/wikidata_influences.json`). No LLM involved anywhere in this script -
stricter than `known_influences.json` on the project's own "signal is
real, never model-originated" rule (§8), since it isn't even LLM-enumerated.

Run through the same held-out permutation test (102 of the 110 pairs survive
the graph's resolvability + chronology filter):

| signal | real mean | null mean | z |
|---|---|---|---|
| stylistic (TF-IDF) | 0.082 | 0.073 | **2.454** — significant |
| conceptual (embedding) | 0.676 | 0.647 | **7.16** — highly significant |

The conceptual result replicates independently (z=7.16 vs the original
z=9.47) - a second, non-LLM source corroborates the headline finding. The
stylistic result does not replicate the original null: **it's significant
here (z=2.45) where it wasn't against known_influences.json (z=0.91)** -
an honest discrepancy, not resolved, worth investigating rather than
picking whichever number is more convenient. See below - it recurs.

**Corpus-density control.** Phase 1's actual mechanism (subset to one book
per author) doesn't map 1:1 onto Phase 2, whose nodes are already
per-author, not per-book. Adapted as two checks in `build_influence_graph.py`:
(a) run the exact `permutation_z` machinery on `n_books_used` itself instead
of similarity, asking whether documented-influence pairs are drawn from
systematically better-represented authors than the null sample; (b) a
stratified robustness re-run of the full held-out test, restricted to the
47 authors with `n_books_used >= 4` (of a max of 6).

- Book-count confound check: z=1.44 - not significant. Documented pairs
  aren't meaningfully denser than the null sample.
- Well-represented subset (47 authors, 46 known-influence pairs):
  conceptual z=6.25 (down from 9.47 on the full 130, but still highly
  significant) - **the headline result is not primarily a density
  artifact.** Stylistic z=2.97 in this subset - significant, same
  direction as the Wikidata discrepancy above.

**Open thread, not yet resolved:** stylistic similarity looks non-significant
on the full known_influences.json sample (z=0.91) but turns significant in
both independent checks that narrow the sample - the Wikidata pairs (z=2.45)
and the well-represented-authors subset (z=2.97). Two honest readings, not
adjudicated here: (a) the full-sample null is genuinely flat and both
narrower samples are small-N noise in the same lucky direction, or (b) the
full sample's non-significance was itself partly an artifact (of density,
or of the specific 130 LLM-enumerated pairs) that both independent narrower
checks happen to correct. Worth a dedicated pass before either claiming or
dismissing a stylistic effect.

---

## 11. Visualization built (2026-07-23)

`visualize_influence.py` → `influence_network.html`, following `visualize.py`'s
pattern of a self-contained generated HTML file. Reuses `influences.html`'s
interaction language (§6) — click a node, its edges light up, everything else
dims, a side panel opens with per-edge detail — but had to adapt it for scale
and honesty in ways the 6-quote original never needed to:

- **The graph is far too dense to render whole.** Mean out-degree is ~38 (an
  early author like Homer is chronologically eligible to connect to nearly
  all 76 others), so all 2,915 edges at once is an unreadable hairball —
  confirmed by an early screenshot pass during this build. Default view shows
  only the top ~7% of candidate edges by conceptual similarity (the signal
  that actually replicated) plus every independently-documented pair
  regardless of rank, with a slider to move the cutoff live.
- **Layout is chronological rank-order, not true-to-scale time.** Author
  years span -762 to 1919 with almost nothing between -37 and 1294 — a
  literal timeline would crush 300+ years of coverage into a sliver.
  Nodes are spaced by chronological *rank*, banded vertically by form
  (poetry/prose/drama/philosophy/other, itself a §7.3 reported variable),
  actual year shown on click.
- **Both signals travel to the UI, never merged** (the §7.3 discipline,
  extended to display): every edge in a node's panel shows conceptual and
  stylistic side by side, plus same-form/cross-form and year-gap, so the
  four-quadrant reading in §7.3 is directly inspectable per pair, not
  collapsed into one number.
- **Documented pairs are visually distinct, always shown, and cite their real
  source** — never merged with the measured candidate edges. Each
  `known_influences.json` entry's `notes` field turned out to be shared
  across every pair from the same source author (all of Shakespeare's
  documented influence pairs carry the same four notes), not written per-pair —
  isolating the one note that actually names the specific target author
  (matched on substring) was necessary to avoid misattributing e.g. the
  Melville note under the Whitman edge. 364 of 377 pairs (97%) resolve this
  way; the rest fall back to an unlabeled "documented" badge rather than a
  guessed quote.
- **A clicked node can end up hidden under its own detail panel** — the panel
  overlays the wide, horizontally-scrolling canvas rather than participating
  in layout, and a node positioned late in the chronology (e.g. Nietzsche,
  ranked 57 of 77) lands exactly where the panel opens. Fixed by scrolling
  the focused node into the safe (non-panel) region on selection. Caught by
  screenshotting the actual click interaction (via a temporary URL-param
  auto-click hook, headless Chrome) rather than trusting the JS logic by
  inspection — the same "verify against a live check, not the design on
  paper" discipline as §10's Wikipedia-infobox catch.
- **Honest framing travels with the page, not just the docs.** The header
  states both replicated z-scores and the unresolved stylistic discrepancy;
  a caveats block at the foot of the page restates "what's solid / what's
  open" in the same terms as §9-10, so the artifact can't be read as stronger
  evidence than the underlying analysis supports if it circulates without
  this doc attached.
