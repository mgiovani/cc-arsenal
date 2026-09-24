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
  results.cols = _.layered(nodes, edges, {}).cols;
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
  // p(0) -> q,r (1) -> s (2) -> t (3): two 2-wide forward channels
  // (rank 0 and rank 1), one labelled adjacent edge (s->t), and one
  // rank-skipping edge (p->t) that must take a lane, not a channel jog.
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
  results.channelStats = _.channelStats(layout, edges);
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


def test_chain_stays_in_one_column(results: dict[str, Any]) -> None:
    assert results['cols'] == 1


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


def test_lane_edges_only_the_rank_skipping_edge(results: dict[str, Any]) -> None:
    assert results['laneCount'] == 1


def test_channel_stats_tracks_the_widest_channel(results: dict[str, Any]) -> None:
    two_parallel_edges = 2
    assert results['channelStats']['tracks'] == two_parallel_edges


def test_channel_stats_flags_a_labelled_edge(results: dict[str, Any]) -> None:
    assert results['channelStats']['labeled'] == 1
