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
def openlib_year(title, author_surname, floor):
    '''Raw OL probe. Same shape gutenberg_ingest.publication_year() uses, but
    the whole candidate list is kept so the choice is auditable.'''
    params = {"title": title, "author": author_surname or "",
              "fields": "first_publish_year,title,author_name",
              "limit": "20", "sort": "old"}
    try:
        d = _http(OPENLIB + "?" + urllib.parse.urlencode(params))
    except Exception as e:                             # noqa: BLE001
        return {"error": repr(e), "docs": [], "floor": floor}
    docs = [{"y": doc.get("first_publish_year"),
             "t": doc.get("title"),
             "a": (doc.get("author_name") or [None])[0]}
            for doc in (d.get("docs") or [])]
    return {"error": None, "docs": docs, "floor": floor}


def pick_year(probe):
    '''gutenberg_ingest.publication_year()'s rule: oldest edition at or after
    the author turned ~15. Returns (year, n_candidates).'''
    floor = probe.get("floor") or 1400
    years = [d["y"] for d in probe["docs"] if d.get("y") and d["y"] >= floor]
    return (min(years) if years else None), len(years)


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
        probes.append({"key": probe_key(t, sur), "title": t,
                       "surname": sur, "floor": 1660})
    ol_all = (stage_openlibrary(probes) if net
              else json.load(open(RAW_OPENLIB, encoding="utf-8")))

    diffs = []
    for t, v in known.items():
        p = ol_all.get(probe_key(t, surname(v["author"])))
        if not p:
            continue
        y, _ = pick_year(p)
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
        year, _ = (pick_year(p) if p else (None, 0))
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
