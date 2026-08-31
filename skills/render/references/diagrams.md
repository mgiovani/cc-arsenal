# Diagrams

When a diagram earns its place, and how to draw one that survives both themes.

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
the one carrying the load and let the rest stay lists.

## Inline SVG, not Mermaid

Mermaid brings its own theme. The pages this skill builds carry three theme
states driven by CSS custom properties, and a Mermaid block will not follow them:
the usual outcome is a diagram that is legible in one theme and washed out or
invisible in the other, then deleted by whoever polishes the page next.

Author the SVG inline and paint it from the page's own neutral tokens. Diagrams
carry no hue: nodes are surface and hairline, edges are the muted foreground,
and emphasis comes from stroke weight and fill value rather than color.

```html
<svg viewBox="0 0 480 200" role="img" aria-labelledby="fanout-t">
  <title id="fanout-t">AI-1 and AI-5 each block several requirements</title>
  <g class="edge"><path d="M96 40 H180" /></g>
  <g class="node"><rect x="8" y="24" width="88" height="32" rx="6" />
    <text x="52" y="44">AI-1</text></g>
</svg>
```

```css
svg .node rect { fill: var(--sunk); stroke: var(--line-strong); }
svg .node text { fill: var(--ink); font-size: 12px; text-anchor: middle; }
svg .edge path { stroke: var(--mute); fill: none; stroke-width: 1.5; }
svg .edge path[marker-end] { marker-end: url(#arrow); }
```

Both themes then work for free, because the tokens already switch.

Set `viewBox` and let the SVG scale; do not fix `width` and `height` in pixels.
Put it in a container with `overflow-x: auto` if it has a minimum readable width.

## Accessibility

- `role="img"` plus a `<title>` that states the diagram's conclusion, not its
  type. "AI-1 and AI-5 each block several requirements" beats "flowchart".
- Never encode meaning in color alone. A critical path is thicker as well as
  darker; a failed node carries a label as well as a fill.
- Text inside an SVG does not reflow. Keep labels to a few words and put the
  detail in the prose beside it.

## Shapes worth knowing

**Fan-out.** One node branching to several, used when the point is how much
depends on one thing. Order the branches by count so the asymmetry reads
immediately.

**Critical path.** A step sequence with the longest chain emphasized by stroke
weight and the parallel branches receding. Label the chain's total, since that
number is the reason the diagram exists.

**Matrix.** Two real axes with a mark at each intersection. Use it only when both
axes are genuinely independent; a matrix with one meaningful axis is a list
wearing a costume.

**Boundary.** Nested regions with the crossings marked, for trust boundaries,
process boundaries and network hops. The crossings carry the meaning, so draw
them heavier than the regions.

## Generative and decorative graphics

For anything with many elements or motion, reach for Canvas rather than
hand-authoring long SVG path data. Do not hand-write path data approximating a
picture: crisp geometry is first class, sketch-style illustration is not.
