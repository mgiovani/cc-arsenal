# Communication Patterns Reference

This document provides SendMessage templates and patterns for inter-agent communication in full team mode. Use these templates to ensure clear, structured communication between the orchestrator and specialized agents.

## 1. Message Types Overview

| Type | Tool | When Used |
|------|------|-----------|
| Direct message | SendMessage type: "message" | Phase handoffs, targeted instructions, file delivery |
| Broadcast | SendMessage type: "broadcast" | Critical issues only (expensive! N messages) |
| Shutdown request | SendMessage type: "shutdown_request" | End of agent's phase or session teardown |
| Shutdown response | SendMessage type: "shutdown_response" | Agent confirms graceful exit |
| Plan approval | SendMessage type: "plan_approval_response" | Lead approves teammate plan before execution |

**Default to "message" (direct messaging).** Only use broadcast for critical, team-wide issues.

## 2. Phase Handoff Templates

### Phase 2 → Product Manager (Specification Kickoff)

```python
SendMessage({
  "type": "message",
  "recipient": "product-manager",
  "content": """Phase 2 (Specification) has started. Read the input digest at .specs/[SPEC_ID]/input-digest.md and the clarified requirements from Phase 1.

Your deliverables:
1. Write .specs/[SPEC_ID]/proposal/brief.md — project overview, goals, constraints, success metrics
2. Write .specs/[SPEC_ID]/proposal/requirements.md — FR-001/NFR-001 numbered functional and non-functional requirements
3. Write .specs/[SPEC_ID]/proposal/acceptance-criteria.md — Given/When/Then user stories for each requirement

Codebase context:
- Project type: [PROJECT_TYPE]
- Tech stack: [TECH_STACK]
- Existing patterns: [PATTERNS]
- Related files: [FILE_PATHS]

Guidelines:
- Number all requirements (FR-001, FR-002, NFR-001, etc.)
- Link acceptance criteria to requirements
- Consider edge cases and error handling
- Align with existing project conventions

When complete:
1. Update your task status via TaskUpdate (mark task [TASK_ID] as completed)
2. Send a message to me with a summary of your deliverables""",
  "summary": "Begin specification phase with input digest"
})
```

### Phase 3 → Architect (Design)

```python
SendMessage({
  "type": "message",
  "recipient": "architect",
  "content": """Phase 3 (Design) has started. The specification has been completed and approved.

Read these artifacts:
1. .specs/[SPEC_ID]/proposal/brief.md — project overview and goals
2. .specs/[SPEC_ID]/proposal/requirements.md — numbered requirements
3. .specs/[SPEC_ID]/proposal/acceptance-criteria.md — user stories
4. .specs/[SPEC_ID]/input-digest.md — original user input

Your deliverables:
1. Write .specs/[SPEC_ID]/design/architecture.md — system architecture, component diagram (Mermaid), data flow
2. Write .specs/[SPEC_ID]/design/api-contract.md — API endpoints, request/response schemas, status codes
3. Write .specs/[SPEC_ID]/design/data-model.md — database schema, entity relationships, migrations
4. Write .specs/[SPEC_ID]/design/implementation-plan.md — file changes, dependency graph, rollout strategy

Codebase context:
- Project type: [PROJECT_TYPE]
- Tech stack: [TECH_STACK]
- Existing architecture: [ARCH_PATTERNS]
- Database: [DATABASE_TYPE]
- API framework: [API_FRAMEWORK]

Guidelines:
- Use Mermaid diagrams for visual clarity
- Specify file paths for all changes
- Consider backward compatibility
- Document security implications
- Plan for testability

When complete:
1. Update your task status via TaskUpdate (mark task [TASK_ID] as completed)
2. Send a message to me with a summary of your design artifacts

Note: Your design will be reviewed by the adversary-reviewer in Phase 4.""",
  "summary": "Begin design phase with approved spec"
})
```

