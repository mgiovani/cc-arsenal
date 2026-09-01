---
name: docs-rfc
description: Create a numbered RFC (Request For Comments) document proposing a
  change and opening it for team discussion, using minimal/standard/detailed
  templates. Trigger on "write an RFC", "draft a proposal for X", "document this
  change before we build it", or "get feedback on this design". Not for recording
  a decision that's already made (use docs-adr), RFCs propose and stay open for
  discussion, ADRs record a choice that happened.
metadata:
  author: mgiovani
  version: 1.1.0
disable-model-invocation: true
argument-hint: <title> [variant]
allowed-tools: Read, Write, Grep, Glob, Bash(git *), Task
---

# Create request for comments

Create a new RFC document proposing and discussing a change.

## Anti-Hallucination guidelines

RFCs propose changes to real systems, so ground every claim before writing:

1. **Verify current state**: explore the codebase to understand what exists today
2. **Reference actual code**: don't invent APIs or patterns; find real examples
3. **Check dependencies**: confirm libraries/tools mentioned actually exist in the project
4. **Validate assumptions**: each claim about current state must be verified

## Workflow

### Phase 1: explore and gather context

Understand the codebase before writing anything. If the Task tool is available,
use the Explore agent:

```
Use Task tool with Explore agent:
- prompt: "Analyze the codebase to understand [RFC_TOPIC]. Find: 1) Current implementation patterns, 2) Related components and their interactions, 3) Existing similar features, 4) Technical constraints. Return verified findings with file paths."
- subagent_type: "Explore"
```

No Task tool available: explore directly with `grep`/`glob`/`read` before writing,
covering the same four questions (current patterns, related components, existing
similar features, technical constraints). Either way, keep what you find: it feeds
the Background and Detailed Design sections in Phase 6.

### Phase 2: parse arguments

1. Extract proposal title from `$ARGUMENTS`
2. Check for a variant keyword: `minimal`, `standard`, or `detailed`
3. If a variant is found, remove it from the title
4. Default variant: `standard`

### Phase 3: determine RFC number

- Scan `docs/rfc/` for existing files matching `RFC-XXXX-*`
- Increment the highest number by 1 (start at `0001` if none exist)
- Format as a 4-digit padded number (e.g. `0001`, `0023`)

### Phase 4: sanitize title for filename

Convert the title to kebab-case, lowercase, special characters stripped.
Example: "Add GraphQL API Support" -> `add-graphql-api-support`

### Phase 5: get author information

Run `git config user.name`, falling back to `"Development Team"` if empty.

### Phase 6: load and populate template

Template location: `assets/templates/`, select based on variant:

- `minimal` -> `minimal.md`: Summary, Motivation, Proposal, Open Questions. Use for small changes.
- `standard` -> `standard.md` (default): adds Rationale and Alternatives, Implementation Plan, Testing Plan, Migration Strategy, Timeline. Use for most feature proposals.
- `detailed` -> `detailed.md`: full set including Goals/Non-Goals, Security Considerations, Performance Implications, Monitoring and Metrics. Use for major/architectural changes.

Draft real content for every `{{PLACEHOLDER}}` present in the selected template:
each variant has its own set (metadata fields, body sections, risk tables,
alternatives, review history, and so on). Base each one on the Phase 1 findings
or on explicit reasoning about the proposal; never leave a placeholder token
literally in the output. The written RFC must contain zero unresolved
`{{...}}` tokens.

### Phase 7: create RFC file

- Filename: `docs/rfc/RFC-XXXX-kebab-case-title.md`
- Ensure `docs/rfc/` exists, write populated content, set status to "Draft"

### Phase 8: report creation

Show the RFC number, title, file path, and next-step guidance (share for feedback,
update status as it progresses).

## Usage examples

```
docs-rfc "Add GraphQL API Support"
docs-rfc minimal "Update Logging Format"
docs-rfc detailed "Migration to Microservices Architecture"
```

## RFC status lifecycle

`Draft` -> `In Review` -> `Accepted` / `Rejected` (or `Withdrawn` at any point,
`Implemented` after accepted work ships). Update the status field as the RFC moves
through review.

## Good practices

- Write the RFC before starting implementation, not after
- Include concrete examples and real code references, not hypotheticals
- Document alternatives considered and why they were rejected
- Link related ADRs, issues, or other RFCs
- Keep it updated as a living document during review
