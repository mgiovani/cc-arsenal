# Communication Patterns Reference

Coordination templates for full-mode team-implement. Full mode requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` (see SKILL.md Prerequisites).

**Tool-neutral note**: everything below assumes a `SendMessage`-equivalent tool for direct agent-to-agent coordination — that's specific to environments with real agent-team support. In **lite mode** (or anywhere `SendMessage` doesn't exist), there is no cross-agent messaging: the orchestrator spawns each role as a sequential `Task` subagent, reads its return value, and manually relays whatever the templates below would have sent as a message into the next subagent's prompt. The message *content* below (what to say, what file paths to include) is still the right content to relay — only the transport changes.

## 1. Message Types Overview

| Type | When Used |
|------|-----------|
| Direct message | Phase handoffs, targeted instructions, file delivery |
| Broadcast | Critical, team-wide issues only (expensive — N messages) |
| Shutdown/stop | End of an agent's phase, or session teardown |

**Default to direct messaging.** Only broadcast for critical team-wide issues.

## 2. Phase Handoff Templates

### Phase 2 → Product Lead (Specification Kickoff)

```
SendMessage({
  "type": "message",
  "recipient": "product-lead",
  "content": """Phase 2 (Specification) has started. Read .specs/[SPEC_ID]/input-digest.md.

Deliverables:
1. .specs/[SPEC_ID]/proposal/brief.md
2. .specs/[SPEC_ID]/proposal/requirements.md (FR-001/NFR-001 numbered)
3. .specs/[SPEC_ID]/proposal/acceptance-criteria.md (Given/When/Then)

Codebase context: project type [X], tech stack [Y], existing patterns [Z].

When complete: TaskUpdate the assigned task, then message me a summary.""",
  "summary": "Begin specification phase with input digest"
})
```

### Phase 3 → Architect (Design)

```
SendMessage({
  "type": "message",
  "recipient": "architect",
  "content": """Phase 3 (Design) has started; the spec is approved.

Read: proposal/brief.md, proposal/requirements.md, proposal/acceptance-criteria.md

Deliverables:
1. design/architecture.md — component diagram (Mermaid), data flow
2. design/api-contracts.md — every endpoint, full request/response schemas
3. design/data-model.md — ER diagram, table schemas, migrations
4. design/diagrams/system-overview.md

Codebase context: [tech stack, existing architecture patterns, DB, API framework].

Note: your design will be reviewed by the adversary-reviewer in Phase 4.
When complete: TaskUpdate, then message me a summary.""",
  "summary": "Begin design phase with approved spec"
})
```

### Phase 4 → Adversary Reviewer (Design Review)

```
SendMessage({
  "type": "message",
  "recipient": "adversary-reviewer",
  "content": """Phase 4 (Design Review). The architect finished the design.

Read: design/architecture.md, design/api-contracts.md, design/data-model.md,
proposal/requirements.md (validate coverage against this)

Deliverable: review/adversary-report.md

Focus: security (OWASP), performance (N+1, missing indexes), scalability (single
points of failure), requirement coverage, edge cases.

Severity: BLOCKER (must fix) | WARNING (should fix) | SUGGESTION (nice to have).
Be thorough — this is your job. Reference requirement IDs. Suggest concrete
alternatives for BLOCKERs.

When complete: message me with BLOCKER/WARNING/SUGGESTION counts and a
recommendation (approve / request changes).""",
  "summary": "Begin adversarial design review"
})
```

### Phase 5 → Product Lead (Task Decomposition)

```
SendMessage({
  "type": "message",
  "recipient": "product-lead",
  "content": """Phase 5 (Task Decomposition). Design passed adversarial review.

Read: design/architecture.md, design/api-contracts.md, design/data-model.md,
review/adversary-report.md (findings already addressed)

Deliverable: TaskCreate entries for all implementation work.

Strategy: one task per logical unit (file/feature/test suite, 1-3 files), file
paths in every description, dependencies via the `dependencies` field, owners
matching the engineers you're about to spawn (frontend-engineer,
backend-engineer, ...). Aim for parallel work wherever there's no real
dependency.

When complete: message me with task count, per-owner split, and dependency
summary.""",
  "summary": "Begin task decomposition for parallel implementation"
})
```

### Phase 6 → Implementation Engineer (Parallel Implementation)

Same message shape for every component — this example is for `frontend-engineer`; swap the file-scope block for `backend-engineer`, `infra-engineer`, etc.

```
SendMessage({
  "type": "message",
  "recipient": "frontend-engineer",
  "content": """Phase 6 (Implementation). Tasks assigned to you exist on the board.

Read: design/architecture.md, design/api-contracts.md (endpoints you'll call),
design/data-model.md (types/schemas)

File scope — do not modify outside this:
YOU OWN: [FRONTEND_DIR]/, [TESTS_DIR]/frontend/
READ-ONLY: [SHARED_TYPES_DIR]/ (backend owns it)
DO NOT TOUCH: [BACKEND_DIR]/

Claim tasks via TaskUpdate, implement following existing patterns, write tests,
mark completed. If you're blocked by backend work or need a contract change,
message me — don't reach into backend files to unblock yourself.

When all your tasks are done: run your tests, confirm clean output, message me
a summary.""",
  "summary": "Begin frontend implementation with assigned tasks"
})
```

### Phase 7 → QA Engineer (Testing)

```
SendMessage({
  "type": "message",
  "recipient": "qa-engineer",
  "content": """Phase 7 (Testing). Implementation is complete.

Read: proposal/acceptance-criteria.md (your test plan), proposal/requirements.md,
design/api-contracts.md

Deliverable: review/qa-plan.md — acceptance-criteria table (criterion/test
case/status/evidence), real test-suite results, coverage, bugs found with repro
steps, overall PASS/FAIL verdict.

Run ALL existing tests to catch regressions, not just new-feature tests. Don't
approve if any acceptance criterion fails.

When complete: message me with the pass/fail summary and a recommendation.""",
  "summary": "Begin testing phase with acceptance criteria"
})
```

### Phase 8 → Tech Writer (Documentation, if spawned)

```
SendMessage({
  "type": "message",
  "recipient": "tech-writer",
  "content": """Phase 8 (Documentation). Implementation and testing are complete.

Read: proposal/brief.md, design/api-contracts.md, the actual implementation files
(not just the spec — document what shipped)

Deliverables: README.md update (if user-facing), CHANGELOG.md entry (Keep a
Changelog format, under [Unreleased]), API doc updates if endpoints changed.

When complete: message me with the list of files updated.""",
  "summary": "Begin documentation phase"
})
```

## 3. Adversarial Review Patterns

### Routing BLOCKER Findings Back to the Architect

```
SendMessage({
  "type": "message",
  "recipient": "architect",
  "content": """adversary-reviewer found [N] BLOCKER issues in your design.

Read review/adversary-report.md.

BLOCKER findings:
1. [summary]
2. [summary]

Address ALL BLOCKERs, update the design artifacts directly, and document each
fix (original issue → your solution → changed artifacts) in
review/blocker-resolution.md.

When complete: TaskUpdate, then message me — I'll route back to
adversary-reviewer for re-review.""",
  "summary": "[N] BLOCKER issues found, requesting resolution"
})
```

### Re-Review After Resolution

```
SendMessage({
  "type": "message",
  "recipient": "adversary-reviewer",
  "content": """architect addressed all BLOCKERs — see review/blocker-resolution.md.

Re-review the updated design/architecture.md, design/api-contracts.md,
design/data-model.md. Mark each BLOCKER RESOLVED or UNRESOLVED in
review/adversary-report.md. Outcome: APPROVED or REQUEST CHANGES.

This is at most your 2nd review cycle — if BLOCKERs remain unresolved after this
pass, approve with the remaining issues documented rather than looping again.""",
  "summary": "BLOCKERs addressed, requesting re-review"
})
```

## 4. Blocker Escalation

### Agent → Orchestrator

```
SendMessage({
  "type": "message",
  "recipient": "team-lead",
  "content": """BLOCKER during [PHASE_NAME].

Task: [TASK_ID] · Current work: [what I was doing]
Issue: [detailed description]
Impact: cannot proceed with [X]; affects tasks [IDs]; potentially affects [other agents/phases]
Options: 1. [option] 2. [option]
My recommendation: [approach]""",
  "summary": "BLOCKER: [brief description]"
})
```

### Orchestrator → User

Plain text, not a tool call — this goes through whatever the orchestrator uses to talk to the user (e.g. `AskUserQuestion`):

```
BLOCKER: user input required.

