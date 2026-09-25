# Mode: review

A findings triage board. The reader decides what gets fixed.

## The page

- **Header**: finding count by severity, and what was reviewed (the diff, the
  branch, the paths).
- **Grouped by severity first**, then by file. Severity is why the reader is
  here; file is how they act.
- **Per finding**, one anchored block: a one-line claim, the file and line as a
  monospace reference, the code excerpt with the offending line marked, and the
  concrete failure it causes. Trim the excerpt to what carries the point.
- **Filters**: by severity, by dimension where the source skill has them
  (correctness, performance, security, style), and undecided.

Anchor per finding: `finding-<path-slug>-<line>-<claim-slug>`. The claim slug is
not optional: `review-code` reviews several dimensions at once, so two findings
on one line are routine, and two blocks sharing an anchor share a verdict and
every comment. Label: the claim.

## Verdicts

`fix`, `won't fix`, `discuss`.

## Data

From `review-code`, `review-security`, `review-perf`, `review-design`,
`review-plan`, or `vrt-check`.

Preserve the source skill's severity ranking exactly. Preserve its claim wording.
The reader is deciding whether the finding is real, and a rewritten claim is a
different finding.

For `vrt-check`, each anchored block carries a before, after and diff image in
one row, sized to a fixed aspect ratio. See page-kit.md for how images are
embedded on each delivery path.

## Notes

- A finding with no reproducible failure is reported as a suggestion, in its own
  group, below the real findings. Mixing the two is how a review loses the
  reader.
- Do not add findings the source skill did not produce. If something obvious was
  missed, say so in the report, not on the page.

## Blocks

Template: `assets/templates/review.html`.

- `page-head`: what was reviewed, in one line, plus the file count.
- `tldr`: the review's overall read, one or two sentences.
- `facts`: scope, files reviewed, finding count, suggestion count, dimensions.
- `tally`: finding count by severity, plus the stacked bar.
- `callout`: a risk the reader must not miss and the decision that follows from
  it, at most one of each.
- `filterbar`: the verdict segment plus a `severity` facet segment.
- `finding`: one per finding, grouped by severity (`h3` per group) then by file
  (`h4` before the first finding in a new file); severity tag, claim, `file:line`
  in `.meta`, the code excerpt with the offending lines marked `.hl`, and an
  optional diff hunk. Diff figures inside a finding carry both `diff` and `code`
  classes so they pick up the same 12px inset as the code excerpt above them.
- `row`: suggestions, in their own group below the findings, no severity tag.
- `empty`: shown in place of the findings groups when a review produced none.
