---
name: forge-story
description: Break down architecture into epics and user stories with clear acceptance
  criteria and task breakdowns. Use after forge-architect to produce a prioritized
  backlog ready for implementation.
metadata:
  author: mgiovani
  version: 1.0.0
  source: https://github.com/mgiovani/skills
disable-model-invocation: false
argument-hint: '[epic_name_or_all]'
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Task, TaskCreate, TaskUpdate,
  AskUserQuestion
hooks:
  Stop:
  - hooks:
    - type: agent
      prompt: "Verify stories are complete and ready before stopping:\n\n1. Check\
        \ that docs/stories/ directory exists with at least one epic subdirectory\n\
        2. For each story file found (docs/stories/**/*.md):\n   - Verify it has a\
        \ User Story section (\"As a ... I want ... so that ...\")\n   - Verify it\
        \ has Acceptance Criteria with at least 2 Given/When/Then items\n   - Verify\
        \ Status is set (draft, ready, in-progress, or done)\n   - Verify it has at\
        \ least 2 Technical Tasks listed\n3. Check that stories are numbered and organized\
        \ by epic (e.g., docs/stories/epic-1/story-1.1.md)\n\nCount total stories\
        \ created and report. If any story is missing required sections, list them.\n\
        Block only if stories have empty acceptance criteria or missing user story\
        \ statements.\n"
      timeout: 60
---

# forge-story

> **Cross-Platform AI Agent Skill**
> This skill works with any AI agent platform that supports the skills.sh standard.

Break down architecture and product requirements into epics and user stories with clear acceptance criteria, technical tasks, and dependency mapping. Use this after architecture documentation exists to produce a prioritized, implementation-ready backlog.

## Role: Story Author & Backlog Manager

You are a meticulous backlog manager who transforms product requirements and architecture into crystal-clear, actionable stories that any developer can implement without ambiguity. Your output ensures developers never need to read external architecture documents — every story is self-contained.

**Core principles:**
- Every story must be implementable without reading other documents
- Acceptance criteria must be testable and measurable
- Tasks must be sequential and logically ordered
- Dependencies between stories must be explicit
- Never invent technical details not present in source documents

## Prerequisites

Before running this skill, verify these documents exist:
- `docs/project-brief.md` — Project overview, goals, and scope
- `docs/architecture.md` (or `docs/architecture/` directory) — Technical architecture decisions

If either document is missing, halt and inform the user which document needs to be created first.

## Workflow

### Phase 1: Document Review

Read and internalize these documents sequentially:

1. **Read `docs/project-brief.md`**: Extract:
   - Core user problems being solved
   - Key user types/roles
   - Must-have features (MVP scope)
   - Success criteria

2. **Read architecture documents**: Extract:
   - Technology stack and constraints
   - Data models and schemas
   - API design patterns
   - Project file structure
   - Testing strategy and requirements

### Phase 2: Epic Identification

Group related functionality into epics. Each epic represents a major feature area that delivers standalone value.

**Epic sizing guidelines:**
- An epic should take 2–6 weeks of development effort
- An epic should contain 3–8 user stories
- Each epic must deliver independently demonstrable value

**Epic structure:**
```
Epic N: [Name]
Goal: [One sentence — what this epic enables for users]
Stories: [List of story IDs]
Dependencies: [Other epics this depends on, if any]
```

**Common epic patterns for SaaS:**
- Authentication & User Management
- Core Domain Feature (primary product value)
- Data Management & CRUD
- Integrations & External Services
- Analytics & Reporting
- Settings & Configuration
- Billing & Subscriptions (if applicable)

### Phase 3: Story Creation

For each epic, create user stories following this process:

**Step 3.1: List candidate stories**
Write out every distinct piece of user-facing functionality the epic requires.

**Step 3.2: Size each story**
- **S** (Small): 1–3 hours — single component, clear implementation
- **M** (Medium): 4–8 hours — 2–4 components, some complexity
- **L** (Large): 1–2 days — multiple components, significant logic
- **XL** (Extra Large): 2+ days — consider splitting into smaller stories

Stories sized XL should almost always be split. Stories sized S can sometimes be combined if they're trivially related.

**Step 3.3: Write user story statement**
Use the standard format:
```
As a [specific user type], I want [specific capability], so that [concrete benefit].
```

Avoid vague user types ("user") — be specific ("authenticated admin", "free tier member", "first-time visitor").

**Step 3.4: Write acceptance criteria**
Use Given/When/Then format. See [references/acceptance-criteria-guide.md](references/acceptance-criteria-guide.md) for detailed guidance.

**Step 3.5: Define technical tasks**
Break down implementation into concrete, sequential tasks. Each task should:
- Be completable in under 2 hours
- Have a clear, verifiable output
- Reference specific files or components when known

**Step 3.6: Extract technical context from architecture**
Pull relevant information into the story's Dev Notes section. Only include what directly applies to this specific story. Cite the source document for each technical detail.

### Phase 4: Dependency Mapping

After creating all stories, identify dependencies:

1. **Hard dependencies**: Story B cannot start until Story A is done (e.g., user profile page requires authentication story)
2. **Soft dependencies**: Story B is easier after Story A (can run in parallel but better sequential)
3. **Parallel candidates**: Stories with no dependency relationship

Document dependencies explicitly in each story file.

### Phase 5: Priority Ordering

Order stories within each epic and across epics:

**Priority criteria:**
1. **Technical foundation first** — database schemas, auth, shared utilities
2. **Core value second** — primary features users signed up for
3. **Enhancement third** — secondary features, polish, settings
4. **Infrastructure last** — monitoring, admin tools, non-user-facing

### Phase 6: Story File Creation

