# Diagrams

Data-driven diagrams: the AI authors plain data, `Render.diagram.<type>` lays
it out with CSS grid and draws connectors by measuring the DOM. See
[blocks.md](blocks.md) for everything else a page is built from, and
`assets/diagram-gallery.html` for every type drawn once with real content.

## Contents

- [When to draw one](#when-to-draw-one)
- [Content shape to type](#content-shape-to-type)
- [The envelope](#the-envelope)
- [Budgets and honesty](#budgets-and-honesty)
- [Accessibility](#accessibility)
- [Flow and behavior](#flow-and-behavior): sequence, state, flowchart, swimlane, cycle
- [Structure](#structure): dependency, architecture, er, containment
- [Planning](#planning): gantt, kanban, storymap, quadrant
- [Analysis and data](#analysis-and-data): fishbone, waterfall, treemap, funnel, line

## When to draw one

A diagram earns its place when the content has a **shape the reader needs and
prose cannot carry**: a fan-out, a cycle, a critical path, a boundary crossing, a
matrix with two real axes. It does not earn its place as decoration, as a
restatement of a list that is already ordered, or as a way to make a page look
considered.

Two tests before drawing:

1. Name the one thing the picture makes obvious that the text does not. If the
   answer is "it summarizes the section", do not draw it.
2. Check the fact is real. A diagram of components that do not exist, or edges
   nobody verified, is worse than no diagram, because it looks authoritative.

A single well-placed diagram beats three. When a page has many candidates, draw
the one carrying the load and let the rest stay lists or blocks.

## Content shape to type

Read the content first, name its shape, then take the type from this table.

| The content is | Use |
|---|---|
| Ordered calls between parties | `sequence` |
| States and the events that move between them | `state` |
| A decision with real branches | `flowchart` |
| Handoffs between roles as a step's owner changes | `swimlane` |
| A loop with no fixed end | `cycle` |
| Zones, and which components cross between them | `architecture` |
| What depends on what | `dependency` |
| Records with fields and the keys that link them | `er` |
| What's nested inside what | `containment` |
| A schedule of bars against a date window | `gantt` |
| Work in progress, read left to right | `kanban` |
| Releases crossed with activities | `storymap` |
| A ranking on two independent axes | `quadrant` |
| Causes feeding one effect | `fishbone` |
| A running total moving up and down | `waterfall` |
| A whole broken into parts by value | `treemap` |
| A sequence that can only shrink | `funnel` |
| A trend across ordered ticks | `line` |
| A before and after, or pros and cons, in prose | `split` (a block, not a diagram, see [blocks.md](blocks.md)) |

When two rows fit, pick the one whose shape carries the point. A plan step
list with handoffs is `swimlane` only if the handoffs are the point;
otherwise `steps`.

## The envelope

Every call is `Render.diagram.<type>({ anchor: 'diagram-<slug>', title,
...data })`. `anchor` must start with `diagram-` (the feedback-loop
convention); `title` is the conclusion, one sentence, not a caption. There is
no other shared field: a type that doesn't need a direction or a
critical-path flag doesn't get one. Each call returns one anchored
`<figure class="dg dg-<type>">`: an HTML grid of nodes, an `aria-hidden` SVG
overlay for connectors, a caption, and a `.dg-sr` text alternative. Never
call a builder twice expecting a second figure out of one call.

A page using any diagram links both engine files, right after their `page.*`
counterparts:

```html
<link rel="stylesheet" href="../page.css">
<link rel="stylesheet" href="../diagrams.css">
...
<script src="../page.js"></script>
<script src="../diagrams.js"></script>
```

Every diagram is hue-free. A `key`/`sunk`/`soft` flag on a node or edge maps
to a class the CSS already paints:

- `key` → `is-key`, an ink fill or heavier stroke, for the thing the diagram
  is about.
- `sunk` → `is-sunk`, a muted fill, for context rather than subject.
- `soft` → `is-soft`, a dashed stroke, for a weak or inferred relationship.

Don't derive these by hand (a custom fill, a stroke color, a dash pattern);
pass the flag and let the type draw it.

## Budgets and honesty

Going over a type's budget is a refusal, not a warning that still draws
something smaller. `check()` also refuses a duplicate id regardless of type;
each type then adds its own honesty rule on top and refuses with its own
message rather than draw something misleading.

| Type | Budget | Refuses when |
|---|---|---|
| `dependency` | 9 nodes, 12 edges | an edge names an id not in `nodes` |
| `sequence` | 5 participants, 12 messages | zero messages, or a message names an unknown participant |
| `state` | 9 states, 12 transitions | more than one initial state, a transition with no label, or an unknown id |
| `flowchart` | 9 nodes, 12 edges | a decision with a single outgoing edge or an unlabeled branch, or an unknown id |
| `swimlane` | 5 lanes, 9 steps, 12 edges | a step names an unknown lane, a lane has no steps, or an edge names an unknown id |
| `cycle` | 6 stages (also refuses fewer than 3) | fewer than 3 stages or more than 6 |
| `architecture` | 4 zones, 9 components, 12 edges | no zones at all, a component names an unknown zone, a zone has no components, or an edge names an unknown id |
| `er` | 8 entities, 8 fields each, 12 relations | a relation names an unknown entity or field, or a `card` that isn't `1:1`/`1:n`/`n:1`/`n:m` |
| `containment` | 12 boxes total, 3 levels deep | no boxes at all |
| `gantt` | 12 tasks | a bad date, a task's start after its own end, a task outside the window, or a task starting before its `after` predecessor ends |
| `kanban` | 5 columns, 6 cards each | a `limit` that isn't a positive integer |
| `storymap` | 6 activities, 3 releases, 4 stories per cell | a story names a release id not in `releases`, or an activity has no stories at all |
| `quadrant` | 12 items | a coordinate outside 0..1, or an axis missing its label, low or high |
| `fishbone` | 6 categories, 4 causes each | fewer than 2 categories, or a category with no causes |
| `waterfall` | 8 steps | `start + Σdelta ≠ end` |
| `treemap` | 8 cells | a value ≤ 0, an item under 2% of the total, or items that don't sum to `total` |
| `funnel` | 6 stages | a value ≤ 0, or a stage larger than the one before it |
| `line` | 4 series × 12 points (8 series when 2 ticks make it a slope chart) | a series length that doesn't match `x.ticks`, or a non-finite value |

A refusal renders as an `.empty` block instead of a figure:

```html
<div class="empty">
  <p class="title">Not drawn: <the title></p>
  <p class="text"><the reason, plain sentence></p>
</div>
```

and logs `console.warn('[render diagram] ...')` once. A page that ships this
in production is a bug; the gallery's one deliberate refusal example is the
only place it belongs.

**Split, don't override.** There is no per-page way to raise a budget or
silence a refusal. Data over budget gets rewritten smaller, split one
`architecture` into a diagram per zone, one long `gantt` into a diagram per
phase, never padded past what a reader can actually follow.

## Accessibility

- Labels are real HTML text inside `.dg-node`/`.dg-label`, never SVG `<text>`
  standing in for them, so they wrap, reflow and stay selectable.
- The connector SVG is `aria-hidden="true" focusable="false"`; it exists to
  draw lines a sighted reader follows, not to carry meaning a screen reader
  needs.
- Every relation that only exists as a drawn line is spelled out in prose in
  the figure's `.dg-sr` text alternative (a cycle's back edge, a swimlane's
  cross-lane handoff, an ER relation's cardinality).
- No hue anywhere: `key` is an ink fill or heavier stroke, `sunk` is a muted
  fill, `soft` is a dashed stroke. A critical path or a failed node is never
  color alone.
- 15px is the floor. Nothing in a diagram, including an SVG-adjacent label or
  an axis tick, renders smaller than the rest of the page.

## Flow and behavior

### sequence

Who calls whom, in order, including a reply and a self-call. A graph can't
show order, only structure.
Data: `{ anchor, title, participants: [{id, label, sub?}], messages: [{from, to, label, key?, soft?}] }`.
A message with `from === to` is a self-call, drawn as a small loop off the
lifeline. `soft` marks a reply or an async message.
Modes: explain, tour.
Don't: use it for anything without a strict call order; a request that just
fans out is a `flowchart` or `dependency`.

### state

What a thing can be, and what moves it from one state to the next.
Data: `{ anchor, title, states: [{id, label, sub?, initial?, final?, key?, sunk?}], transitions: [{from, to, label, key?, soft?}], dir?: 'TB'|'LR' }`.
The initial state carries a filled square marker with a short arrow into it;
a final state gets a double rule. A back edge (a state that returns to an earlier one) is
reversed for layering and drawn entering the earlier state from below,
instead of being refused or taking a margin lane.
Modes: explain, map.
Don't: label a transition with only the destination; every transition needs
the event that triggers it.

### flowchart

A decision tree with real branches. The point is the decision, not just the
steps either side of it.
Data: `{ anchor, title, nodes: [{id, label, sub?, kind: 'step'|'decision'|'terminal', key?, sunk?}], edges: [{from, to, label?, key?, soft?}], dir?: 'TB'|'LR' }`.
A decision is a double border; a terminal is a sunk fill. Branch labels sit
at the source end of the edge they name.
Modes: explain, tour.
Don't: give a decision node a single outgoing edge, or leave a branch
unlabeled; that's not a decision, it's a step.

### swimlane

Who does each step, when the step's owner changes partway through. The
handoffs are the point, not just the order.
Data: `{ anchor, title, lanes: [{id, label}], steps: [{id, lane, label, sub?, key?, sunk?}], edges: [{from, to, label?, key?, soft?}] }`.
Lane headers stay pinned while the diagram scrolls sideways at narrow
widths. A cross-lane edge is named as a "handoff" in the text alternative.
Modes: explain, map.
Don't: put a step in a lane you didn't declare, or declare a lane with
nothing in it.

### cycle

A loop with no fixed end. The last stage feeds back into the first, on
purpose.
Data: `{ anchor, title, stages: [{label, sub?, key?}], center? }`.
3 to 6 stages, laid out clockwise on two rows; `center` sits in the gap
between them.
Modes: explain.
Don't: use it for a process with a real end; that's `flowchart` or
`dependency`.

## Structure

### dependency

What depends on what: fan-in, fan-out, and cycles (a tree can't show
either). Replaces the old hand-drawn `graph` block.
Data: `{ anchor, title, nodes: [{id, label, sub?, key?, sunk?}], edges: [{from, to, label?, key?, soft?}], dir?: 'TB'|'LR', critical?: true }`.
A cycle's back edge is reversed for layering (drawn entering its target from
below, not detoured through a margin lane) and named in the text alternative
("Cycle: a → b → a") instead of refusing. A rank-skipping edge gets a dummy
waypoint per intermediate rank so it still runs a straight or single-elbow
line, never a far-margin detour. `critical: true` walks back from the
deepest node and marks the path `is-key`.
Modes: map, explain, tour, plan (via `dir: 'LR', critical: true`).
Don't: pass coordinates; this type lays itself out. Don't use it for a pure
hierarchy with no cross-links; that's `containment`.

### architecture

An architecture of zones, and which components in one zone call into
another. Zones are a fixed rank (one grid column each, left to right);
components inside a zone are ordered the same way any layered diagram
orders its nodes. A filled square marks every place a route crosses a zone
boundary, since that crossing is the point of the diagram.
Data: `{ anchor, title, zones: [{id, label}], components: [{id, label, sub?, zone, key?, sunk?}], edges: [{from, to, label?, key?, soft?}] }`.
Modes: map, explain, tour (fixed left-to-right; no `dir` option).
Don't: pass coordinates. Don't reach for it when nothing is grouped into
zones; that's `dependency`. An edge into an earlier zone is honest, not an
error: it's reversed for layering and drawn entering that earlier zone, the
same as any other back edge, with the crossing marker at the zone boundary.

### er

An entity-relationship diagram: what field on one entity references what
field on another, and the cardinality of that reference. Entities are
layered left to right from the referencing entity to the referenced one;
each relation's line is pinned to its exact field row instead of fanning to
the entity's centre, with a small tick (`one`) or crow's foot (`many`) at
each end.
Data: `{ anchor, title, entities: [{id, label, sub?, fields: [{name, type?, pk?, fk?}]}], relations: [{from: 'entity.field', to: 'entity.field', card: '1:1'|'1:n'|'n:1'|'n:m', label?}] }`.
Modes: map, explain, tour.
Text alternative: "grouping.skills → skill.name, one to many (groups)".
Don't: point a relation at a whole entity when it means one field; the field
is what the tick or crow's foot lines up with. Don't use it for anything
without fields and cardinality; that's `dependency` or `containment`.

### containment

Nesting: what's inside what, up to three levels deep. Pure HTML boxes with no
overlay at all; the nested list structure is itself the text alternative, so
there's no separate `.dg-sr` block. A box's fill alternates panel/sunk by
depth unless its data says `sunk` explicitly.
Data: `{ anchor, title, boxes: [{label, sub?, key?, sunk?, children?: [...]}] }`, recursively.
Modes: map, explain, tour.
Don't: use it for anything that branches or merges (a component calling
another across the tree); that's `dependency` or `architecture`. Don't list a
sibling that doesn't help explain the ones that matter.

## Planning

### gantt

A schedule: bars against a date window, finish-to-start links, an optional
today line and milestones.
Data: `{ anchor, title, start, end, today?, tasks: [{id, label, start, end, status?: 'done'|'active'|'planned', after?, milestone?, key?}] }`
(all dates `YYYY-MM-DD`).
Modes: none (one layout).
Don't: pass a `status` other than done/active/planned expecting it to draw;
unknown statuses fall back to planned. Don't chain more than one `after` per
task, that's a future concern, not this type's.

### kanban

A board: columns of cards, read left to right.
Data: `{ anchor, title, columns: [{id, label, limit?, cards: [{label, sub?, key?, blocked?}]}] }`.
A column over its `limit` still draws, with the count at ink weight 600 and
an "over limit by N" note for screen readers, since going over WIP is
information, not a drawing error.
Modes: none.
Don't: use `blocked` to mean "done"; it renders as a dashed border plus a
"Blocked" tag, a distinct state from `key`.

### storymap

A backbone (activities) crossed with releases (shipping order), each cell a
handful of stories.
Data: `{ anchor, title, releases: [{id, label}], activities: [{id, label, stories: [{label, release, key?}]}] }`
(`releases` in shipping order).
Modes: none.
Don't: expect a cell with zero stories for one release to draw a note; an
empty cell is silent, only a wholly story-less activity refuses.

### quadrant

A 2x2 plot: items placed by two 0..1 scores, labelled corners.
Data: `{ anchor, title, x: {label, low, high}, y: {label, low, high}, quadrants?: {tl, tr, bl, br}, items: [{label, x, y, key?}] }`
(`x`/`y` on each item in 0..1).
Modes: none. `quadrants` overrides the four auto-derived corner labels when
the default "high y, low x"-style phrasing doesn't fit the data.
Don't: pass a coordinate outside 0..1 expecting it to clamp, or leave out an
axis's label, low or high; both are refusals. Colliding labels are spread
apart automatically, don't pre-offset them yourself.

## Analysis and data

### fishbone

A cause-and-effect diagram: categories of causes feeding one effect, no
diagonal lines.
Data: `{ anchor, title, effect, causes: [{label, items: [string]}] }`.
Modes: explain, review, audit.
Don't: pass fewer than 2 categories or a category with no causes; both
refuse.

### waterfall

A running total moving up and down through named steps, with a connector
between each consecutive total.
Data: `{ anchor, title, start: {label, value}, steps: [{label, delta}], end: {label, value}, unit? }`.
Modes: report, review, compare.
Don't: pass a `start`/`steps`/`end` whose sum doesn't reconcile
(`start + Σdelta ≠ end`); it refuses rather than draw a chart that lies.

### treemap

A whole broken into parts sized by value, squarified into a 16:9 rectangle.
Data: `{ anchor, title, items: [{label, value, sub?, key?}], total? }`.
Modes: report, audit, map.
Don't: pass a non-positive value, an item under 2% of the total (fold it into
an "Other" cell first), or items that don't sum to `total` when given; all
three refuse.

### funnel

Sequential stages that can only shrink, with the conversion from each stage
to the next.
Data: `{ anchor, title, stages: [{label, value}] }`.
Modes: report, review.
Don't: pass a non-positive value or a stage larger than the one before it
("not a funnel"); both refuse.

### line

A trend across ordered x-axis ticks; the same builder draws a slope chart
(direct end labels on both ends, no gridline crowding) when there are
exactly 2 ticks.
Data: `{ anchor, title, x: {label, ticks}, y: {label, unit?}, series: [{label, values, key?}] }`.
Modes: report, review, compare.
Don't: pass a series whose `values` length doesn't match `x.ticks`, or a
non-finite value; both refuse. There is no legend: series carry a direct end
label instead.

## Gallery

`assets/diagram-gallery.html` draws every type above once with real content
from this repo, plus one deliberate refusal example. Open it before
composing a page with diagrams: it is the visual contract, the same way
`assets/gallery.html` is for blocks.

## Generative and decorative graphics

For anything with many elements or motion, reach for Canvas rather than
hand-authoring long SVG path data. Do not hand-write path data approximating
a picture: crisp geometry is first class, sketch-style illustration is not.
