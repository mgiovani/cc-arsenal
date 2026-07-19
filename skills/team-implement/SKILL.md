---
name: team-implement
description: "Spec-driven team orchestration for large, multi-component features or new epics: writes a full spec/design/review artifact trail under .specs/, gates code changes behind an explicit user approval, then scales a team from 3 (lite) to roughly 9 (full) agents based on complexity. Use for sizable features spanning frontend+backend+DB, unfamiliar domains, or anything you want a reviewable spec for before code is touched. Not for small/single-component changes (use implement-feature — no spec overhead) and not for reviewing already-written code (use team-review)."
disable-model-invocation: true
argument-hint: "<description|PROJ-123|#issue|!pr|file|url>"
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Task, SendMessage, TaskStop, TaskCreate, TaskUpdate, TaskList, TaskGet, WebFetch, AskUserQuestion
context: fork
agent: general-purpose
---

# Team Implement

Adaptive spec-driven development team that scales from 3 agents (lite) to ~9 (full) based on project complexity. All planning completes before any code changes, with explicit user approval between planning and implementation.

## Prerequisites & fallback chain — read this first

**Full mode** needs multi-agent teams. In Claude Code that requires:
```
CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```
With the flag set, full mode spawns named teammates via the `Task` tool with a `team_name` (the team itself is created implicitly by the first such call — there's no separate "create team" step), coordinates via `SendMessage`, and stops a teammate with `TaskStop`. The exact tool signatures depend on the environment you're running in — treat any call shown below as illustrative and use whatever the local Task/SendMessage/TaskStop equivalents actually are. Do not invent a `Teammate` tool or similar if nothing like it exists here.

**No flag, or a `Task ... team_name` call fails?** Fall back to **Lite mode**: identical phase structure, but roles run as sequential `Task` subagents (no `team_name`, no cross-agent messaging) instead of a coordinated team.

**No `Task`/subagent tool at all?** Fall back further still: run every phase's steps yourself, inline, sequentially. The phase → gate → phase structure below *is* the workflow — teams and subagents are just two ways to parallelize it.

**Delegate mode** (Claude Code, full mode): `Shift+Tab` restricts the lead to coordination-only tools. Without it, wait for teammates to finish before touching their files yourself.

## Input

$ARGUMENTS

## Known Limitations

- No session resumption — an interrupted session loses spawned teammates (full mode)
- One team per session; teammates cannot spawn their own sub-teams
- Teammates sometimes forget to mark tasks complete — poll `TaskList` rather than trusting silence
- Teammates load project CLAUDE.md/AGENTS.md automatically (a benefit, not a limitation)

## Workflow Overview

```
MACRO PHASE A: PLANNING (no code changes)
  Phase 0: Input Ingestion & Discovery
  Phase 1: Clarifying Questions
  Phase 2: Specification
  Phase 3: Architecture & Design
  Phase 4: Adversarial Review
  Phase 5: Task Decomposition
  ══════════════ USER APPROVAL GATE ══════════════
MACRO PHASE B: IMPLEMENTATION (code changes)
  Phase 6: Implementation
  Phase 7: Quality Assurance
  Phase 8: Documentation & Delivery
  Phase 9: Teardown
```

---

## Phase 0: Input Ingestion & Discovery

### Step 0.1: Detect Input Source

Parse `$ARGUMENTS`. Detection order (first match wins) — full patterns and ingestion commands in [references/spec-workflow.md](references/spec-workflow.md) Section 1:

| Pattern | Source | Ingestion |
|---------|--------|-----------|
| `PROJ-123` | Jira | `jira issue view PROJ-123 --json` |
| `#42` / `owner/repo#42` | GitHub issue | `gh issue view 42 --json title,body,labels,comments` |
| `!123` / PR URL | GitHub PR | `gh pr view 123 --json title,body,files,comments,labels` |
| Existing file path | File | Read it |
| Existing directory path | Directory | Read README.md, CLAUDE.md/AGENTS.md, key files |
| `http(s)://` | URL | WebFetch |
| Everything else | Plain text | Use directly as requirements |

### Step 0.2: Project Discovery

Spawn an Explore/haiku agent (with no subagent tool, do this yourself):
```
Task tool (Explore, haiku):
"Discover the project's stack and workflow: read CLAUDE.md/AGENTS.md and README.md,
find task-runner commands (test/lint/build/dev), map major components, note
frameworks/DB/auth patterns and existing conventions. Return a structured summary."
```

### Step 0.3: Assess Complexity

Score against the signals below (full algorithm in [references/spec-workflow.md](references/spec-workflow.md) Section 2):

| Signal | +2 | +1 | 0 |
|--------|----|----|---|
| Components affected | 3+ (frontend+backend+DB+infra) | 2 | Single |
| Security sensitivity | Auth, payments, PII | Permission checks | None |
| Performance requirements | Real-time, SLAs | Caching/optimization | Standard CRUD |
| External integrations | 2+ APIs/services | 1 | Self-contained |
| Estimated file changes | 15+ | 10–14 | <10 |
| Domain familiarity | Unfamiliar tech | Partially familiar | Well-understood |

- **Score 0–1**: lite mode, automatic — for a <10-file single-component change, suggest `implement-feature` instead (no spec overhead needed)
- **Score 2–3**: ask the user, default recommendation lite
- **Score 4+**: full mode, automatic

### Steps 0.4–0.6: Namespace, Initial Artifacts, Git Handling

1. Generate `.specs/<short-id>/` (`<slugified-title>-<YYYYMMDD>`; algorithm in [references/spec-workflow.md](references/spec-workflow.md) Section 3)
2. Write `input-digest.md` and a session `README.md` dashboard from [references/spec-templates.md](references/spec-templates.md)
3. Update `.specs/README.md` (global index — create it if this is the first session)
4. If `.specs/` isn't already tracked or gitignored, ask via `AskUserQuestion` whether to commit it or ignore it — first time only

### Step 0.7: Propose Team Composition

```
AskUserQuestion:
  question: "Complexity assessment complete ([score]/10). Proceed with this team?"
  options:
    - "[MODE] mode with [ROLES] (Recommended)"
    - "Switch to [OTHER_MODE] mode"
    - "Customize team composition"
```

Full-mode team creation is implicit — the first `Task` call in Phase 2 that uses `team_name: "team-<short-id>"` creates the team. There is no separate spawn step.

---

## Phase 1: Clarifying Questions

Scan the input digest for ambiguity — vague requirements, missing acceptance criteria, unclear scope, technology decisions, conflicting asks. Resolve with `AskUserQuestion`, multiple rounds if needed. Skip or shorten this phase for a well-defined source (e.g. a detailed Jira ticket with acceptance criteria already attached).

---

## Phase 2: Specification

### Full Mode

Spawn **Product Lead** (prompt in [references/agent-catalog.md](references/agent-catalog.md)):
```
Task tool (team_name: "team-<short-id>", name: "product-lead"):
  subagent_type: general-purpose, model: sonnet
  prompt: [Product Lead prompt, substituting SPEC_ID and project context]
```
Writes `.specs/<short-id>/proposal/{brief,requirements,acceptance-criteria}.md`.

**Gate: Spec Review** — orchestrator checks coherence, asks the user about remaining gaps.

### Lite Mode

Spawn **Product Analyst** via `Task` (no team) — see agent-catalog.md. Writes combined `brief.md` + task breakdown.

---

## Phase 3: Architecture & Design

### Full Mode

Spawn **Architect** (opus — complex system design benefits from the stronger model):
```
Task tool (team_name: "team-<short-id>", name: "architect"):
  subagent_type: general-purpose, model: opus
  prompt: [Architect prompt from agent-catalog.md]
```
Writes `design/architecture.md`, `design/api-contracts.md`, `design/data-model.md`, `design/diagrams/system-overview.md`, and lightweight ADRs under `decisions/`. Defer to the `cc-arsenal:docs-adr` skill for ADR format and conventions (via the `Skill` tool where available, otherwise follow its documented ADR templates) rather than reinventing one here.

### Lite Mode

Combined **Architect/Developer** subagent writes `design.md`.

---

## Phase 4: Adversarial Review

### Full Mode

Spawn **Adversary Reviewer**. Reviews all spec + design artifacts, writes `review/adversary-report.md`, rates findings **BLOCKER | WARNING | SUGGESTION**.

If BLOCKERs: route findings to Architect (see [references/communication-patterns.md](references/communication-patterns.md) Section 3) → Architect revises → Adversary re-reviews. **Max 2 revision cycles** — proceed even if warnings remain after that, to avoid an infinite loop.

### Lite Mode

**QA/Reviewer** subagent challenges the design, writes `review.md`. Same BLOCKER routing and 2-cycle cap.

---

## Phase 5: Task Decomposition

### Full Mode

**Product Lead** (still active) writes `tasks/task-breakdown.md` and a Mermaid `tasks/task-graph.md`. Orchestrator creates `TaskCreate` entries with dependencies. Target 5–6 tasks per teammate — smaller wastes coordination overhead, larger risks wasted effort between check-ins.

For decomposition technique beyond what's here (estimation, dependency-graph patterns), defer to the `cc-arsenal:project-planner` skill (via the `Skill` tool where available, otherwise apply its documented decomposition steps) instead of reinventing it.

### Lite Mode

Orchestrator writes `tasks.md` with breakdown + Mermaid graph, initializes tasks via `TaskCreate`.

---

## USER APPROVAL GATE

```
AskUserQuestion:
  question: "Planning complete for [TITLE]. Specs at .specs/<short-id>/. [N] requirements, [M] tasks, [K] parallelizable. Ready to proceed?"
  options:
    - "Approve and begin implementation"
    - "Request changes (I'll describe what to modify)"
    - "Save spec only — do not implement"
    - "Cancel"
```

No code changes happen before this gate passes. "Save spec only" skips straight to Phase 9 teardown. "Request changes" jumps back to the relevant phase.

---

## Phase 6: Implementation

**Only after approval.**

### Full Mode

Spawn one **Implementation Engineer** per affected component, in parallel (e.g. `frontend-engineer`, `backend-engineer` — same prompt template, scoped by component; see agent-catalog.md):
```
Task tool (team_name: "team-<short-id>", name: "frontend-engineer"):
  subagent_type: general-purpose, model: sonnet
  prompt: [Implementation Engineer prompt, component: frontend]
```
Each engineer claims tasks from the board (`TaskList` → `TaskUpdate`), reads spec files (API contracts, data model), implements per the architecture, writes tests, marks tasks completed, reports to the orchestrator.

**File scope enforcement**: each engineer's handoff message states its file scope explicitly (see [references/communication-patterns.md](references/communication-patterns.md) Section 5) — this is what prevents two engineers editing the same files. Orchestrator commits incrementally after each engineer completes.

### Lite Mode

**Architect/Developer** subagent implements sequentially per spec, writes tests, runs quality checks.

---

## Phase 7: Quality Assurance

### Full Mode

Spawn **QA Engineer**: validates each acceptance criterion, runs the test suite, checks coverage against a number it actually measured (target >80%, not an assumed figure), writes `review/qa-plan.md`.

Conditional specialists — spawn only if the spec flags the need:
- **Security Engineer** — security-sensitive features (auth, payments, PII)
- **Performance Engineer** — explicit performance/SLA requirements
- **Infrastructure/DevOps Engineer** — deployment or infra changes

**Adversary Reviewer** does a second pass on the implementation.

**Gate: Quality Verification** — all tests pass, no BLOCKER findings. On failure: loop to Phase 6, max 3 retries (see [references/spec-workflow.md](references/spec-workflow.md) Section 6).

### Lite Mode

**QA/Reviewer** subagent runs tests, lint, checks acceptance criteria. On failure: loop to Phase 6.

---

## Phase 8: Documentation & Delivery

Spawn **Tech Writer** (haiku) only if the feature is user-facing or changes an API — otherwise the orchestrator handles the minimal doc updates itself. Updates README.md, CHANGELOG.md, and API docs as applicable, plus `.specs/<short-id>/README.md` with final status.

---

## Phase 9: Teardown

### Full Mode

1. Send a courtesy completion message to any still-active teammate via `SendMessage`
2. Stop each teammate (`TaskStop` on `name@team-<short-id>`, or the local equivalent)
3. Update `.specs/<short-id>/README.md` with final status
4. Present summary to user

### Lite Mode

1. Update `.specs/<short-id>/README.md` with final status
2. Present summary to user

---

## Quality Gates Summary

| Gate | Between | Pass Criteria | On Failure | Max Retries |
|------|---------|---------------|------------|-------------|
| Clarifying Questions | 0→2 | All ambiguities resolved | More questions | Unlimited |
| Spec Review | 2→3 | Requirements complete, criteria clear | Revise specs | 2 |
| Adversarial Review | 3→5 | Zero BLOCKER findings | Architect revises | 2 |
| User Approval | 5→6 | User approves plan | Revise or cancel | Unlimited |
| Quality Verification | 6→8 | Tests pass, no BLOCKER findings | Loop to Phase 6 | 3 |
| Final Delivery | 8→done | Spec artifacts exist, all tasks done | Block completion | 1 |

## Agent Roles Quick Reference

Full prompts and activation criteria: [references/agent-catalog.md](references/agent-catalog.md).

| Role | Model | Phase | Full Mode | Lite Mode |
|------|-------|-------|-----------|-----------|
| Product Lead | sonnet | 2, 5 | Dedicated (merges PM + Scrum Master) | Combined as Product Analyst |
| Architect | opus | 3 | Dedicated | Combined as Architect/Developer |
| Implementation Engineer(s) | sonnet | 6 | One per component, parallel | Combined as Architect/Developer |
| QA Engineer | sonnet | 7 | Dedicated | Combined as QA/Reviewer |
| Adversary Reviewer | sonnet | 4, 7 | Dedicated | Combined as QA/Reviewer |
| Security Engineer | sonnet | 7 | Conditional | Combined as QA/Reviewer |
| Performance Engineer | sonnet | 7 | Conditional | — |
| Infrastructure/DevOps Engineer | sonnet | 7 | Conditional | — |
| Tech Writer | haiku | 8 | Conditional | — |

## Wave-Based Agent Lifecycle (Full Mode)

Agents spawn per phase and shut down when done to bound cost. Details: [references/spec-workflow.md](references/spec-workflow.md) Section 5.

| Wave | Phases | Agents | Shutdown After |
|------|--------|--------|-----------------|
| 1 | 2, 5 | Product Lead | Phase 5 |
| 2 | 3 | Architect | Phase 3 |
| 3 | 4 | Adversary Reviewer | Phase 4 |
| 4 | 6 | Implementation Engineer(s), parallel | Phase 6 |
| 5 | 7 | QA Engineer + conditional Security/Performance/Infra + Adversary (2nd pass) | Phase 7 |
| 6 | 8 | Tech Writer (if spawned) | Phase 8 |

## Communication Patterns (Full Mode)

All inter-agent coordination goes through `SendMessage` (or its local equivalent). Templates: [references/communication-patterns.md](references/communication-patterns.md).

- Default to a direct message; broadcast only for critical team-wide issues
- Always include exact file paths in handoff messages
- State each engineer's file scope explicitly to prevent write conflicts
- Report status in plain text + `TaskUpdate` — never a JSON status blob

## Spec Artifacts

Namespaced under `.specs/<short-id>/`. Templates: [references/spec-templates.md](references/spec-templates.md).

### Full Mode Structure
```
.specs/<short-id>/
├── README.md
├── input-digest.md
├── proposal/{brief,requirements,acceptance-criteria}.md
├── design/{architecture,api-contracts,data-model}.md
│   └── diagrams/system-overview.md
├── review/{adversary-report,security-assessment,qa-plan}.md
├── tasks/{task-breakdown,task-graph}.md
└── decisions/NNNN-*.md
```

### Lite Mode Structure
```
.specs/<short-id>/
├── README.md
├── input-digest.md
├── brief.md
├── design.md
├── review.md
└── tasks.md
```

## Error Recovery

Recovery strategies for unresponsive teammates, repeated test failures, post-implementation BLOCKERs, interrupted sessions, circular task dependencies, and invalid agent output: [references/spec-workflow.md](references/spec-workflow.md) Section 7.

## Usage

```bash
/team-implement Add user authentication with OAuth2 and JWT
/team-implement #42
/team-implement owner/repo#42
/team-implement PROJ-123
/team-implement !456
/team-implement ./docs/requirements.md
/team-implement https://example.com/feature-spec
/team-implement ./src/auth/
```

## References

- [references/agent-catalog.md](references/agent-catalog.md) — role definitions and prompt templates
- [references/spec-workflow.md](references/spec-workflow.md) — input detection, complexity matrix, phase transitions, quality gates, error recovery
- [references/communication-patterns.md](references/communication-patterns.md) — coordination templates
- [references/spec-templates.md](references/spec-templates.md) — representative `.specs/` artifact templates
- `cc-arsenal:docs-adr` — ADR format for `decisions/`
- `cc-arsenal:project-planner` — deeper task-decomposition technique for Phase 5
