# The feedback loop

Every page this skill builds carries the same mechanic: the user marks things,
saves, and the marks come back bound to what they were left on. This file
specifies that mechanic. It is shared by all twelve modes.

## The two kinds of feedback

**Verdicts** are a small fixed choice on a page's primary items: keep, change,
drop, or the mode's equivalent. They exist because a three-state decision across
eighty rows has to be one click. Seven modes have them; `explain`, `map`,
`tour`, `timeline` and `report` do not.

**Comments** are free text bound to any anchored element, including headings,
diagrams, prose and table cells. Every mode has them. A verdict decides; a
comment explains.

## Anchors

Every block the user might comment on carries `data-anchor`. The value is
derived from **content identity**, never from position in the document:

| Content | Anchor |
|---------|--------|
| A requirement | `req-PRD-FR-005` |
| A plan step | `step-migrate-token-table` |
| A finding | `finding-src-auth-py-42-timing-compare` |
| A comparison option | `option-postgres` |
| A criterion row | `criterion-ops-burden` |
| A section heading | `section-tradeoffs` |
| A diagram | `diagram-fanout` |

Position-derived anchors (`step-3`, `item-7`, `row-12`) break the moment content
is inserted above them, and the break is silent: the old anchor still resolves,
so a comment left on the third step reappears on whatever is third next time,
attached to the wrong work and never flagged as orphaned. Derive from the
identifier the content already has, and where it has none, slugify the content's
own text.

Anchors must also be **unique within a page**. A file-and-line anchor collides
whenever two findings land on the same line, which multi-dimension reviews
produce routinely. Append a slug of the claim, and if a collision still remains,
append an ordinal to the later one. Two blocks sharing an anchor share a verdict
and share every comment, so marking one marks both.

Alongside `data-anchor`, each anchored element carries `data-label` (a short
human-readable name for the thing) and sits inside a section that carries
`data-section`. Both are stored with any comment left there, and both are what
make read-back legible.

## State shape

The page embeds one JSON object and renders itself from it.

```html
<script id="state" type="application/json">{"v":1,"verdicts":{},"comments":[]}</script>
```

```js
{
  "v": 1,
  "updated": "2026-08-30T14:20:00.000Z",
  "page": { "winner": "option-postgres" },
  "verdicts": {
    "req-PRD-FR-005": { "d": "change" }
  },
  "comments": [
    {
      "anchor":  "req-PRD-FR-005",
      "label":   "PRD-FR-005 · The skill loader must discover skills",
      "section": "Derived requirements / Functional",
      "text":    "four tiers, not three",
      "at":      "2026-08-30T14:19:12.000Z"
    }
  ]
}
```

Storing `label` and `section` on the comment, rather than only the anchor, is
what lets a later read report "you said X about Y, under Z". It also lets an
orphaned comment stay meaningful after its anchor disappears.

`verdicts` is keyed by anchor, so it holds only per-block decisions. A decision
belonging to the page rather than to one block goes in `page`, which is where
`compare` mode's winner lives. Write and read it through the runtime,
`Render.setPage(key, value)` and `Render.getPage(key)`, rather than touching
`state.page` directly: `setPage` persists, marks the Save button dirty and
repaints every `button[data-page-key][data-page-value]` on the page (the
`.pick` control) to match. A `null` or `undefined` value deletes the key.
Read-back covers `page`, `verdicts` and `comments`.

## The affordance

A single control in the gutter of every anchored block. It shows a `+` when the
block has no comments and a count when it does. Both states are drawn in the
page's neutrals, dim by default and ink once the block carries a comment: the
count itself is the signal. There is no hue to compete with here; a verdict is
now encoded by the ink fill's position in its segmented control, not by a
color, so the mark stays in the page's neutrals in every state. It must be
reachable by keyboard, so it reveals on `:focus-within` as well as `:hover`,
and carries a real `aria-label`.

Lay the gutter out with grid rather than pulling the control into negative
space. A `position: absolute; left: -1.75rem` child is clipped by any ancestor
with `overflow-x: auto`, which is exactly what wraps the wide tables and
matrices whose cells this skill says must be commentable. `assets/page.css`
does this already, in its `.anchored`, `.anchored > .mark` and
`:is(td, th).anchored` rules: a CSS grid gutter column on desktop that moves
to a right-aligned column under 720px and stays statically visible there, and
into a corner-positioned mark for an anchored table cell. Reuse those classes
rather than re-deriving the layout.

