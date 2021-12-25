'''
    Author: Aidan Jude
    Date: 05/04/21
'''

import copy
import json
import os
import statistics
import time
from collections import defaultdict

import ipywidgets as widgets
import networkx as nx
import plotly.express as px
import plotly.graph_objects as go

from constants import *

'''
Pseudocode:
    1. Iterate by year of publication
    2. Join books with similar qualities
    3. Determine if clusters exist

    Todo:
      - Add requirements.txt
      - Cluster analysis:
        - Find way to identify clusters that form in the graph
            - Highlight them? 
      - Edge validity algorithms:
        - Try different genre weighting algorithms
        - Use NLP model for weighting edge validity
            - Edge validity in graph could be weighted between genre overlap and NLP model analysis of description/reviews text corpus     
'''


def get_traces(G):
    node_positions = nx.spring_layout(G, k=.3, iterations=100)
    #   k:              controls the distance between the nodes and varies between 0 and 1
    #   iterations:     is the number of times simulated annealing is run
    #       
    #   default k=0.1 and iterations=50
    
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


def evaluate_every_genre_as_edge(G, books):
    proposed_edges = []
    genre_of_edges = []
    genre_counter = {}

    # find all edges between books of that year based on genre
    for book in books:
        for node in G.nodes:
            if node != book["title"]:# evaluate all the OTHER books in corpus
                for other_book in books: # find the JSON object for the other book we want to evaluate
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
                            except KeyError:
                                genre_counter[genre] = 1
    
    ordered_genre_dict = dict((sorted(genre_counter.items(),
                                    key=lambda k: k[1], reverse=True)))
    
    # print(ordered_genre_dict)
    
    return proposed_edges, genre_of_edges, genre_counter


def determine_overlap_of_genres_between_nodes(source, dest):
    common_genres = list(set(source['genres']).intersection(set(dest['genres'])))
    min_genres_between_two = min(len(source['genres']), len(dest['genres']))
    
    if min_genres_between_two == 0:
        overlap = 0
    else:
        overlap = len(common_genres) / min_genres_between_two
    
    # print(source['title'] + " <---------> " + dest['title'] + ", Weight: " + str(overlap))
    return overlap
    

'''
    Methods:
        evaluate_every_genre_as_edge: 
            Iterate through every genre that a given node (book) has listed, determine if the edge should exist in graph
                params = { 'statistic': "p10" | "within_single_std_median" }
        
        compare_all_genres_between_nodes:
            Assert the commonality between the two nodes, based on the overlap of their genre
                params = { 'required_weight': number (between 0 and 1) }
'''
def determine_valid_edges(G, books, method, params):
    valid_edges = []
    
    if method == "compare_all_genres_between_nodes":
        for book in books:
            for node in G.nodes:
                if node != book["title"]: # evaluate all the OTHER books in corpus
                    for other_book in books: # find the JSON object for the other book we want to evaluate
                        if other_book["title"] == node:
                            other_node = other_book 
                            break
                    if other_node is not None:
                        overlap = determine_overlap_of_genres_between_nodes(book, other_node)
                        if overlap >= params['required_weight']:
                            valid_edges.append(tuple([book["title"], node]))
        return valid_edges
                                
    elif method == "evaluate_every_genre_as_edge":
        proposed_edges, genre_of_edges, genre_counter= evaluate_every_genre_as_edge(G, books)
        
        if params['statistic'] == "within_single_std_median":
            average = statistics.median(genre_counter.values())
            standard_deviation = statistics.stdev(genre_counter.values())

            lower_bound = average - standard_deviation
            upper_bound = average + standard_deviation

            for index, edge in enumerate(proposed_edges):
                occurrences_of_genre_in_corpus = genre_counter[genre_of_edges[index]]
                if occurrences_of_genre_in_corpus > lower_bound and \
                        occurrences_of_genre_in_corpus < upper_bound:
                    valid_edges.append(edge)
                    
        elif params['statistic']  == "p10":
            upper_bound = sum(genre_counter.values()) * .10
            existing_connections = defaultdict(list)

            for index, edge in enumerate(proposed_edges):
                occurrences_of_genre_in_corpus = genre_counter[genre_of_edges[index]]
                if occurrences_of_genre_in_corpus < upper_bound:
                    source = edge[0]
                    dest = edge[1]
                    try:
                        if dest not in existing_connections[source]:
                            existing_connections[source].append(dest)
                            valid_edges.append(edge)
                    except KeyError:
                        existing_connections[source].append(dest)
                        valid_edges.append(edge)

    return valid_edges


def populate_graphs():
    graphs = []
    G = nx.Graph()

    books = []
    with open(os.path.join(shelved_books, "books.json"), "r", encoding='utf-8') as f:
        books = json.load(f)["books"]

    # add nodes for year
    for book in books:
        G.add_node(book["title"])

    # run edges through algorithm for validity
    valid_edges = determine_valid_edges(
                    G,
                    books,
                    "compare_all_genres_between_nodes", 
                    {'required_weight': .9 }
                )

    # populate graph with the valid edges
    for edge in valid_edges:
        G.add_edge(edge[0], edge[1])
        
    # remove isolated nodes from graph
    G.remove_nodes_from(list(nx.isolates(G)))

    graphs.append(copy.deepcopy(G))

    return graphs


def main():
    graphs = populate_graphs()

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
