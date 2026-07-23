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
<title>Author Influence Network — literature-mutations Phase 2</title>
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
  .graph-node{cursor:pointer}
  .graph-node circle{transition:opacity .2s}
  .graph-node:hover circle{stroke:var(--ink);stroke-width:1.5}
  .graph-node.dim circle,.graph-node.dim text{opacity:.15}
  .graph-node.focus circle{stroke:var(--accent);stroke-width:2}
  .graph-label{font-family:'SF Mono',ui-monospace,Menlo,Consolas,monospace;font-size:9px;
    fill:var(--ink2);pointer-events:none;transition:opacity .2s}
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
      and replicates across two separate validation sources; stylistic similarity is a
      genuinely open, unresolved question (see caveats below).
      <b>Click any author to trace their edges.</b> Full method:
      <a href="docs/PHASE2_INFLUENCE_NETWORK.md">design doc</a>.</p>
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
    <div class="panel" id="panel"><span class="panel-close" id="panel-close">✕ close</span>
      <div id="panel-body"></div></div>
  </div>

  <p class="caveats">
    <b>What this is:</b> chronologically-valid candidate edges with a measured similarity
    score, not proof of influence — the accent-colored edges are the subset independently
    documented (LLM-enumerated critical consensus, or Wikidata's structured "influenced by"
    property; never used to build the graph, only to check it after the fact).
    <b>What's solid:</b> conceptual similarity between documented pairs is significantly
    higher than a shuffled-timeline null, twice over, on two independent sources (z=9.47
    on 130 held-out pairs, z=7.16 replicated on 102 independent Wikidata pairs) — and it
    survives a density-confound check on the best-represented authors (z=6.25).
    <b>What's open:</b> stylistic similarity is <i>not</i> significant on the full held-out
    sample (z=0.91) but <i>is</i> significant in two narrower checks (Wikidata z=2.45,
    well-represented subset z=2.97) — an honest, unresolved discrepancy, not adjudicated
    here. n=77 authors is real but modest scale.
  </p>

  <footer>literature-mutations · <a href="README.md">repo</a> ·
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

  const nodeEls = authors.map((a,i)=>{
    const g = el('g', {class:'graph-node', 'data-id':i});
    const r = 3 + a.nBooksUsed * 0.9;
    g.appendChild(el('circle', {cx:a.x, cy:a.y, r, fill:FORM_COLOR[a.form], stroke:'none'}));
    const t = el('text', {class:'graph-label', x:a.x, y:a.y - r - 4, 'text-anchor':'middle'});
    t.textContent = a.name.split(' ').slice(-1)[0];
    g.appendChild(t);
    svg.appendChild(g);
    g.addEventListener('click', ()=> selectNode(i));
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
    scrollEl.scrollTo({left: Math.max(0, targetLeft), behavior: 'smooth'});
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
