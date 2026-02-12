---
name: team-implement
description: "Spec-driven team orchestration: adaptive development team that scales from 3 to 11 agents based on project complexity. Accepts plain text, Jira tickets, GitHub issues, PRs, files, directories, or URLs as input. Plans thoroughly first, gets user approval, then implements with parallel agents."
disable-model-invocation: true
argument-hint: "<description|PROJ-123|#issue|!pr|file|url>"
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Task, Teammate, SendMessage, TaskCreate, TaskUpdate, TaskList, TaskGet, WebFetch, AskUserQuestion
context: fork
agent: general-purpose
---

# Team Implement

Adaptive spec-driven development team that scales from 3 agents (lite) to 11 agents (full) based on project complexity. All planning completes before any code changes, with explicit user approval between planning and implementation.

## Prerequisites

**Full mode** requires the experimental agent teams flag. Add to your environment or `settings.json`:

```
CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

**Lite mode** works without this flag (uses Task subagents instead of Teammate API).

**Delegate mode** (recommended for full mode): Press `Shift+Tab` to enable delegate mode, which restricts the lead to coordination-only tools and prevents it from implementing tasks itself. Without delegate mode, always wait for teammates to complete their tasks before proceeding — do not implement tasks yourself.

## Input

$ARGUMENTS

## Known Limitations

- **No session resumption**: `/resume` does not restore teammates. If a session is interrupted mid-team, teammates are lost
- **One team per session**: Cannot run multiple team-implement invocations simultaneously
- **No nested teams**: Teammates cannot spawn their own teams
- **Task status can lag**: Teammates sometimes forget to mark tasks complete; orchestrator should monitor
- **Teammates load CLAUDE.md**: Project-specific guidance applies automatically to all agents (this is a benefit)

## Workflow Overview

```
MACRO PHASE A: PLANNING (no code changes)
  Phase 0: Input Ingestion & Discovery
  Phase 1: Clarifying Questions
  Phase 2: Specification
  Phase 3: Architecture & Design
  Phase 4: Adversarial Review
  Phase 5: Task Decomposition

  ══════════════════════════════════════
  USER APPROVAL GATE
  ══════════════════════════════════════

MACRO PHASE B: IMPLEMENTATION (code changes)
  Phase 6: Implementation
  Phase 7: Quality Assurance
  Phase 8: Documentation & Delivery
  Phase 9: Teardown
```

---

## Phase 0: Input Ingestion & Discovery

### Step 0.1: Detect Input Source

Parse `$ARGUMENTS` to determine the input type. For detection patterns and ingestion commands, see [references/spec-workflow.md](references/spec-workflow.md) Section 1.

**Detection order** (first match wins):

| Pattern | Source Type | Ingestion |
|---------|-----------|-----------|
| `PROJ-123` | Jira ticket | `jira issue view PROJ-123 --json` |
| `#42` or `owner/repo#42` | GitHub issue | `gh issue view 42 --json title,body,labels,comments` |
| `!123` or PR URL | GitHub PR | `gh pr view 123 --json title,body,files,comments,labels` |
| Existing file path | File | Read file content |
| Existing directory path | Directory | Read README.md, CLAUDE.md, key files |
| `http://` or `https://` | URL | WebFetch to extract content |
| Everything else | Plain text | Use directly as requirements |

### Step 0.2: Project Discovery

Spawn an Explore/haiku agent to understand the project:

```
Task tool (Explore, haiku):
"Discover the project's technology stack and development workflow:
  1. Read CLAUDE.md and README.md for project context
  2. Check for task runners: Makefile, package.json, pyproject.toml
  3. Identify test, lint, build, dev server commands
  4. Map major components and modules
  5. Note frameworks, databases, authentication patterns
  6. Find existing patterns and conventions
  Return: structured summary of project architecture and available commands."
```

### Step 0.3: Assess Complexity

