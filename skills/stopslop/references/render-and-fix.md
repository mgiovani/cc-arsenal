# Render and fix

Offer this after the summary. Do it only when the user wants it.

## Render

Use the `render` skill to build an `audit` page (via the `Skill` tool as `render audit`, otherwise follow the render skill's steps inline). Pass it the findings from the saved JSON.

- One anchored item per finding, anchor `finding-<path-slug>-<line>-<code>`. Add an ordinal suffix if two anchors would collide.
- Each item carries the file:line, rule code and name, message, and the `fix` hint when present.
- Verdicts: `fix`, `won't fix`, `discuss`.
- Group by area (directory) first, tier second, as the audit mode does.
- Large runs: render every Tier A finding plus the top N per rule, and state the cap and the omitted total on the page.
- Output goes to `.cc-arsenal/renders/audit-<slug>-<date>.html`. Give the path and ask the user to mark and save it.

## Apply

When the user says the page is marked, read its `state` block (`{"v":1,"verdicts":{anchor:{d}},"comments":[...]}`) per the render skill's feedback loop.

1. Edit only findings whose verdict is `fix`. Honor any comment on the anchor.
2. For `won't fix`, add an `ai-slop-ignore` directive only if the user asked (see `suppressions.md`).
3. Leave `discuss` items alone and list them.
4. Re-run stopslop on the touched files only, with the full-report flags. Report what remains, quoting the output.
