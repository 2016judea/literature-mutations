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

    Outputs:
      genre_growth.mp4                  - 2560x1440, for the desktop web edition
      genre_growth_portrait.mp4         - 1080x1440, for phones. NOT the same
                                          film letterboxed but re-laid-out, with
                                          type sized for a phone.

    Neither cut carries a title, a subtitle or a provenance footer. The page that
    hosts them states all three in real selectable text immediately above and
    below the frame, so baking them in made the page introduce itself three times
    and pushed the graph below the fold on a phone. What is left in frame is only
    what text cannot do: a thing happening over time.
      genre_growth_poster.png           - last-frame poster for both players
        _portrait.png
      figure_genre_growth_panels.pdf    - the same growth as six stills, for
        .png                              any print/PDF rendering of the paper

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

# --- theme: the warm paper of the research page, both of its modes -----------
# research/index.html switches on prefers-color-scheme with no toggle, so a
# light-only film glares on every dark-mode visitor. The dark ledger colours are
# NOT a flip of the light ones - they are re-stepped and re-validated against the
# dark surface with the dataviz skill's validate_palette.js (all six checks pass
# on both). Do not hand-tune either set without re-running that script.
THEMES = {
    "light": dict(bg="#f7f3ec", bg2="#efe9dd", ink="#1c1814", ink2="#544e44",
                  rule=(0.235, 0.196, 0.157, 0.16),
                  neutral_node=[0.62, 0.59, 0.55, 1.0],
                  neutral_edge=[0.235, 0.196, 0.157, 1.0],
                  split="#c2412a", merge="#0f6fb3", birth="#94690a"),
    "dark": dict(bg="#15120f", bg2="#1d1916", ink="#e9e3d5", ink2="#b3aa9a",
                 rule=(0.90, 0.86, 0.78, 0.16),
                 neutral_node=[0.49, 0.47, 0.43, 1.0],
                 neutral_edge=[0.90, 0.86, 0.78, 1.0],
                 split="#d4553a", merge="#2f86cc", birth="#a87d18"),
}

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


def apply_theme(name):
    '''Swap the module palette. Rendering is sequential, so globals are safe.'''
    global BG, BG2, INK, INK2, RULE, NEUTRAL_NODE, NEUTRAL_EDGE
    global C_SPLIT, C_MERGE, C_BIRTH
    t = THEMES[name]
    BG, BG2, INK, INK2, RULE = t["bg"], t["bg2"], t["ink"], t["ink2"], t["rule"]
    NEUTRAL_NODE, NEUTRAL_EDGE = t["neutral_node"], t["neutral_edge"]
    C_SPLIT, C_MERGE, C_BIRTH = t["split"], t["merge"], t["birth"]

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
HOLD_START = 10    # ~0.4s. Was 36 (~1.5s) to give the frame's title time to be
                   # read - there is no longer a title, and with the poster
                   # showing the finished graph, a long empty hold made autoplay
                   # snap from full to blank and read as a failed load.
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

    def node_state(self, ynow, L):
        age = (ynow - self.year) * SUB
        live = age >= 0
        flash = np.where(live, np.exp(-np.clip(age, 0, None) / FLASH_TAU), 0.0)
        sizes = np.where(live, L["node_base"] + L["flash_size"] * flash, 0.0)
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


def style_ledger_axes(ax, ledger, L):
    ax.set_facecolor(BG)
    ax.set_xlim(YEAR0, YEAR1)
    top = max(ledger["splits"][-1], ledger["merges"][-1], ledger["births"][-1])
    # Landscape seats the readouts inside the axes and needs headroom above the
    # curves; portrait puts them in a row above it, so the plot can fill its box.
    ax.set_ylim(0, top * (1.18 if L["key"] == "landscape" else 1.06))
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("bottom", "left"):
        ax.spines[s].set_color(RULE)
        ax.spines[s].set_linewidth(0.8)
    ax.tick_params(colors=INK2, labelsize=L["led_tick_fs"], length=3, width=0.8)
    if L["key"] == "portrait":
        ax.set_xticks([1700, 1800, 1900])
        ax.set_yticks([0, 15, 30])
    for lbl in ax.get_xticklabels() + ax.get_yticklabels():
        lbl.set_fontfamily(MONO)
    ax.grid(axis="y", color=RULE, linewidth=0.6, alpha=0.7)
    ax.set_axisbelow(True)