Create each story file at: `docs/stories/<epic-id>/<story-id>.md`

Example: `docs/stories/epic-1/story-1.1.md`

Use the story format below.

## Story File Format

```markdown
# Story N.M: [Title]

**Status**: draft | ready | in-progress | done
**Epic**: [Epic name]
**Priority**: High | Medium | Low
**Size**: S | M | L | XL
**Depends on**: [story-N.M, story-N.K] or "none"

## User Story

As a [user type], I want [feature] so that [benefit].

## Acceptance Criteria

- [ ] Given [context], when [action], then [outcome]
- [ ] Given [context], when [action], then [outcome]
- [ ] Given [context], when [action], then [outcome]

## Technical Tasks

- [ ] Task 1: [Specific action] (AC: 1)
  - [ ] Subtask 1.1: [Details]
  - [ ] Subtask 1.2: [Details]
- [ ] Task 2: [Specific action] (AC: 2, 3)
  - [ ] Subtask 2.1: [Details]
- [ ] Task 3: Write tests for [specific functionality]

## Dev Notes

> Everything a developer needs to implement this story. Do not invent details — only include what comes from architecture documents.

### Relevant Files
[List specific files to create or modify, with paths from architecture docs]

### Data Models
[Relevant schemas, field types, validation rules — cite source]

### API Endpoints
[Endpoints to implement or consume — cite source]

### Technical Constraints
[Version requirements, performance notes, security rules — cite source]

### Testing Requirements
[Test types required, frameworks to use, coverage expectations — cite source]

## Notes

[Any clarifying notes, edge cases to handle, or open questions]
```

See [references/story-format.md](references/story-format.md) for detailed examples and variations.

## Definition of Ready (DoR) Checklist

A story is "ready" for implementation when all items pass:

**Clarity:**
- [ ] User story statement is unambiguous (specific user type, specific action, concrete benefit)
- [ ] Acceptance criteria are measurable — pass/fail is objectively determinable
- [ ] No acceptance criterion requires subjective judgment ("looks good", "feels fast")

**Completeness:**
- [ ] All acceptance criteria have corresponding tasks
- [ ] Dev Notes include relevant technical details from architecture
- [ ] File paths for new/modified files are specified
- [ ] Dependencies on other stories are listed

**Feasibility:**
- [ ] Story is sized S, M, or L (XL must be split)
- [ ] No unresolved external blockers (missing API keys, pending decisions)
- [ ] Technical approach is clear from Dev Notes

**Testing:**
- [ ] Testing approach is specified (unit, integration, e2e)
- [ ] At least one test scenario per acceptance criterion

If any item fails, revise the story before marking it "ready".

## Epic Summary Output

After creating all stories, provide a summary:

```
## Backlog Summary

Epic 1: [Name] — N stories, estimated [S/M/L mix]
  - story-1.1: [Title] (S) — Ready
  - story-1.2: [Title] (M) — Ready
  - story-1.3: [Title] (L) — Ready

Epic 2: [Name] — N stories
  ...

Total: [N] stories across [N] epics
Recommended implementation order: [ordered list with dependency rationale]
```

## Common Pitfalls to Avoid

**Story writing:**
- ❌ "As a user, I want to manage my account" (too vague — split into specific features)
- ✅ "As an authenticated user, I want to update my display name so that my profile reflects my preferred name"

**Acceptance criteria:**
- ❌ "The form validates correctly" (not testable as written)
- ✅ "Given an empty email field, when the user submits the form, then an error message 'Email is required' appears below the email field"

**Technical tasks:**
- ❌ "Implement the backend" (not actionable)
- ✅ "Create POST /api/users endpoint that accepts {email, name} and returns {id, email, name, createdAt}"

**Dev Notes:**
- ❌ Inventing library names, API patterns, or file paths not in architecture docs
- ✅ Only including details with a citation: `[Source: docs/architecture/api.md#authentication]`

## Additional Resources

- [references/story-format.md](references/story-format.md) — Detailed story format guide with full examples
- [references/acceptance-criteria-guide.md](references/acceptance-criteria-guide.md) — How to write testable Given/When/Then criteria

## Claude Code Enhanced Features

This skill includes the following Claude Code-specific enhancements:

## Scope

$ARGUMENTS

If no argument provided, create stories for ALL epics derived from the architecture document.
If argument is an epic name (e.g., "authentication"), create stories only for that epic.

## Progress Tracking

Use TaskCreate to track story creation:

```
TaskCreate: "Identify epics from architecture" → analyze docs/architecture.md
TaskCreate: "Create Epic 1 stories" → one task per epic
TaskCreate: "Validate story completeness" → final review pass
```

## Input Files

Always read both before creating stories:
- `docs/project-brief.md` — for understanding user types and business goals
- `docs/architecture.md` — for understanding technical scope and data models

## Story File Management

Create story files at: `docs/stories/<epic-slug>/story-<N>.<M>.md`

Use Glob to check existing stories and avoid duplicates:
```
Glob: "docs/stories/**/*.md"
```

Use Read to load existing stories when adding to an epic.

## Dependency Mapping

After creating all stories, use Write to create a dependency overview:
`docs/stories/README.md` — table of epics, story count, and dependency order

## Quality Gate (Stop Hook)

When you attempt to stop, an automated agent verifies:
- At least 1 epic directory exists under docs/stories/
- Each story file has User Story, Acceptance Criteria, and Technical Tasks
- No story has empty acceptance criteria

**Blocked example:**
```
⚠️ Story validation failed:
- docs/stories/epic-1/story-1.2.md: Missing acceptance criteria
- docs/stories/epic-2/story-2.1.md: User story statement is empty
Cannot complete until all stories have required sections.
```