### Phase 4 → Adversary Reviewer (Design Review)

```python
SendMessage({
  "type": "message",
  "recipient": "adversary-reviewer",
  "content": """Phase 4 (Design Review) has started. The architect has completed the design.

Read these artifacts:
1. .specs/[SPEC_ID]/design/architecture.md — system architecture
2. .specs/[SPEC_ID]/design/api-contract.md — API endpoints
3. .specs/[SPEC_ID]/design/data-model.md — database schema
4. .specs/[SPEC_ID]/design/implementation-plan.md — file changes
5. .specs/[SPEC_ID]/proposal/requirements.md — requirements to validate against

Your deliverable:
1. Write .specs/[SPEC_ID]/reviews/design-review.md — adversarial review with findings

Review focus:
- Security vulnerabilities (OWASP Top 10, injection, auth, CORS)
- Performance bottlenecks (N+1 queries, missing indexes, unbounded lists)
- Scalability issues (single points of failure, resource limits)
- Testability gaps (untestable components, missing test hooks)
- Requirement coverage (missing FRs/NFRs)
- Edge cases and error handling

Finding severity levels:
- **BLOCKER**: Must fix before implementation (security, data loss, broken requirements)
- **MAJOR**: Should fix (performance, scalability, maintainability)
- **MINOR**: Nice to have (code style, optimization, documentation)

Guidelines:
- Be thorough and critical (this is your role!)
- Provide specific, actionable feedback
- Reference requirement IDs when relevant
- Suggest concrete alternatives for BLOCKERs

When complete:
1. Update your task status via TaskUpdate (mark task [TASK_ID] as completed)
2. Send a message to me with:
   - Count of BLOCKER/MAJOR/MINOR findings
   - Summary of critical issues
   - Recommendation (approve / request changes)""",
  "summary": "Begin adversarial design review"
})
```

### Phase 5 → Scrum Master (Task Decomposition)

```python
SendMessage({
  "type": "message",
  "recipient": "scrum-master",
  "content": """Phase 5 (Task Decomposition) has started. Design has been approved after adversarial review.

Read these artifacts:
1. .specs/[SPEC_ID]/design/implementation-plan.md — high-level file changes
2. .specs/[SPEC_ID]/design/architecture.md — system architecture
3. .specs/[SPEC_ID]/design/api-contract.md — API endpoints
4. .specs/[SPEC_ID]/design/data-model.md — database schema
5. .specs/[SPEC_ID]/reviews/design-review.md — review feedback (already addressed)

Your deliverable:
1. Create tasks via TaskCreate for ALL implementation work

Task decomposition strategy:
- One task per logical unit of work (file, feature, test suite)
- Include file paths in task descriptions
- Set dependencies using `dependencies` field (task IDs)
- Assign tasks to frontend-dev or backend-dev based on scope
- Ensure frontend/backend can work in parallel when possible

Task template:
```
TaskCreate({
  "title": "[FRONTEND|BACKEND] Brief description",
  "description": "Detailed instructions including file paths and acceptance criteria",
  "owner": "frontend-dev" or "backend-dev",
  "dependencies": ["task-id-1", "task-id-2"]  // only if blocking dependencies exist
})
```

Guidelines:
- Frontend tasks: UI components, user interactions, client-side validation, API calls
- Backend tasks: API endpoints, business logic, database operations, server-side validation
- Shared tasks: Type definitions, API contracts, data models (backend owns, frontend reads)
- Keep tasks small (1-3 files each) for parallel work
- Document dependencies explicitly (e.g., "API endpoint must exist before frontend integration")

When complete:
1. Update your task status via TaskUpdate (mark task [TASK_ID] as completed)
2. Send a message to me with:
   - Total task count
   - Frontend vs backend split
   - Dependency graph summary
   - Estimated parallel work windows""",
  "summary": "Begin task decomposition for parallel implementation"
})
```

