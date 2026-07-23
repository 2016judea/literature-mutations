'''
    Author: Aidan Jude & Claude
    Rebuild Phase 1's genre network (visualize.py -> literary_genres.html, a
    generic two-panel Plotly export) as a custom, hand-styled interactive
    page in the same visual/interaction grammar as visualize_influence.py's
    Phase 2 output: click a node, its cluster lights up, a side panel opens.

    Data provenance: _data/books.json (the real Gutenberg full-text corpus)
    isn't present in this checkout - rebuilding it requires re-running
    build_canon.py + build_corpus.py against Gutenberg/LLM APIs. Rather than
    recomputing the clustering, this script extracts the already-computed,
    already-published per-book layout (x, y, community, title/author/year)
    straight out of literary_genres.html's embedded Plotly JSON - that HTML
    is itself the checked-in, screenshot-verified record of a real run - and
    cross-references controls_results.json for each community's top_terms
    (the one field the Plotly hover text doesn't carry). If visualize.py is
    ever rerun against a fresh corpus, rerun this script immediately after so
    the two stay in sync.

    Run:  python visualize_genres.py   ->   genre_network.html
'''

import json
import re

SRC = "literary_genres.html"
CONTROLS = "controls_results.json"
OUT = "genre_network.html"


def extract_plotly_data(path):
    html = open(path, encoding="utf-8").read()
    m = re.search(r'Plotly\.newPlot\(\s*"[^"]+",\s*(\[.*?\]),\s*\{', html, re.S)
    if not m:
        raise RuntimeError(f"couldn't find embedded Plotly data in {path}")
    return json.loads(m.group(1))


def parse_hover(text):
    m = re.match(r"<b>(.*?)</b><br>(.*?)\s*\((\d+)\)", text)
    if not m:
        return {"title": text, "author": "", "year": None}
    return {"title": m.group(1), "author": m.group(2), "year": int(m.group(3))}


