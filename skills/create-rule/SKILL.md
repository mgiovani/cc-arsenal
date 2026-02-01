---
name: create-rule
description: "Create a new memory rule following Claude Code best practices for project instructions, coding standards, and workflow guidelines. This skill should be used when users want to create CLAUDE.md rules, .claude/rules/ files, or memory instructions for Claude Code."
disable-model-invocation: true
argument-hint: "<rule-name> [description]"
allowed-tools: ["Read", "Write", "Edit", "Grep", "Glob", "Bash(git *)", "Bash(mkdir *)", "Task", "TodoWrite", "AskUserQuestion"]
---

# Create Memory Rule

Generate a new memory rule following Claude Code best practices for project instructions, coding standards, and workflow guidelines.

> **Note**: Claude Code has merged commands into skills (v2.1.3+). This skill creates **memory rules** (CLAUDE.md entries and `.claude/rules/` files), not skills or commands.
>
> For the memory hierarchy and rule file specifications, see [references/memory-hierarchy.md](references/memory-hierarchy.md).
> For glob patterns and rule examples, see [references/rule-examples.md](references/rule-examples.md).

## Reference Documentation

- Claude Code memory documentation: https://code.claude.com/docs/en/memory

## Anti-Hallucination Guidelines

**CRITICAL**: When creating rules:

1. **Verify existing patterns first** - Don't assume conventions, check the actual codebase
2. **Reference real code** - Base rules on actual patterns found in the project
3. **Don't invent standards** - If no convention exists, ask the user before creating one
4. **Check for conflicts** - Ensure new rules don't contradict existing ones
5. **Validate frontmatter** - Only use `paths` frontmatter for `.claude/rules/` files

## Your Task

### Phase 0: Gather Up-to-Date Documentation (Use claude-code-guide Agent)

**CRITICAL**: Before creating any rule, fetch the latest official documentation:

```
Use Task tool with claude-code-guide agent:
- prompt: "I need to create a new Claude Code memory rule. Please research and provide:

    1. **Rules File Specification**:
       - Current frontmatter format (paths field syntax)
       - Glob pattern support and limitations
       - File naming and organization conventions

    2. **Memory Hierarchy**:
       - Current loading order (enterprise, project, user, etc.)
       - Priority rules when conflicts occur
       - Path specificity rules

    3. **CLAUDE.md Best Practices**:
       - Current structure recommendations
       - Import syntax (@path/to/file)
       - Section organization patterns

    4. **Recent Changes**:
       - Any new frontmatter fields
       - New memory features or capabilities
       - Deprecated patterns to avoid

    Return specific, actionable information with examples."
- subagent_type: "claude-code-guide"
```

### Phase 1: Understand Context (Use Explore Agent)

Understand the codebase context to create relevant rules:

```
Use Task tool with Explore agent:
- prompt: "The user wants to create a rule called [RULE_NAME] with description: [DESCRIPTION]. Search the codebase to understand: 1) Existing CLAUDE.md files and their structure, 2) Existing .claude/rules/ if any, 3) Relevant code patterns the rule should enforce. Return findings with file paths."
- subagent_type: "Explore"
- model: "haiku"
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

Spawn parallel Explore agents with model: haiku to gather patterns:

```
Agent 1 - Analyze Existing Memory:
- prompt: "Read any existing CLAUDE.md files and .claude/rules/*.md in the project. Extract common patterns: structure, formatting, specificity level. Return best practices observed."
- subagent_type: "Explore"
- model: "haiku"

Agent 2 - Identify Rule Category:
- prompt: "Search existing rules in .claude/rules/ directory. Analyze the category structure used (code-style, testing, security, etc.). Based on '[DESCRIPTION]', which existing category best fits? Return recommended category, filename, and examples of similar rules."
- subagent_type: "Explore"
- model: "haiku"

Agent 3 - Check for Conflicts:
- prompt: "Search for existing rules that might conflict with or overlap '[DESCRIPTION]'. Check CLAUDE.md files and .claude/rules/. Return any potential conflicts or opportunities to consolidate."
- subagent_type: "Explore"
- model: "haiku"
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

Generate the rule following the templates in [references/rule-examples.md](references/rule-examples.md).

**For path-specific rules** (with frontmatter):

```markdown
---
paths: src/**/*.ts, lib/**/*.ts
---

# [Rule Title]

[Brief description of what this rule enforces]

## Guidelines

- [Specific instruction 1]
- [Specific instruction 2]

## Examples

### Good
[Example of correct pattern]

### Avoid
[Example of pattern to avoid]
```

**For general rules** (no frontmatter):

```markdown
# [Rule Title]

[Brief description of what this rule enforces]

## Guidelines

- [Specific instruction 1]
- [Specific instruction 2]

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

- **BE SPECIFIC**: "Use 2-space indentation for TypeScript files" not "Format code properly"
- **USE IMPERATIVE LANGUAGE**: "Include JSDoc comments on exported functions" not "You should probably add comments"
- **PROVIDE EXAMPLES**: Show code snippets of correct patterns
- **KEEP RULES FOCUSED**: One file per topic (testing.md, api-design.md)
- **USE PATH RESTRICTIONS SPARINGLY**: Only when rules truly apply to specific file types

## Usage

```bash
# Create a new rule with name only (interactive)
/create-rule code-style

# Create with description
/create-rule testing "Enforce 80% coverage and describe blocks for tests"

# Create in a subdirectory
/create-rule frontend/react "Component patterns and hooks usage"
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

After running this skill, you will have:

1. A new `.md` file in the appropriate rules directory
2. Properly structured frontmatter (if path-specific)
3. Clear, specific, actionable guidelines
4. Examples showing correct and incorrect patterns
5. Verification that rules don't conflict with existing ones

---

**Reference**: https://code.claude.com/docs/en/memory
**Output Locations**:
- Project: `.claude/rules/`
- User: `~/.claude/rules/`
- Direct: `./CLAUDE.md` or `~/.claude/CLAUDE.md`
