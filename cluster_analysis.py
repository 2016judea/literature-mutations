'''
    Author: Aidan Jude
    Reconstructed: the original module was imported by generate_network.py
    (get_nodes_with_low_clustering_coefficients) but never committed.

    Local clustering coefficient of a node = how close its neighbours are to
    being a complete clique. Nodes that sit on the sparse fringe of the graph
    (low coefficient) are noise for genre-cluster detection, so we strip them
    out before drawing / analysing the network.
'''

import networkx as nx


def get_nodes_with_low_clustering_coefficients(G, threshold=0.1):
    '''
    Return the nodes whose local clustering coefficient is at or below
    `threshold`. These are weakly-embedded nodes that don't belong to any
    dense genre region. Returned as a list so it can be fed straight into
    G.remove_nodes_from(...).
    '''
    coefficients = nx.clustering(G)
    return [node for node, coeff in coefficients.items() if coeff <= threshold]
