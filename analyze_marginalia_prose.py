'''
    Author: Aidan Jude

    S7 — the measurement the marginalia corpus uniquely permits.

    THE QUESTION. Attribution can tell you Shakespeare influenced Melville.
    It cannot tell you WHICH LINES. vendor/marginalia can:

        Do the passages a reader MARKED resemble that reader's own prose
        more than unmarked passages of the same book do?

    Nobody has asked this at scale because nobody had the joined data. It is
    the first claim in this repo that scholarly attribution structurally
    cannot make, because attribution has no passage.

    THE CONTROL, and why it decides whether anything else is trustworthy.
    Melville left 169 transcribed marks in Thomas Beale's *Natural History
    of the Sperm Whale* (1839), a book he demonstrably lifted into
    Moby-Dick — the cetology chapters paraphrase Beale closely and the
    borrowing is uncontested. If the method cannot recover Beale, it cannot
    be trusted on Shakespeare. Beale is not on Gutenberg; the 1839 edition
    is fetched from the Internet Archive.

    THE DESIGN, and the confound it exists to kill.

    Naively one would compare the corpus's transcribed marked text against
    the source book's remaining text. That is wrong: the marked text is
    Melville's Marginalia Online's transcription of an 1837/1857 printing,
    and the comparison text is a modern Gutenberg edition. The two differ
    in orthography, and the difference is systematic — so any similarity
    gap would partly measure edition, not attention.

    So marked passages are FUZZY-LOCATED inside the comparison text and the
    marked span is taken in the comparison text's own orthography. Both
    sides of the test then share a single edition. Match rate is reported
    per author; a low rate means the wrong edition, not a weak signal.

    Null: random spans from the same book, drawn to the same length
    distribution as the located marked spans, N times. p is the fraction of
    draws scoring at or above the marked set.

    WHAT THIS CANNOT SAY, stated up front because the result is worthless
    without it: a positive means marked passages are lexically closer to
    the reader's own prose. It does NOT establish direction. He may have
    marked what already sounded like him. The one purchase on direction
    available here is the EARLY/LATE split — Melville's pre-1849 books
    against Moby-Dick and after — and it is reported separately, never
    merged into the headline.

    In:   vendor/marginalia/_data/  (submodule; run its build first)
    Out:  _data/marginalia_prose.json
    Run:  python analyze_marginalia_prose.py
'''

import gzip
import json
import os
import random
import re
import sys
import urllib.request

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "cache", "s7")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_data", "marginalia_prose.json")
MARG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor", "marginalia", "_data")
UA = {"User-Agent": "literature-mutations/1.0 (personal research; aidanjude2016@gmail.com)"}
SEED = 20260827
N_DRAWS = 2000          # actual draws per null; the headline p rests on this

# The reader. Melville is the only reader in the corpus with both a large
# body of transcribed marks AND a large body of his own public-domain prose,
# which is what this test needs on both sides.
READER = "Herman Melville"
READER_EARLY = {4045: "Typee (1846)", 4045.1: None, 13720: "Omoo (1847)"}
READER_TEXTS = {
    # early: written BEFORE the 1849-51 reading that produced Moby-Dick
    4045: ("Typee", 1846, "early"),
    13720: ("Omoo", 1847, "early"),
    8118: ("Redburn", 1849, "early"),
    # late: Moby-Dick and after
    2701: ("Moby-Dick", 1851, "late"),
    21816: ("Pierre", 1852, "late"),
    21715: ("The Confidence-Man", 1857, "late"),
}

