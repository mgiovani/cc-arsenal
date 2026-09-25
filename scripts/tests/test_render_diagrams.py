"""Shells out to node to test diagrams.js's pure helpers (Render.diagram._).

Skipped entirely if node isn't on PATH. The harness stubs just enough of
window/document/Render for the file to load without touching a real DOM,
then calls layered/squarify/ticks/check directly and prints one JSON blob.
"""

from __future__ import annotations

import itertools
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
DIAGRAMS_JS = ROOT / 'skills' / 'render' / 'assets' / 'diagrams.js'

HARNESS = r"""
const vm = require('vm');
const fs = require('fs');

const src = fs.readFileSync(process.argv[2], 'utf8');

function StubResizeObserver() { this.observe = () => {}; this.disconnect = () => {}; }
function StubMutationObserver() { this.observe = () => {}; this.disconnect = () => {}; }

const document = {
  documentElement: {},
  fonts: { ready: Promise.resolve() },
  querySelectorAll: () => [],
  createElementNS: () => ({
    setAttribute() {},
    appendChild() {},
    remove() {},
    getBBox: () => ({ width: 0, height: 0 }),
  }),
};
const sandbox = {
  console,
  window: {},
  document,
  requestAnimationFrame: (fn) => setTimeout(fn, 0),
  getComputedStyle: () => ({ getPropertyValue: () => '' }),
  ResizeObserver: StubResizeObserver,
  MutationObserver: StubMutationObserver,
};
sandbox.window.document = document;
sandbox.window.CSS = { escape: (s) => String(s) };
sandbox.Render = {
  esc: (s) => String(s),
  slug: (s) => String(s),
  cap: (s) => s.charAt(0).toUpperCase() + s.slice(1),
  anchored: (o) => o.html,
};
sandbox.window.Render = sandbox.Render;
vm.createContext(sandbox);
vm.runInContext(src, sandbox, { filename: process.argv[2] });

const _ = sandbox.window.Render.diagram._;
const results = {};

{
  const nodes = [{ id: 'a' }, { id: 'b' }, { id: 'c' }, { id: 'd' }];
  const edges = [
    { from: 'a', to: 'b' },
    { from: 'a', to: 'c' },
    { from: 'b', to: 'd' },
    { from: 'c', to: 'd' },
  ];
  const layout = _.layered(nodes, edges, {});
  results.ranks = Object.fromEntries(nodes.map((n) => [n.id, layout.rank.get(n.id)]));
}
{
  const nodes = [{ id: 'a' }, { id: 'b' }, { id: 'c' }];
  const edges = [{ from: 'a', to: 'b' }, { from: 'b', to: 'c' }, { from: 'c', to: 'a' }];
  results.backCount = _.layered(nodes, edges, {}).back.size;
}
{
  const nodes = [{ id: 'a' }, { id: 'b' }, { id: 'c' }, { id: 'd' }];
  const edges = [{ from: 'a', to: 'b' }, { from: 'b', to: 'c' }, { from: 'c', to: 'd' }];
  // A single-file chain never needs a second half-column: cols2 == 2 is one
  // whole node-width, not the old cols == 1.
  results.cols2 = _.layered(nodes, edges, {}).cols2;
}
{
  const values = [6, 6, 4, 3, 2, 2, 1];
  const w = 16; const h = 9;
  const rects = _.squarify(values, w, h);
  results.squarifyArea = w * h;
  results.squarifyTotal = rects.reduce((s, r) => s + r.w * r.h, 0);
  results.squarifyRatios = rects.map((r, i) => (r.w * r.h) / values[i]);
}
{
  results.ticks = _.ticks(-3, 47, 5);
}
{
  const over = { nodes: 10, edges: 2, ids: ['a', 'b'] };
  const dup = { nodes: 2, edges: 1, ids: ['a', 'a'] };
  const ok = { nodes: 2, edges: 1, ids: ['a', 'b'] };
  results.overBudget = _.check('dependency', {}, over);
  results.duplicateIds = _.check('dependency', {}, dup);
  results.withinBudget = _.check('dependency', {}, ok);
}
{
  // p(0) -> q,r (1) -> s (2) -> t (3): a rank-skipping edge (p->t, span 3)
  // now gets its own 2-dummy chain instead of a margin lane -- layered() no
  // longer has ANY lane edges of its own (isLane is a swimlane-only concept
  // once a layout carries chainOf).
  const nodes = [{ id: 'p' }, { id: 'q' }, { id: 'r' }, { id: 's' }, { id: 't' }];
  const edges = [
    { from: 'p', to: 'q' },
    { from: 'p', to: 'r' },
    { from: 'q', to: 's' },
    { from: 'r', to: 's' },
    { from: 's', to: 't', label: 'ships' },
    { from: 'p', to: 't' },
  ];
  const layout = _.layered(nodes, edges, {});
  results.laneCount = _.laneEdges(layout, edges).length;
  const ptInfo = layout.chainOf.get(edges[5]);
  results.ptSpan = ptInfo.span;
  results.ptChainLength = ptInfo.chain.length;
  results.ptRev = ptInfo.rev;
}
{
  // fanFrac spreads siblings evenly, but an odd-sized fan's middle slot
  // must NOT land at exactly 0.5 (its box's own centre) -- that is the
  // exact coincidence a barycenter-centred sibling elsewhere can also
  // land on (R3). n === 1 has no sibling to spread from and stays centred.
  results.fanFracOddMiddle = _.fanFrac(1, 3);
  results.fanFracEven = [_.fanFrac(0, 2), _.fanFrac(1, 2)];
  results.fanFracSingle = _.fanFrac(0, 1);
}
{
  // A parent with two children centres over them (half-column placement):
  // A's own centre lands exactly on the midpoint of B and C's centres.
  const nodes = [{ id: 'A' }, { id: 'B' }, { id: 'C' }];
  const edges = [{ from: 'A', to: 'B' }, { from: 'A', to: 'C' }];
  const layout = _.layered(nodes, edges, {});
  // every real node is 2 half-columns wide
  const centerOf = (id) => layout.pos.get(id).col + 1;
  results.parentCenter = centerOf('A');
  results.childMidpoint = (centerOf('B') + centerOf('C')) / 2;
}
{
  // A 2-cycle's back edge (B->A) is reversed for layering (layFrom is its
  // OWN target, e.to), never lane-routed: span 1 needs no dummy at all.
  const nodes = [{ id: 'A' }, { id: 'B' }];
  const edges = [{ from: 'A', to: 'B' }, { from: 'B', to: 'A' }];
  const layout = _.layered(nodes, edges, {});
  const info = layout.chainOf.get(edges[1]);
  results.backRev = info.rev;
  results.backSpan = info.span;
  results.backChain = info.chain;
  results.backIsLane = _.isLane(layout, edges[1]);
}
{
  // Crafted 3-rank fan-in/fan-out (within the 9-node/12-edge budget) whose
  // barycenter-only ordering leaves 4 crossings; the transpose pass (exact
  // crossing count, dummies included) brings the SAME graph down to 2.
  const nodes = [
    { id: 'a0' }, { id: 'a1' }, { id: 'a2' }, { id: 'a3' },
    { id: 'b0' }, { id: 'b1' }, { id: 'b2' }, { id: 'c0' }, { id: 'c1' },
  ];
  const edges = [
    { from: 'a0', to: 'b0' }, { from: 'a0', to: 'b2' }, { from: 'a1', to: 'b2' },
    { from: 'a2', to: 'b0' }, { from: 'a2', to: 'b1' }, { from: 'a3', to: 'b2' },
    { from: 'a3', to: 'b0' }, { from: 'b0', to: 'c1' }, { from: 'b1', to: 'c1' },
    { from: 'b2', to: 'c0' },
  ];
  const layout = _.layered(nodes, edges, {});
  const byRank = new Map();
  for (const [id, p] of layout.pos) {
    if (!byRank.has(p.rank)) byRank.set(p.rank, []);
    byRank.get(p.rank).push([id, p.col]);
  }
  for (const arr of byRank.values()) arr.sort((x, y) => x[1] - y[1]);
  const orderOf = new Map();
  for (const arr of byRank.values()) arr.forEach(([id], i) => orderOf.set(id, i));
  const ranks = [...byRank.keys()].sort((x, y) => x - y);
  let crossings = 0;
  for (let r = 0; r < ranks.length - 1; r += 1) {
    const pairs = edges
      .filter((e) => (
        layout.pos.get(e.from).rank === ranks[r]
        && layout.pos.get(e.to).rank === ranks[r + 1]
      ))
      .map((e) => [orderOf.get(e.from), orderOf.get(e.to)])
      .sort((x, y) => x[0] - y[0]);
    for (let i = 0; i < pairs.length; i += 1) {
      for (let j = i + 1; j < pairs.length; j += 1) {
        if (pairs[j][1] < pairs[i][1]) crossings += 1;
      }
    }
  }
  results.transposeCrossings = crossings;
}
{
  // Per-channel tracks: a 3-way fan (busy) vs. a single straight edge
  // (quiet) one rank later -- each channel sizes to its OWN load.
  const nodes = [{ id: 'A' }, { id: 'B' }, { id: 'C' }, { id: 'D' }, { id: 'E' }];
  const edges = [
    { from: 'A', to: 'B' }, { from: 'A', to: 'C' },
    { from: 'A', to: 'D' }, { from: 'D', to: 'E' },
  ];
  const layout = _.layered(nodes, edges, {});
  results.busyTracks = layout.channels[0].tracks;
  results.quietTracks = layout.channels[1].tracks;
}
{
  // Port rule regression (R9/R10): a decision-shaped root fanning to two
  // children sits at a DIFFERENT half-column than either child (hop.straight
  // is false -- this is a real elbow candidate, not the trivial same-column
  // case), but each child's own box still overlaps the root's box on the
  // cross axis, exactly the reported S-bend shape. route() must draw each
  // edge as ONE straight segment landing inside that overlap, not an elbow
  // toward the root's own raw centre (which sits outside the left child's
  // box entirely here). A minimal fake DOM stands in for real layout: only
  // the two things route()/wires() actually read, getBoundingClientRect()
  // and a scriptable document.createElementNS('g'), are the pieces under
  // test -- everything else about drawing (paths, markers, labels) is
  // exercised for real, just against rects this test controls directly.
  const nodes = [{ id: 'root' }, { id: 'left' }, { id: 'right' }];
  const edges = [{ from: 'root', to: 'left' }, { from: 'root', to: 'right' }];
  const layout = _.layered(nodes, edges, {});

  const rects = {
    root: { left: 150, top: 0, width: 300, height: 50 }, // x: 150-450
    left: { left: 50, top: 100, width: 200, height: 50 }, // x: 50-250 (overlaps root)
    right: { left: 350, top: 100, width: 200, height: 50 }, // x: 350-550 (overlaps root)
  };
  const nodeEls = nodes.map((n) => ({
    dataset: { id: n.id }, getBoundingClientRect: () => rects[n.id],
  }));
  const canvasRect = { left: 0, top: 0, width: 1000, height: 1000 };
  const svg = {
    textContent: '',
    setAttribute() {},
    appendChild() {},
    querySelectorAll: () => [],
  };
  const fig = {
    dataset: {},
    querySelector: (sel) => {
      if (sel === '.dg-wires') return svg;
      if (sel !== '.dg-canvas') return null;
      return {
        getBoundingClientRect: () => canvasRect,
        scrollWidth: 1000, scrollHeight: 1000, clientWidth: 1000, clientHeight: 1000,
      };
    },
    querySelectorAll: (sel) => (sel === '.dg-node[data-id]' ? nodeEls : []),
  };
  document.createElementNS = () => {
    const attrs = {}; let html = '';
    return {
      setAttribute(k, v) { attrs[k] = v; },
      getAttribute(k) { return attrs[k]; },
      set innerHTML(v) { html = v; },
      get innerHTML() { return html; },
      querySelector(sel) {
        if (sel !== '.dg-line') return null;
        const m = /<path class="dg-line" d="([^"]*)"/.exec(html);
        return m ? { getAttribute: () => m[1] } : null;
      },
    };
  };

  // route() never hands its drawn <g> elements back out, so capture them at
  // the one seam that does: svg.appendChild.
  const edgeD = {};
  const drawn = [];
  svg.appendChild = (g) => drawn.push(g);
  _.route(fig, layout, edges, { dir: 'TB' });
  function pointsOf(d) {
    const cmds = d.match(/[MVHL][^MVHL]*/g) || [];
    let cur = null; const pts = [];
    for (const c of cmds) {
      const cmd = c[0];
      const nums = c.slice(1).trim().split(/\s+/).map(Number);
      if (cmd === 'M') cur = { x: nums[0], y: nums[1] };
      else if (cmd === 'V') cur = { x: cur.x, y: nums[0] };
      else if (cmd === 'H') cur = { x: nums[0], y: cur.y };
      else cur = { x: nums[0], y: nums[1] };
      pts.push({ ...cur });
    }
    return pts;
  }
  for (const g of drawn) {
    const line = g.querySelector('.dg-line');
    const pts = pointsOf(line.getAttribute('d'));
    const to = g.getAttribute('data-to');
    edgeD[to] = pts;
  }
  results.portRuleLeftPoints = edgeD.left.length;
  results.portRuleLeftX = edgeD.left.map((p) => p.x);
  results.portRuleRightPoints = edgeD.right.length;
  results.portRuleRightX = edgeD.right.map((p) => p.x);
}

{
  // TC-1/TC-2: call every public Render.diagram.<type> builder directly (not
  // just the internal Render.diagram._ helpers), one refusal case per
  // honesty/budget rule in references/diagrams.md's "Budgets and honesty"
  // table plus one valid input per type. A refusal is an `.empty`/"Not
  // drawn" block; a case that throws instead (e.g. a rule not landed yet)
  // is recorded as a 'threw:<message>' string so it fails its own
  // assertion cleanly instead of crashing every other case in this fixture.
  const diag = sandbox.window.Render.diagram;
  const DIAGRAM_CASES = [
    ['dependency-over-budget', () => diag.dependency({
      anchor: 'diagram-dep-bad', title: 'Too many nodes',
      nodes: Array.from({ length: 10 }, (_, i) => ({ id: `n${i}`, label: `N${i}` })),
      edges: [],
    })],
    ['dependency-ok', () => diag.dependency({
      anchor: 'diagram-dep-ok', title: 'Small graph',
      nodes: [{ id: 'a', label: 'A' }, { id: 'b', label: 'B' }],
      edges: [{ from: 'a', to: 'b' }],
    })],
    ['sequence-unknown-participant', () => diag.sequence({
      anchor: 'diagram-seq-bad', title: 'Bad message',
      participants: [{ id: 'a', label: 'A' }, { id: 'b', label: 'B' }],
      messages: [{ from: 'a', to: 'z', label: 'hi' }],
    })],
    ['sequence-ok', () => diag.sequence({
      anchor: 'diagram-seq-ok', title: 'Ok exchange',
      participants: [{ id: 'a', label: 'A' }, { id: 'b', label: 'B' }],
      messages: [{ from: 'a', to: 'b', label: 'hi' }],
    })],
    ['state-multiple-initial', () => diag.state({
      anchor: 'diagram-state-bad', title: 'Two starts',
      states: [
        { id: 'a', label: 'A', initial: true }, { id: 'b', label: 'B', initial: true },
      ],
      transitions: [{ from: 'a', to: 'b', label: 'go' }],
    })],
    ['state-ok', () => diag.state({
      anchor: 'diagram-state-ok', title: 'One start',
      states: [{ id: 'a', label: 'A', initial: true }, { id: 'b', label: 'B' }],
      transitions: [{ from: 'a', to: 'b', label: 'go' }],
    })],
    ['flowchart-decision-single-branch', () => diag.flowchart({
      anchor: 'diagram-flow-bad', title: 'One branch',
      nodes: [{ id: 'a', label: 'A', kind: 'decision' }, { id: 'b', label: 'B' }],
      edges: [{ from: 'a', to: 'b', label: 'yes' }],
    })],
    ['flowchart-ok', () => diag.flowchart({
      anchor: 'diagram-flow-ok', title: 'Two branches',
      nodes: [
        { id: 'a', label: 'A', kind: 'decision' },
        { id: 'b', label: 'B' }, { id: 'c', label: 'C' },
      ],
      edges: [{ from: 'a', to: 'b', label: 'yes' }, { from: 'a', to: 'c', label: 'no' }],
    })],
    ['swimlane-unknown-lane', () => diag.swimlane({
      anchor: 'diagram-lane-bad', title: 'Bad lane',
      lanes: [{ id: 'l1', label: 'L1' }],
      steps: [{ id: 's1', label: 'S1', lane: 'zzz' }],
      edges: [],
    })],
    ['swimlane-ok', () => diag.swimlane({
      anchor: 'diagram-lane-ok', title: 'One lane',
      lanes: [{ id: 'l1', label: 'L1' }],
      steps: [{ id: 's1', label: 'S1', lane: 'l1' }],
      edges: [],
    })],
    ['cycle-too-few-stages', () => diag.cycle({
      anchor: 'diagram-cycle-bad', title: 'Two stages',
      stages: [{ id: 'a', label: 'A' }, { id: 'b', label: 'B' }],
    })],
    ['cycle-ok', () => diag.cycle({
      anchor: 'diagram-cycle-ok', title: 'Three stages',
      stages: [{ id: 'a', label: 'A' }, { id: 'b', label: 'B' }, { id: 'c', label: 'C' }],
    })],
    ['architecture-no-zones', () => diag.architecture({
      anchor: 'diagram-arch-bad', title: 'No zones',
      zones: [], components: [], edges: [],
    })],
    ['architecture-ok', () => diag.architecture({
      anchor: 'diagram-arch-ok', title: 'One zone',
      zones: [{ id: 'z1', label: 'Z1' }],
      components: [{ id: 'c1', label: 'C1', zone: 'z1' }],
      edges: [],
    })],
    ['er-unknown-field', () => diag.er({
      anchor: 'diagram-er-bad', title: 'Bad relation',
      entities: [{ id: 'e1', label: 'E1', fields: [{ name: 'id' }] }],
      relations: [{ from: 'e1.id', to: 'e1.zzz', card: '1:n' }],
    })],
    ['er-ok', () => diag.er({
      anchor: 'diagram-er-ok', title: 'One relation',
      entities: [
        { id: 'e1', label: 'E1', fields: [{ name: 'id' }] },
        { id: 'e2', label: 'E2', fields: [{ name: 'id' }, { name: 'e1_id' }] },
      ],
      relations: [{ from: 'e1.id', to: 'e2.e1_id', card: '1:n' }],
    })],
    ['containment-too-deep', () => diag.containment({
      anchor: 'diagram-cont-bad', title: 'Too deep',
      boxes: [{
        label: 'A',
        children: [{
          label: 'B',
          children: [{ label: 'C', children: [{ label: 'D' }] }],
        }],
      }],
    })],
    ['containment-ok', () => diag.containment({
      anchor: 'diagram-cont-ok', title: 'Shallow',
      boxes: [{ label: 'A', children: [{ label: 'B' }] }],
    })],
    ['gantt-bad-date', () => diag.gantt({
      anchor: 'diagram-gantt-bad', title: 'Bad window',
      start: '2024-1-1', end: '2024-01-10',
      tasks: [{ id: 't1', label: 'T1', start: '2024-01-02', end: '2024-01-05' }],
    })],
    ['gantt-ok', () => diag.gantt({
      anchor: 'diagram-gantt-ok', title: 'One task',
      start: '2024-01-01', end: '2024-01-10',
      tasks: [{ id: 't1', label: 'T1', start: '2024-01-02', end: '2024-01-05' }],
    })],
    ['kanban-bad-limit', () => diag.kanban({
      anchor: 'diagram-kanban-bad', title: 'Bad limit',
      columns: [{ id: 'c1', label: 'C1', limit: 0, cards: [] }],
    })],
    ['kanban-ok', () => diag.kanban({
      anchor: 'diagram-kanban-ok', title: 'One column',
      columns: [{ id: 'c1', label: 'C1', limit: 3, cards: [{ label: 'Card 1' }] }],
    })],
    ['storymap-unknown-release', () => diag.storymap({
      anchor: 'diagram-story-bad', title: 'Bad release',
      activities: [{ id: 'a1', label: 'A1', stories: [{ label: 'S1', release: 'zzz' }] }],
      releases: [{ id: 'r1', label: 'R1' }],
    })],
    ['storymap-ok', () => diag.storymap({
      anchor: 'diagram-story-ok', title: 'One story',
      activities: [{ id: 'a1', label: 'A1', stories: [{ label: 'S1', release: 'r1' }] }],
      releases: [{ id: 'r1', label: 'R1' }],
    })],
    ['quadrant-coordinate-out-of-range', () => diag.quadrant({
      anchor: 'diagram-quad-bad', title: 'Bad coordinate',
      x: { label: 'X', low: 'Lo', high: 'Hi' }, y: { label: 'Y', low: 'Lo', high: 'Hi' },
      items: [{ label: 'Item', x: 1.5, y: 0.5 }],
    })],
    // Missing x/y axes: the engine's own refusal for this lands separately
    // (see the calling task); this case pins the contract down regardless
    // of which side lands first.
    ['quadrant-missing-axes', () => diag.quadrant({
      anchor: 'diagram-quad-noaxes', title: 'No axes',
      items: [{ label: 'Item', x: 0.5, y: 0.5 }],
    })],
    ['quadrant-ok', () => diag.quadrant({
      anchor: 'diagram-quad-ok', title: 'One item',
      x: { label: 'X', low: 'Lo', high: 'Hi' }, y: { label: 'Y', low: 'Lo', high: 'Hi' },
      items: [{ label: 'Item', x: 0.5, y: 0.5 }],
    })],
    ['fishbone-too-few-categories', () => diag.fishbone({
      anchor: 'diagram-fish-bad', title: 'One category',
      effect: 'Effect', causes: [{ label: 'C1', items: ['x'] }],
    })],
    ['fishbone-ok', () => diag.fishbone({
      anchor: 'diagram-fish-ok', title: 'Two categories',
      effect: 'Effect',
      causes: [{ label: 'C1', items: ['x'] }, { label: 'C2', items: ['y'] }],
    })],
    ['waterfall-total-mismatch', () => diag.waterfall({
      anchor: 'diagram-wf-bad', title: 'Bad total',
      start: { label: 'Start', value: 100 },
      steps: [{ label: 'S1', delta: 10 }],
      end: { label: 'End', value: 200 },
    })],
    ['waterfall-ok', () => diag.waterfall({
      anchor: 'diagram-wf-ok', title: 'Good total',
      start: { label: 'Start', value: 100 },
      steps: [{ label: 'S1', delta: 10 }],
      end: { label: 'End', value: 110 },
    })],
    ['treemap-sum-mismatch', () => diag.treemap({
      anchor: 'diagram-tm-bad-sum', title: 'Bad sum',
      items: [{ label: 'A', value: 10 }, { label: 'B', value: 10 }], total: 100,
    })],
    ['treemap-cell-too-small', () => diag.treemap({
      anchor: 'diagram-tm-bad-cell', title: 'Tiny cell',
      items: [{ label: 'A', value: 99 }, { label: 'B', value: 1 }],
    })],
    ['treemap-ok', () => diag.treemap({
      anchor: 'diagram-tm-ok', title: 'Two cells',
      items: [{ label: 'A', value: 60 }, { label: 'B', value: 40 }],
    })],
    ['funnel-stage-grows', () => diag.funnel({
      anchor: 'diagram-fn-bad', title: 'Grows',
      stages: [{ label: 'S1', value: 50 }, { label: 'S2', value: 100 }],
    })],
    ['funnel-ok', () => diag.funnel({
      anchor: 'diagram-fn-ok', title: 'Shrinks',
      stages: [{ label: 'S1', value: 100 }, { label: 'S2', value: 50 }],
    })],
    ['line-length-mismatch', () => diag.line({
      anchor: 'diagram-ln-bad', title: 'Bad length',
      x: { ticks: [1, 2, 3], label: 'X' }, y: {},
      series: [{ label: 'S1', values: [1, 2] }],
    })],
    ['line-ok', () => diag.line({
      anchor: 'diagram-ln-ok', title: 'Good length',
      x: { ticks: [1, 2, 3], label: 'X' }, y: {},
      series: [{ label: 'S1', values: [1, 2, 3] }],
    })],
  ];

  results.diagramCases = {};
  for (const [name, fn] of DIAGRAM_CASES) {
    try {
      const html = fn();
      const isEmptyBlock = typeof html === 'string' && html.includes('class="empty"');
      results.diagramCases[name] = isEmptyBlock && html.includes('Not drawn');
    } catch (err) {
      results.diagramCases[name] = `threw:${err.message}`;
    }
  }
}

process.stdout.write(JSON.stringify(results));
"""


