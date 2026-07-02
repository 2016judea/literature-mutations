'''
    Author: Aidan Jude
    Visualize the CONTROLLED finding (see controls.py): after removing style
    drift and author voice, which genres are genuine temporal EMERGENCES vs
    perennial modes.

    Two panels in one self-contained HTML:
      (1) The de-trended, one-book-per-author genre network - nodes coloured by
          community, positioned by force layout. Hover for title/author/year.
      (2) Temporal-concentration chart - each genre plotted by its birth window
          and its concentration z-score. Genres with z <= -2 (concentrated =
          genuinely emergent, e.g. detective fiction) are highlighted; the rest
          are perennial modes spread across the whole period.

    Run:  python visualize.py   ->   literary_genres.html
'''

import json
import os

import numpy as np
import networkx as nx
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.feature_extraction.text import TfidfVectorizer

from constants import shelved_books

OUT = "literary_genres.html"
PALETTE = ["#e6194B", "#3cb44b", "#4363d8", "#f58231", "#911eb4", "#42d4f4",
           "#f032e6", "#469990", "#9A6324", "#808000", "#000075", "#a9a9a9"]
K = 6


def main():
    books = json.load(open(os.path.join(shelved_books, "books.json"),
                           encoding="utf-8"))["books"]
    authors = [b["author"] for b in books]
    years = np.array([int(b["date_published"]) for b in books], float)

    V = TfidfVectorizer(stop_words="english", max_features=20000,
                        min_df=3, max_df=0.4, sublinear_tf=True)
    X = V.fit_transform([b["description"] for b in books]).toarray().astype(np.float32)
    terms = np.array(V.get_feature_names_out())

    # one book per author (earliest) + style-drift de-trend
    seen, keep = set(), []
    for i in np.argsort(years):
        if authors[i] not in seen:
            seen.add(authors[i]); keep.append(i)
    keep = np.array(sorted(keep))
    Xk, yk = X[keep], years[keep]
    yc = yk - yk.mean()
    Xkd = Xk - np.outer(yc, (Xk * yc[:, None]).sum(0) / (yc @ yc))
    M = Xkd / np.clip(np.linalg.norm(Xkd, axis=1, keepdims=True), 1e-9, None)

    S = M @ M.T
    np.fill_diagonal(S, -1.0)
    G = nx.Graph()
    G.add_nodes_from(range(len(keep)))
    for i in range(len(keep)):
        for j in np.argpartition(-S[i], K)[:K]:
            G.add_edge(i, int(j))
    import networkx.algorithms.community as nxc
    comms = [c for c in nxc.louvain_communities(G, seed=42) if len(c) >= 5]

    rng = np.random.default_rng(0)
    def zconc(idx):
        d = [yk[rng.choice(len(yk), len(idx), replace=False)].std() for _ in range(2000)]
        return (yk[idx].std() - np.mean(d)) / np.std(d)

    import collections
    NOISE = ("Best Books", "Category", "--", "Listings", "Banned Books",
             "Anne Haight", "Harvard Classics", "Movie Books")
    def held_out_name(idx):
        labs = collections.Counter(
            g for i in idx for g in (books[keep[i]].get("genres") or [])
            if not any(n in g for n in NOISE))
        return labs.most_common(1)[0][0] if labs else None

    info = {}
    for ci, c in enumerate(comms):
        idx = list(c)
        top = list(terms[np.argsort(-M[idx].mean(0))[:5]])
        name = held_out_name(idx) or " ".join(top[:3])
        info[ci] = {"idx": idx, "name": name, "terms": top, "z": zconc(idx),
                    "y0": int(yk[idx].min()), "y1": int(yk[idx].max()),
                    "color": PALETTE[ci % len(PALETTE)]}
    node_comm = {i: ci for ci, c in enumerate(comms) for i in c}

    pos = nx.spring_layout(G, k=0.35, iterations=120, seed=7)
    fig = make_subplots(
        rows=1, cols=2, column_widths=[0.6, 0.4],
        subplot_titles=("Genre network (style- & author-controlled)",
                        "Temporal concentration — is a genre <i>born</i> or perennial?"))

    ex, ey = [], []
    for u, v in G.edges():
        ex += [pos[u][0], pos[v][0], None]; ey += [pos[u][1], pos[v][1], None]
    fig.add_trace(go.Scatter(x=ex, y=ey, mode="lines", hoverinfo="none",
                  line=dict(width=0.3, color="rgba(150,150,150,0.4)"),
                  showlegend=False), row=1, col=1)

    for ci, meta in info.items():
        emergent = meta["z"] <= -2.0
        nx_, ny_, txt = [], [], []
        for i in meta["idx"]:
            nx_.append(pos[i][0]); ny_.append(pos[i][1])
            b = books[keep[i]]
            txt.append(f"<b>{b['title']}</b><br>{b['author']} ({int(yk[i])})")
        label = f"{meta['name']}  (z={meta['z']:+.1f})" + (" ★" if emergent else "")
        fig.add_trace(go.Scatter(x=nx_, y=ny_, mode="markers", name=label,
                      marker=dict(size=10 if emergent else 7, color=meta["color"],
                                  line=dict(width=1.5 if emergent else 0.4,
                                            color="black" if emergent else "white")),
                      text=txt, hoverinfo="text"), row=1, col=1)

    # panel 2: z vs birth window
    order = sorted(info.values(), key=lambda m: m["z"])
    for rank, m in enumerate(order):
        emergent = m["z"] <= -2.0
        fig.add_trace(go.Scatter(
            x=[m["y0"], m["y1"]], y=[rank, rank], mode="lines+markers",
            line=dict(color=m["color"], width=9 if emergent else 5),
            marker=dict(size=10, color=m["color"]), showlegend=False,
            hovertext=f"{m['name']}: {m['y0']}–{m['y1']}, z={m['z']:+.1f}",
            hoverinfo="text"), row=1, col=2)
        tag = f" {m['name']}  z={m['z']:+.1f}" + ("  ★ EMERGENT" if emergent else "")
        fig.add_annotation(x=m["y1"], y=rank, text=tag, xanchor="left",
                           yanchor="middle", showarrow=False,
                           font=dict(size=10, color="black" if emergent else "#666"),
                           row=1, col=2)

    fig.update_xaxes(visible=False, row=1, col=1)
    fig.update_yaxes(visible=False, row=1, col=1)
    fig.update_xaxes(title_text="year", range=[1660, 1990], row=1, col=2)
    fig.update_yaxes(visible=False, row=1, col=2)
    fig.update_layout(
        title=dict(text="Literature Mutations — genres from prose, after controlling "
                        "for style drift & author voice", x=0.5, font=dict(size=16)),
        plot_bgcolor="white", height=720, autosize=True,
        legend=dict(title="community (★ = temporally emergent)", font=dict(size=9)),
        margin=dict(l=10, r=10, t=70, b=40))
    fig.write_html(OUT, include_plotlyjs="cdn", default_width="100%",
                   config={"responsive": True})
    print(f"Wrote {OUT}  |  emergent genres: "
          f"{[m['name'] for m in order if m['z'] <= -2.0]}")


if __name__ == "__main__":
    main()
