# Team Review - Report Template

Use this template when generating the consolidated review report in Phase 5.

## Report Format

```markdown
# Team Code Review Report

**Scope**: [PR #123 | Commit abc123 | Entire Codebase]
**Date**: [YYYY-MM-DD]
**Mode**: [Full (7 reviewers) | Lite (4 combined reviewers)]
**Files Reviewed**: [N files]
**Total Findings**: [N issues]

## Executive Summary

[2-3 sentence overview of code quality and key findings. Include team consensus on whether the PR is ready to merge.]

**Overall Assessment**: [Approve | Approve with minor fixes | Request changes | Block]

**Reviewer Consensus**:
| Reviewer | Verdict | Key Concern |
|----------|---------|-------------|
| Architecture | [Approve/Concerns] | [One-line summary] |
| Security | [Approve/Concerns] | [One-line summary] |
| Performance | [Approve/Concerns] | [One-line summary] |
| Testing | [Approve/Concerns] | [One-line summary] |
| Style | [Approve/Concerns] | [One-line summary] |
| Docs & UX | [Approve/Concerns] | [One-line summary] |
| Adversary | [Approve/Concerns] | [One-line summary] |

## Severity Breakdown

| Severity | Count | Description |
|----------|-------|-------------|
| Critical | N | Bugs causing data loss, security holes, crashes |
| Major | N | Significant reliability, performance, or maintainability issues |
| Minor | N | Readability, consistency, or minor improvements |
| Nit | N | Style preferences, optional enhancements |

## Critical & Major Findings (Action Required)

### [FINDING_ID]: [Issue Title]
- **Severity**: Critical
- **Reviewer**: [Architecture/Security/Performance/etc.]
- **File**: `path/to/file.ext:line_start-line_end`
- **Description**: [What is wrong and why]
- **Code**:
  ```
  [Actual problematic code]
  ```
- **Impact**: [What goes wrong]
- **Suggested Fix**:
  ```
  [Corrected code example]
  ```

[Repeat for all Critical and Major findings...]

## Findings by Reviewer

### Architecture Review (N findings)

#### [ARCH-1]: [Issue Title]
- **Severity**: [Level]
- **File**: `path/to/file.ext:line_start-line_end`
- **Description**: [Issue and rationale]
- **Suggested Fix**: [Code example]

[Repeat for each finding...]

### Security Review (N findings)

#### [SEC-1]: [Issue Title]
- **Severity**: [Level]
- **OWASP**: [A01-A10]
- **File**: `path/to/file.ext:line_start-line_end`
- **Description**: [Vulnerability and attack scenario]
- **Suggested Fix**: [Code example]

[Repeat...]

### Performance Review (N findings)

#### [PERF-1]: [Issue Title]
- **Severity**: [Level]
- **File**: `path/to/file.ext:line_start-line_end`
- **Complexity**: [Current O(?) → Suggested O(?)]
- **Description**: [Issue]
- **Suggested Fix**: [Optimized code]

[Repeat...]

### Testing Review (N findings)

#### [TEST-1]: [Issue Title]
- **Severity**: [Level]
- **Source**: `path/to/source.ext:line`
- **Test File**: `path/to/test.ext` (or "Missing")
- **Description**: [Missing scenario]
- **Example Test**: [Code]

[Repeat...]

### Style & Patterns Review (N findings)

#### [STYLE-1]: [Issue Title]
- **Severity**: [Level]
- **File**: `path/to/file.ext:line_start-line_end`
- **Principle**: [DRY/SOLID/Convention]
- **Description**: [Issue]
- **Suggested Fix**: [Refactored code]

[Repeat...]

### Docs & UX Review (N findings)

#### [DOCS-1]: [Issue Title]
- **Severity**: [Level]
- **File**: `path/to/file.ext:line_start-line_end`
- **Description**: [Issue]
- **Suggested Fix**: [Improvement]

[Repeat...]

## Adversary Review

### Challenges to Other Findings
| Finding | Verdict | Rationale |
|---------|---------|-----------|
| [SEC-1] | Agree | [Confirmed exploitable] |
| [PERF-2] | Disagree (downgrade to Nit) | [Cold path, negligible impact] |
| [STYLE-3] | Adjust (upgrade to Major) | [Causes confusion in multiple places] |

### Additional Findings from Adversary

#### [ADV-1]: [Issue Title]
- **Severity**: [Level]
- **File**: `path/to/file.ext:line_start-line_end`
- **Description**: [Edge case or blind spot]
- **Why others missed it**: [Explanation]
- **Suggested Fix**: [Mitigation]

[Repeat...]

## Cross-Cutting Concerns

Findings that span multiple review dimensions:

- **[File:line]** — Flagged by [Security + Architecture]: [Description of cross-cutting issue]
- **[File:line]** — Flagged by [Performance + Testing]: [Description]

## Positive Observations

Highlight well-written code and good patterns:

- **[Area]**: [What was done well and why it's notable]
- **[Area]**: [Another positive observation]

## Action Items by Priority

### Immediate (Critical) — Must fix before merge
1. **[FINDING_ID]** — [Brief action item with file reference]

### High Priority (Major) — Should fix before merge
1. **[FINDING_ID]** — [Brief action item]

### When Convenient (Minor) — Can fix in follow-up
1. **[FINDING_ID]** — [Brief action item]

### Optional (Nit) — Author's discretion
1. **[FINDING_ID]** — [Brief action item]

## Statistics

| Metric | Value |
|--------|-------|
| Files reviewed | N |
| Files with issues | N |
| Total findings | N |
| Reviewers active | N |
| Adversary challenges | N (N accepted, N rejected) |

### Findings by Reviewer

| Reviewer | Critical | Major | Minor | Nit | Total |
|----------|----------|-------|-------|-----|-------|
| Architecture | N | N | N | N | N |
| Security | N | N | N | N | N |
| Performance | N | N | N | N | N |
| Testing | N | N | N | N | N |
| Style | N | N | N | N | N |
| Docs & UX | N | N | N | N | N |
| Adversary | N | N | N | N | N |
| **Total** | **N** | **N** | **N** | **N** | **N** |

---

**Verdict**: [Approve / Approve with fixes / Request changes / Block]
**Next Steps**: Address Critical and Major findings. Run `/team-review` again after fixes for diff-only re-review.
```

## Re-Review Report Format

Use this format for iterative re-reviews after fixes:

```markdown
# Team Review Re-Review Report (Diff-Only)

**Original Review Date**: [YYYY-MM-DD]
**Re-Review Date**: [YYYY-MM-DD]
**Files Re-Scanned**: [N files changed since last review]
**Reviewers Re-Activated**: [List of re-spawned reviewers]

## Summary

| Metric | Count |
|--------|-------|
| Previous findings | N |
| Resolved | N |
| Remaining | N |
| New issues from fixes | N |

## Resolved Findings
- ~~**[SEC-1]** [Issue title]~~ — Fixed in `file.py:45` ✅
- ~~**[PERF-2]** [Issue title]~~ — Fixed in `file.ts:30` ✅

## Remaining Findings
- **[ARCH-1]** [Issue title] — Still present in `file.js:67`

## New Findings
### [NEW-1]: [Issue Title]
- **Severity**: [Level]
- **Introduced by**: Fix for [Original Finding ID]
- **File**: `path/to/file.ext:line`
- **Description**: [Issue]

---

**Updated Verdict**: [Approve / Request further changes]
```
