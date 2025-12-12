---
description: "Create a new memory rule following Claude Code best practices"
argument-hint: "<rule-name> [description]"
allowed-tools: ["Read", "Write", "Edit", "Grep", "Glob", "Bash(git *)", "Bash(mkdir *)", "Task", "TodoWrite", "AskUserQuestion"]
---

# Create Memory Rule

Generate a new memory rule following Claude Code best practices for project instructions, coding standards, and workflow guidelines.

## Reference Documentation

Claude Code memory documentation: https://code.claude.com/docs/en/memory.md

## Memory Hierarchy

Claude Code loads memory from multiple locations in priority order:

| Type | Location | Purpose | Shared With |
|------|----------|---------|-------------|
| **Enterprise** | `/Library/Application Support/ClaudeCode/CLAUDE.md` | Organization-wide policies | All org users |
| **Project** | `./CLAUDE.md` or `./.claude/CLAUDE.md` | Team-shared project instructions | Team via git |
| **Project Rules** | `./.claude/rules/*.md` | Modular, topic-specific rules | Team via git |
| **User** | `~/.claude/CLAUDE.md` | Personal preferences (all projects) | Just you |
| **User Rules** | `~/.claude/rules/*.md` | Personal modular rules | Just you |
| **Project Local** | `./CLAUDE.local.md` | Personal project preferences | Just you |

## Your Task

### Phase 1: Understand Context (Use Explore Agent)

First, understand the codebase context to create relevant rules:

```
Use Task tool with Explore agent:
- prompt: "The user wants to create a rule called [RULE_NAME] with description: [DESCRIPTION]. Search the codebase to understand: 1) Existing CLAUDE.md files and their structure, 2) Existing .claude/rules/ if any, 3) Relevant code patterns the rule should enforce. Return findings with file paths."
- subagent_type: "Explore"
```

### Phase 2: Parse Arguments

1. **Extract rule name** from `$1` or first word of `$ARGUMENTS`
2. **Extract description** from remaining arguments or ask user
3. **Determine rule type**:
   - **Modular rule**: `.claude/rules/<name>.md` (recommended for focused topics)
   - **CLAUDE.md entry**: Add to existing `./CLAUDE.md` or `~/.claude/CLAUDE.md`
4. **Determine scope**:
   - **Project rule**: `.claude/rules/` (shared with team)
   - **User rule**: `~/.claude/rules/` (personal, all projects)

### Phase 3: Gather Rule Requirements

Ask user or infer from context:

```
Questions to determine:
1. What specific behavior should this rule enforce?
2. Is it path-specific? (applies only to certain file patterns)
3. Should it be project-scoped or user-scoped?
4. What category does it belong to? (code-style, testing, security, workflow, etc.)
5. Are there existing similar rules to reference or extend?
```

### Phase 4: Analyze Existing Rules (Use SubAgents)

Spawn parallel agents to gather patterns:

```
Agent 1 - Analyze Existing Memory:
- prompt: "Read any existing CLAUDE.md files and .claude/rules/*.md in the project. Extract common patterns: structure, formatting, specificity level. Return best practices observed."
- subagent_type: "Explore"

Agent 2 - Identify Rule Category:
- prompt: "Based on the rule description '[DESCRIPTION]', what category does it fit? Consider: code-style, testing, security, api-design, documentation, workflow, tooling. Return recommended category and filename."
- subagent_type: "general-purpose"

Agent 3 - Check for Conflicts:
- prompt: "Search for existing rules that might conflict with or overlap '[DESCRIPTION]'. Check CLAUDE.md files and .claude/rules/. Return any potential conflicts or opportunities to consolidate."
- subagent_type: "Explore"
```

### Phase 5: Generate Rule Structure

Use TodoWrite to track rule creation:

```
TodoWrite:
- [ ] Create rule file with frontmatter (if path-specific)
- [ ] Write clear, specific instructions
- [ ] Add examples where helpful
- [ ] Validate rule syntax
- [ ] Test rule applicability
```

### Phase 6: Write Rule File

Generate the rule following this template structure:

#### For Path-Specific Rules (with frontmatter):

```markdown
---
paths: src/**/*.ts, lib/**/*.ts
---

# [Rule Title]

[Brief description of what this rule enforces]

## Guidelines

- [Specific instruction 1]
- [Specific instruction 2]
- [Specific instruction 3]

## Examples

### Good
\`\`\`typescript
// Example of correct pattern
\`\`\`

### Avoid
\`\`\`typescript
// Example of pattern to avoid
\`\`\`
```

#### For General Rules (no frontmatter):

```markdown
# [Rule Title]

[Brief description of what this rule enforces]

## Guidelines

- [Specific instruction 1]
- [Specific instruction 2]
- [Specific instruction 3]

## Examples

[Concrete examples if helpful]
```

### Phase 7: Validate Generated Rule

Before writing, verify:

```
1. Rule is specific and actionable (not vague)
2. If path-specific, glob patterns are correct
3. Instructions use imperative language ("Use X" not "You should use X")
4. No duplicate or conflicting rules exist
5. Filename is descriptive and follows kebab-case
6. Category organization makes sense
7. Examples are realistic and helpful
```

### Phase 8: Write and Report

1. Create the rule file at appropriate location
2. Report what was created
3. Suggest testing the rule with `/memory` command

## Rule Design Principles

### Frontmatter Syntax

```yaml
---
# Only for path-specific rules
paths: src/**/*.ts
# Supports glob patterns and brace expansion
paths: src/**/*.{ts,tsx}
# Multiple patterns with comma
paths: {src,lib}/**/*.ts, tests/**/*.test.ts
---
```

### Glob Pattern Reference