### Phase 6 → Frontend Dev (Parallel Implementation)

```python
SendMessage({
  "type": "message",
  "recipient": "frontend-dev",
  "content": """Phase 6 (Implementation) has started. The scrum-master has created tasks for you.

Read these artifacts:
1. .specs/[SPEC_ID]/design/architecture.md — system architecture
2. .specs/[SPEC_ID]/design/api-contract.md — API endpoints you'll call
3. .specs/[SPEC_ID]/design/data-model.md — data types and schemas
4. Task list at ~/.claude/tasks/[TEAM_NAME]/ — check for tasks assigned to you

Your responsibilities:
- Implement ALL tasks assigned to "frontend-dev"
- Check TaskList periodically for newly unblocked tasks
- Claim tasks with TaskUpdate (set owner to your name)
- Mark tasks completed with TaskUpdate when done

File scope (DO NOT modify backend files):
- [FRONTEND_DIR]/ — UI components, pages, client-side logic
- [SHARED_TYPES_DIR]/ — read-only (backend owns, you consume)
- [TESTS_DIR]/frontend/ — frontend-specific tests

API contract:
- All endpoints are documented in .specs/[SPEC_ID]/design/api-contract.md
- If an endpoint doesn't exist yet, create a mock/stub for local testing
- Coordinate with backend-dev via orchestrator if API changes are needed

Guidelines:
- Follow existing project patterns and conventions
- Add client-side validation matching API contract
- Write tests for components and user flows
- Handle loading states and errors gracefully
- Use TypeScript types from shared directory

Coordination:
- If you discover a blocker, send a message to me (orchestrator) immediately
- If you need API contract changes, send a message to me (don't contact backend-dev directly)
- Stay in your file scope (don't modify backend code)

When a task is complete:
1. Run tests to ensure nothing broke
2. Update task status via TaskUpdate (mark as completed)
3. Check TaskList for next available task
4. If all your tasks are done, send me a summary message""",
  "summary": "Begin frontend implementation with assigned tasks"
})
```

### Phase 6 → Backend Dev (Parallel Implementation)

```python
SendMessage({
  "type": "message",
  "recipient": "backend-dev",
  "content": """Phase 6 (Implementation) has started. The scrum-master has created tasks for you.

Read these artifacts:
1. .specs/[SPEC_ID]/design/architecture.md — system architecture
2. .specs/[SPEC_ID]/design/api-contract.md — API endpoints you'll implement
3. .specs/[SPEC_ID]/design/data-model.md — database schema and migrations
4. Task list at ~/.claude/tasks/[TEAM_NAME]/ — check for tasks assigned to you

Your responsibilities:
- Implement ALL tasks assigned to "backend-dev"
- Check TaskList periodically for newly unblocked tasks
- Claim tasks with TaskUpdate (set owner to your name)
- Mark tasks completed with TaskUpdate when done

File scope (DO NOT modify frontend files):
- [BACKEND_DIR]/ — API routes, business logic, database operations
- [SHARED_TYPES_DIR]/ — type definitions (you own these, frontend reads)
- [MIGRATIONS_DIR]/ — database migrations
- [TESTS_DIR]/backend/ — backend-specific tests

Implementation priorities:
1. Database migrations (frontend needs stable schema)
2. Shared type definitions (frontend depends on these)
3. API endpoints (follow contract exactly)
4. Business logic and validation
5. Integration tests

API contract compliance:
- All endpoints must match .specs/[SPEC_ID]/design/api-contract.md exactly
- If you need to change the contract, send a message to me (orchestrator) first
- Document any deviations in your task updates

Guidelines:
- Follow existing project patterns and conventions
- Add server-side validation for all inputs
- Write tests for endpoints and business logic
- Handle errors gracefully with proper status codes
- Consider security (authentication, authorization, input sanitization)

Coordination:
- If you discover a blocker, send a message to me (orchestrator) immediately
- If you need API contract changes, send a message to me (don't contact frontend-dev directly)
- Stay in your file scope (don't modify frontend code)

When a task is complete:
1. Run tests to ensure nothing broke
2. Update task status via TaskUpdate (mark as completed)
3. Check TaskList for next available task
4. If all your tasks are done, send me a summary message""",
  "summary": "Begin backend implementation with assigned tasks"
})
```

