# Blocks

The building blocks every render page is composed from. Styles live in
`assets/page.css`, and `assets/gallery.html` shows each one once with real
content. Open the gallery before composing a page: it is the visual contract.

Blocks exist to replace walls of text. When content has a shape (an order, a
comparison, a before and after, a number per item), a block shows that shape and
a paragraph hides it. Prefer a block whenever content has a shape, and keep
prose for the reasoning that connects blocks.

## Content shape to block

Read the content first, name its shape, then take the block from this table.

| The content is | Use |
|---|---|
| The one-sentence answer to the page's question | `tldr` |
| A handful of labelled values about one subject | `facts` |
| Counts that add up to a whole | `tally` |
| A risk, a decision or a caveat the reader must not miss | `callout` |
| A list of items the reader judges one by one | `row` |
| An item that needs its code evidence beside it | `finding` |
| Several loose options of equal weight | `idea` |
| Conditions that are either met or not | `checklist` |
| A code excerpt to point at | `code` |
| A before and after of code | `diff` (unified or split) |
| Code whose lines each need an explanation | `annot` |
| Records with the same fields | `table` |
| Options scored against criteria | `matrix` |
| Two dimensions of numbers | `heat` |
| One number per item | `bars` |
| A sequence where order matters | `steps` |
| Events with dates or times | `timeline` |
| A pipeline where each stage feeds the next | `flow` |
| A structure that branches or merges | `graph` |
| An architecture of stacked levels | `layers` |
| Files and folders, with the ones a change touches | `tree` |
| A before and after, or pros and cons, in prose | `split` |
| Detail most readers can skip | `disclosure` |
| Two or more views of the same thing | `tabs` |
| A list with nothing in it | `empty` |

When two rows fit, pick the one whose shape carries the point. A plan step list
with dates is `timeline` only if the dates are the point; otherwise `steps`.

## Page frame

Every page follows the skeleton in [page-kit.md](page-kit.md): toolbar, optional
shortcuts panel, then `<main class="wrap" id="root">` holding sections. Wide
modes use `<main class="wrap wrap-wide">` with a `toc` rail. Every template
carries the same waiver comment right after `<title>` (see `gallery.html`),
exactly this line, because Geist is the typeface the brief mandates and a
trailing rationale after `--` reads as a dash to the linter:

```html
<!-- impeccable-disable overused-font -->
```

A section is `<section class="section" data-section="Name" id="slug">` with an
`<h2>` (or `.section-head` holding the `<h2>` and a `.meta` count). Subgroups use
`<h3>`. A page may open with `.page-head` (`<h1>` plus a `.meta` line).

Shared text classes: `.title` (item name, 500), `.meta` (secondary, 15px),
`.text` (short description, 15px, muted), `.mono` (identifiers, paths, code),
`.num` (right-aligned tabular numbers). Mono is for identifiers, code, paths and
counts only.

### Type notes

15px is the floor: nothing on a render page renders smaller, not meta, tags,
kbd, line numbers, code, counts, legends or SVG labels. Hierarchy comes from
weight (400/500/600) and color (`--ink`, `--mute`, `--soft`), not from
shrinking text.

## Render API

`page.js` exposes `window.Render`:

| Call | Returns |
|---|---|
| `Render.esc(s)` | HTML-escaped text |
| `Render.slug(s)` | a lowercase, hyphenated slug |
| `Render.cap(s)` | `s` with its first letter capitalised |
| `Render.path(p)` | escaped text with a `<wbr>` after every `/`, so a long path wraps at a segment boundary, not mid-word; use it for any path shown in `.facts dd.mono` or a `.path` figcaption |
| `Render.anchored({anchor, label, cls, facets, verdict, html})` | one `.anchored` article: mark button, `.body`, and (if `verdict: true`) an appended `Render.verdict(anchor)` |
| `Render.verdict(anchor)` | a `.verdict.seg[data-for]`: empty before `Render.init()`, filled buttons after (see Anchored blocks below) |
| `Render.init({verdicts, file, title})` | wires the page: loads state, builds `.counts`/`.seg[data-filter="verdict"]`, fills verdict placeholders, paints state, wires keyboard and click handling. `verdicts` is an ordered array (positive, middle, negative) or `null` for a comments-only mode. Idempotent. |
| `Render.getPage(key)` / `Render.setPage(key, value)` | reads/writes a page-level decision (see `pick` in Primitives and feedback-loop.md) |