Evaluate complexity signals to determine team mode. See [references/spec-workflow.md](references/spec-workflow.md) Section 2 for the full scoring matrix.

| Signal | +2 (Full) | +1 (Medium) | 0 (Lite) |
|--------|-----------|-------------|----------|
| Components affected | 3+ (frontend + backend + DB + infra) | 2 components | Single component |
| Security sensitivity | Auth, payments, PII | Permission checks | No sensitive data |
| Performance requirements | Real-time, SLAs | Caching, optimization | Standard CRUD |
| External integrations | 2+ APIs/services | 1 external API | Self-contained |
| Estimated file changes | 15+ files | 10-14 files | <10 files |
| Domain familiarity | Unfamiliar tech | Partially familiar | Well-understood |

**Thresholds:**
- Score 0-1: Use **lite mode** automatically
- Score 2-3: Ask user (recommend lite)
- Score 4+: Use **full mode** automatically

### Step 0.4: Generate Spec Namespace

Create `.specs/<short-id>/` directory. Format: `<slugified-title>-<YYYYMMDD>` (e.g., `auth-oauth2-20260205`). See [references/spec-workflow.md](references/spec-workflow.md) Section 3 for the generation algorithm.

### Step 0.5: Create Initial Artifacts

1. Create `.specs/<short-id>/` directory
2. Write `.specs/<short-id>/input-digest.md` using template from [references/spec-templates.md](references/spec-templates.md)
3. Write `.specs/<short-id>/README.md` (session dashboard)
4. Update `.specs/README.md` (global index) — create if first spec session

### Step 0.6: Git Handling (first time only)

If `.specs/` does not already exist in git or `.gitignore`, ask the user:

```
AskUserQuestion:
  question: "How should .specs/ be handled in git?"
  options:
    - "Commit to git (specs are part of the project)"
    - "Add to .gitignore (specs are local-only)"
```

### Step 0.7: Propose Team Composition

Present the mode decision and team composition to the user for confirmation:

```
AskUserQuestion:
  question: "Complexity assessment complete. Proceed with this team?"
  options:
    - "[MODE] mode with [ROLES] (Recommended)"
    - "Switch to [OTHER_MODE] mode"
    - "Customize team composition"
```

**Full mode team spawn:**
```
Teammate({ operation: "spawnTeam", team_name: "team-<short-id>" })
```

---

## Phase 1: Clarifying Questions

**CRITICAL**: Before any planning begins, analyze the input digest for ambiguities.

