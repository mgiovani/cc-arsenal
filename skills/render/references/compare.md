# Mode: compare

An option matrix that ends in a decision.

## The page

- **The question**, stated once at the top, with what changes depending on the
  answer. A comparison whose consequence is unstated is trivia.
- **The matrix**: options across, criteria down. Each cell carries a mark and the
  evidence behind it, not a bare score. A cell with no evidence is shown as
  unknown, which is a real and useful state.
- **Criteria weights**, visible and adjustable where the reader disagrees about
  what matters. Weighting is usually where the real disagreement lives, and
  hiding it hides the argument.
- **Per option**, a summary block naming what it is best at and what it costs.
- **Recommendation**, stated plainly with its reasoning, and marked as a
  recommendation rather than a conclusion.

Anchors: `option-<slug>` on each option, `criterion-<slug>` on each criterion
row, and `cell-<option>-<criterion>` on each intersection.

## Verdicts

One choice across the whole page: pick a winner. Plus a per-criterion override,
for the reader who accepts the matrix but rejects one row's weight.

## Data

From `docs-adr`, `docs-rfc`, `find-skills`, or a comparison done for the
occasion. For an ADR the alternatives section is the matrix, and the consequences
are the cost row.

Every cell needs a source: a benchmark, a doc, a constraint from the project. A
mark with nothing behind it is an opinion formatted as data, and the matrix
launders it into looking measured.

## Notes

- Three to five options. Beyond that the matrix stops being scannable and the
  extra columns are usually options nobody is really considering.
- Include the option of doing nothing when it is genuinely available. It is
  frequently the right answer and it is the one most often left off.
- Do not normalize scores across criteria that have no common unit. Show the real
  values and let the weights do the work.
