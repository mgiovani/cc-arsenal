# Page kit

The document skeleton, where the file goes, and how it gets published. Shared by
all eight modes.

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

A first publish also needs a `favicon`, one or two emoji, and takes a
one-sentence `description` for the gallery card. Pick a favicon that suits the
mode and the subject, then never change it: readers find the tab by its icon, so
omit the parameter on every redeploy and the page keeps the icon it has. This is
the one place emoji are correct; the ban further down concerns icons drawn
inside the page.

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

One file, no build step, no external JavaScript. Order matters: the state block
comes before the script that reads it, and the script that captures `RAW` runs
before anything mutates the DOM.

```html
<title>Two To Four Words</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=...&display=swap">
<style>/* tokens first, then components */</style>

<script id="state" type="application/json">{"v":1,"verdicts":{},"comments":[]}</script>

<div class="wrap"><!-- static structure --></div>

<script>
const RAW = document.documentElement.outerHTML;   // must be the first statement
const DATA = { /* the real content, inlined */ };
/* render from state, wire events, publish */
</script>
```

Inline the content as a JavaScript object rather than fetching it. The page has
to work with no network beyond its font stylesheet.

When publishing as an Artifact, omit `<!doctype>`, `<html>`, `<head>` and
`<body>`; the publish step supplies them. The `RAW` capture still returns the
full wrapped document at runtime, which is what `publish()` needs.

## Color

**Monochrome.** One neutral ramp carries the entire page: background, surface,
hairline, foreground, and two muted foreground steps. Nothing else is colored.
No brand accent. No colored headings, links, filters, counts, badges, section
rules or diagrams. Selected, pressed and active states are an ink fill, a
foreground-colored fill, never a hue.

The one exception is the verdict vocabulary, capped at **three tints, used
nowhere else**: keep, change and drop. They are muted enough that a screen of
marked rows still reads as a document rather than an alert, and they appear only
as the text and faint background of the verdict control itself.

That cap is the whole rule. Do not add a fourth hue for severity, for category,
for a chart series, or for anything else. Severity is already carried by
grouping and rank; a category is carried by its heading; a chart is carried by
fill value and stroke weight. If a page seems to need another color, the
encoding is wrong, not the palette.

A reference ramp, to be adjusted in value but not in saturation:

```css
:root {                       /* light */
  --bg:#FCFCFB; --panel:#FFFFFF; --sunk:#F4F4F2;
  --line:#E6E6E2; --line-strong:#C9C9C3;
  --ink:#111112; --mute:#5C5C61; --soft:#78787E;
  --keep:#25655A; --edit:#8A6210; --drop:#9E3830;
  --keep-bg:#E6EFEC; --edit-bg:#F4EDDC; --drop-bg:#F7E8E6;
}
```

```css
                              /* dark */
  --bg:#0A0A0B; --panel:#131315; --sunk:#141416;
  --line:#232326; --line-strong:#3A3A40;
  --ink:#ECECEE; --mute:#A0A0A8; --soft:#84848C;
  --keep:#6FC0AB; --edit:#DBAE4C; --drop:#EA8C84;
  --keep-bg:#16241F; --edit-bg:#241E12; --drop-bg:#261816;
```

The neutrals carry a slight bias rather than sitting on pure grey, which is what
keeps a monochrome page from reading as unstyled. Keep that bias consistent
across both themes.

Before publishing, count the distinct hues in the stylesheet. Six neutral steps
plus three verdict tints is the budget. A tenth color is a bug.

## Theming

Three states, not two. An explicit choice stamps `data-theme` on the root
element; the default setting stamps nothing, and only `prefers-color-scheme`
separates light from dark there.

```css
:root { /* the complete light palette, as tokens: see Color above */ }
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) { /* redefine only the tokens */ }
}
:root[data-theme="dark"] { /* redefine them again */ }
```

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

- **One UI family** carries headings, controls, labels and body, with a mono
  face for identifiers, counts, code and file paths. A display face in a row
  label is a costume. Set `font-variant-numeric: tabular-nums` wherever digits
  align in a column.
- **Fixed rem scale**, not `clamp()`, and a tight ratio: 1.125 to 1.2 between
  steps. These pages carry many type roles, so exaggerated contrast between them
  reads as noise. Tracking floor is -0.04em, and -0.02em to -0.03em usually sits
  better on a heading.
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
- **No sparklines or progress rings standing in for content.**
- **No emoji as an icon inside the page.** Draw the SVG or use none. The
  published artifact's favicon is a separate thing and is emoji by contract.
- **No spinner** in the middle of content where a skeleton belongs.
- **No monospace as a costume.** It is for identifiers, code, paths and
  measurement, not for signalling that a page is technical.
