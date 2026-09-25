# Mode: report

A status and metrics summary: a standup, a sprint wrap-up, an audit-at-a-glance.
The reader is not deciding anything on this page, they are catching up.

## The page

- **Header**: the headline status in one sentence (`tldr`), then a handful of
  labelled values that frame it (`facts`).
- **Deliverables or work items by group**, as counts that sum to a whole
  (`tally`), so the reader sees the shape of the period before any detail.
- **Work per area**, as one number per item (`bars`). This is what "where did
  the time go" looks like without a table.
- **A two-dimensional breakdown** where the period has one (`heat` or `table`):
  area against day, area against status, locale against category. Use whichever
  block the axes deserve; `heat` earns its place when the magnitude itself is
  part of the point, `table` when the reader needs exact values side by side.
- **A trend**, optional, where a metric is worth tracking across more than one
  checkpoint: `DATA.trend` (2 or more x-axis ticks, one or more series) draws a
  `Render.diagram.line`; exactly 2 ticks reads as a slope chart. Skip it where a
  single period's numbers are the whole story.
- **Blockers**, each a `callout` with `data-kind="risk"`. A report that hides
  what is stuck is worse than no report.
- **Next steps**, as a `checklist` mixing what is already done with what is
  still open.
- **An optional short timeline** of the period, only when the dates themselves
  carry information the reader needs (a launch date, a deadline slipping).

No hero metric block: a report has several numbers that matter together, and a
single blown-up figure hides the rest. Every block on the page is anchored, even
though there is nothing to vote on, because the reader still needs to leave a
note on any one of them.

Anchor per block: derived from the block's own subject, for example
`tally-deliverables-<slug>`, `bars-<what-they-measure>`,
`risk-<slug-of-the-claim>`. A report is regenerated every period, so an anchor
that survives a rerun with the same shape (`risk-file-ownership-boundary`, not
`risk-1`) is what lets a standing comment on a recurring blocker keep landing on
it.

## Verdicts

None. A report states what happened; it does not ask the reader to rule on each
line. Comments are the whole feedback surface, same as `explain`.

## Data

From a manual pull of commits, issues and PRs over a stated period. State the
period once, in the header, and
never let a number in `facts`, `tally` or `bars` silently mix periods.

Counts come from the source, not from rounding for a cleaner headline. Where a
group's count is zero, show it as zero rather than dropping the row: an empty
row in `tally` or `breakdown` is information (nothing shipped there this
period), and dropping it hides that.

## Notes

- Group by area or by track, not by contributor, unless the report is
  specifically about individual workload. A wrap-up organized by person reads as
  a scoreboard, which changes what people report.
- A risk with no owner and no next step is a complaint, not a callout. Pair
  every `risk` callout with at least one line in the `checklist` that addresses
  it, even if that line is "decide by Friday".
- Keep the period's own ordering for the timeline. Do not reorder by importance;
  the timeline is for "when", the rest of the page is for "what matters".
