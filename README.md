# Literature Mutations

**Can the genre system of English fiction be recovered from prose alone — and can we measure the *rate* at which genres form?**

This began in 2021 as a course proposal at Columbia (the original proposal is preserved in [`docs/PROPOSAL.md`](docs/PROPOSAL.md)). It has since been rebuilt into a working pipeline with real results — one positive, one negative, both reported honestly below.

---

## TL;DR

- **Yes to the first question.** An unsupervised network built from raw opening prose recovers the recognizable genre system of English fiction — detective, science fiction, nautical adventure, historical romance, the early English novel, American realism — and each emergent cluster is **confirmed by held-out genre labels the model never sees.**
- **Mostly no to the second.** There is **no global mutation *rate*** — the apparent acceleration is a corpus-density artifact, and the event count is indistinguishable from shuffled publication dates (null model, z = −0.27). *But* after controlling for three confounds (density, style drift, author voice), **detective fiction stands out as one genuine, datable genre emergence** (books of 1878–1926, z ≈ −3.0). Genre birth is real but rare and genre-specific, not a smooth rate.

---

## Corpus: canon-first, cross-referenced

Earlier drafts scraped whatever was available (Goodreads shelves; then bulk Project Gutenberg). Both are biased and unrepresentative. Instead the corpus is now defined **top-down** and **cross-referenced**:

1. **[`build_canon.py`](build_canon.py)** assembles the pre-1929 public-domain English-novel canon by querying many sources — named critic lists (Guardian 100, Modern Library), reference lists (1001 Books), era/genre buckets, and a crowd source (4chan /lit/) — each confirmed by **two independent model families** (Gemini, grounded in Google Search; and Claude). Every title gets a *support score*: how many lists and how many models back it. → **440 titles**, 159 cross-model confirmed.
2. **[`build_corpus.py`](build_corpus.py)** then goes and *finds* each title on Project Gutenberg (a title+author match is a third, independent existence check), pulling ~20k words of **real full text**. → **345 titles matched**, spanning 1660–1928.

No model ever writes the text we analyze. LLMs only enumerate citeable list membership and verifiable facts; the signal is always real authorial prose.

## Method

- **Text → vectors** ([`semantic_edges.py`](semantic_edges.py)): TF-IDF over each novel's prose, dropping vocabulary common to >40% of books (shared "novel-ese") so edges reflect *distinctive* genre vocabulary.
- **Vectors → graph** ([`temporal_network.py`](temporal_network.py)): each book links to its *k* nearest neighbors. (A global similarity threshold fails — over long English prose every novel is somewhat similar to every other, giving one blob; k-NN recovers structure robustly.)
- **Graph → genres**: Louvain community detection. The corpus is also grown year-by-year to produce cumulative snapshots for the temporal analysis.
- **Validation**: Gutenberg subject labels are held out and never used to build edges — they only *check* whether emergent clusters correspond to recognized genres.

## Result 1 — genres emerge from prose (robust)

Eight communities emerge, each named by an LLM from its member titles + distinctive vocabulary, and each matched against the held-out labels:

| Emergent genre | Distinctive vocabulary | Held-out label agrees | Exemplars |
|---|---|---|---|
| Detective fiction | detective inspector police murder holmes poirot | **Detective and mystery stories** | Sign of the Four, Leavenworth Case |
| Science fiction | scientific science machine | **Science fiction** | Clockwork Man, Tono-Bungay |
| Nautical adventure | deck cabin mate aboard shore | Adventure | Call of the Wild, Almayer's Folly |
| Historical romance | thy thou sword knight soldier | **Historical fiction** | Quo Vadis, She |
| Early English novel | madam parson behaviour discourse | England — Fiction | Robinson Crusoe, Tom Jones |
| American realism | car dollars chicago hotel york | Psychological fiction | The Great Gatsby, Age of Innocence |

