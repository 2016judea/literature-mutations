'''
    Author: Aidan Jude & Claude
    The animation §4 of the proposal asks for.

    docs/PROPOSAL.md §4 closes on an open question: hierarchical clustering is
    the more natural fit for genres/subgenres, but should it be top-down
    (divisive) or bottom-up (agglomerative)? That is really a question about
    literary history - do genres differentiate INTO subgenres, or do subgenres
    coalesce INTO genres? - and the proposal's own last line suggests the way to
    look at it: "watching the graph as a whole formed on a year-by-year
    publication basis."

    This renders exactly that: the genre network accreting one publication year
    at a time, 1678-1928, with the mutation ledger (births / splits / merges)
    running underneath so the divisive-vs-agglomerative balance is legible as it
    happens rather than asserted afterwards.

    Two outputs, because a PDF cannot hold a video:
      genre_growth.mp4                  - the animation (supplementary material)
      figure_genre_growth_panels.pdf    - the same growth as six stills, which
        .png                              is what actually goes in the paper

    DATA PROVENANCE (same constraint, and same solution, as visualize_genres.py)
    _data/books.json - the real Gutenberg full-text corpus - is not in this
    checkout; rebuilding it means re-running build_canon.py + build_corpus.py
    against Gutenberg/LLM APIs. So nothing here is recomputed. Every value drawn
    is lifted from a checked-in artifact of a real run:

      genre_network.html  ->  the 166-novel author-controlled layout: per-book
                              title/author/year, x/y position, community
                              assignment, the 760 k-NN edges, and the eight
                              community names/colors/z-scores. This is the same
                              embedded DATA object the live site renders, so the
                              video and the interactive page cannot disagree.
      results.json        ->  the dated mutation ledger (births/splits/merges
                              per year) and the null model, from the full
                              345-novel run.

    Those two are different runs of the same pipeline and the frame says so:
    the network is the author-controlled corpus (one book per author, the
    confound-controlled view), the ledger is the full corpus. No number here is
    typed by hand or recomputed from a different method than the one published.

    HONESTY NOTE, carried on the frame itself
    results.json's own null model finds the event count indistinguishable from
    shuffled publication dates (90 real vs 94 +/- 15, z = -0.27). So the ledger
    must never be narrated as a rate or an acceleration - the README already
    retired that claim. What the animation legitimately shows is the *shape* of
    formation (which clusters seed early, which differentiate late, whether
    splits or merges carry the structure), not a speed.

    Node POSITIONS are from the final graph layout and are therefore fixed for
    the whole run; only a novel's presence is temporal. Edges are the final
    k-NN graph induced on the novels published so far - the paper rebuilds k-NN
    per snapshot, which needs the vectors we do not have. Both facts are
    printed on the frame; neither affects who is adjacent to whom at the end.

    Run:  python animate_genre_growth.py            # both outputs
          python animate_genre_growth.py --panels   # stills only (fast)
'''

import json
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.animation import FuncAnimation, FFMpegWriter

SRC = "genre_network.html"
RESULTS = "results.json"
OUT_MP4 = "genre_growth.mp4"
OUT_PANELS = "figure_genre_growth_panels"

# --- theme: the warm paper of research/literature-mutations.html -------------
BG = "#f7f3ec"
BG2 = "#efe9dd"
INK = "#1c1814"
INK2 = "#544e44"
RULE = (0.235, 0.196, 0.157, 0.16)
SERIF = ["Iowan Old Style", "Georgia", "Palatino", "DejaVu Serif"]
MONO = ["Menlo", "DejaVu Sans Mono"]
SYMBOL = ["DejaVu Sans"]          # the serif faces have no ★ glyph — it tofus

# A novel whose community has not yet cohered, and the links between them.
NEUTRAL_NODE = [0.62, 0.59, 0.55, 1.0]
NEUTRAL_EDGE = [0.235, 0.196, 0.157, 1.0]

# Ledger series. Not the genre palette - these encode event type, not identity,
# and a viewer must never read them as a ninth and tenth genre. Validated with
# the dataviz skill's validate_palette.js against this surface: passes all six
# checks (lightness band, chroma floor, CVD separation, normal-vision floor,
# contrast). Do not hand-tune these without re-running that script.
C_SPLIT = "#c2412a"
C_MERGE = "#0f6fb3"
C_BIRTH = "#94690a"

