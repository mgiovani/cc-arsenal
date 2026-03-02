---
# Enhancement for: forge-brief
disable-model-invocation: false
argument-hint: "<project_idea>"
allowed-tools: "Read, Write, Edit, Bash, Grep, Glob, Task, TaskCreate, TaskUpdate, WebFetch, WebSearch, AskUserQuestion, EnterPlanMode"
hooks:
  Stop:
  - hooks:
    - type: agent
      prompt: |
        Verify the project brief is complete before stopping:

        1. Check that docs/project-brief.md exists and is non-empty
        2. Verify it contains ALL required sections:
           - Executive Summary
           - Problem Statement & Target Users
           - Proposed Solution & Key Features
           - Competitive Landscape (at least 2 competitors analyzed)
           - Technical Constraints & Preferences
           - Success Metrics
           - Out of Scope
        3. Check that each section has substantive content (not just headers)

        If any section is missing or empty, report what is incomplete and return decision: block.
        Only allow stopping when the brief is complete and all sections are filled.
      timeout: 60
---

## Claude Code Enhanced Features

This skill includes the following Claude Code-specific enhancements:

## Project Idea

$ARGUMENTS

## Progress Tracking

Use TaskCreate to track the brief creation workflow:

```
TaskCreate: "Elicit project requirements" → in_progress while asking questions
TaskCreate: "Research competitive landscape" → for competitor research phase
TaskCreate: "Draft project brief" → for writing docs/project-brief.md
TaskCreate: "Review and finalize brief" → final review pass
```

## Research Enhancement

Use WebSearch to enrich competitive analysis:

```
WebSearch: "[product category] competitors 2026"
WebSearch: "[target market] SaaS tools comparison"
WebSearch: "[problem domain] market size 2026"
```

Use WebFetch to read competitor websites and extract positioning, pricing, and key features.

## Quality Gate (Stop Hook)

When you attempt to stop, an automated agent verifies:
- `docs/project-brief.md` exists and has all required sections
- Each section contains substantive content (not placeholder text)
- Competitive landscape includes at least 2 real competitors with analysis

**Blocked example:**
```
⚠️ Brief incomplete:
- Missing: Technical Constraints & Preferences (empty section)
- Missing: Success Metrics (only header, no content)
Cannot complete until all sections are filled.
```

## Parallel Research Pattern

For thorough competitive analysis, run parallel research:

```
Spawn 2 parallel Task agents:
  Agent 1: Research top 3 direct competitors (features, pricing, positioning)
  Agent 2: Research market size, trends, and target user pain points

Merge findings into Competitive Landscape section.
```
