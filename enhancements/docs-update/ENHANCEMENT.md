---
# Enhancement for: docs-update
disable-model-invocation: true
argument-hint: "[all|<doc-name>|category:<name>]"
allowed-tools: "Read, Write, Grep, Glob, Bash(git *), Task, TodoWrite"
context: "fork"
agent: "general-purpose"
---

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