## Anchored blocks

Any block the reader can comment on is wrapped as an anchored block:

```html
<article class="anchored row" data-anchor="finding-src-auth-py-42-timing-compare"
         data-label="Timing-unsafe token compare" data-facet-severity="high">
  <button class="mark" type="button" aria-label="Comment on Timing-unsafe token compare">+</button>
  <div class="body"> ...block content... </div>
</article>
```

- `data-anchor` is content-derived and unique, per
  [feedback-loop.md](feedback-loop.md). `data-label` is always set.
- `data-facet-<name>` feeds a toolbar filter `.seg[data-filter="<name>"]`.
- The mark hangs in a 40px left gutter on desktop and moves to a right rail
  under 720px, always visible there. The runtime fills it with a count
  (`.mark.has`), adds `.comments` and `.composer` inside `.body`, sets
  `data-vrank` for the chosen verdict, `.is-current` for keyboard focus and
  `hidden` when filtered out.
- The verdict control goes inside `.body`, usually at the end of `.head`. Build
  it with `Render.verdict(anchor)` (or `Render.anchored({..., verdict: true})`,
  which appends the same markup) rather than writing the buttons by hand:

```js
Render.verdict('finding-src-auth-py-42-timing-compare')
```

  Before `Render.init()` has a vocabulary to draw from, this returns an empty
  placeholder; after init, or once init runs over placeholders already in the
  page, it is the three buttons:

