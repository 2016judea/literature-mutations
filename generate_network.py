'''
    Author: Aidan Jude
    Date: 05/04/21
'''

import copy
import json
import os
import statistics
import time

import ipywidgets as widgets
import networkx as nx
import plotly.express as px
import plotly.graph_objects as go

from constants import *

'''
Pseudocode:
    1. Iterate by year of publication
    2. Join books with matching shelves (prune unhelpful shelves, aka "Fiction")
    3. Determine if cluster exists

    Todo:
      - Add requirements.txt
      - Dynamically build cluster defitions/labels
      - Add genre as edge label
'''


def get_traces(G):
    node_positions = nx.spring_layout(G)
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = node_positions[edge[0]]
        x1, y1 = node_positions[edge[1]]
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines')

    node_x = []
    node_y = []
    for node in G.nodes():
        x, y = node_positions[node]
        node_x.append(x)
        node_y.append(y)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        marker=dict(
            showscale=True,
            # colorscale options
            # 'Greys' | 'YlGnBu' | 'Greens' | 'YlOrRd' | 'Bluered' | 'RdBu' |
            # 'Reds' | 'Blues' | 'Picnic' | 'Rainbow' | 'Portland' | 'Jet' |
            # 'Hot' | 'Blackbody' | 'Earth' | 'Electric' | 'Viridis' |
            colorscale='Blackbody',
            reversescale=True,
            color=[],
            size=10,
            colorbar=dict(
                thickness=15,
                title='Node Connections',
                xanchor='left',
                titleside='right'
            ),
            line_width=2))

    node_adjacencies = []
    node_text = []
    for node, adjacencies in enumerate(G.adjacency()):
        node_adjacencies.append(len(adjacencies[1]))
        node_text.append(adjacencies[0])

    node_trace.marker.color = node_adjacencies
    node_trace.text = node_text

    return node_trace, edge_trace


def determine_valid_edges(proposed_edges, genre_of_edges, genre_counter):
    average = statistics.mean(genre_counter.values())
    standard_deviation = statistics.stdev(genre_counter.values())

    lower_bound = average - standard_deviation
    upper_bound = average + standard_deviation

    valid_edges = []

    for index, edge in enumerate(proposed_edges):
        if genre_counter[genre_of_edges[index]] > lower_bound and \
                genre_counter[genre_of_edges[index]] < upper_bound:
            valid_edges.append(edge)

    return valid_edges


def populate_graphs():
    graphs = []
    G = nx.Graph()
    genre_counter = {}

    for index, dataset in enumerate(os.listdir(shelved_books)):
        books = []
        with open(os.path.join(shelved_books, dataset), "r", encoding='utf-8') as f:
            books = json.load(f)["books"]

        # add nodes for year
        for book in books:
            G.add_node(book["title"])

        proposed_edges = []
        genre_of_edges = []

        # find all edges between books of that year based on genre
        for book in books:
            for node in G.nodes:
                if node != book["title"]:
                    for other_book in books:
                        if other_book["title"] == node:
                            node_object = other_book
                            break
                    for genre in book["genres"]:
                        if genre not in untracked_genres:
                            if genre in node_object["genres"]:
                                proposed_edges.append(
                                    tuple([book["title"], node]))
                                genre_of_edges.append(genre)
                                try:
                                    genre_counter[genre] = genre_counter[genre] + 1
                                except:
                                    genre_counter[genre] = 1

        # run edges through algorithm for validity
        valid_edges = determine_valid_edges(
            proposed_edges, genre_of_edges, genre_counter)

        # populate graph with the valid edges
        for edge in valid_edges:
            G.add_edge(edge[0], edge[1])

        graphs.append(copy.deepcopy(G))

    # outside loop
    ordered_genre_dict = dict((sorted(genre_counter.items(),
                                      key=lambda k: k[1], reverse=True)))

    return graphs, ordered_genre_dict


def main():
    graphs, ordered_genre_dict = populate_graphs()

    # print ordered_genre_dict

    frames = []
    steps = []
    year = 1950
    for graph in graphs:
        node_trace, edge_trace = get_traces(graph)
        frames.append({
            "data": [edge_trace, node_trace],
            "name": year
        },)
        steps.append(
            {
                'method': 'animate',
                'label': str(year),
                'value': None,
                'args': [[year], {'frame': {'duration': 0, 'redraw': False},
                                  'mode': 'immediate', "fromcurrent": True}
                         ],
            }
        )
        year += 1

    fig = go.Figure(
        data=frames[0]["data"],
        frames=frames,
        layout=go.Layout(
            title='Literary Genre Network',
            titlefont_size=16,
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            annotations=[dict(
                text="Python code: <a href='https://plotly.com/ipython-notebooks/network-graphs/'> https://plotly.com/ipython-notebooks/network-graphs/</a>",
                showarrow=False,
                xref="paper", yref="paper",
                x=0.005, y=-0.002)],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            sliders=[{'active': 0,
                      'yanchor': 'top',
                      'xanchor': 'left',
                      'currentvalue': {
                          'font': {'size': 20},
                          'prefix': 'Year: ',
                          'visible': True,
                          'xanchor': 'right'
                      },
                      'transition': {'duration': 300, 'easing': 'cubic-in-out'},
                      'pad': {'b': 10, 't': 50},
                      'len': 0.9,
                      'x': 0.1,
                      'y': 0,
                      'steps': steps
                      }]
        )
    )

    fig.show()


if __name__ == "__main__":
    main()
