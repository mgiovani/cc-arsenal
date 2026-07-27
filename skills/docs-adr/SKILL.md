---
name: docs-adr
description: Create a numbered Architecture Decision Record (ADR) documenting a technical
  decision with context, alternatives, and consequences. Trigger on "create an ADR",
  "document this architectural decision", "record why we chose X", or "write an ADR
  for [decision]". Not for a decision still open for discussion (use docs-rfc, RFCs
  propose, ADRs record) and not for bootstrapping a project's whole docs/ tree from
  scratch (use docs-init).
metadata:
  author: mgiovani
  version: 1.1.0
disable-model-invocation: true
argument-hint: <title> [variant]
allowed-tools: Read, Write, Grep, Glob, Task
context: fork
agent: general-purpose
---

# Create Architecture Decision Record

Create a new Architecture Decision Record (ADR) documenting an architectural decision.

## Anti-Hallucination Guidelines

ADRs document real decisions about real code: every claim in the ADR must be verifiable
in the repo, not assumed. Before writing:

1. **Verify the technology exists**: if the ADR mentions "Redis", confirm Redis is
   actually used somewhere in the codebase.
2. **Reference actual files**: grep/glob to find real file paths; never invent one.
3. **Quote real code**: if citing a pattern, find an actual example of it.
4. **Check current state**: the Context section must reflect verified reality, not a
   plausible-sounding guess.

## Workflow

### Phase 1: Parse Arguments

1. Extract the decision title from the command arguments. If no title was given, stop
   here and ask the user for one (and optionally which variant): don't invent a
   placeholder title or proceed to the later phases.
2. Check for a variant keyword as the leading token: `lightweight`, `full`, or `nygard`.
   A matching word inside the title itself (e.g. "Full-Text Search") is not a variant
   keyword, only strip it when it's a standalone token preceding the title.
3. If a variant keyword is found, strip it from the title.
4. Default variant: `nygard`.

### Phase 2: Determine ADR Number

- Scan `docs/adr/` for files matching `XXXX-*`.
- Find the highest existing number and increment by 1 (start at `0001` if none exist).
- Format as a 4-digit zero-padded number (e.g. `0001`, `0023`).

### Phase 3: Sanitize Title for Filename

Convert the title to kebab-case, lowercase, special characters stripped.
Example: "Use Redis for Caching" -> `use-redis-for-caching`.

### Phase 4: Gather Context

Use the Task tool with the Explore agent, when available, to search the codebase for
the decision topic: current implementation (if any), related config files, dependencies
involved, and existing documentation. Ask it to return verified file paths and relevant
snippets, not summaries it can't back up.

If the Task tool isn't available, run the equivalent searches directly instead:
e.g. `grep -rn "<topic>"` across source files, `find . -name "*.config.*"` or
`docker-compose.yml` for infra-flavored decisions, `find . -name "*schema*" -o -name
"*models*"` for data-layer decisions. Either path, only include context you actually
found; an ADR with no verifiable context is a red flag, not something to pad with
plausible-sounding filler.

### Phase 5: Load and Populate Template

- Templates live in `assets/templates/`: `nygard.md` (default), `lightweight.md`, `full.md`.
- Load the selected template and grep it for every `{{TOKEN}}` placeholder it actually
  contains, the three templates use different token sets (e.g. nygard has `{{CONTEXT}}`;
  lightweight has `{{PROBLEM}}`, `{{DECISION}}`, `{{ALTERNATIVES}}`, `{{CONSEQUENCES}}`,
  `{{NOTES}}`; full has a longer set including `{{AUTHORS}}`, `{{STAKEHOLDERS}}`,
  `{{OPTION_1_NAME}}`, etc.). Don't assume a fixed list: fill whatever the loaded
  template actually contains.
- `{{ADR_NUMBER}}`, `{{ADR_TITLE}}`, and `{{DATE}}` (YYYY-MM-DD) appear in all three;
  fill those from Phases 1-3 regardless of variant.
- After substitution, scan the rendered output for any leftover `{{...}}`: zero
  unresolved tokens before writing the file.

### Phase 6: Create ADR File

- Filename: `docs/adr/XXXX-kebab-case-title.md`.
- Create `docs/adr/` if it doesn't exist.
- Write the populated content with initial Status set to "Proposed".

### Phase 7: Report Creation

Report the ADR number, title, and file path, plus next steps (e.g. review with the team,
flip Status to Accepted once approved).

## Template Variants

| Variant | Sections | Use when |
|---|---|---|
| **nygard** (default) | Status, Context, Decision, Consequences | Most decisions, balanced detail |
| **lightweight** | Status, Decision, Rationale | Simple, straightforward decisions |
| **full** | Status, Context, Decision Drivers, Considered Options, Decision, Consequences (Positive/Negative/Neutral), Pros and Cons, Related Decisions, References | Complex, high-impact decisions |

## Usage Examples

```
docs-adr "Database Migration Strategy"
```
-> `docs/adr/0004-database-migration-strategy.md` (nygard, next available number).

```
docs-adr lightweight "Use Redis for Session Storage"
```
-> strips "lightweight", verifies Redis is actually referenced in the repo, writes
`docs/adr/0005-use-redis-for-session-storage.md` with just Status/Decision/Rationale.

```
docs-adr full "Adopt Event-Driven Architecture"
```
-> writes the full variant with Considered Options and split Consequences, citing real
messaging/event code found during context gathering.

## ADR Numbering & Status Lifecycle

- First ADR is conventionally `0001-record-architecture-decisions.md` (meta-ADR);
  subsequent ones auto-increment.
- Status progresses: **Proposed** (default on creation) -> **Accepted** ->
  **Deprecated** or **Superseded** (by a later ADR, which should link back to this one).

## Notes

- One decision per ADR: split unrelated decisions into separate records.
- Write in imperative language ("we will", not "we should").
- Document the real reasons a decision was made, including trade-offs and downsides,
  not the idealized version.
- Cross-link: reference related or superseded ADRs by number.
