# The feedback loop

Every page this skill builds carries the same mechanic: the user marks things,
saves, and the marks come back bound to what they were left on. This file
specifies that mechanic. It is shared by all eight modes.

## The two kinds of feedback

**Verdicts** are a small fixed choice on a page's primary items: keep, change,
drop, or the mode's equivalent. They exist because a three-state decision across
eighty rows has to be one click. Six modes have them; `explain` and `map` do
not.

**Comments** are free text bound to any anchored element, including headings,
diagrams, prose and table cells. Every mode has them. A verdict decides; a
comment explains.

## Anchors

Every block the user might comment on carries `data-anchor`. The value is
derived from **content identity**, never from position in the document:

| Content | Anchor |
|---------|--------|
| A requirement | `req-PRD-FR-005` |
| A plan step | `step-3` |
| A finding | `finding-src-auth-py-42` |
| A comparison option | `option-postgres` |
| A criterion row | `criterion-ops-burden` |
| A section heading | `section-tradeoffs` |
| A diagram | `diagram-fanout` |

Position-derived anchors (`item-7`, `row-12`) break the moment content is
inserted above them, which silently reattaches an old comment to a new item.
Derive from the identifier the content already has. Where content has no natural
identifier, slugify its text.

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

## The affordance

A single control in the gutter of every anchored block. It shows a `+` when the
block has no comments and a count when it does. It must be reachable by keyboard,
so reveal it on `:focus-within` as well as `:hover`, and give it a real
`aria-label`.

```css
.anchored { position: relative; }
.anchored > .mark {
  position: absolute; left: -1.75rem; top: .1rem;
  opacity: 0; transition: opacity .12s ease;
  background: none; border: 0; cursor: pointer;
  font: inherit; font-size: .75rem; color: var(--faint);
  width: 1.25rem; height: 1.25rem; border-radius: 4px;
}
.anchored:hover > .mark,
.anchored:focus-within > .mark,
.anchored > .mark:focus-visible,
.anchored > .mark.has { opacity: 1; }
.anchored > .mark.has { color: var(--accent); }
@media (max-width: 760px) {
  .anchored > .mark { position: static; opacity: 1; margin-bottom: .35rem; }
}
```

On narrow viewports there is no hover and no gutter, so the control becomes
static and always visible. Do not ship a page whose only feedback affordance
requires a mouse.

Clicking opens a composer inline, directly under the block. Not a modal: a modal
hides the thing being commented on, which is the one piece of context the user
needs.

## Wiring

Delegate to one event listener on `document`, so the handlers survive a
re-render.

```js
const state = JSON.parse(document.getElementById("state").textContent);
state.verdicts = state.verdicts || {};
state.comments = state.comments || [];

const commentsFor = a => state.comments.filter(c => c.anchor === a);

document.addEventListener("click", ev => {
  const mark = ev.target.closest(".mark");
  if (!mark) return;
  const block = mark.closest(".anchored");
  openComposer(block, block.dataset.anchor);
});

function saveComment(block, text) {
  if (!text.trim()) return;
  state.comments.push({
    anchor:  block.dataset.anchor,
    label:   block.dataset.label || block.textContent.trim().slice(0, 80),
    section: block.closest("[data-section]")?.dataset.section || "",
    text:    text.trim(),
    at:      new Date().toISOString(),
  });
  persist();
  paintMark(block);
}
```

`persist()` writes to `localStorage` immediately so nothing is lost between
saves, and flags the save control as dirty. Publishing is explicit, on a button,
never on load and never on every keystroke.

## Saving

Capture the document source once, before any render mutates the DOM, then swap
the state block into it. Never serialize the live DOM.

```js
const RAW = document.documentElement.outerHTML;   // first line of the script

async function publish() {
  const json = JSON.stringify(state).replace(/</g, "\\u003c");
  const doc  = "<!doctype html>\n" + RAW.replace(
    /(<script id="state" type="application\/json">)[\s\S]*?(<\/script>)/,
    (m, open, close) => open + json + close);
  // Artifact runtime: await (await claude.use("artifact")).publish(doc)
  // File fallback: offer `doc` as a download, or tell the user to save in place
}
```

Escaping `<` in the JSON keeps a comment containing markup from closing the
script tag early. Write the closing tag in the pattern as `<\/script>` so the
HTML parser does not end the script at the regex literal.

See [page-kit.md](page-kit.md) for which of the two save paths applies and how
to choose at runtime.

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
