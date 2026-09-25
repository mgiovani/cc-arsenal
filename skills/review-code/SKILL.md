---
name: review-code
description: Runs a comprehensive multi-agent code review of a PR, commit, or the
  whole codebase across six dimensions (correctness, performance, code style, test
  coverage, error handling, and simplicity/over-engineering) and returns a severity-ranked
  report with file:line findings and fix suggestions. Use when the user wants a thorough
  code review, asks to review a PR or diff, or wants over-engineered code flagged
  for simplification. Analysis only, identifying issues without modifying code, committing,
  or running tests. Not for a security-focused audit (use review-security), a visual/UX
  design critique (use review-design), or a deep performance-only investigation with
  profiling and query-level analysis (use review-perf).
metadata:
  summary: "Multi-agent code review across six dimensions, from correctness and performance to tests and error handling"
  author: mgiovani
  version: 1.1.0
---

# Code Review

Multi-agent code review spanning six dimensions: correctness, performance, code style, test coverage gaps, error handling, and simplicity/over-engineering. This skill performs analysis only. It surfaces issues, explains why they matter, and suggests fixes, but never touches the code itself.

Every finding must cite a `file:line` you actually read: no hypothetical issues, no estimated counts. Only review files within the determined scope, and only flag style deviations from the project's own conventions, not personal preference.

## Review Workflow

### Phase 0: Determine Review Scope

Parse arguments to determine what to review:

```
Arguments:
- <pr_number>: Review only files changed in PR (e.g., "123", "#123")
- <commit_sha>: Review only files changed in commit (e.g., "abc123")
- "--all" or no args: Review entire codebase
- "--focus [correctness|performance|style|tests|errors]": Focus on specific review dimension
```

If PR or commit specified, use Bash to get changed files and diff context:

```bash
# For PR - get files and full diff
gh pr view <pr_number> --json files --jq '.files[].path'
gh pr diff <pr_number>

# For commit
git diff-tree --no-commit-id --name-only -r <commit_sha>
git show <commit_sha>
```

When reviewing a PR or commit, always retrieve the full diff: the diff context is essential for understanding what changed versus what was already there. Agents should focus findings on the changed lines while using surrounding code for context.

### Phase 1: Project Discovery

Explore the codebase to understand its technology stack and conventions, plus whatever quality standards it already holds itself to:

### Phase 2: Initialize Progress Tracking (optional)

