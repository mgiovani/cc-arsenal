# Render and fix

Offer this after the summary. Do it only when the user wants it.

## Render

Use the `render` skill to build an `audit` page. render is user-invoked only, so the `Skill` tool rejects it: follow its SKILL.md steps inline, or ask the user to run `/render audit`. Pass it the findings from the saved JSON. Start from its audit template and finish with its `scripts/assemble.py`; never hand-write the final HTML.

- Fill the audit template's `DATA` from the JSON, one entry per finding; the template derives each anchor from `area` + `title`, so never hand-build anchors:
  - `area`: the finding's top-level directory (one `areas[]` entry each).
  - `title`: `<code> <name> (<path>:<line>)`, so every title, and therefore every anchor, is unique.
  - `severity`: Tier A `high`, Tier B `medium`, Tier C `low`.
  - `category`: `reliability` for artifact, structure, stdlib and provenance rules; `drift` for the prose groups.
  - `detail`: the message, then the `fix` hint when present. `location`: `<path>:<line>`.
- Verdicts: `fix`, `won't fix`, `discuss`.
- Large runs: render every Tier A finding plus the top N per rule, and state the cap and the omitted total on the page.
- Output goes to `<repo-root>/.cc-arsenal/renders/audit-<slug>-<date>.html` (create the directory). It is the only file written inside the repo; the JSON stays in scratch. Give the path and ask the user to mark and save it.

## Apply

When the user says the page is marked, read its `state` block (`{"v":1,"verdicts":{anchor:{d}},"comments":[...]}`) per the render skill's feedback loop.

1. Edit only findings whose verdict is `fix`. Honor any comment on the anchor.
2. For `won't fix`, add an `ai-slop-ignore` directive only if the user asked (see `suppressions.md`).
3. Leave `discuss` items alone and list them.
4. Re-run stopslop on the touched files only, with the full-report flags. Report what remains, quoting the output.