Genres were recovered from the words alone, and independent labels confirm them. See [`visualize_genres.py`](visualize_genres.py) → `genre_network.html` for the interactive network (click any novel or genre to trace its cluster) — [live on the site](https://aidanjude.vercel.app/research/literature-mutations.html), alongside Phase 2's influence network, under the "Explore the genres" tab. (`visualize.py` → `literary_genres.html` still produces the original static two-panel Plotly export.)

## Result 2 — there is no global mutation *rate*, but one genre genuinely emerges

The original thesis wanted a genre-*mutation rate* over time. There is no such global rate — the apparent signal is a stack of confounds, each of which we found (and were fooled by) in turn ([`controls.py`](controls.py)):

| Test | Apparent signal | Verdict |
|---|---|---|
| Per-*year* mutation rate | "accelerates, inflection ~1890" | ❌ **corpus-density** artifact (later eras have more books) |
| Per-*book* rate + null model | — | ❌ no global signal: real chronology (90 events) ≈ shuffled years (94 ± 15, **z = −0.27**) |
| Style-drift control | "science fiction emerges, z = −4.9" | ❌ **prolific-author** artifact (the cluster was H.G. Wells's voice; not robust across k) |
| **+ author control (one book/author) + k/seed sweep** | **detective fiction, z ≈ −3.0** | ✅ **robust, label-validated** |

Three structural confounds, each controlled:
1. **Corpus density** — measure per *book*, not per year.
2. **Style drift** — English prose drifts over time (corr(similarity, year-gap) = −0.32), making *any* text graph temporally structured. Regress the year trend out of the vectors (→ corr ≈ 0).
3. **Author voice** — ~20–26% of raw k-NN edges are same-author; prolific authors (Wells, Conrad, Doyle: 8–10 books each) form clusters that masquerade as concentrated genres. Use one book per author.

After all three, each emergent community is tested for temporal **concentration** vs a null (random same-size draws). The result:

- **Detective fiction is the one genuine, datable emergence** — z ≈ −3.0, concentrated in the **books of 1878–1926**, matched to the held-out "Detective and mystery stories" label, robust across k = 4–6 and all seeds. This fits literary history exactly: detective fiction is the paradigm genre with a real birth (Poe → Collins → Doyle → the golden age). *(An earlier revision of this README said "~1840s–1920s", which read as a corpus figure and was wrong by ~35 years: `controls_results.json` says 1878–1926. Poe and Collins are literary-historical context, not books in the corpus.)*
- **Everything else is a perennial *mode*** — gothic, adventure, domestic, historical fiction are spread across all 250 years (z ≈ 0), not "born" at a point.

Conclusion: genre birth is **real but rare and genre-specific**, not a smooth global rate. The measurable findings are unsupervised genre **recovery** and the emergence of **detective fiction** specifically — not a universal mutation rate.

## Reproducing

```bash
pip install networkx scikit-learn numpy plotly
export GEMINI_API_KEY=...  ANTHROPIC_API_KEY=...   # for corpus assembly only

python build_canon.py        # -> _data/canon.json   (cross-referenced canon)
python build_corpus.py       # -> _data/books.json   (real Gutenberg full text)
python analyze.py            # -> results.json        (communities, naming, null model, sweep)
python visualize.py           # -> literary_genres.html (static two-panel Plotly export)
python visualize_genres.py   # -> genre_network.html (click-to-explore version, needs literary_genres.html + controls_results.json)
EDGE_METHOD=semantic python temporal_network.py   # the year-by-year timeline
```

## Limitations & honest next steps

- **Pre-1929 ceiling.** Public-domain full text stops at ~1928, so this is the genre story *up to modernism* — cyberpunk, modern fantasy, and postmodernism are out of reach without a licensed-text or excerpt source.
- **The rate question isn't dead, the *instrument* is.** A per-book, null-model-controlled statistic might still find real structure; the raw event count does not. That is the honest open problem.
- **~~Reception vs text.~~ Built — see Phase 3 below.** Genre also lives in how readers/critics classify books over time, and a period-reception dataset measures formation directly. This was listed here as the hardest and most direct future dataset; it now exists for the American trade, 1855–1929.

## Phase 2 — Author Influence Network

A second, separate result: does textual similarity between specific authors
track real, documented influence, beyond chronology alone? Built on the same
discipline (measured signal only, held out against real influence claims,
never fabricated) but a different graph — directed, author-to-author,
chronologically-forward-only candidate edges, two independent similarity
signals (stylistic TF-IDF + conceptual embedding) kept separate rather than
merged into one score.

**[`build_bibliography.py`](build_bibliography.py)** cross-references 2,411
works across 108 authors (each confirmed by two independent model families);
**[`build_corpus.py`](build_corpus.py)** resolves 583 of those to real
Gutenberg prose across 77 authors, Homer through the 1920s;
**[`build_influence_graph.py`](build_influence_graph.py)** builds 2,915
directed candidate edges, each carrying both scores.

Held out against **two independent validation sources** — neither used to
build a single edge:

| validation source | stylistic z | conceptual z |
|---|---|---|
| `known_influences.json` — 130 pairs, LLM-enumerated critical consensus | 0.91 (not significant) | **9.47** (highly significant) |
| Wikidata P737 "influenced by" — 102 pairs, no LLM involved | **2.45** (significant) | **7.16** (replicates) |
| well-represented subset (n=47 authors, density control) | **2.97** (significant) | **6.25** (replicates) |

**Conceptual similarity is a real, replicated result** — not a density
artifact (the well-represented subset still holds), not a same-form artifact
(cross-form documented pairs like Wagner → Nietzsche score the same as
same-form pairs). **Stylistic similarity is a genuinely open question,
deliberately left unresolved**: null on the full 130-pair sample but
significant in both narrower independent checks. Two honest readings, not
adjudicated — either the full-sample null is real and both narrower checks
are small-N noise landing the same lucky direction, or the full-sample null
was itself partly an artifact that both narrower checks correct. Worth a
dedicated pass before claiming or dismissing it either way.

Full design, results, and honest limits in
[`docs/PHASE2_INFLUENCE_NETWORK.md`](docs/PHASE2_INFLUENCE_NETWORK.md).

**Visualization:** [`visualize_influence.py`](visualize_influence.py) →
`influence_network.html` — an interactive, chronologically-laid-out, directed
graph. Click any author and their edges light up; a side panel shows both
similarity scores per connection, plus the real citation note where a
connection is independently documented (Wikidata or the held-out list), not
just measured. Hosted live at
[aidanjude.vercel.app/research/literature-mutations.html](https://aidanjude.vercel.app/research/literature-mutations.html).

## Phase 3 — the period reception series

A third result, and the one nobody else has built. Underwood defines genre
membership with **modern retrospective labels** and names that as a limitation.
Genre also lives in how the trade classified books *at the time* — so this
measures that directly, from the American book trade's own dated pages.

**Source.** Two serials on Internet Archive, free OCR, no lending restriction,
**no OCR cost**: *American Publishers' Circular and Literary Gazette* (1852–1871)
spliced ahead of *Publishers' Weekly* (1872–1929). **3,487 dated issues, 128.5M
words, 0 fetch failures.** Two probes got here — Gutenberg back matter was a
no-go (4 publisher ads in 343 books), and the two trade catalogues the obvious
next guess named both failed on measurement.

**The artifact is Publishers' Weekly's Weekly Record annotation** — one dated
descriptive line per American book published. PW states the policy in its own
section masthead, which is what licenses this as *classification* rather than
review opinion:

> "The annotations are **descriptive, not critical; intended to place not to
> judge** the books."

### The finding

> **"Mystery story" appears zero times in 41.8 million words of the American
> book trade across 1,690 issues, 1855–1895 — then 1,605 times in the following
> 34 years.**

First occurrence 1896, sustained from 1896, take-off **1906–1909**, plateau near
40 per million to 1929. It is not one repeated house ad (169 hits across 45 of 56
issues in 1920) and not authors' titles — the hits sit in the trade's own
descriptive line: *"A mystery story for girls"* is a shelf label, not a review.

**A second datable genre, found by the reception side alone.** And detective
fiction now agrees on **three** independent clocks: the books (1878–1926), the
general language (Ngrams take-off 1889), and the trade (sustained 1873, take-off
1891–1897, still rising at 1929).

### One honest correction to our own method

A fraction-of-peak take-off computed on a **smoothed sparse** series can precede
the term's first actual occurrence — a 9-year moving average spreads a first
spike backwards. It did: `sensation novel` first appears in 1863 and the
estimator reported a take-off of **1859**, which happens to match Phase 2's
Ngrams date exactly. That would have been a false replication. Across smoothing
widths 9/5/3/1, `sea story`'s take-off moves **74 years**. Take-offs therefore
ship as **bands**, and a band spanning more than 10 years is reported as *not
measurable*. Five of eleven terms survive the rule.

**Limits.** It is the **American** trade, so any regression against the textual
series is a US-side measurement; IA's British holding is 24 items. The annotation
series only exists from **1878** — the Circular never annotated — which is why
the parser-free per-million series is the primary one. 1929 is a hard ceiling on
both sides.

Full method, all eleven terms and every caveat:
[`docs/S6-SLICE3-RECEPTION-SERIES.md`](docs/S6-SLICE3-RECEPTION-SERIES.md), with
the two probes that found the source in
[`docs/S6-SLICE1-BACKMATTER-PROBE.md`](docs/S6-SLICE1-BACKMATTER-PROBE.md) and
[`docs/S6-SLICE2-TRADE-CATALOGUE.md`](docs/S6-SLICE2-TRADE-CATALOGUE.md).
The dated per-book table is `_data/reception_entries.jsonl.gz` — 1,517
genre-bearing trade annotations, 1878–1929.

```bash
python build_reception_series.py     # -> reception_series.json  (69 min, once)
python analyze_reception_series.py   # -> reception_clock_trade.json  (seconds)
python emit_trade_figure.py          # -> trade_series_figure.html (Figs. 8-9)
```

**Published 2026-09-04**, with the S2 name clock alongside it, as §10 and §11 of
[the paper on the site](https://aidanjude.vercel.app/research/literature-mutations#reception).
Both sections' figures are pasted verbatim from the emitters
([`emit_reception_figure.py`](emit_reception_figure.py),
[`emit_trade_figure.py`](emit_trade_figure.py)) so no number on the page is
hand-typed. That lifts the site freeze in
[`docs/RESEARCH-PROGRAM.md`](docs/RESEARCH-PROGRAM.md) for this work only, on
Aidan's instruction, exactly as 2026-08-27 lifted it for S7.

## References

See [`docs/PROPOSAL.md`](docs/PROPOSAL.md) for the original 2021 proposal and its full reference list (Stanford Literary Lab's *Quantitative Formalism*, Moretti, Hope & Witmore's Docuscope work, Galton's *Vox Populi*, and the clustering literature).