YEAR0, YEAR1 = 1678, 1928
SUB = 2            # animation frames per publication year
FPS = 24
HOLD_START = 36    # ~1.5s on the empty frame so the title can be read
HOLD_END = 96      # ~4s on the finished graph so the answer can be read
FLASH_TAU = 6.0    # frames; how fast a newly published novel stops flashing
EDGE_FADE = 8.0    # frames; how fast a new edge reaches full (low) alpha


# --- extraction --------------------------------------------------------------
def extract_data(path):
    '''Pull the embedded DATA object out of the published interactive page.'''
    html = open(path, encoding="utf-8").read()
    i = html.index("const DATA =")
    seg = html[i + len("const DATA ="):]
    depth, start = 0, None
    for j, ch in enumerate(seg):
        if ch == "{":
            if depth == 0:
                start = j
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(seg[start:j + 1])
    raise RuntimeError(f"couldn't find embedded DATA in {path}")


def load_ledger(path):
    '''Cumulative births/splits/merges by year, plus the null model.'''
    r = json.load(open(path, encoding="utf-8"))
    tl = sorted(r["timeline"], key=lambda t: t["year"])
    years = np.array([t["year"] for t in tl])
    out = {k: np.cumsum([t[k] for t in tl]) for k in ("births", "splits", "merges")}
    out["raw"] = {k: np.array([t[k] for t in tl]) for k in ("births", "splits", "merges")}
    out["years"] = years
    out["null"] = r["honest_metrics"]["null_model"]
    out["n_books"] = r["n_books"]
    return out


# --- shared scene construction ----------------------------------------------
class Scene:
    '''Everything both the video and the stills need, built once.'''

    def __init__(self, data, ledger):
        self.meta = data["meta"]
        self.ledger = ledger
        self.genres = sorted(data["genres"], key=lambda g: g["idx"])

        books = data["books"]
        self.xy = np.array([[b["x"], b["y"]] for b in books])
        self.year = np.array([b["year"] for b in books], dtype=float)
        self.gidx = np.array([b["genre"] for b in books])
        self.titles = [b["title"] for b in books]
        self.colors = np.array([_rgba(self.genres[g]["color"]) for g in self.gidx])

        e = np.array(data["edges"])
        self.segs = np.stack([self.xy[e[:, 0]], self.xy[e[:, 1]]], axis=1)
        self.e_year = np.maximum(self.year[e[:, 0]], self.year[e[:, 1]])
        self.e_g = self.gidx[e[:, 0]]
        self.e_same = self.gidx[e[:, 0]] == self.gidx[e[:, 1]]
        # An edge inside a community is the structure; an edge across two is the
        # seam between them. Drawing the seam fainter is what lets clusters read
        # as clusters at 166 nodes without drawing hulls that imply hard borders.
        self.e_rgba = np.array([_rgba(self.genres[g]["color"]) for g in self.e_g])

    # --- per-frame state -----------------------------------------------------
    def counts(self, ynow):
        return np.array([np.sum((self.gidx == g["idx"]) & (self.year <= ynow))
                         for g in self.genres])

    def genre_active(self, ynow):
        '''A community only "exists" once >=3 of its novels are published.

        This is not a display flourish - it is temporal_network.py's own rule
        (detect_communities drops communities of fewer than 3 members as specks).
        Applying it here is what makes the animation answer §4 instead of merely
        illustrating it: a novel is drawn neutral until the cluster it will
        belong to has actually cohered, so the viewer watches clusters BECOME
        clusters rather than seeing the final answer painted on from frame one.
        '''
        return self.counts(ynow) >= 3

    def node_state(self, ynow):
        age = (ynow - self.year) * SUB
        live = age >= 0
        flash = np.where(live, np.exp(-np.clip(age, 0, None) / FLASH_TAU), 0.0)
        sizes = np.where(live, 26 + 190 * flash, 0.0)
        face = self.node_colors(ynow)
        face[:, 3] = np.where(live, 1.0, 0.0)
        return live, flash, sizes, face

    def node_colors(self, ynow):
        '''Genre colour once the community has cohered; neutral before that.'''
        active = self.genre_active(ynow)
        face = self.colors.copy()
        face[~active[self.gidx]] = NEUTRAL_NODE
        return face

    def edge_state(self, ynow, instant=False):
        age = (ynow - self.e_year) * SUB
        live = age >= 0
        ramp = np.where(live, 1.0 if instant else np.clip(age / EDGE_FADE, 0.0, 1.0), 0.0)
        active = self.genre_active(ynow)
        # An edge reads as community structure only if it is internal to a
        # community that has cohered; otherwise it is just a similarity link.
        cohered = self.e_same & active[self.e_g]
        rgba = np.where(cohered[:, None], self.e_rgba, np.array(NEUTRAL_EDGE))
        rgba = rgba.copy()
        rgba[:, 3] = ramp * np.where(cohered, 0.30, 0.10)
        return rgba


