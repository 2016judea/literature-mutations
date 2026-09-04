'''
    Author: Aidan Jude & Claude
    Phase 3 figures: the American book trade's own dated classifications.

    Same idiom and the same reasons as emit_reception_figure.py — inline SVG
    whose strokes are the page's CSS classes (.ed .ax .nd .ln .ac .acs .acd
    .band .lbl), W=680 to match Figs. 1-7, so the figures adapt to light and
    dark for free and no number on them is ever typed by hand.

    COLOR NOTE carries over verbatim from emit_reception_figure.py: this
    palette's two ink tokens fail the categorical-pair floor (dE 9.1 light,
    9.7 dark), so hue never carries a category here. Fig. 8 has ONE measured
    series in accent (`mystery story`, the finding) read against recessive
    context in ink2 (`detective story`), separated by weight, a direct label
    and vertical position. Fig. 9 uses accent for a single binary that is a
    verdict rather than a category — whether a take-off is measurable at all.

    THE SITE IS NO LONGER FROZEN FOR THIS WORK. Aidan asked for Phase 3 to be
    published, 2026-09-04, which lifts the standing freeze in
    docs/RESEARCH-PROGRAM.md for these figures exactly as his 2026-08-27
    instruction lifted it for S7. This script still writes only its own two
    files; the paste into writing-topology is a separate, deliberate step.

      trade_series_figure.html    paste-ready <figure> blocks
      trade_series_preview.html   standalone, self-contained tokens

    Run:  python emit_trade_figure.py
    In:   reception_series.json        (build_reception_series.py)
          reception_clock_trade.json   (analyze_reception_series.py)
'''

import json
import os

OUT_FRAG = "trade_series_figure.html"
OUT_PREVIEW = "trade_series_preview.html"

W = 680
SMOOTH_LABEL = {"smooth_9": "9", "smooth_5": "5", "smooth_3": "3",
                "smooth_1": "1"}

# Row titles for Fig. 9. `detective (any)` is the union term the analysis
# carries beside `detective story`; both ship, because the union is what makes
# the 1873 sustained date defensible and dropping it would flatter the result.
SHORT = {
    "detective story": "detective story",
    "detective (any)": "detective (any form)",
    "mystery story": "mystery story",
    "sensation novel": "sensation novel",
    "scientific romance": "scientific romance",
    "ghost story": "ghost story",
    "historical romance": "historical romance",
    "adventure story": "adventure story",
    "western story": "western story",
    "love story": "love story",
    "sea story": "sea story",
}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def commas(n):
    return f"{n:,}"


def millions(n):
    return f"{n / 1e6:.1f}M"