If TodoWrite is available, use it to track review progress across the specialist dimensions and report generation. Skip it for a small scoped review or in an environment without it (it's a convenience, not a requirement).

### Phase 3: Parallel Specialist Review

Spawn 6 parallel Explore agents for comprehensive code review (5 below, plus Agent 6 from the simplicity/over-engineering module later in this file). Each agent specializes in a specific review dimension. For detailed agent prompts and patterns, see [references/agent-prompts.md](references/agent-prompts.md).

Agent assignments:

| Agent | Dimension | Focus |
|-------|-----------|-------|
| 1 | Correctness & Logic | bugs, race conditions, off-by-one errors, null safety, type mismatches |
| 2 | Performance | algorithmic complexity, unnecessary allocations, N+1 queries, missing caching, memory leaks |
| 3 | Code Style & Patterns | naming, structure, DRY violations, SOLID adherence, framework idioms |
| 4 | Test Coverage Gaps | untested code paths, missing edge case tests, weak assertions, test quality |
| 5 | Error Handling & Edge Cases | unhandled exceptions, missing validation, boundary conditions, graceful degradation |

No Task/Explore tool available: run the same six specialist prompts (Agents 1-6, full text in [references/agent-prompts.md](references/agent-prompts.md)) as sequential Grep+Read passes instead of parallel subagents. Take one dimension at a time, in the same order, each following the same steps below, then merge all six dimensions' findings into one list before Phase 4.

Each agent must:
1. Grep for issue patterns across files in scope
2. Read each match to verify context and confirm it is a genuine issue
3. Extract exact code snippets (5-10 lines) with file:line references
4. Explain why the code is problematic
5. Classify severity (Critical/Major/Minor/Nit)
6. Provide a concrete fix suggestion with code example

Severity definitions:

| Severity | Meaning |
|----------|---------|
| Critical | Bugs that cause data loss, crashes, security holes, or incorrect business logic |
| Major | Significant issues that hurt reliability or performance, or create a maintainability risk |
| Minor | Improvements to readability and consistency, plus minor inefficiencies worth flagging |
| Nit | Style preferences, cosmetic suggestions, optional improvements |

### Phase 4: Consolidate & Analyze Findings

After all agents complete:

1. Collect all findings from the 6 parallel agents.
2. Deduplicate: remove duplicate findings across agents (e.g., the same function flagged by both correctness and error handling agents).
3. Prioritize by severity, using the same scale as above: Critical (data corruption, crashes, security implications, broken business logic), Major (performance bottlenecks, reliability issues, test gaps for critical paths), Minor (code readability, minor inefficiencies, style inconsistencies), Nit (naming preferences, optional simplifications, cosmetic changes).
4. Categorize by dimension: group findings under the 6 specialist categories.
5. Cross-reference findings that span multiple dimensions (e.g., a missing null check is both a correctness and error handling issue).
6. Compute statistics: total findings by severity, by dimension, files reviewed vs. files with issues.

### Phase 5: Generate Review Report

Generate a comprehensive markdown report following the template in [references/report-template.md](references/report-template.md).

Report sections:
1. Executive summary with overall code quality assessment
2. Severity breakdown with counts
3. Findings organized by dimension: each one carries a file:line, a code snippet, an explanation, and a fix suggestion
4. Prioritized action items (Critical first, then Major)
5. Positive observations - highlight well-written code, good patterns, thorough tests

To re-review after fixes, just run the skill again on the same PR/commit: Phase 0's scoping naturally re-derives the current diff, so it re-scopes to what's actually still there without a separate workflow.

## Usage

```bash
# Review a specific PR
review-code 123
review-code #456

# Review a specific commit
review-code abc123def

# Review entire codebase
review-code --all
review-code

# Focus on a specific dimension
review-code 123 --focus performance
review-code --all --focus tests

# Re-review after fixes — just run it again on the same PR/commit
review-code 123
```

## Focus Options

- `correctness`: Focus on bugs, logic errors, type safety, race conditions
- `performance`: Focus on algorithmic complexity, resource usage, caching, queries
- `style`: Focus on naming, structure, patterns, framework idioms, DRY/SOLID
- `tests`: Focus on test coverage gaps, assertion quality, edge case testing
- `errors`: Focus on error handling, validation, boundary conditions, graceful degradation

If no focus specified, perform comprehensive review across all dimensions.

## Additional Resources

- [references/agent-prompts.md](references/agent-prompts.md) - Detailed grep patterns and agent prompts for each review dimension
- [references/report-template.md](references/report-template.md) - Full markdown report template with all sections

## Limitations

- Static, pattern-based analysis: cannot measure actual runtime/performance impact or detect runtime-only issues; some findings may turn out to be intentional design choices
- Language support: grep patterns in [references/agent-prompts.md](references/agent-prompts.md) are written for C-like and Python syntax, so adapt them for other languages before relying on pattern coverage
- Does not modify code or run tests/benchmarks, and skips security-specific analysis entirely (use review-security for that)

## Simplicity & Over-engineering lens (Claude Code enhancement)

LLM-written code tends to over-engineer: interfaces built for one implementation, factories for one product, wrapper layers that just forward a call. None of that shows up as a bug, so the five specialists in Phase 3 don't catch it: it needs its own lens. This module adds a 6th parallel specialist and a matching report dimension.

### Agent 6: Simplicity & Over-engineering

Spawn this agent alongside Agents 1-5 in Phase 3, in the same parallel batch. Full prompt and tag definitions: [references/agent-prompts.md](references/agent-prompts.md#agent-6---simplicity--over-engineering).

Routing out of scope: when Agent 6 flags something that Phase 4 consolidation determines is actually a correctness, security, or performance issue, move it into the matching dimension (`CL-`, `PF-`, or `EH-` prefix) instead of reporting it as an OE finding. An over-engineered function that also happens to be buggy is a bug first.

Add its dimension (`OE-` prefix, Minor/Nit by default) to Phase 4/5 output: full report-addendum spec in [references/agent-prompts.md](references/agent-prompts.md#agent-6---simplicity--over-engineering).
