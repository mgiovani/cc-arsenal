# Mode: prd

A requirement inventory the owner can sign off on, one requirement at a time.

## The page

- **Header**: total requirements, how many are already agreed, how many are
  waiting on the reader. Two numbers beat a progress bar nobody asked for.
- **Per family**: requirements grouped by their ID family, each family carrying a
  one-line description of what it covers and a count of what is still open.
- **Per requirement**, one anchored block: the ID in mono, the requirement text
  at a readable measure, and the evidence path that produced it (the finding,
  decision or session it traces to). A requirement with no recorded source says
  so, because that is itself a finding.
- **Filters**: all, undecided, and one per family. Counts on each.
- **Bulk action**: approve the rest of a family in one click, since most rows in
  a well-written spec are uncontroversial and making the reader click each one is
  what stops them finishing.

Anchor per requirement: `req-<ID>`. Label: the ID plus the first clause.

## Verdicts

`keep` (ship as written), `change` (the comment says what to fix), `drop` (it
should not be a requirement).

## Data

From `product-prd`, a PRD file, or a validation tracker. Take the requirement
text verbatim. Do not summarize a requirement to make it fit: the wording is the
thing being approved, and a paraphrase approves something else.

Where a tracker records which requirements are already validated, show them as a
count only and keep them off the page. A reader asked to re-approve settled work
stops trusting the page.

## Notes

- Sort within a family by ID, not by your sense of importance. The reader knows
  their own spec's order.
- If a requirement contradicts another, anchor a note on both rather than
  picking a winner.
