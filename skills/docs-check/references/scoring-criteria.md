# Scoring Criteria

Complete scoring rubrics and thresholds for documentation quality assessment.

## Freshness Scoring (per document)

| Score Range | Rating   | Criteria |
|-------------|----------|----------|
| 90-100      | Fresh    | Updated within last 7 days or no related code changes |
| 70-89       | Good     | Minor code changes since last update |
| 50-69       | Stale    | Significant code changes since last update |
| < 50        | Outdated | Major code changes or very old |

## Completeness Scoring (per document)

| Score Range | Rating     | Criteria |
|-------------|------------|----------|
| 90-100      | Complete   | All sections present, no placeholders |
| 70-89       | Good       | Most sections present, minor gaps |
| 50-69       | Incomplete | Several missing sections |
| < 50        | Poor       | Major sections missing |

## Quality Scoring (per document)

| Score Range | Rating    | Criteria |
|-------------|-----------|----------|
| 90-100      | Excellent | No issues, all diagrams valid |
| 70-89       | Good      | Minor formatting issues |
| 50-69       | Fair      | Several issues |
| < 50        | Poor      | Major problems, broken diagrams |

## Overall Score Calculation

- Average of all document scores
- Weight by importance: core docs (architecture, onboarding) matter more than supporting docs (contributing, RFCs) — let a stale contributing.md pull the overall score down less than a stale architecture.md.

## Detailed Report Format (per document)

For each documentation file, include:
- **Filename and path**
- **Score breakdown** (Freshness + Completeness + Quality)
- **Last Updated**: Timestamp
- **Specific Issues**: With line numbers
- **Recommendations**: Actionable next steps with commands

## Best Practices for Scoring

- **Run regularly**: Make it part of your workflow
- **Address issues**: Do not let documentation debt accumulate
- **Automate**: Consider running in CI for documentation PRs
- **Prioritize**: Fix high-impact issues first
- **Track scores**: Monitor documentation health over time
