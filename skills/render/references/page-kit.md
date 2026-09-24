# Page kit

The document skeleton, where the file goes, and how it gets published. Shared by
all twelve modes.

## Output path

Default: `.cc-arsenal/renders/<mode>-<slug>-<YYYY-MM-DD>.html`, relative to the
project root. `<slug>` comes from the subject, lowercased and hyphenated.

`--out <path>` overrides it. Re-running with the same path updates that page in
place, which is how a revision keeps its link and its marks. That preservation
is not automatic: read the existing page's state block first and embed it in the
new one, per the re-render rules in
[feedback-loop.md](feedback-loop.md). A rebuild that emits an empty state
destroys everything the reader has done.

Where the file lives after that, and whether it is committed, is the user's
call. Do not add it to `.gitignore`, do not warn about committing it, and do not
move it.

## The two delivery paths

**Published.** Where an `Artifact` tool exists, write the file, then publish it
and return the link. Declare `capabilities: {artifact: {}}` so the page can save
new versions of itself. Load the `artifact-capabilities` skill before writing any
`claude.use` code (or, where no skill-loading tool exists, follow the runtime
contract that tool documents); it carries the current call shapes.

A first publish also needs an `icon`, one short generic word that suits the
mode and the subject (`review`, `chart`, `map`, `diff`), never a product or
brand name and never an emoji, and takes a one-sentence `description` for the
gallery card. Pick one and then never change it: readers find the tab by its
icon, so omit the parameter on every redeploy and the page keeps the icon it
has.

The publish is by file path, so **keep the local file**. It is the source for
every later update to that URL. If it drifts from what is published, the next
publish silently reverts the page to the stale copy. When updating a page that
was published earlier, read the live version first and build the update from
that.

**Local file.** Where no `Artifact` tool exists, the same self-contained HTML on
disk is the deliverable. Print the path.

The round trip still works, but not by the reader pressing the browser's own
save: a `file://` page cannot overwrite itself, and a Save-Page-As serializes
the original markup, whose state block is still empty. Instead the page's save
control regenerates the document exactly as it would for a publish, then hands
it to the reader as a download through an object URL:

```js
const blob = new Blob([doc], { type: "text/html" });
const a = document.createElement("a");
a.href = URL.createObjectURL(blob);
a.download = "review-auth-2026-08-30.html";   // the page's own filename
a.click();
URL.revokeObjectURL(a.href);
```

The downloaded copy carries the marks. Tell the reader, in one line, to replace
the file at the printed path with it and say when they have, since the skill
reads that path and not their downloads folder.

Resolve which path applies at build time. Do not ask the user which environment
they are in.

## Document skeleton

No page is authored from a blank file. Every mode ships a template at
`assets/templates/<mode>.html`: a complete page linking `../page.css` and
`../page.js`, a `/*SAMPLE*/`-marked `DATA` object standing in for real
content, and the render calls already wired to `Render.anchored()`,
`Render.init()` and the rest of the runtime `assets/page.js` ships (`esc`,
`slug`, `cap`, `path`, `verdict`, `getPage`, `setPage`). Building a page is
copy, fill, assemble, check:

1. Copy the template straight to the real output path,
   `.cc-arsenal/renders/<mode>-<slug>-<YYYY-MM-DD>.html`, and edit it there.
   Its sibling relative links, `../page.css` and `../page.js`, no longer
   resolve once the file has moved; that is expected, `scripts/assemble.py`
   falls back to the skill's own `assets/` directory by filename whenever the
   relative link misses, so the move is safe. Replace the whole
   `/*SAMPLE*/`-marked `DATA` object and compose any extra blocks.
2. Run `scripts/assemble.py` on that same path, in place, `-o` pointing at the
   input it just read. The file goes from linked template to a single gated
   page in one command.
3. Run `npx impeccable detect` on the result and fix whatever it flags.

```bash
cp skills/render/assets/templates/plan.html .cc-arsenal/renders/plan-auth-rework-2026-09-23.html
# edit .cc-arsenal/renders/plan-auth-rework-2026-09-23.html: replace /*SAMPLE*/ DATA, compose extra sections
python3 skills/render/scripts/assemble.py .cc-arsenal/renders/plan-auth-rework-2026-09-23.html \
  -o .cc-arsenal/renders/plan-auth-rework-2026-09-23.html
npx impeccable detect .cc-arsenal/renders/plan-auth-rework-2026-09-23.html
```

