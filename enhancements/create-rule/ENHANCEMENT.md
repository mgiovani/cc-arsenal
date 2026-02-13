---
# Enhancement for: create-rule
disable-model-invocation: true
argument-hint: "<rule-name> [description]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Bash(git *)
  - Bash(mkdir *)
  - Task
  - TodoWrite
  - AskUserQuestion
---

## Claude Code Enhanced Features

This skill includes the following Claude Code-specific enhancements:

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
