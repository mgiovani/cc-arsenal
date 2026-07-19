---
name: docs-diagram
description: Generate a Mermaid diagram (ER, architecture, deployment, or security)
  by reading the actual codebase and writing it to docs/. Use for requests like
  "draw an ER diagram of these tables", "show me the architecture", "diagram the
  deployment setup", "visualize the security data flow", or "generate a system
  diagram". Not for scaffolding a new docs directory structure (use docs-init),
  syncing existing prose docs with code changes (use docs-update), or recording a
  design decision's rationale (use docs-adr) — this skill only produces diagrams
  generated from code.
metadata:
  author: mgiovani
  version: 1.1.1
disable-model-invocation: true
argument-hint: <type> [context]
allowed-tools: Read, Write, Grep, Glob, Task
context: fork
agent: general-purpose
---

# Generate System Diagrams

Generate a Mermaid diagram — ER, architecture, deployment, or security — from the
real codebase and write it to `docs/`.

## Supported Diagram Types

| Type | Output File | Description |
|------|------------|-------------|
| `er` | `docs/data-model.md` | Entity-Relationship diagram from database models |
| `arch` | `docs/architecture.md` | System architecture and component relationships |
| `deployment` | `docs/deployment.md` | Deployment infrastructure and CI/CD |
| `security` | `docs/security.md` | Security architecture and data flow |

## Workflow

### 1. Parse the request

Extract the diagram type (`er`, `arch`, `deployment`, `security`) and any optional
scope context (e.g. "for the user and order tables"). If the type is missing or
invalid, don't guess — stop, and end your response with a direct question naming
the supported types, e.g. "Which diagram type do you want: architecture, er,
deployment, or security?". Listing the types without asking, or asking without
listing them, is not enough — go no further until the user answers.

### 2. Analyze the codebase

- **Scoped request** (e.g. "er diagram for the user and order tables"): Read/Grep
  the named files directly.
- **Broad or ambiguous request** (e.g. "show me the architecture" on an unfamiliar
  codebase): when a Task tool is available, spawn one Explore subagent per aspect
  that matters for the diagram type (e.g. for `arch`: services, databases,
  external integrations, data flow). Without a Task tool, run the same per-aspect
  checks sequentially inline with Read/Grep/Glob instead — same checks, no
  parallelism, just slower.

See [references/detection-patterns.md](references/detection-patterns.md) for
detection commands per diagram type.

### 3. Verify before adding anything

Diagrams must represent real, existing components — never a plausible guess.

- Read the file that defines a component before adding it; don't add it from
  memory or inference.
- Confirm a relationship by finding the actual import/reference/FK in code, not
  by assuming two similarly-named things are connected.
- Get counts by running a command (e.g. `find . -name "*service*" | wc -l`), then
  use that number — never estimate "about 5 services".
- Drop anything that can't be verified this way. An empty directory or an unused
  stub file is not a component.

### 4. Generate the Mermaid diagram

Use the syntax for the diagram type from
[references/mermaid-patterns.md](references/mermaid-patterns.md). Keep it
readable — if a system has too many pieces for one clear diagram, split it into
multiple focused views rather than cramming everything into one.

### 5. Populate the template

Load `assets/templates/<type>.md` (`er` → `data-model.md`, `arch` →
`architecture.md`, `deployment` → `deployment.md`, `security` → `security.md`).
Replace `{{PROJECT_NAME}}`, `{{DATE}}`, the diagram placeholder, and the
entity/component list placeholders with the verified content from steps 3-4.

### 6. Write the output

Write to the file in `docs/` named in the table above. If it already exists, ask
before overwriting, and preserve any hand-written sections you can identify
(anything outside the placeholder fields).

### 7. Report results

State the diagram type, the output file, and the actual counts detected (e.g.
"4 entities, 6 relationships") — these must be the numbers from step 3's
commands, not a summary written from memory. Suggest regenerating when the
diagrammed subsystem changes.

## Worked Examples

**Scoped ER request** — `docs-diagram er for the user and order tables`: Grep for
`class User` / `class Order` in the ORM models directory, read both files, extract
columns and FKs, confirm the `Order.user_id` FK by checking it's actually declared
in the model, then write `docs/data-model.md` with an `erDiagram` block containing
only `USER` and `ORDER`.

**Broad architecture request** — `docs-diagram arch`: with a Task tool, spawn
Explore agents for services, databases, and external integrations; without one,
run `find . -name "*service*"`, `find . -name "*.config.*"`, and a grep for known
client SDKs sequentially. Merge only the components every check confirms into one
`graph TB` diagram.

**Missing/invalid type** — `docs-diagram`: do not guess a type or generate
anything; end the response with "Which diagram type do you want: architecture,
er, deployment, or security?" alongside their output files.

## Notes

- Regenerate after the diagrammed subsystem changes (schema migration, new
  service, new deploy target, new auth flow) — this skill is meant to be re-run,
  not written once and left stale.
- Additional context on codebase detection commands and Mermaid syntax lives in
  [references/detection-patterns.md](references/detection-patterns.md) and
  [references/mermaid-patterns.md](references/mermaid-patterns.md) — load them
  when doing the actual detection/generation work, not before.
