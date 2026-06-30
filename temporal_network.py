'''
    Author: Aidan Jude
    The temporal core the paper's thesis (sec. 4-5) actually requires.

    generate_network.py builds ONE static graph. The thesis is about the RATE
    at which genres mutate over time. This module supplies the missing spine:

        1. Bucket books by publication year.
        2. Grow the graph cumulatively, one year at a time.
        3. Detect communities (= genres / subgenres) in each yearly snapshot.
        4. Match each year's communities to the previous year's.
        5. Emit dated mutation events:
              BIRTH  - a community with no ancestor in year t-1
              SPLIT  - one community in t-1 maps to >1 communities in t
              MERGE  - >1 communities in t-1 map to one community in t
        6. The count of these events per year IS the genre-mutation rate.

    Run:  python temporal_network.py
          (falls back to a synthetic corpus if _data/books.json isn't present,
           so it runs end-to-end with nothing scraped yet.)
'''

import json
import os
import re
import csv
from collections import defaultdict

import numpy as np
import networkx as nx
import networkx.algorithms.community as nx_comm

from constants import shelved_books, untracked_genres
from semantic_edges import attach_embeddings, semantic_overlap

# --- tuning knobs -----------------------------------------------------------
EDGE_METHOD = os.environ.get("EDGE_METHOD", "genre")
                           # "genre"   -> genre-set overlap (the original paper)
                           # "semantic"-> cosine over description embeddings (sec. 6)
EDGE_MIN_OVERLAP = 0.5     # genre-overlap threshold for an edge (matches paper)
# Semantic edges use k-nearest-neighbors, not a global cosine threshold: over
# long English prose every novel is somewhat similar to every other, so a
# threshold yields one blob. Linking each book to its k most-similar peers
# recovers genre structure robustly regardless of the absolute cosine scale.
EDGE_KNN = 6
MATCH_MIN_JACCARD = 0.3    # how much membership overlap counts as "the same"
                           # community persisting from one year to the next


# --- 1. load + parse --------------------------------------------------------
def load_books():
    path = os.path.join(shelved_books, "books.json")
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["books"]


def parse_year(date_published):
    '''date_published is free text e.g. "September 1st 2004". Pull the year.'''
    if not date_published:
        return None
    m = re.search(r"\b(1[0-9]{3}|20[0-9]{2})\b", str(date_published))
    return int(m.group(1)) if m else None


def books_by_year(books):
    grouped = defaultdict(list)
    kept = []
    for b in books:
        year = parse_year(b.get("date_published"))
        genres = [g for g in (b.get("genres") or []) if g not in untracked_genres]
        if year is None or not genres:
            continue
        entry = {"title": b["title"], "genres": set(genres),
                 "description": b.get("description")}
        grouped[year].append(entry)
        kept.append(entry)

    # For semantic edges, embed the whole kept corpus once so the vectors are
    # comparable across every year before snapshots are built.
    if EDGE_METHOD == "semantic" and kept:
        backend = attach_embeddings(kept)
        print(f"Semantic edges via: {backend}\n")
    return grouped


# --- 2 + 3. cumulative snapshots + community detection ----------------------
def genre_overlap(a, b):
    smaller = min(len(a["genres"]), len(b["genres"]))
    if smaller == 0:
        return 0.0
    return len(a["genres"] & b["genres"]) / smaller


def edge_valid(a, b):
    '''Whether an edge should connect two books, per the selected method.'''
    if EDGE_METHOD == "semantic":
        return semantic_overlap(a, b) >= SEMANTIC_MIN_COSINE
    return genre_overlap(a, b) >= EDGE_MIN_OVERLAP


def build_snapshot(books_so_far):
    '''All books published up to and including the current year -> one graph.'''
    G = nx.Graph()
    for b in books_so_far:
        G.add_node(b["title"], genres=b["genres"])
    books = list(books_so_far)

    if EDGE_METHOD == "semantic" and EDGE_KNN and len(books) > 2:
        # k-nearest-neighbors graph from the precomputed description vectors.
        M = np.vstack([b["vec"] for b in books])
        sims = M @ M.T
        np.fill_diagonal(sims, -1.0)
        k = min(EDGE_KNN, len(books) - 1)
        for i, b in enumerate(books):
            for j in np.argpartition(-sims[i], k)[:k]:
                G.add_edge(b["title"], books[int(j)]["title"])
    else:
        for i in range(len(books)):
            for j in range(i + 1, len(books)):
                if edge_valid(books[i], books[j]):
                    G.add_edge(books[i]["title"], books[j]["title"])

    G.remove_nodes_from(list(nx.isolates(G)))
    return G


