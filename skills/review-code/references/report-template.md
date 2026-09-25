# Code review - report template

Use this template when generating the review report in Phase 5. It's a shape to fill in, not literal text to copy: swap every bracketed placeholder for the real finding, and drop any section that ends up with zero findings in it.

Every dimension shares one findings-block schema (severity, location, description, code, an extra field, suggested fix). Repeat that block once per finding, and repeat it for each dimension in the table below, swapping in that dimension's prefix, location fields, and extra field. Keep the extra field even when trimming everything else to stay terse.

## Report format

```markdown
# Code Review Report

**Scope**: [PR #123 | Commit abc123 | Entire Codebase]
**Date**: [YYYY-MM-DD]
**Files Reviewed**: [N files]
**Total Findings**: [N issues]

## Executive Summary

[2-3 sentence overview of code quality, key strengths, and most important issues to address]

**Overall Assessment**: [Excellent | Good | Needs Improvement | Significant Issues]

## Severity Breakdown

| Severity | Count | Description |
|----------|-------|-------------|
| Critical | N | Bugs causing data loss, crashes, or incorrect business logic |
| Major | N | Significant reliability, performance, or maintainability issues |
| Minor | N | Readability, consistency, or minor inefficiency improvements |
| Nit | N | Style preferences, cosmetic suggestions, optional improvements |

## Findings by Dimension

For each dimension below with at least one finding, add a heading (`### <Dimension> (N findings)`) and repeat this block once per finding:

#### Finding <PREFIX>-N: [Issue Title]
- Severity: [Critical | Major | Minor | Nit]
- File: `path/to/file.ext:LINE-LINE` (Test Coverage Gaps use Source File and Test File instead, per the table below)
- Description: [What is wrong and why]
- Code:
  ```
  [Actual problematic code] (Test Coverage Gaps omit this field)
  ```
- [Dimension's extra field, from the table below]: [value]
- Suggested Fix:
  ```
  [Corrected code example] (Test Coverage Gaps use this field for the suggested test instead)
  ```

| Dimension | Prefix | What it covers | Extra field |
|-----------|--------|-----------------|-------------|
| Correctness & Logic | CL | Bugs, race conditions, and logic errors, each pinned to the exact lines that misbehave | Impact: what goes wrong and when |
| Performance | PF | Slow paths, with a before/after estimate so the payoff of fixing them is obvious | Complexity: current Big-O to suggested Big-O |
| Code Style & Patterns | CS | Drift from this project's own conventions, not a general opinion about style | Convention: the project convention or industry standard being violated |
| Test Coverage Gaps | TC | Untested code paths next to a concrete example of the scenario a new test would need to cover; Source File and Test File (or "Missing") replace the single File field, Code is omitted, and Suggested Fix becomes Suggested Test | Missing Scenario: the specific test case that should exist |
| Error Handling & Edge Cases | EH | Unhandled failures and missing validation, described by the scenario that would trigger them in production | Failure Scenario: the specific scenario that causes a problem |
| Simplicity & Over-engineering | OE | Unnecessary complexity flagged by the Agent 6 lens ([agent-prompts.md](agent-prompts.md#agent-6---simplicity--over-engineering)); default severity Minor or Nit | Tag: one of `[delete]`/`[reuse]`/`[stdlib]`/`[builtin]`/`[unneeded]`/`[simplify]`, plus lines removed |

## Positive Observations

Highlight well-written code, good patterns, and strengths found during review:

- [Pattern/Area]: [What was done well and why it's notable]
- [Pattern/Area]: [Another positive observation]

## Action Items by Priority

### Immediate (Critical)
1. [CL-1] - [Brief action item with file reference]
2. [...]

### High Priority (Major)
1. [PF-1] - [Brief action item with file reference]
2. [...]

### When Convenient (Minor)
1. [CS-1] - [Brief action item with file reference]
2. [...]

### Optional (Nit)
1. [CS-3] - [Brief action item with file reference]
2. [...]

## Statistics

| Metric | Value |
|--------|-------|
| Files reviewed | N |
| Files with issues | N |
| Total findings | N |
| Critical findings | N |
| Major findings | N |
| Minor findings | N |
| Nit findings | N |
| Findings per file (avg) | N.N |

### Findings by Dimension

| Dimension | Critical | Major | Minor | Nit | Total |
|-----------|----------|-------|-------|-----|-------|
| Correctness & Logic | N | N | N | N | N |
| Performance | N | N | N | N | N |
| Code Style & Patterns | N | N | N | N | N |
| Test Coverage Gaps | N | N | N | N | N |
| Error Handling | N | N | N | N | N |
| Simplicity & Over-engineering | N | N | N | N | N |
| **Total** | **N** | **N** | **N** | **N** | **N** |

---

**Next Steps**: Address Critical and Major findings first. Run `/review-code` again after fixes, it re-derives the current diff and reports what changed.
```
