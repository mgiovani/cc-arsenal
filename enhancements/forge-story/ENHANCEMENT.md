---
# Enhancement for: forge-story
disable-model-invocation: false
argument-hint: "[epic_name_or_all]"
allowed-tools: "Read, Write, Edit, Bash, Grep, Glob, Task, TaskCreate, TaskUpdate, AskUserQuestion"
hooks:
  Stop:
  - hooks:
    - type: agent
      prompt: |
        Verify stories are complete and ready before stopping:

        1. Check that docs/stories/ directory exists with at least one epic subdirectory
        2. For each story file found (docs/stories/**/*.md):
           - Verify it has a User Story section ("As a ... I want ... so that ...")
           - Verify it has Acceptance Criteria with at least 2 Given/When/Then items
           - Verify Status is set (draft, ready, in-progress, or done)
           - Verify it has at least 2 Technical Tasks listed
        3. Check that stories are numbered and organized by epic (e.g., docs/stories/epic-1/story-1.1.md)

        Count total stories created and report. If any story is missing required sections, list them.
        Block only if stories have empty acceptance criteria or missing user story statements.
      timeout: 60
---

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