### Phase 7 → QA Engineer (Testing)

```python
SendMessage({
  "type": "message",
  "recipient": "qa-engineer",
  "content": """Phase 7 (Testing) has started. Frontend and backend implementation is complete.

Read these artifacts:
1. .specs/[SPEC_ID]/proposal/acceptance-criteria.md — user stories to validate
2. .specs/[SPEC_ID]/proposal/requirements.md — functional requirements
3. .specs/[SPEC_ID]/design/api-contract.md — API endpoints to test
4. Implementation files in [FRONTEND_DIR]/ and [BACKEND_DIR]/

Your deliverables:
1. Write .specs/[SPEC_ID]/testing/test-plan.md — test strategy, coverage plan, test cases
2. Write .specs/[SPEC_ID]/testing/test-results.md — test execution results, bugs found, pass/fail status
3. Create or update test files in [TESTS_DIR]/

Test coverage requirements:
- Unit tests: All business logic functions, API endpoints
- Integration tests: API + database interactions, frontend + backend integration
- E2E tests: Critical user flows from acceptance criteria
- Edge cases: Error handling, boundary conditions, invalid inputs

Test focus areas:
- Functional correctness (all requirements met)
- API contract compliance (request/response schemas)
- Error handling (4xx, 5xx responses)
- Security (authentication, authorization, input validation)
- Performance (acceptable response times)

Bug severity levels:
- **CRITICAL**: Blocking user flows, data loss, security issues
- **HIGH**: Major functionality broken, poor UX
- **MEDIUM**: Minor functionality issues, edge case failures
- **LOW**: Cosmetic issues, minor inconsistencies

Guidelines:
- Run ALL existing tests to catch regressions
- Add new tests for new functionality
- Document any test failures with steps to reproduce
- Suggest fixes for bugs (don't fix them yourself)

When complete:
1. Update your task status via TaskUpdate (mark task [TASK_ID] as completed)
2. Send a message to me with:
   - Test pass/fail summary
   - Critical/High bug count
   - Recommendation (approve for release / request fixes)""",
  "summary": "Begin testing phase with acceptance criteria"
})
```

### Phase 8 → Tech Writer (Documentation)

```python
SendMessage({
  "type": "message",
  "recipient": "tech-writer",
  "content": """Phase 8 (Documentation) has started. Implementation and testing are complete.

Read these artifacts:
1. .specs/[SPEC_ID]/proposal/brief.md — project overview
2. .specs/[SPEC_ID]/design/api-contract.md — API endpoints
3. .specs/[SPEC_ID]/design/architecture.md — system architecture
4. Implementation files in [FRONTEND_DIR]/ and [BACKEND_DIR]/
5. Existing documentation in [DOCS_DIR]/

Your deliverables:
1. Update or create API documentation (if API changes)
2. Update or create user-facing documentation (if user-facing features)
3. Update or create developer documentation (if architecture changes)
4. Write .specs/[SPEC_ID]/documentation/summary.md — list of all documentation changes

Documentation types:
- **API docs**: Endpoint reference, request/response examples, authentication
- **User docs**: Feature guides, tutorials, screenshots, FAQs
- **Developer docs**: Architecture decisions, setup instructions, contribution guidelines
- **Release notes**: User-facing changes, migration steps, breaking changes

Guidelines:
- Follow existing documentation style and structure
- Add code examples and API usage samples
- Include visual aids (screenshots, diagrams) for user docs
- Document breaking changes and migration paths
- Update table of contents and navigation

File locations:
- API docs: [API_DOCS_DIR]/
- User docs: [USER_DOCS_DIR]/
- Developer docs: [DEV_DOCS_DIR]/
- Release notes: [RELEASE_NOTES_FILE]

When complete:
1. Update your task status via TaskUpdate (mark task [TASK_ID] as completed)
2. Send a message to me with:
   - List of documentation files created/updated
   - Summary of major documentation changes
   - Recommendation for documentation review""",
  "summary": "Begin documentation phase"
})
```