Look for:
- Vague requirements ("should support authentication" — which kind?)
- Missing acceptance criteria
- Unclear scope boundaries (what's in/out)
- Technology decisions needing user input
- Conflicting requirements

Use `AskUserQuestion` to resolve ambiguities. Multiple rounds are fine. Only proceed when requirements are clear enough to specify.

If the input is already well-defined (e.g., detailed Jira ticket with acceptance criteria), this phase can be brief or skipped.

---

## Phase 2: Specification

### Full Mode

Spawn **Product Manager** and **Scrum Master** (Wave 1). See [references/agent-catalog.md](references/agent-catalog.md) for complete prompt templates.

```
Task tool (team_name: "team-<short-id>", name: "product-manager"):
  subagent_type: general-purpose
  model: sonnet
  prompt: [Product Manager prompt from agent-catalog.md, substituting SPEC_ID and project context]
```

Product Manager writes:
- `.specs/<short-id>/proposal/brief.md`
- `.specs/<short-id>/proposal/requirements.md`
- `.specs/<short-id>/proposal/acceptance-criteria.md`

Scrum Master reviews for completeness.

**Gate: Spec Review** — Orchestrator validates coherence, asks user about remaining gaps.

### Lite Mode

Spawn **Product Analyst** subagent (via Task, not Teammate). See [references/agent-catalog.md](references/agent-catalog.md) Combined Agent 12.

Product Analyst writes:
- `.specs/<short-id>/brief.md`
- `.specs/<short-id>/design.md` (combined)

---

## Phase 3: Architecture & Design

### Full Mode

Spawn **Architect** (Wave 2, **opus** model). See [references/agent-catalog.md](references/agent-catalog.md) Agent 3.

```
Task tool (team_name: "team-<short-id>", name: "architect"):
  subagent_type: general-purpose
  model: sonnet
  prompt: [Architect prompt from agent-catalog.md]
```

Architect writes:
- `.specs/<short-id>/design/architecture.md`
- `.specs/<short-id>/design/api-contracts.md`
- `.specs/<short-id>/design/data-model.md`
- `.specs/<short-id>/design/diagrams/system-overview.md`
- `.specs/<short-id>/decisions/NNNN-*.md` (lightweight ADRs)

### Lite Mode

**Architect/Developer** subagent writes `.specs/<short-id>/design.md` (combined). See [references/agent-catalog.md](references/agent-catalog.md) Combined Agent 13.

---

## Phase 4: Adversarial Review

### Full Mode

Spawn **Adversary Reviewer** (Wave 3). See [references/agent-catalog.md](references/agent-catalog.md) Agent 11.

Adversary reviews ALL spec + design artifacts and writes:
- `.specs/<short-id>/review/adversary-report.md`

Findings rated as: **BLOCKER** | **WARNING** | **SUGGESTION**

If BLOCKERs found:
1. Route findings back to Architect via orchestrator (see [references/communication-patterns.md](references/communication-patterns.md) Section 3)
2. Architect revises design
3. Adversary re-reviews
4. **Maximum 2 revision cycles** — after that, approve even if warnings remain

### Lite Mode

**QA/Reviewer** subagent challenges design and writes `.specs/<short-id>/review.md`. If BLOCKERs: orchestrator feeds back, spawns revision subagent.

---

## Phase 5: Task Decomposition

### Full Mode

**Scrum Master** (from Wave 1, still active) creates:
- `.specs/<short-id>/tasks/task-breakdown.md`
- `.specs/<short-id>/tasks/task-graph.md` (Mermaid dependency graph)

Orchestrator creates TaskCreate entries with dependencies via the Task Management System. Target 5-6 tasks per teammate — too small wastes coordination overhead, too large risks wasted effort without check-ins.

### Lite Mode

Orchestrator creates `.specs/<short-id>/tasks.md` with breakdown and Mermaid graph, then initializes tasks via TaskCreate.

---

## USER APPROVAL GATE

Present the complete plan to the user via `AskUserQuestion`:

```
AskUserQuestion:
  question: "Planning complete for [TITLE]. Specs at .specs/<short-id>/. [N] requirements, [M] tasks, [K] parallelizable. Ready to proceed?"
  options:
    - "Approve and begin implementation"
    - "Request changes (I'll describe what to modify)"
    - "Save spec only — do not implement"
    - "Cancel"
```

**Option 3 (spec-only)**: Users may want just the planning artifacts without code changes. Skip to Phase 9 (teardown).

**If changes requested**: Jump back to the relevant phase (spec, architecture, or tasks) based on user feedback.

---

## Phase 6: Implementation

**Only after user approval.**

### Full Mode

Spawn implementation agents in parallel (Wave 5). See [references/agent-catalog.md](references/agent-catalog.md) Agents 4-5.

```
# Spawn in parallel
Task tool (team_name: "team-<short-id>", name: "frontend-dev"):
  subagent_type: general-purpose, model: sonnet
  prompt: [Frontend Developer prompt from agent-catalog.md]

Task tool (team_name: "team-<short-id>", name: "backend-dev"):
  subagent_type: general-purpose, model: sonnet
  prompt: [Backend Developer prompt from agent-catalog.md]
```

Each agent:
1. Claims tasks from the shared task board (TaskList → TaskUpdate)
2. Reads spec files for guidance (API contracts, data model)
3. Implements following architecture
4. Writes tests
5. Marks tasks completed (TaskUpdate)
6. Sends completion message to orchestrator

**File scope enforcement**: Frontend and backend agents have strict boundaries. See [references/communication-patterns.md](references/communication-patterns.md) Section 5 for conflict prevention.

Orchestrator commits incrementally after each agent completes.

### Lite Mode

**Architect/Developer** subagent implements sequentially per spec. Writes tests, runs quality checks.

---

## Phase 7: Quality Assurance

### Full Mode

Spawn **QA Engineer** (Wave 6) + optional specialized agents. See [references/agent-catalog.md](references/agent-catalog.md) Agent 6.

QA Engineer:
1. Validates each acceptance criterion
2. Runs test suite
3. Checks code coverage (target: >80%)
4. Writes `.specs/<short-id>/review/qa-plan.md`

Optional agents (spawn based on spec):
- **Security Engineer** (Agent 7): If security-sensitive features
- **Performance Engineer** (Agent 8): If performance requirements
- **Infrastructure/DevOps** (Agent 9): If deployment changes

**Adversary Reviewer** (2nd pass) challenges the implementation.

**Gate: Quality Verification** — All tests pass, no critical findings. If failures: loop to Phase 6 (max 3 retries). See [references/spec-workflow.md](references/spec-workflow.md) Section 6.

### Lite Mode

**QA/Reviewer** subagent validates: run tests, lint, check acceptance criteria. If failures: loop to Phase 6.

---

## Phase 8: Documentation & Delivery

### Full Mode

Spawn **Tech Writer** (Wave 7, haiku model). See [references/agent-catalog.md](references/agent-catalog.md) Agent 10.

Tech Writer updates:
- README.md (if feature-facing)
- CHANGELOG.md
- API documentation (if API changes)
- `.specs/<short-id>/README.md` (final status)

### Lite Mode

Orchestrator handles minimal doc updates.

---

## Phase 9: Teardown

### Full Mode

1. Send `shutdown_request` to all remaining agents (see [references/communication-patterns.md](references/communication-patterns.md) Section 6)
2. Wait for `shutdown_response` from each
3. Run `Teammate({ operation: "cleanup" })`
4. Update `.specs/<short-id>/README.md` with final status
5. Present summary to user

### Lite Mode

1. Update `.specs/<short-id>/README.md` with final status
2. Present summary to user

---

## Quality Gates Summary

| Gate | Between Phases | Pass Criteria | On Failure | Max Retries |
|------|---------------|---------------|------------|-------------|
| Clarifying Questions | 0 → 2 | All ambiguities resolved | More questions | Unlimited |
| Spec Review | 2 → 3 | Requirements complete, criteria clear | Revise specs | 2 |
| Adversarial Review | 3 → 5 | Zero BLOCKER findings | Architect revises | 2 |
| User Approval | 5 → 6 | User approves full plan | Revise or cancel | Unlimited |
| Quality Verification | 6 → 8 | Tests pass, no critical findings | Loop to Phase 6 | 3 |
| Final Delivery | 8 → done | Spec artifacts exist, all tasks done | Block completion | 1 |

## Agent Roles Quick Reference

For complete prompt templates and activation criteria, see [references/agent-catalog.md](references/agent-catalog.md).

| Role | Model | Phase | Full Mode | Lite Mode |
|------|-------|-------|-----------|-----------|
| Product Manager | sonnet | 2 | Dedicated | Combined as Product Analyst |
| Scrum Master | sonnet | 2, 5 | Dedicated | Combined as Product Analyst |
| Architect | sonnet | 3 | Dedicated | Combined as Architect/Developer |
| Frontend Developer | sonnet | 6 | Dedicated | Combined as Architect/Developer |
| Backend Developer | sonnet | 6 | Dedicated | Combined as Architect/Developer |
| QA Engineer | sonnet | 7 | Dedicated | Combined as QA/Reviewer |
| Security Engineer | sonnet | 7 | Conditional | Combined as QA/Reviewer |
| Performance Engineer | sonnet | 7 | Conditional | — |
| Infrastructure/DevOps | sonnet | 7 | Conditional | — |
| Tech Writer | sonnet | 8 | Dedicated | — |
| Adversary Reviewer | sonnet | 4, 7 | Dedicated | Combined as QA/Reviewer |

## Wave-Based Agent Lifecycle (Full Mode)

Agents spawn per phase and shut down when done to minimize cost:

| Wave | Phases | Agents | Shutdown After |
|------|--------|--------|---------------|
| 1 | 1-2, 5 | Product Manager, Scrum Master | Phase 5 |
| 2 | 3 | Architect | Phase 3 |
| 3 | 4 | Adversary Reviewer | Phase 4 |
| 5 | 6 | Frontend Dev, Backend Dev (conditional) | Phase 6 |
| 6 | 7 | QA Engineer + optional Security/Perf/Infra | Phase 7 |
| 7 | 8 | Tech Writer | Phase 8 |

See [references/spec-workflow.md](references/spec-workflow.md) Section 5 for details.

## Communication Patterns (Full Mode)

All inter-agent communication uses SendMessage. See [references/communication-patterns.md](references/communication-patterns.md) for templates covering:

1. Phase handoff messages (orchestrator → next agent)
2. Adversarial review routing (findings → architect → re-review)
3. Blocker escalation (agent → orchestrator → user)
4. Parallel coordination (frontend + backend contract sharing)
5. Shutdown sequences

**Key rules:**
- Default to `type: "message"` (direct). Only use `type: "broadcast"` for critical team-wide issues.
- Always include exact file paths in handoff messages
- Enforce file scope boundaries for implementation agents
- Never send JSON status messages — use plain text + TaskUpdate

## Spec Artifacts

All artifacts are namespaced under `.specs/<short-id>/`. See [references/spec-templates.md](references/spec-templates.md) for all templates.

### Full Mode Structure

```
.specs/<short-id>/
├── README.md                    # Session dashboard
├── input-digest.md              # Normalized input
├── proposal/
│   ├── brief.md
│   ├── requirements.md
│   └── acceptance-criteria.md
├── design/
│   ├── architecture.md
│   ├── api-contracts.md
│   ├── data-model.md
│   └── diagrams/
│       └── system-overview.md
├── review/
│   ├── adversary-report.md
│   ├── security-assessment.md
│   └── qa-plan.md
├── tasks/
│   ├── task-breakdown.md
│   └── task-graph.md
└── decisions/
    └── 0001-decision-title.md
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

See [references/spec-workflow.md](references/spec-workflow.md) Section 7 for recovery strategies covering:

- Teammate fails to respond (re-send → re-spawn → subagent fallback)
- Tests fail repeatedly (detailed feedback → code review → user escalation)
- Critical issue found post-implementation (hotfix task or architecture revision)
- Session interrupted (check for existing `.specs/`, offer resume)
- Circular task dependencies (detect via DFS, request revision)
- Invalid agent output (validation error → retry → subagent fallback)

## Usage

```bash
# Plain text description
/team-implement Add user authentication with OAuth2 and JWT

# GitHub issue
/team-implement #42
/team-implement owner/repo#42

# Jira ticket
/team-implement PROJ-123

# GitHub PR (spec for changes needed)
/team-implement !456

# File with requirements
/team-implement ./docs/requirements.md

# URL with spec
/team-implement https://example.com/feature-spec

# Directory to analyze
/team-implement ./src/auth/
```

## References

- [references/agent-catalog.md](references/agent-catalog.md) — All 11 agent role definitions with complete prompt templates
- [references/spec-workflow.md](references/spec-workflow.md) — Input detection, complexity matrix, phase transitions, quality gates
- [references/communication-patterns.md](references/communication-patterns.md) — SendMessage templates for team coordination
- [references/spec-templates.md](references/spec-templates.md) — File templates for all `.specs/` artifacts