# --- the two cuts ------------------------------------------------------------
# One scene, two framings. The phone is not a smaller desktop: at 390px wide the
# landscape cut's 10.5pt provenance note renders around 2px tall, so the portrait
# cut is re-laid-out rather than scaled, and the note it cannot carry is moved to
# the page's <figcaption> where it becomes real, selectable, resizable text.
LANDSCAPE = dict(
    key="landscape", out="genre_growth.mp4",
    figsize=(16, 9), dpi=160,                       # 2560 x 1440
    chrome=False,
    net=[0.018, 0.050, 0.552, 0.900], net_top_pad=0.14,
    leg=[0.622, 0.445, 0.360, 0.400], leg_cols=1,
    led=[0.640, 0.105, 0.340, 0.200],
    led_title_y=0.415, led_row_y=[0.385, 0.360, 0.335],
    title_y=0.945, title_fs=26, sub_y=0.900, sub_fs=12.5, text_x=0.025,
    year_xy=(0.982, 0.968), year_fs=52, count_y=0.902, count_fs=13,
    footer=False, leg_note=True,
    leg_name_fs=11.5, leg_count_fs=10.5, leg_head_fs=9.5, note_fs=9.5,
    led_title_fs=13.5, led_label_fs=11, led_tick_fs=9, led_ylabel_fs=10.5,
    edge_lw=1.0, node_lw=1.1, node_base=26, flash_size=190, ring_size=620,
    crf="18",
)

# The ledger is deliberately absent here. Fitting it under the network at a size
# a phone can actually read left every element cramped, and the first render came
# out with the title over the year and the legend over the ledger. It is a second
# idea on a screen that has room for one: the network IS the film on a phone. The
# ledger stays in the landscape cut, and its numbers are restated as real text in
# the page's <figcaption>, where they are legible at any size.
PORTRAIT = dict(
    key="portrait", out="genre_growth_portrait.mp4",
    figsize=(9, 12), dpi=120,                       # 1080 x 1440
    chrome=False,
    net=[0.030, 0.190, 0.940, 0.647], net_top_pad=0.12,
    leg=[0.055, 0.022, 0.890, 0.135], leg_cols=2,
    led=None, led_title_y=None, led_row_y=None,
    title_y=0.980, title_fs=30, sub_y=0.880, sub_fs=16, text_x=0.040,
    year_xy=(0.955, 0.962), year_fs=62, count_y=0.892, count_fs=19,
    footer=False, leg_note=False,
    leg_name_fs=17, leg_count_fs=17, leg_head_fs=14, note_fs=14,
    led_title_fs=18, led_label_fs=16, led_tick_fs=14, led_ylabel_fs=None,
    edge_lw=1.4, node_lw=1.5, node_base=44, flash_size=330, ring_size=1000,
    crf="20",
)


def build_figure(scene, L):
    '''Explicit axes rather than a gridspec.

    The layout is a network with equal aspect, and the layout's data is 1.09:1 -
    near square. Dropped into a wide gridspec cell, equal aspect shrank the graph
    to the cell's HEIGHT and left half the frame empty, with the year label
    stranded in the middle. So the network gets a near-square box sized to the
    data, and everything else lives in the space that frees up.
    '''
    fig = plt.figure(figsize=L["figsize"], dpi=L["dpi"], facecolor=BG)
    ax_net = fig.add_axes(L["net"])
    style_network_axes(ax_net, scene, top_pad=L["net_top_pad"])
    ax_leg = fig.add_axes(L["leg"])
    ax_leg.axis("off"); ax_leg.set_facecolor(BG)
    ax_led = None
    if L["led"]:
        ax_led = fig.add_axes(L["led"])
        style_ledger_axes(ax_led, scene.ledger, L)
    return fig, ax_net, ax_leg, ax_led