The gutter column belongs to the block, so it travels with the block into a
scroll container and cannot fall off the left edge of the viewport. On narrow
viewports there is no hover, so the control collapses into the flow and stays
visible. Do not ship a page whose only feedback affordance requires a mouse.

Clicking opens a composer inline, directly under the block. Not a modal: a modal
hides the thing being commented on, which is the one piece of context the user
needs.

## Wiring

`assets/page.js` ships this wiring already; a page never re-implements it.
Everything delegates to two listeners on `document` (`onClick`, `onKeydown`),
wired once by `wireEvents()`, so the handlers survive a re-render. State is
loaded once by `loadState()`, then normalised by `normalize()` before anything
reads it.

Set `data-label` on every anchored block rather than relying on the runtime's
fallback. The affordance button is a child of the block, so a bare
`block.textContent` would pick up the `+` or the comment count and store
labels reading `"+Rate limiter must reject..."`. `labelFor()` reads an inner
`.body` element (with the mark, comments and composer stripped out first) for
that reason; give every anchored block a `.body` and the fallback stays
correct if `data-label` is ever missing.

Saving a comment (`submitComment()`) or a verdict (`setVerdict()`) both end in
`persist()`, which stamps `state.updated`, writes the draft to `localStorage`
and calls `markDirty()` to flag the Save control. Publishing is explicit, on
the Save button (`save()`), never on load and never on every keystroke.

**What `localStorage` is and is not.** It holds work the reader has not
published yet, so a closed tab does not lose it. `loadState()` reads it and
uses the draft only when it is strictly newer than the embedded state:

```js
if (draft && draft.updated > (embedded.updated || '')) return normalize(draft);
```

The comparison matters. Without it a draft resurrects comments the author has
already acted on and removed from the published page. `save()` calls
`clearDraft()` after a successful publish.

## Saving

`assets/page.js` captures the document source once, as the first statement in
the file (`const RAW = document.documentElement.outerHTML`), before any render
mutates the DOM, then swaps the state block into a fresh copy of it. Never
serialize the live DOM.

`buildDocument()` does the swap: it locates the `<script id="state">` tag in
`RAW`, re-serializes `state` with `<` escaped (`.replace(/</g, '\\u003c')`,
which keeps a comment containing markup from closing the script tag early),
and splices the JSON between the original open and close tags. `publish()`
then tries `window.claude.use('artifact')` and falls back to `download()` (a
Blob and an object URL) when no Artifact runtime answers or the publish call
rejects; `save()` wraps both in the Save button's pending and dirty state and
calls `clearDraft()` on success.

`RAW` and the authored file are two different things, and page-kit.md's rule
about omitting the document wrapper applies only to the file. At runtime
`document.documentElement.outerHTML` returns `<html>...</html>` for the live
document, wrapper included and doctype excluded, because the doctype is a
sibling node rather than a child. Prepending the doctype in `buildDocument()`
therefore produces one complete document, not a nested one.

See [page-kit.md](page-kit.md) for which of the two save paths a page ends up
on and how `publish()` chooses between them at runtime.

## Re-rendering an existing page

Writing to a path that already holds a page is a revision, not a new page, and
the reader's marks have to survive it. Before writing:

1. Read the existing file (or the published version) and parse its `state`
   block.
2. Emit the new page with **that state embedded**, not with an empty one.
3. Resolve every anchor in the carried state against the new content. A verdict
   whose anchor is gone is dropped, since the item it judged no longer exists. A
   comment whose anchor is gone is **kept** and reported as orphaned on the next
   read-back, because what the reader said still matters.

Skipping this destroys every mark the reader has left, silently, in the exact
operation they expect to preserve them.

## Reading the marks back

When the user says they have marked the page:

1. Re-read it. Published page: `Artifact` with `action: "read"` and the URL.
   Local file: read the file.
2. Parse the `state` block.
3. Resolve every comment's anchor against the page's current anchors.
4. Report grouped by decision, not by page order: what they want changed, what
   they dropped, what they approved, then the comments.
5. Name every orphan. A comment whose anchor no longer resolves is reported with
   its stored `label` and `section` and flagged as attached to something that has
   since moved or gone. Never drop one silently.

Act on what came back before asking for anything more. If the marks conflict
with each other, say so and ask; do not pick one side quietly.

## The escape hatch

Every page carries a button that copies a plain-text digest of all verdicts and
comments to the clipboard, grouped the same way step 4 groups them. It covers
the case where saving is unavailable and the case where the user would rather
paste than have you re-read the page.