None of these calls takes `--allow-sample` for a real page: a leftover
`/*SAMPLE*/` marker is a gate failure, not a warning. Re-check an already
assembled file later, without rewriting it:

```bash
python3 skills/render/scripts/assemble.py .cc-arsenal/renders/plan-auth-rework-2026-09-23.html --check-only
```

Order still matters inside the template: the state block comes before the
script that reads it, and the script that captures `RAW` runs before anything
mutates the DOM. Inline the content as a JavaScript object rather than
fetching it; the page has to work with no network beyond its font stylesheet.

**The toolbar builds itself.** A template ships two empty containers,
`<div class="counts" aria-label="Counts"></div>` and
`<div class="seg" data-filter="verdict" role="group" aria-label="Filter by verdict"></div>`,
never hand-filled buttons. `Render.init({verdicts, file, title})` fills both
from its `verdicts` vocabulary the first time it runs: an ordered array
(positive, middle, negative) builds the tallies and the three-way filter,
`null` builds a single comment count and removes the filter segment for a
comments-only mode. A verdict control on an item works the same way: call
`Render.verdict(anchor)`, or pass `verdict: true` to `Render.anchored()`, to
emit the empty placeholder,
`<div class="verdict seg" role="group" aria-label="Verdict" data-for="ANCHOR"></div>`,
and let `Render.init()` fill it in, whether that call happens before or after
the placeholder exists. `Render.init()` re-scans the DOM for empty containers
on every call, so `mount(DATA); Render.init({ ... });` and
`Render.init({ ... }); mount(DATA);` are both safe; keep calling
`Render.anchored()` and `Render.verdict()` for these controls rather than
writing the button markup by hand.

Two small helpers round out the runtime: `Render.cap(s)` capitalises a
label's first letter for display, and `Render.path(p)` escapes a file path and
inserts a `<wbr>` after every `/` so it wraps at a segment boundary instead of
mid-word; use it inside `.facts dd.mono` and any `.path` figcaption span in
place of raw `Render.esc()`.

Every template also carries the waiver line
`<!-- impeccable-disable overused-font -->` right after `<title>`, with the
reason `Geist is the typeface the render brief mandates` inline. Keep it when
you copy the template: it is a deliberate waiver, not an oversight for
`impeccable` to flag.

When publishing as an Artifact, omit `<!doctype>`, `<html>`, `<head>` and
`<body>`; the publish step supplies them. The `RAW` capture still returns the
full wrapped document at runtime, which is what `save()` in `assets/page.js`
needs.

## Color

**Zero hue.** Every color on the page is one of the eight neutral tokens
below, `transparent`, `currentColor`, or a `color-mix()` of tokens: R, G and B
sit equal at every step, in both themes. There is no brand accent, no colored
heading, link, filter, count, badge, section rule or diagram, and, unlike an
earlier draft of this kit, no colored verdict either.

| token | light | dark | use |
|---|---|---|---|
| `--bg` | `#FAFAFA` | `#0B0B0B` | page background |
| `--panel` | `#FFFFFF` | `#121212` | rows, toolbar, inputs |
| `--sunk` | `#F4F4F4` | `#1A1A1A` | hover states, code wells |
| `--line` | `#E5E5E5` | `#242424` | hairlines |
| `--line-strong` | `#D4D4D4` | `#363636` | control borders |
| `--ink` | `#0F0F0F` | `#EDEDED` | text, primary fill, focus ring |
| `--mute` | `#525252` | `#A1A1A1` | secondary text |
| `--soft` | `#737373` | `#808080` | meta, placeholders, dropped rows |

An intermediate grey, for a heat cell or a bar fill, is never a ninth hex:
mix two tokens instead, `color-mix(in srgb, var(--ink) 26%, var(--panel))`.
The mix stays neutral because both inputs are, and it tracks whichever theme
is active for free.

**Encodings carry the meaning color used to.** A verdict is a fixed-order
segmented control; the pressed segment is an ink fill, so its *position*
across a long list of rows is the signal, not a hue. A dropped or rejected
item strikes its title and softens its body to `--soft`. Severity is weight:
critical is an ink fill, high is an ink outline, medium and low are a
`--line-strong` outline with `--mute` text. Magnitude is fill value and bar
length (`heat`'s `data-h="0..5"` steps, `bars`' `--v`), always paired with the
printed number so nothing depends on color alone. If a page seems to need
another color, the encoding is wrong, not the palette.

