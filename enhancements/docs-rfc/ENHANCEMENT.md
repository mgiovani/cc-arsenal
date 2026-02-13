---
# Enhancement for: docs-rfc
disable-model-invocation: true
argument-hint: "<title> [variant]"
allowed-tools: "Read, Write, Grep, Glob, Bash(git *), Task"
context: "fork"
agent: "general-purpose"
---

## Claude Code Enhanced Features

This skill includes the following Claude Code-specific enhancements:

## Workflow

### Phase 1: Explore Current State (Use Explore Agent)

Before writing an RFC, thoroughly explore the codebase to understand current state:

```
Use Task tool with Explore agent:
- prompt: "Analyze the codebase to understand [RFC_TOPIC]. Find: 1) Current implementation patterns, 2) Related components and their interactions, 3) Existing similar features, 4) Technical constraints. Return verified findings with file paths."
- subagent_type: "Explore"
```

### Phase 2: Parse Arguments

1. Extract proposal title from `$ARGUMENTS`
2. Check for variant keyword: `minimal`, `standard`, or `detailed`
3. If variant found, remove it from title
4. Default variant: `standard`

### Phase 3: Determine RFC Number

- Scan `docs/rfc/` directory
- Find highest existing RFC number (format: `RFC-XXXX-*`)
- Increment by 1
- If no RFCs exist, start with `0001`
- Format as 4-digit padded number (e.g., `0001`, `0023`)

### Phase 4: Sanitize Title for Filename

- Convert title to kebab-case
- Remove special characters
- Lowercase all letters
- Example: "Add GraphQL API Support" -> `add-graphql-api-support`

### Phase 5: Gather Context

- Analyze codebase to understand current state
- Identify relevant files and patterns
- Find similar implementations or related features
- Understand technical constraints

### Phase 6: Get Author Information

```bash
# Try to get git author
!`git config user.name 2>/dev/null || echo "Development Team"`
```

### Phase 7: Load and Populate Template

- Template location: `assets/templates/`
- Select based on variant:
  - `minimal` -> `minimal.md`
  - `standard` -> `standard.md` (default)
  - `detailed` -> `detailed.md`

Replace placeholders:
- `{{RFC_NUMBER}}` - 4-digit number
- `{{RFC_TITLE}}` - Original title (Title Case)
- `{{DATE}}` - Current date (YYYY-MM-DD)
- `{{AUTHOR}}` - Git user name or "Development Team"
- `{{CONTEXT}}` - Gathered context from codebase
- `{{PROJECT_NAME}}` - Git repo or directory name

### Phase 8: Create RFC File

- Filename: `docs/rfc/RFC-XXXX-kebab-case-title.md`
- Ensure `docs/rfc/` directory exists
- Write populated content
- Set initial status to "Draft"

### Phase 9: Report Creation

- Show RFC number and title
- Display file path
- Provide workflow guidance
