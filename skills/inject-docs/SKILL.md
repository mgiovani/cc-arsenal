---
name: inject-docs
description: "Inject framework-specific best practices and documentation into the project's CLAUDE.md file. Supports Next.js (via Vercel's agents-md codemod) and Python/FastAPI (via zhanymkanov/fastapi-best-practices). This skill should be used when a user wants to add framework documentation for AI coding agents or improve AI agent performance on framework-specific projects."
disable-model-invocation: true
argument-hint: "[nextjs|fastapi]"
allowed-tools: Bash(npx *), Bash(node *), Bash(cat *), Bash(uv *), Bash(python *), Read, Write, Edit, Grep, Glob, Task, AskUserQuestion, WebFetch
---

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
```

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

Use a custom Python script to inject FastAPI best practices:

1. **Fetch the best practices content**:
   ```bash
   # Use WebFetch or curl to get the README from fastapi-best-practices
   # Store in temporary file for processing
   ```

2. **Generate compressed documentation** from the repository content covering:
   - Domain-driven project organization
   - Async/sync routing patterns
   - Pydantic validation best practices
   - Dependency injection patterns
   - Database integration (SQLAlchemy, Alembic)
   - Error handling conventions
   - Testing patterns
   - Code quality tools (Ruff)

3. **Inject into CLAUDE.md**:
   - Check if a "FastAPI Best Practices" section already exists
   - If exists, update it; otherwise append to the end
   - Use clear section headers for easy navigation

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
- **NEVER** use `time.sleep()` in async functions (blocks event loop)
- Use `await asyncio.sleep()` for delays
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

---

**Reference**: [FastAPI Best Practices by zhanymkanov](https://github.com/zhanymkanov/fastapi-best-practices)
```

### Phase 2: Verify Results

After injection completes:

1. **Confirm the target file was updated**:
   - Read the file to verify it contains framework documentation
   - For Next.js: Look for pipe-delimited Next.js entries
   - For FastAPI: Look for "FastAPI Best Practices" section

2. **Check content integrity**:
   - Verify the injected content is properly formatted Markdown
   - Ensure existing content was not corrupted

3. **Report to user**:
   - Which framework was detected
   - Which file was updated (CLAUDE.md or AGENTS.md)
   - Approximate size of the injected documentation
   - Summary of what was added

### Phase 3: Report & Cleanup

Provide a summary to the user:

**For Next.js**:
```
Detected Next.js 15.2.3 in package.json
Updated CLAUDE.md with Next.js framework documentation (~8KB compressed)
Added .next-docs to .gitignore

Review the changes and commit when ready:
  git add CLAUDE.md .gitignore && git commit -m "docs: add Next.js framework reference"
```

**For FastAPI**:
```
Detected FastAPI 0.115.0 in pyproject.toml
Updated CLAUDE.md with FastAPI best practices (~6KB)

Review the changes and commit when ready:
  git add CLAUDE.md && git commit -m "docs: add FastAPI best practices reference"
```

## Usage

```bash
# Auto-detect framework
/inject-docs

# Explicit framework selection
/inject-docs nextjs
/inject-docs fastapi
```

## Examples

### Example 1: Next.js Project

```
> /inject-docs

Detected Next.js 15.2.3 in package.json
Found existing CLAUDE.md - will inject documentation there
Running: npx @next/codemod@canary agents-md --output CLAUDE.md
✓ Updated CLAUDE.md (2.1 KB → 10.3 KB)
✓ Added .next-docs to .gitignore

Review the changes and commit when ready:
  git add CLAUDE.md .gitignore && git commit -m "docs: add Next.js framework reference"
```

### Example 2: FastAPI Project

```
> /inject-docs

Detected FastAPI 0.115.0 in pyproject.toml
Found existing CLAUDE.md - will inject documentation there
Fetching FastAPI best practices from zhanymkanov/fastapi-best-practices...
✓ Updated CLAUDE.md (3.2 KB → 9.5 KB)
✓ Injected FastAPI Best Practices section

Review the changes and commit when ready:
  git add CLAUDE.md && git commit -m "docs: add FastAPI best practices reference"
```

### Example 3: Explicit Framework Selection

```
> /inject-docs fastapi

Detected FastAPI 0.110.0 in requirements.txt
Target file: CLAUDE.md (will be created)
Fetching FastAPI best practices...
✓ Created CLAUDE.md (6.1 KB)
✓ Injected FastAPI Best Practices section
```

## Important Notes

### Next.js
- Requires Next.js project with `next` in package.json
- Version-aware: downloads documentation matching the installed Next.js version
- Non-destructive: injects/updates the index section without overwriting existing content
- Requires network access to download documentation from Vercel's servers
- Full docs downloaded to `.next-docs/` and auto-added to `.gitignore`

### FastAPI
- Requires FastAPI project with `fastapi` in pyproject.toml or requirements.txt
- Version-agnostic: best practices apply across FastAPI versions
- Non-destructive: appends or updates the "FastAPI Best Practices" section
- Requires network access to fetch from GitHub
- Based on production-ready patterns from zhanymkanov's guide

### General
- **Target file priority**: CLAUDE.md (if exists) → AGENTS.md (if exists) → CLAUDE.md (default)
- **Multiple frameworks**: If both frameworks detected, tool will ask which to inject
- **Updates**: Safe to run multiple times - will update existing sections without duplication
- **Commit recommendation**: Always review changes before committing to version control
