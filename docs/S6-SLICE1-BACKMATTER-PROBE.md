# S6 slice 1 — can Gutenberg back matter carry the reception series?

Run 2026-08-18, after S0 finished. Brief:
[`RESEARCH-PROGRAM.md`](RESEARCH-PROGRAM.md) § S6, first slice — a go/no-go on
the cheapest source **before** committing weeks to the dataset.

---

## Go/no-go

**No-go on Gutenberg. The artifact is real and it is worth what the brief hoped —
but Gutenberg does not keep it. S6 needs Internet Archive page scans.**

**4 of 343 books** (1.2%) carry a genuine publisher advertisement, across
**42.2 million words** of full text. Three of those four are the real thing; one
of the five the detector flagged is a false positive. You cannot build a dated
reception series per genre on four data points.

The brief predicted exactly this — "Gutenberg transcribers routinely delete
publisher ads as not part of the work" — and it is now measured rather than
assumed.

**But the negative comes with a strong positive.** The handful that survived show
the artifact is precisely as valuable as S6 claims. In 1904 John Lane's
back-matter ad in *The Napoleon of Notting Hill* carries the heading **"THE NEW
MILITARY NOVEL"** — a publisher naming a genre, dated, in a recruitment
advertisement. That is the S6 measurement, in the wild, on the first look. The
problem is purely one of yield.

And the route out is signposted in the data itself: *The Enchanted Castle*'s
Gutenberg header reads *"reproduced from images generously made available by
**The Internet Archive**/American Libraries"* — the ad page survived precisely
because that transcription came from IA scans.

---

## What was run

`probe_backmatter.py` over **every** book in the reconstructed corpus — not a
sample — fetching the **full** text rather than the 20k-word slice
`build_corpus.py` keeps. 343 books, 42.2M words, 1678–1928, cached to disk so
the detector can be re-run and argued with without re-downloading.

The detector searches a **register, not a string**, in five families:

| family | examples |
|---|---|
| `same_author` | BY THE SAME AUTHOR, WORKS BY |
| `series_or_list` | UNIFORM WITH, NEW NOVELS, *X*'S LIST, THE … SERIES |
| `trade_format` | Crown 8vo, Demy 8vo, cloth gilt |
| `price` | 3s. 6d., 6s., price 2, net. |
| `trade_puffery` | PRESS OPINIONS, NOW READY, JUST PUBLISHED, Second Edition |

A book counts only on **corroboration** — two distinct families in the same
region. Any one of these phrases can appear innocently inside a novel, and most
do: `price` fires in 29 books, essentially all of it money in dialogue.

Only Gutenberg's own `*** START ***`/`*** END ***` body is searched, so the
licence boilerplate cannot be mistaken for period evidence. **Period evidence
only**, per the S6 rule — every marker is language the publisher itself set.

### The result

| | books |
|---|---:|
| fetched and scanned | **343** |
| any single marker anywhere | 38 |
| two families anywhere (corroborated) | 5 |
| — of which genuine advertisements | **4** |
| — of which false positives | 1 (*Ulysses*) |
| `series_or_list` — the diagnostic family | **1** |
| `trade_format` (Crown 8vo etc.) | 4 |

By period: 0 of 107 pre-1850, 1 of 61 in 1850–1889, 3 of 175 in 1890–1928.

### The detector is not broken — two controls

A zero from an instrument never shown to produce a signal is worthless, which is
the trap S0 hit three times. So:

1. **Positive control.** A synthetic late-Victorian ad page (Smith, Elder & Co.'s
   list, Crown 8vo, 6s., PRESS OPINIONS) fires **all five families**. The regexes
   work.
2. **Live-fire control.** The scanner reaches real text and fires on it — 87
   `price` hits across 29 books, 10 `trade_puffery` hits. It is reading the
   books; the ad vocabulary simply is not in them.

`Crown 8vo` — the single most characteristic phrase on a British publisher's ad
page — appears in **4 of 343** full novels.

---

## The four survivors, verbatim

**1. *Little Women*, Alcott, 1868 — back matter at 98% of the file.** The best
example, and exactly the "dated marketing act" S6 is after: a publisher
constituting a series and recruiting into it.

> Louisa M. Alcott's Writings — **THE LITTLE WOMEN SERIES.** =Little Women=; or
> Meg, Jo, Beth, and Amy. Illustrated. 16mo. $1.50. =Little Men.= … The above
> eight volumes, uniformly bound in cloth, gilt, in box, $12.00. … 8 vols.
> Crown 8vo. Decorated cloth, gilt, in box. $16.00. … **THE SPINNING-WHEEL
> SERIES**

