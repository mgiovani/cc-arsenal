---
name: inject-docs
description: Inject framework-specific best practices into CLAUDE.md. Supports Next.js
  and FastAPI.
metadata:
  author: mgiovani
  version: 1.0.0
  source: https://github.com/mgiovani/skills
disable-model-invocation: true
---

# Inject Docs

> **Cross-Platform AI Agent Skill**
> This skill works with any AI agent platform that supports the skills.sh standard.

# Framework Documentation Injector

Inject compressed framework-specific best practices and documentation into the current project's CLAUDE.md or AGENTS.md file. This gives AI coding agents passive access to framework knowledge without requiring tool calls or skills.

## Supported Frameworks

| Framework | Detection Method | Documentation Source |
|-----------|-----------------|---------------------|
| **Next.js** | `next` in package.json | Vercel's agents-md codemod (version-aware) |
| **FastAPI** | `fastapi` in requirements.txt/pyproject.toml | zhanymkanov/fastapi-best-practices |

## Anti-Hallucination Guidelines

**CRITICAL**:
1. **Auto-detect the framework** before running anything - check project files to identify the framework
2. **Do NOT assume tools are available** - verify Node.js/Python tooling exists based on framework
3. **Do NOT claim success** until verifying the target file exists and contains actual content
4. **Read actual output** - report what the commands say, not what is expected

## Implementation Workflow

### Phase 0: Framework Detection & Validation (REQUIRED)

Before running anything, auto-detect the framework and verify prerequisites:

1. **Detect the framework**:
 - Check for `package.json` with `next` dependency → Next.js project
 - Check for `pyproject.toml` with `fastapi` dependency → FastAPI project
 - Check for `requirements.txt` containing `fastapi` → FastAPI project
 - If multiple frameworks detected, prioritize based on arguments or ask user
 - If no framework detected, **STOP** and inform the user: "Could not detect a supported framework (Next.js or FastAPI)."

2. **Detect framework version** (if applicable):
 - For Next.js: extract version from `package.json`
 - For FastAPI: extract version from `pyproject.toml` or `requirements.txt`
 - Report the detected version to the user

3. **Detect target file**:
 - Check if `CLAUDE.md` exists in the project root - use `CLAUDE.md`
 - Else check if `AGENTS.md` exists - use `AGENTS.md`
 - If neither exists, default to `CLAUDE.md` (Claude Code's native format)
 - Inform the user which file will be updated

### Phase 1: Run Framework-Specific Injection

#### Option A: Next.js Projects

Execute the Vercel codemod with the `--output` flag:

```bash
npx @next/codemod@canary agents-md --output <TARGET_FILE>
**What this does**:
- Auto-detects the Next.js version from package.json
- Downloads version-matching documentation from Vercel's servers
- Injects a compressed pipe-delimited index into the target file
- Downloads full docs to `.next-docs/` and adds it to `.gitignore`
- Non-interactive mode (no prompts)

**Important**:
- Requires network access
- Non-destructive: updates existing file without overwriting content
- Compresses ~40KB of docs into ~8KB (Vercel's agent evals showed 100% pass rate vs 53% baseline)

#### Option B: FastAPI Projects

Run the bundled injection script:

```bash
uv run "$(dirname "$0")/scripts/inject_fastapi_docs.py"
```

The script:
- Detects whether `CLAUDE.md` or `AGENTS.md` exists and targets the right file
- Checks if a "FastAPI Best Practices" section already exists (updates it if so, appends if not)
- Injects compressed best practices covering: domain-driven structure, async patterns, Pydantic validation, dependency injection, SQLAlchemy integration, error handling, testing, and Ruff code quality

**Template for FastAPI injection** (see `references/fastapi-best-practices.md` for full content):

```markdown
## FastAPI Best Practices

### Project Structure
- Use domain-driven organization (by feature), not file-type organization
- Each domain is self-contained: router, schemas, models, service, dependencies
- Structure per domain:
 - `router.py` - API endpoints
 - `schemas.py` - Pydantic request/response models
 - `models.py` - Database models (SQLAlchemy)
 - `service.py` - Business logic
 - `dependencies.py` - Route-level dependencies
 - `constants.py`, `config.py`, `exceptions.py`, `utils.py`

### Async Patterns
- Use `async def` for non-blocking I/O (database queries, HTTP calls)
- Use `def` for blocking operations (FastAPI handles threadpool automatically)
- **NEVER** use `time.sleep` in async functions (blocks event loop)
- Use `await asyncio.sleep` for delays
- CPU-intensive work requires multiprocessing/Celery (not threads due to GIL)
- Prefer async database drivers (SQLAlchemy 2.0+ with asyncio)

### Import Discipline
- Use explicit imports with module names: `from src.auth import constants as auth_constants`
- Avoids hidden coupling and improves maintainability
- Critical when importing services or dependencies from other packages

### Validation & Dependencies
- Leverage Pydantic's built-in validation (regex, enums, email, URL, constraints)
- Create custom BaseModel for application-wide consistency
- Use dependencies for business logic validation (DB constraints, authorization, token parsing)
- Dependencies cache within request scope - chain them to avoid redundant computations

### Response Serialization
- Always use `response_model` parameter on endpoints
- Create custom encoders for special types (datetime, UUID)
- FastAPI auto-generates OpenAPI schemas from type hints

### Error Handling
- Define module-specific exception classes
- Raise from dependencies and service layer
- FastAPI auto-converts to HTTP responses
- Use HTTP status codes correctly (400 for client errors, 500 for server errors)

### Database Integration
- SQL-first design: design schema first, then models
- Enforce naming conventions at database level
- Use Alembic for migrations
- Prefer async drivers for scalability

### Testing
- Use async test clients from day one
- Configure fixtures for async operations
- Test at multiple levels: unit (service), integration (router), e2e

### Code Quality
- Use Ruff for linting and formatting (Python-focused, fast)
- Always include type hints for OpenAPI generation
- Enforce strict mypy or pyright type checking
- Use pre-commit hooks for quality gates

### REST Conventions
- Use correct HTTP methods: GET (read), POST (create), PUT/PATCH (update), DELETE (remove)
- Docstrings on endpoints for clarity in auto-generated docs
- Leverage FastAPI's OpenAPI `/docs` as primary API documentation