# Source books Melville marked, paired with a full text of the same work.
# `gutenberg` ids or an Internet Archive identifier. Only works where the
# corpus has emitted marked text AND a full text exists are testable; the
# rest are reported as untestable rather than dropped.
SOURCES = {
    "William Shakespeare": dict(gutenberg=[100], note="Complete Works"),
    "John Milton": dict(gutenberg=[1745], note="Poetical Works"),
    "Nathaniel Hawthorne": dict(gutenberg=[512], note="Mosses from an Old Manse — the marked book"),
    "William Hazlitt": dict(gutenberg=[16209], note="Lectures on the English Poets — the marked book"),
    "Ralph Waldo Emerson": dict(gutenberg=[2944, 2945], note="Essays, First and Second Series"),
    "Arthur Schopenhauer": dict(gutenberg=[10732], note="Essays / Studies in Pessimism"),
    "Christopher Marlowe": dict(gutenberg=[21262, 42724], note="Works, vols 2-3"),
    "Matthew Arnold": dict(gutenberg=[54985], note="Poems"),
    "Thomas Beale": dict(archive="naturalhistoryof00beal",
                         note="Natural History of the Sperm Whale, 1839 — THE CONTROL"),
}

WORD = re.compile(r"[a-z']+")


def _fetch(url, name):
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, name)
    if os.path.exists(p) and os.path.getsize(p) > 20000:
        return open(p, encoding="utf-8", errors="replace").read()
    raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180).read()
    text = raw.decode("utf-8", errors="replace")
    if len(text) < 20000:
        raise RuntimeError(f"{url} returned {len(text)} bytes -- Gutenberg serves an HTML "
                           f"error page as a 404 body, so a short read is a wrong id, "
                           f"not a short book.")
    open(p, "w", encoding="utf-8").write(text)
    return text


def gutenberg(gid):
    raw = _fetch(f"https://www.gutenberg.org/cache/epub/{gid}/pg{gid}.txt", f"pg{gid}.txt")
    s, e = raw.find("*** START"), raw.find("*** END")
    if s < 0 or e < s:
        raise RuntimeError(f"pg{gid}: Gutenberg markers missing; refusing to guess.")
    return raw[raw.find("\n", s) + 1:e]


def archive(ident):
    return _fetch(f"https://archive.org/download/{ident}/{ident}_djvu.txt", f"ia_{ident}.txt")


def tokens(text):
    return WORD.findall(text.lower().replace("’", "'"))


def load_marks():
    '''Marked passages per source author, from the submodule.'''
    vols = {}
    with open(os.path.join(MARG, "volumes.jsonl"), encoding="utf-8") as f:
        for line in f:
            v = json.loads(line)
            vols[v["volume_id"]] = v
    out = {}
    with gzip.open(os.path.join(MARG, "marks.jsonl.gz"), "rt", encoding="utf-8") as f:
        for line in f:
            m = json.loads(line)
            v = vols.get(m["volume_id"])
            if not v or v["reader_id"] != "melville":
                continue
            # Only Herman's own hand -- 433 marks are "Herman or Elizabeth"
            # and all of them sit in the Channing volumes, which are not
            # testable anyway. Filtering here keeps the claim about him.
            if not m.get("hand_is_reader", True):
                continue
            t = (m.get("marked_text") or "").strip()
            if t:
                out.setdefault(v["source_author"], []).append(t)
    return out


def locate(marked, toks, min_score=0.5):
    '''
        Fuzzy-locate each marked passage in the comparison text and return
        the located spans as token index ranges.

        Anchored on the passage's RAREST tokens, because a common-word
        anchor lands anywhere. Scored by token overlap over a window of the
        passage's own length. Anything under min_score is a miss and is
        counted, never forced onto a position -- a forced match is the
        failure mode that makes this whole test look like it worked.
    '''
    freq = {}
    for t in toks:
        freq[t] = freq.get(t, 0) + 1
    index = {}
    for i, t in enumerate(toks):
        if freq[t] <= 200:
            index.setdefault(t, []).append(i)

    spans, misses = [], 0
    for passage in marked:
        pt = tokens(passage)
        if len(pt) < 3:
            misses += 1
            continue
        anchors = sorted(set(pt), key=lambda t: freq.get(t, 0))[:4]
        cands = set()
        for a in anchors:
            for pos in index.get(a, [])[:400]:
                cands.add(max(0, pos - len(pt)))
        if not cands:
            misses += 1
            continue
        want = set(pt)
        best, best_at = 0.0, None
        for start in cands:
            window = toks[start:start + len(pt) * 2]
            if not window:
                continue
            score = len(want & set(window)) / len(want)
            if score > best:
                best, best_at = score, start
        if best >= min_score and best_at is not None:
            spans.append((best_at, best_at + len(pt)))
        else:
            misses += 1
    return spans, misses