# --- Fig. 8: the term that is absent, then everywhere ------------------------
def fig_absent_then_everywhere(series, clock):
    by = series["by_year"]
    years = sorted(int(y) for y in by)
    find = {f["term"]: f for f in clock["findings"]}
    my, det = find["mystery story"], find["detective story"]

    def vals(term):
        return [by[str(y)]["per_million"][term] for y in years]

    v_my, v_det = vals("mystery story"), vals("detective story")
    top = max(max(v_my), max(v_det))

    x0, x1, ytop, ybase = 62, 648, 34, 250
    def X(y):
        return x0 + (y - years[0]) * (x1 - x0) / (years[-1] - years[0])
    def Y(v):
        return ybase - v * (ybase - ytop) / top

    s = [f'<svg viewBox="0 0 {W} 322" role="img" aria-label="Per-million-word '
         f'frequency of the phrase mystery story in the American book trade, '
         f'{years[0]} to {years[-1]}. It is absent for {my["absent_window"][1] - my["absent_window"][0] + 1} '
         f'years and then rises to a plateau, while detective story is present '
         f'from the start of the readable window.">']

    # the absent run, as a shaded region of the plot rather than a note
    a0, a1 = my["absent_window"]
    s.append(f'<rect class="band" x="{X(a0):.1f}" y="{ytop}" '
             f'width="{X(a1) - X(a0):.1f}" height="{ybase - ytop}" opacity=".07"/>')
    # the take-off band
    t0, t1 = (int(v) for v in my["takeoff"].split("-"))
    s.append(f'<rect class="band" x="{X(t0):.1f}" y="{ytop}" '
             f'width="{X(t1) - X(t0):.1f}" height="{ybase - ytop}" opacity=".16"/>')

    # y grid + ticks, in whole tens per million
    step = 20
    v = 0
    while v <= top:
        s.append(f'<path class="ed" d="M{x0} {Y(v):.1f} L{x1} {Y(v):.1f}" '
                 f'opacity=".25"/>')
        s.append(f'<text x="{x0 - 8}" y="{Y(v) + 4:.1f}" text-anchor="end" '
                 f'font-size="10.5">{v}</text>')
        v += step
    s.append(f'<text x="{x0 - 8}" y="{ytop - 12}" text-anchor="end" '
             f'font-size="10" class="lbl">per million</text>')

    # recessive context first, so the measured series sits over it
    d = " ".join(f'{"M" if i == 0 else "L"}{X(y):.1f} {Y(val):.1f}'
                 for i, (y, val) in enumerate(zip(years, v_det)))
    s.append(f'<path class="ln" d="{d}" opacity=".45"/>')

    d = " ".join(f'{"M" if i == 0 else "L"}{X(y):.1f} {Y(val):.1f}'
                 for i, (y, val) in enumerate(zip(years, v_my)))
    s.append(f'<path class="acs" d="{d}"/>')

    # Labelled where each curve is alone on its patch of the plot rather than
    # at a shared peak: the two cross repeatedly after 1918, and every label
    # placed in that zone sat on the other line. detective at 1899 (12.7, with
    # mystery still at 0); mystery above its own 1920 maximum, which is the one
    # point where it is the upper line and nothing is above it.
    def at(term, yr):
        return by[str(yr)]["per_million"][term]
    top_my = max(range(len(years)), key=lambda i: v_my[i])
    s.append(f'<text x="{X(1899):.1f}" y="{Y(at("detective story", 1899)) - 10:.1f}" '
             f'text-anchor="middle" font-size="10.5" class="lbl">detective story</text>')
    s.append(f'<text x="{X(years[top_my]):.1f}" y="{Y(v_my[top_my]) - 11:.1f}" '
             f'text-anchor="middle" font-size="11.5" class="lbl">mystery story</text>')

    # first occurrence
    fy = my["present_window"][0]
    s.append(f'<circle class="ac" cx="{X(fy):.1f}" cy="{Y(by[str(fy)]["per_million"]["mystery story"]):.1f}" r="4"/>')
    s.append(f'<path class="acd" d="M{X(fy):.1f} {ytop + 44} L{X(fy):.1f} '
             f'{Y(by[str(fy)]["per_million"]["mystery story"]) - 8:.1f}"/>')
    s.append(f'<text x="{X(fy):.1f}" y="{ytop + 38}" text-anchor="middle" '
             f'font-size="10.5" class="lbl">first use {fy}</text>')

    # The zero run, labelled inside its own region — high in the band, where
    # neither series has yet risen, so the type never sits on a line.
    mid = (X(a0) + X(a1)) / 2
    s.append(f'<text x="{mid:.1f}" y="{ytop + 70}" text-anchor="middle" '
             f'font-size="12" class="lbl">zero, {a1 - a0 + 1} years</text>')
    s.append(f'<text x="{mid:.1f}" y="{ytop + 86}" text-anchor="middle" '
             f'font-size="10.5">{millions(my["absent_words"])} words · '
             f'{commas(my["absent_issues"])} issues</text>')
    s.append(f'<text x="{(X(t0) + X(t1)) / 2:.1f}" y="{ytop - 6}" '
             f'text-anchor="middle" font-size="10" class="lbl">take-off {my["takeoff"]}</text>')

    # x axis
    s.append(f'<path class="ax" d="M{x0} {ybase} L{x1} {ybase}"/>')
    for y in range(1860, years[-1] + 1, 20):
        s.append(f'<path class="ax" d="M{X(y):.1f} {ybase} L{X(y):.1f} {ybase + 5}"/>')
        s.append(f'<text x="{X(y):.1f}" y="{ybase + 20}" text-anchor="middle" '
                 f'font-size="11">{y}</text>')
    s.append(f'<text x="{x0}" y="{ybase + 46}" font-size="10.5" class="lbl">'
             f'{commas(clock["issues"])} dated issues · '
             f'{commas(clock["words_ocr"])} words of trade OCR · '
             f'American Publishers’ Circular spliced ahead of Publishers’ Weekly</text>')
    s.append('</svg>')

    cap = (
        f'<figcaption class="figcap"><b>Fig. 8 — A genre name entering the '
        f'trade.</b> The phrase <span class="n">“mystery story”</span> appears '
        f'<span class="n">zero times</span> in {millions(my["absent_words"])} '
        f'words of the American book trade across {commas(my["absent_issues"])} '
        f'issues, {a0}–{a1} — then {commas(my["present_hits"])} times in the '
        f'{my["present_window"][1] - my["present_window"][0] + 1} years that '
        f'follow. First use <span class="n">{fy}</span>, sustained from '
        f'{my["sustained_from"]}, take-off <span class="n">{my["takeoff"]}</span>, '
        f'plateau to the {years[-1]} ceiling. It is not one repeated house ad and '
        f'not authors’ titles: the hits sit in the trade’s own descriptive line, '
        f'where <i>“a mystery story for girls”</i> is a shelf label rather than a '
        f'review. <span class="n">“Detective story”</span> is drawn behind it as '
        f'context, not as a peer series — it is already present when the readable '
        f'window opens ({det["absent_window"][1]}), sustained from '
        f'{det["sustained_from"]}, and still rising at {years[-1]}.</figcaption>'
    )
    return (f'    <figure class="fig">\n      <div class="fig-scroll">'
            f'{"".join(s)}</div>\n      {cap}\n    </figure>')


