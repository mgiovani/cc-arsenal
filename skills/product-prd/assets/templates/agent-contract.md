<!-- template: agent-contract: OPTIONAL companion for when the PRD's downstream
     reader is an AI implementation agent (implement-feature / fix-bug / team-implement)
     rather than a human. Emit only in AI-agent-consumer mode. Keep it factual and
     command-level. -->

# Agent Contract: {{PRODUCT}}

Companion to PRD.md for an AI implementation agent. Headings + lists only, no
prose paragraphs: every item independently checkable.

## Commands (exact, with flags)

<!-- The real commands the agent runs, copy-pasteable. -->
- Install: `{{INSTALL_CMD}}`
- Test: `{{TEST_CMD}}`
- Lint: `{{LINT_CMD}}`
- Run: `{{RUN_CMD}}`

## Boundaries: three tiers

**Always (do without asking)**
- {{ALWAYS_1}}

**Ask first (confirm before doing)**
- {{ASK_FIRST_1}}

**Never (hard stop)**
- {{NEVER_1}}

## Project conventions

<!-- Concrete, testable conventions the agent must follow. -->
- {{CONVENTION_1}}

## Definition of done

<!-- Each an independently-testable acceptance criterion, tracing to a PRD-FR ID. -->
- [ ] {{DoD_1}} (satisfies {{REQ_ID}})