def _rgba(hexstr):
    h = hexstr.lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)] + [1.0]


# --- figure scaffolding ------------------------------------------------------
def style_network_axes(ax, scene, pad=0.06, top_pad=0.06):
    '''top_pad buys blank sky for the year/count labels.

    The alternative - a surface plate behind the label - visibly washed out the
    nodes underneath it in the late panels. Never hide data to seat a label.
    '''
    x, y = scene.xy[:, 0], scene.xy[:, 1]
    dx, dy = x.max() - x.min(), y.max() - y.min()
    ax.set_xlim(x.min() - dx * pad, x.max() + dx * pad)
    ax.set_ylim(y.min() - dy * pad, y.max() + dy * top_pad)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_facecolor(BG)


def style_ledger_axes(ax, ledger):
    ax.set_facecolor(BG)
    ax.set_xlim(YEAR0, YEAR1)
    top = max(ledger["splits"][-1], ledger["merges"][-1], ledger["births"][-1])
    ax.set_ylim(0, top * 1.18)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("bottom", "left"):
        ax.spines[s].set_color(RULE)
        ax.spines[s].set_linewidth(0.8)
    ax.tick_params(colors=INK2, labelsize=9, length=3, width=0.8)
    for lbl in ax.get_xticklabels() + ax.get_yticklabels():
        lbl.set_fontfamily(MONO)
    ax.grid(axis="y", color=RULE, linewidth=0.6, alpha=0.7)
    ax.set_axisbelow(True)


def build_figure(scene):
    '''Explicit axes rather than a gridspec.

    The layout is a network with equal aspect, and the layout's data is 1.09:1 -
    near square. Dropped into a wide gridspec cell, equal aspect shrank the graph
    to the cell's HEIGHT and left half the frame empty, with the year label
    stranded in the middle. So the network gets a near-square box sized to the
    data, and everything else lives in the column that frees up.
    '''
    fig = plt.figure(figsize=(16, 9), dpi=120, facecolor=BG)
    ax_net = fig.add_axes([0.025, 0.115, 0.455, 0.730])
    style_network_axes(ax_net, scene, top_pad=0.18)
    ax_leg = fig.add_axes([0.525, 0.435, 0.450, 0.410])
    ax_leg.axis("off"); ax_leg.set_facecolor(BG)
    ax_led = fig.add_axes([0.565, 0.150, 0.400, 0.215])
    style_ledger_axes(ax_led, scene.ledger)
    return fig, ax_net, ax_leg, ax_led


def draw_titles(fig, scene):
    m = scene.meta
    fig.text(0.035, 0.945, "How the genre system of English fiction assembled itself",
             family=SERIF, fontsize=25, color=INK, va="center")
    fig.text(0.035, 0.900,
             f"{m['nAuthors']} novels, one per author  ·  positions fixed from the final "
             "k-NN layout, only publication is temporal  ·  a novel stays grey until its "
             "community reaches three members",
             family=SERIF, fontsize=12.5, color=INK2, va="center", style="italic")
    n = scene.ledger["null"]
    fig.text(0.025, 0.062,
             f"Ledger from the full {scene.ledger['n_books']}-novel run (results.json); "
             f"network is the {m['nAuthors']}-novel author-controlled layout "
             "(genre_network.html). Edges are the final k-NN graph induced on novels\n"
             f"published to date. Null model: {n['real_total_mutations']} real events "
             f"against {n['shuffled_mean']:.0f} ± {n['shuffled_std']:.0f} under shuffled "
             f"publication years (z = {n['z']}) — so the ledger shows the shape of genre "
             "formation, never a rate.",
             family=SERIF, fontsize=10.5, color=INK2, va="center", linespacing=1.6)


