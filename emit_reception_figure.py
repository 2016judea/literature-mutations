'''
    Author: Aidan Jude & Claude
    S2 figures: the reception clock against the textual clock.

    Emitted as inline SVG in research/index.html's own idiom, for the same
    reason emit_paper_figures.py gives: the page's figures are SVG whose strokes
    are CSS classes bound to --ink2 / --faint / --accent, which is why they
    adapt to light and dark for free. Classes reused verbatim (.ed .ax .nd .ln
    .ac .acs .acd .band .lbl), W=680 to match Figs. 1-5.

    THE SITE IS FROZEN (docs/RESEARCH-PROGRAM.md, standing decisions), so this
    writes two files and touches nothing under writing-topology/:
      reception_clock_figure.html   paste-ready <figure> blocks, for the single
                                    site update at the END of the program
      reception_clock_preview.html  standalone, self-contained tokens, so the
                                    figures can actually be looked at now

    COLOR NOTE, recorded because it was checked rather than assumed.
    Running the dataviz validator on this paper's two ink tokens as a
    *categorical pair* fails:

      light  #544e44 vs #3a5a7c   normal-vision dE 9.1   (floor is 15)
      dark   #b3aa9a vs #7ea6c9   normal-vision dE 9.7

    The palette is deliberately near-achromatic newsprint and cannot be
    re-stepped - Figs. 1-5 already use these tokens and the page is frozen. So
    these figures do not encode two categories by hue. There is ONE measured
    series (the name clock, in accent) read against recessive context (the
    textual span, in faint), separated by vertical offset, marker size and a
    direct numeric label. That is also the more honest encoding: a full
    min-max range and an interquartile width are not two peers of one scale,
    and painting them as peers would imply a comparison the data does not
    support.

    Run:  python emit_reception_figure.py
    In:   reception_clock.json   (analyze_reception_clock.py)
'''

import json
import os

OUT_FRAG = "reception_clock_figure.html"
OUT_PREVIEW = "reception_clock_preview.html"

W = 680
WIN_START = 1800          # must match analyze_reception_clock.py
FLOOR_SLACK = 2           # take-off within this of the floor is "not datable"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# Row titles. The analysis carries a descriptive `vocab_reading` per community;
# at 12px monospace the longest of those overruns the label gutter and clips off
# the left edge of the viewBox (seen on the first render). These are the same
# readings, shortened to fit. Presentation only - the full reading stays in
# reception_clock.json and in the prose table.
SHORT = {
    "detective": "Detective fiction",
    "western": "Western fiction",
    "religious": "Religious fiction",
    "historical": "Historical romance",
    "domestic": "Domestic fiction",
    "gothic": "Gothic / sensation",
    "nautical": "Nautical adventure",
    "early_novel": "Novel of manners",
}


def datable(takeoff):
    '''A take-off at the window floor does not mean "took off in 1800" - it
    means the name was ALREADY in use when the readable window opens, so no
    date can be recovered. Rendering that as a date is the single easiest way
    for this figure to lie, so it gets its own predicate.'''
    return takeoff is not None and takeoff > WIN_START + FLOOR_SLACK


