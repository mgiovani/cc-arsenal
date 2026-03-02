---
# Enhancement for: forge-review
disable-model-invocation: false
argument-hint: "[pr_number|commit_sha|--all]"
allowed-tools: "Read, Write, Edit, Bash(git *), Bash(gh *), Grep, Glob, Task, TaskCreate, TaskUpdate"
hooks:
  Stop:
  - hooks:
    - type: agent
      prompt: |
        Verify code review is complete before stopping:

        1. Check that docs/review-report.md exists and is non-empty
        2. Verify the report contains:
           - Overall assessment (APPROVED / NEEDS WORK / MAJOR ISSUES)
           - At least one Findings section (even if empty = "No issues found")
           - Positive Observations section
           - Recommended Refactorings section (can be "None" if clean)
        3. Verify that every finding references a specific file path and line number
        4. If there are CRITICAL or HIGH findings with "NEEDS WORK" overall:
           verify the recommendation section gives concrete, actionable next steps

        Block if the report is missing, has findings without file references, or lacks an Overall assessment.
      timeout: 60
---

## Claude Code Enhanced Features

This skill includes the following Claude Code-specific enhancements:

## Review Scope

$ARGUMENTS

**Scope options:**
- `<pr_number>` — Review only files changed in a GitHub PR
- `<commit_sha>` — Review only files changed in a commit
- `--all` or no args — Review entire codebase

## Progress Tracking

Use TaskCreate to track review phases:

```
TaskCreate: "Determine review scope and changed files" → scope analysis
TaskCreate: "Explore codebase patterns and conventions" → understand project
TaskCreate: "Review by dimension: correctness + performance" → first pass
TaskCreate: "Review by dimension: style + tests + errors" → second pass
TaskCreate: "Write review report" → produce docs/review-report.md
```

## Scope Determination

For PR reviews, get changed files:
```bash
gh pr view <pr_number> --json files --jq '.files[].path'
gh pr diff <pr_number>
```

For commit reviews:
```bash
git diff-tree --no-commit-id --name-only -r <commit_sha>
git show <commit_sha>
```

For full codebase:
```bash
Glob: "src/**/*.{ts,tsx,js,py}" or equivalent for discovered stack
```

## Parallel Review Pattern

For large codebases, spawn parallel review agents:

```
Task Agent 1: Review correctness + error handling
  - Look for unhandled exceptions, type mismatches, logic errors

Task Agent 2: Review performance + architecture
  - N+1 queries, unnecessary re-renders, missing indexes, coupling issues

Task Agent 3: Review test coverage + style
  - Missing tests for edge cases, code complexity, duplication

Merge all findings into docs/review-report.md
```

## Quality Gate (Stop Hook)

When you attempt to stop, an automated agent verifies:
- `docs/review-report.md` exists with all required sections
- Every finding has a file path reference
- Overall assessment is set

**Blocked example:**
```
⚠️ Review report incomplete:
- Missing: Overall assessment (APPROVED/NEEDS WORK/MAJOR ISSUES)
- Finding on line 23 has no file reference
Cannot complete until report is properly structured.
```
