'''
    Author: Aidan Jude
    S0, step 1: rebuild _data/canon.json from checked-in artifacts alone.

    The Phase 1 corpus was never committed (see docs/RESEARCH-PROGRAM.md,
    "State of play"). Its *identity* survives in two published artifacts:

      results.json        -> communities[].titles   ... all 345 titles
      genre_network.html  -> const DATA {}          ... 166 of them with
                                                        author + year

    This script recovers the other 179. It never calls build_canon.py: two
    non-deterministic LLMs would return a DIFFERENT canon and silently break
    comparability with every published number. The surviving title list is the
    ground truth.

    The load-bearing constraint. controls.py keeps ONE book per author (the
    earliest), and genre_network.html's 166 books carry 166 DISTINCT authors.
    So the 166 are a complete cover of the corpus's author set, and every one
    of the missing 179 must be by an author already on that list. Resolution is
    therefore constrained matching, not open search - and any title whose
    author lands outside the 166 is a reconstruction error, not a discovery.

    Two network sources, both already used by gutenberg_ingest.py:
      Gutendex     -> which of the 166 authors wrote this title
      Open Library -> first-publication year

    Every raw response is written to _data/ before anything is interpreted, so
    the next session verifies rather than re-fetches (S2's lesson).

    Run:  python reconstruct_canon.py [--stage gutendex|openlibrary|assemble|all]
    Out:  _data/recon_raw_gutendex.json
          _data/recon_raw_openlibrary.json
          _data/canon.json
          _data/recon_log.json          <- every miss, every substitution
'''

import argparse
import json
import os
import re
import sys
import time
import unicodedata
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

from animate_genre_growth import extract_data          # do not write a 2nd parser
from constants import shelved_books
from gutenberg_ingest import _http, text_plain_url

GUTENDEX = "https://gutendex.com/books/"
OPENLIB = "https://openlibrary.org/search.json"

RESULTS = "results.json"
NETWORK = "genre_network.html"
RAW_GUTENDEX = os.path.join(shelved_books, "recon_raw_gutendex.json")
RAW_OPENLIB = os.path.join(shelved_books, "recon_raw_openlibrary.json")
RAW_OL_TITLE = os.path.join(shelved_books, "recon_raw_ol_title.json")
OVERRIDES = os.path.join(shelved_books, "recon_overrides.json")
CANON_FILE = os.path.join(shelved_books, "canon.json")
LOG_FILE = os.path.join(shelved_books, "recon_log.json")


# --- normalisation ----------------------------------------------------------
def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s)
                   if not unicodedata.combining(c))


def norm_title(t):
    '''Same normalisation build_canon.norm() used, so keys stay comparable.'''
    t = re.sub(r"[^a-z0-9 ]", " ", strip_accents(t).lower())
    t = re.sub(r"^(the|a|an) ", "", t.strip())
    return re.sub(r"\s+", " ", t).strip()


def title_tokens(t):
    return set(norm_title(t).split())


def surname(author):
    '''Last token of a "First Last" name. Canon stores First Last (see the
    166 in genre_network.html); Gutendex stores "Last, First" and is flipped
    on the way in by flip_name().'''
    a = strip_accents(author).replace(",", " ").split()
    return a[-1].lower() if a else ""


def flip_name(gutendex_name):
    '''"Collins, Wilkie" -> "Wilkie Collins". Leaves already-flipped names be.'''
    if "," not in gutendex_name:
        return gutendex_name.strip()
    last, _, first = gutendex_name.partition(",")
    return f"{first.strip()} {last.strip()}".strip()


# --- inputs -----------------------------------------------------------------
def load_titles():
    '''The 345 titles, tagged with the results.json community they sit in.'''
    r = json.load(open(RESULTS, encoding="utf-8"))
    out = []
    for ci, c in enumerate(r["communities"]):
        for t in c["titles"]:
            out.append({"title": t, "results_community": ci})
    assert len({o["title"] for o in out}) == len(out) == 345, "title list changed"
    return out


def load_known():
    '''The 166 with author + year, straight off the published page.'''
    d = extract_data(NETWORK)
    books = d["books"]
    assert len({b["author"] for b in books}) == len(books) == 166, \
        "the one-per-author invariant this script leans on does not hold"
    return {b["title"]: {"author": b["author"], "year": int(b["year"]),
                         "network_genre": b["genre"]} for b in books}


