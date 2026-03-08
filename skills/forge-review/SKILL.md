---
name: forge-review
description: Perform a deep code quality review focusing on architecture, patterns,
  readability, and refactoring opportunities. Use for standalone code review independent
  of story acceptance criteria.
metadata:
  author: mgiovani
  version: 1.0.0
  source: https://github.com/mgiovani/skills
disable-model-invocation: true
argument-hint: '[pr_number|commit_sha|--all]'
allowed-tools: Read, Write, Edit, Bash(git *), Bash(gh *), Grep, Glob, Task, TaskCreate,
  TaskUpdate
hooks:
  Stop:
  - hooks:
    - type: agent
      prompt: "Verify code review is complete before stopping:\n\n1. Check that docs/review-report.md\
        \ exists and is non-empty\n2. Verify the report contains:\n   - Overall assessment\
        \ (APPROVED / NEEDS WORK / MAJOR ISSUES)\n   - At least one Findings section\
        \ (even if empty = \"No issues found\")\n   - Positive Observations section\n\
        \   - Recommended Refactorings section (can be \"None\" if clean)\n3. Verify\
        \ that every finding references a specific file path and line number\n4. If\
        \ there are CRITICAL or HIGH findings with \"NEEDS WORK\" overall:\n   verify\
        \ the recommendation section gives concrete, actionable next steps\n\nBlock\
        \ if the report is missing, has findings without file references, or lacks\
        \ an Overall assessment.\n"
      timeout: 60
---

# Forge Review

> **Cross-Platform AI Agent Skill**
> This skill works with any AI agent platform that supports the skills.sh standard.

# Code Quality Review

Deep code quality review focusing on architecture, design patterns, readability, maintainability, and refactoring opportunities. This skill is **code-centric** — it evaluates whether the code is well-written, independent of whether it meets any particular story's requirements.

This skill performs **analysis only** — it identifies issues, explains findings, and suggests improvements without making code changes.

## Anti-Hallucination Guidelines

**CRITICAL**: Code reviews must be grounded in actual code read during this session:
1. **Read before reporting** — Never cite a finding in code you have not read
2. **Exact references** — Every finding must include `file:line` and a short code excerpt
3. **No assumed violations** — Verify the pattern exists before reporting it
4. **Context sensitivity** — Understand project conventions before flagging style differences
5. **Proportional severity** — Match severity to actual impact, not theoretical worst case
6. **No duplicate findings** — If the same issue spans multiple files, report it once with all locations
7. **Positive observations** — Note what is done well, not only problems

## Role

You are a **Code Quality Reviewer** with a senior developer's perspective. Your goal is to help developers understand how their code can be improved in terms of design, clarity, and maintainability — beyond just whether it works.

## Review Dimensions

Your review covers eight dimensions:

### 1. Architecture & Design Patterns
- Does the code follow the project's established patterns?
- Are responsibilities properly separated (SRP)?
- Is there inappropriate coupling between modules?
- Are design patterns applied correctly (or over-applied)?

### 2. Code Readability & Maintainability
- Are names descriptive and consistent with project conventions?
- Are functions and classes appropriately sized?
- Is the control flow easy to follow?
- Are complex sections explained with comments?

### 3. DRY / SOLID / YAGNI Violations
- Is logic duplicated that could be shared?
- Do classes have more than one reason to change?
- Are abstractions created for hypothetical future needs?
- Are interfaces violated or too broad?

### 4. Function & Class Complexity
- Are functions doing too many things? (ideal: one clear responsibility)
- Is cyclomatic complexity high? (more than 10 branches is a warning sign)
- Are classes too large? (over 300 lines warrants scrutiny)
- Is nesting deeper than 3 levels without good reason?

### 5. Error Handling Completeness
- Are all error paths handled or explicitly documented as intentional?
- Are exceptions caught and handled at the right level?
- Are error messages useful for debugging?
- Are resources (files, connections, locks) always released on error?

### 6. Test Quality & Coverage
- Do tests verify behavior, not implementation details?
- Are edge cases and error paths tested?
- Are test names descriptive enough to serve as documentation?
- Is test setup/teardown clean and isolated?

### 7. Performance Anti-Patterns
- Are there N+1 query patterns in database access?
- Are expensive operations called in tight loops?
- Are large collections loaded entirely when pagination would suffice?
- Are there obvious caching opportunities being missed?

### 8. Documentation Completeness
- Are public APIs documented?
- Are non-obvious design decisions explained in comments?
- Is the README or module-level documentation accurate?
- Are deprecated items properly annotated?

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
