---
name: docs-check
description: Read-only audit of documentation against the current codebase — flags
  stale docs, missing sections, broken links, and hallucinated claims (wrong file
  references, wrong counts, diagram entities that don't exist in code). Use for
  "check the docs", "audit documentation", "are the docs stale", "find hallucinations
  in docs", "docs health check", "does this doc still match the code", or before
  onboarding/release. Reports only, never edits files — for actually fixing or
  regenerating docs use docs-update instead.
metadata:
  author: mgiovani
  version: 2.0.0
argument-hint: '[focus]'
allowed-tools: Read, Grep, Glob, Bash(git *, find *), Task
context: fork
agent: general-purpose
---

# Check Documentation Quality

Audit documentation freshness, completeness, and quality against the current codebase state. Read-only: never edit or write to any doc file.

## Anti-Hallucination Detection

This skill exists to catch docs that lie. For every claim in a doc, verify it against the actual codebase rather than trusting the doc text:
1. **Cross-reference claims** — component/service names, described relationships
2. **Verify counts** — if a doc says "5 services", count the actual services
3. **Check file references** — confirm every referenced path exists
4. **Validate diagrams** — every Mermaid entity must exist in real code

## Workflow

### Phase 1: Scan docs/

1. Glob all documentation files (`docs/`, `docs/adr/`, `docs/rfc/`, top-level `README.md`, `CONTRIBUTING.md`).
2. Infer focus categories from the filenames actually present — don't assume a fixed set. A repo with `docs/data-model.md` gets a "data" category; one with `docs/deployment.md` and `docs/docker-compose.yml` docs gets "infrastructure"; group whatever's there under a name that matches its content. If the user names a focus that doesn't match anything found, say so and list the categories that do exist instead of silently no-op'ing.
3. Detect tech stack, database presence, deployment configs, and project type from the codebase (package files, Dockerfiles, etc.) to know what documentation *should* exist.

### Phase 2: Parse arguments

Extract an optional focus keyword from the invocation and match it against the categories found in Phase 1. No argument means check everything found.

### Phase 3: Verify claims against the codebase

For a small doc set (a handful of files, or a one-shot check like "does this file exist"), verify directly inline with Read/Grep/Glob/git — spawning a subagent for a single lookup adds latency for no benefit.

For a large multi-doc audit (a full `docs/` tree, many ADRs, cross-referencing several files against the codebase), spawn one Explore subagent per document or logical section so each verifies its claims independently. Where no Task tool is available, fall back to processing each document sequentially inline instead — same verification steps, one document at a time, no parallelism. See [references/verification-patterns.md](references/verification-patterns.md) for section-level verification patterns and bash commands.

**Verification categories**: component/service names, numeric counts, diagram entities, file/path references, technology claims (against package files), relationship claims.

### Phase 4: Validation checks

**Relevance**: which docs are relevant given the detected stack; what's missing for detected technologies.

**Freshness**: compare each doc's last-modified date (git log) against related code changes. A doc untouched since before a significant change to the code it describes is stale.

**Completeness**: required sections present, no unreplaced `{{PLACEHOLDER}}` values, diagrams present where expected.

**Quality**: valid Mermaid syntax, no broken internal links, no empty sections.

See [references/verification-patterns.md](references/verification-patterns.md) for the exact commands.

### Phase 5: Rate each document

Skip numeric scoring — a 0-100 breakdown per doc implies precision this check doesn't have. Give each document one coarse rating instead:

- **Good** — current, complete, no broken links or invalid diagrams
- **Stale** — accurate but outdated (freshness or completeness gaps, no false claims)
- **Broken** — contains hallucinations, broken links, or invalid Mermaid syntax
- **Missing** — expected given the detected stack but doesn't exist

See [references/scoring-criteria.md](references/scoring-criteria.md) for the full rubric per rating.

### Phase 6: Generate report

- Status summary with counts per rating
- Documents grouped by rating (Good / Stale / Broken / Missing)
- **Hallucination Report** — claims that don't match reality, with evidence
- Quality issues with specific file:line locations
- Actionable recommendations naming a specific follow-up command (docs-update, docs-diagram) and why

## Output Format

### Status Summary
```
Documentation Health Report

Good (3 docs):
  docs/architecture.md
  docs/onboarding.md
  docs/adr/ (5 records)

Stale (2 docs):
  docs/data-model.md — last updated 2025-03-01, schema changed 2025-06-15
  docs/deployment.md — references removed staging environment

Broken (1 doc):
  docs/architecture.md — Hallucination: claims "6 microservices", 3 found

Missing (1 doc, expected for detected stack):
  docs/security.md — auth code present, no security doc
```

### Hallucination Report

```
Hallucinations Detected:

docs/architecture.md:
  - Line 45: Claims "6 microservices" but only 3 found
    Verified with: find . -name "*service*" -type d | wc -l -> 3
  - Line 78: References "AuthService" which doesn't exist
    Verified with: grep -r "class AuthService" . -> no results
```

### Recommendations Format

```
Priority Recommendations:

1. HIGH: docs/architecture.md claims 6 microservices, only 3 exist
   Command: docs-update architecture
   Reason: hallucinated count, misleads new engineers

2. MEDIUM: docs/data-model.md has 2 unreplaced {{PLACEHOLDER}} values
   Command: docs-update data-model
   Reason: incomplete since scaffolding

3. LOW: docs/security.md missing, auth module exists
   Command: docs-diagram security or docs-init security
   Reason: no security documentation for an app with auth
```

## Usage Examples

```
docs-check                      # check everything found in docs/
docs-check core                 # focus on whatever category maps to "core" in this repo
docs-check focus on database documentation
```

## Important Notes

- Non-destructive: only reads, never modifies documentation.
- Every number reported (counts, dates, "N days stale") must come from a command actually run in this session — never estimate or infer a count without running find/grep/git for it.
- Recommends `docs-update` or `docs-diagram` as the fix — this skill only reports.

## When to Run

- Before onboarding new team members
- During documentation reviews
- After major refactoring
- As part of a pre-release checklist
- When documentation feels stale

## Additional Resources

- [references/verification-patterns.md](references/verification-patterns.md) — load when running Phase 3/4 verification, for exact bash/grep patterns and the subagent prompt templates
- [references/scoring-criteria.md](references/scoring-criteria.md) — load when assigning Phase 5 ratings, for the full Good/Stale/Broken/Missing rubric
