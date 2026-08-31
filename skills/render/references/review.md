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
not optional: `review-code` reviews several dimensions at once and `team-review`
runs several agents, so two findings on one line are routine, and two blocks
sharing an anchor share a verdict and every comment. Label: the claim.

## Verdicts

`fix`, `won't fix`, `discuss`.

## Data

From `review-code`, `review-security`, `review-perf`, `review-design`,
`team-review`, `review-plan`, or `vrt-check`.

Preserve the source skill's severity ranking exactly. Preserve its claim wording.
The reader is deciding whether the finding is real, and a rewritten claim is a
different finding.

For `team-review`, keep the raising agent visible on each finding and keep the
adversary's cross-examination attached to the finding it disputes, not in a
separate section. A disputed finding that looks unanimous misleads the reader.

For `vrt-check`, each anchored block carries a before, after and diff image in
one row, sized to a fixed aspect ratio. See page-kit.md for how images are
embedded on each delivery path.

## Notes

- A finding with no reproducible failure is reported as a suggestion, in its own
  group, below the real findings. Mixing the two is how a review loses the
  reader.
- Do not add findings the source skill did not produce. If something obvious was
  missed, say so in the report, not on the page.