def draw_legend(ax, scene):
    '''Genre rail. Swatch, name and running count per community.

    Returns the handles the animation mutates each frame: a community stays grey
    and its name dim until it reaches three members, at which point it takes its
    colour. So the rail is a readout of how many genres exist *yet*, not a static
    key to the finished answer.
    '''
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.text(0.0, 0.975, "C O M M U N I T I E S", family=MONO, fontsize=9.5,
            color=INK2)
    swatches, names, counts = [], [], []
    rows = len(scene.genres)
    for i, g in enumerate(scene.genres):
        # The block is deliberately compressed into the top 62% of the axes: at
        # 80% the footnote below it overflowed the axes and printed across the
        # ledger's title and y-axis.
        y = 0.905 - i * (0.62 / rows)
        sw = plt.Rectangle((0.0, y - 0.015), 0.021, 0.030,
                           color=NEUTRAL_NODE, transform=ax.transAxes, lw=0)
        ax.add_patch(sw)
        swatches.append(sw)
        label = g["name"] if len(g["name"]) <= 30 else g["name"][:29] + "…"
        t = ax.text(0.038, y, label, family=SERIF, fontsize=11.5, color=INK2,
                    va="center", alpha=0.45,
                    weight="bold" if g["emergent"] else "normal")
        names.append(t)
        counts.append(ax.text(1.0, y, "0", family=MONO, fontsize=10.5, color=INK2,
                              va="center", ha="right"))
    ax.text(0.0, 0.235,
            "Grey until a community reaches three members — the pipeline's own\n"
            "threshold for calling one real. In bold: the one community with a\n"
            "datable emergence (z ≈ −3.0); the other seven are perennial modes.",
            family=SERIF, fontsize=9.5, color=INK2, va="top", style="italic",
            linespacing=1.5)
    return swatches, names, counts


# --- the animation -----------------------------------------------------------
def frame_years():
    seq = [float(YEAR0)] * HOLD_START
    steps = int((YEAR1 - YEAR0) * SUB) + 1
    seq += [YEAR0 + i / SUB for i in range(steps)]
    seq += [float(YEAR1)] * HOLD_END
    return seq


