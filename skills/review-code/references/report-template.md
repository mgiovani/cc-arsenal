# Code review - report template

Use this template when generating the review report in Phase 5.

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

### Correctness & Logic (N findings)

#### Finding CL-1: [Issue Title]
- **Severity**: Critical
- **File**: `path/to/file.py:123-130`
- **Description**: [What is wrong and why]
- **Code**:
  ```python
  # Current code
  [Actual problematic code]
  ```
- **Impact**: [What goes wrong and when]
- **Suggested Fix**:
  ```python
  # Improved code
  [Corrected code example]
  ```

[Repeat for each finding...]

### Performance (N findings)

#### Finding PF-1: [Issue Title]
- **Severity**: Major
- **File**: `path/to/file.ts:45-60`
- **Description**: [What is slow and why]
- **Code**:
  ```typescript
  // Current code
  [Actual code with performance issue]
  ```
- **Complexity**: [Current: O(n²) → Suggested: O(n)]
- **Suggested Fix**:
  ```typescript
  // Optimized code
  [Improved code example]
  ```

[Repeat for each finding...]

### Code Style & Patterns (N findings)

#### Finding CS-1: [Issue Title]
- **Severity**: Minor
- **File**: `path/to/file.go:89-105`
- **Description**: [What violates conventions and why it matters]
- **Code**:
  ```go
  // Current code
  [Actual code with style issue]
  ```
- **Convention**: [Reference to project convention or industry standard]
- **Suggested Fix**:
  ```go
  // Improved code
  [Refactored code example]
  ```

[Repeat for each finding...]

### Test Coverage Gaps (N findings)

#### Finding TC-1: [Issue Title]
- **Severity**: Major
- **Source File**: `path/to/source.py:30-50`
- **Test File**: `path/to/test_source.py` (or "Missing")
- **Description**: [What is untested and why it matters]
- **Missing Scenario**: [Specific test case that should exist]
- **Suggested Test**:
  ```python
  def test_edge_case():
      # Example test for the missing scenario
      [Complete test code example]
  ```

[Repeat for each finding...]

### Error Handling & Edge Cases (N findings)

#### Finding EH-1: [Issue Title]
- **Severity**: Major
- **File**: `path/to/file.js:67-80`
- **Description**: [What error case is unhandled]
- **Code**:
  ```javascript
  // Current code
  [Actual code with error handling gap]
  ```
- **Failure Scenario**: [Specific scenario that causes a problem]
- **Suggested Fix**:
  ```javascript
  // With proper error handling
  [Improved code example]
  ```

[Repeat for each finding...]

## Positive Observations

Highlight well-written code, good patterns, and strengths found during review:

- **[Pattern/Area]**: [What was done well and why it's notable]
- **[Pattern/Area]**: [Another positive observation]

## Action Items by Priority

### Immediate (Critical)
1. **[CL-1]** - [Brief action item with file reference]
2. [...]

### High Priority (Major)
1. **[PF-1]** - [Brief action item with file reference]
2. [...]

### When Convenient (Minor)
1. **[CS-1]** - [Brief action item with file reference]
2. [...]

### Optional (Nit)
1. **[CS-3]** - [Brief action item with file reference]
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
| **Total** | **N** | **N** | **N** | **N** | **N** |

---

**Next Steps**: Address Critical and Major findings first. Run `/review-code` again after fixes, it re-derives the current diff and reports what changed.
```
