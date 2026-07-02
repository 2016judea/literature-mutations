# Literature Mutations

**Can the genre system of English fiction be recovered from prose alone — and can we measure the *rate* at which genres form?**

This began in 2021 as a course proposal at Columbia (the original proposal is preserved in [`docs/PROPOSAL.md`](docs/PROPOSAL.md)). It has since been rebuilt into a working pipeline with real results — one positive, one negative, both reported honestly below.

---

## TL;DR

- **Yes to the first question.** An unsupervised network built from raw opening prose recovers the recognizable genre system of English fiction — detective, science fiction, nautical adventure, historical romance, the early English novel, American realism — and each emergent cluster is **confirmed by held-out genre labels the model never sees.**
- **Mostly no to the second.** There is **no global mutation *rate*** — the apparent acceleration is a corpus-density artifact, and the event count is indistinguishable from shuffled publication dates (null model, z = −0.27). *But* after controlling for three confounds (density, style drift, author voice), **detective fiction stands out as one genuine, datable genre emergence** (~1840s–1920s, z ≈ −3.0). Genre birth is real but rare and genre-specific, not a smooth rate.

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

Genres were recovered from the words alone, and independent labels confirm them. See [`visualize.py`](visualize.py) → `literary_genres.html` for the interactive network.

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

- **Detective fiction is the one genuine, datable emergence** — z ≈ −3.0, concentrated in ~1840s–1920s, matched to the held-out "Detective and mystery stories" label, robust across k = 4–6 and all seeds. This fits literary history exactly: detective fiction is the paradigm genre with a real birth (Poe → Collins → Doyle → the golden age).
- **Everything else is a perennial *mode*** — gothic, adventure, domestic, historical fiction are spread across all 250 years (z ≈ 0), not "born" at a point.

Conclusion: genre birth is **real but rare and genre-specific**, not a smooth global rate. The measurable findings are unsupervised genre **recovery** and the emergence of **detective fiction** specifically — not a universal mutation rate.

## Reproducing

```bash
pip install networkx scikit-learn numpy plotly
export GEMINI_API_KEY=...  ANTHROPIC_API_KEY=...   # for corpus assembly only

python build_canon.py        # -> _data/canon.json   (cross-referenced canon)
python build_corpus.py       # -> _data/books.json   (real Gutenberg full text)
python analyze.py            # -> results.json        (communities, naming, null model, sweep)
python visualize.py          # -> literary_genres.html
EDGE_METHOD=semantic python temporal_network.py   # the year-by-year timeline
```

## Limitations & honest next steps

- **Pre-1929 ceiling.** Public-domain full text stops at ~1928, so this is the genre story *up to modernism* — cyberpunk, modern fantasy, and postmodernism are out of reach without a licensed-text or excerpt source.
- **The rate question isn't dead, the *instrument* is.** A per-book, null-model-controlled statistic might still find real structure; the raw event count does not. That is the honest open problem.
- **Reception vs text.** Genre also lives in how readers/critics classify books over time; a period-reception dataset (not modern retrospective reviews, which back-project today's categories) could measure formation directly — the hardest but most direct future dataset.

## References

See [`docs/PROPOSAL.md`](docs/PROPOSAL.md) for the original 2021 proposal and its full reference list (Stanford Literary Lab's *Quantitative Formalism*, Moretti, Hope & Witmore's Docuscope work, Galton's *Vox Populi*, and the clustering literature).