# --- Fig. 6: the two clocks -------------------------------------------------
def fig_two_clocks(res):
    rows = sorted(res["communities"], key=lambda r: r["concentration_z"])
    ctrl = res["controls"]["_ALL_CONTROLS"]
    n = len(rows)

    lo, hi = 1670, 1975          # 1670 holds the earliest year_min (1678);
    x0, x1 = 246, 612            # 1975 leaves room for the right-hand numbers
    top, dy = 58, 42
    H = top + (n + 1) * dy + 88

    def X(y):
        return x0 + (y - lo) / (hi - lo) * (x1 - x0)

    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="For each recovered '
         f'community, the span of its books in time against the span of its '
         f'genre name in Google Books. Detective fiction is the only community '
         f'whose name take-off is datable and lands inside its textual span.">']

    # the unreadable era. Pre-1800 Ngrams frequencies sit on a corpus small
    # enough that normalisation amplifies noise into apparent signal - "Gothic
    # romance" peaks in 1776 there. The brief excludes it; the figure shows the
    # exclusion rather than silently cropping to it.
    s.append(f'<rect class="band" x="{X(lo):.1f}" y="{top - 22}" '
             f'width="{X(WIN_START) - X(lo):.1f}" height="{(n + 1) * dy + 4}" '
             f'opacity=".07"/>')
    s.append(f'<path class="acd" d="M{X(WIN_START):.1f} {top - 22} '
             f'L{X(WIN_START):.1f} {top + (n + 1) * dy - 18}"/>')
    s.append(f'<text x="{X(WIN_START) - 5:.1f}" y="{top - 30}" text-anchor="end" '
             f'font-size="10.5" class="lbl">not readable</text>')
    s.append(f'<text x="{X(WIN_START) + 5:.1f}" y="{top - 30}" font-size="10.5" '
             f'class="lbl">name clock measured from 1800</text>')

    for i, r in enumerate(rows):
        y = top + i * dy
        nm = r["name"]
        y_txt, y_nm = y - 7, y + 8

        # left column: the vocabulary reading, then the terms actually queried.
        # The held-out label is NOT the row title - three of the eight disagree
        # with their own community's vocabulary (emit_paper_figures.py:70-74
        # found the same thing independently), and titling by label would carry
        # that error into the figure.
        s.append(f'<text class="lbl" x="238" y="{y - 4}" text-anchor="end" '
                 f'font-size="12">{esc(SHORT[r["key"]])}</text>')
        s.append(f'<text x="238" y="{y + 10}" text-anchor="end" font-size="9.5" '
                 f'opacity=".8">{esc(", ".join(r["terms"][:2]))}</text>')

        # textual clock: full min-max span of the community's books, recessive
        s.append(f'<path class="ed" d="M{X(r["year_min"]):.1f} {y_txt} '
                 f'L{X(r["year_max"]):.1f} {y_txt}"/>')
        for yr in (r["year_min"], r["year_max"]):
            s.append(f'<path class="ed" d="M{X(yr):.1f} {y_txt - 4} '
                     f'L{X(yr):.1f} {y_txt + 4}"/>')
        s.append(f'<text x="{X(r["year_max"]) + 7:.1f}" y="{y_txt + 3.5}" '
                 f'font-size="9.5" opacity=".85">σ {r["year_std"]:.0f}</text>')

        # name clock: interquartile span of usage mass, the measured series
        p25, p75 = nm["mass_p25"], nm["mass_p75"]
        if p25 is not None:
            s.append(f'<path class="acs" d="M{X(p25):.1f} {y_nm} '
                     f'L{X(p75):.1f} {y_nm}" stroke-linecap="round"/>')
            s.append(f'<text class="lbl" x="{X(p75) + 7:.1f}" y="{y_nm + 3.5}" '
                     f'font-size="9.5">{nm["mass_iqr"]}y</text>')

        # take-off marker, or an explicit "already in use" chevron at the floor
        t = nm["takeoff_10pct"]
        if datable(t):
            # the take-off sits well left of the usage bar in every datable row -
            # a name enters the language decades before the bulk of its use. Left
            # unconnected the dot read as a separate series on the first render,
            # so tie it to the bar it belongs to.
            if p25 is not None and t < p25:
                s.append(f'<path class="acd" d="M{X(t):.1f} {y_nm} '
                         f'L{X(p25):.1f} {y_nm}" opacity=".55"/>')
            s.append(f'<circle class="ac" cx="{X(t):.1f}" cy="{y_nm}" r="4.6"/>')
            s.append(f'<text class="lbl" x="{X(t):.1f}" y="{y_nm - 8}" '
                     f'text-anchor="middle" font-size="10">{t}</text>')
        else:
            s.append(f'<path class="acs" d="M{X(WIN_START) + 7:.1f} {y_nm - 4.5} '
                     f'L{X(WIN_START) + 1:.1f} {y_nm} '
                     f'L{X(WIN_START) + 7:.1f} {y_nm + 4.5}" fill="none"/>')
            s.append(f'<text class="lbl" x="{X(WIN_START) + 12:.1f}" '
                     f'y="{y_nm - 7}" font-size="10">already in use</text>')

    # control row, set apart: era-neutral phrases about fiction. If corpus
    # composition alone produced narrow naming mass, this row would be narrow
    # too. It is the widest thing on the chart, which is what licenses reading
    # any of the rows above as signal.
    y = top + n * dy + 10
    s.append(f'<path class="ed" d="M28 {y - 22} L{x1} {y - 22}" opacity=".3"/>')
    s.append(f'<text class="lbl" x="238" y="{y - 4}" text-anchor="end" '
             f'font-size="12">CONTROL — not a genre</text>')
    ctrl_terms = [k for k in res["controls"] if not k.startswith("_")][:2]
    s.append(f'<text x="238" y="{y + 10}" text-anchor="end" font-size="9.5" '
             f'opacity=".8">{esc(", ".join(ctrl_terms))}</text>')
    s.append(f'<path class="ln" d="M{X(ctrl["mass_p25"]):.1f} {y + 8} '
             f'L{X(ctrl["mass_p75"]):.1f} {y + 8}" stroke-linecap="round" '
             f'opacity=".55"/>')
    s.append(f'<text x="{X(ctrl["mass_p75"]) + 7:.1f}" y="{y + 11.5}" '
             f'font-size="9.5" opacity=".85">{ctrl["mass_iqr"]}y</text>')

    ay = top + (n + 1) * dy - 14
    s.append(f'<path class="ax" d="M{X(lo):.1f} {ay} L{X(1955):.1f} {ay}"/>')
    for t in range(1700, 1951, 50):
        s.append(f'<path class="ax" d="M{X(t):.1f} {ay} L{X(t):.1f} {ay + 5}"/>')
        s.append(f'<text x="{X(t):.1f}" y="{ay + 19}" text-anchor="middle" '
                 f'font-size="11">{t}</text>')

    # two lines, not one: at 10.5px the single-line legend ran past the 680
    # viewBox and lost its last item (seen on the first render)
    s.append(f'<text x="32" y="{ay + 38}" font-size="10.5" class="lbl">'
             f'—— books in the community (min–max)      '
             f'σ = spread of those years</text>')
    s.append(f'<text x="32" y="{ay + 54}" font-size="10.5" class="lbl">'
             f'<tspan class="ac" font-size="13">●</tspan> name take-off  '
             f'┄┄ ━━ middle half of the name’s use</text>')
    s.append("</svg>")

    det = next(r for r in rows if r["key"] == "detective")
    d = det["name"]
    cap = (
        f'<figcaption class="figcap"><b>Fig. 6 — Two clocks on the same '
        f'genres.</b> Thin rules are each community’s books in time; '
        f'<span class="n">accent</span> is when its genre <i>name</i> entered '
        f'English, measured from Google Books with no dependence on the text '
        f'pipeline. Only <span class="n">detective fiction</span> has a datable '
        f'name take-off that lands inside its own textual span '
        f'(<span class="n">{d["takeoff_10pct"]}</span> against books of '
        f'{det["year_min"]}–{det["year_max"]}), and the name peaks in '
        f'<span class="n">{d["peak_year_in_window"]}</span> — the golden age. '
        f'The rest were already in use before the readable window opens, which '
        f'is what a perennial mode looks like from the reception side. Rows are '
        f'titled by each cluster’s own vocabulary, not by its held-out '
        f'label: three of the eight labels disagree with the cluster they name '
        f'(see Fig. 7). The control row is era-neutral phrasing about fiction '
        f'(“the novel”, “a novel”), and its naming mass is '
        f'<span class="n">{ctrl["mass_iqr"]}y</span> wide — as spread as the '
        f'widest genre here and {ctrl["mass_iqr"] / d["mass_iqr"]:.1f}× wider '
        f'than detective’s {d["mass_iqr"]}y. Corpus composition does not '
        f'manufacture narrow naming mass, so the narrow rows are signal and '
        f'not an artifact of Google Books growing.</figcaption>'
    )
    return (f'    <figure class="fig">\n      <div class="fig-scroll">'
            f'{"".join(s)}</div>\n      {cap}\n    </figure>')