## 3. Adversarial Review Patterns

### Sending Work to Adversary

```python
SendMessage({
  "type": "message",
  "recipient": "adversary-reviewer",
  "content": """The architect has completed the design. Please perform an adversarial review.

Artifacts to review:
1. .specs/[SPEC_ID]/design/architecture.md
2. .specs/[SPEC_ID]/design/api-contract.md
3. .specs/[SPEC_ID]/design/data-model.md
4. .specs/[SPEC_ID]/design/implementation-plan.md

Validation against:
- .specs/[SPEC_ID]/proposal/requirements.md (check coverage)

Focus on finding BLOCKERs:
- Security vulnerabilities
- Data loss risks
- Missing requirements
- Performance bottlenecks
- Scalability issues

Deliverable: .specs/[SPEC_ID]/reviews/design-review.md

Send me a summary when complete.""",
  "summary": "Design complete, requesting adversarial review"
})
```

### Routing BLOCKER Findings Back to Architect

```python
SendMessage({
  "type": "message",
  "recipient": "architect",
  "content": """The adversary-reviewer has found [N] BLOCKER issues in your design.

Read the review at .specs/[SPEC_ID]/reviews/design-review.md

BLOCKER findings:
1. [BLOCKER_SUMMARY_1]
2. [BLOCKER_SUMMARY_2]
...

Your task:
1. Address ALL BLOCKER findings
2. Update the design artifacts accordingly
3. Document your changes in .specs/[SPEC_ID]/reviews/blocker-resolution.md

Guidelines:
- For each BLOCKER, document:
  - Original issue
  - Your solution
  - Changed artifacts
- Update design files directly (architecture.md, api-contract.md, etc.)
- Consider secondary effects (don't break other parts of the design)

When complete:
1. Update your task status via TaskUpdate
2. Send me a summary of your changes
3. I will route back to adversary-reviewer for re-review""",
  "summary": "[N] BLOCKER issues found, requesting resolution"
})
```

### Resolution Confirmation

```python
SendMessage({
  "type": "message",
  "recipient": "adversary-reviewer",
  "content": """The architect has addressed all BLOCKER findings.

Read the resolution document:
- .specs/[SPEC_ID]/reviews/blocker-resolution.md

Re-review the updated design:
1. .specs/[SPEC_ID]/design/architecture.md (updated)
2. .specs/[SPEC_ID]/design/api-contract.md (updated)
3. .specs/[SPEC_ID]/design/data-model.md (updated)

Your task:
1. Verify each BLOCKER has been adequately addressed
2. Update .specs/[SPEC_ID]/reviews/design-review.md with re-review status
3. Mark each BLOCKER as RESOLVED or UNRESOLVED

Outcome options:
- **APPROVED**: All BLOCKERs resolved, design is good to implement
- **REQUEST CHANGES**: BLOCKERs remain unresolved

Send me a summary with your recommendation.""",
  "summary": "BLOCKERs addressed, requesting re-review"
})
```

## 4. Blocker Escalation Patterns

### Agent → Orchestrator Escalation

Template for when any agent discovers a blocker during work:

```python
SendMessage({
  "type": "message",
  "recipient": "team-lead",  # orchestrator's name
  "content": """BLOCKER discovered during [PHASE_NAME] phase.

Context:
- Task: [TASK_ID or PHASE_NAME]
- Current work: [WHAT_I_WAS_DOING]

Issue:
[DETAILED_DESCRIPTION_OF_BLOCKER]

Impact:
- Cannot proceed with [SPECIFIC_WORK]
- Affects tasks: [TASK_IDS]
- Potentially affects: [OTHER_AGENTS or PHASES]

Possible solutions:
1. [OPTION_1]
2. [OPTION_2]

Request:
[WHAT_YOU_NEED] (e.g., user input, architect decision, requirement clarification)

My recommendation: [YOUR_SUGGESTED_APPROACH]""",
  "summary": "BLOCKER: [brief description]"
})
```

### Orchestrator → User Escalation

When orchestrator needs user input to resolve a blocker:

```text
BLOCKER: User input required

The [AGENT_NAME] has encountered a blocker during [PHASE_NAME]:

Issue:
[BLOCKER_DESCRIPTION]

Context:
- Affected tasks: [TASK_IDS]
- Artifacts: [FILE_PATHS]
- Current progress: [PROGRESS_SUMMARY]

Options we've identified:
1. [OPTION_1] — Pros: [...] Cons: [...]
2. [OPTION_2] — Pros: [...] Cons: [...]

Our recommendation: [OPTION_X]

Please advise on how to proceed.
```

### Orchestrator → Agent Routing

When orchestrator routes a question to another agent:

```python
SendMessage({
  "type": "message",
  "recipient": "architect",  # or other agent
  "content": """Question routed from [SOURCE_AGENT] regarding [TOPIC].

Original question:
[QUOTED_QUESTION_FROM_AGENT]

Context:
- Related task: [TASK_ID]
- Related artifacts: [FILE_PATHS]
- Why this is being routed to you: [REASONING]

Please provide:
1. [SPECIFIC_ANSWER_1]
2. [SPECIFIC_ANSWER_2]

Note: [SOURCE_AGENT] is blocked on this, so prioritize your response.

When done, send me your answer (I'll route it back to [SOURCE_AGENT]).""",
  "summary": "Question from [SOURCE_AGENT]: [brief topic]"
})
```

## 5. Parallel Coordination Patterns

### Frontend + Backend Contract Sharing

Send the same message to both agents:

```python
# To frontend-dev
SendMessage({
  "type": "message",
  "recipient": "frontend-dev",
  "content": """API contract is finalized. Read .specs/[SPEC_ID]/design/api-contract.md for all endpoints and schemas.

Key endpoints for your work:
- [ENDPOINT_1]: [BRIEF_DESCRIPTION]
- [ENDPOINT_2]: [BRIEF_DESCRIPTION]

Data models:
- [MODEL_1]: .specs/[SPEC_ID]/design/data-model.md#[ANCHOR]
- [MODEL_2]: .specs/[SPEC_ID]/design/data-model.md#[ANCHOR]

You can start implementing UI components now. If an endpoint doesn't exist yet, use a mock for local testing.

If you need contract changes, notify me (don't modify the contract yourself).""",
  "summary": "API contract finalized, ready for implementation"
})

# To backend-dev
SendMessage({
  "type": "message",
  "recipient": "backend-dev",
  "content": """API contract is finalized. Read .specs/[SPEC_ID]/design/api-contract.md for all endpoints and schemas.

Your implementation must match this contract exactly:
- [ENDPOINT_1]: [BRIEF_DESCRIPTION]
- [ENDPOINT_2]: [BRIEF_DESCRIPTION]

Data models:
- [MODEL_1]: .specs/[SPEC_ID]/design/data-model.md#[ANCHOR]
- [MODEL_2]: .specs/[SPEC_ID]/design/data-model.md#[ANCHOR]

Priority: Implement shared type definitions first (frontend depends on these).

If you need contract changes, notify me (don't modify the contract without approval).""",
  "summary": "API contract finalized, ready for implementation"
})
```

### Conflict Prevention