# --- Fig. 9: take-offs ship as bands ----------------------------------------
def fig_bands(clock):
    terms = clock["series"]["per_million"]["terms"]
    tol = clock["estimator"]["tolerance_years"]
    rows = sorted(terms.items(),
                  key=lambda kv: (kv[1]["takeoff_spread_years"] is None,
                                  kv[1]["takeoff_spread_years"] or 0))

    lo, hi = 1850, 1935
    x0, x1 = 196, 486        # the verdicts live in a fixed column at NOTE_X,
    NOTE_X = 498             # so the widest band cannot push one off the frame
    rowh, top = 26, 40
    # `sensation novel` carries a callout above its row; the extra headroom is
    # inserted before it rather than the callout being squeezed into the gap
    # between two rows, where it landed on the wrong band.
    CALLOUT = "sensation novel"
    gap_at = [t for t, _ in rows].index(CALLOUT)
    GAP = 18
    H = top + rowh * len(rows) + GAP + 66

    def X(y):
        return x0 + (y - lo) * (x1 - x0) / (hi - lo)

    def ROW(i):
        return top + i * rowh + (GAP if i >= gap_at else 0)

    n_meas = sum(1 for _, v in rows if v["takeoff_measurable"])
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="For each of the '
         f'{len(rows)} genre terms, the range of take-off years produced by four '
         f'smoothing widths. {n_meas} of {len(rows)} bands are narrower than '
         f'{tol} years and are reported as measurable; the rest are not.">']

    for i, (term, v) in enumerate(rows):
        y = ROW(i)
        known = [yr for yr in v["takeoff_band"].values() if yr is not None]
        meas = v["takeoff_measurable"]
        cls = "acs" if meas else "ed"
        s.append(f'<text class="lbl" x="{x0 - 12}" y="{y + 4}" '
                 f'text-anchor="end" font-size="12">{esc(SHORT[term])}</text>')
        # the band across smoothing widths
        s.append(f'<path class="{cls}" d="M{X(min(known)):.1f} {y} '
                 f'L{X(max(known)):.1f} {y}" stroke-linecap="round" '
                 f'stroke-width="{7 if meas else 5}" '
                 f'opacity="{1 if meas else .55}"/>')
        # first actual occurrence — the thing a smoothed take-off can precede
        s.append(f'<circle class="nd" cx="{X(v["first_hit"]):.1f}" cy="{y}" r="3.6"/>')
        spread = v["takeoff_spread_years"]
        if meas:
            s.append(f'<text class="lbl" x="{NOTE_X}" y="{y + 4}" '
                     f'font-size="10.5">{v["takeoff"]}</text>')
        else:
            miss = [k for k, val in v["takeoff_band"].items() if val is None]
            note = (f'no crossing at width {SMOOTH_LABEL[miss[0]]}' if miss
                    else f'{spread}y wide — not measurable')
            s.append(f'<text x="{NOTE_X}" y="{y + 4}" '
                     f'font-size="10.5" opacity=".85">{note}</text>')

    # the one that would have been a false replication
    sen = terms[CALLOUT]
    sy = ROW(gap_at)
    sx = X(sen["takeoff_band"]["smooth_9"])
    s.append(f'<path class="acd" d="M{sx:.1f} {sy - 14} L{sx:.1f} {sy - 6}"/>')
    s.append(f'<text x="{sx:.1f}" y="{sy - 18}" '
             f'text-anchor="middle" font-size="10" class="lbl">'
             f'band opens {sen["takeoff_band"]["smooth_9"]} — before its '
             f'{sen["first_hit"]} first use</text>')

    ax = ROW(len(rows) - 1) + 20
    s.append(f'<path class="ax" d="M{x0} {ax} L{x1} {ax}"/>')
    for y in range(1850, hi + 1, 25):
        s.append(f'<path class="ax" d="M{X(y):.1f} {ax} L{X(y):.1f} {ax + 5}"/>')
        s.append(f'<text x="{X(y):.1f}" y="{ax + 19}" text-anchor="middle" '
                 f'font-size="11">{y}</text>')
    s.append(f'<text x="32" y="{ax + 40}" font-size="10.5" class="lbl">'
             f'<tspan class="nd" font-size="13">●</tspan> first actual '
             f'occurrence  ━━ take-off across smoothing widths '
             f'{"/".join(str(k) for k in clock["estimator"]["smooth_widths_tested"])}'
             f'</text>')
    s.append(f'<text x="32" y="{ax + 56}" font-size="10.5" class="lbl">'
             f'accent = band ≤ {tol}y, reported as a date · '
             f'grey = wider, reported as not measurable</text>')
    s.append('</svg>')

    sea = terms["sea story"]
    cap = (
        f'<figcaption class="figcap"><b>Fig. 9 — Why take-offs ship as bands.</b> '
        f'A fraction-of-peak take-off computed on a <i>smoothed sparse</i> series '
        f'can precede the term’s first actual occurrence, because a moving average '
        f'spreads a first spike backwards. It did: <span class="n">sensation '
        f'novel</span> first appears in {sen["first_hit"]} and the estimator '
        f'reported <span class="n">{sen["takeoff_band"]["smooth_9"]}</span> — '
        f'which happens to match the Google Books date exactly, and would have '
        f'been read as a replication. Re-run across smoothing widths '
        f'{"/".join(str(k) for k in clock["estimator"]["smooth_widths_tested"])}, '
        f'<span class="n">sea story</span>’s take-off moves '
        f'<span class="n">{sea["takeoff_spread_years"]} years</span>. So every '
        f'take-off here is a band, a band wider than {tol} years is reported as '
        f'not measurable, and <span class="n">{n_meas} of {len(rows)}</span> terms '
        f'survive the rule.</figcaption>'
    )
    return (f'    <figure class="fig">\n      <div class="fig-scroll">'
            f'{"".join(s)}</div>\n      {cap}\n    </figure>')


