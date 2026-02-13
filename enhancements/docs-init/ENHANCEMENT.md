---
# Enhancement for: docs-init
disable-model-invocation: true
argument-hint: "[context]"
allowed-tools: "Read, Write, Grep, Glob, Bash(git *), Task"
context: "fork"
agent: "general-purpose"
---

## Claude Code Enhanced Features

This skill includes the following Claude Code-specific enhancements:

## Workflow

### Phase 1: Deep Codebase Exploration (Use Explore Agent)

Use the Task tool with `subagent_type: "Explore"` to thoroughly analyze the codebase before generating any documentation.

```
Use Task tool with Explore agent:
- prompt: "Analyze this codebase structure. Find: 1) All source directories with actual code files, 2) Package manager files (package.json, pyproject.toml, etc.), 3) Database/ORM files, 4) Infrastructure configs (Docker, K8s), 5) Existing documentation. Return ONLY verified findings with file paths."
- subagent_type: "Explore"
```

### Phase 2: Verify Findings

After exploration, verify each finding by reading the actual files:
- Read package.json/pyproject.toml to confirm tech stack
- Read model files to confirm database entities exist
- Check directories are not empty before claiming components exist

### Phase 3: Detect Project Characteristics

- Technology stack (language, frameworks, databases)
- Project type (web app, CLI, library, microservice, etc.)
- Infrastructure (Docker, K8s, cloud configs)
- Database/ORM presence (SQLAlchemy, Prisma, TypeORM, Django, etc.)

### Phase 4: Determine Relevant Documentation

**Core Documentation** (always generate):
- `docs/architecture.md` - System architecture overview
- `docs/onboarding.md` - Developer onboarding guide
- `docs/adr/0001-record-architecture-decisions.md` - First ADR (meta-ADR)

**Data Documentation** (if database detected):
- `docs/data-model.md` - Database schema and ER diagrams

**Infrastructure Documentation** (if deployment configs found):
- `docs/deployment.md` - CI/CD and deployment procedures
- `docs/security.md` - Security architecture

**Development Documentation** (if collaborative project):
- `docs/contributing.md` - Contribution guidelines
- `docs/rfc/` - RFC directory for proposals

### Phase 5: Check for Existing Documentation

- Scan `docs/` directory
- If files exist, ask user before overwriting
- Show what will be created vs what exists

### Phase 6: Load and Populate Templates

Templates are in `assets/templates/`. Replace placeholders:
- `{{PROJECT_NAME}}` - From git repo name or directory name
- `{{DATE}}` - Current date (YYYY-MM-DD format)
- `{{TECH_STACK}}` - Detected technologies
- `{{DESCRIPTION}}` - Brief project description from README or git
- `{{CONTEXT}}` - Gathered context from codebase analysis

### Phase 7: Verify Before Writing

Before writing each document, verify claims:
1. Re-read the source file to confirm the claim
2. If claiming "X components exist", verify the count with ls/find
3. If referencing a function/class, grep to confirm it exists
4. Remove any claims that cannot be verified

### Phase 8: Generate Documentation

- Create `docs/` directory if it does not exist
- Create subdirectories: `docs/adr/`, `docs/rfc/` (if needed)
- Generate each relevant documentation file
- Populate with project-specific content

### Phase 9: Report Results

- List all documentation files created
- Show what was skipped (already exists)
- Provide next steps