Before publishing, run `scripts/assemble.py` rather than eyeballing the
stylesheet. It gates the assembled page mechanically: every `hex` value must
be 6-digit with R=G=B (rule `hex`), no `rgb/hsl/hwb/lab/lch/oklab/oklch`
function (`color-function`), no CSS named color in a color-bearing property
(`named-color`), and `border-radius`/`rx`/`ry` only `0` (`radius`). A
`font-size` or `font` shorthand size below the 15px floor, in any unit or
keyword, is its own violation (`font-size`), and so is a leftover
`/*SAMPLE*/` marker (`sample`). The `shadow` rule covers `box-shadow`
(`none` or a 1px inset outline only), `filter`
(never a `drop-shadow(...)` or a `blur(...)` function), and `backdrop-filter`
(an unconditional violation). A violation prints as `file:line: rule: snippet`
and the script exits nonzero. A tenth color or a rounded corner is a gate
failure, not a style note. A 13px label fails the same way.

## Theming

Three states, not two. An explicit choice stamps `data-theme` on the root
element; the default setting stamps nothing, and only `prefers-color-scheme`
separates light from dark there. `assets/page.css` carries the real block
verbatim:

```css
:root {
  color-scheme: light;
  --bg: #FAFAFA;
  --panel: #FFFFFF;
  --sunk: #F4F4F4;
  --line: #E5E5E5;
  --line-strong: #D4D4D4;
  --ink: #0F0F0F;
  --mute: #525252;
  --soft: #737373;
}
:root:not([data-theme="light"]) {
  @media (prefers-color-scheme: dark) {
    color-scheme: dark;
    --bg: #0B0B0B;
    --panel: #121212;
    --sunk: #1A1A1A;
    --line: #242424;
    --line-strong: #363636;
    --ink: #EDEDED;
    --mute: #A1A1A1;
    --soft: #808080;
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --bg: #0B0B0B;
  --panel: #121212;
  --sunk: #1A1A1A;
  --line: #242424;
  --line-strong: #363636;
  --ink: #EDEDED;
  --mute: #A1A1A1;
  --soft: #808080;
}
```

The `@media` sits *inside* `:root:not([data-theme="light"])`, not the other way
around. A top-level `@media (prefers-color-scheme: dark) { :root { ... } }`
would read more simply, but a static analyzer walking the cascade (a contrast
checker, a linter, `impeccable`) commonly flattens or skips a top-level media
block and evaluates only the bare `:root`. It never sees the dark values, so it
can pass a page that is actually broken in dark mode. Nesting the media query
inside the selector keeps a real browser's auto/light/dark resolution correct
while keeping those static checks honest about which rule actually wins.

Style every component through the tokens. A color declared only inside a media
block or a `[data-theme]` block does not apply in the unstamped state, which
puts one theme's text on the other theme's background. Give `body` an explicit
token background: a transparent body borrows the host's.

Theme the surfaces you did not draw, from the same tokens: `::selection`,
`caret-color`, `scrollbar-color`, the focus ring. They ship with browser
defaults that belong to no palette.

## Type and layout

These pages are Operate surfaces: scanned and worked, not read start to finish.
Brand lives in precision, and the interface should disappear into the task.

- **Geist carries headings, controls, labels and body; Geist Mono carries
  identifiers, counts, code and file paths.** Load both from one Google Fonts
  link, weights 400/500/600 only
  (`family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500`). A display
  face in a row label is a costume. Set `font-variant-numeric: tabular-nums`
  wherever digits align in a column.
- **15px is the smallest font size anywhere on the page.** No text drops
  below it: not meta, tags, kbd, line numbers, code, counts, legends, SVG
  labels, nothing. `scripts/assemble.py`'s `font-size` rule gates this
  mechanically.
- **Fixed px scale, not `clamp()`: 15 / 17 / 20 / 30.** 15 carries body text,
  UI labels, buttons, filters, tags, meta, mono identifiers and paths, code
  excerpts, kbd, line numbers, legends, heat and matrix values, and SVG node
  labels. 17 is `h3` and sub-section headings. 20 is `h2` and the `.tldr`
  statement. 30 is `h1`, tracked at -0.02em. Hierarchy within the 15px layer
  comes from weight (400/500/600) and color (`--ink`/`--mute`/`--soft`), the
  way Linear does it, never from shrinking text further. Line-height: 1.55 for
  body, 1.25 for UI controls and headings.