def draw_titles(fig, scene, L):
    """The film's own title, subtitle and provenance footer.

    Off by default. The page that hosts this film already states its title, its
    corpus and its null model in real selectable text, immediately above and
    below the frame - so baking them into pixels made the page introduce itself
    three times over, and on a phone pushed the graph itself below the fold.
    They are not deleted, they are relocated to the surface that does them
    better. What is left in the frame is only what text cannot do: a thing
    happening over time.
    """
    if not L["chrome"]:
        return
    m = scene.meta
    x = L["text_x"]
    title = ("How the genre system of English fiction assembled itself"
             if L["key"] == "landscape" else
             "How the genre system of\nEnglish fiction assembled itself")
    fig.text(x, L["title_y"], title, family=SERIF, fontsize=L["title_fs"],
             color=INK, va="top", linespacing=1.25)
    sub = (f"{m['nAuthors']} novels, one per author  ·  positions fixed from the final "
           "k-NN layout, only publication is temporal  ·  a novel stays grey until its "
           "community reaches three members"
           if L["key"] == "landscape" else
           f"{m['nAuthors']} novels, one per author. Positions are fixed;\n"
           "only publication is temporal.")
    fig.text(x, L["sub_y"], sub, family=SERIF, fontsize=L["sub_fs"], color=INK2,
             va="top", style="italic", linespacing=1.45)

    if not L["footer"]:
        return
    n = scene.ledger["null"]
    fig.text(x, 0.062,
             f"Ledger from the full {scene.ledger['n_books']}-novel run (results.json); "
             f"network is the {m['nAuthors']}-novel author-controlled layout "
             "(genre_network.html). Edges are the final k-NN graph induced on novels\n"
             f"published to date. Null model: {n['real_total_mutations']} real events "
             f"against {n['shuffled_mean']:.0f} ± {n['shuffled_std']:.0f} under shuffled "
             f"publication years (z = {n['z']}) — so the ledger shows the shape of genre "
             "formation, never a rate.",
             family=SERIF, fontsize=10.5, color=INK2, va="center", linespacing=1.6)


