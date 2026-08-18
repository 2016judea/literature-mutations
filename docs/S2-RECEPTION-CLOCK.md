# S2 — The reception clock

Run 2026-08-18 against the brief in [`RESEARCH-PROGRAM.md`](RESEARCH-PROGRAM.md)
§ "S2 — The reception clock". S2 depends on nothing, so it ran without S0.

**Verdict, first: the two clocks agree on detective fiction.** Its name enters
English in **1889** (robust across thresholds: 1883 / 1889 / 1897 at 5 / 10 / 20 %
of peak), which lands inside the textual span of 1878–1926, and the name peaks in
**1932** — the golden age, where literary history puts it. The instrument is
externally licensed on the one positive result the project has.

**And the null holds from the reception side too.** Five of the eight communities'
names were already in use before the readable window opens, or take off early with
usage spread across the whole era. A perennial mode looks perennial in a source
that never touched the corpus. Per the brief, this was the most valuable outcome
available here — the absence is now corroborated rather than merely unrefuted.

Reproduce with:

```
python pull_ngrams.py              # _data/ngrams_raw.json (cached; no re-fetch)
python analyze_reception_clock.py  # reception_clock.json
python emit_reception_figure.py    # Figs. 6-7 + a standalone preview page
```

---

## What was NOT done

**No published number was recomputed, so the drift rule was not engaged.** The
textual columns below are read verbatim out of the checked-in
`controls_results.json`. S2 does not verify them — that is S0's job, and
`_data/books.json` is still absent from the checkout.

**The live site was not touched.** It is frozen for the duration.
`emit_reception_figure.py` writes a paste-ready fragment
(`reception_clock_figure.html`) plus a standalone preview page, and nothing under
`writing-topology/`.

**S2 repairs none of P1–P3.** It is a validator. The sampling frame is still
partly genre-selected, the corpus is still canon-filtered, and Louvain
event-counting is still unstable.

---

## The pairing decision, stated up front

Communities are paired to Ngrams terms **by their distinctive vocabulary, not by
their held-out label.** Three of eight labels name a genre their own cluster is
not:

| community's own top terms | held-out label | what it actually is |
|---|---|---|
| `cattle mountain wagon camp` | "Best Books Ever Listings" | Western / frontier |
| `catholics archbishop priest cardinal` | "Fantasy fiction" | religious / ecclesiastical |
| `castle sensations veil madame trembled` | "Science fiction" | **Gothic** |