**2. *The Napoleon of Notting Hill*, Chesterton, 1904 — back matter at 99.6%.**
A publisher naming a **genre** as an ad heading. This is the S6 measurement.

> *Mr. Lane's New Fiction* — **THE NEW MILITARY NOVEL.** LIFE IN A GARRISON TOWN.
> … By LIEUTENANT BILSE. The Military Novel suppressed by the German Government.
> Second Edition. Crown 8vo. 6s. MY FRIEND PROSPERO: A Novel. By HENRY HARLAND.
> Crown 8vo. 6s. *By the same Author*. THE CARDINAL'S SNUFF-BOX. … 3s. 6d. net.

**3. *The Enchanted Castle*, Nesbit, 1907 — front matter.** Segmented by
audience rather than genre, but a real dated trade list — and transcribed *from
Internet Archive scans*, which is the whole point.

> BY THE SAME AUTHOR — **FOR CHILDREN** *Illustrated, crown 8vo, cloth gilt, 6s.*
> The Treasure Seekers / The Would-be-Goods / … **FOR GROWN-UPS** *Crown 8vo,
> cloth, 6s.* Man and Maid — LONDON: T. FISHER UNWIN

**4. *The Man in the Brown Suit*, Christie, 1924** (and *Those Barren Leaves*,
Huxley, 1925, which fires one family only). Both are **author bibliographies**,
not genre lists — they name the author's other titles and nothing else:

> THE MAN IN THE BROWN SUIT — BY THE SAME AUTHOR — THE MYSTERIOUS AFFAIR AT
> STYLES / THE SECRET ADVERSARY / THE MURDER ON THE LINKS — … DODD, MEAD AND
> COMPANY 1924

Useful for authorship chronology, useless for genre. Worth separating in any
future pass: *"by the same author"* lists and *genre series* ads are different
artifacts, and only the second measures genre formation.

**False positive:** *Ulysses* trips `trade_format` + `price` on narrative prose
about books and money ("Hozier's *History of the Russo-Turkish War*"). Reported
rather than quietly dropped, because a 1-in-5 false-positive rate at this yield
is itself a reason not to build on the source.

---

## What this means for S6

**Internet Archive is required, and the probe says why it will work.** The one
Gutenberg text that kept a full trade list got it from IA scans. IA holds page
images of the physical book including bound-in ads; Gutenberg holds a
transcription of *the work*, and its transcribers strip the rest by editorial
policy. The material is not lost — it is one layer down, in the scans.

**Cost, stated honestly.** This is the more expensive pipeline the brief warned
about: page images rather than plain text, so OCR (or IA's existing OCR layer)
plus page-region detection, plus edition-level metadata to date each ad to a
printing rather than to the novel's first publication. It is not a week.

**Three things to carry into that work, from this probe.**

1. **The register works.** All five families fire cleanly on a real ad page and
   the false-positive mode is understood. The same marker set can be pointed at
   OCR text with minor tuning.
2. **Ads sit at the extremes of the volume** — 98%+ for back matter, <1% for
   front. Page-position priors will cut OCR cost sharply.
3. **Separate the two artifacts up front.** "By the same author" is an author
   list; "Mr. Lane's New Fiction / THE NEW MILITARY NOVEL" is a genre act. Only
   the second is S6 evidence, and conflating them would inflate the series with
   data that cannot speak to genre.

**A cheaper intermediate worth pricing before committing to OCR:** publishers'
trade circulars and *The Publishers' Circular* / *The English Catalogue of Books*
were themselves printed serials, many already transcribed, and they carry the
same series-and-genre headings in bulk rather than one novel at a time. The brief
lists circulating-library catalogues and periodical reviews as the next rungs;
this probe suggests the trade catalogue may be a better first target than the
bound-in ad page, because it concentrates the same evidence.

**Not started:** the reception series itself, per the brief.

---

## Artifacts

- `probe_backmatter.py` — the probe, with both controls.
- `backmatter_probe_full.json` — all 343 books: per-family counts, positions as a
  fraction of the file, and verbatim samples. Committed so the next session
  re-reads rather than re-fetches 42M words.
- Full texts cached at `/tmp/gutenberg_full` (not committed — ~250MB, and
  re-fetchable from the ids in the manifest).
