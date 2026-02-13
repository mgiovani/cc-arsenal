---
name: review-code
description: Perform comprehensive multi-agent code review for PRs, commits, or entire
  codebases. This skill should be used when a user wants a thorough code review covering
  correctness, performance, code style, test coverage, and error handling. Analysis
  only - identifies issues without modifying code.
metadata:
  author: mgiovani
  version: 1.0.0
  source: https://github.com/mgiovani/skills
---

# Review Code

> **Cross-Platform AI Agent Skill**
> This skill works with any AI agent platform that supports the skills.sh standard.

# Code Review

Comprehensive multi-agent code review covering correctness, performance, code style, test coverage gaps, and error handling. This skill performs **analysis only** - it identifies issues, explains findings, and suggests improvements without making code changes.

## Anti-Hallucination Guidelines

**CRITICAL**: Code reviews must be based on ACTUAL code analysis and VERIFIED patterns:
1. **Read before claiming** - Never report issues in code that has not been read
2. **Evidence-based findings** - Every finding must reference specific file paths and line numbers
3. **Pattern matching** - Use Grep to find actual problematic patterns, not hypothetical ones
4. **Quantifiable results** - Count actual instances, do not estimate
5. **No false positives** - Verify each finding matches documented issue patterns
6. **Scope verification** - Only review files within specified scope (PR/commit/all)
7. **Respect conventions** - Understand project patterns before flagging style issues
8. **Context matters** - A pattern acceptable in one context may be problematic in another

## Review Workflow

### Phase 0: Determine Review Scope

Parse arguments to determine what to review:

```
Arguments:
- <pr_number>: Review only files changed in PR (e.g., "123", "#123")
- <commit_sha>: Review only files changed in commit (e.g., "abc123")
- "--all" or no args: Review entire codebase
- "--focus [correctness|performance|style|tests|errors]": Focus on specific review dimension
If PR or commit specified, use Bash to get changed files and diff context:
```bash
# For PR - get files and full diff
gh pr view <pr_number> --json files --jq '.files[].path'
gh pr diff <pr_number>

# For commit
git diff-tree --no-commit-id --name-only -r <commit_sha>
git show <commit_sha>
**Important**: When reviewing a PR or commit, always retrieve the full diff. The diff context is essential for understanding what changed vs. what was already there. Agents should focus findings on **changed lines** while using surrounding code for context.

### Phase 1: Project Discovery

Explore the codebase to understand the project's technology stack, conventions, and quality standards:

### Phase 2: Initialize Progress Tracking

Use TodoWrite to track review progress across all specialist dimensions and report generation.

### Phase 3: Parallel Specialist Review

Spawn 5 parallel Explore agents for comprehensive code review. Each agent specializes in a specific review dimension. For detailed agent prompts and patterns, see [references/agent-prompts.md](references/agent-prompts.md).

**Agent assignments:**
- **Agent 1**: Correctness & Logic — bugs, race conditions, off-by-one errors, null safety, type mismatches
- **Agent 2**: Performance — algorithmic complexity, unnecessary allocations, N+1 queries, missing caching, memory leaks
- **Agent 3**: Code Style & Patterns — naming, structure, DRY violations, SOLID adherence, framework idioms
- **Agent 4**: Test Coverage Gaps — untested code paths, missing edge case tests, weak assertions, test quality
- **Agent 5**: Error Handling & Edge Cases — unhandled exceptions, missing validation, boundary conditions, graceful degradation

Each agent must:
1. Grep for issue patterns across files in scope
2. Read each match to verify context and confirm it is a genuine issue
3. Extract exact code snippets (5-10 lines) with file:line references
4. Explain why the code is problematic
5. Classify severity (Critical/Major/Minor/Nit)
6. Provide a concrete fix suggestion with code example

**Severity Definitions:**
- **Critical**: Bugs that cause data loss, crashes, security holes, or incorrect business logic
- **Major**: Significant issues affecting reliability, performance degradation, or maintainability risks
- **Minor**: Improvements for readability, consistency, or minor inefficiencies
- **Nit**: Style preferences, cosmetic suggestions, optional improvements