# --- Fig. 7: what the held-out labels would have done -----------------------
def fig_label_trap(res):
    bad = [r for r in res["communities"]
           if not r["label_agrees_with_vocab"] and "name_from_label_terms" in r]
    n = len(bad)

    lo, hi = 1795, 1960
    x0, x1 = 246, 592
    top, dy = 56, 46
    H = top + n * dy + 80

    def X(y):
        return x0 + (y - lo) / (hi - lo) * (x1 - x0)

    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="For the three '
         f'communities whose held-out label disagrees with their vocabulary, '
         f'the label-derived name take-off is 60 to 140 years later than the '
         f'vocabulary-derived one.">']

    for i, r in enumerate(bad):
        y = top + i * dy
        a = r["name"]["takeoff_10pct"]
        b = r["name_from_label_terms"]["takeoff_10pct"]

        s.append(f'<text class="lbl" x="238" y="{y - 3}" text-anchor="end" '
                 f'font-size="12">{esc(SHORT[r["key"]])}</text>')
        s.append(f'<text x="238" y="{y + 11}" text-anchor="end" font-size="9.5" '
                 f'opacity=".8">labelled “{esc(r["held_out_label"])}”</text>')

        ax_, bx = X(max(a, lo)), X(b)
        s.append(f'<path class="ed" d="M{ax_:.1f} {y} L{bx:.1f} {y}"/>')
        # the drift, as an arrow from truth to artifact
        s.append(f'<path class="acd" d="M{ax_:.1f} {y} L{bx - 7:.1f} {y}"/>')
        s.append(f'<path class="acs" d="M{bx - 8:.1f} {y - 4.5} L{bx - 1:.1f} {y} '
                 f'L{bx - 8:.1f} {y + 4.5}" fill="none"/>')
        s.append(f'<circle class="nd" cx="{ax_:.1f}" cy="{y}" r="4.4"/>')
        # a non-datable take-off prints as the window floor, not as its raw
        # crossing year: "1801" is not a date, it is the floor plus noise, and
        # printing it invites a reader to treat it as a measurement
        a_lbl = f"≤{WIN_START}" if not datable(a) else str(a)
        s.append(f'<text x="{ax_:.1f}" y="{y - 10}" text-anchor="middle" '
                 f'font-size="10.5" class="lbl">{a_lbl}</text>')
        s.append(f'<text class="lbl" x="{bx + 8:.1f}" y="{y + 4}" '
                 f'font-size="11">{b}</text>')
        s.append(f'<text x="{(ax_ + bx) / 2:.1f}" y="{y + 17}" '
                 f'text-anchor="middle" font-size="10" opacity=".85">'
                 f'+{b - a} years</text>')

    ay = top + n * dy - 6
    s.append(f'<path class="ax" d="M{X(1800):.1f} {ay} L{X(1955):.1f} {ay}"/>')
    for t in range(1800, 1951, 50):
        s.append(f'<path class="ax" d="M{X(t):.1f} {ay} L{X(t):.1f} {ay + 5}"/>')
        s.append(f'<text x="{X(t):.1f}" y="{ay + 19}" text-anchor="middle" '
                 f'font-size="11">{t}</text>')
    s.append(f'<text x="32" y="{ay + 40}" font-size="10.5" class="lbl">'
             f'<tspan class="nd" font-size="13">●</tspan> dated from the '
             f'cluster’s own vocabulary</text>')
    s.append(f'<text x="32" y="{ay + 56}" font-size="10.5" class="lbl">'
             f'┄→ dated instead from its held-out label</text>')
    s.append("</svg>")

    worst = max(bad, key=lambda r: r["name_from_label_terms"]["takeoff_10pct"]
                - r["name"]["takeoff_10pct"])
    dw = (worst["name_from_label_terms"]["takeoff_10pct"]
          - worst["name"]["takeoff_10pct"])
    cap = (
        f'<figcaption class="figcap"><b>Fig. 7 — The cost of trusting the '
        f'label.</b> Three of the eight held-out Gutenberg labels name a genre '
        f'their own cluster is not: the cluster labelled '
        f'“Science fiction” has the vocabulary <i>castle, veil, '
        f'trembled</i>, and the one labelled “Fantasy fiction” has '
        f'<i>archbishop, cardinal, priest</i>. Dating those clusters by their '
        f'label instead of their vocabulary moves the answer '
        f'<span class="n">+{dw} years</span> in the worst case '
        f'({esc(worst["vocab_reading"])}) and invents a twentieth-century '
        f'emergence for a mode that was already named before 1800. The labels '
        f'validate <i>that</i> a cluster is recognised; they do not license '
        f'dating it.</figcaption>'
    )
    return (f'    <figure class="fig">\n      <div class="fig-scroll">'
            f'{"".join(s)}</div>\n      {cap}\n    </figure>')