# --- stage 1: Gutendex ------------------------------------------------------
def gutendex_search(title):
    url = GUTENDEX + "?" + urllib.parse.urlencode(
        {"search": title, "languages": "en"})
    try:
        res = _http(url).get("results", [])
    except Exception as e:                             # noqa: BLE001
        return {"error": repr(e), "results": []}
    keep = []
    for b in res[:10]:
        keep.append({
            "id": b["id"],
            "title": b.get("title", ""),
            "authors": [{"name": a.get("name", ""),
                         "birth_year": a.get("birth_year"),
                         "death_year": a.get("death_year")}
                        for a in (b.get("authors") or [])],
            "has_text": bool(text_plain_url(b.get("formats") or {})),
            "download_count": b.get("download_count"),
        })
    return {"error": None, "results": keep}


def stage_gutendex(titles, workers=8):
    have = {}
    if os.path.isfile(RAW_GUTENDEX):
        have = json.load(open(RAW_GUTENDEX, encoding="utf-8"))
    todo = [t["title"] for t in titles if t["title"] not in have]
    print(f"Gutendex: {len(have)} cached, {len(todo)} to fetch")
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(gutendex_search, t): t for t in todo}
        for i, f in enumerate(as_completed(futs), 1):
            have[futs[f]] = f.result()
            if i % 25 == 0:
                json.dump(have, open(RAW_GUTENDEX, "w", encoding="utf-8"),
                          indent=1, ensure_ascii=False)
                print(f"  {i}/{len(todo)}", end="\r")
    json.dump(have, open(RAW_GUTENDEX, "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)
    print(f"\nWrote {RAW_GUTENDEX} ({len(have)} titles)")
    return have


# --- stage 2: Open Library --------------------------------------------------
def _ol_query(params):
    try:
        d = _http(OPENLIB + "?" + urllib.parse.urlencode(params))
    except Exception as e:                             # noqa: BLE001
        return None, repr(e)
    return [{"y": doc.get("first_publish_year"),
             "t": doc.get("title"),
             "a": (doc.get("author_name") or [None])[0]}
            for doc in (d.get("docs") or [])], None


def openlib_year(title, author_surname, floor):
    '''Raw OL probe, kept whole so the year choice stays auditable.

    Two queries, not one. gutenberg_ingest.publication_year() asks only for
    sort=old, which on a famous title returns a wall of mis-dated reprint and
    anthology records - that is what dated Treasure Island to 1781 on the
    first pass here. The relevance-ranked query is added as a second opinion
    and the two candidate pools are merged at pick time.
    '''
    base = {"title": title, "author": author_surname or "",
            "fields": "first_publish_year,title,author_name", "limit": "20"}
    old, e1 = _ol_query(dict(base, sort="old"))
    rel, e2 = _ol_query(base)
    return {"error": e1 or e2, "docs": old or [], "docs_relevance": rel or [],
            "floor": floor}


# build_canon.py:129 admitted a title only if 1660 <= year < 1929, so any
# Open Library year outside that window is known-wrong for this corpus.
YEAR_LO, YEAR_HI = 1660, 1929


def series_year_counts(ol_all):
    '''(surname, year) -> how many DIFFERENT titles by that author Open Library
    offers that year for.

    A collected-works record ("The Waverley Novels", one catalogue date) is
    returned under every novel in the set, so its year shows up under a dozen
    distinct titles. First-publication years do not behave that way. Left
    unfiltered this dated nine Scott novels to exactly 1800; with the filter
    Ivanhoe/Rob Roy/The Talisman/Redgauntlet/The Fortunes of Nigel all come
    back exact. Measured on the 166 known years it never hurts (mean |err|
    3.43 -> 3.25y) - the calibration set understates it because it contains
    only two Scott novels, which is why the mechanism, not the score, is the
    argument for keeping it.
    '''
    pair = {}
    for key, p in ol_all.items():
        _, _, sur = key.partition("||")
        seen = set()
        for d in (p.get("docs") or []) + (p.get("docs_relevance") or []):
            y = d.get("y")
            if y and (sur, y) not in seen:
                seen.add((sur, y))
                pair[(sur, y)] = pair.get((sur, y), 0) + 1
    return pair


SERIES_MIN_TITLES = 5


def pick_year(probe, title=None, floor=None, sur=None, series=None):
    '''gutenberg_ingest.publication_year()'s rule - oldest edition at or after
    the author turned ~15 - with four corrections the reference lacks. Each was
    measured against the 166 canon years that survive in genre_network.html;
    together they take mean |error| from 16.9 years to 2.5.

      * the floor must actually be author_birth + 15. Flooring at 1660 instead
        admits Open Library's junk early records and pulls dates a mean 16.9
        years early (Treasure Island 1781, The Jungle Book 1740).
      * candidates are restricted to docs whose title really matches, so a
        different book that shares a word cannot supply the year.
      * collected-works records are dropped (see series_year_counts).
      * an exact century (1700 / 1800 / 1900) loses to any non-round candidate.
        Open Library uses these as placeholders; a genuine first publication
        landing on the boundary is rare enough that the trade pays (mean |err|
        3.25 -> 2.50y).

    Returns (year, n_candidates).
    '''
    floor = max(floor or probe.get("floor") or YEAR_LO, YEAR_LO)
    want = title_tokens(title) if title else None
    cands = []
    for d in list(probe.get("docs") or []) + list(probe.get("docs_relevance") or []):
        y = d.get("y")
        if not y or not (floor <= y < YEAR_HI):
            continue
        if want:
            got = title_tokens(d.get("t") or "")
            if len(want & got) / max(len(want), 1) < 0.6:
                continue
        if series is not None and sur is not None \
                and series.get((sur, y), 0) >= SERIES_MIN_TITLES:
            continue
        cands.append(y)
    non_round = [y for y in cands if y % 100]
    if non_round:
        cands = non_round
    return (min(cands) if cands else None), len(cands)


def stage_openlibrary(probes_todo, workers=6):
    have = {}
    if os.path.isfile(RAW_OPENLIB):
        have = json.load(open(RAW_OPENLIB, encoding="utf-8"))
    todo = [p for p in probes_todo if p["key"] not in have]
    print(f"Open Library: {len(have)} cached, {len(todo)} to fetch")
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(openlib_year, p["title"], p["surname"], p["floor"]): p
                for p in todo}
        for i, f in enumerate(as_completed(futs), 1):
            have[futs[f]["key"]] = f.result()
            if i % 25 == 0:
                json.dump(have, open(RAW_OPENLIB, "w", encoding="utf-8"),
                          indent=1, ensure_ascii=False)
                print(f"  {i}/{len(todo)}", end="\r")
    json.dump(have, open(RAW_OPENLIB, "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)
    print(f"\nWrote {RAW_OPENLIB} ({len(have)} probes)")
    return have


# --- author resolution, constrained to the 166 ------------------------------
def build_author_index(known):
    '''surname -> [{"author", "earliest"}], from the 166.

    NOTE the 166 contain SPELLING VARIANTS OF THE SAME PERSON - 'H.G. Wells',
    'H. G. Wells' and 'Herbert George Wells' are three entries. That is a
    property of the original corpus (build_canon.py keyed on
    norm(title)+surname, so one human could enter under several spellings),
    and controls.py's one-book-per-author control groups on the EXACT string,
    so those variants each contributed a book to the "one per author" subset.
    Preserved here deliberately: correcting it would change n_authors and the
    controlled subset, i.e. would stop reproducing the published numbers.
    Reported in docs/S0-CORPUS-RECONSTRUCTION.md as a finding, not fixed here.
    '''
    idx = {}
    for v in known.values():
        idx.setdefault(surname(v["author"]), []).append(
            {"author": v["author"], "earliest": v["year"]})
    for v in idx.values():
        v.sort(key=lambda d: d["earliest"])
    return idx


def given_tokens(name):
    '''Given-name tokens/initials, lowercased, accents stripped, minus the
    surname. "H. G. Wells" -> {"h","g"}; "Herbert George Wells" -> {"herbert",
    "george","h","g"} (initials added so the two forms can be compared).'''
    parts = strip_accents(name).lower().replace(".", " ").replace(",", " ").split()
    if len(parts) <= 1:
        return set()
    given = parts[:-1]
    return set(given) | {g[0] for g in given if g}


def compatible(a, b):
    '''Do two name spellings plausibly denote the same person? True when the
    given-name evidence does not contradict - initials matching full names
    counts as agreement ("H. G." vs "Herbert George").'''
    ga, gb = given_tokens(a), given_tokens(b)
    if not ga or not gb:
        return True
    ia = {t[0] for t in ga}
    ib = {t[0] for t in gb}
    return bool(ga & gb) or ia == ib


def choose_spelling(cands, gutendex_name, book_year):
    '''Pick which of the 166 spellings this book should carry.

    Two different jobs, in order:
      1. DIFFERENT PEOPLE sharing a surname (Sinclair / Wyndham / Matthew
         Lewis; George / T. S. Eliot). Decided on given-name evidence from
         Gutendex - real disambiguation.
      2. SAME PERSON under variant spellings (the Wells case). Unrecoverable:
         the original canon record's spelling is not in any surviving
         artifact. Decided by the only constraint that is observable - the
         spelling must not be one whose earliest-in-corpus book this book
         would displace, because controls.py keeps the earliest book per
         author string and the resulting 166 are known. Logged as an
         assumption; see the verdict doc.
    '''
    if len(cands) == 1:
        return cands[0]["author"], "single"
    same = [c for c in cands if compatible(c["author"], gutendex_name)]
    if len(same) == 1:
        return same[0]["author"], "given_name"
    pool = same or cands
    fits = [c for c in pool if book_year is None or c["earliest"] < book_year]
    if fits:
        return fits[-1]["author"], "year_constrained"
    return pool[0]["author"], "displaces_earliest"


def resolve_author(title, gx, author_idx, bib_by_title, ol_title_probe=None):
    '''Which of the 166 authors wrote this title?
    Returns (candidates, gutendex_name, how, note) - the spelling choice is
    made later, once a year is known.

    There is deliberately NO "first Gutendex hit with a known surname"
    fallback. Gutendex's fuzzy search on a short title returns unrelated
    books: searching "She" returns ten Sherlock Holmes volumes and would have
    filed Haggard's She under Conan Doyle. A fabricated attribution is worse
    than a logged miss.
    '''
    want = title_tokens(title)

    # 1. Gutendex: title overlaps AND the surname is one of the 166.
    best = None
    for b in gx.get("results", []):
        got = title_tokens(b["title"])
        overlap = len(want & got) / max(len(want), 1)
        if overlap < 0.5:
            continue
        for a in b["authors"]:
            flipped = flip_name(a["name"])
            sn = surname(flipped)
            if sn in author_idx and (best is None or overlap > best[0]):
                best = (overlap, sn, flipped, b["id"])
    if best:
        return (author_idx[best[1]], best[2], "gutendex",
                f"gutenberg_id={best[3]} overlap={best[0]:.2f}")

    # 2. Open Library, searched on title alone - an independent catalogue, and
    #    the one that rescues titles Gutendex's search ranks badly.
    for d in (ol_title_probe or {}).get("docs", []):
        if not d.get("a"):
            continue
        got = title_tokens(d.get("t") or "")
        if len(want & got) / max(len(want), 1) < 0.5:
            continue
        sn = surname(d["a"])
        if sn in author_idx:
            return (author_idx[sn], d["a"], "openlibrary_title",
                    f"ol_title={d.get('t')!r}")

    # 3. bibliography.json (Phase 2, same LLM cross-reference method the
    #    original canon used) - accepted only if it lands inside the 166.
    rec = bib_by_title.get(norm_title(title))
    if rec and surname(rec["author"]) in author_idx:
        return (author_idx[surname(rec["author"])], rec["author"],
                "bibliography", f"bib_year={rec['year']}")

    return None, None, "unresolved", ""


def birth_years(gx_all):
    """surname -> earliest author birth year seen anywhere in the Gutendex pull.

    gutenberg_ingest.publication_year() floors the year search at the author's
    birth + 15, which is the single thing that keeps Open Library's mis-dated
    reprint records out. That floor needs a birth year, and Gutendex ships one
    on every author record - so harvest it once across the whole raw pull
    rather than per title."""
    out = {}
    for probe in gx_all.values():
        for b in probe.get("results", []):
            for a in b.get("authors", []):
                by = a.get("birth_year")
                if not by:
                    continue
                sn = surname(flip_name(a["name"]))
                out[sn] = min(out.get(sn, 9999), by)
    return out



# --- the short-title guard --------------------------------------------------
# Gutendex search is fuzzy, so a one- or two-word title matches almost
# anything: "She" returned ten Sherlock Holmes volumes, "The Italian" returned
# Wharton's Italian Villas and Their Gardens, "The Rainbow" returned a WWI
# divisional roster. Each of those would have entered the corpus as a real
# book filed under the wrong author, carrying that author's dates - silent,
# and invisible to any check that only counts how many titles resolved.
#
# So resolution is not trusted on its own. Every reconstructed book must also
# have a Gutendex record under the ASSIGNED author whose title matches exactly,
# allowing the subtitle drift normal for 18th-century novels ("Tom Jones" ->
# "History of Tom Jones, a Foundling"). Anything that fails goes to the
# constrained sweep below rather than into the corpus.

def title_matches(want_norm, got_norm, surname_pinned=False):
    '''Exact after normalisation, or - only where it is safe - the canon title
    appearing as a whole-word run inside the Gutenberg one (subtitle drift:
    "Tom Jones" -> "History of Tom Jones, a Foundling").

    The run-form is NOT safe on a short title searched without an author. The
    first version of this guard allowed it unconditionally and passed exactly
    the three misattributions it was written to catch: " rainbow " matched
    "Roster of the Rainbow division", " italian " matched "Italian Villas and
    Their Gardens", " wanderer " matched "The weird of the wanderer". A guard
    that matches less than the rule it names certifies the bug.

    So the run-form needs one of two things behind it: a title long enough
    (>= 3 tokens) that a verbatim appearance is not coincidence, or a surname
    already pinned to one of the 166, which is what the sweep provides.
    '''
    if got_norm == want_norm:
        return True
    if not (surname_pinned or len(want_norm.split()) >= 3):
        return False
    return f" {want_norm} " in f" {got_norm} "


def has_exact_record(title, author, gx_probe):
    '''Does Gutendex file this exact title under the author we assigned it to?

    surname_pinned is deliberately FALSE here even though a surname is in
    hand. The surname on offer is the assignment under test, so treating it as
    established would let the guard assume its own conclusion - and it did:
    the first version passed The Rainbow/Johnson, The Italian/Wharton and
    The Wanderer/Rolfe by matching " rainbow " inside a title it had itself
    chosen. A check built on the same assumption as the code it checks
    confirms the bug instead of finding it.
    '''
    sur = surname(author)
    want = norm_title(title)
    for b in gx_probe.get("results", []):
        for a in b.get("authors", []):
            if surname(flip_name(a["name"])) != sur:
                continue
            if title_matches(want, norm_title(b.get("title", ""))):
                return b["id"]
    return None


# A canon title is normally the HEAD of the Gutenberg title, with volume or
# subtitle matter after it. These are the words that follow it when that is
# what is happening, as opposed to a different work that merely opens with the
# same word ("Italian Letters", "Wanderer of the Wasteland").
SUBTITLE_MARKERS = {"volume", "vol", "part", "or", "book", "complete"}


def sweep_winner(title, hits):
    '''Pick one surname out of a sweep that returned several.

    The sweep matches with the surname pinned, which is loose enough to catch
    unrelated works: "The Italian" came back under Radcliffe, Godwin,
    Hawthorne and Wharton at once. Rank by how the Gutenberg title relates to
    the canon title - exact, then canon-title-plus-volume/subtitle, then
    nothing - and accept only an unambiguous top rank. Radcliffe's
    "The Italian, Volume 1 (of 3)" wins over Godwin's "Italian Letters";
    Burney's "The Wanderer; or, Female Difficulties" over Grey's "Wanderer of
    the Wasteland". Returns None when the top rank is still tied, so an
    unresolvable case is logged rather than guessed.
    '''
    want = norm_title(title)

    def rank(got):
        g = norm_title(got or "")
        if g == want:
            return 2
        if g.startswith(want + " "):
            nxt = g[len(want) + 1:].split()
            if nxt and (nxt[0] in SUBTITLE_MARKERS or nxt[0].isdigit()):
                return 1
        return 0

    scored = [(rank(h.get("gutenberg_title")), h["surname"]) for h in hits]
    if not scored:
        return None
    best = max(s for s, _ in scored)
    if best == 0:
        return None
    winners = {sn for s, sn in scored if s == best}
    return winners.pop() if len(winners) == 1 else None


def sweep_for_author(title, author_idx, workers=16, pages=3):
    '''Find which of the 166 authors Gutenberg actually files this title under.

    Two passes, cheapest first:
      1. page deeper on the plain title search - the raw pull keeps only the
         first 10 hits and Haggard's She sits below them;
      2. failing that, ask for "<title> <surname>" once per candidate surname.
         166 queries, but it is a search over the constraint set rather than a
         guess, and it is the only thing that finds Radcliffe's The Italian.
    '''
    want = norm_title(title)
    hits = []
    url = GUTENDEX + "?" + urllib.parse.urlencode(
        {"search": title, "languages": "en"})
    for _ in range(pages):
        if not url:
            break
        try:
            d = _http(url)
        except Exception:                              # noqa: BLE001
            break
        for b in d.get("results", []):
            if not title_matches(want, norm_title(b.get("title", ""))):
                continue
            for a in b.get("authors", []):
                sn = surname(flip_name(a["name"]))
                if sn in author_idx:
                    hits.append({"id": b["id"], "gutenberg_title": b.get("title"),
                                 "surname": sn, "via": "deep_page"})
        url = d.get("next")
    if hits:
        return hits

    def one(sn):
        u = GUTENDEX + "?" + urllib.parse.urlencode(
            {"search": f"{title} {sn}", "languages": "en"})
        try:
            res = _http(u).get("results", [])
        except Exception:                              # noqa: BLE001
            return []
        out = []
        for b in res[:8]:
            if not title_matches(want, norm_title(b.get("title", "")), True):
                continue
            for a in b.get("authors", []):
                if surname(flip_name(a["name"])) == sn:
                    out.append({"id": b["id"], "gutenberg_title": b.get("title"),
                                "surname": sn, "via": "surname_sweep"})
        return out

    with ThreadPoolExecutor(max_workers=workers) as ex:
        for f in as_completed([ex.submit(one, sn) for sn in author_idx]):
            hits += f.result()
    return hits


def probe_key(title, sur):
    return f"{title}||{sur}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="all",
                    choices=["gutendex", "openlibrary", "assemble", "all"])
    args = ap.parse_args()
    net = args.stage in ("gutendex", "openlibrary", "all")

    titles = load_titles()
    known = load_known()
    author_idx = build_author_index(known)
    bib = json.load(open(os.path.join(shelved_books, "bibliography.json"),
                         encoding="utf-8"))
    bib_by_title = {}
    for e in bib:
        bib_by_title.setdefault(norm_title(e["title"]), e)

    print(f"{len(titles)} titles; {len(known)} carry author+year on the page; "
          f"{len(titles) - len(known)} to resolve")

    gx_all = (stage_gutendex(titles) if args.stage in ("gutendex", "all")
              else json.load(open(RAW_GUTENDEX, encoding="utf-8")))

    births = birth_years(gx_all)

    def floor_for(sur):
        by = births.get(sur)
        return max((by + 15) if by else YEAR_LO, YEAR_LO)

    log = {"unresolved_author": [], "author_source": {}, "spelling_choice": {},
           "collisions": [], "year_source": {}, "year_missing": [],
           "year_before_author_earliest": [], "calibration": {},
           "displaces_earliest": []}

    # --- pass A: author candidates from Gutendex -----------------------------
    cand = {}
    for rec in titles:
        t = rec["title"]
        if t in known:
            continue
        cand[t] = resolve_author(t, gx_all.get(t, {}), author_idx, bib_by_title)

    # --- pass B: Open Library title-only rescue for the Gutendex misses ------
    missing = [t for t, c in cand.items() if c[0] is None]
    print(f"\nAfter Gutendex: {len(cand) - len(missing)} resolved, "
          f"{len(missing)} need the Open Library title pass")
    ol_titles = {}
    if os.path.isfile(RAW_OL_TITLE):
        ol_titles = json.load(open(RAW_OL_TITLE, encoding="utf-8"))
    todo = [t for t in missing if t not in ol_titles]
    if todo and net:
        with ThreadPoolExecutor(max_workers=6) as ex:
            futs = {ex.submit(openlib_year, t, "", 1660): t for t in todo}
            for f in as_completed(futs):
                ol_titles[futs[f]] = f.result()
        json.dump(ol_titles, open(RAW_OL_TITLE, "w", encoding="utf-8"),
                  indent=1, ensure_ascii=False)
        print(f"Wrote {RAW_OL_TITLE} ({len(ol_titles)} probes)")
    for t in missing:
        cand[t] = resolve_author(t, gx_all.get(t, {}), author_idx,
                                 bib_by_title, ol_titles.get(t))

    for t, c in cand.items():
        log["author_source"][c[2]] = log["author_source"].get(c[2], 0) + 1
        if c[0] is None:
            log["unresolved_author"].append(t)
    print("Author resolution:", log["author_source"])
    if log["unresolved_author"]:
        print("UNRESOLVED:")
        for t in log["unresolved_author"]:
            print("   ", t)

    # --- pass C: years. Probe every title, including the 166, so the 166
    #     double as a calibration set for the source used on the 179. --------
    probes = []
    for rec in titles:
        t = rec["title"]
        if t in known:
            sur = surname(known[t]["author"])
        elif cand[t][0]:
            sur = surname(cand[t][0][0]["author"])
        else:
            continue
        probes.append({"key": probe_key(t, sur), "title": t, "surname": sur,
                       "floor": floor_for(sur)})
    ol_all = (stage_openlibrary(probes) if net
              else json.load(open(RAW_OPENLIB, encoding="utf-8")))

    series = series_year_counts(ol_all)

    diffs = []
    for t, v in known.items():
        p = ol_all.get(probe_key(t, surname(v["author"])))
        if not p:
            continue
        sur = surname(v["author"])
        y, _ = pick_year(p, t, floor_for(sur), sur, series)
        if y is None:
            y, _ = pick_year(p, t, floor_for(sur))
        if y:
            diffs.append((t, v["year"], y, y - v["year"]))
    exact = sum(1 for _, _, _, d in diffs if d == 0)
    within2 = sum(1 for _, _, _, d in diffs if abs(d) <= 2)
    log["calibration"] = {
        "what": "Open Library year, scored against the 166 canon years that "
                "survive in genre_network.html. This is the error rate the "
                "same source injects into the 179 reconstructed years.",
        "n_probed": len(diffs), "exact": exact, "within_2y": within2,
        "exact_pct": round(100 * exact / max(len(diffs), 1), 1),
        "within_2y_pct": round(100 * within2 / max(len(diffs), 1), 1),
        "mean_abs_err": round(sum(abs(d) for *_, d in diffs) / max(len(diffs), 1), 2),
        "worst": [{"title": t, "canon": c, "openlibrary": o, "delta": d}
                  for t, c, o, d in sorted(diffs, key=lambda x: -abs(x[3]))[:30]],
    }
    print(f"\nOpen Library calibration vs the 166 known canon years: "
          f"{exact}/{len(diffs)} exact ({log['calibration']['exact_pct']}%), "
          f"{within2} within 2y ({log['calibration']['within_2y_pct']}%), "
          f"mean |err| {log['calibration']['mean_abs_err']}y")

    # --- pass C2: the short-title guard, then the constrained sweep ----------
    # Runs BEFORE assembly, because its whole job is to stop a wrong author
    # reaching the corpus. Findings are cached in OVERRIDES so a re-run does
    # not repeat 166 queries a title.
    over = json.load(open(OVERRIDES, encoding="utf-8")) \
        if os.path.isfile(OVERRIDES) else {}
    def ol_corroborates(t, sur):
        '''Does the OTHER catalogue also file this title under this author?

        Gutendex-strict alone flags 49 of 179 - mostly harmless 18th-century
        subtitle drift ("Tom Jones" is catalogued as "History of Tom Jones, a
        Foundling"), and sweeping all 49 costs 166 queries each against a
        throttled API. Requiring the two catalogues to DISAGREE before paying
        for a sweep cuts that to 6 while still catching every known
        misattribution - The Italian/Wharton, The Wanderer/Rolfe and
        The Rainbow/Johnson all fail here, because Open Library has no such
        title by that author at all.
        '''
        p = ol_all.get(probe_key(t, sur))
        if not p:
            return False
        want = norm_title(t)
        for d in (p.get("docs") or []) + (p.get("docs_relevance") or []):
            if d.get("y") and title_matches(want, norm_title(d.get("t") or "")):
                return True
        return False

    suspect = []
    for t, c in cand.items():
        if c[0] is None:
            suspect.append(t)
            continue
        author = c[0][0]["author"]
        if has_exact_record(t, author, gx_all.get(t, {})):
            continue
        if ol_corroborates(t, surname(author)):
            continue
        suspect.append(t)
    print(f"\nShort-title guard: {len(suspect)} of {len(cand)} reconstructed "
          f"titles have no exact-title Gutendex record under the assigned "
          f"author; sweeping.")
    for t in suspect:
        if t in over:
            continue
        if not net:
            continue
        hits = sweep_for_author(t, author_idx)
        found = sorted({h["surname"] for h in hits})
        over[t] = {"hits": hits[:6], "surnames": found}
        json.dump(over, open(OVERRIDES, "w", encoding="utf-8"),
                  indent=1, ensure_ascii=False)
    log["guard_suspect"] = suspect
    log["guard_corrections"] = []
    for t in suspect:
        o = over.get(t)
        if not o or not o["surnames"]:
            continue
        sn = sweep_winner(t, o["hits"])
        if sn is None:
            log.setdefault("guard_ambiguous", []).append(
                {"title": t, "surnames": o["surnames"]})
            continue
        was = cand[t][0][0]["author"] if cand[t][0] else None
        if sn in author_idx and surname(was or "") != sn:
            log["guard_corrections"].append(
                {"title": t, "was": was,
                 "now_surname": sn, "evidence": o["hits"][:2]})
            cand[t] = (author_idx[sn], author_idx[sn][0]["author"],
                       "gutendex_sweep",
                       f"gutenberg_id={o['hits'][0]['id']} "
                       f"title={o['hits'][0]['gutenberg_title'][:60]!r}")
    if log["guard_corrections"]:
        print("Guard corrected these attributions:")
        for g in log["guard_corrections"]:
            print(f"   {g['title'][:38]:38s} {str(g['was'])[:22]:22s} -> "
                  f"{g['now_surname']}")

    # any sweep-corrected author needs its own Open Library year probe
    extra = []
    for g in log["guard_corrections"]:
        t = g["title"]
        sur = surname(cand[t][0][0]["author"])
        if probe_key(t, sur) not in ol_all:
            extra.append({"key": probe_key(t, sur), "title": t,
                          "surname": sur, "floor": floor_for(sur)})
    if extra and net:
        ol_all = stage_openlibrary(extra)
        series = series_year_counts(ol_all)

    # --- pass D: assemble ----------------------------------------------------
    earliest = {v["author"]: v["year"] for v in known.values()}
    records, dropped = [], []
    for rec in titles:
        t = rec["title"]
        if t in known:
            records.append({
                "title": t, "author": known[t]["author"],
                "year": known[t]["year"],
                "recon": {"author_src": "genre_network.html",
                          "year_src": "genre_network.html",
                          "spelling": "known", "note": "",
                          "results_community": rec["results_community"]}})
            continue
        cands, gname, how, note = cand[t]
        if cands is None:
            dropped.append({"title": t, "why": "no author inside the 166"})
            continue
        sur = surname(cands[0]["author"])
        p = ol_all.get(probe_key(t, sur))
        # A second floor, and a provable one. genre_network.html's 166 are
        # controls.py's one-book-per-author pick, i.e. each author's EARLIEST
        # book in the corpus - so no other book by that author can predate it.
        # Open Library's error skews early, and without this the too-early
        # years quietly displace the real earliest book: Huckleberry Finn came
        # back as 1875 and took Tom Sawyer's place as Twain's earliest, Jekyll
        # and Hyde as 1875 took Treasure Island's, Kenilworth as 1798 took
        # Waverley's. Eight of the 166 controlled books were the wrong book
        # for exactly this reason. The floor is the earliest across every
        # spelling of the surname, since those spellings are one person.
        person_floor = min(c["earliest"] for c in cands)
        fl = max(floor_for(sur), person_floor)
        year, _ = (pick_year(p, t, fl, sur, series) if p else (None, 0))
        if year is None and p:
            # Relax the SERIES filter if it left nothing, never the floor.
            # An earlier version fell back to the loose floor here and let
            # The Singing Bone through at 1900 against Freeman's 1907 - a
            # fallback that quietly discards the guard it is falling back
            # from is worse than no guard, because the log then says clean.
            year, _ = pick_year(p, t, fl)
        ysrc = "openlibrary"
        if year is None:
            b = bib_by_title.get(norm_title(t))
            if b and surname(b["author"]) == sur:
                year, ysrc = int(b["year"]), "bibliography"
            else:
                log["year_missing"].append(t)
                dropped.append({"title": t, "why": "no year from any source"})
                continue
        author, choice = choose_spelling(cands, gname, year)
        log["year_source"][ysrc] = log["year_source"].get(ysrc, 0) + 1
        log["spelling_choice"][choice] = log["spelling_choice"].get(choice, 0) + 1
        if len(cands) > 1:
            log["collisions"].append(
                {"title": t, "year": year, "gutendex_name": gname,
                 "candidates": [c["author"] for c in cands],
                 "chosen": author, "rule": choice})
        if choice == "displaces_earliest":
            log["displaces_earliest"].append({"title": t, "year": year,
                                              "chosen": author})
        e = earliest.get(author)
        if e is not None and year < e:
            log["year_before_author_earliest"].append(
                {"title": t, "author": author, "resolved_year": year,
                 "author_earliest_in_corpus": e})
        records.append({
            "title": t, "author": author, "year": int(year),
            "recon": {"author_src": how, "year_src": ysrc, "spelling": choice,
                      "note": note,
                      "results_community": rec["results_community"]}})

    log["dropped"] = dropped
    json.dump(records, open(CANON_FILE, "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    json.dump(log, open(LOG_FILE, "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print("\nYear source:", log["year_source"])
    print("Spelling choice:", log["spelling_choice"])
    print("Books whose resolved year predates their author's earliest-in-corpus "
          f"(would change the controlled subset): {len(log['year_before_author_earliest'])}")
    print(f"\nWrote {CANON_FILE}: {len(records)}/345 titles, {len(dropped)} dropped")
    print(f"Wrote {LOG_FILE}")
    print("distinct author strings:", len({r["author"] for r in records}))


if __name__ == "__main__":
    main()
