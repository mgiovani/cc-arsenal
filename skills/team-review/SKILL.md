---
name: team-review
description: "Multi-agent review team (architecture, security, performance, testing, style, docs/UX, plus an adversary that challenges the other 6) for security-sensitive, architectural, or large PRs (15+ files) where a single-agent pass risks missing cross-cutting issues. Use for auth/payments/PII changes, schema/pattern changes, or compliance sign-off. For a standard PR or a quick pre-merge check, use /review-code instead — it's faster and cheaper."
disable-model-invocation: true
argument-hint: "<pr_number|commit_sha|--all> [--focus area] [--lite]"
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Task, Teammate, SendMessage, TaskCreate, TaskUpdate, TaskList, TaskGet, WebFetch, AskUserQuestion
context: fork
agent: general-purpose
---

# Team Review

Multi-agent team orchestration for comprehensive PR code review. Spawns 6 specialized reviewer agents plus 1 adversary reviewer as a coordinated team. Designed for security-sensitive, architectural, or high-impact code changes where a single-agent review is insufficient.

For simpler reviews, use `/review-code` (single-agent with parallel Explore subagents).

## Prerequisites

**Full mode** requires the experimental agent teams flag. Add to your environment or `settings.json`:

```
CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

**Lite mode** (`--lite` flag or automatic fallback) works without this flag — uses Task subagents instead of the Teammate API. Fewer agents, lower cost, still comprehensive.

**No `Task`/subagent tools at all?** Drop one level further: work through each reviewer's checklist yourself, one after another, instead of spawning subagents. The 6 review dimensions (plus adversary pass) are the methodology; Teammate/Task parallelism is just how Claude Code speeds it up.

**Delegate mode** (recommended for full mode): Press `Shift+Tab` to enable delegate mode, which restricts the lead to coordination-only tools and prevents it from reviewing code itself.

## Input

$ARGUMENTS

## Notes

- `/resume` does not restore teammates — an interrupted full-mode session loses the team; re-run from scratch.
- Only one team-review can run per session.
- Analysis only — it finds issues but never edits code; use `/implement-feature` or `/fix-bug` for the actual fixes.
- Teammates sometimes forget to mark tasks complete, so the orchestrator should poll task status rather than assume completion.
- Every reviewer must ground findings in code it actually read (file:line, real snippet) and flag uncertain cases as "needs manual verification" instead of asserting — a false positive here costs more than a missed finding, since it erodes trust in the whole report.
- Abort early if the requested scope (PR/commit) doesn't exist or isn't readable — don't let reviewers spin on a bad input. If reviewer tasks stall past ~10 min, or the adversary doesn't report back, proceed to consolidation with what's in hand rather than blocking the whole review.

## Workflow Overview

```
Phase 0: Scope Detection & Input Ingestion
Phase 1: Project Discovery
Phase 2: Team Composition & Spawn
Phase 3: Parallel Specialist Review (6 reviewers + 1 adversary)
Phase 4: Consolidation & Cross-Reference
Phase 5: Report Generation
Phase 6: Teardown

Optional: Iterative re-review after fixes
```

---

## Phase 0: Scope Detection & Input Ingestion

Parse `$ARGUMENTS` to determine what to review:

| Pattern | Source Type | Ingestion |
|---------|-----------|-----------|
| `123` or `#123` | PR number | `gh pr view 123 --json files,title,body,labels,comments` + `gh pr diff 123` |
| `abc123` | Commit SHA | `git show abc123` + `git diff-tree --no-commit-id --name-only -r abc123` |
| `--all` or no args | Entire codebase | `git ls-files` (respects .gitignore) |
| `--lite` | Force lite mode | Use Task subagents instead of Teammate API |
| `--focus <area>` | Focus area | Spawn only relevant reviewers |

**Retrieve full diff context for PR/commit reviews.** Reviewers must focus findings on changed lines while using surrounding code for context.

---

## Phase 1: Project Discovery

Spawn an Explore/haiku agent to understand the project:

```
Task tool (Explore, haiku):
"Discover the project's technology stack, coding conventions, and quality standards:
  1. Read CLAUDE.md and README.md for project context and conventions
  2. Check package.json, pyproject.toml, pom.xml, go.mod for languages/frameworks
  3. Identify linting/formatting configs: .eslintrc, .prettierrc, ruff.toml, .editorconfig
  4. Identify test frameworks and patterns
  5. Check for CI/CD quality gates in .github/workflows
  6. Note architectural patterns: MVC, Clean Architecture, DDD, etc.
  7. Identify security tools: SAST, dependency scanning, pre-commit hooks
  Return: Technology stack, conventions, quality standards, and security tooling summary."
```

