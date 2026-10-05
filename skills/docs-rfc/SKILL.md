---
name: docs-rfc
description: Create a numbered RFC (Request For Comments) document proposing a
  change and opening it for team discussion, using minimal/standard/detailed
  templates. Trigger on "write an RFC", "draft a proposal for X", "document this
  change before we build it", or "get feedback on this design". Not for recording
  a decision that's already made (use docs-adr), RFCs propose and stay open for
  discussion, ADRs record a choice that happened.
metadata:
  summary: "Request for Comments documentation"
  author: mgiovani
  version: 1.1.0
disable-model-invocation: true
argument-hint: <title> [variant]
---

# Create request for comments

Create a new RFC document proposing and discussing a change.

## Anti-hallucination guidelines

RFCs propose changes to real systems, so ground every claim before writing:

1. Verify current state: explore the codebase to understand what exists today.
2. Reference actual code: don't invent APIs or patterns, find real examples.
3. Check dependencies: confirm libraries/tools mentioned actually exist in the project.
4. Validate assumptions: each claim about current state must be verified.

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
the Background and Detailed Design sections in Phase 2.

### Phase 2: fill the template

Copy this checklist and tick each step:

```
- [ ] Parse `$ARGUMENTS`: title, plus an optional variant keyword (`minimal`, `standard`, `detailed`); remove the keyword from the title; default `standard`
- [ ] Number: scan `docs/rfc/` for `RFC-XXXX-*`, add 1 to the highest (start at `0001`), 4-digit padded
- [ ] Slug: kebab-case the title, lowercase, special characters stripped ("Add GraphQL API Support" -> `add-graphql-api-support`)
- [ ] Author: `git config user.name`, falling back to `"Development Team"` if empty
- [ ] Load the variant template from `<skill-dir>/assets/templates/` and draft real content for every `{{PLACEHOLDER}}` from the Phase 1 findings or explicit reasoning
- [ ] Write `docs/rfc/RFC-XXXX-kebab-case-title.md` (create `docs/rfc/` if missing) with status "Draft"
- [ ] Run the leftover-token check below; fix and re-run until it prints nothing
```

Variants:

- `minimal` -> `minimal.md`: Summary, Motivation, Proposal, Open Questions. Use for small changes.
- `standard` -> `standard.md` (default): adds Rationale and Alternatives, Implementation Plan, Testing Plan, Migration Strategy, Timeline. Use for most feature proposals.
- `detailed` -> `detailed.md`: full set including Goals/Non-Goals, Security Considerations, Performance Implications, Monitoring and Metrics. Use for major/architectural changes.

Each variant has its own placeholder set (metadata fields, body sections, risk
tables, alternatives, review history, and so on). Never leave a placeholder
token literally in the output.

Leftover-token check, run on the file just written:

```bash
grep -nE '\{\{|\}\}|TODO|TBD' docs/rfc/RFC-XXXX-kebab-case-title.md
```

Every hit is an unfilled placeholder or an unfinished draft: draft the content
and re-run. After 3 rounds, stop and report what still matches.

### Phase 3: report creation

Show the RFC number, title, file path, and next-step guidance (share for feedback,
update status as it progresses). This is the last step; nothing downstream
consumes this report beyond the person reading it.

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
