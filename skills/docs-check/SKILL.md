---
name: docs-check
description: "Validate documentation freshness, completeness, and quality against the current codebase state. This skill should be used when users want to check documentation health, find stale docs, detect hallucinations in documentation, or audit documentation quality."
disable-model-invocation: true
argument-hint: "[focus]"
allowed-tools: Read, Grep, Glob, Bash(git *, find *), Task
context: fork
agent: general-purpose
---

# Check Documentation Quality

Validate documentation freshness, completeness, and quality against current codebase state.

## Anti-Hallucination Detection

**CRITICAL**: This skill should DETECT hallucinations in existing docs:
1. **Cross-reference claims** - For each claim in docs, verify against actual code
2. **Verify component counts** - If docs say "5 services", count actual services
3. **Check file references** - Verify all referenced files actually exist
4. **Validate diagrams** - Ensure diagram components match real codebase

## Workflow

### Phase 1: Parallel Documentation Analysis (Use SubAgents)

#### For Multiple Documents

Spawn parallel subagents for each documentation file:

```
Use Task tool with multiple parallel agents:

Agent 1 - Core Docs Verification:
- prompt: "Read docs/architecture.md and verify EVERY claim against the actual codebase. For each component mentioned, confirm it exists. For each count, verify with find/glob. Report any claims that cannot be verified."
- subagent_type: "general-purpose"

Agent 2 - Data Docs Verification:
- prompt: "Read docs/data-model.md and verify all entities exist in actual model files. Check each relationship claimed is real. Report mismatches."
- subagent_type: "general-purpose"

Agent 3 - Explore Codebase Reality:
- prompt: "Analyze the actual codebase structure. Count real components, services, models. This will be compared against documentation claims."
- subagent_type: "Explore"
```

#### For Single Document (Section-Level Verification)

Even when checking ONE document, spawn subagents for each logical section. See [references/verification-patterns.md](references/verification-patterns.md) for detailed section-level verification patterns.

**Verification categories to parallelize**:
- Component/service names - Do they exist?
- Numeric counts - Are they accurate?
- Diagram entities - Are they real?
- File/path references - Do files exist?
- Technology claims - Are they in package files?
- Relationship claims - Do the connections exist in code?

### Phase 2: Parse Arguments

1. Extract optional focus area from `$ARGUMENTS`
2. Focus areas: `core`, `data`, `infrastructure`, `all`
3. Default: check all documentation

### Phase 3: Scan and Analyze

1. Find all documentation files in `docs/`
2. Identify documentation types present
3. Check for ADRs and RFCs
4. Detect technology stack, database presence, deployment configs, project type

### Phase 4: Perform Validation Checks

**A. Relevance Check**: Determine which docs are relevant, identify missing documentation for detected technologies.

**B. Freshness Check**: Compare doc last-modified dates with related code changes using git history. Flag docs not updated after significant code changes.

**C. Completeness Check**: Verify all required sections are present, check for unreplaced `{{PLACEHOLDER}}` values, ensure diagrams exist where expected.

**D. Quality Check**: Validate Mermaid diagram syntax, check for broken internal links, verify markdown formatting, check for empty sections.

For detailed verification commands and bash patterns, see [references/verification-patterns.md](references/verification-patterns.md).

### Phase 5: Calculate Scores

See [references/scoring-criteria.md](references/scoring-criteria.md) for complete scoring rubrics.

**Score categories per document**:
- **Freshness** (0-100): Based on recency of updates relative to code changes
- **Completeness** (0-100): Based on section coverage and placeholder replacement
- **Quality** (0-100): Based on formatting, diagram validity, link integrity

**Overall Score**: Average of all document scores, weighted by importance (core docs > others).

### Phase 6: Generate Report

Produce a comprehensive report containing:
- Status summary with overall score
- List of documents by status (Good, Needs Attention, Missing)
- **Hallucination Report** - Claims that do not match reality
- Quality issues with specific locations and line numbers
- Actionable recommendations with specific commands

## Output Format

### Status Summary
```
Documentation Health Report

Overall Score: 85/100

Good (3 docs):
  docs/architecture.md (Score: 95/100)
  docs/onboarding.md (Score: 92/100)
  docs/adr/ (5 records, Score: 88/100)

Needs Attention (2 docs):
  docs/data-model.md (Score: 65/100)
  docs/deployment.md (Score: 58/100)

Missing (2 docs):
  docs/security.md
  docs/api-documentation.md

Quality Issues:
  docs/data-model.md:42 - Invalid Mermaid syntax
  docs/architecture.md:15 - Broken link to [non-existent.md]
```

### Recommendations Format

```
Priority Recommendations:

1. HIGH: Update data model documentation
   Command: /docs-diagram er
   Reason: Schema changed 5 days ago, ER diagram missing

2. MEDIUM: Fix deployment documentation placeholders
   Command: /docs-update deployment
   Reason: Contains unreplaced placeholders

3. LOW: Add security documentation
   Command: /docs-diagram security
   Reason: Good practice for complete documentation
```

## Usage Examples

Check all documentation:
```
/docs-check
```

With specific focus:
```
/docs-check core
/docs-check data
/docs-check focus on database documentation
```

Quick check:
```
/docs-check quick
```

## Important Notes

- **Non-destructive**: Only reads, never modifies documentation
- **Git-aware**: Uses git history to assess freshness
- **Context-aware**: Understands project type and relevant docs
- **Actionable**: Provides specific commands to fix issues
- **Incremental**: Can be run frequently

## When to Run

- Before onboarding new team members
- During documentation reviews
- After major refactoring
- As part of pre-release checklist
- When documentation feels stale
- Regularly (weekly or bi-weekly)

## Additional Resources

- For detailed verification commands and bash patterns, see [references/verification-patterns.md](references/verification-patterns.md)
- For complete scoring rubrics and thresholds, see [references/scoring-criteria.md](references/scoring-criteria.md)

---

**Dependencies**: Requires git for freshness checking
**Output**: Comprehensive health report with scores and recommendations