---

## Phase 2: Team Composition & Spawn

### Assess Complexity

Evaluate complexity to determine full vs. lite mode:

| Signal | Full Mode (+2) | Medium (+1) | Lite Mode (0) |
|--------|----------------|-------------|----------------|
| Files changed | 15+ files | 5-14 files | <5 files |
| Security sensitivity | Auth, payments, PII | Permission checks | No sensitive data |
| Architectural impact | New patterns, schema changes | Modifying existing patterns | Localized changes |
| Cross-cutting concerns | Multiple modules/services | 2 components | Single component |

**Thresholds:**
- Score 0-2: Use **lite mode** automatically
- Score 3-4: Ask user (recommend lite for cost efficiency)
- Score 5+: Use **full mode** automatically

**Override**: `--lite` flag forces lite mode regardless of score.

### Full Mode Team Spawn

```
Teammate({ operation: "spawnTeam", team_name: "review-<pr_or_scope>" })
```

Spawn 7 reviewer agents. For complete prompt templates, see [references/agent-catalog.md](references/agent-catalog.md).

| Role | Agent Name | Model | Focus |
|------|-----------|-------|-------|
| Architecture Reviewer | `arch-reviewer` | opus | System design, API contracts, data modeling, dependency graph |
| Security Reviewer | `security-reviewer` | sonnet | OWASP Top 10, auth/authz, input validation, secrets |
| Performance Reviewer | `perf-reviewer` | sonnet | Algorithmic complexity, queries, caching, memory |
| Testing Reviewer | `test-reviewer` | sonnet | Coverage gaps, assertion quality, test architecture |
| Style & Patterns Reviewer | `style-reviewer` | sonnet | Naming, DRY/SOLID, framework idioms, readability |
| Docs & UX Reviewer | `docs-reviewer` | haiku | API ergonomics, error messages, documentation, changelog |
| Adversary Reviewer | `adversary-reviewer` | sonnet | Challenges assumptions, finds edge cases, stress-tests design |

### Lite Mode (Task Subagents)

Spawn 4 Task subagents (combined roles) instead of full team:

| Combined Role | Covers | Model |
|---------------|--------|-------|
| Architecture & Security | arch-reviewer + security-reviewer | sonnet |
| Performance & Style | perf-reviewer + style-reviewer | sonnet |
| Testing & Error Handling | test-reviewer + edge cases | sonnet |
| Adversary | adversary-reviewer + docs-reviewer | sonnet |

### Focus Mode

When `--focus` is specified, spawn only relevant reviewers:

| Focus | Agents Spawned |
|-------|---------------|
| `architecture` | arch-reviewer, adversary-reviewer |
| `security` | security-reviewer, adversary-reviewer |
| `performance` | perf-reviewer, adversary-reviewer |
| `testing` | test-reviewer, adversary-reviewer |
| `style` | style-reviewer, docs-reviewer |

---

## Phase 3: Parallel Specialist Review

All reviewers work simultaneously on the same file set. Each reviewer follows its specialized prompt from [references/agent-catalog.md](references/agent-catalog.md).

### Task Assignment

Create tasks for each reviewer via TaskCreate, then assign:

```
TaskCreate:
  subject: "Architecture review of PR #[N]"
  description: "Review changed files for architectural issues, API design, data modeling..."
  activeForm: "Reviewing architecture"

TaskCreate:
  subject: "Security review of PR #[N]"
  description: "Review changed files for OWASP vulnerabilities, auth issues..."
  activeForm: "Reviewing security"

# ... repeat for each reviewer

# Assign to agents
TaskUpdate: { taskId: "arch-task", owner: "arch-reviewer" }
TaskUpdate: { taskId: "security-task", owner: "security-reviewer" }
# ... etc.
```

### Reviewer Instructions (Common Preamble)

Each reviewer receives:
1. The list of files in scope
2. The full diff (for PR/commit reviews)
3. Project discovery results from Phase 1
4. Their specialized review prompt from [references/agent-catalog.md](references/agent-catalog.md)

