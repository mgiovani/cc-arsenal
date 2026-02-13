---
# Enhancement for: docs-adr
disable-model-invocation: true
argument-hint: "<title> [variant]"
allowed-tools: "Read, Write, Grep, Glob, Task"
context: "fork"
agent: "general-purpose"
---

## Claude Code Enhanced Features

This skill includes the following Claude Code-specific enhancements:

## Workflow

### Phase 1: Explore Context (Use Explore Agent)

Before writing an ADR, use the Explore agent to understand the relevant codebase context:

```
Use Task tool with Explore agent:
- prompt: "Search for code related to [DECISION_TOPIC]. Find: 1) Current implementation if any, 2) Related configuration files, 3) Dependencies involved, 4) Any existing documentation. Return verified file paths and relevant code snippets."
- subagent_type: "Explore"
```

### Phase 2: Parse Arguments

1. Extract decision title from `$ARGUMENTS`
2. Check for variant keyword: `lightweight`, `full`, or `madr`
3. If variant found, remove it from title
4. Default variant: `nygard` (Nygard style)

### Phase 3: Determine ADR Number

- Scan `docs/adr/` directory
- Find highest existing ADR number (format: `XXXX-*`)
- Increment by 1
- If no ADRs exist, start with `0001`
- Format as 4-digit padded number (e.g., `0001`, `0023`)

### Phase 4: Sanitize Title for Filename

- Convert title to kebab-case
- Remove special characters
- Lowercase all letters
- Example: "Use Redis for Caching" -> `use-redis-for-caching`

### Phase 5: Gather Context

- Search codebase for relevant information about the decision topic
- Look for related code, configs, or documentation
- Understand current state and alternatives
- Keep context concise but informative

### Phase 6: Load and Populate Template

- Template location: `assets/templates/`
- Select based on variant:
  - `nygard` -> `nygard.md` (default)
  - `lightweight` -> `lightweight.md`
  - `full` -> `full.md`
  - `madr` -> `madr.md`

Replace placeholders:
- `{{ADR_NUMBER}}` - 4-digit number
- `{{ADR_TITLE}}` - Original title (Title Case)
- `{{DATE}}` - Current date (YYYY-MM-DD)
- `{{CONTEXT}}` - Gathered context from codebase
- `{{PROJECT_NAME}}` - Git repo or directory name

### Phase 7: Create ADR File

- Filename: `docs/adr/XXXX-kebab-case-title.md`
- Ensure `docs/adr/` directory exists
- Write populated content
- Set initial status to "Proposed"

### Phase 8: Report Creation

- Show ADR number and title
- Display file path
- Provide next steps
