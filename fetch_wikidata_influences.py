'''
    Author: Aidan Jude
    Phase 2, step 2b: an independent, non-LLM-enumerated validation source.

    known_influences.json (build_influence_graph.py's held-out check) is
    entirely LLM-enumerated - a real limitation the design doc names
    directly (docs/PHASE2_INFLUENCE_NETWORK.md SS9). This script builds a
    second list from a source no model touches: Wikidata's structured
    "influenced by" property (P737), queried straight off each author's
    Wikidata item. No model ever originates or paraphrases the claim here -
    only the API and exact-name matching against the graph's own author list.

    (Wikipedia's own infobox influences/influenced fields were checked first
    and found populated for only 2 of 77 authors - those parameters were
    deprecated as unsourced/POV-prone years ago and stripped from most
    articles. Wikidata's P737 claims are a separate, still-actively-
    maintained store: 44 of 77 authors have them, 350 claims total.)

    Env:  none (public API, no key required)
    Run:  python fetch_wikidata_influences.py
    In:   _data/influence_graph.json (for the 77 canonical author names)
    Out:  _data/wikidata_influences.json
'''

import json
import os
import socket
import time
import urllib.parse
import urllib.request

socket.setdefaulttimeout(45)

from constants import shelved_books

GRAPH_FILE = os.path.join(shelved_books, "influence_graph.json")
OUT_FILE = os.path.join(shelved_books, "wikidata_influences.json")

WD_API = "https://www.wikidata.org/w/api.php"
UA = "literature-mutations-research/1.0 (personal research project; contact: aidanjude2016@gmail.com)"


def _api_get(base, params):
    url = f"{base}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(3):
        try:
            return json.loads(urllib.request.urlopen(req, timeout=30).read())
        except Exception:                              # noqa: BLE001
            time.sleep(2 * (attempt + 1))
    return None


def load_author_names():
    graph = json.load(open(GRAPH_FILE, encoding="utf-8"))
    return [a["name"] for a in graph["authors"]]


def wikidata_qid(name):
    r = _api_get(WD_API, {"action": "wbsearchentities", "search": name,
                          "language": "en", "format": "json", "limit": 1})
    hits = (r or {}).get("search", [])
    return hits[0]["id"] if hits else None


def p737_target_qids(qid):
    r = _api_get(WD_API, {"action": "wbgetclaims", "entity": qid,
                          "property": "P737", "format": "json"})
    claims = (r or {}).get("claims", {}).get("P737", [])
    qids = []
    for c in claims:
        try:
            qids.append(c["mainsnak"]["datavalue"]["value"]["id"])
        except KeyError:
            continue
    return qids


def resolve_labels(qids):
    '''Batch-resolve QIDs -> English labels (wbgetentities allows up to 50/call).'''
    labels = {}
    qids = list(dict.fromkeys(qids))                    # dedupe, preserve order
    for i in range(0, len(qids), 50):
        batch = qids[i:i + 50]
        r = _api_get(WD_API, {"action": "wbgetentities", "ids": "|".join(batch),
                              "props": "labels", "languages": "en", "format": "json"})
        for qid, entity in (r or {}).get("entities", {}).items():
            label = entity.get("labels", {}).get("en", {}).get("value")
            if label:
                labels[qid] = label
        time.sleep(0.2)
    return labels


def main():
    names = load_author_names()
    canonical_set = set(names)
    print(f"{len(names)} canonical authors to check")

    qid_of = {}
    for i, name in enumerate(names, 1):
        qid_of[name] = wikidata_qid(name)
        if i % 20 == 0 or i == len(names):
            print(f"  resolved QIDs: {i}/{len(names)}")
        time.sleep(0.15)

    raw_pairs = []                                       # (from_qid, to_name) - "from" unresolved yet
    for i, (name, qid) in enumerate(qid_of.items(), 1):
        if not qid:
            continue
        targets = p737_target_qids(qid)
        for t_qid in targets:
            raw_pairs.append((t_qid, name))              # t_qid "influenced" name
        if i % 20 == 0 or i == len(names):
            print(f"  fetched P737 claims: {i}/{len(names)}, {len(raw_pairs)} raw pairs so far")
        time.sleep(0.15)

    all_target_qids = [q for q, _ in raw_pairs]
    labels = resolve_labels(all_target_qids)

    pairs, unmatched = [], set()
    for t_qid, to_name in raw_pairs:
        from_name = labels.get(t_qid)
        if from_name is None:
            continue
        if from_name in canonical_set and from_name != to_name:
            pairs.append({"from": from_name, "to": to_name, "source": "wikidata_p737"})
        else:
            unmatched.add(from_name)

    seen = set()
    deduped = []
    for p in pairs:
        key = (p["from"], p["to"])
        if key not in seen:
            seen.add(key)
            deduped.append(p)

    print(f"\n{len(deduped)} unique pairs resolving inside the 77-author graph "
          f"(from {len(raw_pairs)} raw P737 claims)")
    print(f"{len(unmatched)} distinct 'influenced by' targets fell outside the "
          f"77-author set (expected - most real influences aren't in this corpus)")

    os.makedirs(shelved_books, exist_ok=True)
    json.dump(deduped, open(OUT_FILE, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"Wrote {OUT_FILE}")


if __name__ == "__main__":
    main()
