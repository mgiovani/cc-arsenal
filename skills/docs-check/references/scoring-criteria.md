# Rating Criteria

Coarse per-document rubric for Phase 5. No numeric scoring or weighted averages — one rating per document, chosen by the first rule below that applies (checked in order).

## Rating Definitions

| Rating  | Applies when |
|---------|--------------|
| Broken  | Contains a hallucination (claim contradicted by the codebase), a broken internal link, or invalid Mermaid syntax |
| Missing | Doc is expected given the detected stack (e.g. a `data-model.md` for a repo with a schema) but doesn't exist |
| Stale   | All claims check out, but the doc predates a significant related code change, has unreplaced `{{PLACEHOLDER}}` values, or is missing an expected section |
| Good    | Current, complete, no broken links, no invalid diagrams, no hallucinations |

Broken outranks Stale: a doc with one false claim is Broken even if everything else about it is current — a wrong claim is worse than an old-but-true one.

## Evidence Requirement

Every rating must cite what was actually checked — a git log date, a grep result, a find count. Never assign "Stale" or "Broken" without the command output that justifies it; never assign "Good" without having actually run the freshness/completeness/quality checks in Phase 4.

## Detailed Report Format (per document)

For each documentation file rated Stale, Broken, or Missing, include:
- Filename and path
- Rating and the one-line reason
- Specific issues with line numbers where applicable
- The verification command used as evidence
- Recommended follow-up command (docs-update, docs-diagram, docs-init)

Good-rated docs need only a one-line listing — no evidence dump for docs with nothing wrong.

## Best Practices

- Run regularly — freshness drift compounds silently between checks.
- Prioritize Broken over Stale over Missing when recommending fixes — hallucinations mislead readers actively, staleness merely under-informs them.
- Don't let a "mostly fine" rating hide one hallucinated claim inside a doc — Broken always surfaces in the summary even if the rest of the doc is solid.
