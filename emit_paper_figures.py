'''
    Author: Aidan Jude & Claude
    Emit the two new paper figures as inline SVG, in research/index.html's own
    idiom, generated from the result JSON rather than hand-drawn.

    WHY INLINE SVG AND NOT A RENDERED IMAGE
    The page's existing figures are hand-authored inline SVG whose strokes and
    fills are CSS classes bound to custom properties (--ink2, --faint, --accent).
    That is why they adapt to light and dark, and why the accent change from
    rust to blue propagated to them for free. A PNG or an MP4 cannot do that -
    it would need a light cut, a dark cut, and a re-render every time a token
    moves. So these are emitted in the same idiom, using the same classes.

    WHY GENERATED AND NOT TYPED
    Every coordinate here derives from subcluster_results.json,
    controls_results.json and stylistic_representation.json. A figure with
    hand-typed geometry drifts silently the moment an analysis is re-run; a
    figure emitted from the JSON either regenerates or fails loudly.

    Run:  python emit_paper_figures.py   ->   paper_figures.html
          then paste each <figure> block into research/index.html
'''

import json
import os
from statistics import NormalDist

OUT = "paper_figures.html"
ALPHA = 0.05

W = 680                       # matches the viewBox width of Figs 1-3


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# --- Figure: the emergence test ---------------------------------------------
def fig_emergence(controls, n_sub_tests, sub_z_crit):
    comms = sorted(controls["communities"], key=lambda c: c["concentration_z"])
    n = len(comms)
    z_crit = NormalDist().inv_cdf(ALPHA / n)          # Bonferroni over these n

    lo, hi = -4.0, 2.0
    x0, x1 = 232, 648
    top, dy = 44, 34
    H = top + n * dy + 52

    def X(z):
        return x0 + (z - lo) / (hi - lo) * (x1 - x0)

    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Temporal '
         f'concentration z-score for each of the {n} recovered communities. '
         f'Only detective fiction clears the corrected threshold.">']

    # the region that survives correction
    s.append(f'<rect class="band" x="{X(lo):.1f}" y="{top - 16}" '
             f'width="{X(z_crit) - X(lo):.1f}" height="{n * dy + 6}"/>')
    s.append(f'<path class="acd" d="M{X(z_crit):.1f} {top - 16} '
             f'L{X(z_crit):.1f} {top + n * dy - 10}"/>')
    s.append(f'<path class="ed" d="M{X(0):.1f} {top - 16} '
             f'L{X(0):.1f} {top + n * dy - 10}"/>')

    for i, c in enumerate(comms):
        y = top + i * dy
        z = c["concentration_z"]
        emergent = z <= z_crit
        cls = "ac" if emergent else "nd"
        label = c["held_out_label"] or "unlabelled"
        # The held-out label alone would be misleading: several are wrong (the
        # one labelled "Science fiction" is the Gothic novel, and "Best Books
        # Ever Listings" is a popularity shelf, not a genre). Printing each
        # cluster's own distinctive vocabulary beside its label lets a reader
        # see the mismatch rather than inherit it.
        terms = " ".join(c.get("top_terms", [])[:3])
        s.append(f'<text class="lbl" x="224" y="{y + 1}" text-anchor="end" '
                 f'font-size="12">{esc(label)}</text>')
        s.append(f'<text x="224" y="{y + 15}" text-anchor="end" '
                 f'font-size="10.5" opacity=".85">{esc(terms)}</text>')
        s.append(f'<path class="{"acs" if emergent else "ed"}" '
                 f'd="M{X(0):.1f} {y} L{X(z):.1f} {y}"/>')
        s.append(f'<circle class="{cls}" cx="{X(z):.1f}" cy="{y}" '
                 f'r="{5.5 if emergent else 4}"/>')
        s.append(f'<text x="{X(z) + (-12 if z < 0 else 12):.1f}" y="{y + 4}" '
                 f'text-anchor="{"end" if z < 0 else "start"}" '
                 f'font-size="11">{z:+.2f}</text>')

    ay = top + n * dy - 2
    s.append(f'<path class="ax" d="M{X(lo):.1f} {ay} L{X(hi):.1f} {ay}"/>')
    for t in range(int(lo), int(hi) + 1):
        s.append(f'<path class="ax" d="M{X(t):.1f} {ay} L{X(t):.1f} {ay + 5}"/>')
        s.append(f'<text x="{X(t):.1f}" y="{ay + 19}" text-anchor="middle" '
                 f'font-size="11">{t:+d}</text>')
    s.append(f'<text x="{X(lo):.1f}" y="{ay + 36}" font-size="11.5" '
             f'class="lbl">← more concentrated in time</text>')
    s.append(f'<text x="{X(hi):.1f}" y="{ay + 36}" text-anchor="end" '
             f'font-size="11.5" class="lbl">more spread out →</text>')
    s.append(f'<text x="{X(z_crit) - 6:.1f}" y="{top - 24}" text-anchor="end" '
             f'font-size="11" class="lbl">survives correction</text>')
    s.append("</svg>")

    cap = (f'<figcaption class="figcap"><b>Fig. 4 — Which communities are '
           f'genuinely datable.</b> Temporal concentration of each recovered '
           f'community against random same-size draws; <span class="n">z ≤ '
           f'{z_crit:.2f}</span> is the Bonferroni threshold for {n} tests. '
           f'Only <span class="n">detective fiction</span> clears it. Small grey '
           f'type is each cluster\'s own distinctive vocabulary, which does not '
           f'always match the label it was assigned. Sub-clustering the same '
           f'graph into as many as {n_sub_tests} finer communities, across seven '
           f'Louvain resolutions and ten seeds, leaves the answer unchanged: '
           f'detective alone, 10 of 10 seeds at every resolution — though past '
           f'resolution 2.0 the correction bar rises to {sub_z_crit:.2f} and nothing '
           f'clears it, including detective. 166 novels will not support finer '
           f'genre discovery than this.</figcaption>')
    return (f'    <figure class="fig">\n      <div class="fig-scroll">'
            f'{"".join(s)}</div>\n      {cap}\n    </figure>')