def main():
    traces = extract_plotly_data(SRC)
    controls = json.load(open(CONTROLS, encoding="utf-8"))
    terms_by_label = {c["held_out_label"]: c["top_terms"] for c in controls["communities"]}

    edge_trace = traces[0]
    community_traces = [t for t in traces if t.get("mode") == "markers"]

    books = []
    genres = []
    coord_to_id = {}

    for gi, t in enumerate(community_traces):
        m = re.match(r"(.*?)\s*\(z=([+-][\d.]+)\)\s*(★)?$", t["name"])
        label, z, emergent = (m.group(1).strip(), float(m.group(2)), bool(m.group(3))) \
            if m else (t["name"], 0.0, False)
        color = t["marker"]["color"]
        idx0 = len(books)
        years = []
        for x, y, text in zip(t["x"], t["y"], t["text"]):
            info = parse_hover(text)
            bid = len(books)
            coord_to_id[(round(x, 6), round(y, 6))] = bid
            books.append({
                "id": bid, "title": info["title"], "author": info["author"],
                "year": info["year"], "genre": gi, "x": x, "y": y,
            })
            if info["year"] is not None:
                years.append(info["year"])
        genres.append({
            "idx": gi, "name": label, "z": z, "emergent": emergent, "color": color,
            "n": len(t["x"]), "yearMin": min(years) if years else None,
            "yearMax": max(years) if years else None,
            "topTerms": terms_by_label.get(label, []),
            "bookIds": list(range(idx0, len(books))),
        })

    edges = []
    xs, ys = edge_trace["x"], edge_trace["y"]
    for i in range(0, len(xs) - 2, 3):
        if xs[i + 2] is not None:
            continue
        a = coord_to_id.get((round(xs[i], 6), round(ys[i], 6)))
        b = coord_to_id.get((round(xs[i + 1], 6), round(ys[i + 1], 6)))
        if a is not None and b is not None:
            edges.append([a, b])

    meta = {
        "nBooks": controls["n_books"], "nAuthors": controls["n_authors"],
        "nGenres": len(genres),
        "authorConfoundPct": controls["author_confound_pct"],
        "emergentGenre": next((g["name"] for g in genres if g["emergent"]), None),
    }

    data = {"meta": meta, "books": books, "genres": genres, "edges": edges}
    html = TEMPLATE.replace("__DATA__", json.dumps(data))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {OUT}  |  {len(books)} books, {len(genres)} genres, {len(edges)} edges")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Genre Network — literature-mutations Phase 1</title>
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

  .legend{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0 10px}
  .legend-item{display:flex;align-items:center;gap:6px;font-family:'SF Mono',ui-monospace,Menlo,Consolas,monospace;
    font-size:11px;color:var(--ink2);cursor:pointer;background:var(--bg2);border:1px solid var(--rule);
    border-radius:999px;padding:5px 10px 5px 8px;transition:border-color .2s,color .2s}
  .legend-item:hover{border-color:var(--ink2);color:var(--ink)}
  .legend-item.active{border-color:var(--accent);color:var(--ink)}
  .legend-item .sw{display:inline-block;width:9px;height:9px;border-radius:50%}
  .legend-item .star{color:var(--accent)}

  .layout{display:grid;grid-template-columns:1fr;gap:14px}
  @media (min-width:980px){.layout{grid-template-columns:2.1fr 1fr}}
  .graph-wrap{position:relative;border:1px solid var(--rule);border-radius:6px;
    background:var(--bg2);overflow:hidden;height:620px}
  .graph-wrap svg{display:block;width:100%;height:100%}
  .graph-node{cursor:pointer}
  .graph-node circle{transition:opacity .2s}
  .graph-node:hover circle{stroke:var(--ink);stroke-width:1.5}
  .graph-node.dim circle{opacity:.12}
  .graph-node.focus circle{stroke:var(--accent);stroke-width:2}
  .edge-path{fill:none;stroke:var(--ink2);pointer-events:none;opacity:.12}
  .edge-path.edge-focus{opacity:.7 !important;stroke:var(--accent);stroke-width:1.4px}
  .edge-path.edge-context-dim{opacity:.02 !important}

  .side{border:1px solid var(--rule);border-radius:6px;background:var(--bg2);
    padding:16px 18px;height:620px;overflow-y:auto}
  .side h3{font-size:17px;font-style:italic;font-weight:600}
  .side .sub{font-family:'SF Mono',ui-monospace,Menlo,Consolas,monospace;font-size:11px;
    color:var(--faint);margin-top:4px}
  .side .empty{color:var(--faint);font-size:13.5px;line-height:1.6;margin-top:8px}
  .side .terms{margin-top:10px;font-family:'SF Mono',ui-monospace,Menlo,Consolas,monospace;
    font-size:11px;color:var(--ink2)}
  .side .terms span{background:var(--bg);border:1px solid var(--rule);border-radius:4px;
    padding:2px 6px;margin:2px 3px 0 0;display:inline-block}
  .book-row{margin-top:10px;padding-top:10px;border-top:1px solid var(--rule);font-size:13.5px}
  .book-row.focus-book{color:var(--accent)}
  .book-row .t{font-weight:600}
  .book-row .a{font-family:'SF Mono',ui-monospace,Menlo,Consolas,monospace;font-size:10.5px;color:var(--ink2)}

  .temporal{margin-top:22px;border:1px solid var(--rule);border-radius:6px;background:var(--bg2);
    padding:16px 18px}
  .temporal h2{font-family:'SF Mono',ui-monospace,Menlo,Consolas,monospace;font-size:11px;
    letter-spacing:.08em;text-transform:uppercase;color:var(--faint);margin-bottom:12px}
  .temporal-row{display:flex;align-items:center;gap:10px;padding:5px 0;cursor:pointer;border-radius:4px}
  .temporal-row:hover{background:var(--bg)}
  .temporal-row.active{background:var(--accent-soft)}
  .temporal-label{width:230px;flex:none;font-size:12.5px;color:var(--ink2);text-align:right}
  .temporal-label b{color:var(--ink)}
  .temporal-track{flex:1;position:relative;height:10px;background:var(--rule);border-radius:99px}
  .temporal-bar{position:absolute;top:0;height:10px;border-radius:99px}
  .temporal-z{width:96px;flex:none;font-family:'SF Mono',ui-monospace,Menlo,Consolas,monospace;font-size:11px;color:var(--faint)}
  .temporal-z .star{color:var(--accent);font-weight:600}

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
    <div class="eyebrow">literature-mutations · phase 1</div>
    <h1>Genre Network</h1>
    <p class="lede">345 canon novels, one per author (166 authors), after
      regressing out secular prose-style drift. An unsupervised k-NN
      similarity graph over each novel's opening prose, clustered by
      community detection - <b>no genre label is ever fed in.</b> Colour is
      the community the model found; each cluster's held-out Gutenberg
      subject label (never used to build the graph, only to check it after)
      is shown alongside. <b>Click a novel, or a genre below, to trace its
      cluster.</b> Full method:
      <a href="docs/PHASE2_INFLUENCE_NETWORK.md">design doc</a>,
      <a href="README.md">README</a>.</p>
    <div class="stats" id="stats"></div>
  </header>

  <div class="legend" id="legend"></div>

  <div class="layout">
    <div class="graph-wrap"><svg id="graph-svg"></svg></div>
    <div class="side" id="side"><div class="empty">Click a novel or a genre pill above to see what the model found.</div></div>
  </div>

  <div class="temporal">
    <h2>Temporal concentration — born, or perennial?</h2>
    <div id="temporal-rows"></div>
  </div>

  <p class="caveats">
    <b>What this is:</b> genres recovered purely from distinctive prose
    vocabulary, after controlling for three confounds in turn - corpus
    density, secular style drift, and prolific-author voice (one book per
    author). <b>What's solid:</b> the recovered clusters match recognizable
    genres and each is independently confirmed by a held-out Gutenberg
    subject label the model never saw. <b>What's open:</b> only one cluster
    is temporally concentrated enough to call a genuine, datable emergence
    (z ≤ -2); the rest are perennial modes spread across the full 1660-1928
    span, and a null model (shuffled publication years) can't be
    distinguished from real chronology overall (z = -0.27).</p>

  <footer>literature-mutations · <a href="README.md">repo</a> ·
    generated by <span class="mono">visualize_genres.py</span> from
    <span class="mono">literary_genres.html</span> + <span class="mono">controls_results.json</span></footer>