```html
<div class="verdict seg" role="group" aria-label="Verdict" data-for="finding-src-auth-py-42-timing-compare">
  <button type="button" data-v="keep" aria-pressed="false">Keep</button>
  <button type="button" data-v="change" aria-pressed="false">Change</button>
  <button type="button" data-v="drop" aria-pressed="false">Drop</button>
</div>
```

  Order-independent: **call `Render.init()` first, then mount; either order
  works.** Building markup and inserting it before `Render.init()` runs (the
  usual template shape: build the page's HTML, then call `Render.init()`) is
  fine, `Render.verdict()`/`Render.anchored({verdict: true})` never throw on a
  null config, and `Render.init()` fills every empty `.verdict[data-for]` it
  finds and paints its state in one pass. Calling `Render.init()` before
  mounting works too: by then the vocabulary is set, so `Render.verdict()`
  returns the filled buttons directly. `Render.init()` itself is idempotent,
  safe to call more than once.
  Order is fixed: positive, middle, negative. The pressed segment is an ink
  fill, so its position reads the decision down a long list. Negative
  (`data-vrank="3"`) strikes the title and softens the body.
- A table cell can be anchored too (`<td class="anchored">` with the same mark
  and body); its mark sits in the cell corner.

Don't: derive an anchor from position (`step-3`), or leave `data-label` off.

## At a glance

### tldr

The page's answer in one or two sentences, 20px. It replaces any hero.
Markup: `<p class="tldr">...</p>`. Modes: explain, report, review, audit, tour.
Don't: add a label or kicker above it; the sentence is the heading.

### facts

A few labelled values in a hairline-shared grid.
Markup: `<dl class="facts"><div><dt>Files changed</dt><dd>8</dd></div>...</dl>`;
add `class="mono"` on a `dd` holding an identifier. Modes: report, diff, review,
explain. Don't: blow one value up into a big-number hero metric.

### tally

Counts that sum to a whole, plus one stacked bar in four neutral shades.
Markup: `<div class="tally"><dl class="tally-counts"><div class="s1"><dt>Tests</dt><dd>107</dd></div>...</dl><div class="tally-bar" aria-hidden="true"><i class="s1" style="--v:107"></i>...</div></div>`.
Shades `s1` (ink) to `s3` (light), `s0` for the remainder or undecided; `--v`
is the raw count. Modes: review, audit, report, prd. Don't: use more than four
segments or show a bar without its counts.

### callout

A Note, Risk or Decision the reader must not miss, set off by a 1px ink rule.
Markup: `<aside class="callout" data-kind="risk|decision|note"><span class="callout-label">Risk</span><p>...</p></aside>`.
Modes: all. Don't: stack more than three in a row or use one for ordinary prose.

## Items

### row

The default item: one line of head, an optional description, hairline-shared
with its neighbours. Wrap consecutive rows in `<div class="list">`.
Markup: `.anchored.row > .body > .head` holding a severity tag, `.title`,
`.meta`, the verdict control; then `p.text` and an optional `cite.source`.
Modes: prd, plan, review, audit, report. Don't: put paragraphs in the head.

### finding

A row with its code evidence underneath.
Markup: as `row` with class `finding`, plus a `figure.code` after `.text`.
Modes: review, audit, diff. Don't: paste more than about 12 lines; link the rest.

### idea

Options of equal weight in a grid of hairline-shared cells.
Markup: `<div class="ideas">` of `.anchored.idea`, each `.body` holding `.title`,
`p.text` (the tension it resolves), `.meta` (theme) and the verdict control.
Modes: brainstorm, compare. Don't: float them as separate shadowed cards.

### checklist

Conditions met or not.
Markup: `<ul class="checklist"><li class="done"><span class="box" aria-hidden="true"></span><span>...</span></li></ul>`;
omit `done` for open items. Modes: plan, prd, report. Don't: use it for items
the reader is meant to vote on; that is `row` with a verdict.

## Code

### code

An excerpt with a path header, line numbers and highlighted lines.
Markup:
`<figure class="code"><figcaption><span class="path">src/auth.py</span><span class="meta">L40-46</span></figcaption><div class="lines"><span class="ln" data-n="42">...</span><span class="ln hl" data-n="43">...</span></div></figure>`.
Each `.ln` keeps its own whitespace; escape `<`, `>` and `&`. The block
scrolls sideways inside itself. Modes: review, audit, explain, tour, diff.
Don't: syntax-colour it; highlight the lines that matter with `.hl` instead.

### diff

A change, unified or split. Lines carry `.add`, `.del`, `.hunk` or nothing
(context); the sign is the first character of the text. Added lines are a
light fill at weight 500, removed lines are `--soft`.
Unified: `<figure class="diff"><figcaption><span class="path">...</span><span class="diff-stat">+4 -1</span></figcaption><div class="lines">...</div></figure>`.
Split: replace `.lines` with `<div class="diff-split">` holding two `<div>`s, each
an `<h4>` (Before, After) and a `.lines`; pad the shorter side with
`<span class="ln pad" data-n=""> </span>`. Split stacks under 720px.
Modes: diff, review, plan. Don't: show a whole file; one hunk per block.

### annot

Code on the left, numbered notes on the right; stacks under 860px.
Markup: `<div class="annot"><figure class="code">...lines with <span class="pin">1</span> at the end...</figure><ol class="notes"><li><span class="pin">1</span><span><b>Claim.</b> Detail.</span></li></ol></div>`.
Modes: explain, tour, review. Don't: annotate more than five lines in one block.

## Data

### table

Records with the same fields. Borderless, rules between rows, sticky header,
numbers right-aligned in tabular figures.
Markup: `<div class="table-scroll"><table class="table"><thead>...</thead><tbody>...</tbody><tfoot>...</tfoot></table></div>`;
numeric cells take `class="num"`. Modes: audit, report, prd, compare. Don't:
put a table outside `.table-scroll`; wide tables must scroll in place.

### matrix

Options (columns) against criteria (rows), with evidence in every cell.
Markup: `<table class="matrix">` in a `.table-scroll`; row headers are
`<th>Criterion<span class="meta">weight 3</span></th>`; each cell holds
`<span class="score"><span class="pips" aria-label="4 of 5"><i class="on"></i>...</span>4</span><span class="text">evidence</span>`.
Mark the chosen option with `class="win"` on its `th` and cells. Modes: compare.
An interactive matrix adds a `.pick` button per option header (see Primitives)
so the reader can pick a winner rather than only see a static one. Don't: leave
a cell without evidence.

### heat

Two dimensions of numbers, filled by magnitude with the value always printed.
Markup: `<div class="heat-scroll"><table class="heat">` with row headers as
`<th>` and cells `<td data-h="0..5">value</td>`, plus an optional
`.heat-legend`. Pick `data-h` from fixed thresholds and state them in the caption.
Modes: audit, report, map. Don't: drop the numbers and leave only shading.

### bars

One number per item, as inline bars with no background track.
Markup: `<ol class="bars"><li><span class="label">...</span><span class="bar"><i style="--v:.62"></i></span><span class="value">131</span></li></ol>`;
`--v` is the value over the maximum (0 to 1). `.bar.dim` greys a bar that is
context rather than subject. Modes: report, audit, review. Don't: sort bars any
way but by value unless the order itself is the data.

## Structure

### steps

A sequence where order matters, joined by a 1px connector.
Markup: `<ol class="steps"><li class="step" data-state="done|todo"><span class="step-n">1</span><div class="step-c"><span class="title">...</span><p class="text">...</p></div></li></ol>`.
Anchored: `<li class="anchored" data-anchor=...><button class="mark">...</button><div class="body step">...</div></li>`.
Modes: plan, tour, explain. Don't: number things whose order means nothing.

### timeline

Dated events along a vertical rule.
Markup: `<ol class="timeline"><li class="event" [data-state="minor"]><time datetime="...">2026-09-16 16:13</time><div class="what"><span class="title">...</span><span class="meta">...</span></div></li></ol>`.
Anchored: the `.event` class goes on the `.body`. Modes: timeline, report,
review. Don't: use it for undated steps.

### flow

A pipeline of stages, horizontal on desktop and vertical under 720px.
Markup: `<ol class="flow"><li class="stage [key]"><span class="title">...</span><span class="meta mono" title="fn()">fn()</span></li></ol>`.
`key` marks the stage the page is about. The function name is single-line with
an ellipsis, never a mid-word wrap; the `title` attribute carries the full text
for a name too long to show. Modes: explain, map, tour. Don't: use it for
branching structure; that is `graph`.

### graph

Inline SVG for structure that branches or merges, per
[diagrams.md](diagrams.md). Square nodes, 1px edges, emphasis by stroke weight.
Markup: `<div class="graph"><svg viewBox="..." role="img" aria-labelledby="t"><title id="t">The conclusion</title><g class="edge [key|soft]"><path .../></g><g class="node [key|sunk]"><rect .../><text .../></g></svg></div>`.
Define arrowheads as `<marker>` elements (add `class="key"` for the heavy one).
Modes: map, explain, tour. Don't: set `rx`, a fill colour, or a pixel width.

### layers

An architecture of stacked levels, top level first.
Markup: `<ol class="layers"><li [class="key"]><span class="layer-name">Runtime<span class="meta">page.js</span></span><span class="layer-items"><span class="tag">...</span></span></li></ol>`.
Modes: map, explain, tour. Don't: draw arrows between layers; that is `graph`.

### tree

Files and folders, with the touched ones marked.
Markup: `<ul class="tree"><li class="dir"><span class="name">src/</span><ul><li data-touch="add|mod|del"><span class="name">auth.py</span><span class="touch">M</span></li></ul></li></ul>`;
`.note` adds a short comment after a name. Modes: diff, plan, map, tour.
Don't: list untouched siblings unless they explain the touched ones.

### split

Two sides compared in prose: before and after, pros and cons.
Markup: `<div class="split"><div class="side before"><h4 class="side-h">Before</h4><ul><li>...</li></ul></div><div class="side after">...</div></div>`.
Stacks under 720px. Modes: compare, diff, explain. Don't: use it for code;
code before and after is `diff`.

## Frame blocks

### toolbar

`<header class="toolbar">` holds one or two rows, sticky as a single unit
under one hairline:

```html
<header class="toolbar">
  <div class="toolbar-row">
    <span class="toolbar-title">...</span>
    <div class="counts" aria-label="Counts"></div>
    <span class="spacer"></span>
    <div class="seg" role="group" aria-label="Theme" data-theme-toggle>...</div>
    <div class="toolbar-group">
      <button class="btn" data-action="digest">Copy digest</button>
      <button class="btn btn-icon" data-action="shortcuts" aria-label="Keyboard shortcuts" aria-expanded="false" aria-controls="shortcuts">?</button>
      <button class="btn btn-primary" data-action="save">Save</button>
    </div>
  </div>
  <div class="filterbar">
    <div class="seg" data-filter="verdict" role="group" aria-label="Filter by verdict"></div>
    <!-- more .seg[data-filter="<facet>"] controls, hand-authored with their buttons; then optionally a right-aligned .meta -->
  </div>
</header>
```

`.counts` and `.seg[data-filter="verdict"]` ship empty exactly like that:
`Render.init()` writes their contents from the page's verdict vocabulary, and
replaces whatever they already hold, so nothing else should populate them. In
a verdict mode `.counts` gets one tile per verdict value plus `undecided`
(labels lowercase as given, e.g. "won't fix"); the filter seg gets All,
Undecided, then each verdict capitalised. In a comments-only mode (`verdicts:
null`) `.counts` gets a single "N comments" tile that updates as comments are
added or deleted, and `.seg[data-filter="verdict"]` is removed outright, so
templates for those modes can still ship it and let init tear it down. Any
other `.seg[data-filter="<facet>"]` (severity, kind, ...) is not vocabulary-
driven and keeps its hand-authored buttons.

`.toolbar-row` is `--bar` (52px); `.filterbar` is 48px with a hairline above
it, dividing it from the row. A page with no verdicts and no facet filters
omits `.filterbar` entirely. At 720px and under the header stops being sticky
and each row scrolls sideways as one line rather than wrapping into several
stacked rows; the title truncates with an ellipsis instead of pushing other
controls off. Don't: add a logo, a third row, or a blurred background.

### toc

The rail for wide pages, shown from 1100px.
Markup: `<nav class="toc" aria-label="On this page"><h2>On this page</h2><ol><li><a href="#id" aria-current="true">...</a></li></ol></nav>`.
Don't: use it on a page with fewer than four sections.

### tabs

Views of the same thing.
Markup: `<div class="tabs" role="tablist"><button role="tab" aria-selected="true" aria-controls="p1">...</button></div><div role="tabpanel" id="p1">...</div>`;
switching sets `aria-selected`, `tabindex` and `hidden`. Don't: hide content the
reader must see to decide; tabs are for alternate views, not for chapters.

### disclosure

Detail most readers skip, on native `<details>`. No container box: a hairline
runs between items (and above the first), and the native marker is replaced by
a plus that flattens to a minus when open, drawn as two 1px CSS bars, not a
glyph.
Markup: `<details class="disclosure"><summary>Question<span class="meta">source</span></summary><div class="disclosure-body">...</div></details>`.
Don't: fold away the answer itself.

### empty

A list with nothing in it, saying what is missing and what to do.
Markup: `<div class="empty"><p class="title">No orphaned comments</p><p class="text">...</p>[<button class="btn">...</button>]</div>`.
Don't: write "Nothing here".

## Primitives

- `btn`, `btn-primary`: 32px buttons. `.btn-icon` is square. `.is-dirty` on
  Save shows unsaved work; `aria-busy="true"` marks a pending action.
- `seg`: segmented control of `<button aria-pressed>`; collapsed hairlines make
  one object. A filter's selected segment is a light fill; a verdict's is ink.
- `pick`: a page-level choice button, `<button class="btn pick" data-page-key="winner" data-page-value="option-a" aria-pressed="false">Pick</button>`.
  Clicking it calls `Render.setPage(key, value)` (toggling off if already set)
  and the runtime keeps `aria-pressed` in sync; a pressed pick is an ink fill,
  same weight as a pressed verdict. Use it wherever one reader decision applies
  to the whole page rather than to one block, for example a `matrix`'s winner
  column or a `compare` mode's chosen option. See feedback-loop.md for the
  `page` state key this writes to.
- `tag`, `tag-high`, `tag-crit`: severity by weight. Critical is an ink fill,
  high an ink outline, medium and low a grey outline. `.tag.mono` for a filename.
- `kbd`: a key, in mono.
- `source`: a citation, `<cite class="source"><a href="...">def6a6f</a> path:line</cite>`.
- `comments`, `composer`: inserted by the runtime; `.comment` holds
  `.comment-meta` and `.comment-text`, `.composer` holds a textarea and
  `.composer-actions`.
- `shortcuts`: the inline keyboard panel under the toolbar, a
  `.shortcuts-inner` grid of `.shortcut` rows with `.keys`.
