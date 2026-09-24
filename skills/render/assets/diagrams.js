// diagrams.js: core engine for Render.diagram.*. Loads after page.js (needs
// window.Render for esc/anchored) and before any per-group fragment.
//
// File layout once every group lands: this core IIFE, then one IIFE per
// group (flow, structure, planning, data) that destructures Render.diagram._
// and does Object.assign(Render.diagram, {...}). Merging fragments is a
// plain concatenation; nothing here should need to change for a group to
// land.
(() => {
  'use strict';

  const { esc } = window.Render;

  // -- budgets -------------------------------------------------------------
  // references/diagrams.md mirrors this table. Nested by
  // type so group builders never collide on a shared key name.
  const BUDGET = {
    dependency: { nodes: 9, edges: 12 },
    sequence: { lifelines: 5, messages: 12 },
    state: { states: 9, transitions: 12 },
    flowchart: { nodes: 9, edges: 12 },
    swimlane: { lanes: 5, steps: 9, edges: 12 },
    cycle: { stages: 6 },
    architecture: { zones: 4, components: 9, edges: 12 },
    er: { entities: 8, fields: 8, relations: 12 },
    containment: { boxes: 12, depth: 3 },
    gantt: { tasks: 12 },
    kanban: { columns: 5, cards: 6 },
    storymap: { activities: 6, releases: 3, stories: 4 },
    quadrant: { items: 12 },
    fishbone: { categories: 6, causes: 4 },
    waterfall: { steps: 8 },
    treemap: { cells: 8 },
    funnel: { stages: 6 },
    line: { series: 4, points: 12, slopeSeries: 8 },
  };

  // -- token reader ----------------------------------------------------------

  function px(name) {
    const raw = getComputedStyle(document.documentElement).getPropertyValue(name);
    const n = parseFloat(raw);
    if (Number.isNaN(n)) {
      console.warn(`[render diagram] token ${name} did not resolve to a length; using 8px.`);
      return 8;
    }
    return n;
  }

  function round(n) {
    return Math.round(n * 100) / 100;
  }

  function cssId(id) {
    return window.CSS?.escape ? CSS.escape(String(id)) : String(id).replace(/(["\\])/g, '\\$1');
  }

  // -- lifecycle -------------------------------------------------------------
  // frame() only registers a draw callback and schedules one rAF sweep; the
  // actual figures don't exist in the DOM yet (the caller's mount() still
  // has to write the returned markup into #root). By the time the sweep
  // runs, mount() has already run synchronously.

  const registry = new Map(); // dgId -> draw(fig)
  const wiredEls = new WeakSet();
  const pendingRaf = new WeakMap();
  let sweepScheduled = false;
  let figCounter = 0;

  function isVisible(el) {
    return Boolean(el.offsetParent || el.getClientRects().length);
  }

  function scheduleRedraw(el, run) {
    if (pendingRaf.has(el)) return;
    const id = requestAnimationFrame(() => {
      pendingRaf.delete(el);
      run();
    });
    pendingRaf.set(el, id);
  }

  function wireFigure(el) {
    const draw = registry.get(el.dataset.dg);
    if (!draw) return;
    wiredEls.add(el);
    const run = () => { if (isVisible(el)) draw(el); };
    if ('ResizeObserver' in window) {
      const ro = new ResizeObserver(() => scheduleRedraw(el, run));
      ro.observe(el.querySelector('.dg-canvas'));
      for (const n of el.querySelectorAll('.dg-node')) ro.observe(n);
    }
    document.fonts?.ready?.then(run);
    run();
  }

  function sweep() {
    sweepScheduled = false;
    for (const el of document.querySelectorAll('.dg[data-dg]')) {
      if (!wiredEls.has(el)) { wireFigure(el); continue; }
      if (isVisible(el)) {
        const draw = registry.get(el.dataset.dg);
        if (draw) scheduleRedraw(el, () => draw(el));
      }
    }
  }

  function scheduleSweep() {
    if (sweepScheduled) return;
    sweepScheduled = true;
    requestAnimationFrame(sweep);
  }

  // A hidden tab panel or disclosure can't be measured while display:none,
  // so a figure inside one is skipped at sweep time (isVisible above) and
  // only drawn once its ancestor's [hidden] is lifted. This one observer
  // covers every figure instead of each caller wiring its own.
  if (typeof MutationObserver !== 'undefined' && document.documentElement) {
    new MutationObserver(sweep).observe(document.documentElement, {
      attributes: true, attributeFilter: ['hidden'], subtree: true,
    });
  }

  // -- frame / fail / check ---------------------------------------------------

  // styleAttr is a caller-built literal, e.g. ` style="--cols:${n};--ranks:${m}"`,
  // never a generic {key: value} object: the gate scans this file's own JS
  // source text, and a runtime Object.entries().map().join() can never
  // produce a literal `--name:` prefix for it to see. Every call site below
  // writes its own fixed-shape template instead.
  function frame({ type, anchor, title = '', html = '', styleAttr = '', sr = '', dir, edges, draw }) {
    figCounter += 1;
    const dgId = `dg-${figCounter}`;
    const dirAttr = dir ? ` data-dir="${esc(dir)}"` : '';
    const edgesAttr = edges != null ? ` data-edges="${edges}"` : '';
    const cap = title ? `<figcaption class="dg-cap">${esc(title)}</figcaption>` : '';
    const srBlock = sr ? `<div class="dg-sr">${sr}</div>` : '';
    const markup = (
      `<figure class="dg dg-${esc(type)}" data-dg="${dgId}"${dirAttr}${edgesAttr}${styleAttr}>`
      + `<div class="dg-scroll"><div class="dg-canvas">${html}`
      + '<svg class="dg-wires" aria-hidden="true" focusable="false"></svg></div></div>'
      + `${cap}${srBlock}</figure>`
    );
    if (draw) registry.set(dgId, draw);
    scheduleSweep();
    return window.Render.anchored({ anchor, label: title || type, cls: 'dg-anchor', html: markup });
  }

  function fail(anchor, title, reason) {
    console.warn(`[render diagram] ${title || anchor}: ${reason}`);
    const html = (
      `<div class="empty"><p class="title">Not drawn: ${esc(title || anchor)}</p>`
      + `<p class="text">${esc(reason)}</p></div>`
    );
    return window.Render.anchored({ anchor, label: title || anchor, html });
  }

  // counts: plain numbers keyed like the type's BUDGET entry, plus an
  // optional `ids` array checked for duplicates regardless of type.
  function check(type, data, counts) {
    if (counts.ids) {
      const seen = new Set();
      for (const id of counts.ids) {
        if (seen.has(id)) return `Duplicate id "${id}". Every id in this diagram must be unique.`;
        seen.add(id);
      }
    }
    const budget = BUDGET[type] || {};
    for (const [key, n] of Object.entries(counts)) {
      if (key === 'ids') continue;
      const max = budget[key];
      if (max != null && n > max) {
        return `${n} ${key} passed, the limit is ${max}. Split this into smaller diagrams.`;
      }
    }
    return null;
  }

  // -- node ------------------------------------------------------------------

  // styleAttr: see the comment on frame() above; a caller-built literal
  // like ` style="--r:${p.rank};--c:${p.col}"`, not a {key: value} object.
  function node(n, extraCls = '', styleAttr = '') {
    const cls = ['dg-node', extraCls, n.key ? 'is-key' : '', n.sunk ? 'is-sunk' : '', n.soft ? 'is-soft' : '']
      .filter(Boolean).join(' ');
    const sub = n.sub ? `<span class="meta">${esc(n.sub)}</span>` : '';
    return `<div class="${cls}" data-id="${esc(n.id)}"${styleAttr}><span class="title">${esc(n.label)}</span>${sub}</div>`;
  }

  // -- layered layout ----------------------------------------------------------
  function layered(nodes, edges, opts = {}) {
    const ids = nodes.map((n) => n.id);
    const idSet = new Set(ids);
    const outEdges = new Map(ids.map((id) => [id, []]));
    const loops = [];
    const real = [];
    for (const e of edges) {
      if (e.from === e.to) { loops.push(e); continue; }
      if (!idSet.has(e.from) || !idSet.has(e.to)) continue; // callers refuse unknown ids before this point
      outEdges.get(e.from).push(e);
      real.push(e);
    }

    // 1. cycle breaking: DFS in input order, an edge into a GRAY node is back.
    const WHITE = 0; const GRAY = 1; const BLACK = 2;
    const color = new Map(ids.map((id) => [id, WHITE]));
    const forward = new Map(ids.map((id) => [id, []]));
    const back = new Set();
    function visit(id) {
      color.set(id, GRAY);
      for (const e of outEdges.get(id)) {
        const c = color.get(e.to);
        if (c === WHITE) { forward.get(id).push(e); visit(e.to); } else if (c === GRAY) { back.add(e); } else { forward.get(id).push(e); }
      }
      color.set(id, BLACK);
    }
    for (const id of ids) if (color.get(id) === WHITE) visit(id);

    // 2. rank by longest path (Kahn), forward edges only. opts.rank(id) can
    // pin a node's rank (architecture zones); pinned nodes are never raised.
    const pin = typeof opts.rank === 'function' ? opts.rank : null;
    const rank = new Map(ids.map((id) => [id, pin ? (pin(id) ?? 0) : 0]));
    const indeg = new Map(ids.map((id) => [id, 0]));
    for (const id of ids) for (const e of forward.get(id)) indeg.set(e.to, indeg.get(e.to) + 1);
    const queue = ids.filter((id) => indeg.get(id) === 0);
    while (queue.length) {
      const id = queue.shift();
      for (const e of forward.get(id)) {
        if (!pin || pin(e.to) == null) {
          const candidate = rank.get(id) + 1;
          if (candidate > rank.get(e.to)) rank.set(e.to, candidate);
        }
        indeg.set(e.to, indeg.get(e.to) - 1);
        if (indeg.get(e.to) === 0) queue.push(e.to);
      }
    }
    const maxRank = ids.length ? Math.max(...ids.map((id) => rank.get(id))) : 0;

    // 3. order within rank: 4 barycenter sweeps, stable sort.
    const byRank = Array.from({ length: maxRank + 1 }, () => []);
    for (const id of ids) byRank[rank.get(id)].push(id);
    const colIndex = new Map();
    function reindex() { for (const arr of byRank) arr.forEach((id, i) => colIndex.set(id, i)); }
    reindex();
    const parentsOf = new Map(ids.map((id) => [id, []]));
    const childrenOf = new Map(ids.map((id) => [id, []]));
    for (const id of ids) for (const e of forward.get(id)) { parentsOf.get(e.to).push(id); childrenOf.get(id).push(e.to); }
    function barycenter(id, neighborsOf) {
      const ns = neighborsOf.get(id);
      return ns.length ? ns.reduce((s, n) => s + colIndex.get(n), 0) / ns.length : colIndex.get(id);
    }
    function sweepPass(neighborsOf) {
      for (const arr of byRank) {
        const scored = arr.map((id, i) => [id, barycenter(id, neighborsOf), i]);
        scored.sort((a, b) => (a[1] - b[1]) || (a[2] - b[2]));
        arr.length = 0;
        for (const [id] of scored) arr.push(id);
      }
      reindex();
    }
    sweepPass(parentsOf); sweepPass(childrenOf); sweepPass(parentsOf); sweepPass(childrenOf);

    // 4. placement: parents' mean column, pushed right on collision, then a
    // backward pass compacts left again without crossing. ponytail: no
    // second desired-value recompute in the backward pass, just a squeeze;
    // good enough at this diagram's node counts (<=9), revisit if a real
    // page ever wants tighter packing.
    const col = new Map();
    for (const arr of byRank) {
      let prev = -1;
      for (const id of arr) {
        const parents = parentsOf.get(id);
        const desired = parents.length
          ? Math.round(parents.reduce((s, p) => s + col.get(p), 0) / parents.length)
          : colIndex.get(id);
        const placed = Math.max(desired, prev + 1);
        col.set(id, placed);
        prev = placed;
      }
      for (let i = arr.length - 2; i >= 0; i -= 1) {
        const next = col.get(arr[i + 1]);
        col.set(arr[i], Math.max(0, Math.min(col.get(arr[i]), next - 1)));
      }
    }
    const used = [...new Set(col.values())].sort((a, b) => a - b);
    const remap = new Map(used.map((c, i) => [c, i]));
    for (const id of ids) col.set(id, remap.get(col.get(id)));

    const pos = new Map(ids.map((id) => [id, { rank: rank.get(id), col: col.get(id) }]));

    // 5. critical path: from the deepest node, walk a forward predecessor
    // at each rank back to a source.
    let critical = null;
    if (opts.critical && ids.length) {
      const cNodes = new Set(); const cEdges = new Set();
      let current = ids.reduce((best, id) => (rank.get(id) > rank.get(best) ? id : best), ids[0]);
      cNodes.add(current);
      let guard = ids.length + 1;
      while (guard > 0) {
        guard -= 1;
        const incoming = real.filter((e) => e.to === current && !back.has(e) && rank.get(e.from) === rank.get(current) - 1);
        if (!incoming.length) break;
        const [e] = incoming;
        cEdges.add(e); cNodes.add(e.from); current = e.from;
      }
      critical = { nodes: cNodes, edges: cEdges };
    }

    return { rank, pos, ranks: maxRank + 1, cols: used.length, back, loops, critical };
  }

  // -- router / wires ----------------------------------------------------------

  // (a = rank axis, c = cross axis); TB maps a->y, c->x; LR maps a->x, c->y.
  function axes(box, dir) {
    return dir === 'LR'
      ? { a0: box.x, a1: box.x + box.w, c0: box.y, c1: box.y + box.h }
      : { a0: box.y, a1: box.y + box.h, c0: box.x, c1: box.x + box.w };
  }
  function pt(a, c, dir) {
    return dir === 'LR' ? { x: a, y: c } : { x: c, y: a };
  }

  function wires(fig) {
    const svg = fig.querySelector('.dg-wires');
    const canvas = fig.querySelector('.dg-canvas');

    function box(el) {
      const c = canvas.getBoundingClientRect();
      const r = el.getBoundingClientRect();
      return { x: r.left - c.left, y: r.top - c.top, w: r.width, h: r.height };
    }

    function clear() {
      svg.textContent = '';
      const w = canvas.scrollWidth || canvas.clientWidth || 1;
      const h = canvas.scrollHeight || canvas.clientHeight || 1;
      svg.setAttribute('viewBox', `0 0 ${w} ${h}`);
    }

    function pathFromPoints(points) {
      let d = `M ${round(points[0].x)} ${round(points[0].y)}`;
      for (let i = 1; i < points.length; i += 1) {
        const a = points[i - 1]; const b = points[i];
        if (Math.abs(b.x - a.x) < 0.1) d += ` V ${round(b.y)}`;
        else if (Math.abs(b.y - a.y) < 0.1) d += ` H ${round(b.x)}`;
        else d += ` L ${round(b.x)} ${round(b.y)}`;
      }
      return d;
    }

    function shorten(points, len) {
      if (points.length < 2 || len <= 0) return points;
      const out = points.slice();
      const a = out[out.length - 2]; const b = out[out.length - 1];
      const dx = b.x - a.x; const dy = b.y - a.y;
      const dist = Math.hypot(dx, dy) || 1;
      const t = Math.max(0, (dist - len) / dist);
      out[out.length - 1] = { x: a.x + dx * t, y: a.y + dy * t };
      return out;
    }

    function headMarkup(points, kind) {
      if (kind === 'none' || points.length < 2) return '';
      const a = points[points.length - 2]; const b = points[points.length - 1];
      const dx = Math.sign(b.x - a.x); const dy = Math.sign(b.y - a.y);
      const m = px('--marker');
      const back = dx !== 0 ? { x: b.x - dx * m, y: b.y } : { x: b.x, y: b.y - dy * m };
      if (kind === 'one') {
        return dx !== 0
          ? `<path class="dg-head is-one" d="M ${round(back.x)} ${round(back.y - m / 2)} V ${round(back.y + m / 2)}"/>`
          : `<path class="dg-head is-one" d="M ${round(back.x - m / 2)} ${round(back.y)} H ${round(back.x + m / 2)}"/>`;
      }
      if (kind === 'many') {
        const p1 = dx !== 0 ? { x: back.x, y: back.y - m * 0.6 } : { x: back.x - m * 0.6, y: back.y };
        const p2 = dx !== 0 ? { x: back.x, y: back.y + m * 0.6 } : { x: back.x + m * 0.6, y: back.y };
        return `<path class="dg-head is-many" d="M ${round(p1.x)} ${round(p1.y)} L ${round(b.x)} ${round(b.y)} `
          + `L ${round(p2.x)} ${round(p2.y)} M ${round(p1.x)} ${round(p1.y)} L ${round(p2.x)} ${round(p2.y)}"/>`;
      }
      const p1 = dx !== 0 ? { x: back.x, y: back.y - m * 0.5 } : { x: back.x - m * 0.5, y: back.y };
      const p2 = dx !== 0 ? { x: back.x, y: back.y + m * 0.5 } : { x: back.x + m * 0.5, y: back.y };
      return `<path class="dg-head" d="M ${round(b.x)} ${round(b.y)} L ${round(p1.x)} ${round(p1.y)} `
        + `L ${round(p2.x)} ${round(p2.y)} Z"/>`;
    }

    function longestSegment(points) {
      let best = { i: 1, len: -1 };
      for (let i = 1; i < points.length; i += 1) {
        const len = Math.hypot(points[i].x - points[i - 1].x, points[i].y - points[i - 1].y);
        if (len > best.len) best = { i, len };
      }
      const a = points[best.i - 1]; const b = points[best.i];
      return { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
    }

    function labelMarkup(points, text, labelAt) {
      if (!text) return '';
      const at = labelAt === 'source' ? points[0] : longestSegment(points);
      const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      t.setAttribute('class', 'dg-label-text');
      t.textContent = text;
      svg.appendChild(t);
      const bbox = t.getBBox();
      t.remove();
      const pad = px('--label-gap');
      const rx = at.x - bbox.width / 2 - pad / 2;
      const ry = at.y - bbox.height / 2 - pad / 4;
      return (
        `<rect class="dg-label" x="${round(rx)}" y="${round(ry)}" width="${round(bbox.width + pad)}" `
        + `height="${round(bbox.height + pad / 2)}"/>`
        + `<text class="dg-label-text" x="${round(at.x)}" y="${round(at.y)}" `
        + `dominant-baseline="central" text-anchor="middle">${esc(text)}</text>`
      );
    }

    function wire(points, opts = {}) {
      const kind = opts.head || 'arrow';
      const m = kind === 'none' ? 0 : px('--marker');
      const d = pathFromPoints(shorten(points, m));
      const cls = ['dg-edge', opts.key ? 'is-key' : '', opts.soft ? 'is-soft' : ''].filter(Boolean).join(' ');
      const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      g.setAttribute('class', cls);
      g.setAttribute('data-from', String(opts.from ?? ''));
      g.setAttribute('data-to', String(opts.to ?? ''));
      g.innerHTML = `<path class="dg-line" d="${d}"/>${headMarkup(points, kind)}${labelMarkup(points, opts.label, opts.labelAt)}`;
      svg.appendChild(g);
      return g;
    }

    return { svg, box, wire, clear };
  }

  // isLane: an edge that can't run straight down into the next rank without
  // crossing other ranks' node rows, so it takes a margin lane outside the
  // node grid instead of jogging through it (back edge, same-rank, or a
  // forward edge that skips a rank). Shared by route() and by a builder's
  // own --back/--loops styleAttr count, so the two never drift apart.
  function isLane(layout, e) {
    if (e.from === e.to) return false;
    const backSet = layout.back || new Set();
    if (backSet.has(e)) return true;
    return layout.rank.get(e.to) - layout.rank.get(e.from) !== 1;
  }
  function laneEdges(layout, edges) {
    return edges.filter((e) => isLane(layout, e));
  }

  // forwardChannels: adjacent-rank edges grouped by the rank they leave,
  // i.e. the ones route() jogs through the channel rather than lanes
  // around. Exposed so a builder can size --tracks itself (see channelStats)
  // without recomputing this grouping.
  function forwardChannels(layout, edges) {
    const groups = new Map();
    for (const e of edges) {
      if (isLane(layout, e)) continue;
      const key = layout.rank.get(e.from);
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(e);
    }
    return groups;
  }

  // channelStats: the --tracks/--labeled pair diagrams.css turns into the
  // rank gap (see its --channel-gap). Only valid for a layered()+route()
  // figure; a builder with its own layout computes the equivalent itself
  // (max wires sharing one rank-to-rank band, and whether any of them carry
  // a label) and writes --tracks/--labeled the same way in its own
  // styleAttr.
  //
  // A lane edge (route()'s margin path) steps into this same channel band
  // on both ends before it crosses to the margin (R2), and a labelled step
  // needs full label-height room there (laneBand(e)), not just a --route
  // slot — room forwardChannels() never asks for, since it excludes lane
  // edges entirely. Treating a labelled lane as needing its own track slot
  // folds that into the shared formula instead of adding a second one.
  function channelStats(layout, edges) {
    const groups = forwardChannels(layout, edges);
    let tracks = 0;
    for (const g of groups.values()) tracks = Math.max(tracks, g.length);
    if (laneEdges(layout, edges).some((e) => e.label)) tracks = Math.max(tracks, 2);
    const labeled = edges.some((e) => e.from !== e.to && e.label) ? 1 : 0;
    return { tracks, labeled };
  }

  // laneBand: how much room one lane edge needs, cumulative from the grid
  // edge outward — big enough for a --route run off the port on one end and
  // a --marker + --route arrowhead run on the other, or (when the edge is
  // labelled) the same line-height-plus-clearance the channel-gap formula
  // in diagrams.css uses, whichever is larger. Lanes are drawn in order, so
  // the Nth lane's actual distance from the grid is the sum of the first N
  // bands — always >= its own band, so this is a sufficient (if sometimes
  // generous) per-lane reservation, not a tight one.
  function laneBand(e) {
    const base = px('--route') + px('--marker');
    if (!e.label) return base;
    return Math.max(base, px('--text') * px('--leading-tight') + 2 * px('--label-gap'));
  }

  // laneReserve: total lane space a figure's CSS must reserve, in --route
  // units (so `calc(var(--back) * var(--route))` — already in
  // diagrams.css — comes out to the exact pixel sum route() will actually
  // use). A builder with its own layout mirrors this in its own --back.
  function laneReserve(layout, edges) {
    const routeGap = px('--route') || 1;
    const total = laneEdges(layout, edges).reduce((sum, e) => sum + laneBand(e), 0);
    return round(total / routeGap);
  }

  // route(): drives wires() from a layered() layout. `port(edge, end)` (end
  // is 'from'|'to') can return { frac } to pin a port instead of fanning it,
  // e.g. ER lining a relation up with its field row.
  function route(fig, layout, edges, opts = {}) {
    const dir = opts.dir === 'LR' ? 'LR' : 'TB';
    const portOverride = typeof opts.port === 'function' ? opts.port : null;
    const w = wires(fig);
    w.clear();

    const boxes = new Map();
    for (const el of fig.querySelectorAll('.dg-node[data-id]')) boxes.set(el.dataset.id, w.box(el));
    // The margin lanes' baseline is the grid's own content edge (the
    // nearest/widest node's near/far side on the cross axis), not the
    // canvas element's border box: that box already includes the padding
    // CSS reserved for these lanes (--back(-start) * --route, see
    // diagrams.css), so measuring from it would double that reservation
    // and push lanes straight through it.
    const gridEdge = boxes.size
      ? Math.max(...[...boxes.values()].map((b) => axes(b, dir).c1))
      : axes(w.box(fig.querySelector('.dg-canvas')), dir).c1;

    const real = edges.filter((e) => e.from !== e.to);
    const loopEdges = edges.filter((e) => e.from === e.to);
    const lanes = new Set(laneEdges(layout, real));

    // Every edge attaches to a node on one of two physical sides: its
    // rank-axis "a1" side (a regular forward edge's own exit, and a
    // forward lane's exit / a backward lane's entry) or its "a0" side (a
    // regular forward edge's entry, and the reverse for lanes). Two edges
    // sharing a (node, side) must fan across it together regardless of
    // whether either one is a lane — a lane's initial hop leaves via the
    // exact same side a regular edge does (R3: two independent fans that
    // both default a lone member to the centre collide there).
    const sideGroups = new Map();
    function sideKey(id, side) { return `${id}|${side}`; }
    function addSide(id, side, e) {
      const k = sideKey(id, side);
      if (!sideGroups.has(k)) sideGroups.set(k, []);
      sideGroups.get(k).push(e);
    }
    for (const e of real) {
      const forward = lanes.has(e) ? layout.rank.get(e.to) > layout.rank.get(e.from) : true;
      addSide(e.from, forward ? 'a1' : 'a0', e);
      addSide(e.to, forward ? 'a0' : 'a1', e);
    }
    function sideFrac(id, side, e) {
      const group = sideGroups.get(sideKey(id, side)) || [e];
      const otherOf = (edge) => (edge.from === id ? edge.to : edge.from);
      const sorted = [...group].sort((a, b) => (
        (layout.pos.get(otherOf(a))?.col ?? 0) - (layout.pos.get(otherOf(b))?.col ?? 0)
      ));
      const i = Math.max(0, sorted.indexOf(e));
      return (i + 1) / (sorted.length + 1);
    }

    const routeGap = px('--route');
    let laneOffset = 0;
    let drawn = 0;

    // Track colouring for the forward case: every non-straight edge leaving
    // the same rank shares a channel, so give each one a distinct mid-jog
    // offset instead of stacking them on one line (a greedy index, not a
    // real interval-graph colouring; the small budgets here never need more).
    const channelGroups = forwardChannels(layout, real);

    for (const e of real) {
      const fromBox = boxes.get(e.from); const toBox = boxes.get(e.to);
      if (!fromBox || !toBox) continue;
      const fromA = axes(fromBox, dir); const toA = axes(toBox, dir);
      let points;

      if (lanes.has(e)) {
        // A lane edge must never cut sideways through the row it leaves or
        // enters (R2): step into the empty rank-gap band first (clearing
        // every sibling in that row, since grid items stretch to a shared
        // row height), only then cross to the margin lane and back. `step`
        // reuses laneBand's route+marker/label sizing so this hop is itself
        // never a too-short run (R5) or a too-tight label seam (R4).
        const forward = layout.rank.get(e.to) > layout.rank.get(e.from);
        const sign = forward ? 1 : -1;
        const exitA = forward ? fromA.a1 : fromA.a0;
        const enterA = forward ? toA.a0 : toA.a1;
        const step = laneBand(e);
        laneOffset += laneBand(e);
        const laneCross = gridEdge + laneOffset;
        const cf = portOverride?.(e, 'from')?.frac ?? sideFrac(e.from, forward ? 'a1' : 'a0', e);
        const ct = portOverride?.(e, 'to')?.frac ?? sideFrac(e.to, forward ? 'a0' : 'a1', e);
        const c1 = fromA.c0 + (fromA.c1 - fromA.c0) * cf;
        const c2 = toA.c0 + (toA.c1 - toA.c0) * ct;
        points = [
          pt(exitA, c1, dir),
          pt(exitA + sign * step, c1, dir),
          pt(exitA + sign * step, laneCross, dir),
          pt(enterA - sign * step, laneCross, dir),
          pt(enterA - sign * step, c2, dir),
          pt(enterA, c2, dir),
        ];
      } else {
        const f1 = portOverride?.(e, 'from') ?? { frac: sideFrac(e.from, 'a1', e) };
        const f2 = portOverride?.(e, 'to') ?? { frac: sideFrac(e.to, 'a0', e) };
        const c1 = fromA.c0 + (fromA.c1 - fromA.c0) * f1.frac;
        const c2 = toA.c0 + (toA.c1 - toA.c0) * f2.frac;
        const p1 = pt(fromA.a1, c1, dir); const p2 = pt(toA.a0, c2, dir);
        if (Math.abs(c1 - c2) < routeGap / 2) {
          // Ports close enough that a jog would draw a sub-route/2 sliver
          // (R5): snap to one cross position so the line stays a single
          // straight orthogonal segment instead of a near-invisible dogleg.
          points = [pt(fromA.a1, c1, dir), pt(toA.a0, c1, dir)];
        } else {
          const group = channelGroups.get(layout.rank.get(e.from)) || [e];
          const step = (toA.a0 - fromA.a1) / (group.length + 1);
          const mid = fromA.a1 + step * (group.indexOf(e) + 1);
          points = [p1, pt(mid, c1, dir), pt(mid, c2, dir), p2];
        }
      }

      w.wire(points, {
        from: e.from, to: e.to, key: Boolean(layout.critical?.edges.has(e)), soft: Boolean(e.soft),
        head: e.end === 'one' || e.end === 'many' || e.end === 'none' ? e.end : 'arrow',
        label: e.label, labelAt: e.labelAt,
      });
      drawn += 1;
    }

    for (const e of loopEdges) {
      const box = boxes.get(e.from);
      if (!box) continue;
      const a = axes(box, dir);
      const c1 = a.c0 + (a.c1 - a.c0) * 0.3; const c2 = a.c0 + (a.c1 - a.c0) * 0.7;
      const out = a.a1 + routeGap * 2;
      w.wire([pt(a.a1, c1, dir), pt(out, c1, dir), pt(out, c2, dir), pt(a.a1, c2, dir)], {
        from: e.from, to: e.to, key: Boolean(e.key), soft: Boolean(e.soft), label: e.label, head: 'arrow',
      });
      drawn += 1;
    }

    fig.dataset.dgEdges = String(drawn);
    return drawn;
  }

  // -- squarify / scale / ticks / days / nudge / thin -----------------------

  function squarify(values, w, h) {
    const total = values.reduce((s, v) => s + v, 0);
    const scaleF = (w * h) / (total || 1);
    const items = values.map((v, i) => ({ v, i, area: v * scaleF })).sort((a, b) => b.v - a.v);
    const rects = new Array(values.length);

    function worst(row, length) {
      const sum = row.reduce((s, r) => s + r.area, 0);
      const maxA = Math.max(...row.map((r) => r.area));
      const minA = Math.min(...row.map((r) => r.area));
      return Math.max((length * length * maxA) / (sum * sum), (sum * sum) / (length * length * minA));
    }
    function layoutRow(row, x, y, length, horizontal) {
      const sum = row.reduce((s, r) => s + r.area, 0);
      const thickness = length ? sum / length : 0;
      let pos = 0;
      for (const item of row) {
        const extent = thickness ? item.area / thickness : 0;
        rects[item.i] = horizontal
          ? { x, y: y + pos, w: thickness, h: extent }
          : { x: x + pos, y, w: extent, h: thickness };
        pos += extent;
      }
      return thickness;
    }

    let remaining = items.slice();
    let x = 0; let y = 0; let width = w; let height = h;
    while (remaining.length) {
      const horizontal = width >= height;
      const length = horizontal ? height : width;
      let row = [remaining[0]];
      let i = 0;
      while (i + 1 < remaining.length) {
        const next = remaining[i + 1];
        if (worst([...row, next], length) <= worst(row, length)) { row.push(next); i += 1; } else break;
      }
      const thickness = layoutRow(row, x, y, length, horizontal);
      if (horizontal) { x += thickness; width -= thickness; } else { y += thickness; height -= thickness; }
      remaining = remaining.slice(row.length);
    }
    return rects;
  }

  function scale(d0, d1) {
    const span = d1 - d0 || 1;
    return (v) => (v - d0) / span;
  }

  function niceNum(range, round1) {
    if (range <= 0) return 1;
    const exp = Math.floor(Math.log10(range));
    const frac = range / 10 ** exp;
    let niceFrac;
    if (round1) niceFrac = frac < 1.5 ? 1 : frac < 3 ? 2 : frac < 7 ? 5 : 10;
    else niceFrac = frac <= 1 ? 1 : frac <= 2 ? 2 : frac <= 5 ? 5 : 10;
    return niceFrac * 10 ** exp;
  }

  function ticks(min, max, n = 5) {
    const lo = Math.min(0, min); const hi = Math.max(0, max);
    if (lo === hi) return [lo];
    const step = niceNum(niceNum(hi - lo, false) / Math.max(1, n - 1), true);
    const niceMin = Math.floor(lo / step) * step;
    const niceMax = Math.ceil(hi / step) * step;
    const out = [];
    for (let v = niceMin; v <= niceMax + step / 2; v += step) out.push(Number((Math.round(v / step) * step).toFixed(10)));
    return out;
  }

  function days(iso) {
    return Math.round(Date.parse(`${iso}T00:00:00Z`) / 86400000);
  }

  function nudge(els, axis = 'y') {
    const minGap = px('--fan') || 8;
    const items = [...els].map((el) => ({ el, box: el.getBoundingClientRect() }))
      .sort((a, b) => (axis === 'y' ? a.box.top - b.box.top : a.box.left - b.box.left));
    let prevEdge = -Infinity;
    for (const it of items) {
      const start = axis === 'y' ? it.box.top : it.box.left;
      const size = axis === 'y' ? it.box.height : it.box.width;
      const dy = start < prevEdge + minGap ? prevEdge + minGap - start : 0;
      it.el.style.setProperty('--dy', String(Math.round(dy)));
      prevEdge = start + dy + size;
    }
  }

  function thin(els) {
    let prevRight = -Infinity;
    for (const el of els) {
      el.hidden = false;
      const box = el.getBoundingClientRect();
      if (box.left < prevRight) { el.hidden = true; continue; }
      prevRight = box.right;
    }
  }

  // -- dependency (the old .graph, replaced) -----------------------------------

  function dependency(data = {}) {
    const { anchor, title = '', nodes = [], edges = [], dir = 'TB', critical = false } = data;
    const ids = nodes.map((n) => n.id);
    const reason = check('dependency', data, { nodes: nodes.length, edges: edges.length, ids });
    if (reason) return fail(anchor, title, reason);
    const idSet = new Set(ids);
    const unknown = edges.find((e) => !idSet.has(e.from) || !idSet.has(e.to));
    if (unknown) return fail(anchor, title, `Edge references an unknown id ("${unknown.from}" -> "${unknown.to}"). Fix the id and try again.`);

    const layout = layered(nodes, edges, { dir, critical });
    const laneRoom = laneReserve(layout, edges);
    const { tracks, labeled } = channelStats(layout, edges);

    const nodesHtml = nodes.map((n) => {
      const p = layout.pos.get(n.id);
      const isCrit = layout.critical?.nodes.has(n.id);
      return node(n, isCrit ? 'is-key' : '', ` style="--r:${p.rank + 1};--c:${p.col + 1}"`);
    }).join('');

    const cycleNote = layout.back.size
      ? `<p>Cycle: ${esc([...layout.back].map((e) => `${e.from} → ${e.to}`).join(', '))}.</p>` : '';
    const srItems = edges.map((e) => (
      `<li>${esc(e.from)} → ${esc(e.to)}${e.label ? `: ${esc(e.label)}` : ''}${e.soft ? ' (soft)' : ''}</li>`
    )).join('');
    const sr = `<ul>${srItems}</ul>${cycleNote}`;

    return frame({
      type: 'dependency',
      anchor,
      title,
      dir,
      edges: edges.length,
      styleAttr: ` style="--cols:${layout.cols};--ranks:${layout.ranks};--back:${laneRoom};--loops:${layout.loops.length ? 1 : 0};--tracks:${tracks};--labeled:${labeled}"`,
      html: nodesHtml,
      sr,
      draw(fig) { route(fig, layout, edges, { dir }); },
    });
  }

  window.Render = window.Render || {};
  window.Render.diagram = {
    dependency,
    _: Object.freeze({
      BUDGET, px, round, cssId, frame, fail, check, node, layered, route, wires,
      isLane, laneEdges, forwardChannels, channelStats, laneBand, laneReserve,
      squarify, scale, ticks, days, nudge, thin,
    }),
  };
})();

// Flow and behavior: sequence, state, flowchart, swimlane, cycle.
(() => {
  'use strict';

  const { esc } = window.Render;
  const {
    frame, fail, check, node, layered, route, wires,
    channelStats, laneReserve, px, cssId,
  } = window.Render.diagram._;

  // -- sequence ----------------------------------------------------------
  // Custom layout: not layered()/route() (a lifeline isn't a rank/column
  // grid). Participant heads reuse node() in row 1 (grid-column ~= --n,
  // read by core's own .dg-canvas rule via --cols); each message is its own
  // full-width row below it. Lifelines and arrows are drawn straight into
  // wires(fig).svg rather than through dg-edge for the lifelines (a
  // lifeline is not an edge: it has no from/to pair and must never count
  // against frame()'s declared `edges`), and through wires().wire() for the
  // actual messages, whose real endpoint is a point on the lifeline, not
  // the participant head box up in row 1 — so each message edge carries
  // data-from-el/data-to-el pointing at the lifeline.

  function sequence(data = {}) {
    const { anchor, title = '', participants = [], messages = [] } = data;
    const ids = participants.map((p) => p.id);
    const reason = check('sequence', data, { lifelines: participants.length, messages: messages.length, ids });
    if (reason) return fail(anchor, title, reason);
    if (!messages.length) return fail(anchor, title, 'No messages passed. A sequence needs at least one.');
    const idSet = new Set(ids);
    const unknown = messages.find((m) => !idSet.has(m.from) || !idSet.has(m.to));
    if (unknown) return fail(anchor, title, `Message references an unknown participant ("${unknown.from}" -> "${unknown.to}"). Fix the id and try again.`);

    const headsHtml = participants.map((p, i) => node(p, '', ` style="--r:1;--c:${i + 1}"`)).join('');
    const msgHtml = messages.map((m, i) => (
      `<div class="dg-msg" data-id="dg-msg-${i}" style="--r:${i + 2}">`
      + `<span class="dg-msg-n">${i + 1}</span><span class="dg-msg-label${m.soft ? ' is-soft' : ''}${m.key ? ' is-key' : ''}">${esc(m.label || '')}</span>`
      + '</div>'
    )).join('');

    const byId = new Map(participants.map((p) => [p.id, p]));
    const srItems = messages.map((m) => (
      `<li>${esc(byId.get(m.from).label)} → ${esc(byId.get(m.to).label)}: ${esc(m.label || '')}</li>`
    )).join('');

    return frame({
      type: 'sequence',
      anchor,
      title,
      edges: messages.length,
      styleAttr: ` style="--cols:${participants.length}"`,
      html: headsHtml + msgHtml,
      sr: `<ol>${srItems}</ol>`,
      draw(fig) {
        const w = wires(fig);
        w.clear();
        const headBoxes = participants.map((p) => w.box(fig.querySelector(`.dg-node[data-id="${cssId(p.id)}"]`)));
        const rowEls = messages.map((_, i) => fig.querySelector(`[data-id="dg-msg-${i}"]`)).filter(Boolean);
        if (!rowEls.length) return;
        const lastRow = w.box(rowEls[rowEls.length - 1]);
        const lifelineBottom = lastRow.y + lastRow.h;
        // Lifelines are drawn directly, not through wires().wire(): they
        // carry no from/to pair and must never be counted as a dg-edge (the
        // declared `edges` count above is messages.length, not messages +
        // participants).
        participants.forEach((p, i) => {
          const box = headBoxes[i];
          const x = round2(box.x + box.w / 2);
          const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
          path.setAttribute('class', 'dg-lifeline');
          path.setAttribute('data-lifeline', p.id);
          path.setAttribute('d', `M ${x} ${round2(box.y + box.h)} V ${round2(lifelineBottom)}`);
          w.svg.appendChild(path);
        });

        const loopW = px('--route') * 2;
        let drawn = 0;
        messages.forEach((m, i) => {
          const rowBox = w.box(rowEls[i]);
          const fromIdx = participants.findIndex((p) => p.id === m.from);
          const toIdx = participants.findIndex((p) => p.id === m.to);
          const fromX = round2(headBoxes[fromIdx].x + headBoxes[fromIdx].w / 2);
          const toX = round2(headBoxes[toIdx].x + headBoxes[toIdx].w / 2);
          const y = round2(rowBox.y + rowBox.h);
          let points;
          if (m.from === m.to) {
            const yTop = round2(y - px('--route') * 2);
            points = [{ x: fromX, y: yTop }, { x: fromX + loopW, y: yTop }, { x: fromX + loopW, y }, { x: fromX, y }];
          } else {
            points = [{ x: fromX, y }, { x: toX, y }];
          }
          const g = w.wire(points, { from: m.from, to: m.to, key: Boolean(m.key), soft: Boolean(m.soft), head: 'arrow' });
          g.setAttribute('data-from-el', `[data-lifeline="${cssId(m.from)}"]`);
          g.setAttribute('data-to-el', `[data-lifeline="${cssId(m.to)}"]`);
          drawn += 1;
        });
        fig.dataset.dgEdges = String(drawn);
      },
    });
  }

  function round2(n) { return Math.round(n * 100) / 100; }

  // -- state ---------------------------------------------------------------
  // A layered()/route() type, same shape as dependency; the only additions
  // are the initial-marker and final-double-rule encodings (pure CSS,
  // driven by the is-initial/is-final classes below).

  function state(data = {}) {
    const { anchor, title = '', states = [], transitions = [], dir = 'TB' } = data;
    const ids = states.map((s) => s.id);
    const reason = check('state', data, { states: states.length, transitions: transitions.length, ids });
    if (reason) return fail(anchor, title, reason);
    const idSet = new Set(ids);
    const unknown = transitions.find((t) => !idSet.has(t.from) || !idSet.has(t.to));
    if (unknown) return fail(anchor, title, `Transition references an unknown id ("${unknown.from}" -> "${unknown.to}"). Fix the id and try again.`);
    const unlabeled = transitions.find((t) => !t.label);
    if (unlabeled) return fail(anchor, title, `Transition "${unlabeled.from}" -> "${unlabeled.to}" has no label. Name the event that triggers it.`);
    const initials = states.filter((s) => s.initial);
    if (initials.length > 1) return fail(anchor, title, `${initials.length} initial states declared. A state machine starts in exactly one place.`);

    const layout = layered(states, transitions, { dir });
    const laneRoom = laneReserve(layout, transitions);
    const { tracks, labeled } = channelStats(layout, transitions);

    const nodesHtml = states.map((s) => {
      const p = layout.pos.get(s.id);
      const extra = [s.initial ? 'is-initial' : '', s.final ? 'is-final' : ''].filter(Boolean).join(' ');
      return node(s, extra, ` style="--r:${p.rank + 1};--c:${p.col + 1}"`);
    }).join('');

    const initialNote = initials[0] ? `<p>Initial: ${esc(initials[0].label)}.</p>` : '';
    const srItems = transitions.map((t) => (
      `<li>${esc(t.from)} → ${esc(t.to)} on ${esc(t.label)}</li>`
    )).join('');

    return frame({
      type: 'state',
      anchor,
      title,
      dir,
      edges: transitions.length,
      styleAttr: ` style="--cols:${layout.cols};--ranks:${layout.ranks};--back:${laneRoom};--loops:${layout.loops.length ? 1 : 0};--tracks:${tracks};--labeled:${labeled}"`,
      html: nodesHtml,
      sr: `${initialNote}<ul>${srItems}</ul>`,
      draw(fig) { route(fig, layout, transitions, { dir }); },
    });
  }

  // -- flowchart -------------------------------------------------------------
  // Also layered()/route(); the honesty rule is the decision-branch check,
  // and the visual encoding is a double border (decision) / sunk fill
  // (terminal), both pure CSS on classes derived from `kind`.

  function flowchart(data = {}) {
    const { anchor, title = '', nodes = [], edges = [], dir = 'TB' } = data;
    const ids = nodes.map((n) => n.id);
    const reason = check('flowchart', data, { nodes: nodes.length, edges: edges.length, ids });
    if (reason) return fail(anchor, title, reason);
    const idSet = new Set(ids);
    const unknown = edges.find((e) => !idSet.has(e.from) || !idSet.has(e.to));
    if (unknown) return fail(anchor, title, `Edge references an unknown id ("${unknown.from}" -> "${unknown.to}"). Fix the id and try again.`);
    const outOf = new Map(ids.map((id) => [id, []]));
    for (const e of edges) outOf.get(e.from)?.push(e);
    const badDecision = nodes.find((n) => {
      if (n.kind !== 'decision') return false;
      const out = outOf.get(n.id) || [];
      return out.length < 2 || out.some((e) => !e.label);
    });
    if (badDecision) return fail(anchor, title, `Decision "${badDecision.label}" needs at least 2 labeled outgoing edges (its branch names).`);

    const layout = layered(nodes, edges, { dir });
    const laneRoom = laneReserve(layout, edges);
    const { tracks, labeled } = channelStats(layout, edges);

    const nodesHtml = nodes.map((n) => {
      const p = layout.pos.get(n.id);
      const extra = n.kind === 'decision' ? 'is-decision' : n.kind === 'terminal' ? 'is-sunk' : '';
      return node(n, extra, ` style="--r:${p.rank + 1};--c:${p.col + 1}"`);
    }).join('');

    const srItems = edges.map((e) => (
      `<li>${esc(e.from)} → ${esc(e.to)}${e.label ? `: ${esc(e.label)}` : ''}</li>`
    )).join('');

    return frame({
      type: 'flowchart',
      anchor,
      title,
      dir,
      edges: edges.length,
      styleAttr: ` style="--cols:${layout.cols};--ranks:${layout.ranks};--back:${laneRoom};--loops:${layout.loops.length ? 1 : 0};--tracks:${tracks};--labeled:${labeled}"`,
      html: nodesHtml,
      sr: `<ul>${srItems}</ul>`,
      draw(fig) { route(fig, layout, edges, { dir }); },
    });
  }

  // -- swimlane --------------------------------------------------------------
  // Lanes are fixed rows (never barycenter-ordered), so this can't go
  // through layered()'s own column placement. It still reuses layered()
  // for its longest-path rank and cycle-breaking, then re-ranks so no two
  // steps in the same lane share a rank (the later one, and everything it
  // reaches, moves right — see resolveLanes below), and finally reuses
  // route() itself by handing it a layout shaped exactly like layered()
  // returns, with `pos.col` set to the lane index and dir:'LR' so rank ==
  // the horizontal axis, lane == the vertical one. A --lane-head column is
  // the only thing route()/its CSS doesn't already know about.

  function resolveLanes(steps, edges, laneIndexOf) {
    const ids = steps.map((s) => s.id);
    const laneOfStep = new Map(steps.map((s) => [s.id, laneIndexOf.get(s.lane)]));
    const base = layered(steps, edges, {});
    const rank = new Map(base.rank);
    const childrenOf = new Map(ids.map((id) => [id, []]));
    for (const e of edges) if (e.from !== e.to) childrenOf.get(e.from)?.push(e.to);
    function bump(id, minRank, guard) {
      if (guard <= 0 || rank.get(id) >= minRank) return;
      rank.set(id, minRank);
      for (const child of childrenOf.get(id) || []) bump(child, minRank + 1, guard - 1);
    }
    const occupied = new Set();
    // ponytail: one forward pass, no re-check after a bump moves a step
    // into a rank its own lane already occupies. Fine at this diagram's
    // budget (<=9 steps); a real collision cascade would need a second
    // pass, add one if a real page ever needs it.
    for (const id of [...ids].sort((a, b) => rank.get(a) - rank.get(b))) {
      const lane = laneOfStep.get(id);
      let r = rank.get(id);
      while (occupied.has(`${lane}|${r}`)) r += 1;
      if (r !== rank.get(id)) bump(id, r, ids.length + 1);
      occupied.add(`${lane}|${rank.get(id)}`);
    }
    const maxRank = ids.length ? Math.max(...ids.map((id) => rank.get(id))) : 0;
    const pos = new Map(ids.map((id) => [id, { rank: rank.get(id), col: laneOfStep.get(id) }]));
    return { rank, pos, ranks: maxRank + 1, back: base.back, loops: base.loops, critical: null };
  }

  function swimlane(data = {}) {
    const { anchor, title = '', lanes = [], steps = [], edges = [] } = data;
    const ids = steps.map((s) => s.id);
    const reason = check('swimlane', data, { lanes: lanes.length, steps: steps.length, edges: edges.length, ids });
    if (reason) return fail(anchor, title, reason);
    const laneIds = new Set(lanes.map((l) => l.id));
    const badLane = steps.find((s) => !laneIds.has(s.lane));
    if (badLane) return fail(anchor, title, `Step "${badLane.label}" names an unknown lane ("${badLane.lane}"). Add it to lanes or fix the id.`);
    const used = new Set(steps.map((s) => s.lane));
    const emptyLane = lanes.find((l) => !used.has(l.id));
    if (emptyLane) return fail(anchor, title, `Lane "${emptyLane.label}" has no steps. Remove it or give it work.`);
    const idSet = new Set(ids);
    const unknown = edges.find((e) => !idSet.has(e.from) || !idSet.has(e.to));
    if (unknown) return fail(anchor, title, `Edge references an unknown step id ("${unknown.from}" -> "${unknown.to}"). Fix the id and try again.`);

    const laneIndexOf = new Map(lanes.map((l, i) => [l.id, i]));
    const layout = resolveLanes(steps, edges, laneIndexOf);
    layout.cols = lanes.length;
    const laneRoom = laneReserve(layout, edges);
    const { tracks, labeled } = channelStats(layout, edges);

    const headsHtml = lanes.map((l, i) => (
      `<div class="dg-lane-head" style="--c:${i + 1}"><span class="title">${esc(l.label)}</span></div>`
    )).join('');
    const stepsHtml = steps.map((s) => {
      const p = layout.pos.get(s.id);
      return node(s, '', ` style="--r:${p.rank + 2};--c:${p.col + 1}"`);
    }).join('');

    const laneOf = new Map(steps.map((s) => [s.id, s.lane]));
    const srItems = edges.map((e) => (
      `<li>${esc(e.from)} → ${esc(e.to)}${laneOf.get(e.from) !== laneOf.get(e.to) ? ' (handoff)' : ''}</li>`
    )).join('');

    return frame({
      type: 'swimlane',
      anchor,
      title,
      dir: 'LR',
      edges: edges.length,
      styleAttr: ` style="--cols:${layout.cols};--ranks:${layout.ranks};--back:${laneRoom};--loops:${layout.loops.length ? 1 : 0};--tracks:${tracks};--labeled:${labeled}"`,
      html: headsHtml + stepsHtml,
      sr: `<ul>${srItems}</ul>`,
      draw(fig) { route(fig, layout, edges, { dir: 'LR' }); },
    });
  }

  // -- cycle -------------------------------------------------------------
  // Custom layout: 2 rows, clockwise. Every consecutive pair is either
  // same-row-adjacent (a straight horizontal run) or a row change (a
  // one-elbow V-H-V through the row-gap band); nothing here is a diagonal.

  function cycle(data = {}) {
    const { anchor, title = '', stages = [], center } = data;
    const reason = check('cycle', data, { stages: stages.length });
    if (reason) return fail(anchor, title, reason);
    if (stages.length < 3) return fail(anchor, title, `${stages.length} stages passed; a cycle needs at least 3.`);

    const n = stages.length;
    const topCount = Math.ceil(n / 2);
    const rowOf = (i) => (i < topCount ? 0 : 1);
    const colOf = (i) => (i < topCount ? i : topCount - 1 - (i - topCount));

    const nodesHtml = stages.map((s, i) => node(
      { ...s, id: s.id ?? `stage-${i}` }, '', ` style="--r:${rowOf(i) + 1};--c:${colOf(i) + 1}"`,
    )).join('');
    const centerHtml = center ? `<div class="dg-cycle-center">${esc(center)}</div>` : '';

    const srItems = stages.map((s, i) => `<li>${esc(s.label)} → ${esc(stages[(i + 1) % n].label)}</li>`).join('');

    return frame({
      type: 'cycle',
      anchor,
      title,
      edges: n,
      styleAttr: ` style="--cols:${topCount}"`,
      html: nodesHtml + centerHtml,
      sr: `<ol>${srItems}</ol>${center ? `<p>${esc(center)}</p>` : ''}`,
      draw(fig) {
        const w = wires(fig);
        w.clear();
        const boxes = stages.map((_, i) => w.box(fig.querySelectorAll('.dg-node')[i]));
        const topBox = boxes[0]; // stage 0 is always top row (topCount = ceil(n/2) >= 1)
        const bottomIdx = stages.findIndex((_, i) => rowOf(i) === 1); // always found: n >= 3
        const gapMid = round2((topBox.y + topBox.h + boxes[bottomIdx].y) / 2);

        function anchorY(box, row) { return row === 0 ? box.y + box.h : box.y; }
        // n === 3 puts a single stage on the short row, so that one stage
        // is both the down-transition's entry and the wrap-transition's
        // exit, on the very same (top) side. Anchoring "exit" and "enter"
        // at two different fractions across the side keeps those two
        // segments --route/2 apart (R3) instead of stacking on the node's
        // centre; every other stage only ever plays one role, so the same
        // offset there is just a harmless few-px nudge off centre.
        function anchorX(box, role) { return box.x + box.w * (role === 'exit' ? 0.35 : 0.65); }
        function dedupe(pts) {
          return pts.filter((p, i) => i === 0 || Math.hypot(p.x - pts[i - 1].x, p.y - pts[i - 1].y) > 0.5);
        }
        const routeGap = px('--route');

        // Walking a 2-row cycle clockwise crosses rows exactly twice (the
        // down-transition and the wrap-back-to-start), regardless of n. Both
        // would otherwise jog through the same y = gapMid and register as a
        // 0-gap parallel pair (R3) wherever their horizontal runs meet or
        // pass close together; staggering the two crossings to their own
        // level, --route apart, keeps them on separate lines instead.
        let crossingsSeen = 0;
        let drawn = 0;
        for (let i = 0; i < n; i += 1) {
          const j = (i + 1) % n;
          const a = boxes[i]; const b = boxes[j];
          const rowA = rowOf(i); const rowB = rowOf(j);
          let points;
          if (rowA === rowB) {
            const y = round2(a.y + a.h / 2);
            const goingRight = b.x > a.x;
            points = [
              { x: round2(goingRight ? a.x + a.w : a.x), y },
              { x: round2(goingRight ? b.x : b.x + b.w), y },
            ];
          } else {
            const level = round2(gapMid + (crossingsSeen === 0 ? -routeGap : routeGap));
            crossingsSeen += 1;
            const ax = round2(anchorX(a, 'exit')); const bx = round2(anchorX(b, 'enter'));
            points = dedupe([
              { x: ax, y: round2(anchorY(a, rowA)) },
              { x: ax, y: level },
              { x: bx, y: level },
              { x: bx, y: round2(anchorY(b, rowB)) },
            ]);
          }
          w.wire(points, { from: stages[i].id ?? `stage-${i}`, to: stages[j].id ?? `stage-${j}`, key: Boolean(stages[i].key) });
          drawn += 1;
        }
        fig.dataset.dgEdges = String(drawn);

        if (center) {
          const centerEl = fig.querySelector('.dg-cycle-center');
          const canvasBox = w.box(fig.querySelector('.dg-canvas'));
          centerEl.style.setProperty('--cx', '0.5');
          centerEl.style.setProperty('--cy', String(round2(gapMid / canvasBox.h)));
        }
      },
    });
  }

  Object.assign(window.Render.diagram, { sequence, state, flowchart, swimlane, cycle });
})();

// Structure: architecture, er, containment. dependency ships from core.
(() => {
  'use strict';

  const { esc } = window.Render;
  const {
    frame, fail, check, node, layered, route, wires,
    channelStats, laneReserve, px, round, cssId,
  } = window.Render.diagram._;

  // -- architecture ----------------------------------------------------------
  // Zones are a fixed rank (one grid column each, left to right); components
  // barycenter-order inside their zone the same way layered() orders any
  // rank. A dashed .dg-zone frame draws behind each column, with its own
  // header row reserved above the component rows (see diagrams-structure.css)
  // so the label never sits on a component. Wherever an edge's rank changes
  // it has crossed a zone boundary; a filled .dg-cross square marks each
  // boundary it passes through, which is the point of this diagram type.

  function architecture(data = {}) {
    const { anchor, title = '', zones = [], components = [], edges = [] } = data;
    if (!zones.length) return fail(anchor, title, 'No zones passed. Use dependency for a flat graph with no zones.');
    const zoneIndex = new Map(zones.map((z, i) => [z.id, i]));
    const compIds = components.map((c) => c.id);
    const reason = check('architecture', data, {
      zones: zones.length, components: components.length, edges: edges.length, ids: compIds,
    });
    if (reason) return fail(anchor, title, reason);

    const badZone = components.find((c) => !zoneIndex.has(c.zone));
    if (badZone) return fail(anchor, title, `Component "${badZone.id}" names an unknown zone ("${badZone.zone}").`);
    const emptyZone = zones.find((z) => !components.some((c) => c.zone === z.id));
    if (emptyZone) return fail(anchor, title, `Zone "${emptyZone.label}" has no components. Remove it or give it one.`);
    const compIdSet = new Set(compIds);
    const badEdge = edges.find((e) => !compIdSet.has(e.from) || !compIdSet.has(e.to));
    if (badEdge) return fail(anchor, title, `Edge references an unknown id ("${badEdge.from}" -> "${badEdge.to}"). Fix the id and try again.`);

    const compZone = new Map(components.map((c) => [c.id, zoneIndex.get(c.zone)]));
    // layered()'s column placement walks ranks in ascending order and looks
    // up each node's parents' columns as it goes, so a "parent" that hasn't
    // been placed yet (any edge into an EARLIER zone, i.e. backward once
    // ranks are pinned by zone) reads back undefined and poisons the mean
    // with NaN. Ordering only needs forward/same-zone edges; route() below
    // still draws every edge, backward ones included, straight off `layout`.
    const orderEdges = edges.filter((e) => compZone.get(e.to) >= compZone.get(e.from));
    const layout = layered(components, orderEdges, { rank: (id) => compZone.get(id) });
    const laneRoom = laneReserve(layout, edges);
    const { tracks, labeled } = channelStats(layout, edges);

    const zoneHtml = zones.map((z, i) => (
      `<div class="dg-zone" style="--r:${i + 1}"></div>`
      + `<span class="dg-zone-head" style="--r:${i + 1}">${esc(z.label)}</span>`
    )).join('');
    // Row 1 is reserved for zone headers (diagrams-structure.css gives
    // .dg-architecture .dg-canvas an extra leading "auto" row), so every
    // component sits one row lower than its own col would otherwise place it.
    const nodesHtml = components.map((c) => {
      const p = layout.pos.get(c.id);
      return node(c, '', ` style="--r:${p.rank + 1};--c:${p.col + 2}"`);
    }).join('');

    const srEdges = edges.map((e) => (
      `<li>${esc(e.from)} → ${esc(e.to)}${e.label ? `: ${esc(e.label)}` : ''}</li>`
    )).join('');
    const crossings = edges.filter((e) => compZone.get(e.from) !== compZone.get(e.to)).map((e) => (
      `<li>crosses ${esc(zones[compZone.get(e.from)].label)} → ${esc(zones[compZone.get(e.to)].label)}</li>`
    )).join('');
    const sr = `<ul>${srEdges}</ul>${crossings ? `<ul>${crossings}</ul>` : ''}`;

    return frame({
      type: 'architecture',
      anchor,
      title,
      dir: 'LR',
      edges: edges.length,
      styleAttr: ` style="--cols:${layout.cols};--ranks:${layout.ranks};--back:${laneRoom};--loops:${layout.loops.length ? 1 : 0};--tracks:${tracks};--labeled:${labeled}"`,
      html: zoneHtml + nodesHtml,
      sr,
      draw(fig) {
        route(fig, layout, edges, { dir: 'LR' });
        drawZoneCrossings(fig, components, layout, edges, compZone);
      },
    });
  }

  function drawZoneCrossings(fig, components, layout, edges, compZone) {
    const svg = fig.querySelector('.dg-wires');
    const w = wires(fig);
    const byRank = new Map();
    for (const c of components) {
      const r = layout.rank.get(c.id);
      if (!byRank.has(r)) byRank.set(r, c.id);
    }
    const boundaryX = [];
    for (let r = 0; r + 1 < layout.ranks; r += 1) {
      const aId = byRank.get(r); const bId = byRank.get(r + 1);
      const aEl = aId != null ? fig.querySelector(`.dg-node[data-id="${cssId(aId)}"]`) : null;
      const bEl = bId != null ? fig.querySelector(`.dg-node[data-id="${cssId(bId)}"]`) : null;
      boundaryX.push(aEl && bEl ? (w.box(aEl).x + w.box(aEl).w + w.box(bEl).x) / 2 : null);
    }
    const gap = px('--marker');
    for (const e of edges) {
      if (e.from === e.to) continue;
      const zf = compZone.get(e.from); const zt = compZone.get(e.to);
      if (zf === zt) continue;
      const fromEl = fig.querySelector(`.dg-node[data-id="${cssId(e.from)}"]`);
      const toEl = fig.querySelector(`.dg-node[data-id="${cssId(e.to)}"]`);
      if (!fromEl || !toEl) continue;
      const fromBox = w.box(fromEl); const toBox = w.box(toEl);
      const y = (fromBox.y + fromBox.h / 2 + toBox.y + toBox.h / 2) / 2;
      const lo = Math.min(zf, zt); const hi = Math.max(zf, zt);
      for (let b = lo; b < hi; b += 1) {
        const x = boundaryX[b];
        if (x == null) continue;
        svg.insertAdjacentHTML('beforeend', `<rect class="dg-cross" x="${round(x - gap / 2)}" y="${round(y - gap / 2)}" width="${round(gap)}" height="${round(gap)}"/>`);
      }
    }
  }

  // -- er ----------------------------------------------------------------------
  // Entity boxes are layered() left to right from the referencing entity to
  // the referenced one; route() draws the line and its "to"-side glyph, its
  // port pinned to the target field row instead of fanning to the side. The
  // "from"-side glyph (ER needs one at each end) isn't something route() can
  // draw, so it's added after, read straight off the drawn line's own first
  // two points (never re-derived), by fromEndGlyph below.

  const CARD_KINDS = new Set(['1:1', '1:n', 'n:1', 'n:m']);
  const cardSide = (c) => (c === '1' ? 'one' : 'many');
  const cardWord = (c) => (c === '1' ? 'one' : 'many');

  function splitRef(ref) {
    const i = ref.lastIndexOf('.');
    return i < 0 ? [ref, ''] : [ref.slice(0, i), ref.slice(i + 1)];
  }

  function er(data = {}) {
    const { anchor, title = '', entities = [], relations = [] } = data;
    const entityIds = entities.map((e) => e.id);
    const entityIdSet = new Set(entityIds);
    const fieldSets = new Map(entities.map((e) => [e.id, new Set(e.fields.map((f) => f.name))]));
    const maxFields = entities.length ? Math.max(...entities.map((e) => e.fields.length)) : 0;
    const reason = check('er', data, {
      entities: entities.length, relations: relations.length, fields: maxFields, ids: entityIds,
    });
    if (reason) return fail(anchor, title, reason);

    const badCard = relations.find((r) => !CARD_KINDS.has(r.card));
    if (badCard) return fail(anchor, title, `Relation "${badCard.from}" -> "${badCard.to}" names an unknown card ("${badCard.card}"). Use 1:1, 1:n, n:1 or n:m.`);
    const badRef = relations.find((r) => {
      const [fe, ff] = splitRef(r.from); const [te, tf] = splitRef(r.to);
      return !entityIdSet.has(fe) || !fieldSets.get(fe)?.has(ff) || !entityIdSet.has(te) || !fieldSets.get(te)?.has(tf);
    });
    if (badRef) return fail(anchor, title, `Relation references an unknown entity or field ("${badRef.from}" -> "${badRef.to}").`);

    const routeEdges = relations.map((r) => {
      const [fromEntity, fromField] = splitRef(r.from);
      const [toEntity, toField] = splitRef(r.to);
      const [fromCard, toCard] = r.card.split(':');
      return {
        from: fromEntity, to: toEntity, fromField, toField, label: r.label,
        end: cardSide(toCard), endFrom: cardSide(fromCard),
      };
    });

    const layout = layered(entities, routeEdges);
    const laneRoom = laneReserve(layout, routeEdges);
    const { tracks, labeled } = channelStats(layout, routeEdges);

    const entitiesHtml = entities.map((ent) => {
      const p = layout.pos.get(ent.id);
      const rows = ent.fields.map((f) => {
        const tags = [f.pk ? 'PK' : '', f.fk ? 'FK' : ''].filter(Boolean).join('/');
        return (
          `<div class="dg-field" data-field="${esc(ent.id)}.${esc(f.name)}">`
          + `<span class="fname">${esc(f.name)}</span>`
          + (f.type ? `<span class="ftype">${esc(f.type)}</span>` : '')
          + (tags ? `<span class="tag">${esc(tags)}</span>` : '')
          + '</div>'
        );
      }).join('');
      return (
        `<div class="dg-node" data-id="${esc(ent.id)}" style="--r:${p.rank + 1};--c:${p.col + 1}">`
        + `<div class="dg-ehead">${esc(ent.label)}</div>${rows}</div>`
      );
    }).join('');

    const srItems = relations.map((r) => {
      const [fromCard, toCard] = r.card.split(':');
      return `<li>${esc(r.from)} → ${esc(r.to)}, ${cardWord(fromCard)} to ${cardWord(toCard)}${r.label ? ` (${esc(r.label)})` : ''}</li>`;
    }).join('');

    return frame({
      type: 'er',
      anchor,
      title,
      dir: 'LR',
      edges: routeEdges.length,
      styleAttr: ` style="--cols:${layout.cols};--ranks:${layout.ranks};--back:${laneRoom};--loops:${layout.loops.length ? 1 : 0};--tracks:${tracks};--labeled:${labeled}"`,
      html: entitiesHtml,
      sr: `<ul>${srItems}</ul>`,
      draw(fig) {
        const w = wires(fig);
        const entityBoxes = new Map();
        for (const ent of entities) {
          const el = fig.querySelector(`.dg-node[data-id="${cssId(ent.id)}"]`);
          if (el) entityBoxes.set(ent.id, w.box(el));
        }
        // Two relations can honestly reference the same field (e.g. two FKs
        // into one PK); pinning both to that row's exact centre would run
        // their final approach on top of one another (R3). Group by the
        // (entity, field, side) port they share and spread across the row's
        // own height by --route instead, same idea as the core fan does
        // across a whole node side, just scoped to one row.
        const portGroups = new Map();
        for (const edge of routeEdges) {
          for (const end of ['from', 'to']) {
            const entityId = end === 'from' ? edge.from : edge.to;
            const fieldName = end === 'from' ? edge.fromField : edge.toField;
            const k = `${end}:${entityId}.${fieldName}`;
            if (!portGroups.has(k)) portGroups.set(k, []);
            portGroups.get(k).push(edge);
          }
        }
        const routeGap = px('--route');
        const port = (edge, end) => {
          const entityId = end === 'from' ? edge.from : edge.to;
          const fieldName = end === 'from' ? edge.fromField : edge.toField;
          const rowEl = fig.querySelector(`.dg-field[data-field="${cssId(`${entityId}.${fieldName}`)}"]`);
          const entBox = entityBoxes.get(entityId);
          if (!rowEl || !entBox || !entBox.h) return undefined;
          const rowBox = w.box(rowEl);
          const group = portGroups.get(`${end}:${entityId}.${fieldName}`) || [edge];
          const i = Math.max(0, group.indexOf(edge));
          const spread = group.length > 1 ? (i - (group.length - 1) / 2) * routeGap : 0;
          const half = Math.max(0, rowBox.h / 2 - routeGap / 4);
          const y = rowBox.y + rowBox.h / 2 + Math.max(-half, Math.min(half, spread));
          const frac = (y - entBox.y) / entBox.h;
          return { frac: Math.min(1, Math.max(0, frac)) };
        };
        route(fig, layout, routeEdges, { dir: 'LR', port });
        drawFromEndGlyphs(fig, routeEdges);
      },
    });
  }

  function firstTwoPoints(d) {
    const m = /^M\s*(-?[\d.]+)\s+(-?[\d.]+)\s*([VHL])\s*(-?[\d.]+)(?:\s+(-?[\d.]+))?/.exec(d || '');
    if (!m) return null;
    const x0 = Number(m[1]); const y0 = Number(m[2]);
    let x1 = x0; let y1 = y0;
    if (m[3] === 'V') y1 = Number(m[4]);
    else if (m[3] === 'H') x1 = Number(m[4]);
    else { x1 = Number(m[4]); y1 = Number(m[5]); }
    return [{ x: x0, y: y0 }, { x: x1, y: y1 }];
  }

  function fromEndGlyph(p0, p1, kind) {
    if (kind !== 'one' && kind !== 'many') return '';
    const dx = Math.sign(p1.x - p0.x); const dy = Math.sign(p1.y - p0.y);
    const m = px('--marker');
    const fwd = dx !== 0 ? { x: p0.x + dx * m, y: p0.y } : { x: p0.x, y: p0.y + dy * m };
    if (kind === 'one') {
      return dx !== 0
        ? `<path class="dg-end is-one" d="M ${round(fwd.x)} ${round(fwd.y - m / 2)} V ${round(fwd.y + m / 2)}"/>`
        : `<path class="dg-end is-one" d="M ${round(fwd.x - m / 2)} ${round(fwd.y)} H ${round(fwd.x + m / 2)}"/>`;
    }
    const q1 = dx !== 0 ? { x: fwd.x, y: fwd.y - m * 0.6 } : { x: fwd.x - m * 0.6, y: fwd.y };
    const q2 = dx !== 0 ? { x: fwd.x, y: fwd.y + m * 0.6 } : { x: fwd.x + m * 0.6, y: fwd.y };
    return (
      `<path class="dg-end is-many" d="M ${round(q1.x)} ${round(q1.y)} L ${round(p0.x)} ${round(p0.y)} `
      + `L ${round(q2.x)} ${round(q2.y)} M ${round(q1.x)} ${round(q1.y)} L ${round(q2.x)} ${round(q2.y)}"/>`
    );
  }

  function drawFromEndGlyphs(fig, routeEdges) {
    const real = routeEdges.filter((e) => e.from !== e.to);
    const drawnEls = [...fig.querySelectorAll('.dg-edge')].slice(0, real.length);
    real.forEach((edge, i) => {
      const el = drawnEls[i];
      const line = el?.querySelector('.dg-line');
      const pts = line && firstTwoPoints(line.getAttribute('d'));
      if (!pts) return;
      el.insertAdjacentHTML('beforeend', fromEndGlyph(pts[0], pts[1], edge.endFrom));
    });
  }

  // -- containment -------------------------------------------------------------
  // Pure HTML: nested <ul>/<li> boxes, no wires. The nesting itself is the
  // text alternative, so frame() gets no sr block.

  function countBoxes(list) {
    return list.reduce((n, b) => n + 1 + (b.children ? countBoxes(b.children) : 0), 0);
  }
  function maxDepth(list, d = 1) {
    return list.reduce((m, b) => (b.children?.length ? Math.max(m, maxDepth(b.children, d + 1)) : m), d);
  }
  function boxHtml(b, depth) {
    const cls = [
      'dg-box',
      b.key ? 'is-key' : '',
      b.sunk ? 'is-sunk' : (depth % 2 === 1 ? 'is-alt' : ''),
    ].filter(Boolean).join(' ');
    const sub = b.sub ? `<span class="dg-sub">${esc(b.sub)}</span>` : '';
    const children = b.children?.length
      ? `<ul class="dg-children">${b.children.map((c) => `<li>${boxHtml(c, depth + 1)}</li>`).join('')}</ul>`
      : '';
    return `<div class="${cls}"><div class="dg-boxhead"><span class="dg-label">${esc(b.label)}</span>${sub}</div>${children}</div>`;
  }

  function containment(data = {}) {
    const { anchor, title = '', boxes = [] } = data;
    if (!boxes.length) return fail(anchor, title, 'No boxes passed. Add at least one box.');
    const reason = check('containment', data, { boxes: countBoxes(boxes), depth: maxDepth(boxes) });
    if (reason) return fail(anchor, title, reason);

    const html = `<ul class="dg-boxes">${boxes.map((b) => `<li>${boxHtml(b, 0)}</li>`).join('')}</ul>`;
    return frame({ type: 'containment', anchor, title, html });
  }

  Object.assign(window.Render.diagram, { architecture, er, containment });
})();

// Planning: gantt, kanban, storymap, quadrant.
(() => {
  'use strict';
  const { esc, cap } = window.Render;
  const {
    frame, fail, check, wires, px, round, cssId, days, nudge, thin,
  } = window.Render.diagram._;

  const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
  function badDate(iso) { return !DATE_RE.test(iso || '') || Number.isNaN(days(iso)); }

  // Evenly spaced day offsets across [0, span], endpoints included, so tick
  // labels land on real calendar days instead of "nice number" day counts.
  function dateTicks(span, n) {
    if (span <= 0) return [0];
    const out = [];
    for (let i = 0; i <= n; i += 1) out.push(Math.round((span * i) / n));
    return [...new Set(out)];
  }
  function isoFromDay(dayNum) {
    return new Date(dayNum * 86400000).toISOString().slice(0, 10);
  }

  // -- gantt -------------------------------------------------------------

  function gantt(data = {}) {
    const {
      anchor, title = '', start, end, today, tasks = [],
    } = data;
    const ids = tasks.map((t) => t.id);
    const reason = check('gantt', data, { tasks: tasks.length, ids });
    if (reason) return fail(anchor, title, reason);

    if (badDate(start) || badDate(end)) {
      return fail(anchor, title, `The window's start ("${start}") and end ("${end}") must both be YYYY-MM-DD dates.`);
    }
    const winStart = days(start); const winEnd = days(end);
    if (winStart >= winEnd) return fail(anchor, title, `The window start (${start}) must be before its end (${end}).`);

    for (const t of tasks) {
      if (badDate(t.start) || badDate(t.end)) return fail(anchor, title, `Task "${t.id}" has a start or end that isn't a YYYY-MM-DD date.`);
      if (days(t.start) > days(t.end)) return fail(anchor, title, `Task "${t.id}" starts (${t.start}) after it ends (${t.end}).`);
      if (days(t.start) < winStart || days(t.end) > winEnd) {
        return fail(anchor, title, `Task "${t.id}" (${t.start} to ${t.end}) falls outside the window ${start} to ${end}.`);
      }
    }
    const byId = new Map(tasks.map((t) => [t.id, t]));
    for (const t of tasks) {
      if (t.after == null) continue;
      const pred = byId.get(t.after);
      if (!pred) return fail(anchor, title, `Task "${t.id}" depends on unknown task "${t.after}".`);
      if (days(t.start) < days(pred.end)) {
        return fail(anchor, title, `Task "${t.id}" starts (${t.start}) before its predecessor "${t.after}" ends (${pred.end}).`);
      }
    }

    const span = winEnd - winStart;
    const frac = (iso) => (days(iso) - winStart) / span;
    const rowIndex = new Map(tasks.map((t, i) => [t.id, i]));
    const rows = tasks.map((t) => ({
      ...t, s: frac(t.start), e: t.milestone ? frac(t.start) : frac(t.end),
    }));
    const todayFrac = today && !badDate(today) ? frac(today) : null;
    const showToday = todayFrac != null && todayFrac >= 0 && todayFrac <= 1;

    const tickHtml = dateTicks(span, 5).map((d, i) => (
      `<span class="dg-tick" data-tick="${i}" style="--t:${round(d / span)}">${esc(isoFromDay(winStart + d).slice(5))}</span>`
    )).join('');
    const tickToday = showToday ? `<span class="dg-today" style="--t:${round(todayFrac)}"></span>` : '';

    const rowsHtml = rows.map((t) => {
      const rowToday = showToday ? `<span class="dg-today" style="--t:${round(todayFrac)}"></span>` : '';
      if (t.milestone) {
        return (
          `<div class="dg-row"><div class="dg-row-label">${esc(t.label)}</div>`
          + `<div class="dg-row-track"><span class="dg-bar dg-milestone${t.key ? ' is-key' : ''}" data-bar="${esc(t.id)}" `
          + `style="--s:${round(t.s)}"></span>${rowToday}<span class="dg-sr">Milestone</span></div></div>`
        );
      }
      const status = t.status || 'planned';
      const cls = ['dg-bar', `is-${esc(status)}`, t.key ? 'is-key' : ''].filter(Boolean).join(' ');
      return (
        `<div class="dg-row"><div class="dg-row-label">${esc(t.label)}</div>`
        + `<div class="dg-row-track"><span class="${cls}" data-bar="${esc(t.id)}" `
        + `style="--s:${round(t.s)};--e:${round(t.e)}"></span>${rowToday}<span class="dg-sr">${esc(cap(status))}</span></div></div>`
      );
    }).join('');

    const links = rows.filter((t) => t.after != null);
    const srItems = rows.map((t) => {
      const dep = t.after ? `, after "${byId.get(t.after).label}"` : '';
      const kind = t.milestone ? 'Milestone' : cap(t.status || 'planned');
      return `<li>${esc(t.label)}: ${esc(t.start)} to ${esc(t.end)} (${kind})${esc(dep)}.</li>`;
    }).join('');

    return frame({
      type: 'gantt',
      anchor,
      title,
      edges: links.length || undefined,
      styleAttr: '',
      html: `<div class="dg-gantt-grid"><div class="dg-gantt-head"><div class="dg-row-label"></div>`
        + `<div class="dg-row-track dg-tick-row">${tickHtml}${tickToday}</div></div>${rowsHtml}</div>`,
      sr: `<ol>${srItems}</ol>`,
      draw(fig) {
        for (const row of fig.querySelectorAll('.dg-tick-row')) thin([...row.querySelectorAll('.dg-tick')]);
        if (!links.length) return;
        const w = wires(fig);
        w.clear();
        let drawn = 0;
        const route = px('--route');
        // Every link touching a given (task, exit-or-entry side) shares one
        // fan across that bar's width instead of all defaulting to its
        // centre (mirrors core route()'s sideFrac: two links off the same
        // predecessor would otherwise draw the exact same x, R3's "merged
        // track" case).
        const bySource = new Map(); const byTarget = new Map();
        for (const t of links) {
          if (!bySource.has(t.after)) bySource.set(t.after, []);
          bySource.get(t.after).push(t);
          if (!byTarget.has(t.id)) byTarget.set(t.id, []);
          byTarget.get(t.id).push(t);
        }
        function fanX(box, group, t) {
          const i = group.indexOf(t);
          return box.x + (box.w * (i + 1)) / (group.length + 1);
        }
        for (const t of links) {
          const fromEl = fig.querySelector(`[data-bar="${cssId(t.after)}"]`);
          const toEl = fig.querySelector(`[data-bar="${cssId(t.id)}"]`);
          if (!fromEl || !toEl) continue;
          const a = w.box(fromEl); const b = w.box(toEl);
          const dir = rowIndex.get(t.id) >= rowIndex.get(t.after) ? 1 : -1;
          const fromX = fanX(a, bySource.get(t.after), t);
          const toX = fanX(b, byTarget.get(t.id), t);
          const fromY = dir > 0 ? a.y + a.h : a.y;
          const toY = dir > 0 ? b.y : b.y + b.h;
          let points;
          if (Math.abs(toX - fromX) < route) {
            // Close enough that a jog would draw a sub-route/2 sliver (R5):
            // snap to one x, same as core route()'s aligned-port case, so
            // this stays a single straight vertical segment (R5-exempt).
            points = [{ x: fromX, y: fromY }, { x: fromX, y: toY }];
          } else {
            // |toX-fromX| >= route here, so the single H jog's own length
            // already clears route/2 on its own; only the two V runs (port
            // exit/entry) need their own route clearance.
            const span2 = Math.abs(toY - fromY);
            const midY = span2 >= route * 2 ? fromY + dir * route : fromY + dir * (span2 / 2);
            points = [
              { x: fromX, y: fromY },
              { x: fromX, y: midY },
              { x: toX, y: midY },
              { x: toX, y: toY },
            ];
          }
          const g = w.wire(points, { from: t.after, to: t.id });
          g.setAttribute('data-from-el', `[data-bar="${cssId(t.after)}"]`);
          g.setAttribute('data-to-el', `[data-bar="${cssId(t.id)}"]`);
          drawn += 1;
        }
        fig.dataset.dgEdges = String(drawn);
      },
    });
  }

  // -- kanban --------------------------------------------------------------

  function kanban(data = {}) {
    const { anchor, title = '', columns = [] } = data;
    const reason = check('kanban', data, {
      columns: columns.length,
      cards: columns.reduce((max, c) => Math.max(max, (c.cards || []).length), 0),
    });
    if (reason) return fail(anchor, title, reason);

    for (const c of columns) {
      if (c.limit != null && (!Number.isInteger(c.limit) || c.limit <= 0)) {
        return fail(anchor, title, `Column "${c.label}" has a limit (${JSON.stringify(c.limit)}) that isn't a positive integer.`);
      }
    }

    const colsHtml = columns.map((c) => {
      const count = (c.cards || []).length;
      const over = c.limit != null && count > c.limit;
      const countCls = over ? 'dg-kanban-count is-over' : 'dg-kanban-count';
      const countText = c.limit != null ? `${count}/${c.limit}` : String(count);
      const overNote = over ? `<p class="dg-sr">Over limit by ${count - c.limit}.</p>` : '';
      const cardsHtml = (c.cards || []).map((card) => {
        const cls = ['dg-kanban-card', card.key ? 'is-key' : '', card.blocked ? 'is-blocked' : ''].filter(Boolean).join(' ');
        const sub = card.sub ? `<span class="meta">${esc(card.sub)}</span>` : '';
        const tag = card.blocked ? '<span class="dg-tag">Blocked</span>' : '';
        return `<li class="${cls}"><span class="title">${esc(card.label)}</span>${sub}${tag}</li>`;
      }).join('');
      return (
        `<div class="dg-kanban-col"><div class="dg-kanban-head"><span class="title">${esc(c.label)}</span>`
        + `<span class="${countCls} mono">${esc(countText)}</span></div>${overNote}<ul class="dg-kanban-cards">${cardsHtml}</ul></div>`
      );
    }).join('');

    const srItems = columns.map((c) => {
      const names = (c.cards || []).map((card) => card.label + (card.blocked ? ' (blocked)' : '')).join(', ');
      return `<li>${esc(c.label)}: ${esc(names || 'empty')}.</li>`;
    }).join('');

    return frame({
      type: 'kanban',
      anchor,
      title,
      html: `<div class="dg-kanban-board">${colsHtml}</div>`,
      sr: `<ul>${srItems}</ul>`,
    });
  }

  // -- storymap --------------------------------------------------------------

  function storymap(data = {}) {
    const { anchor, title = '', activities = [], releases = [] } = data;
    const perCellMax = activities.reduce((max, a) => {
      const byRelease = new Map();
      for (const s of a.stories || []) byRelease.set(s.release, (byRelease.get(s.release) || 0) + 1);
      return Math.max(max, ...(byRelease.size ? [...byRelease.values()] : [0]));
    }, 0);
    const reason = check('storymap', data, {
      activities: activities.length, releases: releases.length, stories: perCellMax,
      ids: [...activities.map((a) => a.id), ...releases.map((r) => r.id)],
    });
    if (reason) return fail(anchor, title, reason);

    const releaseIds = new Set(releases.map((r) => r.id));
    for (const a of activities) {
      if (!(a.stories || []).length) return fail(anchor, title, `Activity "${a.label}" has no stories.`);
      for (const s of a.stories) {
        if (!releaseIds.has(s.release)) return fail(anchor, title, `Activity "${a.label}" has a story assigned to unknown release "${s.release}".`);
      }
    }

    const backbone = activities.map((a) => `<div class="dg-backbone-cell">${esc(a.label)}</div>`).join('');
    const bandsHtml = releases.map((r) => {
      const cut = `<div class="dg-release-cut">${esc(r.label)}</div>`;
      const cells = activities.map((a) => {
        const stories = (a.stories || []).filter((s) => s.release === r.id);
        const items = stories.map((s) => `<li class="dg-story${s.key ? ' is-key' : ''}">${esc(s.label)}</li>`).join('');
        return `<div class="dg-cell"><ul>${items}</ul></div>`;
      }).join('');
      return `${cut}<div class="dg-story-row">${cells}</div>`;
    }).join('');

    const srItems = activities.map((a) => {
      const stories = (a.stories || []).map((s) => `${s.label} (${releases.find((r) => r.id === s.release)?.label})`).join('; ');
      return `<li>${esc(a.label)}: ${esc(stories)}.</li>`;
    }).join('');

    return frame({
      type: 'storymap',
      anchor,
      title,
      styleAttr: ` style="--n:${activities.length}"`,
      html: `<div class="dg-storymap-grid"><div class="dg-backbone">${backbone}</div>${bandsHtml}</div>`,
      sr: `<ul>${srItems}</ul>`,
    });
  }

  // -- quadrant --------------------------------------------------------------

  function quadrant(data = {}) {
    const {
      anchor, title = '', x, y, quadrants, items = [],
    } = data;
    const reason = check('quadrant', data, { items: items.length });
    if (reason) return fail(anchor, title, reason);

    for (const it of items) {
      if (!(it.x >= 0 && it.x <= 1) || !(it.y >= 0 && it.y <= 1)) {
        return fail(anchor, title, `Item "${it.label}" has a coordinate outside 0..1 (x=${it.x}, y=${it.y}).`);
      }
    }

    const corner = quadrants || {
      tl: `${y.high}, ${x.low}`,
      tr: `${y.high}, ${x.high}`,
      bl: `${y.low}, ${x.low}`,
      br: `${y.low}, ${x.high}`,
    };

    const itemsHtml = items.map((it, i) => (
      `<div class="dg-quad-item${it.key ? ' is-key' : ''}" data-quad="${i}" style="--x:${round(it.x)};--y:${round(it.y)}">`
      + `<span class="dg-quad-mark"></span><span class="dg-quad-label">${esc(it.label)}</span></div>`
    )).join('');

    const srItems = items.map((it) => `<li>${esc(it.label)}: ${esc(y.label)} ${it.y >= 0.5 ? esc(y.high) : esc(y.low)}, ${esc(x.label)} ${it.x >= 0.5 ? esc(x.high) : esc(x.low)}.</li>`).join('');

    return frame({
      type: 'quadrant',
      anchor,
      title,
      html: (
        `<div class="dg-quad-plot">`
        + `<span class="dg-quad-corner is-tl">${esc(corner.tl)}</span><span class="dg-quad-corner is-tr">${esc(corner.tr)}</span>`
        + `<span class="dg-quad-corner is-bl">${esc(corner.bl)}</span><span class="dg-quad-corner is-br">${esc(corner.br)}</span>`
        + `<span class="dg-quad-axis is-x">${esc(x.label)}</span><span class="dg-quad-axis is-y">${esc(y.label)}</span>`
        + `${itemsHtml}</div>`
      ),
      sr: `<ul>${srItems}</ul>`,
      draw(fig) {
        nudge(fig.querySelectorAll('.dg-quad-label'), 'y');
      },
    });
  }

  Object.assign(window.Render.diagram, {
    gantt, kanban, storymap, quadrant,
  });
})();

// Analysis and data: fishbone, waterfall, treemap, funnel, line.
//
// Every class this file introduces is prefixed dg-fb-/dg-wf-/dg-tm-/dg-fn-/
// dg-ln- (one per type) rather than a bare generic name, to avoid colliding
// with a bare rule defined in another group's stylesheet.
(() => {
  'use strict';

  const { esc } = window.Render;
  const {
    frame, fail, check, wires, squarify, scale, ticks, nudge, px, round, cssId,
  } = window.Render.diagram._;

  function fmtSigned(n) {
    return n >= 0 ? `+${n}` : String(n);
  }

  // -- fishbone ----------------------------------------------------------

  function fishbone(data = {}) {
    const { anchor, title = '', effect = '', causes = [] } = data;
    const reason = check('fishbone', data, {
      categories: causes.length,
      causes: causes.reduce((m, c) => Math.max(m, (c.items || []).length), 0),
    });
    if (reason) return fail(anchor, title, reason);
    if (causes.length < 2) {
      return fail(anchor, title, `${causes.length} cause categories passed; a fishbone needs at least 2.`);
    }
    const empty = causes.find((c) => !(c.items || []).length);
    if (empty) return fail(anchor, title, `Category "${empty.label}" has no causes listed.`);

    const cols = Math.ceil(causes.length / 2);
    const catsHtml = causes.map((c, i) => {
      const row = i % 2 === 0 ? 'is-fb-top' : 'is-fb-bottom';
      const col = Math.floor(i / 2) + 1;
      const items = (c.items || []).map((it) => `<li>${esc(it)}</li>`).join('');
      return (
        `<div class="dg-fb-cat ${row}" style="--col:${col}">`
        + `<span class="title">${esc(c.label)}</span><ul>${items}</ul></div>`
      );
    }).join('');

    const html = (
      `<div class="dg-fb-plot" style="--cols:${cols}">${catsHtml}`
      + `<div class="dg-fb-spine" style="--col:${cols + 1}"></div>`
      + `<div class="dg-fb-effect" style="--col:${cols + 1}"><span class="title">${esc(effect)}</span></div>`
      + '</div>'
    );

    const sr = (
      `<ul>${causes.map((c) => (
        `<li>${esc(c.label)}: ${(c.items || []).map(esc).join(', ')}</li>`
      )).join('')}</ul><p>Effect: ${esc(effect)}</p>`
    );

    return frame({ type: 'fishbone', anchor, title, html, sr });
  }

  // -- waterfall -----------------------------------------------------------

  function waterfall(data = {}) {
    const { anchor, title = '', start, steps = [], end, unit = '' } = data;
    const reason = check('waterfall', data, { steps: steps.length });
    if (reason) return fail(anchor, title, reason);
    if (!start || !end) return fail(anchor, title, 'A waterfall needs both a start and an end total.');

    const total = steps.reduce((s, d) => s + d.delta, start.value);
    if (round(total) !== round(end.value)) {
      return fail(
        anchor, title,
        `${start.value} plus the ${steps.length} deltas comes to ${round(total)}${unit}, `
        + `not the stated end of ${end.value}${unit}.`,
      );
    }

    const bars = [{ id: 'start', label: start.label, kind: 'total', value: start.value, lo: Math.min(0, start.value), hi: Math.max(0, start.value), after: start.value }];
    let running = start.value;
    steps.forEach((s, i) => {
      const from = running;
      running += s.delta;
      bars.push({
        id: `step-${i}`, label: s.label, kind: s.delta >= 0 ? 'is-wf-up' : 'is-wf-down', delta: s.delta,
        lo: Math.min(from, running), hi: Math.max(from, running), after: running,
      });
    });
    bars.push({ id: 'end', label: end.label, kind: 'total', value: end.value, lo: Math.min(0, end.value), hi: Math.max(0, end.value), after: end.value });

    const domainMin = Math.min(0, ...bars.map((b) => b.lo));
    const domainMax = Math.max(0, ...bars.map((b) => b.hi));
    const f = scale(domainMin, domainMax);

    const barsHtml = bars.map((b) => {
      const val = b.kind === 'total' ? String(b.value) : fmtSigned(b.delta);
      const kindCls = b.kind === 'total' ? 'is-wf-total' : b.kind;
      return (
        `<div class="dg-wf-col" data-id="${b.id}">`
        + `<div class="dg-wf-bar ${kindCls}" style="--lo:${round(f(b.lo))};--hi:${round(f(b.hi))}">`
        + `<span class="dg-wf-val">${esc(val)}${esc(unit)}</span></div>`
        + `<span class="dg-wf-col-label">${esc(b.label)}</span></div>`
      );
    }).join('');

    const html = (
      `<div class="dg-wf-plot" style="--n:${bars.length};--zero:${round(f(0))}">`
      + `<div class="dg-wf-zero"></div>${barsHtml}</div>`
    );

    const sr = (
      `<table><caption>${esc(title || 'Waterfall')}</caption>`
      + `<thead><tr><th>Step</th><th>Value</th></tr></thead><tbody>`
      + bars.map((b) => `<tr><td>${esc(b.label)}</td><td>${esc(b.kind === 'total' ? String(b.value) : fmtSigned(b.delta))}${esc(unit)}</td></tr>`).join('')
      + '</tbody></table>'
    );

    return frame({
      type: 'waterfall',
      anchor,
      title,
      html,
      sr,
      draw(fig) {
        const w = wires(fig);
        w.clear();
        const cols = [...fig.querySelectorAll('.dg-wf-col')];
        // Reference a column's own box, not .dg-wf-plot's: the plot has its
        // own top/bottom padding (room for the outermost value labels), so
        // its border box is taller than the --lo/--hi fractions' actual
        // reference frame, which is each stretched .dg-wf-col's content box.
        const plotBox = w.box(cols[0]);
        for (let i = 0; i < cols.length - 1; i += 1) {
          const a = w.box(cols[i]);
          const b = w.box(cols[i + 1]);
          const y = plotBox.y + plotBox.h * (1 - f(bars[i].after));
          const g = w.wire(
            [{ x: a.x + a.w, y }, { x: b.x, y }],
            { from: bars[i].id, to: bars[i + 1].id, soft: true, head: 'none' },
          );
          g.dataset.fromEl = `[data-id="${cssId(bars[i].id)}"]`;
          g.dataset.toEl = `[data-id="${cssId(bars[i + 1].id)}"]`;
        }
      },
    });
  }

  // -- treemap ---------------------------------------------------------------

  function treemap(data = {}) {
    const { anchor, title = '', items = [], total } = data;
    const reason = check('treemap', data, { cells: items.length });
    if (reason) return fail(anchor, title, reason);
    const bad = items.find((it) => !(it.value > 0));
    if (bad) return fail(anchor, title, `"${bad.label}" has a value of ${bad.value}; every treemap value must be positive.`);

    const sum = items.reduce((s, it) => s + it.value, 0);
    const declaredTotal = total != null ? total : sum;
    if (round(sum) !== round(declaredTotal)) {
      return fail(anchor, title, `Items sum to ${round(sum)}, not the stated total of ${declaredTotal}.`);
    }
    const small = items.find((it) => it.value / declaredTotal < 0.02);
    if (small) return fail(anchor, title, `"${small.label}" is under 2% of the total; fold it into Other.`);

    const W = 16;
    const H = 9;
    const rects = squarify(items.map((it) => it.value), W, H);
    const cellsHtml = items.map((it, i) => {
      const r = rects[i];
      const share = round((it.value / declaredTotal) * 100);
      const sub = it.sub ? `<span class="dg-tm-sub">${esc(it.sub)}</span>` : '';
      return (
        `<div class="dg-tm-cell${it.key ? ' is-key' : ''}" data-id="cell-${i}" `
        + `style="--x:${round(r.x / W)};--y:${round(r.y / H)};--w:${round(r.w / W)};--h:${round(r.h / H)}">`
        + `<span class="title">${esc(it.label)}</span><span class="dg-tm-val">${it.value} · ${share}%</span>${sub}</div>`
      );
    }).join('');

    const sr = `<ul>${items.map((it) => `<li>${esc(it.label)}: ${it.value} (${round((it.value / declaredTotal) * 100)}%)</li>`).join('')}</ul>`;

    return frame({
      type: 'treemap',
      anchor,
      title,
      html: `<div class="dg-tm-plot">${cellsHtml}</div>`,
      sr,
      draw(fig) {
        // ponytail: a fixed pixel floor, not a measured text metric; good
        // enough at this budget's cell count, revisit with real wrapping
        // math if a page ever needs finer control.
        for (const cell of fig.querySelectorAll('.dg-tm-cell')) {
          const sub = cell.querySelector('.dg-tm-sub');
          if (!sub) continue;
          sub.hidden = cell.getBoundingClientRect().height < 72;
        }
      },
    });
  }

  // -- funnel ----------------------------------------------------------------

  function funnel(data = {}) {
    const { anchor, title = '', stages = [] } = data;
    const reason = check('funnel', data, { stages: stages.length });
    if (reason) return fail(anchor, title, reason);
    const bad = stages.find((s) => !(s.value > 0));
    if (bad) return fail(anchor, title, `"${bad.label}" has a value of ${bad.value}; every funnel stage must be positive.`);
    for (let i = 1; i < stages.length; i += 1) {
      if (stages[i].value > stages[i - 1].value) {
        return fail(
          anchor, title,
          `"${stages[i].label}" (${stages[i].value}) is larger than "${stages[i - 1].label}" `
          + `(${stages[i - 1].value}); that is not a funnel.`,
        );
      }
    }

    const first = stages[0]?.value || 1;
    const rowsHtml = stages.map((s, i) => {
      const v = round(s.value / first);
      const conv = i === 0 ? '' : `<span class="dg-fn-conv">${round((s.value / stages[i - 1].value) * 100)}% of previous</span>`;
      return (
        `<div class="dg-fn-row" data-id="stage-${i}">`
        + `<span class="dg-fn-label">${esc(s.label)}</span>`
        + `<span class="dg-fn-track"><span class="dg-fn-bar" style="--v:${v}"></span></span>`
        + `<span class="dg-fn-value">${s.value}${conv}</span></div>`
      );
    }).join('');

    const sr = (
      `<table><thead><tr><th>Stage</th><th>Value</th><th>Conversion</th></tr></thead><tbody>`
      + stages.map((s, i) => `<tr><td>${esc(s.label)}</td><td>${s.value}</td><td>${i === 0 ? '—' : `${round((s.value / stages[i - 1].value) * 100)}%`}</td></tr>`).join('')
      + '</tbody></table>'
    );

    return frame({ type: 'funnel', anchor, title, html: `<div class="dg-fn-plot">${rowsHtml}</div>`, sr });
  }

  // -- line (slope chart when x.ticks.length === 2) ---------------------------

  function line(data = {}) {
    const { anchor, title = '', x = {}, y = {}, series = [] } = data;
    const xTicks = x.ticks || [];
    const tickCount = xTicks.length;
    if (tickCount < 2) return fail(anchor, title, `${tickCount} x-axis ticks passed; a line needs at least 2.`);
    const isSlope = tickCount === 2;

    const maxPoints = series.reduce((m, s) => Math.max(m, (s.values || []).length), 0);
    const counts = isSlope
      ? { slopeSeries: series.length, points: maxPoints }
      : { series: series.length, points: maxPoints };
    const reason = check('line', data, counts);
    if (reason) return fail(anchor, title, reason);

    const badLen = series.find((s) => (s.values || []).length !== tickCount);
    if (badLen) return fail(anchor, title, `"${badLen.label}" has ${badLen.values.length} values; there are ${tickCount} x-axis ticks.`);
    const badVal = series.find((s) => s.values.some((v) => !Number.isFinite(v)));
    if (badVal) return fail(anchor, title, `"${badVal.label}" has a non-finite value.`);

    const all = series.flatMap((s) => s.values);
    const domain = ticks(Math.min(0, ...all), Math.max(0, ...all));
    const f = scale(domain[0], domain[domain.length - 1]);
    const xAt = (i) => i / (tickCount - 1);

    const gridHtml = domain.map((t) => (
      `<div class="dg-ln-grid" style="--y:${round(1 - f(t))}"><span class="dg-ln-tick">${esc(String(t))}${esc(y.unit || '')}</span></div>`
    )).join('');
    const xticksHtml = xTicks.map((t, i) => `<span style="--x:${round(xAt(i))}">${esc(String(t))}</span>`).join('');

    const points = series.map((s) => s.values.map((v, i) => ({ x: xAt(i), y: 1 - f(v) })));
    const labelsHtml = series.map((s, si) => {
      const pts = points[si];
      const ends = isSlope ? [['is-ln-start', pts[0]], ['is-ln-end', pts[pts.length - 1]]] : [['is-ln-end', pts[pts.length - 1]]];
      return ends.map(([pos, p]) => (
        `<span class="dg-ln-end-label ${pos}" style="--y:${round(p.y)}">${esc(s.label)}</span>`
      )).join('');
    }).join('');

    const html = (
      `<div class="dg-ln-plot"><div class="dg-ln-chart">`
      + `<div class="dg-ln-grids">${gridHtml}</div>`
      + `<div class="dg-ln-xticks">${xticksHtml}</div>`
      + `</div><div class="dg-ln-labels">${labelsHtml}</div></div>`
    );

    const srRows = xTicks.map((t, i) => (
      `<tr><td>${esc(String(t))}</td>${series.map((s) => `<td>${s.values[i]}</td>`).join('')}</tr>`
    )).join('');
    const sr = (
      `<table><caption>${esc(title || 'Line chart')}</caption>`
      + `<thead><tr><th>${esc(x.label || '')}</th>${series.map((s) => `<th>${esc(s.label)}</th>`).join('')}</tr></thead>`
      + `<tbody>${srRows}</tbody></table>`
    );

    return frame({
      type: 'line',
      anchor,
      title,
      html,
      sr,
      draw(fig) {
        const w = wires(fig);
        w.clear();
        const chartBox = w.box(fig.querySelector('.dg-ln-chart'));
        const marker = px('--marker') / 2 || 4;
        series.forEach((s, si) => {
          const pts = points[si].map((p) => ({ x: chartBox.x + chartBox.w * p.x, y: chartBox.y + chartBox.h * p.y }));
          const d = `M ${pts.map((p) => `${round(p.x)} ${round(p.y)}`).join(' L ')}`;
          const marks = pts.map((p) => (
            `<rect class="dg-ln-point" x="${round(p.x - marker / 2)}" y="${round(p.y - marker / 2)}" width="${round(marker)}" height="${round(marker)}"/>`
          )).join('');
          const cls = s.key ? 'is-key' : `is-ln-dash-${(si % 3) + 1}`;
          w.svg.insertAdjacentHTML(
            'beforeend',
            `<g class="dg-edge ${cls}" data-from="${esc(s.label)}" data-to="${esc(s.label)}">`
            + `<path class="dg-line" d="${d}"/>${marks}</g>`,
          );
        });
        const startLabels = [...fig.querySelectorAll('.dg-ln-end-label.is-ln-start')];
        const endLabels = [...fig.querySelectorAll('.dg-ln-end-label.is-ln-end')];
        if (startLabels.length) nudge(startLabels, 'y');
        if (endLabels.length) nudge(endLabels, 'y');
      },
    });
  }

  Object.assign(window.Render.diagram, {
    fishbone, waterfall, treemap, funnel, line,
  });
})();
