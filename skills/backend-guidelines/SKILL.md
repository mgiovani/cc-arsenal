---
name: backend-guidelines
description: "Python backend defaults for FastAPI services on Postgres: Pydantic v2 schemas separate from ORM models, pydantic-settings config, layering enforced with import-linter, append-only migrations, full annotations checked by ty, ruff, uv, logging and Logfire, DBOS durable workflows and Pydantic AI agents. Use when writing or changing backend Python (routes, services, schemas, settings, queries, workflows, agent code) and the project has no stricter rule, or when asked how to structure a Python API. Not for language-agnostic rules (use code-guidelines), React or CSS work (use frontend-guidelines), creating or running a migration (use db-migrate), a security audit (use review-security) or a performance audit (use review-perf)."
metadata:
  summary: "Owner's Python, FastAPI and Postgres defaults: schemas, layering, migrations, typing, workflows, agents"
---

# Backend Guidelines

The project's own AGENTS.md or CLAUDE.md and its lint config win over this skill. Apply these rules only where the project is silent, and say so when you follow a project rule that differs.

Apply the `code-guidelines` skill first: use the `Skill` tool where available, otherwise read its SKILL.md and the references it routes to, and announce it with a `Using code-guidelines for the language-agnostic rules` line. This skill holds only what is specific to the backend and repeats none of it.

Before the first edit, read the project's instruction files, `pyproject.toml` (ruff, ty, pytest and import-linter sections) and one existing module of the kind you are adding. Find the real lint and test commands in the task runner (`justfile`, `Makefile`).

## Pick the reference

| What you are doing | Read |
|---|---|
| Adding a route, a request or response model, a dependency, a cursor | [references/api-and-schemas.md](references/api-and-schemas.md) |
| Creating a package, deciding where code goes, drawing an import boundary | [references/layering.md](references/layering.md) |
| Writing a table, a query, a transaction or a migration | [references/database-and-migrations.md](references/database-and-migrations.md) |
| Adding a setting, a secret, an entry point or a test environment | [references/config-and-secrets.md](references/config-and-secrets.md) |
| Annotating code, tuning ruff, ty or pytest, choosing tools | [references/typing-and-lint.md](references/typing-and-lint.md) |
| Adding a log line, a span, a metric or a request id | [references/observability.md](references/observability.md) |
| Writing a background job, a queue, a schedule or a restart path | [references/durable-workflows.md](references/durable-workflows.md) |
| Building or testing an LLM agent, a tool or an output model | [references/ai-agents.md](references/ai-agents.md) |

Read one reference per task. Read a second only when the task crosses both topics, such as an agent that runs inside a workflow.

## Rules for every task

1. Put a Pydantic v2 model at every boundary: request, response, event, config and model output. Keep it a separate class from the ORM model. One class that is both couples the wire format to the table, and a column change then breaks clients.
2. Load config through `pydantic-settings` into one settings object built at startup. Code that reads `os.environ` in the middle of a request makes tests and deploys disagree.
3. Keep models and services free of the web framework. They never import `fastapi`, `starlette` or a workflow engine. Enforce it with an import-linter contract, and extend the contract in the same change that adds a package.
4. Append a migration and never edit a merged one. A fix is a new revision at the end of the chain.
5. Annotate every function and every variable whose type is not obvious. Write no `Any`, no `type: ignore`, no `ty: ignore` and no `cast` that only silences an error. When a third-party stub forces one, stop and report it.
6. Use uv for environments and commands, ruff for lint and format, ty for types. Run them through the project's task runner, never from memory.
7. Never block the event loop. Inside `async def`, call only async clients. For blocking work, write a plain `def` and let the framework run it in a threadpool.
8. Verify before you call the work done: lint, format check, ty, import-linter and the tests, plus a real Postgres run for any change that touches SQL. Report counts and exit codes from the run.

## Where defaults differ between projects

Three choices vary between the owner's repos. Use the default below, and defer to what the project's config or existing code does.

- Complexity caps: set none yourself. Obey the caps the project's ruff config sets, and fix the code rather than the cap.
- Entities: a frozen slotted dataclass inside the domain, a Pydantic model at the edge. Some projects use one `BaseModel` for entities as well. Match the module you are editing.
- Test docstrings: none by default, as code-guidelines says. Use the project's requirement marker where it has one, and a one-line id docstring only where the project does that instead.

The other disagreements, such as module file names, are settled inside the references.

## When the task is unclear

For a vague request, build the smallest route-service-schema slice that works and name what you left out. Ask before adding a dependency, a new top-level package or a change to a pinned tool range.
