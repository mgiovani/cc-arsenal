---
name: inject-docs
description: Inject compressed framework-specific best practices and docs into
  CLAUDE.md or AGENTS.md so AI coding agents get passive framework knowledge
  without extra tool calls. Supports Next.js (via Vercel's agents-md codemod,
  version-aware) and FastAPI (via a bundled best-practices template). Use when
  a user wants to add Next.js or FastAPI docs to CLAUDE.md/AGENTS.md, run the
  Vercel agents-md codemod, inject framework best practices for AI agents, or
  improve AI agent performance on a Next.js or FastAPI project. This is the
  only framework-doc-injection skill in this toolkit — don't look for a
  Next.js-specific variant.
metadata:
  author: mgiovani
  version: 1.0.0
disable-model-invocation: true
argument-hint: ''
allowed-tools: Bash(npx *), Bash(node *), Bash(uv run *), Bash(cat *), Read, Grep, Glob, Task, AskUserQuestion
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

Execute the Vercel codemod with the `--output` flag, in the project root:

```bash
npx @next/codemod@canary agents-md --output <TARGET_FILE>
```

Where `<TARGET_FILE>` is the file detected in Phase 0 (e.g., `CLAUDE.md` or `AGENTS.md`).

**What this does**:
- Auto-detects the Next.js version from package.json
- Downloads version-matching documentation from Vercel's servers
- Injects a compressed pipe-delimited index into the target file
- Downloads full docs to `.next-docs/` and adds it to `.gitignore`
- Non-interactive mode (no prompts, thanks to `--output`)

**Important**:
- Requires network access
- Non-destructive: injects/updates the index section without overwriting existing content
- Compresses ~40KB of docs into ~8KB (Vercel's agent evals showed 100% pass rate vs 53% baseline)
- Target file priority: CLAUDE.md (if exists) → AGENTS.md (if exists) → CLAUDE.md (default)

#### Option B: FastAPI Projects

Run the bundled injection script:

```bash
uv run "$(dirname "$0")/scripts/inject_fastapi_docs.py"
```

The script:
- Detects whether `CLAUDE.md` or `AGENTS.md` exists and targets the right file
- Checks if a "FastAPI Best Practices" section already exists (updates it if so, appends if not)
- Injects compressed best practices covering: domain-driven structure, async patterns, Pydantic validation, dependency injection, SQLAlchemy integration, error handling, testing, and Ruff code quality

See `references/fastapi-best-practices.md` for the exact content injected.

### Phase 2: Verify Results

After Phase 1 completes:

1. **Confirm the target file was updated** - read it back and check it contains the injected framework content (pipe-delimited Next.js index, or the `## FastAPI Best Practices` section)
2. **Check size** - note the approximate size before/after (Next.js codemod prints this; for FastAPI, compare file sizes yourself)
3. Do not report success on command exit code alone — verify the content actually landed.

### Phase 3: Report

Summarize for the user:
- Framework and version detected
- Which file was updated (CLAUDE.md or AGENTS.md), created vs. updated
- Confirmation that framework docs were injected, with approximate size
- Suggest reviewing the diff and committing

## Examples

### Next.js project with existing CLAUDE.md

```
> inject Next.js docs

Detected Next.js 15.2.3 in package.json
Found existing CLAUDE.md - will inject documentation there
Running: npx @next/codemod@canary agents-md --output CLAUDE.md
Updated CLAUDE.md (2.1 KB -> 10.3 KB)
Added .next-docs to .gitignore

Review the changes and commit when ready:
  git add CLAUDE.md .gitignore && git commit -m "docs: add Next.js agents-md framework reference"
```

### FastAPI project with no existing docs file

```
> inject FastAPI best practices

Detected FastAPI 0.115.0 in pyproject.toml
No CLAUDE.md or AGENTS.md found - creating CLAUDE.md
Ran scripts/inject_fastapi_docs.py
Created CLAUDE.md (0 B -> 6.8 KB) with "FastAPI Best Practices" section

Review the changes and commit when ready:
  git add CLAUDE.md && git commit -m "docs: add FastAPI best-practices reference"
```