def render_video(scene, out=OUT_MP4):
    import imageio_ffmpeg
    plt.rcParams["animation.ffmpeg_path"] = imageio_ffmpeg.get_ffmpeg_exe()

    fig, ax_net, ax_leg, ax_led = build_figure(scene)
    draw_titles(fig, scene)
    swatches, name_handles, count_handles = draw_legend(ax_leg, scene)

    lc = LineCollection(scene.segs, linewidths=1.0, capstyle="round")
    lc.set_color(scene.edge_state(YEAR0 - 1))
    ax_net.add_collection(lc)

    # A 2px surface ring on every node so overlapping marks stay separable.
    nodes = ax_net.scatter(scene.xy[:, 0], scene.xy[:, 1], s=0,
                           facecolors=scene.colors, edgecolors=BG,
                           linewidths=1.1, zorder=3)
    rings = ax_net.scatter(scene.xy[:, 0], scene.xy[:, 1], s=0,
                           facecolors="none", edgecolors=scene.colors,
                           linewidths=1.4, zorder=2)

    # Figure coords, not axes coords: with equal aspect the axes box is not the
    # box matplotlib reports, so transAxes placement drifts to the middle.
    year_txt = fig.text(0.472, 0.840, str(YEAR0), family=MONO, fontsize=44,
                        color=INK, ha="right", va="top", alpha=0.88)
    n_txt = fig.text(0.472, 0.786, "0 novels", family=MONO, fontsize=12.5,
                     color=INK2, ha="right", va="top")

    led = scene.ledger
    lines, readouts = {}, {}
    series = [("splits", C_SPLIT, "splits  — one community differentiating"),
              ("merges", C_MERGE, "merges  — communities coalescing"),
              ("births", C_BIRTH, "births  — no ancestor in the prior year")]
    for i, (key, col, label) in enumerate(series):
        (ln,) = ax_led.plot([], [], color=col, lw=2.0, solid_capstyle="round")
        lines[key] = ln
        # A surface plate behind the readouts: they sit in the upper-left, where
        # the cumulative curves are still near zero, so this masks gridlines
        # only. Without it the y=30 rule strikes through "merges".
        plate = dict(boxstyle="square,pad=0.22", facecolor=BG, edgecolor="none")
        readouts[key] = ax_led.text(
            0.042, 0.95 - i * 0.135, "", transform=ax_led.transAxes,
            family=MONO, fontsize=11, color=col, va="top", ha="right",
            bbox=plate, zorder=4)
        ax_led.text(0.058, 0.95 - i * 0.135, label, transform=ax_led.transAxes,
                    family=SERIF, fontsize=11, color=INK2, va="top",
                    bbox=plate, zorder=4)
    ax_led.set_title("The mutation ledger — divisive (splits) against agglomerative (merges)",
                     family=SERIF, fontsize=13.5, color=INK, loc="left", pad=8)
    ax_led.set_ylabel("cumulative events", family=SERIF, fontsize=10.5, color=INK2)
    marker = ax_led.axvline(YEAR0, color=INK, lw=0.9, alpha=0.35)

    seq = frame_years()

    def update(fi):
        ynow = seq[fi]
        live, flash, sizes, face = scene.node_state(ynow)
        nodes.set_sizes(sizes)
        nodes.set_facecolors(face)
        ring_face = face.copy()
        ring_face[:, 3] = flash * 0.9
        rings.set_sizes(np.where(live, 40 + 620 * flash, 0.0))
        rings.set_edgecolors(ring_face)
        lc.set_color(scene.edge_state(ynow))

        year_txt.set_text(str(int(ynow)))
        active = scene.genre_active(ynow)
        n_txt.set_text(f"{int(live.sum())} novels  ·  "
                       f"{int(active.sum())}/{len(scene.genres)} communities cohered")
        for i, (c, on) in enumerate(zip(scene.counts(ynow), active)):
            count_handles[i].set_text(str(int(c)))
            swatches[i].set_color(scene.genres[i]["color"] if on else NEUTRAL_NODE)
            name_handles[i].set_color(INK if on else INK2)
            name_handles[i].set_alpha(1.0 if on else 0.45)

        m = led["years"] <= ynow
        for key in lines:
            lines[key].set_data(led["years"][m], led[key][m])
            v = int(led[key][m][-1]) if m.any() else 0
            readouts[key].set_text(f"{v:>3d}")
        marker.set_xdata([ynow, ynow])
        return ()

    anim = FuncAnimation(fig, update, frames=len(seq), interval=1000 / FPS, blit=False)
    writer = FFMpegWriter(fps=FPS, bitrate=6000, codec="libx264",
                          extra_args=["-pix_fmt", "yuv420p", "-preset", "slow"])
    print(f"rendering {len(seq)} frames -> {out}")
    anim.save(out, writer=writer,
              progress_callback=lambda i, n: (i % 50 == 0) and print(f"  {i}/{n}"))
    plt.close(fig)
    print(f"wrote {out}")


# --- the stills that go in the paper ----------------------------------------
# Fixed, not quantile-spaced. Equal-corpus-growth spacing put the first panel at
# 1813 and skipped the entire formative century - the part of the story the
# proposal is actually asking about. These are spaced by literary time instead.
PANEL_YEARS = [1750, 1800, 1850, 1880, 1905, 1928]


def render_panels(scene, out=OUT_PANELS, years=None):
    years = years or PANEL_YEARS
    fig, axes = plt.subplots(2, 3, figsize=(13, 8.6), dpi=200, facecolor=BG)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.845, bottom=0.165,
                        wspace=0.03, hspace=0.08)

    prev = YEAR0 - 1
    for ax, y in zip(axes.ravel(), years):
        style_network_axes(ax, scene, top_pad=0.30)
        lc = LineCollection(scene.segs, linewidths=0.7)
        lc.set_color(scene.edge_state(y, instant=True))
        ax.add_collection(lc)

        live = scene.year <= y
        new = live & (scene.year > prev)
        face = scene.node_colors(y)
        # Everything published to date, then the arrivals since the last panel
        # ringed on top - without this the six stills read as one picture.
        ax.scatter(scene.xy[live, 0], scene.xy[live, 1], s=17,
                   facecolors=face[live], edgecolors=BG, linewidths=0.7, zorder=3)
        ax.scatter(scene.xy[new, 0], scene.xy[new, 1], s=64, facecolors="none",
                   edgecolors=face[new], linewidths=1.1, alpha=0.85, zorder=4)

        nc = int(scene.genre_active(y).sum())
        ax.text(0.02, 0.995, str(y), transform=ax.transAxes, family=MONO,
                fontsize=17, color=INK, va="top", zorder=5)
        sub = f"{int(live.sum())} novels  ·  {nc}/{len(scene.genres)} cohered"
        if new.any():
            sub += f"\n+{int(new.sum())} since {max(prev, YEAR0)}"
        ax.text(0.02, 0.930, sub, transform=ax.transAxes, family=MONO,
                fontsize=9, color=INK2, va="top", linespacing=1.6, zorder=5)
        prev = y

    m = scene.meta
    fig.text(0.02, 0.966, "Figure: the genre network assembling, 1678–1928",
             family=SERIF, fontsize=17, color=INK, va="center")
    fig.text(0.02, 0.930,
             f"{m['nAuthors']} novels, one per author. Positions are fixed from the final "
             "k-NN layout; only publication is temporal. A novel is grey until the community it "
             "belongs to reaches\nthree members — the same threshold the pipeline uses to call a "
             "community real — so clusters are seen cohering rather than assumed. Rings mark "
             "arrivals since the previous panel.\n\"Cohered\" counts final communities whose "
             "novels have arrived; it cannot fall. Louvain re-partitioning, which can and does "
             "fall, is the ledger's business, not this figure's.",
             family=SERIF, fontsize=9.5, color=INK2, va="top", style="italic",
             linespacing=1.55)

    draw_genre_key(fig, scene)

    for ext in ("pdf", "png"):
        fig.savefig(f"{out}.{ext}", facecolor=BG)
        print(f"wrote {out}.{ext}")
    plt.close(fig)
    return years


