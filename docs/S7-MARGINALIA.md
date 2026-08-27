# S7 — marginalia as a third evidence class

Scoped and run 2026-08-27. **Aidan un-parked Phase 2 in the same instruction**
("port this into literature mutations. And continue our research with it"),
which supersedes the standing decision in
[`RESEARCH-PROGRAM.md`](RESEARCH-PROGRAM.md) that Phase 2 was out of scope. It
also supersedes the site freeze — he authorised publication explicitly.

The corpus is a submodule: [`vendor/marginalia`](../vendor/marginalia) →
[`github.com/2016judea/marginalia-corpus`](https://github.com/2016judea/marginalia-corpus).
8 sources, 555 readers, 216,553 marks, 36,420 of them in an author's own hand,
2,139 source authors, four centuries.

---

## Why it is a different class from what Phase 2 already has

`build_influence_graph.py` validates against two held-out sources, and both
answer *who does the record say influenced whom*:

| | n | pairs in graph |
|---|---:|---:|
| `known_influences.json` — LLM-enumerated | 377 | 130 |
| `wikidata_influences.json` — Wikidata P737 | 350 | 102 |

The marginalia corpus answers *who demonstrably read whom*, from marks in
surviving copies. It is the only one of the three that carries a **passage**, a
**weight**, and a **hand**.

---

## Finding 1 — marked passages recover borrowing, not influence

[`analyze_marginalia_prose.py`](../analyze_marginalia_prose.py) →
`_data/marginalia_prose.json`

> Do the passages a reader marked resemble that reader's own prose more than
> unmarked passages of the same book?

Melville is the only reader with both a large body of transcribed marks and a
large body of his own public-domain prose. Marked passages are **fuzzy-located
inside the comparison edition** and the marked span taken in *that* edition's
orthography, so both sides of the test share one text — otherwise the gap would
partly measure edition rather than attention. Null: 2,000 random spans per book,
matched to the located spans' length distribution.

| source author | marks | located | rate | z | p | late-shift z | late-shift p |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Thomas Beale** — *the control* | 169 | 158 | 0.94 | **+1.69** | **0.042** | **+2.85** | **0.0015** |
| Ralph Waldo Emerson | 76 | 53 | 0.70 | +0.05 | 0.44 | +1.29 | 0.064 |
| William Hazlitt | 285 | 145 | 0.51 | −0.59 | 0.72 | −1.85 | 0.98 |
| Matthew Arnold | 171 | 131 | 0.77 | −0.78 | 0.81 | −0.72 | 0.78 |
| John Milton | 480 | 394 | 0.82 | −1.08 | 0.99 | +0.04 | 0.31 |
| Nathaniel Hawthorne | 320 | 183 | 0.57 | −1.39 | 0.93 | +1.54 | 0.037 |
| William Shakespeare | 704 | 615 | 0.87 | **−1.88** | 0.99 | +1.15 | 0.12 |

**The control fires and nothing else does.** Beale's *Natural History of the
Sperm Whale* is the book Melville uncontestedly lifted into Moby-Dick's cetology
chapters, and it is the only positive. Its directional result is the stronger
one: the passages he marked are **significantly more like Moby-Dick and after
than like Typee, Omoo and Redburn**, relative to random spans of the same book
(z = +2.85, p = 0.0015). The borrowing is visible in the arithmetic.

Shakespeare runs the other way — the lines Melville marked are **less** like his
own prose than random lines of the same book are. Milton and Hawthorne trend the
same way.

So the honest reading: **marked-passage lexical similarity measures source-text
appropriation, not influence.** Melville's Shakespeare debt is structural —
soliloquy, tragic form, Ahab's rhetoric — and a bag-of-words method cannot see
it. Reporting this as a failure of the corpus would be wrong; it is a finding
about what the *instrument* can reach, in the same spirit as Phase 1's
"there is no global mutation rate".

Untestable and why: **Schopenhauer** located 30 of 200 passages (0.15) — the
Gutenberg edition is not the volume he marked, so the located spans are a biased
sample of it. **Marlowe** matched well (0.71) but yields only 27 spans — the
edition is right, there is simply not enough marked text.

---

## Finding 2 — reading does predict stylistic similarity, within-reader

[`validate_graph_against_marginalia.py`](../validate_graph_against_marginalia.py)
→ `_data/marginalia_validation.json`

### The confound that invalidated the first version

Run against a graph-wide null, the marginalia edges looked excellent — reference
edges z = 4.60, beating both existing sources. Then the pairs were printed:
**all 21 reference pairs are Nietzsche→X and all 6 heavy-mark pairs are
Melville→X.** The entire result was one author's position in the graph. That is
Phase 1's author-voice confound with a single endpoint rather than a prolific
one, and a graph-wide null is blind to it. The reference pairs also averaged
4.95 books/author against 4.2 graph-wide — the density confound Phase 2 already
controls for.

### The valid test

Hold the reader fixed. Are the authors a reader **demonstrably read** more
similar to him than the authors in the same graph he **did not**? Every pair on
both sides then shares one endpoint, so the reader's global position, register
and density all cancel. 2,000 draws.

| reader · evidence | read | not read | stylistic z | p | conceptual z | p |
|---|---:|---:|---:|---:|---:|---:|
| **Nietzsche · named in his own prose** | 21 | 53 | **+4.24** | **0.0005** | **+2.84** | **0.002** |
| **James Joyce · marked** | 6 | 70 | **+3.18** | **0.0015** | **+2.42** | **0.0045** |
| **Herman Melville · marked** | 6 | 69 | **+2.36** | **0.019** | +1.14 | 0.13 |
| Walt Whitman · marked | 12 | 64 | −0.36 | 0.63 | +0.06 | 0.48 |

**Three of four readers, at n as small as 6.** The authors these writers
physically read sit measurably closer to them in the similarity graph than the
authors they did not — and this survives the control that killed the naive
version.

Whitman is the null, and his tier explains it: most of his edges come from the
Bibliographical Handlist, which is *attested reading with no surviving mark* —
T3, the weakest tier in the corpus. The one reader whose evidence is thinnest per
edge is the one reader who fails. That is the tier ladder doing its job rather
than a result to explain away.

---

## The two findings together

Reading shows up in an author's **overall** style — three of four readers, and
Nietzsche's own naming of sources is the single strongest signal measured here,
stronger than either attribution source. But **the specific lines a reader marked
are not the lexical route by which it happens**, except where the reader is
plainly lifting material, as Melville is from Beale.

That is a coherent claim and a falsifiable one: influence is diffuse at the
corpus level and invisible at the passage level to a lexical instrument.

## What binds, and what to do about it

**The graph's 77 authors, not the corpus's 2,139.** Only 24 mark edges and 21
reference edges have both ends in the graph, and only four readers overlap at
all. Every number above rests on n between 6 and 21. The corpus is not the
limiting side.

So the next step is not more marginalia. It is **widening the Phase 2 author
set** toward the corpus's 2,139 source authors — which is the deferred S4/S5
work (NovelTM, HathiTrust EF) with a concrete new reason to run it, and a
concrete target list. Until then these are strong hints on small n, and should be
described that way.

Reproduce:

```bash
git submodule update --init vendor/marginalia
python analyze_marginalia_prose.py
python validate_graph_against_marginalia.py
```

Both are seeded (`SEED = 20260827`) and cache their fetches under
`data/cache/s7/`.