def detect_communities(G):
    '''Return a list of frozenset-of-titles, one per community.'''
    if G.number_of_nodes() == 0:
        return []
    try:
        comms = nx_comm.louvain_communities(G, seed=42)
    except Exception:
        comms = nx_comm.greedy_modularity_communities(G)
    return [frozenset(c) for c in comms if len(c) >= 3]   # ignore tiny specks


# --- 4 + 5. match communities across years, classify mutations --------------
def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def classify_mutations(prev, curr):
    '''
    prev, curr: lists of community sets (year t-1 and year t).
    Returns counts of births / splits / merges between the two snapshots.
    '''
    births, splits, merges = 0, 0, 0

    # For each current community, who in prev does it descend from?
    ancestors = []          # ancestors[i] = list of prev-indices matching curr[i]
    for c in curr:
        anc = [i for i, p in enumerate(prev) if jaccard(p, c) >= MATCH_MIN_JACCARD]
        ancestors.append(anc)
        if not anc:
            births += 1     # no lineage in t-1 -> a new genre appeared

    # A prev community that maps forward to >1 current communities = a split.
    forward = defaultdict(list)
    for ci, anc in enumerate(ancestors):
        for pi in anc:
            forward[pi].append(ci)
    splits = sum(1 for pi, children in forward.items() if len(children) > 1)

    # A current community with >1 ancestors = a merge.
    merges = sum(1 for anc in ancestors if len(anc) > 1)

    return {"births": births, "splits": splits, "merges": merges,
            "n_communities": len(curr)}


# --- driver -----------------------------------------------------------------
def mutation_timeline(grouped):
    years = sorted(grouped)
    cumulative = []
    prev_comms = []
    timeline = []

    for year in years:
        cumulative.extend(grouped[year])
        G = build_snapshot(cumulative)
        comms = detect_communities(G)
        events = classify_mutations(prev_comms, comms)
        events["year"] = year
        events["mutations"] = events["births"] + events["splits"] + events["merges"]
        timeline.append(events)
        prev_comms = comms

    return timeline


def synthetic_corpus():
    '''Tiny fake corpus so the pipeline runs with nothing scraped.
    Designed so a new "cyberpunk" cluster splits out of sci-fi over time.'''
    rng = []
    def add(title, year, genres, desc):
        rng.append({"title": title, "date_published": str(year),
                    "genres": genres, "description": desc})
    # early: undifferentiated sci-fi
    for i in range(6):
        add(f"SF-{i}", 1950 + i, ["Science Fiction", "Fiction"],
            "A starship crew explores distant planets and alien worlds in deep space.")
    # mystery cluster
    for i in range(6):
        add(f"MY-{i}", 1955 + i, ["Mystery", "Crime", "Fiction"],
            "A detective investigates a murder, hunting the killer through clues and suspects.")
    # cyberpunk splits off sci-fi in the 80s
    for i in range(6):
        add(f"CP-{i}", 1984 + i, ["Science Fiction", "Cyberpunk", "Dystopia"],
            "A hacker jacks into cyberspace against megacorporations in a neon dystopian city.")
    return rng


def main():
    books = load_books()
    source = "_data/books.json"
    if not books:
        books = synthetic_corpus()
        source = "SYNTHETIC fallback (no _data/books.json found)"

    grouped = books_by_year(books)
    timeline = mutation_timeline(grouped)

    print(f"Source: {source}")
    print(f"{len(books)} books -> {len(grouped)} publication years\n")
    print(f"{'year':>6} {'comms':>6} {'births':>7} {'splits':>7} {'merges':>7} {'mut':>5}")
    for row in timeline:
        print(f"{row['year']:>6} {row['n_communities']:>6} {row['births']:>7} "
              f"{row['splits']:>7} {row['merges']:>7} {row['mutations']:>5}")

    out = "mutation_timeline.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["year", "n_communities", "births",
                                          "splits", "merges", "mutations"])
        w.writeheader()
        for row in timeline:
            w.writerow({k: row[k] for k in w.fieldnames})
    print(f"\nWrote {out} -> this column 'mutations' is your genre-mutation rate.")


if __name__ == "__main__":
    main()
