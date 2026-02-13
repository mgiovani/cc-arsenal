---
name: docs-update
description: Update documentation by synchronizing with the current codebase state.
  This skill should be used when users want to refresh stale documentation, sync docs
  with code changes, or update specific documentation files or categories.
metadata:
  author: mgiovani
  version: 1.0.0
  source: https://github.com/mgiovani/skills
disable-model-invocation: true
argument-hint: '[all|<doc-name>|category:<name>]'
allowed-tools: Read, Write, Grep, Glob, Bash(git *), Task, TodoWrite
context: fork
agent: general-purpose
---

# Docs Update

> **Cross-Platform AI Agent Skill**
> This skill works with any AI agent platform that supports the skills.sh standard.

# Update Documentation

Synchronize documentation with the current codebase state. Can update all docs, specific files, or entire categories.

## Anti-Hallucination Guidelines

**CRITICAL**: Documentation updates must reflect REALITY, not assumptions:
1. **Explore before updating** - Use Explore agent to understand actual codebase state
2. **Verify every claim** - Before writing any statement, verify it with code
3. **Count accurately** - Use find/glob for exact counts, never estimate
4. **Remove stale content** - Delete claims about features that no longer exist
5. **Cross-reference** - After updating, verify the update matches reality

## Workflow

### Phase 1: Deep Codebase Analysis (Explore Codebase)

Before updating ANY documentation, thoroughly explore the codebase:

### Phase 2: Track Progress (Use TodoWrite)

For updating multiple documents, use TodoWrite to track progress:
```
Create todos for each document to update, marking them in_progress as you work
### Phase 3: Parse Arguments

1. Extract update mode from `command arguments`
2. Modes:
 - No args or `all` -> Update all relevant docs
 - `<doc-name>` -> Update specific doc (e.g., `architecture`)
 - `category:<name>` -> Update category (e.g., `category:data`)
3. Default: Update all

### Phase 4: Determine Update Scope and Analyze

**For "all" mode**: Analyze entire project, identify all relevant documentation types, update everything that exists or should exist.

**For specific doc mode**: Validate doc name, find the corresponding file, update only that document.

**For category mode**: Parse category name (`core`, `data`, `infrastructure`, `development`), identify all docs in that category, update all.

### Phase 5: Check Documentation Freshness

```bash
# For each doc, compare with related code changes
!`git log --since="$(git log -1 --format=%ai docs/architecture.md)" --oneline --name-only | head -30`
Identify which docs are outdated and prioritize updates.

### Phase 6: Parallel Updates (Use Parallel Analysis)

For multiple document updates, see [references/update-strategies.md](references/update-strategies.md) for parallel subagent patterns.

#### For Multiple Documents ("all" or "category" mode)

#### For Single Document (Section-Level Parallelization)

Even when updating ONE document, spawn subagents for each major section. See [references/update-strategies.md](references/update-strategies.md) for section-level patterns.

### Phase 7: Update Each Document

- Re-analyze relevant parts of codebase
- **Verify each claim before writing** - Read actual files
- Regenerate diagrams if needed
- Update content while preserving custom sections
- Replace placeholders with current values
- **Remove claims that cannot be verified**

### Phase 8: Post-Update Verification