def draw_genre_key(fig, scene, y0=0.105, x0=0.02, cols=4, dy=0.034, width=0.235):
    '''Fixed grid. A single flowed row overran the figure and clipped a genre.

    The emergent community is marked by weight, not by a ★: the serif faces have
    no star glyph, and placing one after a proportional-width name needs a
    renderer measurement that is not worth the dependency.
    '''
    for i, g in enumerate(scene.genres):
        cx = x0 + (i % cols) * width
        cy = y0 - (i // cols) * dy
        fig.patches.append(plt.Rectangle((cx, cy - 0.008), 0.010, 0.016,
                                         color=g["color"], transform=fig.transFigure,
                                         lw=0, figure=fig))
        name = g["name"] if len(g["name"]) <= 30 else g["name"][:29] + "…"
        fig.text(cx + 0.015, cy, name, family=SERIF, fontsize=9, color=INK,
                 va="center", weight="bold" if g["emergent"] else "normal")
    rows = (len(scene.genres) + cols - 1) // cols
    fig.text(x0, y0 - rows * dy - 0.004,
             "In bold: the one community with a datable emergence (z ≈ −3.0). The rest are "
             "perennial modes, spread across all 250 years.",
             family=SERIF, fontsize=9, color=INK2, va="center", style="italic")


def report(scene):
    '''What the ledger actually says, printed so it can be quoted in the paper.'''
    led = scene.ledger
    print(f"\ncorpus drawn      {scene.meta['nAuthors']} novels / "
          f"{len(scene.segs)} edges / {len(scene.genres)} communities")
    print(f"ledger corpus     {led['n_books']} novels, {YEAR0}-{YEAR1}")
    tot = {k: int(led[k][-1]) for k in ("births", "splits", "merges")}
    print(f"totals            splits {tot['splits']}  merges {tot['merges']}  "
          f"births {tot['births']}  (total {sum(tot.values())})")
    print(f"split : merge     {tot['splits'] / max(tot['merges'], 1):.2f} : 1")
    for lo, hi in ((1660, 1799), (1800, 1849), (1850, 1889), (1890, 1928)):
        m = (led["years"] >= lo) & (led["years"] <= hi)
        if not m.any():
            continue
        d = {k: int(led["raw"][k][m].sum()) for k in ("births", "splits", "merges")}
        print(f"  {lo}-{hi}      splits {d['splits']:3d}  merges {d['merges']:3d}  "
              f"births {d['births']:3d}   split:merge "
              f"{d['splits'] / max(d['merges'], 1):.2f}")
    n = led["null"]
    print(f"null model        real {n['real_total_mutations']} vs shuffled "
          f"{n['shuffled_mean']} +/- {n['shuffled_std']} (z={n['z']}) -> {n['verdict']}")


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    os.chdir(here)
    scene = Scene(extract_data(SRC), load_ledger(RESULTS))
    report(scene)
    years = render_panels(scene)
    print(f"panel years       {years}")
    if "--panels" not in sys.argv:
        render_video(scene)


if __name__ == "__main__":
    main()
