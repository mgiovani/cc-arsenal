---
name: docs-init
description: Bootstraps a documentation structure (architecture, onboarding, data-model,
  deployment, security, contributing, and a first ADR) for a project that has little
  or no docs/ directory, exploring the codebase and populating templates only with
  content evidenced in the code. Use when the user wants to set up docs, bootstrap
  documentation, initialize project docs, scaffold a docs/ folder, or create docs from
  scratch for a new or undocumented project. Not for refreshing or syncing docs that
  already exist (use docs-update). Not for generating a standalone architecture or
  ER diagram without the surrounding document (use docs-diagram).
metadata:
  author: mgiovani
  version: 2.0.0
disable-model-invocation: true
argument-hint: '[context]'
allowed-tools: Read, Write, Grep, Glob, Bash(git *), Bash(find *), Task
context: fork
agent: general-purpose
---

# Initialize Project Documentation

Bootstrap a `docs/` structure for a project with little or no existing documentation. Only generate what the codebase actually evidences.

## Anti-Hallucination Guidelines

Every claim in generated docs must trace to something read or grepped in this run:

1. Verify a file/directory exists before referencing it.
2. Get counts from `ls`/`find`/`grep`, never estimate.
3. Quote real function/class/table names, not assumed ones.
4. An empty directory is not a feature, don't document it.
5. If a claim can't be verified, drop it rather than guess.

## Workflow

### 1. Explore the codebase

Find: source directories with actual code, package manager files (`package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, ...), database/ORM files, infrastructure configs (Docker, k8s, Terraform), and any existing `docs/`. See Detection Commands below for the exact patterns.

If a Task/subagent tool is available, delegate this to an Explore agent with that scope. Otherwise run the same `grep`/`find` commands inline and `Read` each hit: the result must be the same either way.

Verify every finding before using it: read the package manifest, read the model file, confirm a directory has real files inside it, not just an empty folder.

### 2. Detect project characteristics

From the exploration, determine: language/framework stack, project type (web app, CLI, library, service), whether a database/ORM is present, and whether infrastructure/deployment configs exist.

### 3. Decide which docs to generate

- **Always**: `docs/architecture.md`, `docs/onboarding.md`, `docs/adr/0001-record-architecture-decisions.md` (Nygard-format meta-ADR, generate inline, no template file)
- **If a database/ORM was found**: `docs/data-model.md`
- **If deployment configs were found** (Dockerfile, k8s manifest, CI workflow, IaC): `docs/deployment.md`, `docs/security.md`
- **If the project looks collaborative** (multiple contributors in `git log`, an open-source license, no existing CONTRIBUTING): `docs/contributing.md`, `docs/rfc/` directory

Don't generate a doc type with no supporting evidence: an empty data-model.md for a stateless CLI is worse than no file at all.

### 4. Check for existing docs

Scan `docs/`. For any target file that already exists, do not overwrite it: list it under "skipped" and ask the user before touching it. This skill is safe to rerun: by default it only fills gaps.

### 5. Populate templates

Templates live in `assets/templates/` (see reference table below). For each one you're using:

1. Grep it for its actual placeholder set: `grep -oE '\{\{[A-Z_0-9]+\}\}' assets/templates/<name>.md | sort -u`
2. Map every placeholder to a value from step 1/2's verified findings. Never leave a placeholder as a literal `{{TOKEN}}` in the output.
3. Templates mark some sections as conditional with an HTML comment ("delete if...", "only if evidenced"). Where the codebase gives no evidence for that section, delete the whole section (heading included, not just the placeholder text).
4. After writing the file, grep it for `\{\{[A-Z_0-9]+\}\}` again. Zero matches. If any remain, resolve or delete them before moving on.

**Worked example** (a FastAPI + PostgreSQL service):

```
$ grep -oE '\{\{[A-Z_0-9]+\}\}' assets/templates/architecture.md | sort -u
{{COMPONENT_DEPENDENCIES}}
{{COMPONENT_DESCRIPTION}}
{{COMPONENT_NAME}}
{{DATA_FLOW}}
{{DATE}}
{{DEPLOYMENT_SUMMARY}}
...
```

Map each to a verified finding: `{{TECHNOLOGY_STACK}}` becomes "Python 3.12, FastAPI 0.115, PostgreSQL 16 via SQLAlchemy", read from `pyproject.toml` and the model files, not assumed. If `security.md`'s Compliance section has no GDPR/HIPAA evidence in the codebase (no consent flow, no PHI handling), delete that whole section rather than fill it with a guess.

### 6. Write the files

Create `docs/` (and `docs/adr/`, `docs/rfc/` if needed). Write each file that isn't being skipped.

### 7. Report

List what was created, what was skipped (already existed), and next steps.

## Template Reference

| Document | Template | Generated when |
|----------|----------|-----------------|
| Architecture | `architecture.md` | always |
| Onboarding | `onboarding.md` | always |
| First ADR | inline (Nygard format) | always |
| Data Model | `data-model.md` | database/ORM detected |
| Deployment | `deployment.md` | deployment config detected |
| Security | `security.md` | deployment config detected |
| Contributing | `contributing.md` | collaborative project |

## Detection Commands

Run these directly (or hand them to the Explore agent from step 1):

```bash
# Language/framework
find . -name "package.json" -o -name "pyproject.toml" -o -name "go.mod" -o -name "Cargo.toml" | head -5

# Database/ORM
find . -name "*models.py" -o -name "*schema.prisma" -o -name "*entity.ts" | head -5

# Infrastructure
find . -name "Dockerfile" -o -name "docker-compose.yml" -o -name "*.k8s.yaml" | head -5

# Project name and description
basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
head -20 README.md 2>/dev/null
```

## Usage Examples

```
docs-init
docs-init for Python FastAPI microservice
docs-init for Next.js SaaS application
```

## Example Output

```
Documentation Initialization Complete

Created:
 docs/architecture.md - System architecture overview
 docs/onboarding.md - Developer onboarding guide
 docs/adr/0001-record-architecture-decisions.md - Meta-ADR
 docs/data-model.md - Database schema (SQLAlchemy detected)
 docs/deployment.md - Deployment guide (Docker detected)

Skipped (already exists):
 docs/contributing.md

Next steps:
 1. Review and customize the generated docs
 2. docs-diagram er / docs-diagram arch for standalone diagrams
 3. docs-adr "Decision Title" for future ADRs
```

## Notes

- Safe to rerun: only fills gaps, asks before overwriting existing files.
- User-supplied context (e.g. "for a FastAPI microservice") steers detection but doesn't replace verification: still confirm the stack from the actual files.