# --- preview scaffold -------------------------------------------------------
# The real tokens, copied from writing-topology/research/index.html:15-16 and
# the .fig rules at :108-128. Duplicated here ONLY so the figures can be
# rendered and inspected while the site is frozen; the site remains the source
# of truth and this file is not deployed.
PREVIEW = '''<!doctype html>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>S2 reception clock — figure preview</title>
<style>
:root{{--bg:#f7f3ec;--bg2:#efe9dd;--ink:#1c1814;--ink2:#544e44;--faint:#8b8478;
  --rule:rgba(60,50,40,.16);--accent:#3a5a7c}}
@media(prefers-color-scheme:dark){{:root{{--bg:#15120f;--bg2:#1d1916;--ink:#e9e3d5;
  --ink2:#b3aa9a;--faint:#7d766a;--rule:rgba(230,220,200,.16);--accent:#7ea6c9}}}}
body{{background:var(--bg);color:var(--ink);font-family:Georgia,serif;line-height:1.5;
  max-width:760px;margin:0 auto;padding:32px 20px 60px}}
h1{{font-family:ui-monospace,monospace;font-size:13px;letter-spacing:.18em;
  text-transform:uppercase;color:var(--faint);font-weight:500}}
.fig{{margin:26px 0 6px}}
.fig svg{{width:100%;height:auto;display:block;background:var(--bg2);
  border:1px solid var(--rule);border-radius:7px}}
.fig .ed{{stroke:var(--faint);stroke-width:1.2;fill:none;opacity:.5}}
.fig .ax{{stroke:var(--faint);stroke-width:1.3;fill:none}}
.fig .nd{{fill:var(--ink2)}}
.fig .ln{{stroke:var(--ink2);stroke-width:2.2;fill:none}}
.fig .ac{{fill:var(--accent)}}
.fig .acs{{stroke:var(--accent);stroke-width:2;fill:none}}
.fig .acd{{stroke:var(--accent);stroke-width:1.6;stroke-dasharray:5 5;fill:none}}
.fig .band{{fill:var(--accent);opacity:.10}}
.fig text{{font-family:ui-monospace,monospace;fill:var(--faint)}}
.fig .lbl{{fill:var(--ink2)}}
.fig-scroll{{overflow-x:auto;overflow-y:hidden;-webkit-overflow-scrolling:touch}}
.fig-scroll svg{{min-width:600px}}
.figcap{{margin:11px 0 4px;font-family:ui-monospace,monospace;font-size:11.5px;
  color:var(--faint);text-align:center;letter-spacing:.02em;line-height:1.55}}
.figcap b{{color:var(--ink2);font-weight:500}}.figcap .n{{color:var(--accent)}}
</style>
<h1>S2 — reception clock (preview, not deployed)</h1>
{body}
'''


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    with open("reception_clock.json") as fh:
        res = json.load(fh)

    blocks = [fig_two_clocks(res), fig_label_trap(res)]
    with open(OUT_FRAG, "w") as fh:
        fh.write("\n\n".join(blocks) + "\n")
    with open(OUT_PREVIEW, "w") as fh:
        fh.write(PREVIEW.format(body="\n".join(blocks)))

    print(f"wrote {OUT_FRAG} ({len(blocks)} figures) and {OUT_PREVIEW}")
    for b in blocks:
        print(f"  {len(b)} chars")


if __name__ == "__main__":
    main()