</div>

<script>
const DATA = __DATA__;
(function(){
  const svg = document.getElementById('graph-svg');
  const svgNS = 'http://www.w3.org/2000/svg';
  function el(tag, attrs){ const e=document.createElementNS(svgNS,tag); for(const k in attrs) e.setAttribute(k, attrs[k]); return e; }

  const books = DATA.books, genresMeta = DATA.genres, edges = DATA.edges;

  const xs = books.map(b=>b.x), ys = books.map(b=>b.y);
  const xMin=Math.min(...xs), xMax=Math.max(...xs), yMin=Math.min(...ys), yMax=Math.max(...ys);
  const W = 900, H = 620, pad = 36;
  function sx(x){ return pad + (x - xMin) / (xMax - xMin) * (W - 2*pad); }
  function sy(y){ return pad + (y - yMin) / (yMax - yMin) * (H - 2*pad); }
  books.forEach(b=>{ b.sx = sx(b.x); b.sy = sy(b.y); });

  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');

  const edgeEls = edges.map(([a,b])=>{
    const A = books[a], B = books[b];
    const path = el('path', {
      class:'edge-path', d:`M ${A.sx} ${A.sy} L ${B.sx} ${B.sy}`, 'stroke-width':0.5
    });
    svg.appendChild(path);
    return {path, a, b};
  });

  const nodeEls = books.map((b,i)=>{
    const g = el('g', {class:'graph-node', 'data-id':i});
    const genre = genresMeta[b.genre];
    const r = genre.emergent ? 6 : 4.4;
    g.appendChild(el('circle', {cx:b.sx, cy:b.sy, r, fill:genre.color,
      stroke: genre.emergent ? 'black' : 'none', 'stroke-width': genre.emergent ? 1.2 : 0}));
    svg.appendChild(g);
    g.addEventListener('click', ()=> selectBook(i));
    return g;
  });

  const side = document.getElementById('side');

  function clearFocus(){
    nodeEls.forEach(g=>g.classList.remove('dim','focus'));
    edgeEls.forEach(({path})=>path.classList.remove('edge-focus','edge-context-dim'));
    document.querySelectorAll('.legend-item').forEach(el=>el.classList.remove('active'));
    document.querySelectorAll('.temporal-row').forEach(el=>el.classList.remove('active'));
  }

  function highlightGenre(gi){
    const genre = genresMeta[gi];
    const inGenre = new Set(genre.bookIds);
    nodeEls.forEach((g,i)=>{
      g.classList.toggle('focus', false);
      g.classList.toggle('dim', !inGenre.has(i));
    });
    edgeEls.forEach(({path,a,b})=>{
      const rel = inGenre.has(a) && inGenre.has(b);
      path.classList.toggle('edge-focus', rel);
      path.classList.toggle('edge-context-dim', !rel);
    });
    document.querySelectorAll('.legend-item').forEach(el=>
      el.classList.toggle('active', +el.dataset.genre === gi));
    document.querySelectorAll('.temporal-row').forEach(el=>
      el.classList.toggle('active', +el.dataset.genre === gi));
  }

  function genreOverview(gi){
    const genre = genresMeta[gi];
    highlightGenre(gi);
    const members = genre.bookIds.map(id=>books[id]).sort((a,b)=>(a.year||0)-(b.year||0));
    const termsHtml = genre.topTerms.map(t=>`<span>${t}</span>`).join('');
    const rows = members.map(b=>`<div class="book-row"><div class="t">${b.title}</div>
      <div class="a">${b.author}${b.year?' · '+b.year:''}</div></div>`).join('');
    side.innerHTML = `
      <h3>${genre.name}${genre.emergent ? ' ★' : ''}</h3>
      <div class="sub">${genre.n} novels · ${genre.yearMin}–${genre.yearMax} ·
        z = ${genre.z >= 0 ? '+' : ''}${genre.z.toFixed(2)}${genre.emergent ? ' (temporally concentrated)' : ' (perennial mode)'}</div>
      <div class="terms">${termsHtml}</div>
      ${rows}
    `;
  }

  function selectBook(i){
    const b = books[i];
    genreOverview(b.genre);
    nodeEls[i].classList.add('focus');
    // re-render side with this book pinned to the top
    const genre = genresMeta[b.genre];
    const members = genre.bookIds.map(id=>books[id]).sort((x,y)=>(x.year||0)-(y.year||0));
    const termsHtml = genre.topTerms.map(t=>`<span>${t}</span>`).join('');
    const rows = members.map(m=>`<div class="book-row${m.id===i?' focus-book':''}"><div class="t">${m.id===i?'▸ ':''}${m.title}</div>
      <div class="a">${m.author}${m.year?' · '+m.year:''}</div></div>`).join('');
    side.innerHTML = `
      <h3>${genre.name}${genre.emergent ? ' ★' : ''}</h3>
      <div class="sub">${genre.n} novels · ${genre.yearMin}–${genre.yearMax} ·
        z = ${genre.z >= 0 ? '+' : ''}${genre.z.toFixed(2)}${genre.emergent ? ' (temporally concentrated)' : ' (perennial mode)'}</div>
      <div class="terms">${termsHtml}</div>
      ${rows}
    `;
  }

  svg.addEventListener('click', e=>{ if(e.target === svg) clearFocus(); });

  // legend
  const legend = document.getElementById('legend');
  genresMeta.forEach(genre=>{
    const el2 = document.createElement('div');
    el2.className = 'legend-item';
    el2.dataset.genre = genre.idx;
    el2.innerHTML = `<span class="sw" style="background:${genre.color}"></span>${genre.name}${genre.emergent?' <span class="star">★</span>':''}`;
    el2.addEventListener('click', ()=> genreOverview(genre.idx));
    legend.appendChild(el2);
  });

  // temporal concentration panel
  const yearsAll = books.map(b=>b.year).filter(y=>y!=null);
  const yMinAll = Math.min(...yearsAll), yMaxAll = Math.max(...yearsAll);
  const temporalRoot = document.getElementById('temporal-rows');
  const ranked = [...genresMeta].sort((a,b)=>a.z-b.z);
  ranked.forEach(genre=>{
    const row = document.createElement('div');
    row.className = 'temporal-row';
    row.dataset.genre = genre.idx;
    const left = (genre.yearMin - yMinAll) / (yMaxAll - yMinAll) * 100;
    const width = Math.max(1.5, (genre.yearMax - genre.yearMin) / (yMaxAll - yMinAll) * 100);
    row.innerHTML = `
      <div class="temporal-label"><b>${genre.name}</b>${genre.emergent?' ★':''}</div>
      <div class="temporal-track"><div class="temporal-bar" style="left:${left}%;width:${width}%;background:${genre.color}"></div></div>
      <div class="temporal-z">${genre.yearMin}–${genre.yearMax} <span class="${genre.emergent?'star':''}">z=${genre.z>=0?'+':''}${genre.z.toFixed(1)}</span></div>
    `;
    row.addEventListener('click', ()=> genreOverview(genre.idx));
    temporalRoot.appendChild(row);
  });

  // stats header
  const m = DATA.meta;
  const stats = document.getElementById('stats');
  const rows = [
    [m.nBooks, 'novels'],
    [m.nAuthors, 'authors (one book each, de-trended)'],
    [m.nGenres, 'genre clusters recovered'],
    [m.emergentGenre, 'the one temporally-concentrated genre', true],
    [m.authorConfoundPct.toFixed(1) + '%', 'raw edges were same-author (controlled out)'],
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