def bag(toks, spans):
    out = []
    for a, b in spans:
        out += toks[a:b]
    return out


def cosine(a, b, idf):
    '''TF-IDF cosine between two token bags under a shared idf.'''
    def vec(bagged):
        tf = {}
        for t in bagged:
            if t in idf:
                tf[t] = tf.get(t, 0) + 1
        n = sum(tf.values()) or 1
        return {t: (c / n) * idf[t] for t, c in tf.items()}
    va, vb = vec(a), vec(b)
    if not va or not vb:
        return 0.0
    dot = sum(v * vb.get(t, 0.0) for t, v in va.items())
    na = sum(v * v for v in va.values()) ** 0.5
    nb = sum(v * v for v in vb.values()) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


def main():
    rng = random.Random(SEED)
    marks = load_marks()

    reader_docs = {}
    for gid, (title, year, era) in sorted(READER_TEXTS.items(), key=lambda kv: kv[1][1]):
        reader_docs[title] = dict(era=era, year=year, toks=tokens(gutenberg(gid)))
    reader_all = [t for d in reader_docs.values() for t in d["toks"]]
    reader_early = [t for d in reader_docs.values() if d["era"] == "early" for t in d["toks"]]
    reader_late = [t for d in reader_docs.values() if d["era"] == "late" for t in d["toks"]]

    # idf over the reader's books plus every source book: a shared vocabulary
    # space, and it drops words common to most documents -- the "novel-ese"
    # control Phase 1's semantic_edges.py applies for the same reason.
    docs = {f"reader:{k}": v["toks"] for k, v in reader_docs.items()}
    source_toks = {}
    untestable = {}
    for author, spec in SOURCES.items():
        if author not in marks:
            untestable[author] = "no emitted marked text in the corpus"
            continue
        try:
            if "gutenberg" in spec:
                text = "\n".join(gutenberg(g) for g in spec["gutenberg"])
            else:
                text = archive(spec["archive"])
        except Exception as exc:
            untestable[author] = f"full text unavailable: {str(exc)[:90]}"
            continue
        source_toks[author] = tokens(text)
        docs[f"source:{author}"] = source_toks[author]

    import math
    N = len(docs)
    df = {}
    for d in docs.values():
        for t in set(d):
            df[t] = df.get(t, 0) + 1
    # drop vocabulary present in >40% of documents (Phase 1's threshold) and
    # anything appearing in only one, which cannot support a comparison
    idf = {t: math.log(N / c) for t, c in df.items() if 1 < c <= max(2, int(N * 0.4))}

    results = {}
    for author, toks in source_toks.items():
        spans, misses = locate(marks[author], toks)
        rate = len(spans) / len(marks[author])
        # A low match rate means the comparison edition is not the work he
        # marked, so the located spans are a biased sample of it. Schopenhauer
        # located 29 of 200 (0.145) and would otherwise have been reported as a
        # result -- 20 spans was too permissive a floor.
        if rate < 0.3:
            untestable[author] = (f"only {len(spans)} of {len(marks[author])} marked "
                                  f"passages located ({rate:.2f}) -- the comparison "
                                  f"edition is probably not the work he marked, so the "
                                  f"located spans are a biased sample of it")
            continue
        if len(spans) < 40:
            untestable[author] = (f"{len(spans)} located spans at a good match rate "
                                  f"({rate:.2f}) -- the edition is right, there is "
                                  f"simply not enough marked text to test")
            continue
        marked_bag = bag(toks, spans)
        lengths = [b - a for a, b in spans]

        def draw():
            sp = []
            for L in lengths:
                if len(toks) <= L:
                    continue
                s = rng.randrange(0, len(toks) - L)
                sp.append((s, s + L))
            return bag(toks, sp)

        obs = cosine(marked_bag, reader_all, idf)
        # One draw feeds BOTH nulls, so the direction test is not a second
        # experiment on fresh randomness.
        null, null_shift = [], []
        for _ in range(N_DRAWS):
            b = draw()
            null.append(cosine(b, reader_all, idf))
            e, l = cosine(b, reader_early, idf), cosine(b, reader_late, idf)
            null_shift.append(l - e)
        null.sort()
        mu = sum(null) / len(null)
        sd = (sum((x - mu) ** 2 for x in null) / max(1, len(null) - 1)) ** 0.5
        ge = sum(1 for x in null if x >= obs)

        # DIRECTION. `shift` is how much more the span resembles Moby-Dick and
        # after than it resembles Typee/Omoo/Redburn. A marked set can only
        # claim a direction if its shift beats random spans of the same book --
        # otherwise the gap is a property of the book, not of what he marked.
        obs_e = cosine(marked_bag, reader_early, idf)
        obs_l = cosine(marked_bag, reader_late, idf)
        shift = obs_l - obs_e
        smu = sum(null_shift) / len(null_shift)
        ssd = (sum((x - smu) ** 2 for x in null_shift) / max(1, len(null_shift) - 1)) ** 0.5
        sge = sum(1 for x in null_shift if x >= shift)
        results[author] = dict(
            note=SOURCES[author]["note"],
            n_marked_passages=len(marks[author]), n_located=len(spans), n_missed=misses,
            match_rate=round(len(spans) / len(marks[author]), 3),
            marked_words=len(marked_bag), source_words=len(toks),
            observed=round(obs, 5), null_mean=round(mu, 5), null_sd=round(sd, 6),
            z=round((obs - mu) / sd, 2) if sd else None,
            p=round((ge + 1) / (len(null) + 1), 4),
            # direction, reported separately and never merged into the headline
            marked_vs_early=round(obs_e, 5),
            marked_vs_late=round(obs_l, 5),
            late_shift=round(shift, 5),
            late_shift_null_mean=round(smu, 5),
            late_shift_z=round((shift - smu) / ssd, 2) if ssd else None,
            late_shift_p=round((sge + 1) / (len(null_shift) + 1), 4),
        )

    payload = dict(
        question=("Do the passages a reader marked resemble that reader's own prose more "
                  "than unmarked passages of the same book?"),
        reader=READER, seed=SEED, n_null_draws=N_DRAWS // 4,
        caveat=("A positive result means marked passages are lexically closer to the "
                "reader's prose. It does NOT establish direction -- he may have marked "
                "what already sounded like him. marked_vs_early / marked_vs_late is the "
                "only purchase on direction here and is reported separately."),
        reader_corpus={k: dict(year=v["year"], era=v["era"], words=len(v["toks"]))
                       for k, v in reader_docs.items()},
        results=results, untestable=untestable,
    )
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(payload, open(OUT, "w"), indent=1)

    print(f"reader corpus: {len(reader_all):,} words "
          f"(early {len(reader_early):,} / late {len(reader_late):,})\n")
    print(f'{"source author":<22} {"marks":>6} {"found":>6} {"rate":>5} '
          f'{"z":>7} {"p":>7} | {"late-shift":>10} {"z":>6} {"p":>7}')
    for a, r in sorted(results.items(), key=lambda kv: -(kv[1]["z"] or 0)):
        print(f'{a[:22]:<22} {r["n_marked_passages"]:>6} {r["n_located"]:>6} '
              f'{r["match_rate"]:>5} {str(r["z"]):>7} {r["p"]:>7} | '
              f'{r["late_shift"]:>10} {str(r["late_shift_z"]):>6} {r["late_shift_p"]:>7}')
    if untestable:
        print("\nuntestable:")
        for a, why in untestable.items():
            print(f"  {a}: {why}")


if __name__ == "__main__":
    main()