### Phase 4: Consolidate & Analyze Findings

After all agents complete:

1. **Collect all findings** from the 5 parallel agents
2. **Deduplicate** - Remove duplicate findings across agents (e.g., the same function flagged by both correctness and error handling agents)
3. **Prioritize by severity**:
 - **Critical**: Data corruption, crashes, security implications, broken business logic
 - **Major**: Performance bottlenecks, reliability issues, test gaps for critical paths
 - **Minor**: Code readability, minor inefficiencies, style inconsistencies
 - **Nit**: Naming preferences, optional simplifications, cosmetic changes
4. **Categorize by dimension**: Group findings under the 5 specialist categories
5. **Cross-reference**: Note findings that span multiple dimensions (e.g., a missing null check is both a correctness and error handling issue)
6. **Statistics**: Count total findings by severity, by dimension, files reviewed vs. files with issues

### Phase 5: Generate Review Report

Generate a comprehensive markdown report following the template in [references/report-template.md](references/report-template.md).

**Report sections:**
1. Executive summary with overall code quality assessment
2. Severity breakdown with counts
3. Findings organized by dimension, each with file:line, code snippet, explanation, and fix suggestion
4. Prioritized action items (Critical first, then Major)
5. Positive observations - highlight well-written code, good patterns, thorough tests

### Phase 6: Iterative Re-Review (Diff-Only Re-Scan)

**This is the key differentiator.** After the initial review, if the user makes fixes and requests a re-review:

1. **Detect changes since last review**:
 ```bash
 # Get files changed since the review started
 git diff --name-only HEAD@{<timestamp>}..HEAD
 # Or if on a branch with new commits
 git diff --name-only <last_reviewed_commit>..HEAD
 2. **Scope re-review to changed files only** - Do NOT re-scan the entire codebase
3. **Re-run only relevant agents** - If fixes were for performance issues, re-run Agent 2 (Performance) on the changed files
4. **Verify fixes** - Check that previously reported Critical/Major issues are actually resolved
5. **Report delta** - Show what was fixed, what remains, and any new issues introduced by the fixes

**Re-review output format:**
```markdown
## Re-Review Report (Diff-Only)

**Files re-scanned**: [N files changed since last review]
**Previous findings**: [N total]
**Resolved**: [N findings fixed]
**Remaining**: [N findings still present]
**New issues**: [N new findings from fixes]

### Resolved Findings
- ~~[Finding title]~~ — Fixed in `file.py:45`

### Remaining Findings
- [Finding title] — Still present in `file.py:30`

### New Findings
- [New finding from fix] — Introduced in `file.py:50`
To trigger a re-review, the user runs the skill again after making fixes. The skill detects that a review was recently performed (by checking git log for recent review-related commits or by the user explicitly stating "re-review") and automatically enters diff-only mode.

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

# Re-review after fixes (run again on same PR)
review-code 123
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

## What This Skill Does

- Identifies bugs, logic errors, and correctness issues
- Analyzes performance bottlenecks and optimization opportunities
- Reviews code style, patterns, and architectural adherence
- Discovers test coverage gaps and weak test assertions
- Evaluates error handling, input validation, and edge cases
- Generates a comprehensive markdown report with actionable findings
- Supports iterative diff-only re-review after fixes

## What This Skill Does NOT Do

- Does not modify any code
- Does not automatically fix issues
- Does not commit changes
- Does not run tests or benchmarks
- Does not perform security-specific analysis (use review-security for that)
- Does not guarantee detection of all issues

## Limitations

- **Static analysis only**: Cannot detect runtime-only issues
- **Pattern-based**: May miss deeply context-specific problems
- **No dynamic testing**: Cannot measure actual performance impact
- **False positives possible**: Some findings may be intentional design choices
- **Requires manual review**: Expert judgment recommended for Critical findings
- **Language support**: Best coverage for Python, JavaScript/TypeScript, Go, Java; basic coverage for other languages
