---
name: docs-init
description: "Initialize comprehensive documentation structure for a project based on detected technologies and configuration. This skill should be used when users want to set up project documentation from scratch, bootstrap docs for a new project, or create initial documentation structure."
disable-model-invocation: true
argument-hint: "[context]"
allowed-tools: Read, Write, Grep, Glob, Bash(git *), Task
context: fork
agent: general-purpose
---

# Initialize Project Documentation

Generate comprehensive documentation structure for a project based on detected technologies and configuration.

## Anti-Hallucination Guidelines

**CRITICAL**: Before documenting ANY feature, component, or capability:
1. **Verify existence** - Read the actual file/directory to confirm it exists
2. **Count accurately** - Use `ls` or `find` to get exact counts, do not estimate
3. **Quote actual code** - Reference real function names, not assumed ones
4. **Check empty directories** - A directory existing does not mean content exists
5. **Never assume** - If it cannot be verified, do not document it

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

Templates are in `resources/templates/`. Replace placeholders:
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

## Context Detection Examples

```bash
# Check for language/framework
!`find . -name "package.json" -o -name "pyproject.toml" -o -name "go.mod" -o -name "Cargo.toml" | head -5`

# Check for database
!`find . -name "*models.py" -o -name "*schema.prisma" -o -name "*entity.ts" | head -5`

# Check for infrastructure
!`find . -name "Dockerfile" -o -name "docker-compose.yml" -o -name "*.k8s.yaml" | head -5`

# Get project name
!`basename $(git rev-parse --show-toplevel 2>/dev/null || pwd)`

# Get project description
!`head -20 README.md 2>/dev/null || echo ""`
```

## Template Locations

Templates are loaded from `resources/templates/`:

| Document Type | Template File |
|--------------|---------------|
| Architecture | `architecture.md` |
| Onboarding | `onboarding.md` |
| ADR (first) | `adr/nygard.md` |
| Data Model | `data-model.md` |
| Deployment | `deployment.md` |
| Security | `security.md` |
| Contributing | `contributing.md` |

## Usage Examples

Basic initialization (auto-detect everything):
```
/docs-init
```

With additional context:
```
/docs-init for Python FastAPI microservice
/docs-init for Next.js SaaS application
/docs-init for React component library
```

## Important Notes

- **Zero-config**: Works without any configuration file
- **Smart detection**: Only generates relevant documentation
- **Safe**: Always asks before overwriting existing files
- **Customizable**: User context in command is used to enhance generation
- **Git-aware**: Uses git information when available
- **Incremental**: Can be run multiple times safely

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

Next Steps:
  1. Review and customize generated documentation
  2. Run /docs-diagram er to generate ER diagram
  3. Run /docs-diagram arch to generate architecture diagram
  4. Create ADRs for key decisions: /docs-adr "Decision Title"
```

## When to Run

- Starting a new project
- Adding documentation to an existing project
- Reorganizing project documentation
- Onboarding new team members

**Note**: This skill can be run multiple times. It will only create missing files and ask before overwriting existing ones.

---

**Template Location**: `resources/templates/`
**Output Directory**: `docs/`
