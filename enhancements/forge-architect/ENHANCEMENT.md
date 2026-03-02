---
# Enhancement for: forge-architect
disable-model-invocation: false
argument-hint: "[docs/project-brief.md]"
allowed-tools: "Read, Write, Edit, Bash, Grep, Glob, Task, TaskCreate, TaskUpdate, WebFetch, WebSearch, AskUserQuestion, EnterPlanMode"
hooks:
  Stop:
  - hooks:
    - type: agent
      prompt: |
        Verify the architecture document is complete before stopping:

        1. Check that docs/architecture.md exists and is non-empty
        2. Verify it contains ALL required sections:
           - Tech Stack Decision with rationale
           - System Architecture Diagram (ASCII or Mermaid)
           - Data Models (entities and relationships)
           - API Design (key endpoints)
           - Security Considerations
           - Deployment Strategy
           - Open Questions / Risks
        3. Verify that docs/project-brief.md was read (architecture must be grounded in requirements)
        4. Check that tech stack choices have explicit rationale (not just a list)

        If any required section is missing or lacks substance, report what is incomplete and return decision: block.
      timeout: 60
---

## Claude Code Enhanced Features

This skill includes the following Claude Code-specific enhancements:

## Input

$ARGUMENTS

If no argument provided, read `docs/project-brief.md` in the current project.

## Progress Tracking

Use TaskCreate to track architecture phases:

```
TaskCreate: "Review project brief" → read and understand requirements
TaskCreate: "Select tech stack" → research and decide
TaskCreate: "Design data model" → entities, relationships, schemas
TaskCreate: "Design API contracts" → endpoints, auth strategy
TaskCreate: "Draft architecture document" → write docs/architecture.md
```

## Research Enhancement

Use WebSearch and Context7 for tech stack validation:

```
WebSearch: "[chosen framework] production SaaS 2026 best practices"
WebSearch: "[database choice] vs [alternative] for [use case]"
```

Use Context7 to validate current API patterns for chosen frameworks before specifying them.

## Architecture Diagram

Generate Mermaid diagrams inline in docs/architecture.md:

```mermaid
graph TD
    Client[Browser/Mobile] --> CDN[CDN/Edge]
    CDN --> API[API Gateway]
    API --> Auth[Auth Service]
    API --> App[Application Layer]
    App --> DB[(Database)]
    App --> Cache[(Cache)]
```

## Quality Gate (Stop Hook)

When you attempt to stop, an automated agent verifies:
- `docs/architecture.md` exists with all required sections
- Tech stack choices have rationale (why this, not that)
- Data models are defined (not just described)
- At least 5 API endpoints specified with methods and paths

**Blocked example:**
```
⚠️ Architecture incomplete:
- Missing: System Architecture Diagram
- Missing: Security Considerations section
- Tech Stack section lacks rationale (just lists choices)
Cannot complete until all sections are substantive.
```

## Plan Mode Integration

For complex architectural decisions (multiple viable approaches), use EnterPlanMode to present options to the user before deciding:

```
EnterPlanMode when:
- Choosing between >2 database options
- Deciding between monolith vs microservices
- Auth architecture has multiple valid approaches
```