Each reviewer must:
1. Read each file in scope
2. For PRs: focus analysis on changed lines, use surrounding code for context
3. Grep for dimension-specific patterns
4. Verify each finding by reading the code in context
5. Classify severity: Critical / Major / Minor / Nit
6. Write findings to a structured format with file:line references, code snippets, explanations, and fix suggestions
7. Mark their review task as completed via TaskUpdate
8. Send findings summary to the orchestrator via SendMessage

### Adversary Reviewer (Special Role)

The adversary reviewer operates differently:
1. **Waits** for initial findings from at least 3 other reviewers (orchestrator forwards summaries)
2. **Challenges** the findings: Are any false positives? Are severity ratings accurate?
3. **Finds gaps**: What did the other reviewers miss? What assumptions are untested?
4. **Stress-tests**: What happens at 10x scale? What if inputs are malicious? What if dependencies fail?
5. **Reports**: Additional findings + challenges to existing findings

---

## Phase 4: Consolidation & Cross-Reference

After all reviewers complete, the orchestrator:

1. **Collects all findings** from 7 reviewers (6 specialists + 1 adversary)
2. **Deduplicates** - Merge findings flagged by multiple reviewers (e.g., same function flagged by security AND performance)
3. **Incorporates adversary feedback** - Adjust severity ratings, remove confirmed false positives, add adversary's unique findings
4. **Cross-references** - Note findings that span multiple dimensions
5. **Prioritizes by severity**:
   - **Critical**: Data loss, security holes, crashes, incorrect business logic
   - **Major**: Performance degradation, reliability risks, significant test gaps
   - **Minor**: Readability, consistency, minor improvements
   - **Nit**: Style preferences, optional enhancements
6. **Computes statistics**: Total findings, by severity, by reviewer, files with issues

---

## Phase 5: Report Generation

Generate a comprehensive review report following the template in [references/report-template.md](references/report-template.md).

**Report sections:**
1. Executive summary with overall assessment and team consensus
2. Severity breakdown with counts
3. Findings by reviewer dimension, each with file:line, code snippet, explanation, and fix suggestion
4. Adversary findings and challenges
5. Cross-cutting concerns (findings spanning multiple dimensions)
6. Positive observations - highlight well-written code and good patterns
7. Prioritized action items

---

## Phase 6: Teardown

### Full Mode

1. Send `shutdown_request` to all reviewer agents
2. Wait for `shutdown_response` from each
3. Run `Teammate({ operation: "cleanup" })`
4. Present final report to user

### Lite Mode

1. Collect all subagent results
2. Present final report to user

---

## Iterative Re-Review

After the initial review, if fixes are made and a re-review is requested:

1. **Detect changes**: `git diff --name-only <last_reviewed_commit>..HEAD`
2. **Scope to changed files only** - Do NOT re-review the entire codebase
3. **Re-spawn only relevant reviewers** - If fixes addressed security findings, re-spawn security-reviewer and adversary-reviewer only
4. **Verify fixes** - Check that previously reported Critical/Major issues are resolved
5. **Report delta** - Show resolved, remaining, and new findings

---

## Usage

```bash
# Full team review of a PR (auto-detects complexity)
/team-review 123

# Force lite mode for cost efficiency
/team-review 123 --lite

# Focus on specific dimension
/team-review 123 --focus security

# Review a specific commit
/team-review abc123def

# Review entire codebase
/team-review --all

# Re-review after fixes
/team-review 123
```

## When to Use team-review vs review-code

| Scenario | Use |
|----------|-----|
| Standard PR review | `/review-code` (faster, cheaper) |
| Security-sensitive changes (auth, payments, PII) | `/team-review` |
| Architectural changes (new patterns, schema) | `/team-review` |
| Large PRs (15+ files) | `/team-review` |
| Quick check before merging | `/review-code` |
| Compliance or audit requirements | `/team-review` |
| Re-review after fixes | Either (both support diff-only) |

## Additional Resources

- [references/agent-catalog.md](references/agent-catalog.md) - Complete prompt templates for all 7 reviewer agents
- [references/report-template.md](references/report-template.md) - Review report template with all sections

## What This Skill Does

- Orchestrates 7 specialized reviewer agents working in parallel
- Provides deep, multi-dimensional code review with expert-level analysis
- Includes adversary review to challenge assumptions and find blind spots
- Generates comprehensive report with cross-referenced findings
- Supports iterative diff-only re-review after fixes

## What This Skill Does NOT Do

- Does not modify any code
- Does not automatically fix issues
- Does not commit changes
- Does not run tests or benchmarks
- Does not replace human review for compliance sign-off
