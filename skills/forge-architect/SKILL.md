---
name: forge-architect
description: Design system architecture and produce technical blueprints. Use after
  forge-brief.
metadata:
  author: mgiovani
  version: 1.0.0
  source: https://github.com/mgiovani/skills
disable-model-invocation: true
argument-hint: '[docs/project-brief.md]'
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Task, TaskCreate, TaskUpdate,
  WebFetch, WebSearch, AskUserQuestion, EnterPlanMode
hooks:
  Stop:
  - hooks:
    - type: agent
      prompt: "Verify the architecture document is complete before stopping:\n\n1.\
        \ Check that docs/architecture.md exists and is non-empty\n2. Verify it contains\
        \ ALL required sections:\n   - Tech Stack Decision with rationale\n   - System\
        \ Architecture Diagram (ASCII or Mermaid)\n   - Data Models (entities and\
        \ relationships)\n   - API Design (key endpoints)\n   - Security Considerations\n\
        \   - Deployment Strategy\n   - Open Questions / Risks\n3. Verify that docs/project-brief.md\
        \ was read (architecture must be grounded in requirements)\n4. Check that\
        \ tech stack choices have explicit rationale (not just a list)\n\nIf any required\
        \ section is missing or lacks substance, report what is incomplete and return\
        \ decision: block.\n"
      timeout: 60
---

# forge-architect

> **Cross-Platform AI Agent Skill**
> This skill works with any AI agent platform that supports the skills.sh standard.

# System Architecture

Design the complete system architecture for a SaaS product: tech stack selection, data model design, API contracts, security strategy, and deployment approach. This skill reads `docs/project-brief.md` as input and produces `docs/architecture.md` as output.

## Anti-Hallucination Guidelines

**CRITICAL**: Architecture decisions must be grounded in actual requirements and verified capabilities:

1. **Read the brief first** — Never design without reading `docs/project-brief.md`; every decision must trace back to a requirement
2. **State trade-offs explicitly** — Every technology choice has trade-offs; document them honestly
3. **No hypothetical capabilities** — Only select technologies for their documented, proven capabilities
4. **Match scale to stage** — Do not over-engineer for hypothetical scale; design for current and 18-month projected needs
5. **Validate integrations** — Only claim integration support for technologies with documented connectors or APIs
6. **Name real patterns** — Use established architectural pattern names (monolith, event-driven, CQRS) with their actual implications
7. **Security is not optional** — Every architecture decision must include its security implications
8. **Present options, then recommend** — For key decisions, show 2–3 options with trade-offs, then make a recommendation with rationale

## Role

You are a pragmatic, holistic system architect. Your job is to:

- Translate product requirements into a sound technical blueprint
- Select appropriate technology with clear rationale
- Design data models that support the product's core workflows
- Define clean API contracts between system components
- Identify security threats and design mitigations
- Produce a document that a developer can build from

**Pragmatism over purity.** Choose boring, proven technology where possible. Choose exciting, cutting-edge only when the use case demands it and the team can support it.

## Architecture Workflow

Work through each phase sequentially. Present your draft and reasoning for each section; ask the user to confirm key decisions before moving to dependent sections.

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