This is not a new discovery — [`emit_paper_figures.py:70-74`](../emit_paper_figures.py#L70-L74)
already recorded it independently ("the one labelled 'Science fiction' is the
Gothic novel, and 'Best Books Ever Listings' is a popularity shelf, not a
genre"), and [`README.md:66`](../README.md#L66) calls that community gothic in
prose. The brief's own term list anticipated it too: it includes "sensation
novel" and "ghost story", which are not held-out labels.

**It is also the single largest effect S2 found.** Dating those three clusters by
their label instead of their vocabulary moves the answer by **+62 to +142 years**
and invents a twentieth-century emergence for modes named before 1800:

| cluster | dated from vocabulary | dated from its label | error |
|---|---|---|---|
| Gothic / sensation | ≤1800 | 1942 *(“science fiction”)* | **+142 y** |
| Religious fiction | ≤1800 | 1930 *(“fantasy fiction”)* | +129 y |
| Novel of manners | 1860 | 1922 *(“Bildungsroman”)* | +62 y |

That is exactly the fake late emergence the brief warns about, quantified. The
held-out labels validate *that* a cluster is recognised. They do not license
dating it. **This belongs in the paper as a methods caution** — Fig. 7 draws it.

---

## The table

Textual columns from `controls_results.json`; name columns from
`reception_clock.json`. Sorted by textual concentration, as Fig. 4 is.

| genre (from vocabulary) | n | books span | σ | z | name take-off | name IQR | name peak |
|---|--:|---|--:|--:|--:|--:|--:|
| **Detective fiction** | 13 | 1878–1926 | 14.9 | **−3.04** | **1889** | **23 y** | 1932 |
| Western fiction | 35 | 1726–1925 | 44.6 | −1.24 | 1886 | 21 y | 1938 |
| Religious fiction | 5 | 1820–1907 | 33.0 | −0.60 | ≤1800 | 50 y | 1859 |
| Historical romance | 13 | 1748–1921 | 47.4 | −0.30 | ≤1800 | 65 y | 1899 |
| Domestic fiction | 31 | 1678–1928 | 54.3 | +0.20 | 1822 | 50 y | 1866 |
| Gothic / sensation | 29 | 1764–1925 | 54.3 | +0.21 | ≤1800 | 59 y | 1867 |
| Nautical adventure | 10 | 1719–1919 | 55.8 | +0.43 | 1833 | 47 y | 1902 |
| Novel of manners | 30 | 1719–1923 | 63.3 | +1.45 | 1860 | 35 y | 1929 |
| *CONTROL — era-neutral* | — | — | — | — | ≤1800 | **67 y** | 1898 |

`≤1800` means **not datable**, not "took off in 1800": the name was already in use
when the readable window opens. Take-off is the first year the 9-year smoothed
curve crosses 10 % of its in-window peak and holds for 10 years. IQR is the
25th–75th-percentile width of usage mass, 1800–1950.

### The control is what makes the table readable

Era-neutral phrasing about fiction — "the novel", "a novel", "the story", "prose
fiction" — has **67 y** of naming spread, as wide as the widest genre here and
**2.9× wider** than detective's 23 y. Ngrams normalises by tokens per year but
corpus *composition* still drifts; if that drift alone produced narrow naming
mass, the control would be narrow too. It is the opposite. So the narrow rows are
signal, not an artifact of Google Books growing.

---

## Three findings the aggregate hides

**1. A real dated formation is buried inside "perennial" Gothic.** The aggregate
reads ≤1800 only because "Gothic romance" was already current. Per term:

| term | take-off | IQR | peak |
|---|--:|--:|--:|
| Gothic romance | ≤1800 | 103 y | 1931 |
| ghost story | 1810 | 54 y | 1872 |
| **sensation novel** | **1859** | **16 y** | **1867** |
| Gothic novel | 1914 | 15 y | 1950 |

`sensation novel` — take-off 1859, the narrowest mass of any term measured, peak
1867 — is the actual 1860s sensation boom (Collins's *Woman in White*, 1860;
Braddon's *Lady Audley's Secret*, 1862). And `Gothic novel` taking off in 1914 is
not a genre forming; it is the modern critical term being coined. **A lead for
[`subcluster_emergence.py`](../subcluster_emergence.py), not yet a result** — the
brief's own note stands that 166 novels will not support finer genre discovery.

**2. Western is the one genuine ambiguity.** Its name clock says datable
(take-off 1886, IQR 21 y, peak 1938 — the pulp era, correct), and the textual
instrument put it second-most concentrated at z = −1.24. But its community is
labelled "Best Books Ever Listings" — a popularity shelf — and spans 1726–1925.
So either the cluster is a mixed bag whose Western vocabulary is a subset, or
there is a real Western formation the textual instrument only half-caught. **This
is the strongest specific question S2 hands to S3/S4.**

**3. Two terms measure criticism, not period reception.** `comedy of manners`
(take-off 1871, peak 1929) and `Gothic novel` (1914) are retrospective critical
vocabulary. The brief's rule for S6 — period evidence only — applies here too, and
the Novel of manners row is the weakest in the table because of it.

---

## Limitations, so a reviewer does not have to find them

- **Take-off resolves to roughly ±10 years, not ±1.** The 10-year persistence run
  is sensitive to noise near the threshold: Western's aggregate takes off in 1886
  while every one of its individual terms takes off 1894–1899, because a second
  term's small contribution fills a dip that was breaking the run. Quote take-off
  as a decade.
- **First attestation is unusable and is not reported above.** It puts "detective
  story" at 1838, but the OED dates *detective* to about 1843. Isolated OCR hits
  clear the 5-nonzero-in-10 filter. Only the peak-relative take-off is robust.
- **Nothing named before 1800 can be dated here.** Gothic is the case: the
  readable window opens after the name is already current, so ≤1800 is an upper
  bound, not a measurement. Pre-1800 Ngrams sits on a corpus small enough that
  normalisation amplifies noise — "Gothic romance" *peaks* in 1776 there, which is
  why the brief excludes it.
- **"western story" may capture non-genre uses** ("a western story" meaning a
  story from the West). Not disambiguated.
- **The cross-clock correlations are underpowered and are not claimed.**
  r(year_min, take-off) = 0.18 and r(year_std, name IQR) = 0.39, both over n = 8;
  neither is significant. The defensible statement is the threshold one: the two
  textually-concentrated communities (z < −1) have the two narrowest name spreads
  (21 y, 23 y) and the six perennial ones are 35–65 y against a control of 67 y.
  Do not report an r for n = 8.

---

## Housekeeping — flagged, not fixed

The brief's noted README mismatch is now sharper rather than resolved.
[`README.md:11`](../README.md#L11) and `:65` say detective fiction is
"concentrated in ~1840s–1920s"; `controls_results.json` says **1878–1926**. S2 adds
that the *name* does not take off until 1889 either. Nothing measured supports
1840s as a corpus figure, on either clock — it reads as Poe-as-context. **Left
unchanged:** it is a published figure, and the standing drift rule is report and
stop, so Aidan calls it.