```python
SendMessage({
  "type": "message",
  "recipient": "frontend-dev",
  "content": """File scope reminder:

YOU OWN (modify freely):
- [FRONTEND_DIR]/
- [TESTS_DIR]/frontend/

READ ONLY (don't modify):
- [SHARED_TYPES_DIR]/ (backend owns)
- [BACKEND_DIR]/ (backend owns)

DO NOT TOUCH:
- [BACKEND_DIR]/
- [MIGRATIONS_DIR]/
- [API_DIR]/

If you need changes to read-only files, notify me and I'll coordinate with backend-dev.""",
  "summary": "File scope reminder to prevent conflicts"
})
```

### Progress Synchronization

Template for agents to report progress:

```python
# Agent → Orchestrator
SendMessage({
  "type": "message",
  "recipient": "team-lead",
  "content": """Progress update for [PHASE_NAME]:

Completed tasks:
- [TASK_ID_1]: [BRIEF_SUMMARY]
- [TASK_ID_2]: [BRIEF_SUMMARY]

In-progress tasks:
- [TASK_ID_3]: [% complete] — [ETA]

Blocked tasks:
- [TASK_ID_4]: [BLOCKER_SUMMARY]

Remaining tasks: [N] tasks

Estimated completion: [TIME_ESTIMATE]

Notes:
- [ANY_IMPORTANT_CONTEXT]""",
  "summary": "Progress update: [X] of [Y] tasks complete"
})
```

## 6. Shutdown Patterns

### Phase Completion Shutdown

```python
SendMessage({
  "type": "shutdown_request",
  "recipient": "product-manager",
  "content": """Phase 2 (Specification) is complete. Your deliverables have been reviewed and accepted:

Deliverables:
- .specs/[SPEC_ID]/proposal/brief.md ✓
- .specs/[SPEC_ID]/proposal/requirements.md ✓
- .specs/[SPEC_ID]/proposal/acceptance-criteria.md ✓

Thank you for your work. You can shut down now."""
})
```

### Agent Shutdown Response

Template for how agents should respond to shutdown requests:

```python
SendMessage({
  "type": "shutdown_response",
  "request_id": "[REQUEST_ID_FROM_SHUTDOWN_MESSAGE]",
  "approve": true
})
```

If agent needs to reject shutdown:

```python
SendMessage({
  "type": "shutdown_response",
  "request_id": "[REQUEST_ID_FROM_SHUTDOWN_MESSAGE]",
  "approve": false,
  "content": "Still working on task [TASK_ID]. Need [ESTIMATE] more time to complete [SPECIFIC_WORK]."
})
```

### End-of-Session Cleanup

Template for shutting down ALL remaining agents at teardown:

```python
# Read team config to get all active agents
team_config = Read("~/.claude/teams/[TEAM_NAME]/config.json")

# Send shutdown request to each agent
for agent in team_config["members"]:
    if agent["name"] != "team-lead":  # don't shut down yourself
        SendMessage({
          "type": "shutdown_request",
          "recipient": agent["name"],
          "content": f"""Session complete. All implementation work is done.

Thank you for your contributions to this project. You can shut down now."""
        })
```

## 7. Anti-Patterns

### DON'T: Broadcast for Routine Updates

```python
# ❌ BAD: Broadcasting to 6 agents = 6 messages
SendMessage({
  "type": "broadcast",
  "content": "Design phase is complete.",
  "summary": "Design complete"
})

# ✅ GOOD: Direct message to relevant agent
SendMessage({
  "type": "message",
  "recipient": "scrum-master",
  "content": "Design phase is complete. You can start task decomposition.",
  "summary": "Design complete, begin task decomposition"
})
```

### DON'T: Message Agents That Haven't Been Spawned