[AGENT_NAME] hit a blocker during [PHASE_NAME]: [description].
Affected: tasks [IDs], artifacts [paths].
Options: 1. [option, pros/cons] 2. [option, pros/cons]
Recommendation: [option X]. How should I proceed?
```

## 5. Parallel Coordination

### Contract Sharing (send to every implementation engineer)

```
SendMessage({
  "type": "message",
  "recipient": "frontend-engineer",  # same content, per-recipient endpoint list, to every engineer
  "content": """API contract finalized: design/api-contracts.md.

Key endpoints for your component: [list with one-line descriptions].
Data models: design/data-model.md#[anchor].

Start implementing now. If an endpoint doesn't exist yet, mock it using the
documented response shape. Contract changes go through me, not directly between
engineers.""",
  "summary": "API contract finalized, ready for implementation"
})
```

### Conflict Prevention (file-scope reminder)

```
SendMessage({
  "type": "message",
  "recipient": "frontend-engineer",
  "content": """File scope reminder — YOU OWN: [dirs]. READ-ONLY: [shared dirs].
DO NOT TOUCH: [other components' dirs]. Need a change outside your scope?
Message me and I'll coordinate with the owning engineer.""",
  "summary": "File scope reminder to prevent conflicts"
})
```

### Progress Sync (agent → orchestrator)

```
SendMessage({
  "type": "message",
  "recipient": "team-lead",
  "content": """Progress for [PHASE_NAME]: completed [task IDs + one-line summary],
in-progress [task ID, % done], blocked [task ID + reason]. [N] tasks remaining.""",
  "summary": "Progress update: [X] of [Y] tasks complete"
})
```

## 6. Teardown

There is no confirmed universal "shutdown_request/shutdown_response" message pair — treat this as the pattern, not a fixed API. Send a plain completion message, then stop the teammate with whatever this environment's real stop primitive is (`TaskStop` in Claude Code):

```
SendMessage({
  "type": "message",
  "recipient": "product-lead",
  "content": "Phase 2 complete, deliverables accepted: brief.md, requirements.md,
  acceptance-criteria.md. Thanks — you can stop now."
})
# then:
TaskStop({ "name": "product-lead@team-<short-id>" })  # or the local equivalent
```

At session end, do this for every still-active teammate rather than assuming they've already exited.

## 7. Anti-Patterns

**Broadcasting for routine updates** — broadcast is N messages; use a direct message to the one agent who needs it.

**Messaging an agent that hasn't been spawned yet** — spawn first (`Task` with `team_name`), confirm the spawn, then message.

**Vague handoffs without file paths** — "read the spec and design something" forces the recipient to guess; always give exact paths to read and exact paths to write.

**Telling an agent HOW instead of WHAT** — "design the architecture" + constraints (existing stack, NFRs) beats prescribing "use Express with 3 endpoints called X/Y/Z" — that's the Architect's call to make.

**Letting an engineer touch files outside its declared scope** — state YOU OWN / READ-ONLY / DO NOT TOUCH explicitly in every Phase-6 handoff; this is the actual mechanism that prevents merge conflicts between parallel engineers.

**JSON status blobs instead of plain text + TaskUpdate** — `SendMessage` content is for a human-readable handoff, not a structured payload; use `TaskUpdate` for machine-readable status.

## Template Checklist

Every phase handoff should include:
- [ ] Phase name
- [ ] Exact file paths to read
- [ ] Exact file paths to write
- [ ] Codebase context (stack, patterns, conventions)
- [ ] What to do when complete (TaskUpdate + message back)
- [ ] File scope (implementation phases only)
- [ ] Coordination notes (parallel phases only — how to avoid conflicts)