@pytest.fixture(scope='module')
def results() -> dict[str, Any]:
    node = shutil.which('node')
    if not node:
        pytest.skip('node not on PATH')
    harness = Path(__file__).with_name('_dg_harness.js')
    harness.write_text(HARNESS, encoding='utf-8')
    try:
        out = subprocess.run(
            [node, str(harness), str(DIAGRAMS_JS)],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
    finally:
        harness.unlink(missing_ok=True)
    return json.loads(out.stdout)


def test_longest_path_ranks(results: dict[str, Any]) -> None:
    assert results['ranks'] == {'a': 0, 'b': 1, 'c': 1, 'd': 2}


def test_cycle_yields_one_back_edge(results: dict[str, Any]) -> None:
    assert results['backCount'] == 1


SINGLE_CHAIN_COLS2 = 2  # one whole node-width in half-columns


def test_chain_stays_in_one_column(results: dict[str, Any]) -> None:
    assert results['cols2'] == SINGLE_CHAIN_COLS2


def test_squarify_areas_sum_to_rect(results: dict[str, Any]) -> None:
    assert results['squarifyTotal'] == pytest.approx(results['squarifyArea'], abs=1e-6)


def test_squarify_areas_proportional_to_value(results: dict[str, Any]) -> None:
    tolerance = 1e-6
    ratios = results['squarifyRatios']
    assert max(ratios) - min(ratios) < tolerance


def test_ticks_include_zero(results: dict[str, Any]) -> None:
    assert 0 in results['ticks']


def test_ticks_are_nice_numbers(results: dict[str, Any]) -> None:
    values = results['ticks']
    domain_min, domain_max = -3, 47
    step = values[1] - values[0]
    assert step > 0
    for a, b in itertools.pairwise(values):
        assert pytest.approx(b - a, abs=1e-9) == step
    assert values[0] <= domain_min
    assert values[-1] >= domain_max


def test_check_refuses_over_budget_dependency(results: dict[str, Any]) -> None:
    assert results['overBudget'] is not None


def test_check_refuses_duplicate_ids(results: dict[str, Any]) -> None:
    assert results['duplicateIds'] is not None


def test_check_allows_within_budget(results: dict[str, Any]) -> None:
    assert results['withinBudget'] is None


def test_layered_never_has_lane_edges_of_its_own(results: dict[str, Any]) -> None:
    # isLane is a swimlane-only (no dummy chain) concept now; a layout with
    # chainOf never reaches it, rank-skipping edges get dummies instead.
    assert results['laneCount'] == 0


RANK_SKIP_SPAN = 3
RANK_SKIP_CHAIN_LENGTH = 4  # layFrom, 2 dummies, layTo


def test_rank_skipping_edge_gets_one_dummy_per_intermediate_rank(
    results: dict[str, Any],
) -> None:
    assert results['ptSpan'] == RANK_SKIP_SPAN
    assert results['ptChainLength'] == RANK_SKIP_CHAIN_LENGTH
    assert results['ptRev'] is False


def test_parent_with_two_children_is_centered(results: dict[str, Any]) -> None:
    assert results['parentCenter'] == pytest.approx(results['childMidpoint'])


def test_back_edge_is_reversed_for_layering_with_no_lane(results: dict[str, Any]) -> None:
    assert results['backRev'] is True
    assert results['backSpan'] == 1
    assert results['backChain'] == ['A', 'B']  # layFrom is e.to (A), not e.from
    assert results['backIsLane'] is False


TRANSPOSE_CROSSINGS_AFTER = 2


def test_transpose_lowers_crossings_on_a_crafted_case(results: dict[str, Any]) -> None:
    # A barycenter-only ordering leaves 4 crossings on this graph; the
    # transpose pass (exact crossing count, dummies included) gets it to 2.
    assert results['transposeCrossings'] == TRANSPOSE_CROSSINGS_AFTER


def test_channel_track_counts_differ_busy_vs_quiet(results: dict[str, Any]) -> None:
    assert results['busyTracks'] > results['quietTracks']


FAN_MID_LO = 0.5
FAN_MID_HI = 0.75


def test_fan_frac_odd_middle_slot_is_off_centre(results: dict[str, Any]) -> None:
    # Regression: this must never be exactly 0.5 (see the R3 coincidence
    # this fix closes), and must still fall strictly inside its own slot.
    fan_frac_odd_middle = results['fanFracOddMiddle']
    assert fan_frac_odd_middle != pytest.approx(FAN_MID_LO)
    assert FAN_MID_LO < fan_frac_odd_middle < FAN_MID_HI


def test_fan_frac_even_sized_fan_is_untouched(results: dict[str, Any]) -> None:
    third = 1 / 3
    assert results['fanFracEven'] == [pytest.approx(third), pytest.approx(2 * third)]


def test_fan_frac_single_port_stays_centred(results: dict[str, Any]) -> None:
    assert results['fanFracSingle'] == pytest.approx(0.5)


STRAIGHT_SEGMENT_POINTS = 2


def test_port_between_overlapping_boxes_is_one_straight_segment(
    results: dict[str, Any],
) -> None:
    # Regression for the S-bend/diagonal-wire fix: a direct edge between two
    # cross-overlapping boxes draws exactly one segment (2 points), never an
    # elbow toward the other node's raw centre.
    assert results['portRuleLeftPoints'] == STRAIGHT_SEGMENT_POINTS
    assert results['portRuleRightPoints'] == STRAIGHT_SEGMENT_POINTS


# TC-1/TC-2: every public Render.diagram.<type> builder, called directly,
# against the "Budgets and honesty" table in references/diagrams.md -- one
# refusal case per documented rule plus one valid input per type that must
# NOT refuse. See the DIAGRAM_CASES table in HARNESS above for the data.
DIAGRAM_CASE_EXPECTATIONS: dict[str, bool] = {
    'dependency-over-budget': True,
    'dependency-ok': False,
    'sequence-unknown-participant': True,
    'sequence-ok': False,
    'state-multiple-initial': True,
    'state-ok': False,
    'flowchart-decision-single-branch': True,
    'flowchart-ok': False,
    'swimlane-unknown-lane': True,
    'swimlane-ok': False,
    'cycle-too-few-stages': True,
    'cycle-ok': False,
    'architecture-no-zones': True,
    'architecture-ok': False,
    'er-unknown-field': True,
    'er-ok': False,
    'containment-too-deep': True,
    'containment-ok': False,
    'gantt-bad-date': True,
    'gantt-ok': False,
    'kanban-bad-limit': True,
    'kanban-ok': False,
    'storymap-unknown-release': True,
    'storymap-ok': False,
    'quadrant-coordinate-out-of-range': True,
    'quadrant-missing-axes': True,
    'quadrant-ok': False,
    'fishbone-too-few-categories': True,
    'fishbone-ok': False,
    'waterfall-total-mismatch': True,
    'waterfall-ok': False,
    'treemap-sum-mismatch': True,
    'treemap-cell-too-small': True,
    'treemap-ok': False,
    'funnel-stage-grows': True,
    'funnel-ok': False,
    'line-length-mismatch': True,
    'line-ok': False,
}


@pytest.mark.parametrize(
    ('case_name', 'expect_refused'), sorted(DIAGRAM_CASE_EXPECTATIONS.items())
)
def test_diagram_builder_refusal(
    results: dict[str, Any], case_name: str, expect_refused: bool
) -> None:
    assert results['diagramCases'][case_name] is expect_refused


ROOT_LEFT_OVERLAP = (150, 250)
ROOT_RIGHT_OVERLAP = (350, 450)


def test_port_between_overlapping_boxes_lands_in_the_overlap(
    results: dict[str, Any],
) -> None:
    # Both points of that one segment share a single x (axis-aligned, R9),
    # and it's a MEANINGFUL x: inside the actual overlap between the root
    # (150-450) and each child (50-250 / 350-550) -- not the root's own raw
    # centre (300), which sits outside the left child's box entirely.
    left_x = results['portRuleLeftX']
    right_x = results['portRuleRightX']
    assert left_x[0] == pytest.approx(left_x[1])
    assert ROOT_LEFT_OVERLAP[0] < left_x[0] < ROOT_LEFT_OVERLAP[1]
    assert right_x[0] == pytest.approx(right_x[1])
    assert ROOT_RIGHT_OVERLAP[0] < right_x[0] < ROOT_RIGHT_OVERLAP[1]
