'''
    Author: Aidan Jude & Claude
    Visualize Phase 2's directed, dual-signal author-influence graph
    (see docs/PHASE2_INFLUENCE_NETWORK.md). Deliberately deferred until real,
    validated edges existed (design doc §6) - they now do, twice over (§9-10).

    Reuses /influences.html's interaction language (click a node, its edges
    light up, everything else dims, a side panel opens) as UI pattern only -
    the data underneath is measured, not curated (see design doc §1).

    The underlying graph is dense (2,915 candidate edges over 77 authors,
    mean out-degree ~38 - an early author like Homer is chronologically
    eligible to connect to almost everyone later) so it is never rendered
    whole. Default view shows only the top slice by conceptual similarity
    (the one signal that replicated significantly, twice) plus every
    independently-documented pair (known_influences.json /
    wikidata_influences.json), regardless of rank. A slider adjusts the cutoff.
    Both signals are shown per-edge and never merged into one score - that
    was the explicit design bet in §7.3.

    Run:  python visualize_influence.py   ->   influence_network.html
'''

import json
import os

from constants import shelved_books

OUT = "influence_network.html"


def build_validated_index(known, wikidata):
    """Map (from, to) -> {'known': note|True, 'wikidata': True} for pairs
    documented by either independent source."""
    idx = {}

    def note_for(rec):
        hits = [n for n in rec.get("notes", []) if rec["to"] in n]
        return hits[0] if hits else None

    for rec in known:
        key = (rec["from"], rec["to"])
        idx.setdefault(key, {})["known"] = note_for(rec) or True
    for rec in wikidata:
        key = (rec["from"], rec["to"])
        idx.setdefault(key, {})["wikidata"] = True
    return idx


def main():
    graph = json.load(open(os.path.join(shelved_books, "influence_graph.json"),
                       encoding="utf-8"))
    known = json.load(open(os.path.join(shelved_books, "known_influences.json"),
                       encoding="utf-8"))
    wikidata = json.load(open(os.path.join(shelved_books, "wikidata_influences.json"),
                          encoding="utf-8"))

    validated_idx = build_validated_index(known, wikidata)

    authors = sorted(graph["authors"], key=lambda a: a["earliest_year"])
    id_of = {a["name"]: i for i, a in enumerate(authors)}
    nodes = [{
        "id": i,
        "name": a["name"],
        "year": a["earliest_year"],
        "form": a["form"],
        "nBooksUsed": a["n_books_used"],
        "nBooksTotal": a["n_books_total"],
    } for i, a in enumerate(authors)]

    edges = []
    n_validated_in_graph = 0
    for e in graph["edges"]:
        key = (e["from"], e["to"])
        v = validated_idx.get(key)
        validated = None
        note = None
        if v:
            n_validated_in_graph += 1
            if "known" in v and "wikidata" in v:
                validated = "both"
            elif "known" in v:
                validated = "known"
            else:
                validated = "wikidata"
            if isinstance(v.get("known"), str):
                note = v["known"]
        edges.append({
            "from": id_of[e["from"]],
            "to": id_of[e["to"]],
            "stylistic": e["stylistic"],
            "conceptual": e["conceptual"],
            "sameForm": e["same_form"],
            "yearGap": e["year_gap"],
            "validated": validated,
            "note": note,
        })

    meta = {
        "nAuthors": graph["n_authors"],
        "nEdges": graph["n_edges"],
        "nValidated": n_validated_in_graph,
        "signalCorrelation": graph["signal_correlation"],
        "sameFormPct": graph["same_form_pct"],
        "heldOut": graph["held_out_validation"],
        "heldOutWikidata": graph["held_out_validation_wikidata"],
        "densityControl": graph["density_control"],
    }

    data = {"meta": meta, "authors": nodes, "edges": edges}
    html = TEMPLATE.replace("__DATA__", json.dumps(data))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {OUT}  |  {len(nodes)} authors, {len(edges)} candidate edges, "
          f"{n_validated_in_graph} independently documented")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Author Influence Network — Literature Mutations, Aidan Jude</title>
<!-- THE PUBLISHED PAGE IS THE ONE THAT MATTERS, SO THE GENERATOR EMITS IT WHOLE.
     This block, the absolute repo links below, the .nd-dot touch targets and the
     postMessage height report were all hand-patched into the deployed copy at
     aidanjude.vercel.app/research/ and never existed here. That is the wrong way
     round: this file is the source, the deployed page is its output, and a
     regeneration silently reverted every one of those fixes (done exactly that,
     2026-08-16). Anything the live page needs is emitted here or it does not
     survive the next run. -->