- **Control sizing follows the larger type**: buttons and `.seg` segments 32px
  tall, the toolbar row 52px, the filterbar about 48px, tags about 24px tall,
  `kbd` at least 24px, the `.mark` comment gutter at least 32px, row padding
  scaled to keep the rhythm.
- **Prose measure 65 to 75 characters.** Data and dense rows can run wider.
- **Wide content scrolls inside its own container** with `overflow-x: auto`, so
  the body never scrolls sideways.
- **Layout does the spacing.** Flex or grid with `gap`, never per-element
  margins that collapse or double. Group related rows tightly, separate distinct
  groups generously, and leave more space above a heading than below it.
- **Declare elevation once**, a hairline or a shadow, never both. A 1px border
  under a soft shadow is the ghost card.
- **Responsive behavior is structural**: a column collapses, a row restacks, a
  filter bar scrolls. Type does not fluidly shrink.

## Shape

`border-radius: 0` everywhere, no exception for a form control: `page.css`'s
reset applies it to `*, *::before, *::after` and again explicitly to
`button, input, textarea, select, details, summary`, so a page never has to
repeat it. An SVG node's `rx`/`ry` is `0` for the same reason: a graph's
rectangles are square, its edges use miter joins and square caps
(`stroke-linejoin: miter; stroke-linecap: square`), never a rounded corner or
a soft line end.

No shadow but one: `box-shadow: inset 0 0 0 1px var(--token)`, used where an
outline would clip (a `.layers` row marked `key`) and a `border` would shift
the layout by a pixel. Every other elevation is a hairline (`border` or
`border-top`/`border-bottom`), never a soft offset shadow, and never a
hairline stacked under a shadow. No `blur()`, no `backdrop-filter`, no
translucent panel: a surface is opaque or it is not drawn.

## States

Interactive controls need default, hover, focus, active and pressed. A list
needs an empty state saying what is missing and offering the way back, not
"nothing here". Any operation that takes time shows a pending state on the
control that started it.

Motion runs 120 to 250 ms and conveys state only: a mark landing, a composer
opening, a count changing. No page-load choreography, no scroll-triggered
reveals. The reader is mid-task and did not ask to watch the page arrive.
Honour `prefers-reduced-motion`.

Copy names the action. A control says what happens, an error says what went
wrong and how to fix it, and a count says what it counts.

## Images

Some modes carry images, for example a visual regression triptych.

- **Local file**: embed as `data:` URIs. The file has to stand alone.
- **Published**: upload with the Artifact tool's `upload_asset` action and
  reference the returned URL verbatim. The page must declare the `assets`
  capability first.

Give every image an explicit aspect ratio so the page does not shift as they
load, and real `alt` text.

## What not to build

The defaults that make a generated page look generated:

- **No kicker or eyebrow above a heading.** The heading carries its own weight.
- **No section numbers** (01 / 02 / 03) unless the sequence itself is
  information the reader needs.
- **No card grid as the page's structure.** These pages are lists and tables;
  same-size cards of heading-plus-text are the lazy container, and nested cards
  are always wrong.
- **No hero metric block**: big number, small label, supporting stats.
- **No modal** for a task needing neither interruption nor protected focus.
- **No gradient text, no glass or blur as decoration, no colored border-left**
  above 1px, no hard offset shadows.
- **No border-radius, anywhere, on anything.** A rounded button, tag, or panel
  corner is the fastest way to look generated on this kit.
- **No pill shape.** A tag, a segment, a button is a rectangle with square
  corners, never a stadium shape.
- **No shadow but the 1px inset outline.** No drop shadow, no glow, no
  blurred halo.
- **No blurred or translucent header.** The toolbar is `var(--panel)`, opaque,
  under one hairline; no `backdrop-filter`, no reduced opacity over content.
- **No hue, anywhere, including a verdict.** A verdict, a severity and a
  magnitude are all encoded without color; see the Color section above.
- **No scroll-reveal choreography.** Content is present on load; nothing
  fades or slides in as the reader scrolls.
- **No sparklines or progress rings standing in for content.**
- **No emoji, anywhere, including the published artifact's own icon.** Draw
  an SVG inside the page, or use none; the icon passed to the Artifact tool on
  publish is a plain generic word, never an emoji.
- **No spinner** in the middle of content where a skeleton belongs.
- **No monospace as a costume.** It is for identifiers, code, paths and
  measurement, not for signalling that a page is technical.
