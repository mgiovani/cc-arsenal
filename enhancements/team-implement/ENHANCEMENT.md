---
# Enhancement for: team-implement
disable-model-invocation: true
argument-hint: "<description|PROJ-123|#issue|!pr|file|url>"
allowed-tools: "Read, Write, Edit, Bash, Grep, Glob, Task, Teammate, SendMessage, TaskCreate, TaskUpdate, TaskList, TaskGet, WebFetch, AskUserQuestion"
context: "fork"
agent: "general-purpose"
---

## Claude Code Enhanced Features

This skill includes the following Claude Code-specific enhancements:

## Input

$ARGUMENTS

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

## Quality Gates Summary

| Gate | Between Phases | Pass Criteria | On Failure | Max Retries |
|------|---------------|---------------|------------|-------------|
| Clarifying Questions | 0 → 2 | All ambiguities resolved | More questions | Unlimited |
| Spec Review | 2 → 3 | Requirements complete, criteria clear | Revise specs | 2 |
| Adversarial Review | 3 → 5 | Zero BLOCKER findings | Architect revises | 2 |
| User Approval | 5 → 6 | User approves full plan | Revise or cancel | Unlimited |
| Quality Verification | 6 → 8 | Tests pass, no critical findings | Loop to Phase 6 | 3 |
| Final Delivery | 8 → done | Spec artifacts exist, all tasks done | Block completion | 1 |

## Error Recovery

See [references/spec-workflow.md](references/spec-workflow.md) Section 7 for recovery strategies covering:

- Teammate fails to respond (re-send → re-spawn → subagent fallback)
- Tests fail repeatedly (detailed feedback → code review → user escalation)
- Critical issue found post-implementation (hotfix task or architecture revision)
- Session interrupted (check for existing `.specs/`, offer resume)
- Circular task dependencies (detect via DFS, request revision)
- Invalid agent output (validation error → retry → subagent fallback)