| Pattern | Matches |
|---------|---------|
| `**/*.ts` | All TypeScript files in any directory |
| `src/**/*` | All files under `src/` directory |
| `*.md` | Markdown files in project root only |
| `src/components/*.tsx` | React components in specific directory |
| `**/*.{ts,tsx}` | Both .ts and .tsx files anywhere |
| `{src,lib}/**/*.ts` | TypeScript in src/ or lib/ directories |

### Best Practices

```
Writing Effective Rules:

1. BE SPECIFIC
   Good: "Use 2-space indentation for TypeScript files"
   Bad: "Format code properly"

2. USE IMPERATIVE LANGUAGE
   Good: "Include JSDoc comments on exported functions"
   Bad: "You should probably add comments"

3. PROVIDE EXAMPLES
   Good: Show code snippets of correct patterns
   Bad: Just describe abstractly

4. KEEP RULES FOCUSED
   Good: One file per topic (testing.md, api-design.md)
   Bad: One massive file with everything

5. USE PATH RESTRICTIONS SPARINGLY
   Good: Only when rules truly apply to specific file types
   Bad: Adding paths to every rule unnecessarily

6. ORGANIZE WITH SUBDIRECTORIES
   Good: frontend/react.md, backend/api.md
   Bad: react-frontend-components-rules.md
```

### Category Organization

```
.claude/rules/
├── code-style/
│   ├── formatting.md      # Indentation, line length, etc.
│   ├── naming.md          # Variable/function naming conventions
│   └── imports.md         # Import organization
├── testing/
│   ├── unit-tests.md      # Unit testing conventions
│   ├── integration.md     # Integration testing
│   └── mocking.md         # Mock patterns
├── security/
│   ├── authentication.md  # Auth patterns
│   ├── validation.md      # Input validation
│   └── secrets.md         # Secret handling
├── workflow/
│   ├── git.md             # Git conventions
│   ├── pr-reviews.md      # PR review process
│   └── deployment.md      # Deployment procedures
└── api-design.md          # API design guidelines
```

### Anti-Hallucination Guidelines

**CRITICAL**: When creating rules:

1. **Verify existing patterns first** - Don't assume conventions, check the actual codebase
2. **Reference real code** - Base rules on actual patterns found in the project
3. **Don't invent standards** - If no convention exists, ask the user before creating one
4. **Check for conflicts** - Ensure new rules don't contradict existing ones

## Usage

```bash
# Create a new rule with name only (interactive)
/claude:create-rule code-style

# Create with description
/claude:create-rule testing "Enforce 80% coverage and describe blocks for tests"

# Create in a subdirectory
/claude:create-rule frontend/react "Component patterns and hooks usage"

# Create path-specific rule
/claude:create-rule api-validation "Input validation for API endpoints" --paths "src/api/**/*.ts"
```

## Examples

### Example 1: Simple Code Style Rule

```bash
/claude:create-rule formatting "Use 2-space indentation and single quotes"
```

Creates `.claude/rules/formatting.md`:
```markdown
# Code Formatting

Consistent formatting rules for the codebase.

## Guidelines

- Use 2-space indentation (no tabs)
- Use single quotes for strings (except when string contains single quote)
- Maximum line length: 100 characters
- Add trailing commas in multi-line arrays/objects

## Examples

### Good
\`\`\`typescript
const config = {
  name: 'my-app',
  version: '1.0.0',
};
\`\`\`

### Avoid
\`\`\`typescript
const config = {
    name: "my-app",
    version: "1.0.0"
}
\`\`\`
```

### Example 2: Path-Specific Rule

```bash
/claude:create-rule api-errors "Standard error handling for API routes"
```

Creates `.claude/rules/api-errors.md`:
```markdown
---
paths: src/api/**/*.ts, src/routes/**/*.ts
---

# API Error Handling

Standard error response format for all API endpoints.

## Guidelines

- Use the `ApiError` class for all error responses
- Include error code, message, and optional details
- Log errors with appropriate severity levels
- Never expose internal error details to clients

## Error Response Format

\`\`\`typescript
interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}
\`\`\`

## Examples

### Good
\`\`\`typescript
throw new ApiError('VALIDATION_ERROR', 'Invalid email format', { field: 'email' });
\`\`\`

### Avoid
\`\`\`typescript
throw new Error(err.stack); // Exposes internal details
\`\`\`
```

### Example 3: User-Level Rule

```bash
/claude:create-rule --user preferences "Personal coding preferences"
```

Creates `~/.claude/rules/preferences.md`:
```markdown
# Personal Preferences

My personal coding preferences applied to all projects.

## Guidelines

- Prefer functional programming patterns over OOP
- Use descriptive variable names (no single letters except loop indices)
- Add TODO comments with my GitHub username: @myusername
- Prefer async/await over raw promises
```

## Important Notes

- **Test with `/memory`**: After creating a rule, run `/memory` to verify it's loaded
- **Path patterns**: Use `paths` frontmatter only when rules apply to specific files
- **Subdirectories**: Organize rules into subdirectories for larger projects
- **Symlinks supported**: Share common rules across projects with symlinks
- **CLAUDE.local.md**: For personal project preferences not committed to git
- **Imports**: Use `@path/to/file` syntax in CLAUDE.md to import other files
- **Priority**: Project rules override user rules; more specific paths override general

## Output

After running this command, you will have:

1. A new `.md` file in the appropriate rules directory
2. Properly structured frontmatter (if path-specific)
3. Clear, specific, actionable guidelines
4. Examples showing correct and incorrect patterns
5. Verification that rules don't conflict with existing ones

---

**Reference**: https://code.claude.com/docs/en/memory.md
**Output Locations**:
- Project: `.claude/rules/`
- User: `~/.claude/rules/`
- Direct: `./CLAUDE.md` or `~/.claude/CLAUDE.md`
