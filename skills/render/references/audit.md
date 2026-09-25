# Mode: audit

A whole-repo findings dashboard. Same triage as `review`, different scale and a
different first question: not "is this finding real" but "where is the problem
concentrated".

## The page

- **Header**: total findings, and the one number that frames them (packages
  scanned, locales checked, docs pages audited).
- **Distribution**: where the findings are, by area or directory, as a short
  ranked list with proportional bars. This is the summary the reader came for,
  so it goes above the findings, not below.
- **Per finding**, one anchored block: the same shape as `review`, usually
  shorter, since audit findings are more uniform.
- **Filters**: by area, by severity, by category, and undecided. At audit scale
  the filters are the interface; without them the page is a longer wall of text
  than the one it replaced.

Anchor per finding: `finding-<area-slug>-<claim-slug>`, never an ordinal. Audits
are re-run as the codebase changes, and a numbered anchor moves a comment onto a
different finding every time the count shifts. Label: the claim.

## Verdicts

`fix`, `won't fix`, `discuss`.

## Matrix findings

`i18n-check` and `review-deps` produce two-axis data: locales against keys,
packages against risk dimensions. Render that as a real matrix with the axes on
the page, not as a flattened list. The matrix is the finding, and flattening it
destroys the pattern the reader needs to see.

Anchor each cell that carries a gap, so a comment can land on one locale's one
missing key.

## Data

From `docs-check`, `i18n-check`, `review-deps`, `env-setup`, or `test-suite`'s
coverage analysis.

Counts come from the tool's own output. Never estimate a total, and never round
one for a cleaner headline.

## Notes

- An audit with no findings still gets a page, and it says what was checked. The
  scope is the result.
- Group by area before severity here, inverting `review`. At this scale the
  reader is choosing where to spend an afternoon, not adjudicating one claim.

## Blocks

Template: [`assets/templates/audit.html`](../assets/templates/audit.html), a
`wrap-wide` page with a `toc` rail by area.

| Block | Content |
|---|---|
| `page-head` | Subject, and one meta line: finding count, area count, scan date |
| `tldr` | The one-sentence answer to where the risk is concentrated |
| `facts` | Areas, findings, skills in scope, scan date |
| `tally` | Findings by severity (critical, high, medium, low), four shades |
| `checklist` | What the audit scanned, the scope named as done items |
| `callout` | A risk naming the worst finding, a note on method or scope |
| `heat` | Area by severity, the map of the audit, placed above the findings |
| `bars` | Findings per area, ranked, right after the heat table |
| `row` (anchored, per area section) | One finding: severity tag, claim, file or script location, verdict |
| `empty` | Per area, per tally, per heat and per bars, when the audit's finding list is empty |

Findings live one `section` per area (`data-section` is the area name), each
holding a `.list` of anchored `row` blocks sorted critical to low. The
filterbar carries verdict, area, severity and category, and the verdict
filter's `Undecided` option is load-bearing once an audit runs past a
handful of findings.
