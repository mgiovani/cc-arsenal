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

## Theming

Three states, not two. An explicit choice stamps `data-theme` on the root
element; the default setting stamps nothing, and only `prefers-color-scheme`
separates light from dark there.

```css
:root { /* the complete light palette, as tokens */ }
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

- One UI family carries the whole page in most modes, with a mono face for
  identifiers, counts and code. Set `font-variant-numeric: tabular-nums` wherever
  digits align in a column.
- Fixed rem scale, not `clamp()`. These pages are read at a desk, and a heading
  that shrinks with the viewport looks worse, not better.
- Prose measure 65 to 75 characters. Tables and dense data can run wider.
- Wide content gets `overflow-x: auto` on its own container, so the body never
  scrolls sideways.
- Lay out sibling groups with flex or grid and `gap`, not per-element margins.

## States

Interactive controls need default, hover, focus, active and pressed. A list
needs an empty state saying what is missing and offering the way back, not
"nothing here". Any operation that takes time shows a pending state on the
control that started it.

## Images

Some modes carry images, for example a visual regression triptych.

- **Local file**: embed as `data:` URIs. The file has to stand alone.
- **Published**: upload with the Artifact tool's `upload_asset` action and
  reference the returned URL verbatim. The page must declare the `assets`
  capability first.

Give every image an explicit aspect ratio so the page does not shift as they
load, and real `alt` text.

## What not to build

- No modal for a task that needs neither interruption nor protected focus.
- No spinner in the middle of content where a skeleton belongs.
- No animation that does not convey state. Transitions stay at 120 to 250 ms.
- No emoji standing in for an icon inside the page. Draw the SVG or use none.
  The published artifact's favicon is a separate thing and is emoji by contract.
- No card grid as the page's structure when the content is a list.