<meta property="og:site_name" content="Aidan Jude" />
<meta property="og:locale" content="en_US" />
<meta property="og:type" content="website" />
<meta property="og:url" content="https://aidanjude.vercel.app/research/influence-network" />
<meta property="og:title" content="Author Influence Network — Literature Mutations, Aidan Jude" />
<meta property="og:description" content="Author influence network — literature-mutations, Aidan Jude." />
<meta property="og:image" content="https://aidanjude.vercel.app/og/research.png" />
<meta property="og:image:secure_url" content="https://aidanjude.vercel.app/og/research.png" />
<meta property="og:image:type" content="image/png" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:image:alt" content="Author Influence Network — Literature Mutations, Aidan Jude" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="Author Influence Network — Literature Mutations, Aidan Jude" />
<meta name="twitter:description" content="Author influence network — literature-mutations, Aidan Jude." />
<meta name="twitter:image" content="https://aidanjude.vercel.app/og/research.png" />
<style>
  :root{--bg:#f7f3ec;--bg2:#efe9dd;--ink:#1c1814;--ink2:#544e44;--faint:#8b8478;
        --rule:rgba(60,50,40,.16);--accent:#b8442f;--accent-soft:rgba(184,68,47,.14)}
  @media (prefers-color-scheme:dark){
    :root{--bg:#15120f;--bg2:#1d1916;--ink:#e9e3d5;--ink2:#b3aa9a;--faint:#7d766a;
          --rule:rgba(230,220,200,.16);--accent:#e2765f;--accent-soft:rgba(226,118,95,.16)}
  }
  *{box-sizing:border-box;margin:0;padding:0}
  html,body{background:var(--bg);color:var(--ink);
    font-family:Georgia,'Iowan Old Style',serif;min-height:100vh;-webkit-font-smoothing:antialiased}
  .mono{font-family:'SF Mono',ui-monospace,Menlo,Consolas,monospace}
  .page{max-width:1240px;margin:0 auto;padding:44px 32px 64px}
  @media (max-width:720px){.page{padding:24px 14px 40px}}
  header{margin-bottom:28px}
  .eyebrow{font-family:'SF Mono',ui-monospace,Menlo,Consolas,monospace;font-size:11px;
    color:var(--faint);letter-spacing:.1em;text-transform:uppercase}
  h1{font-size:26px;font-style:italic;font-weight:600;letter-spacing:-.01em;margin:4px 0 10px}
  .lede{max-width:74ch;font-size:15.5px;line-height:1.6;color:var(--ink2)}
  .lede a{color:var(--ink)}
  .lede b{color:var(--ink);font-weight:600}

  .stats{display:flex;flex-wrap:wrap;gap:10px;margin:22px 0}
  .stat{background:var(--bg2);border:1px solid var(--rule);border-radius:6px;
    padding:9px 13px;min-width:130px}
  .stat .n{font-size:17px;font-weight:600}
  .stat .n.sig{color:var(--accent)}
  .stat .l{font-family:'SF Mono',ui-monospace,Menlo,Consolas,monospace;font-size:10px;
    color:var(--faint);letter-spacing:.03em;margin-top:2px}

  .controls{display:flex;flex-wrap:wrap;align-items:center;gap:14px;margin:18px 0 10px;
    font-family:'SF Mono',ui-monospace,Menlo,Consolas,monospace;font-size:11.5px;color:var(--ink2)}
  .controls input[type=range]{width:200px;accent-color:var(--accent)}
  .legend{display:flex;flex-wrap:wrap;gap:12px;margin-left:auto}
  .legend .sw{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:5px;vertical-align:middle}
  .legend .validated-sw{display:inline-block;width:16px;height:2px;background:var(--accent);margin-right:5px;vertical-align:middle}

  .graph-wrap{position:relative;border:1px solid var(--rule);border-radius:6px;
    background:var(--bg2);overflow:hidden}
  .graph-scroll{overflow-x:auto;overflow-y:hidden}
  .graph-scroll svg{display:block}

  /* THE GRAPH HAS ALWAYS SCROLLED SIDEWAYS AND NOTHING EVER SAID SO.
     The x axis is the full author sequence, so the SVG is 1848px wide against a
     1174px column at 1440px and a 360px one at 390px: 36% of the graph is right
     of the edge on a desktop and 81% on a phone. Both are reachable — .graph-scroll
     is overflow-x:auto — but a touch device paints no scrollbar and the cut lands
     mid-figure, so the visitor reads the visible slice as the whole graph and
     leaves having seen antiquity. Measured 2026-08-16 at both widths.
     A mark on each side is the affordance, and each side retracts when its
     direction is exhausted, so "there is more this way" is never claimed falsely.

     A GRADIENT ALONE IS NOT AN AFFORDANCE ON THIS FIGURE. The first cut faded
     var(--bg2) into transparent and it was invisible: dark-on-dark, and the right
     edge of this graph is sparse, so there is often no ink there to fade. The
     gradient still earns its place — it softens the guillotine cut through
     whatever edges DO reach the border — but the thing that says "more this way"
     has to be a mark, so each side carries a chevron. */
  .graph-fade{position:absolute;top:0;bottom:0;width:52px;pointer-events:none;
    opacity:0;transition:opacity .25s;z-index:1;
    display:flex;align-items:center;justify-content:center;
    font-family:'SF Mono',ui-monospace,Menlo,Consolas,monospace;font-size:19px;
    color:var(--accent)}
  .graph-fade.l{left:0;background:linear-gradient(90deg,var(--bg2) 22%,transparent)}
  .graph-fade.r{right:0;background:linear-gradient(270deg,var(--bg2) 22%,transparent)}
  .graph-wrap.can-l .graph-fade.l,.graph-wrap.can-r .graph-fade.r{opacity:1}
  /* The hint names the axis as well as the gesture, because "you can scroll" is
     only worth a line if it also says what you would be scrolling through. It is
     removed outright the first time the visitor scrolls — a hint that survives
     being obeyed is furniture. */
  .scroll-hint{display:none;margin:7px 1px 0;font-family:'SF Mono',ui-monospace,Menlo,Consolas,monospace;
    font-size:11px;color:var(--faint);letter-spacing:.02em}
  .scroll-hint.on{display:block}
  .scroll-hint b{color:var(--ink2);font-weight:500}
  .graph-node{cursor:pointer}
  .graph-node circle{transition:opacity .2s}
  .graph-node:hover circle.nd-dot{stroke:var(--ink);stroke-width:1.5}
  .graph-node.dim circle,.graph-node.dim text{opacity:.15}
  .graph-node.focus circle.nd-dot{stroke:var(--accent);stroke-width:2}
  .graph-label{font-family:'SF Mono',ui-monospace,Menlo,Consolas,monospace;font-size:9px;
    fill:var(--ink2);pointer-events:none;transition:opacity .2s}
  .label-tie{stroke:var(--rule);stroke-width:1;pointer-events:none}
  .graph-node.dim .label-tie{opacity:.15}
  .graph-node:focus{outline:none}
  .graph-node:focus-visible circle.nd-dot{stroke:var(--accent);stroke-width:2.5}
  .edge-path{fill:none;pointer-events:none}
  .edge-path.candidate{stroke:var(--ink2)}
  .edge-path.validated{stroke:var(--accent)}
  .edge-path.edge-hidden{display:none}
  .edge-path.edge-focus{display:inline !important;opacity:1 !important;stroke-width:2.2px}
  .edge-path.edge-context-dim{opacity:.035 !important}

  .panel{position:absolute;top:0;right:0;bottom:0;width:min(400px,92%);background:var(--bg);
    border-left:1px solid var(--rule);padding:46px 24px 24px;transform:translateX(100%);
    transition:transform .28s cubic-bezier(.2,.8,.2,1);overflow-y:auto;
    box-shadow:-14px 0 28px rgba(0,0,0,.1);z-index:3}
  .panel.open{transform:translateX(0)}
  .panel-close{position:absolute;top:14px;right:16px;font-family:'SF Mono',ui-monospace,Menlo,Consolas,monospace;
    font-size:11px;color:var(--faint);cursor:pointer}
  .panel h3{font-size:19px;font-style:italic;font-weight:600}
  .panel .sub{font-family:'SF Mono',ui-monospace,Menlo,Consolas,monospace;font-size:11px;
    color:var(--faint);margin-top:4px}
  .edge-row{margin-top:12px;padding-top:12px;border-top:1px solid var(--rule);font-size:13.5px}
  .edge-row .who{font-weight:600}
  .edge-row .scores{font-family:'SF Mono',ui-monospace,Menlo,Consolas,monospace;font-size:10.5px;
    color:var(--ink2);margin-top:3px}
  .edge-row .badge{display:inline-block;font-family:'SF Mono',ui-monospace,Menlo,Consolas,monospace;
    font-size:9.5px;color:var(--accent);border:1px solid var(--accent);border-radius:3px;
    padding:1px 5px;margin-left:6px}
  .edge-row .note{margin-top:5px;color:var(--ink2);font-size:12.5px;line-height:1.45;font-style:italic}
  .panel .more{margin-top:14px;font-size:11.5px;color:var(--faint);font-family:'SF Mono',ui-monospace,Menlo,Consolas,monospace}

  .caveats{margin-top:26px;padding-top:16px;border-top:1px solid var(--rule);
    font-size:13px;line-height:1.6;color:var(--ink2);max-width:78ch}
  .caveats b{color:var(--ink)}
  footer{margin-top:30px;padding-top:16px;border-top:1px solid var(--rule);
    font-family:'SF Mono',ui-monospace,Menlo,Consolas,monospace;font-size:11px;color:var(--faint)}
  footer a{color:var(--ink2)}
</style>
</head>
<body>
<div class="page">
  <header>
    <div class="eyebrow">literature-mutations · phase 2</div>
    <h1>Author Influence Network</h1>
    <p class="lede">A directed graph of 77 public-domain authors (Homer to the 1920s),
      candidate edges permitted only chronologically forward in time. Every edge carries
      <b>two independent similarity scores, never merged</b>: stylistic (word choice,
      syntax — TF-IDF) and conceptual (ideas, themes — embeddings). Held-out against real,
      independently-documented influence claims, conceptual similarity is significant
      and replicates across two separate validation sources; stylistic similarity does not
      hold up under a proper sweep (see caveats below).
      <b>Click any author to trace their edges.</b> Full method:
      <a href="https://github.com/2016judea/literature-mutations/blob/master/docs/PHASE2_INFLUENCE_NETWORK.md" target="_blank" rel="noopener">design doc</a>.</p>
    <div class="stats" id="stats"></div>
  </header>

  <div class="controls">
    <label for="threshold">min. conceptual similarity to show: <span id="threshold-val" class="mono"></span></label>
    <input type="range" id="threshold" min="0" max="1" step="0.001" />
    <span id="edge-count" class="mono"></span>
    <div class="legend" id="legend"></div>
  </div>

  <div class="graph-wrap">
    <div class="graph-scroll"><svg id="graph-svg"></svg></div>
    <div class="graph-fade l" aria-hidden="true">‹</div>
    <div class="graph-fade r" aria-hidden="true">›</div>
    <div class="panel" id="panel"><span class="panel-close" id="panel-close">✕ close</span>
      <div id="panel-body"></div></div>
  </div>
  <p class="scroll-hint" id="scroll-hint"></p>

  <p class="caveats">
    <b>What this is:</b> chronologically-valid candidate edges with a measured similarity
    score, not proof of influence — the accent-colored edges are the subset independently
    documented (LLM-enumerated critical consensus, or Wikidata's structured "influenced by"
    property; never used to build the graph, only to check it after the fact).
    <b>What's solid:</b> conceptual similarity between documented pairs is significantly
    higher than a shuffled-timeline null, twice over, on two independent sources (z=9.47
    on 130 held-out pairs, z=7.16 replicated on 102 independent Wikidata pairs) — and it
    survives a density-confound check on the best-represented authors (z=6.25).
    <b>What's most likely null:</b> stylistic similarity is <i>not</i> significant on the
    full held-out sample (z=0.91), and the two narrower checks that <i>are</i> significant
    (Wikidata z=2.45, well-represented subset z=2.97) turn out not to sit on a trend.
    Raising the minimum books per author and re-testing at every level — each against a
    null drawn from that same subset — gives 0.9, then −0.7, then 0.3, then a single
    excursion at ≥4 books that decays again. Conceptual, run identically as a control, is
    significant at every level and declines smoothly as pairs are lost. The published trio
    were three non-nested samples, not a series. n=77 authors is real but modest scale.
  </p>

  <footer>literature-mutations · <a href="https://github.com/2016judea/literature-mutations" target="_blank" rel="noopener">repo</a> ·
    generated by <span class="mono">visualize_influence.py</span> from
    <span class="mono">_data/influence_graph.json</span></footer>
</div>

<script>
const DATA = __DATA__;
(function(){
  const svg = document.getElementById('graph-svg');
  const svgNS = 'http://www.w3.org/2000/svg';
  function el(tag, attrs){ const e=document.createElementNS(svgNS,tag); for(const k in attrs) e.setAttribute(k, attrs[k]); return e; }

  const FORM_COLOR = {
    poetry:'#4363d8', prose_fiction:'#e6194B', philosophy:'#911eb4',
    drama:'#f58231', other:'#3cb44b'
  };
  const FORM_LABEL = {
    poetry:'poetry', prose_fiction:'prose fiction', philosophy:'philosophy',
    drama:'drama', other:'other (essay/history/etc.)'
  };

  const STILL = matchMedia('(prefers-reduced-motion: reduce)').matches;

  const authors = DATA.authors;
  const edges = DATA.edges;
  const n = authors.length;

  const W = Math.max(1700, n * 24), H = 620;
  const marginX = 60, marginY = 90;
  const bandOrder = ['poetry','prose_fiction','drama','philosophy','other'];
  const bandY = {}; bandOrder.forEach((f,i)=> bandY[f] = marginY + i * ((H - marginY - 60) / (bandOrder.length - 1)));

  authors.forEach((a,i)=>{
    a.x = marginX + (i/(n-1)) * (W - 2*marginX);
    a.y = bandY[a.form];
  });

  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  svg.setAttribute('width', W);
  svg.setAttribute('height', H);
  svg.setAttribute('preserveAspectRatio', 'xMinYMid meet');
  // The drawing states its own axes to a reader who cannot see it. Both channels
  // are arbitrary without this: x is sequence, not a dated timeline, and y is form
  // alone — a fact a sighted visitor infers from the band labels and no one else can.
  svg.setAttribute('role', 'img');
  svg.setAttribute('aria-label',
    `${n} authors from ${authors[0].name} to ${authors[n-1].name}, left to right in ` +
    `chronological order, in five horizontal bands by form: ` +
    `${bandOrder.map(f=>FORM_LABEL[f]).join(', ')}. Curves join authors whose work is ` +
    `similar; the highlighted subset is independently documented influence. ` +
    `Each author is focusable in turn for their own edge list.`);
  document.querySelector('.graph-wrap').style.height = H + 'px';

  // band labels
  bandOrder.forEach(f=>{
    const t = el('text', {class:'graph-label', x: 12, y: bandY[f]+3, 'font-size':11, fill:'var(--ink2)'});
    t.textContent = FORM_LABEL[f];
    svg.appendChild(t);
  });

  const conceptualVals = edges.map(e=>e.conceptual);
  const cMin = Math.min(...conceptualVals), cMax = Math.max(...conceptualVals);
  const sorted = [...conceptualVals].sort((a,b)=>a-b);
  const defaultThreshold = sorted[Math.floor(sorted.length*0.93)];

  function edgePathD(a,b){
    const x1=a.x, y1=a.y, x2=b.x, y2=b.y;
    const midx = (x1+x2)/2;
    return `M ${x1} ${y1} C ${midx} ${y1}, ${midx} ${y2}, ${x2} ${y2}`;
  }

  const edgeEls = edges.map((e,i)=>{
    const a = authors[e.from], b = authors[e.to];
    const validated = !!e.validated;
    const opacity = validated ? 0.85 : Math.max(0.05, (e.conceptual - cMin) / (cMax - cMin) * 0.55);
    const path = el('path', {
      class: 'edge-path ' + (validated ? 'validated' : 'candidate'),
      d: edgePathD(a,b),
      'stroke-width': validated ? 1.6 : 0.6,
      style: `opacity:${opacity}`,
      'data-i': i
    });
    svg.appendChild(path);
    return path;
  });

  /* LABELS SHARE A BAND, SO THEY OVERPRINT EACH OTHER, NOT THE GRAPH.
     Every label used to sit at a fixed offset above its own dot. x is the author's
     position in the sequence and y is only their form, so any run of same-form
     authors close in time stacks their names on one line: 19 overprinting pairs
     among 77 at 1440px before this, worst offenders Sophocles/Euripides and
     Montaigne/Jefferson at 26px of overlap each — two names rendered as one
     unreadable smear, on a figure whose whole claim is which author is which.

     Lane packing fixes it without moving a single dot: walk each band left to
     right (author order IS x order, since x is i/(n-1)) and drop each label into
     the topmost lane whose previous label has already cleared. A crowded stretch
     stacks upward; a sparse one stays tight against its dot.

     FOUR LANES, AND THE LAST IS THE GIVE-UP LANE. Bands sit ~117px apart and the
     tallest stack reaches r + 4 + 3*11 ≈ 44px, so four lanes cannot touch the band
     above — checked against bandY, not assumed. Three lanes left 4 pairs still
     overprinting (Aurelius/Hippo, Jefferson/Paine, Hawthorne/Godwin, Verne/Flaubert);
     four clears them. When every lane is occupied the label takes the top one and
     overprints anyway — better a known, bounded collision in the least-crowded lane
     than a name silently dropped, because an author who is missing from the drawing
     is indistinguishable from an author who is missing from the corpus.

     LANES ARE A BAND-WIDE BASELINE, NOT AN OFFSET FROM EACH DOT. Measuring each
     lane up from the node's own radius is the obvious way to write this and it is
     wrong: dot radius encodes how many of the author's works are in the corpus, so
     a lane-1 label above a small dot can sit BELOW a lane-0 label above a large
     one. That is how the first cut of this still left 4 overlapping pairs at
     1.3px — Aurelius on lane 1 landing 9.2px from Hippo on lane 0, against a
     10.5px glyph box. Anchoring every lane in a band to that band's largest radius
     makes the spacing exactly LANE_STEP everywhere, which is the only version of
     this that can be reasoned about at all.

     LABEL_CH is the 9px monospace advance width (~0.6em). It is an estimate, but
     an estimate of a MONOSPACE face, where every glyph is the same width — the one
     case where character count predicts pixels exactly. LANE_STEP clears the 10.5px
     box that a 9px face actually renders, which is not the same number as 9. */
  const LANES = 4, LANE_STEP = 11, LABEL_CH = 5.4, LABEL_GAP = 5;
  const laneEnds = {};
  const bandMaxR = {};
  authors.forEach(a=>{
    const r = 3 + a.nBooksUsed * 0.9;
    if (!(a.form in bandMaxR) || r > bandMaxR[a.form]) bandMaxR[a.form] = r;
  });

  const nodeEls = authors.map((a,i)=>{
    const g = el('g', {class:'graph-node', 'data-id':i});
    const r = 3 + a.nBooksUsed * 0.9;
    // Radius encodes corpus depth, so the least-represented authors get the
    // smallest dots — and a 3.9px dot is not a tap target. An invisible circle at
    // a real finger's radius sits under each one; .nd-dot is the visible mark, so
    // hover and focus styling has to name it or it lights the hit area instead.
    g.appendChild(el('circle', {cx:a.x, cy:a.y, r: Math.max(r, 11),
                                fill:'transparent', 'pointer-events':'all'}));
    g.appendChild(el('circle', {class:'nd-dot', cx:a.x, cy:a.y, r,
                                fill:FORM_COLOR[a.form], stroke:'none'}));

    const short = a.name.split(' ').slice(-1)[0];
    const halfW = (short.length * LABEL_CH) / 2;
    const ends = laneEnds[a.form] || (laneEnds[a.form] = new Array(LANES).fill(-Infinity));
    let lane = ends.findIndex(end => a.x - halfW > end + LABEL_GAP);
    if (lane < 0) lane = LANES - 1;
    ends[lane] = a.x + halfW;

    const labelY = a.y - bandMaxR[a.form] - 4 - lane * LANE_STEP;
    const t = el('text', {class:'graph-label', x:a.x, y:labelY, 'text-anchor':'middle'});
    t.textContent = short;
    g.appendChild(t);
    // A label lifted off its dot has to be tied back to it: with 77 dots in five
    // bands the nearest dot below a floating name is not reliably its own. Drawn
    // whenever the lift is big enough to read as a gap rather than as kerning.
    if (a.y - r - labelY > 9) {
      g.appendChild(el('line', {class:'label-tie', x1:a.x, y1:a.y - r - 2,
                                x2:a.x, y2:labelY + 2}));
    }

    g.setAttribute('tabindex', '0');
    g.setAttribute('role', 'button');
    g.setAttribute('aria-label', `${a.name}, ${FORM_LABEL[a.form]}`);
    svg.appendChild(g);
    g.addEventListener('click', ()=> selectNode(i));
    g.addEventListener('keydown', e=>{
      if(e.key === 'Enter' || e.key === ' '){ e.preventDefault(); selectNode(i); }
    });
    return g;
  });

  function applyThreshold(th){
    let shown = 0;
    edgeEls.forEach((path,i)=>{
      const e = edges[i];
      const visible = e.validated || e.conceptual >= th;
      path.classList.toggle('edge-hidden', !visible);
      if(visible) shown++;
    });
    document.getElementById('edge-count').textContent =
      `showing ${shown} of ${edges.length} candidate edges (${DATA.meta.nValidated} independently documented always shown)`;
  }

  const thresholdInput = document.getElementById('threshold');
  thresholdInput.min = cMin; thresholdInput.max = cMax; thresholdInput.step = 0.002;
  thresholdInput.value = defaultThreshold;
  document.getElementById('threshold-val').textContent = defaultThreshold.toFixed(3);
  applyThreshold(defaultThreshold);
  thresholdInput.addEventListener('input', ()=>{
    const v = parseFloat(thresholdInput.value);
    document.getElementById('threshold-val').textContent = v.toFixed(3);
    applyThreshold(v);
    clearFocus();
  });

  const panel = document.getElementById('panel');
  const panelBody = document.getElementById('panel-body');

  function clearFocus(){
    nodeEls.forEach(g=>g.classList.remove('dim','focus'));
    edgeEls.forEach(p=>p.classList.remove('edge-focus','edge-context-dim'));
    panel.classList.remove('open');
  }

  function fmtValidated(e){
    if(e.validated === 'both') return '<span class="badge">known + wikidata</span>';
    if(e.validated === 'known') return '<span class="badge">documented</span>';
    if(e.validated === 'wikidata') return '<span class="badge">wikidata</span>';
    return '';
  }

  function scrollNodeIntoView(a){
    const scrollEl = document.querySelector('.graph-scroll');
    const wrapW = document.querySelector('.graph-wrap').clientWidth;
    const panelW = Math.min(400, wrapW * 0.92);
    const safeW = Math.max(200, wrapW - panelW);
    const targetLeft = a.x - safeW * 0.4;
    // A visitor who asked not to be moved is still owed the node they clicked;
    // reduced motion removes the travel, not the destination.
    scrollEl.scrollTo({left: Math.max(0, targetLeft),
                       behavior: STILL ? 'auto' : 'smooth'});
  }

  function selectNode(i){
    const a = authors[i];
    scrollNodeIntoView(a);
    const touching = edges.map((e,idx)=>({e,idx})).filter(({e})=> e.from===i || e.to===i);
    const ranked = touching.slice().sort((x,y)=> y.e.conceptual - x.e.conceptual);
    const focus = new Set();
    ranked.slice(0,12).forEach(({idx})=>focus.add(idx));
    touching.forEach(({e,idx})=>{ if(e.validated) focus.add(idx); });

    const related = new Set([i]);
    focus.forEach(idx=>{ related.add(edges[idx].from); related.add(edges[idx].to); });

    nodeEls.forEach((g,gi)=>{
      g.classList.toggle('focus', gi===i);
      g.classList.toggle('dim', !related.has(gi));
    });
    edgeEls.forEach((p,pi)=>{
      p.classList.toggle('edge-focus', focus.has(pi));
      p.classList.toggle('edge-context-dim', !focus.has(pi));
    });

    const rows = [...focus].sort((x,y)=> edges[y].conceptual - edges[x].conceptual).map(idx=>{
      const e = edges[idx];
      const outgoing = e.from === i;
      const other = authors[outgoing ? e.to : e.from];
      const arrow = outgoing ? `${a.name.split(' ').slice(-1)[0]} → ${other.name}` : `${other.name} → ${a.name.split(' ').slice(-1)[0]}`;
      return `<div class="edge-row">
        <div class="who">${arrow} ${fmtValidated(e)}</div>
        <div class="scores">conceptual ${e.conceptual.toFixed(3)} · stylistic ${e.stylistic.toFixed(3)} ·
          ${e.sameForm ? 'same form' : 'cross-form'} · ${e.yearGap}y gap</div>
        ${e.note ? `<div class="note">${e.note}</div>` : ''}
      </div>`;
    }).join('');

    const remaining = touching.length - focus.size;
    panelBody.innerHTML = `
      <h3>${a.name}</h3>
      <div class="sub">b. ${a.year < 0 ? Math.abs(a.year)+' BCE' : a.year} ·
        ${FORM_LABEL[a.form]} · ${a.nBooksUsed} of ${a.nBooksTotal} works used</div>
      ${rows}
      ${remaining > 0 ? `<div class="more">+ ${remaining} more chronologically-valid candidate edges below this cutoff, not shown</div>` : ''}
    `;
    panel.classList.add('open');
  }

  document.getElementById('panel-close').addEventListener('click', clearFocus);
  document.querySelector('.graph-scroll').addEventListener('click', e=>{
    if(e.target.tagName === 'svg' || e.target.tagName === 'text' && !e.target.closest('.graph-node')) clearFocus();
  });

  /* THE OFF-SCREEN SHARE, SAID OUT LOUD.
     Both the fades and the hint are driven off ONE measurement of the live
     scroller rather than a breakpoint, because the width that decides this is the
     iframe's, not the phone's — the research page embeds this at 350px inside a
     390px screen, and any media query written against the viewport would be
     measuring the wrong box. It re-measures on resize for the same reason.

     The hint quotes the share it can actually see hidden. A hint that says "scroll
     for more" on a graph with 40px hidden has spent the visitor's attention on
     nothing; one that says 81% has earned it. Under 15% hidden, neither appears. */
  const scroller = document.querySelector('.graph-scroll');
  const wrap = document.querySelector('.graph-wrap');
  const hint = document.getElementById('scroll-hint');
  let hintLive = true;

  function scrollState(){
    const hidden = scroller.scrollWidth - scroller.clientWidth;
    wrap.classList.toggle('can-l', scroller.scrollLeft > 8);
    wrap.classList.toggle('can-r', scroller.scrollLeft < hidden - 8);
    if (hintLive) {
      const share = hidden / scroller.scrollWidth;
      hint.classList.toggle('on', share > 0.15);
      hint.innerHTML = `<b>${Math.round(share * 100)}% of the graph is off to the right.</b> ` +
        `Scroll or swipe it sideways — authors run oldest (Homer) to newest (${authors[n-1].name}).`;
    }
  }
  scroller.addEventListener('scroll', ()=>{
    scrollState();
    // Obeyed once is enough. Keep the fades, retire the sentence.
    if (hintLive && scroller.scrollLeft > 24) { hintLive = false; hint.classList.remove('on'); }
  }, {passive:true});
  new ResizeObserver(scrollState).observe(scroller);
  scrollState();

  // legend
  const legend = document.getElementById('legend');
  bandOrder.forEach(f=>{
    const s = document.createElement('span');
    s.innerHTML = `<span class="sw" style="background:${FORM_COLOR[f]}"></span>${FORM_LABEL[f]}`;
    legend.appendChild(s);
  });
  const vs = document.createElement('span');
  vs.innerHTML = `<span class="validated-sw"></span>independently documented`;
  legend.appendChild(vs);

  /* THE PARENT PAGE SIZES THIS IFRAME FROM WHAT WE TELL IT.
     research/index.html embeds both network pages and listens for this message;
     without it the iframe falls back to a hardcoded 1480px (1860px on phones),
     which clips the caveats on one viewport and leaves dead space on another.
     Re-sent on resize because the fades, the hint line and the wrapped stat rows
     all change our height at a breakpoint. */
  function reportHeight(){
    if (window.parent === window) return;
    window.parent.postMessage({source:'research-iframe',
      height: document.documentElement.scrollHeight}, location.origin);
  }
  reportHeight();
  window.addEventListener('load', reportHeight);
  let resizeT;
  window.addEventListener('resize', ()=>{ clearTimeout(resizeT); resizeT = setTimeout(reportHeight, 150); });

  // stats header
  const m = DATA.meta;
  const stats = document.getElementById('stats');
  const rows = [
    [m.nAuthors, 'authors'],
    [m.nEdges.toLocaleString(), 'candidate edges'],
    [m.nValidated, 'independently documented'],
    ['z=' + m.heldOut.conceptual.z.toFixed(2), 'conceptual, held-out (n=' + m.heldOut.n_known_pairs_in_graph + ')', true],
    ['z=' + m.heldOutWikidata.conceptual.z.toFixed(2), 'conceptual, wikidata-replicated (n=' + m.heldOutWikidata.n_pairs_in_graph + ')', true],
    ['z=' + m.heldOut.stylistic.z.toFixed(2), 'stylistic, held-out (not significant)'],
    [m.signalCorrelation.toFixed(2), 'stylistic↔conceptual correlation'],
    [m.sameFormPct.toFixed(1) + '%', 'edges same-form'],
  ];
  rows.forEach(([val,label,sig])=>{
    const d = document.createElement('div');
    d.className = 'stat';
    d.innerHTML = `<div class="n${sig?' sig':''}">${val}</div><div class="l">${label}</div>`;
    stats.appendChild(d);
  });
})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
