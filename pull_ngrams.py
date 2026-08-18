'''
    Author: Aidan Jude
    S2, step 1: pull the reception clock from Google Books Ngrams.

    docs/RESEARCH-PROGRAM.md SS "S2 - The reception clock" asks one question:
    date each genre by when its *name* entered the language, using a source with
    zero dependence on the text pipeline, then check whether the two clocks
    agree. This script only fetches and caches; analyze_reception_clock.py does
    the dating. Splitting them means the dating method can be re-argued without
    re-hitting Google.

    Two decisions worth defending, both taken 2026-08-18:

    1. We request case_insensitive=true and keep ONLY the "<term> (All)" series
       Google returns. "Bildungsroman", "bildungsroman" and "BILDUNGSROMAN" are
       one act of naming, and splitting them understates a term by ~10-50%.

    2. We request smoothing=0 (raw) and smooth in analyze_reception_clock.py.
       The brief's verified example call used smoothing=3, but a moving average
       applied server-side is an undocumented transform sitting between the
       source and the finding. Ours is in the repo and auditable.

    Env:  none (public endpoint, no key required)
    Run:  python pull_ngrams.py            # fetches only what is not cached
          python pull_ngrams.py --refetch   # ignores the cache
    Out:  _data/ngrams_raw.json
'''

import json
import os
import socket
import sys
import time
import urllib.parse
import urllib.request

socket.setdefaulttimeout(60)

from constants import shelved_books

OUT_FILE = os.path.join(shelved_books, "ngrams_raw.json")

NGRAM_API = "https://books.google.com/ngrams/json"
CORPUS = "en-2019"
YEAR_START, YEAR_END = 1700, 2019

# Google blocks the default urllib agent outright. A browser string is required
# (docs/RESEARCH-PROGRAM.md S2, verified 2026-08-15 and again 2026-08-18).
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# ---------------------------------------------------------------------------
# The vocabulary, paired to the eight controlled communities.
#
# PAIRED BY DISTINCTIVE VOCABULARY, NOT BY held_out_label. This is the one
# substantive judgment in S2 and it is deliberate. controls_results.json's
# held_out_label is the nearest-matching Gutenberg subject label, and for three
# of eight communities it disagrees with what the community's own top_terms say
# the community is:
#
#   community #2  cattle/mountain/wagon/camp        label "Best Books Ever Listings"
#   community #3  catholics/archbishop/cardinal     label "Fantasy fiction"
#   community #6  castle/sensations/veil/trembled   label "Science fiction"
#
# #6 is the load-bearing one. Its vocabulary is Gothic, and README.md:66 already
# calls that community gothic in prose ("gothic, adventure, domestic, historical
# fiction are spread across all 250 years"). Dating a Gothic community against
# the Ngrams curve for "science fiction" would manufacture precisely the fake
# late emergence the brief warns about.
#
# So each community carries BOTH: `terms` (from its vocabulary) and
# `label_terms` (from its held-out label, where that differs). The analysis
# reports both, so the pairing is auditable rather than baked in.
#
# `terms` are PERIOD words first. "Scientific romance" matters more than
# "science fiction" before ~1930; using the modern word for a period genre is
# the brief's named trap.
# ---------------------------------------------------------------------------
COMMUNITIES = [
    {
        "key": "detective",
        "held_out_label": "Detective and mystery stories",
        "vocab_reading": "Detective fiction",
        "label_agrees": True,
        "terms": ["detective story", "detective novel", "detective stories"],
        "label_terms": [],
    },
    {
        "key": "western",
        "held_out_label": "Best Books Ever Listings",
        "vocab_reading": "Western / frontier fiction",
        "label_agrees": False,
        "terms": ["western story", "cowboy story", "frontier novel"],
        # The held-out label is the name of a reading list, not a genre. There is
        # no Ngrams term for it. Recorded as a gap, not silently dropped.
        "label_terms": [],
    },
    {
        "key": "religious",
        "held_out_label": "Fantasy fiction",
        "vocab_reading": "Religious / ecclesiastical fiction",
        "label_agrees": False,
        "terms": ["religious novel", "Catholic novel"],
        "label_terms": ["fantasy fiction", "fantasy novel"],
    },
    {
        "key": "historical",
        "held_out_label": "Historical Fiction",
        "vocab_reading": "Historical romance",
        "label_agrees": True,
        "terms": ["historical romance", "historical novel"],
        "label_terms": ["historical fiction"],
    },
    {
        "key": "domestic",
        "held_out_label": "Domestic fiction",
        "vocab_reading": "Domestic fiction",
        "label_agrees": True,
        "terms": ["domestic novel", "domestic fiction"],
        "label_terms": [],
    },
    {
        "key": "gothic",
        "held_out_label": "Science fiction",
        "vocab_reading": "Gothic / sensation fiction",
        "label_agrees": False,
        "terms": ["Gothic romance", "Gothic novel", "sensation novel", "ghost story"],
        "label_terms": ["scientific romance", "science fiction"],
    },
    {
        "key": "nautical",
        "held_out_label": "Adventure stories",
        "vocab_reading": "Nautical adventure",
        "label_agrees": True,
        "terms": ["sea story", "nautical novel"],
        "label_terms": ["adventure story"],
    },
    {
        "key": "early_novel",
        "held_out_label": "Bildungsromans",
        "vocab_reading": "Early English novel / manners",
        "label_agrees": False,
        "terms": ["novel of manners", "comedy of manners"],
        "label_terms": ["Bildungsroman"],
    },
]