# --- preview scaffold -------------------------------------------------------
# Tokens copied from writing-topology/research/literature-mutations.html, for
# the same reason emit_reception_figure.py copies them: so the figures can be
# looked at before anything is pasted. The site stays the source of truth.
PREVIEW = '''<!doctype html>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Phase 3 trade series — figure preview</title>
<style>
:root{{--bg:#f7f3ec;--bg2:#efe9dd;--ink:#1c1814;--ink2:#544e44;--faint:#8b8478;
  --rule:rgba(60,50,40,.16);--accent:#3a5a7c}}
@media(prefers-color-scheme:dark){{:root{{--bg:#15120f;--bg2:#1d1916;--ink:#e9e3d5;
  --ink2:#b3aa9a;--faint:#7d766a;--rule:rgba(230,220,200,.16);--accent:#7ea6c9}}}}
body{{background:var(--bg);color:var(--ink);
  font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;line-height:1.5;
  max-width:760px;margin:0 auto;padding:32px 20px 60px}}
h1{{font-size:13px;letter-spacing:.18em;text-transform:uppercase;
  color:var(--faint);font-weight:500}}
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
.fig text{{fill:var(--faint)}}
.fig .lbl{{fill:var(--ink2)}}
.fig-scroll{{overflow-x:auto;overflow-y:hidden;-webkit-overflow-scrolling:touch}}
.fig-scroll svg{{min-width:600px}}
.figcap{{margin:11px 0 4px;font-size:11.5px;color:var(--faint);text-align:center;
  letter-spacing:.02em;line-height:1.55}}
.figcap b{{color:var(--ink2);font-weight:500}}.figcap .n{{color:var(--accent)}}
</style>
<h1>Phase 3 — the trade series (preview, not deployed)</h1>
{body}
'''


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    with open("reception_series.json", encoding="utf-8") as fh:
        series = json.load(fh)
    with open("reception_clock_trade.json", encoding="utf-8") as fh:
        clock = json.load(fh)

    blocks = [fig_absent_then_everywhere(series, clock), fig_bands(clock)]
    with open(OUT_FRAG, "w", encoding="utf-8") as fh:
        fh.write("\n\n".join(blocks) + "\n")
    with open(OUT_PREVIEW, "w", encoding="utf-8") as fh:
        fh.write(PREVIEW.format(body="\n".join(blocks)))

    print(f"wrote {OUT_FRAG} ({len(blocks)} figures) and {OUT_PREVIEW}")
    for b in blocks:
        print(f"  {len(b)} chars")


if __name__ == "__main__":
    main()
