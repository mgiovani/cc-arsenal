---
name: docs-rfc
description: Create a numbered RFC (Request For Comments) document proposing and
  documenting a change, using minimal/standard/detailed templates. Use when the user
  asks to write a proposal, draft an RFC, or formally document a proposed change
  before implementation. Not for recording a decision already made (use docs-adr
  for that) — RFCs propose, ADRs record.
metadata:
  author: mgiovani
  version: 1.0.0
disable-model-invocation: true
argument-hint: <title> [variant]
allowed-tools: Read, Write, Grep, Glob, Bash(git *), Task
---

# Create Request For Comments

Create a new RFC document for proposing and discussing a change.

## Anti-Hallucination Guidelines

RFCs propose changes to real systems, so ground every claim before writing:

1. **Verify current state** — explore the codebase to understand what exists today
2. **Reference actual code** — don't invent APIs or patterns; find real examples
3. **Check dependencies** — confirm libraries/tools mentioned actually exist in the project
4. **Validate assumptions** — each claim about current state must be verified

## Workflow

### Phase 1: Explore Current State

Use the Explore agent to understand the codebase before writing anything:

```
Use Task tool with Explore agent:
- prompt: "Analyze the codebase to understand [RFC_TOPIC]. Find: 1) Current implementation patterns, 2) Related components and their interactions, 3) Existing similar features, 4) Technical constraints. Return verified findings with file paths."
- subagent_type: "Explore"
```

### Phase 2: Parse Arguments

1. Extract proposal title from `$ARGUMENTS`
2. Check for a variant keyword: `minimal`, `standard`, or `detailed`
3. If a variant is found, remove it from the title
4. Default variant: `standard`

### Phase 3: Determine RFC Number

- Scan `docs/rfc/` for existing files matching `RFC-XXXX-*`
- Increment the highest number by 1 (start at `0001` if none exist)
- Format as a 4-digit padded number (e.g. `0001`, `0023`)

### Phase 4: Sanitize Title for Filename

Convert the title to kebab-case, lowercase, special characters stripped.
Example: "Add GraphQL API Support" -> `add-graphql-api-support`

### Phase 5: Gather Context

Analyze the codebase to identify relevant files, patterns, similar implementations,
and technical constraints. Useful searches:

```bash
# API changes
find . -name "*router*" -o -name "*controller*" -o -name "*api*" | head -10

# Feature additions
grep -r "export.*function\|export.*class" --include="*.ts" --include="*.js" . | head -20

# Infrastructure changes
find . -name "*.yml" -o -name "*.yaml" -o -name "Dockerfile" | head -10

# Performance changes
grep -r "cache\|redis\|memcache\|performance" --include="*.py" --include="*.ts" . | head -15
```

### Phase 6: Get Author Information

Run `git config user.name`, falling back to `"Development Team"` if empty.

### Phase 7: Load and Populate Template

Template location: `assets/templates/` — select based on variant:

- `minimal` -> `minimal.md` — Summary, Motivation, Proposal, Open Questions. Use for small changes.
- `standard` -> `standard.md` (default) — adds Rationale and Alternatives, Implementation Plan, Testing Plan, Migration Strategy, Timeline. Use for most feature proposals.
- `detailed` -> `detailed.md` — full set including Goals/Non-Goals, Security Considerations, Performance Implications, Monitoring and Metrics. Use for major/architectural changes.

Replace placeholders:
- `{{RFC_NUMBER}}` — 4-digit number
- `{{RFC_TITLE}}` — original title (Title Case)
- `{{DATE}}` — current date (YYYY-MM-DD)
- `{{AUTHOR}}` — git user name or "Development Team"
- `{{CONTEXT}}` — gathered context from codebase
- `{{PROJECT_NAME}}` — git repo or directory name

### Phase 8: Create RFC File

- Filename: `docs/rfc/RFC-XXXX-kebab-case-title.md`
- Ensure `docs/rfc/` exists, write populated content, set status to "Draft"

### Phase 9: Report Creation

Show the RFC number, title, file path, and next-step guidance (share for feedback,
update status as it progresses).

## Usage Examples

```
docs-rfc "Add GraphQL API Support"
docs-rfc minimal "Update Logging Format"
docs-rfc detailed "Migration to Microservices Architecture"
```

## RFC Status Lifecycle

`Draft` -> `In Review` -> `Accepted` / `Rejected` (or `Withdrawn` at any point,
`Implemented` after accepted work ships). Update the status field as the RFC moves
through review.

## Good Practices

- Write the RFC before starting implementation, not after
- Include concrete examples and real code references, not hypotheticals
- Document alternatives considered and why they were rejected
- Link related ADRs, issues, or other RFCs
- Keep it updated as a living document during review