```python
# ❌ BAD: Trying to message an agent that doesn't exist yet
SendMessage({
  "type": "message",
  "recipient": "qa-engineer",
  "content": "Testing phase starts soon"
})
# Error: qa-engineer hasn't been spawned yet!

# ✅ GOOD: Spawn the agent first, then message
Task({
  "team_name": "[TEAM_NAME]",
  "name": "qa-engineer",
  "subagent_type": "Explore",
  "prompt": "[INSTRUCTIONS]"
})
# Wait for spawn confirmation, then send message
```

### DON'T: Forget File Paths in Handoffs

```python
# ❌ BAD: Vague instructions without file paths
SendMessage({
  "type": "message",
  "recipient": "architect",
  "content": "Read the specification and create a design."
})

# ✅ GOOD: Specific file paths
SendMessage({
  "type": "message",
  "recipient": "architect",
  "content": """Read these artifacts:
1. .specs/[SPEC_ID]/proposal/brief.md
2. .specs/[SPEC_ID]/proposal/requirements.md
3. .specs/[SPEC_ID]/proposal/acceptance-criteria.md

Create these deliverables:
1. .specs/[SPEC_ID]/design/architecture.md
2. .specs/[SPEC_ID]/design/api-contract.md"""
})
```

### DON'T: Send Implementation Instructions During Planning

```python
# ❌ BAD: Telling architect HOW to implement
SendMessage({
  "type": "message",
  "recipient": "architect",
  "content": "Use a REST API with Express.js and PostgreSQL. Create 3 endpoints..."
})

# ✅ GOOD: Let architect decide implementation details
SendMessage({
  "type": "message",
  "recipient": "architect",
  "content": """Read the requirements and design the architecture.

Consider:
- Existing tech stack: [STACK]
- Performance requirements: [NFR-001]
- Scalability needs: [NFR-002]

You decide the best approach."""
})
```

### DON'T: Let Agents Modify Files Outside Scope

```python
# ❌ BAD: Frontend agent modifying backend files
# (This will cause merge conflicts and scope violations)

# ✅ GOOD: Strict file scope enforcement in handoff
SendMessage({
  "type": "message",
  "recipient": "frontend-dev",
  "content": """Your file scope:
- [FRONTEND_DIR]/ (you own)
- [TESTS_DIR]/frontend/ (you own)

DO NOT MODIFY:
- [BACKEND_DIR]/
- [SHARED_TYPES_DIR]/
- [MIGRATIONS_DIR]/

If you need changes to these, notify me."""
})
```

### DON'T: Skip Shutdown Confirmations

```python
# ❌ BAD: Assuming agent shut down
# (Agent might still be running and using resources)

# ✅ GOOD: Always wait for shutdown response
SendMessage({
  "type": "shutdown_request",
  "recipient": "product-manager",
  "content": "Phase complete, you can shut down."
})
# Wait for shutdown_response before proceeding
```

### DON'T: Use JSON Status Messages

```python
# ❌ BAD: Sending structured JSON status messages
SendMessage({
  "type": "message",
  "recipient": "team-lead",
  "content": '{"type":"idle","status":"waiting","task_id":"task-001"}'
})

# ✅ GOOD: Plain text communication + TaskUpdate for status
SendMessage({
  "type": "message",
  "recipient": "team-lead",
  "content": "Task task-001 is complete. Waiting for next assignment.",
  "summary": "Task complete, ready for next work"
})
TaskUpdate({"task_id": "task-001", "status": "completed"})
```

## Template Checklist

When sending a phase handoff message, ensure you include:

- [ ] **Phase name**: What phase is starting
- [ ] **Read artifacts**: Exact file paths to read
- [ ] **Deliverables**: Exact file paths to write
- [ ] **Codebase context**: Tech stack, patterns, conventions
- [ ] **Guidelines**: Phase-specific instructions
- [ ] **Next steps**: What to do when complete (TaskUpdate + send message)
- [ ] **File scope**: (For implementation phases) what files agent can modify
- [ ] **Coordination notes**: (For parallel phases) how to avoid conflicts

Use these templates as starting points and adapt them to your specific project structure and requirements.
