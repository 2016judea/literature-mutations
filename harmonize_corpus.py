'''
    Author: Aidan Jude
    S0, step 3b: make the same work carry the same date.

    The published 345-book corpus contains 14 works TWICE, under two titles
    each - "Tom Jones" and "History of Tom Jones, a Foundling", "Cecilia" and
    "Cecilia; or, Memoirs of an Heiress", "The Sign of Four" and "The Sign of
    the Four". This is not a reconstruction artifact: both members of all 14
    pairs are in results.json's published title list. build_canon.py keys its
    dedup on norm(title) + surname, and a subtitle survives that key, so one
    novel entered the canon as two books.

    That is worth stating plainly for the paper - n_books = 345 counts about
    331 distinct works, and byte-identical twins are guaranteed each other's
    nearest neighbour, so they form maximum-strength 2-cliques the community
    detector then sees as structure. NOT fixed here: dropping them would
    change the corpus away from the one that produced the published numbers,
    which is the opposite of S0's job.

    What IS fixed here is a defect this reconstruction introduced. The two
    titles of a pair get their years from different sources, so the same text
    could end up with two dates - Frankenstein at 1818 (known, off the
    published page) and 1816 (my Open Library lookup); The Black Arrow at 1888
    and 1923. One work, two dates, in a corpus whose entire statistic is
    temporal. Resolution order:

      1. a year recovered from genre_network.html wins outright - it is the
         original value, not an estimate;
      2. otherwise take the earliest, since canon.json means first
         publication and Open Library's error here skews late.

    Run:  python harmonize_corpus.py
'''

import collections
import json
import os

from constants import shelved_books

BOOKS = os.path.join(shelved_books, "books.json")
CANON = os.path.join(shelved_books, "canon.json")
LOG = os.path.join(shelved_books, "harmonize_log.json")


def main():
    data = json.load(open(BOOKS, encoding="utf-8"))
    books = data["books"]
    canon = {c["title"]: c for c in json.load(open(CANON, encoding="utf-8"))}

    by_id = collections.defaultdict(list)
    for b in books:
        by_id[b["gutenberg_id"]].append(b)

    log = {"duplicate_works": [], "year_conflicts_fixed": []}
    for gid, group in sorted(by_id.items()):
        if len(group) < 2:
            continue
        years = {int(b["date_published"]) for b in group}
        entry = {"gutenberg_id": gid,
                 "titles": [b["title"] for b in group],
                 "years": sorted(years)}
        log["duplicate_works"].append(entry)
        if len(years) == 1:
            continue
        known = [b for b in group
                 if canon.get(b["title"], {}).get("recon", {}).get("year_src")
                 == "genre_network.html"]
        if known:
            year = int(known[0]["date_published"])
            why = f"published value from {known[0]['title']!r}"
        else:
            year = min(years)
            why = "earliest of the reconstructed years"
        for b in group:
            b["date_published"] = str(year)
        entry["resolved_to"] = year
        log["year_conflicts_fixed"].append(
            {"gutenberg_id": gid, "titles": entry["titles"],
             "was": sorted(years), "now": year, "rule": why})

    json.dump(data, open(BOOKS, "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    json.dump(log, open(LOG, "w", encoding="utf-8"), indent=2)

    print(f"{len(books)} books -> {len(by_id)} distinct Gutenberg works")
    print(f"{len(log['duplicate_works'])} works appear more than once "
          f"(a property of the PUBLISHED corpus, left in place)")
    print(f"{len(log['year_conflicts_fixed'])} of them disagreed on the year "
          f"and were harmonised:")
    for f in log["year_conflicts_fixed"]:
        print(f"   {f['was']} -> {f['now']}   {f['titles'][0][:44]} ({f['rule']})")
    print(f"Wrote {LOG}")


if __name__ == "__main__":
    main()