# --- Figure: the stylistic threshold sweep ----------------------------------
def fig_sweep(sweep):
    ts = [r["threshold"] for r in sweep]
    H = 300
    # x1 stops at 556, not 604: the series are direct-labelled to the right of
    # the last point and ran off the viewBox at the wider setting.
    x0, x1, y0, y1 = 96, 556, 44, 226
    zlo, zhi = -2.0, 10.0

    def X(t):
        return x0 + (t - ts[0]) / (ts[-1] - ts[0]) * (x1 - x0)

    def Y(z):
        return y1 - (z - zlo) / (zhi - zlo) * (y1 - y0)

    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Conceptual and '
         f'stylistic similarity z-scores as the minimum books per author rises. '
         f'Conceptual stays significant and declines smoothly; stylistic never '
         f'establishes a trend.">']

    # |z| < 2: the band where nothing is claimed
    s.append(f'<rect class="band" x="{x0}" y="{Y(2):.1f}" width="{x1 - x0}" '
             f'height="{Y(-2) - Y(2):.1f}" opacity=".07"/>')
    s.append(f'<path class="ed" d="M{x0} {Y(2):.1f} L{x1} {Y(2):.1f}"/>')
    s.append(f'<path class="ed" d="M{x0} {Y(0):.1f} L{x1} {Y(0):.1f}"/>')

    for key, cls, dot in (("conceptual", "acs", "ac"), ("stylistic", "ln", "nd")):
        pts = " ".join(f"{X(r['threshold']):.1f},{Y(r[key]['z']):.1f}"
                       for r in sweep)
        s.append(f'<polyline class="{cls}" points="{pts}" fill="none"/>')
        for r in sweep:
            s.append(f'<circle class="{dot}" cx="{X(r["threshold"]):.1f}" '
                     f'cy="{Y(r[key]["z"]):.1f}" r="3.6"/>')
        last = sweep[-1]
        s.append(f'<text x="{X(last["threshold"]) + 10:.1f}" '
                 f'y="{Y(last[key]["z"]) + 4:.1f}" font-size="12.5" '
                 f'class="lbl">{key}</text>')

    s.append(f'<path class="ax" d="M{x0} {y1} L{x1} {y1}"/>')
    s.append(f'<path class="ax" d="M{x0} {y0} L{x0} {y1}"/>')
    for z in (0, 2, 4, 6, 8, 10):
        s.append(f'<path class="ax" d="M{x0 - 5} {Y(z):.1f} L{x0} {Y(z):.1f}"/>')
        s.append(f'<text x="{x0 - 10}" y="{Y(z) + 4:.1f}" text-anchor="end" '
                 f'font-size="11">{z}</text>')
    for r in sweep:
        t = r["threshold"]
        s.append(f'<path class="ax" d="M{X(t):.1f} {y1} L{X(t):.1f} {y1 + 5}"/>')
        s.append(f'<text x="{X(t):.1f}" y="{y1 + 19}" text-anchor="middle" '
                 f'font-size="11">≥{t}</text>')
        s.append(f'<text x="{X(t):.1f}" y="{y1 + 34}" text-anchor="middle" '
                 f'font-size="10">{r["n_pairs"]}</text>')
    s.append(f'<text x="{X(ts[0]):.1f}" y="{y1 + 54}" text-anchor="middle" '
             f'font-size="10.5" class="lbl">books per author →</text>')
    s.append(f'<text x="{x0 - 10}" y="{y0 - 14}" text-anchor="end" '
             f'font-size="11" class="lbl">z</text>')
    s.append(f'<text x="{X(ts[-1]):.1f}" y="{y1 + 54}" text-anchor="end" '
             f'font-size="10.5" class="lbl">documented pairs remaining</text>')
    s.append("</svg>")

    st = {r["threshold"]: r for r in sweep}
    cap = (f'<figcaption class="figcap"><b>Fig. 5 — Two signals under the same '
           f'test.</b> Each point restricts authors to a minimum number of books '
           f'and re-runs the permutation test against a null drawn from that '
           f'same subset. <span class="n">Conceptual</span> similarity is '
           f'significant at every level and declines smoothly '
           f'({st[ts[0]]["conceptual"]["z"]:.1f} → {st[ts[-1]]["conceptual"]["z"]:.1f}) '
           f'as pairs are lost — a real effect losing power. '
           f'<span class="n">Stylistic</span> never establishes a trend: '
           f'{st[ts[0]]["stylistic"]["z"]:.1f}, then {st[2]["stylistic"]["z"]:.1f}, '
           f'then {st[3]["stylistic"]["z"]:.1f}, before a single excursion at '
           f'≥4 that decays again. Shaded band: |z| &lt; 2, where nothing is '
           f'claimed.</figcaption>')
    return (f'    <figure class="fig">\n      <div class="fig-scroll">'
            f'{"".join(s)}</div>\n      {cap}\n    </figure>')


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    controls = json.load(open("controls_results.json", encoding="utf-8"))
    sub = json.load(open("subcluster_results.json", encoding="utf-8"))
    styl = json.load(open("stylistic_representation.json", encoding="utf-8"))

    # the finest resolution tried, for the caption's "N sub-communities"
    n_sub = max(r["n_communities"] for r in sub["resolutions"])
    z_crit = min(r["bonferroni_z"] for r in sub["resolutions"])

    blocks = [fig_emergence(controls, n_sub, z_crit),
              fig_sweep(styl["threshold_sweep"])]
    open(OUT, "w").write("\n\n".join(blocks) + "\n")
    print(f"wrote {OUT}  ({len(blocks)} figures)")
    for b in blocks:
        print(f"  {len(b)} chars")


if __name__ == "__main__":
    main()