After updating, verify the updates are accurate:
```
For each updated document:
1. Re-read the document
2. For each major claim, verify against actual code
3. If any claim cannot be verified, remove it
4. Run docs-check to validate
### Phase 9: Preserve Custom Content (Important)

- Keep manually added sections
- Preserve non-template content
- Only update auto-generated parts
- If unsure, ask before overwriting

### Phase 10: Report Results

- List documents updated
- List documents skipped (up to date)
- List documents created (if missing)
- Show summary of changes

## Documentation Categories

### Core Documentation
Files that are always relevant:
- `docs/architecture.md` - System architecture
- `docs/onboarding.md` - Developer onboarding
- `docs/adr/` - Architecture Decision Records

**Update when**: Architecture changes, setup process changes

### Data Documentation
Files relevant if database detected:
- `docs/data-model.md` - Database schema and ER diagrams

**Update when**: Schema changes, models modified

### Infrastructure Documentation
Files relevant if deployment configs detected:
- `docs/deployment.md` - CI/CD and deployment
- `docs/security.md` - Security architecture

**Update when**: Infrastructure changes, security updates

### Development Documentation
Files relevant for collaborative projects:
- `docs/contributing.md` - Contribution guidelines
- `docs/rfc/` - RFC documents
- `docs/api-documentation.md` - API documentation

**Update when**: Process changes, API changes

## Document Name Mapping

| Argument | File Path |
|----------------|----------------------------|
| `architecture` | `docs/architecture.md` |
| `onboarding` | `docs/onboarding.md` |
| `data-model` | `docs/data-model.md` |
| `deployment` | `docs/deployment.md` |
| `security` | `docs/security.md` |
| `contributing` | `docs/contributing.md` |
| `api-docs` | `docs/api-documentation.md`|

## Usage Examples

Update all documentation:
```
docs-update
docs-update all
Update specific document:
```
docs-update architecture
docs-update data-model
docs-update onboarding
docs-update deployment
docs-update security
Update entire category:
```
docs-update category:core
docs-update category:data
docs-update category:infrastructure
docs-update category:development
With context:
```
docs-update architecture after microservices refactor
docs-update data-model after schema migration
docs-update category:core for onboarding review
## Template Placeholder Replacement

Replace these placeholders during update:
- `{{PROJECT_NAME}}` - Current project name
- `{{DATE}}` - Current date
- `{{TECH_STACK}}` - Detected technologies
- `{{ER_DIAGRAM}}` - Generated ER diagram
- `{{ARCHITECTURE_DIAGRAM}}` - Generated architecture diagram
- `{{ENTITIES}}` - Extracted entity descriptions
- `{{COMPONENTS}}` - Extracted component descriptions

## Important Notes

- **Preserves custom content**: Does not blindly overwrite
- **Smart updates**: Only updates outdated sections
- **Diagram regeneration**: Auto-regenerates diagrams
- **Git-aware**: Uses git to detect what changed
- **Safe**: Asks before major changes
- **Incremental**: Can be run frequently

## When to Run

- After major refactoring
- When database schema changes
- After adding new features or components
- Before onboarding new team members
- When documentation becomes stale
- As part of release process
- After infrastructure changes
- Before documentation reviews

## Best Practices

- **Run regularly**: Keep documentation current
- **Review changes**: Always review auto-generated updates
- **Preserve custom**: Keep manual additions safe
- **Commit with code**: Update docs alongside code changes
- **Be specific**: Use specific doc names for targeted updates
- **Bulk updates**: Use category updates for efficiency
- **Verify diagrams**: Check generated diagrams for accuracy

## Additional Resources

- For parallel update patterns and section-level strategies, see [references/update-strategies.md](references/update-strategies.md)
- For change detection commands, see [references/change-detection.md](references/change-detection.md)

## Claude Code Enhanced Features

This skill includes the following Claude Code-specific enhancements:

## Workflow

### Phase 1: Deep Codebase Analysis (Use Explore Agent)

Before updating ANY documentation, thoroughly explore the codebase:

```
Use Task tool with Explore agent:
- prompt: "Comprehensively analyze this codebase. Find: 1) All actual source files and their purposes, 2) Real component counts (services, models, APIs), 3) Actual directory structure with content verification, 4) Technologies actually in use (check package files). Return ONLY verified facts with file paths as evidence."
- subagent_type: "Explore"
```

### Phase 2: Track Progress (Use TodoWrite)

For updating multiple documents, use TodoWrite to track progress:
```
Create todos for each document to update, marking them in_progress as you work
```

### Phase 3: Parse Arguments

1. Extract update mode from `$ARGUMENTS`
2. Modes:
   - No args or `all` -> Update all relevant docs
   - `<doc-name>` -> Update specific doc (e.g., `architecture`)
   - `category:<name>` -> Update category (e.g., `category:data`)
3. Default: Update all

### Phase 4: Determine Update Scope and Analyze

**For "all" mode**: Analyze entire project, identify all relevant documentation types, update everything that exists or should exist.

**For specific doc mode**: Validate doc name, find the corresponding file, update only that document.

**For category mode**: Parse category name (`core`, `data`, `infrastructure`, `development`), identify all docs in that category, update all.

### Phase 5: Check Documentation Freshness

```bash
# For each doc, compare with related code changes
!`git log --since="$(git log -1 --format=%ai docs/architecture.md)" --oneline --name-only | head -30`
```

Identify which docs are outdated and prioritize updates.

### Phase 6: Parallel Updates (Use SubAgents)

For multiple document updates, see [references/update-strategies.md](references/update-strategies.md) for parallel subagent patterns.

#### For Multiple Documents ("all" or "category" mode)

```
Use Task tool with multiple parallel agents:

Agent 1 - Architecture Update:
- prompt: "Update docs/architecture.md. Explore codebase, verify claims, remove false info, add missing components."
- subagent_type: "general-purpose"

Agent 2 - Data Model Update:
- prompt: "Update docs/data-model.md. Find actual models, verify ER diagram accuracy."
- subagent_type: "general-purpose"

Agent 3 - Onboarding Update:
- prompt: "Update docs/onboarding.md. Verify setup instructions and commands exist."
- subagent_type: "general-purpose"
```

#### For Single Document (Section-Level Parallelization)

Even when updating ONE document, spawn subagents for each major section. See [references/update-strategies.md](references/update-strategies.md) for section-level patterns.

### Phase 7: Update Each Document

- Re-analyze relevant parts of codebase
- **Verify each claim before writing** - Read actual files
- Regenerate diagrams if needed
- Update content while preserving custom sections
- Replace placeholders with current values
- **Remove claims that cannot be verified**

### Phase 8: Post-Update Verification

After updating, verify the updates are accurate:
```
For each updated document:
1. Re-read the document
2. For each major claim, verify against actual code
3. If any claim cannot be verified, remove it
4. Run /docs-check to validate
```

### Phase 9: Preserve Custom Content (Important)

- Keep manually added sections
- Preserve non-template content
- Only update auto-generated parts
- If unsure, ask before overwriting

### Phase 10: Report Results

- List documents updated
- List documents skipped (up to date)
- List documents created (if missing)
- Show summary of changes
