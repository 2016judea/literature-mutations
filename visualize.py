'''
    Author: Aidan Jude
    Visualize the ROBUST finding: genres recovered from raw prose.

    Two panels in one self-contained HTML:
      (1) The genre network - every canon novel is a node, positioned by force
          layout over the k-NN similarity graph, coloured by its emergent
          community and labelled with the LLM-assigned genre name. Hover a node
          for title / author / year. This is the unsupervised genre system.
      (2) Genre spans over time - when each emergent genre's canon exemplars
          appear (birth -> latest). Shown descriptively; we do NOT claim a
          mutation RATE (the null model killed that - see README).

    Run:  python visualize.py   ->   literary_genres.html
'''

import json
import os

import networkx as nx
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import temporal_network as tn
from semantic_edges import attach_embeddings

OUT = "literary_genres.html"
PALETTE = ["#e6194B", "#3cb44b", "#4363d8", "#f58231", "#911eb4", "#42d4f4",
           "#f032e6", "#bfef45", "#fabed4", "#469990", "#dcbeff", "#9A6324"]


def main():
    tn.EDGE_METHOD = "semantic"
    tn.EDGE_KNN = 6
    books = json.load(open(os.path.join(tn.shelved_books, "books.json"),
                           encoding="utf-8"))["books"]
    for b in books:
        b["genres"] = set(b.get("genres") or [])
    attach_embeddings(books)
    res = json.load(open("results.json", encoding="utf-8"))

    # title -> (genre_name, colour, birth_year)
    title_genre, genre_color = {}, {}
    comms = sorted(res["communities"], key=lambda c: c["birth_year"])
    for i, c in enumerate(comms):
        name = c["genre_name"] or f"cluster {i}"
        genre_color[name] = PALETTE[i % len(PALETTE)]
        for t in c["titles"]:
            title_genre[t] = name

    # graph + layout
    G = tn.build_snapshot(books)
    pos = nx.spring_layout(G, k=0.32, iterations=120, seed=7)

    fig = make_subplots(
        rows=1, cols=2, column_widths=[0.64, 0.36],
        subplot_titles=("Genres recovered from prose (k-NN similarity network)",
                        "When each genre's canon exemplars appear"),
        specs=[[{"type": "scatter"}, {"type": "scatter"}]])

    # edges
    ex, ey = [], []
    for u, v in G.edges():
        ex += [pos[u][0], pos[v][0], None]
        ey += [pos[u][1], pos[v][1], None]
    fig.add_trace(go.Scatter(x=ex, y=ey, mode="lines", hoverinfo="none",
                             line=dict(width=0.3, color="rgba(160,160,160,0.4)"),
                             showlegend=False), row=1, col=1)

    # nodes grouped by genre (one legend entry each)
    meta = {b["title"]: b for b in books}
    for name, color in genre_color.items():
        nx_, ny_, txt = [], [], []
        for t in G.nodes():
            if title_genre.get(t) != name:
                continue
            nx_.append(pos[t][0]); ny_.append(pos[t][1])
            b = meta[t]
            txt.append(f"<b>{t}</b><br>{b['author']} ({b['date_published']})<br><i>{name}</i>")
        fig.add_trace(go.Scatter(x=nx_, y=ny_, mode="markers", name=name,
                                 marker=dict(size=8, color=color,
                                             line=dict(width=0.5, color="white")),
                                 text=txt, hoverinfo="text"), row=1, col=1)
    # nodes with no named genre
    ox, oy, otx = [], [], []
    for t in G.nodes():
        if t not in title_genre:
            ox.append(pos[t][0]); oy.append(pos[t][1])
            b = meta[t]; otx.append(f"<b>{t}</b><br>{b['author']} ({b['date_published']})")
    if ox:
        fig.add_trace(go.Scatter(x=ox, y=oy, mode="markers", name="(unclustered)",
                                 marker=dict(size=6, color="#cccccc"),
                                 text=otx, hoverinfo="text"), row=1, col=1)

    # panel 2: genre spans
    for i, c in enumerate(comms):
        name = c["genre_name"] or f"cluster {i}"
        color = genre_color[name]
        fig.add_trace(go.Scatter(
            x=[c["birth_year"], c["year_max"]], y=[i, i], mode="lines+markers",
            line=dict(color=color, width=7), marker=dict(size=9, color=color),
            name=name, showlegend=False,
            hovertext=f"{name}: {c['birth_year']}–{c['year_max']} "
                      f"({c['size']} books)<br>held-out label: {c['held_out_label']}",
            hoverinfo="text"), row=1, col=2)
        fig.add_annotation(x=c["birth_year"], y=i, text=f" {name}", xanchor="left",
                           yanchor="middle", showarrow=False, font=dict(size=10),
                           row=1, col=2)

    fig.update_xaxes(visible=False, row=1, col=1)
    fig.update_yaxes(visible=False, row=1, col=1)
    fig.update_xaxes(title_text="year", row=1, col=2, range=[1690, 1935])
    fig.update_yaxes(visible=False, row=1, col=2)
    fig.update_layout(
        title=dict(text="Literature Mutations — the genre system, learned from "
                        f"{res['n_books']} canon novels' prose alone",
                   x=0.5, font=dict(size=17)),
        plot_bgcolor="white", height=680, width=1280,
        legend=dict(title="emergent genre", x=0.63, y=1, font=dict(size=10)),
        margin=dict(l=10, r=10, t=70, b=40))

    fig.write_html(OUT, include_plotlyjs="cdn")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