# Controls. Ngrams normalizes by tokens per year, but corpus *composition*
# drifts (the brief's own caveat), and if composition alone pushes usage mass
# later then every genre term inherits that skew and none of the per-genre
# numbers mean anything. These are era-neutral phrases about fiction that were
# in continuous use across the whole window: if they show the same late-mass
# skew as the genre names, the skew is the corpus, not genre formation.
CONTROL_TERMS = ["the novel", "a novel", "the story", "prose fiction"]


def _fetch(terms):
    '''One request for up to a few terms. Returns {requested_term: timeseries}.'''
    params = {
        "content": ",".join(terms),
        "year_start": YEAR_START,
        "year_end": YEAR_END,
        "corpus": CORPUS,
        "smoothing": 0,
        "case_insensitive": "true",
    }
    url = f"{NGRAM_API}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req) as resp:
        payload = json.load(resp)

    # With case_insensitive=true Google returns one "<query> (All)" aggregate
    # per requested term plus every capitalisation variant separately. Keep the
    # aggregates. Match case-insensitively: the "(All)" label echoes back the
    # query's own casing, which is not always what we sent.
    wanted = {t.lower(): t for t in terms}
    out = {}
    for series in payload:
        name = series.get("ngram", "")
        if not name.endswith(" (All)"):
            continue
        base = name[: -len(" (All)")].lower()
        if base in wanted:
            out[wanted[base]] = series["timeseries"]

    # A term with no hits anywhere in the corpus gets no series at all - not an
    # empty one. That is a real answer (the name never entered the language) and
    # must be recorded as zeros rather than left missing, or the analysis will
    # silently skip it.
    for t in terms:
        if t not in out:
            out[t] = None
    return out


def main():
    refetch = "--refetch" in sys.argv

    cache = {}
    if os.path.exists(OUT_FILE) and not refetch:
        with open(OUT_FILE) as fh:
            cache = json.load(fh).get("series", {})
        print(f"cache: {len(cache)} series on disk")

    all_terms = []
    for comm in COMMUNITIES:
        all_terms += comm["terms"] + comm["label_terms"]
    all_terms += CONTROL_TERMS
    # dedupe, preserve order
    seen = set()
    all_terms = [t for t in all_terms if not (t in seen or seen.add(t))]

    todo = [t for t in all_terms if t not in cache]
    print(f"{len(all_terms)} terms total, {len(todo)} to fetch")

    BATCH = 3
    for i in range(0, len(todo), BATCH):
        batch = todo[i : i + BATCH]
        print(f"  fetching {batch} ...", end=" ", flush=True)
        try:
            got = _fetch(batch)
        except Exception as exc:  # noqa: BLE001 - report and continue
            print(f"FAILED: {exc}")
            continue
        for term, ts in got.items():
            cache[term] = ts
            if ts is None:
                print(f"[no data: {term!r}]", end=" ")
        print("ok")
        time.sleep(2.0)  # public endpoint, no key; do not hammer it

    missing = [t for t in all_terms if t not in cache]
    if missing:
        print(f"\nSTILL MISSING after fetch: {missing}")

    payload = {
        "source": "Google Books Ngrams",
        "endpoint": NGRAM_API,
        "corpus": CORPUS,
        "year_start": YEAR_START,
        "year_end": YEAR_END,
        "smoothing": 0,
        "case_insensitive": True,
        "note": (
            "Values are Google's per-year normalized frequencies for the "
            "'(All)' case-insensitive aggregate. index 0 == year_start. "
            "A null series means the term returned no data at all."
        ),
        "communities": COMMUNITIES,
        "control_terms": CONTROL_TERMS,
        "series": cache,
    }
    os.makedirs(shelved_books, exist_ok=True)
    with open(OUT_FILE, "w") as fh:
        json.dump(payload, fh, indent=1)

    n_null = sum(1 for v in cache.values() if v is None)
    print(f"\nwrote {OUT_FILE}: {len(cache)} series ({n_null} with no data)")


if __name__ == "__main__":
    main()
