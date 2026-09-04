Continuing work on `literature-mutations`. **Read
[`docs/RESEARCH-PROGRAM.md`](RESEARCH-PROGRAM.md) in full before touching
anything** — "Standing decisions" and "The reception side is now the strong
side" are your brief. Don't re-litigate the scoping; it was done 2026-08-15
against the real artifacts, and the four standing decisions were settled with
Aidan 2026-08-16.

*Prompt rewritten 2026-09-04, at the end of the session that published Phase 3.
The version before this one still briefed a fresh session to run S6 slice 3 and
S1 — both long done — and told it not to touch the live site, which by then had
been updated twice. A stale brief is worse than none: it spends a session
re-deriving what the repo already knows.*

---

## Everything below is DONE. Do not redo any of it.

| session | verdict | doc |
|---|---|---|
| **S0** — reconstruct the corpus | corpus back on disk; detective reproduces at z = −3.04; Louvain event counts do **not** reproduce and cannot (seed noise ±7.6) | [`S0-CORPUS-RECONSTRUCTION.md`](S0-CORPUS-RECONSTRUCTION.md) |
| **S1** — the provenance audit | **P1 cannot explain the finding**: sampling-independent up to 4 of its 13 books removed adversarially | [`S1-PROVENANCE-BOUND.md`](S1-PROVENANCE-BOUND.md) |
| **S2** — the reception clock (Ngrams) | two clocks agree on detective fiction (name take-off 1889); the null holds on both | [`S2-RECEPTION-CLOCK.md`](S2-RECEPTION-CLOCK.md) |
| **S6 slice 1** — Gutenberg back matter | **no-go**: 4 publisher ads in 343 books / 42.2M words | [`S6-SLICE1-BACKMATTER-PROBE.md`](S6-SLICE1-BACKMATTER-PROBE.md) |
| **S6 slice 2** — the trade catalogue | **go**, and no page-scan OCR needed | [`S6-SLICE2-TRADE-CATALOGUE.md`](S6-SLICE2-TRADE-CATALOGUE.md) |
| **S6 slice 3** — the reception series | built: 3,487 issues, 128.5M words. `mystery story` absent 41 years then 1,605 hits; take-offs now ship as **bands** | [`S6-SLICE3-RECEPTION-SERIES.md`](S6-SLICE3-RECEPTION-SERIES.md) |
| **S7** — marginalia as a third class | marked passages recover **borrowing**, not influence; reading predicts style within-reader, 3 of 4 readers | [`S7-MARGINALIA.md`](S7-MARGINALIA.md) |

**The site is no longer frozen, and it is current.** Sections 10 and 11 of
`writing-topology/research/literature-mutations.html` carry the name clock and
the trade series, published 2026-09-04 on Aidan's instruction. Every figure on
that page comes from an emitter (`emit_reception_figure.py`,
`emit_trade_figure.py`) reading the JSON — **never hand-edit a number into the
page**; change the analysis, re-run the emitter, re-paste the block. The
unreproducible Phase 1 figures flagged in `RESEARCH-PROGRAM.md` are still there
by decision, and are still not yours to fix.

---

## Your task: S4/S5 — widen the author set

**The un-defer trigger has fired.** `RESEARCH-PROGRAM.md` deferred S4 (NovelTM
re-sampling) and S5 (HathiTrust EF) with a stated trigger: *the reception series
exists and the textual series must be re-run at frame scale to validate against
it.* It exists. Both sides of the intended regression are now real, and the
weaker one is 345 canon books.

S7 arrives at the same place from the other direction and hands you a concrete
target list: every marginalia number rests on **n between 6 and 21**, because
only 24 mark edges and 21 reference edges have both ends inside Phase 2's 77
authors, against the corpus's 2,139 source authors. *"The corpus is not the
limiting side."* Widening the author set is the one move that pays both debts.

**Second priority if that stalls: S3**, the instrument. S0 handed it the
strongest argument in the program — the old instrument's seed noise (±7.6)
swamps the null-model effect the README rests on (4.1). The textual series has
to be defensible to serve as the validation check. Full brief in
`RESEARCH-PROGRAM.md` § S3.

---

## Rules that still bind, and why

- **Do not run `build_canon.py`.** Two non-deterministic LLMs return a different
  canon and silently invalidate comparison with every published number.
- **Report and stop on any deviation** from a published number. Write up the
  delta and halt; Aidan calls it with the numbers in front of him. The halt
  applies to the *numbers*, not to the session.
- **Controls before counts.** Slice 2's genre-act detector shipped a real bug
  that its positive control caught first. S2's lesson 5 stands: a verification
  script is not automatically right.
- **Commit the raw pull before you analyse it** — a manifest, not the text,
  when the cache is large.
- **Period evidence only.** The trade series' authority is that it is what the
  trade said *at the time*; a modern label smuggled into it destroys exactly the
  thing that makes it worth having.
- **Take-offs are bands.** A fraction-of-peak crossing on a smoothed sparse
  series can precede the term's first actual use, and did (`sensation novel`,
  1859 against a first use of 1863 — which would have read as a replication of
  the Ngrams date). Band wider than 10 years ⇒ **not measurable**.

## One thing waiting on Aidan, not on a session

**The Stanford Literary Lab email is unblocked.** It was gated on S0 (corpus
back on disk) and on S6 existing; both are now true, and Phase 3 is public, so
there is something to point at. The hook is unchanged: their *Castle at the
Crossroads* project models the gothic **supervised**, and our unsupervised run
says the gothic is a perennial mode (z ≈ 0) while detective fiction is the one
datable birth (z ≈ −3.0). Plan and draft:
`~/.claude/projects/-Users-aidan-Desktop-writing-topology/memory/litlab-outreach-plan.md`.
Contacting a person is his call and his send — draft it, never send it.
