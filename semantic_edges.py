'''
    Author: Aidan Jude
    The "true AI" unlock (paper sec. 6): define edges from what a book *is
    about*, not from the genre labels we're trying to discover.

    genre_overlap() in temporal_network.py is circular — it discovers genres
    from the very shelves it's clustering. This module instead embeds each
    book's description into a vector and connects books whose descriptions are
    semantically close. Genres then emerge from the prose itself.

    Backends, tried in order (first available wins):
      1. sentence-transformers  -> real neural sentence embeddings
      2. scikit-learn TF-IDF    -> bag-of-words baseline, zero network, always runs

    Swap in any embedding API (OpenAI, Voyage, etc.) by implementing one
    function that maps list[str] -> list[vector]; nothing else changes.
'''

import numpy as np


def _embed_sentence_transformers(texts):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    return np.asarray(model.encode(texts, normalize_embeddings=True))


def _embed_tfidf(texts):
    from sklearn.feature_extraction.text import TfidfVectorizer
    # The signal is DISTINCTIVE vocabulary, not shared "novel-ese". max_df=0.4
    # drops words common to >40% of books (said, man, eyes, time...) that
    # otherwise make every novel look similar; min_df=3 drops one-off proper
    # nouns (character names) that link books for incidental reasons.
    vecs = TfidfVectorizer(stop_words="english", max_features=20000,
                           min_df=3, max_df=0.4,
                           sublinear_tf=True).fit_transform(texts)
    # L2-normalize rows so dot product == cosine similarity
    arr = vecs.toarray().astype(np.float32)
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return arr / norms


def embed(texts):
    '''list[str] -> (n, d) L2-normalized matrix. Picks the best backend present.'''
    texts = [t if t else "" for t in texts]
    try:
        return _embed_sentence_transformers(texts), "sentence-transformers"
    except Exception:
        return _embed_tfidf(texts), "tfidf"


def attach_embeddings(books):
    '''
    books: list of dicts each with a "description" (and "title").
    Mutates each dict, adding a normalized "vec". Returns the backend name.
    Embeds the whole corpus once so vectors are comparable across all years.
    '''
    texts = [b.get("description") or b.get("title", "") for b in books]
    matrix, backend = embed(texts)
    for b, v in zip(books, matrix):
        b["vec"] = v
    return backend


def semantic_overlap(a, b):
    '''Cosine similarity between two books' description vectors (in [0, 1]).'''
    va, vb = a.get("vec"), b.get("vec")
    if va is None or vb is None:
        return 0.0
    return float(np.dot(va, vb))