def draw_legend(ax, scene, L):
    '''Genre rail. Swatch, name and running count per community.

    Returns the handles the animation mutates each frame: a community stays grey
    and its name dim until it reaches three members, at which point it takes its
    colour. So the rail is a readout of how many genres exist *yet*, not a static
    key to the finished answer.
    '''
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    swatches, names, counts = [], [], []
    cols = L["leg_cols"]
    rows = (len(scene.genres) + cols - 1) // cols
    maxlen = 30 if cols == 1 else 25

    if L["key"] == "landscape":
        ax.text(0.0, 0.975, "C O M M U N I T I E S", family=MONO,
                fontsize=L["leg_head_fs"], color=INK2)
        # Compressed into the top 62%: at 80% the footnote below overflowed the
        # axes and printed across the ledger's title and y-axis.
        ys = [0.905 - i * (0.62 / rows) for i in range(rows)]
        xs = [0.0]
        col_w, sw_w, sw_h = 1.0, 0.021, 0.030
    else:
        ys = [0.88 - i * 0.26 for i in range(rows)]
        xs = [0.0, 0.52]
        col_w, sw_w, sw_h = 0.45, 0.016, 0.10

    for i, g in enumerate(scene.genres):
        cx = xs[i // rows] if cols > 1 else xs[0]
        y = ys[i % rows]
        sw = plt.Rectangle((cx, y - sw_h / 2), sw_w, sw_h, color=NEUTRAL_NODE,
                           transform=ax.transAxes, lw=0)
        ax.add_patch(sw)
        swatches.append(sw)
        label = g["name"] if len(g["name"]) <= maxlen else g["name"][:maxlen - 1] + "…"
        names.append(ax.text(cx + sw_w * 1.8, y, label, family=SERIF,
                             fontsize=L["leg_name_fs"], color=INK2, va="center",
                             alpha=0.45,
                             weight="bold" if g["emergent"] else "normal"))
        counts.append(ax.text(cx + col_w, y, "0", family=MONO,
                              fontsize=L["leg_count_fs"], color=INK2,
                              va="center", ha="right"))

    if L["leg_note"]:
        # 0.30, not 0.235: this note is three lines and hangs below the axes,
        # where at 0.235 its last line printed through the ledger's title.
        ax.text(0.0, 0.30,
                "Grey until a community reaches three members — the pipeline's own\n"
                "threshold for calling one real. In bold: the one community with a\n"
                "datable emergence (z ≈ −3.0); the other seven are perennial modes.",
                family=SERIF, fontsize=L["note_fs"], color=INK2, va="top",
                style="italic", linespacing=1.5)
    return swatches, names, counts


# --- the animation -----------------------------------------------------------
def frame_years():
    seq = [float(YEAR0)] * HOLD_START
    steps = int((YEAR1 - YEAR0) * SUB) + 1
    seq += [YEAR0 + i / SUB for i in range(steps)]
    seq += [float(YEAR1)] * HOLD_END
    return seq


def render_video(scene, L, theme="light"):
    import imageio_ffmpeg
    plt.rcParams["animation.ffmpeg_path"] = imageio_ffmpeg.get_ffmpeg_exe()
    apply_theme(theme)
    out = L["out"] if theme == "light" else L["out"].replace(".mp4", "_dark.mp4")
    portrait = L["key"] == "portrait"

    fig, ax_net, ax_leg, ax_led = build_figure(scene, L)
    draw_titles(fig, scene, L)
    swatches, name_handles, count_handles = draw_legend(ax_leg, scene, L)

    lc = LineCollection(scene.segs, linewidths=L["edge_lw"], capstyle="round")
    lc.set_color(scene.edge_state(YEAR0 - 1))
    ax_net.add_collection(lc)

    # A surface ring on every node so overlapping marks stay separable.
    nodes = ax_net.scatter(scene.xy[:, 0], scene.xy[:, 1], s=0,
                           facecolors=scene.colors, edgecolors=BG,
                           linewidths=L["node_lw"], zorder=3)
    rings = ax_net.scatter(scene.xy[:, 0], scene.xy[:, 1], s=0,
                           facecolors="none", edgecolors=scene.colors,
                           linewidths=L["node_lw"] * 1.3, zorder=2)

    # Figure coords, not axes coords: with equal aspect the axes box is not the
    # box matplotlib reports, so transAxes placement drifts to the middle.
    yx, yy = L["year_xy"]
    year_txt = fig.text(yx, yy, str(YEAR0), family=MONO, fontsize=L["year_fs"],
                        color=INK, ha="right", va="top", alpha=0.88)
    n_txt = fig.text(yx, L["count_y"], "0 novels", family=MONO,
                     fontsize=L["count_fs"], color=INK2, ha="right", va="top")

    led = scene.ledger
    lines, readouts, marker = {}, {}, None
    if ax_led is not None:
        series = [("splits", C_SPLIT, "splits  — one community differentiating"),
                  ("merges", C_MERGE, "merges  — communities coalescing"),
                  ("births", C_BIRTH, "births  — no ancestor in the prior year")]
        # The readouts live ABOVE the axes, not inside it. Inside, they sat on
        # top of the gridlines and needed a surface plate to stay legible - and
        # the plate then masked the left end of the y=20 and y=30 rules, so the
        # grid read as broken. Nothing is drawn over the plot area now, and the
        # gridlines run their full width.
        x0 = L["led"][0]
        for i, (key, col, label) in enumerate(series):
            (ln,) = ax_led.plot([], [], color=col, lw=2.0, solid_capstyle="round")
            lines[key] = ln
            readouts[key] = fig.text(x0 + 0.026, L["led_row_y"][i], "", family=MONO,
                                     fontsize=L["led_label_fs"], color=col,
                                     va="bottom", ha="right")
            fig.text(x0 + 0.034, L["led_row_y"][i], label, family=SERIF,
                     fontsize=L["led_label_fs"], color=INK2, va="bottom")
        fig.text(x0, L["led_title_y"], "The mutation ledger",
                 family=SERIF, fontsize=L["led_title_fs"], color=INK, va="bottom")
        if L["led_ylabel_fs"]:
            ax_led.set_ylabel("cumulative events", family=SERIF,
                              fontsize=L["led_ylabel_fs"], color=INK2)
        marker = ax_led.axvline(YEAR0, color=INK, lw=0.9, alpha=0.35)

    seq = frame_years()

    def update(fi):
        ynow = seq[fi]
        live, flash, sizes, face = scene.node_state(ynow, L)
        nodes.set_sizes(sizes)
        nodes.set_facecolors(face)
        ring_face = face.copy()
        ring_face[:, 3] = flash * 0.9
        rings.set_sizes(np.where(live, L["node_base"] * 1.6
                                 + L["ring_size"] * flash, 0.0))
        rings.set_edgecolors(ring_face)
        lc.set_color(scene.edge_state(ynow))

        year_txt.set_text(str(int(ynow)))
        active = scene.genre_active(ynow)
        cohered = f"{int(active.sum())}/{len(scene.genres)}"
        # The opening hold sits on a one-novel corpus for ~1.5s, so "1 novels"
        # is the first thing every viewer reads.
        n = int(live.sum())
        novels = f"{n} novel" + ("" if n == 1 else "s")
        n_txt.set_text(f"{novels}  ·  {cohered} cohered" if portrait
                       else f"{novels}  ·  {cohered} communities cohered")
        for i, (c, on) in enumerate(zip(scene.counts(ynow), active)):
            count_handles[i].set_text(str(int(c)))
            swatches[i].set_color(scene.genres[i]["color"] if on else NEUTRAL_NODE)
            name_handles[i].set_color(INK if on else INK2)
            name_handles[i].set_alpha(1.0 if on else 0.45)

        if marker is not None:
            m = led["years"] <= ynow
            for key in lines:
                lines[key].set_data(led["years"][m], led[key][m])
                v = int(led[key][m][-1]) if m.any() else 0
                readouts[key].set_text(f"{v:>3d}")
            marker.set_xdata([ynow, ynow])
        return ()

    anim = FuncAnimation(fig, update, frames=len(seq), interval=1000 / FPS, blit=False)
    # CRF rather than a target bitrate: this is flat colour and hairline strokes,
    # where a fixed bitrate spends too much on the still frames and mosquitoes
    # the edges during the busy years. +faststart puts the moov atom first so a
    # browser can start playing before the whole file lands.
    writer = FFMpegWriter(fps=FPS, bitrate=-1, codec="libx264",
                          extra_args=["-pix_fmt", "yuv420p", "-preset", "slow",
                                      "-crf", L["crf"], "-movflags", "+faststart"])
    print(f"rendering {len(seq)} frames -> {out}")
    anim.save(out, writer=writer,
              progress_callback=lambda i, n: (i % 100 == 0) and print(f"  {i}/{n}"))

    # Poster: the finished graph, so the player shows the answer before playback.
    update(len(seq) - 1)
    poster = out.replace(".mp4", "_poster.jpg")
    fig.savefig(poster, facecolor=BG, dpi=L["dpi"], pil_kwargs={"quality": 88})
    plt.close(fig)
    print(f"wrote {out} + {poster}")


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
    if "--panels" in sys.argv:
        return
    cuts = [PORTRAIT] if "--portrait" in sys.argv else \
           [LANDSCAPE] if "--landscape" in sys.argv else [LANDSCAPE, PORTRAIT]
    themes = ["light"] if "--light" in sys.argv else \
             ["dark"] if "--dark" in sys.argv else ["light", "dark"]
    for L in cuts:
        for theme in themes:
            render_video(scene, L, theme)
    apply_theme("light")


if __name__ == "__main__":
    main()
