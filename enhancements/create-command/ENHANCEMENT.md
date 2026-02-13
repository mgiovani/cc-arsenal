---
# Enhancement for: create-command
disable-model-invocation: true
argument-hint: "<command-name> [description]"
allowed-tools: "Read, Write, Grep, Glob, Bash(git *), Bash(mkdir *), Task, TodoWrite, WebFetch"
---

## Claude Code Enhanced Features

This skill includes the following Claude Code-specific enhancements:

## Reference Documentation

- Official skills documentation: https://code.claude.com/docs/en/skills
- For complete frontmatter field reference, see [references/frontmatter-guide.md](references/frontmatter-guide.md)
- For design patterns (SubAgent, TodoWrite, anti-hallucination), see [references/design-patterns.md](references/design-patterns.md)

## Your Task

### Phase 0: Gather Up-to-Date Documentation (Use claude-code-guide Agent)

**CRITICAL**: Before creating any skill, fetch the latest official documentation:

```
Use Task tool with claude-code-guide agent:
- prompt: "I need to create a new Claude Code skill. Please research and provide:

    1. **SKILL.md Frontmatter Specification**:
       - Complete list of frontmatter fields (name, description, context, agent, etc.)
       - Required vs optional fields
       - String substitution variables ($0, $1, $ARGUMENTS for all args)
       - New fields like 'context', 'agent', 'user-invocable'

    2. **Skill Architecture**:
       - Current directory structure (SKILL.md, scripts/, references/, assets/)
       - Progressive disclosure design principles
       - When to use each resource type

    3. **allowed-tools Best Practices**:
       - Complete list of available tools
       - Tool permission patterns (e.g., 'Bash(git *)' syntax)
       - Security recommendations for tool access

    4. **Recent Changes**:
       - Any breaking changes in skill format
       - New features or capabilities
       - Deprecated patterns to avoid

    Return specific, actionable information with examples that match the current API."
- subagent_type: "claude-code-guide"
```

### Phase 1: Understand Requirements (Use Explore Agent)

Understand what the user wants to create:

```
Use Task tool with Explore agent:
- prompt: "The user wants to create a skill called [SKILL_NAME] with description: [DESCRIPTION]. Search the codebase to understand: 1) Similar existing skills we can reference, 2) Relevant code/configs the skill might interact with, 3) What tools the skill will likely need. Return findings with file paths."
- subagent_type: "Explore"
- model: "haiku"
```

### Phase 2: Parse Arguments

1. **Extract skill name** from `$1` or first word of `$ARGUMENTS`
2. **Extract description** from remaining arguments or ask user
3. **Determine skill location**:
   - Project skill: `.claude/skills/<name>/SKILL.md` (shared with team)
   - User skill: `~/.claude/skills/<name>/SKILL.md` (personal)
4. **Determine if supporting files are needed** (references/, scripts/, assets/)

### Phase 3: Gather Skill Requirements

Ask user or infer from context:

```
Questions to determine:
1. What is the primary purpose of this skill?
2. What tools does it need? (Bash, Read, Write, Edit, Grep, Glob, Task, TodoWrite, etc.)
3. What arguments does it accept?
4. Should Claude invoke this automatically, or only when the user runs it? (disable-model-invocation)
5. Should it use SubAgents for complex operations?
6. Should it track progress with TodoWrite?
7. Does it need supporting files? (references/ for docs, scripts/ for code, assets/ for templates)
8. Should it run in a forked subagent context? (context: fork)
```

### Phase 4: Analyze Similar Skills (Use SubAgents)

Spawn parallel Explore agents with model: haiku to gather patterns from existing skills:

```
Agent 1 - Analyze Existing Skills:
- prompt: "Read the skills in .claude/skills/ directory. Extract common patterns: frontmatter structure, phase organization, tool usage. Return best practices observed."
- subagent_type: "Explore"
- model: "haiku"

Agent 2 - Analyze Tool Requirements:
- prompt: "Based on skill description '[DESCRIPTION]', analyze existing skills that have similar functionality. What tools do they use? Return recommended allowed-tools list based on actual usage patterns."
- subagent_type: "Explore"
- model: "haiku"

Agent 3 - Analyze Verification Patterns:
- prompt: "For a skill that [DESCRIPTION], search existing skills for anti-hallucination and verification patterns. Return specific verification checks used in similar skills."
- subagent_type: "Explore"
- model: "haiku"
```

### Phase 5: Generate Skill Structure

Use TodoWrite to track skill creation:

```
TodoWrite:
- [ ] Create skill directory structure
- [ ] Create SKILL.md with frontmatter
- [ ] Add anti-hallucination guidelines
- [ ] Define task phases with Explore/SubAgents
- [ ] Add verification steps
- [ ] Create supporting files if needed (references/, scripts/, assets/)
- [ ] Include examples and usage
- [ ] Validate skill structure
```

### Phase 6: Write Skill Files

Generate the skill following the template structure. For the complete template and all frontmatter options, see [references/frontmatter-guide.md](references/frontmatter-guide.md). For design patterns, see [references/design-patterns.md](references/design-patterns.md).

**Skill directory structure:**

```
skill-name/
├── SKILL.md           # Core instructions (required, keep under 500 lines)
├── references/        # Documentation loaded as needed (optional)
│   └── *.md
├── scripts/           # Executable code (optional)
│   └── *.py / *.sh
└── assets/            # Files used in output (optional)
    └── templates, images, etc.
```

**SKILL.md template:**

```markdown
---
name: "[skill-name]"
description: "[Clear, concise description - what it does and when to use it]"
disable-model-invocation: true
argument-hint: "[argument-pattern]"
allowed-tools: Read, Write, Edit, Grep, Glob, Task, TodoWrite
---

# [Skill Title]

[Brief description of what this skill does]

## Workflow

### Phase 1: [Initial Analysis] (Use Explore Agent)

**IMPORTANT**: [Why exploration is needed]

\`\`\`
Use Task tool with Explore agent:
- prompt: "[Specific exploration prompt]"
- subagent_type: "Explore"
\`\`\`

### Phase 2: [Core Logic]

[Main steps of the skill]

### Phase 3: Verification

**Before completing, verify**:
\`\`\`
1. [Verification check 1]
2. [Verification check 2]
3. [Final validation]
\`\`\`

## Examples

[Concrete examples of skill usage and expected output]
```

### Phase 7: Validate Generated Skill

Before writing, verify:

```
1. Frontmatter is valid YAML
2. description clearly states what the skill does and when to use it
3. allowed-tools only includes necessary tools
4. argument-hint matches expected usage
5. Anti-hallucination guidelines are specific to skill domain
6. Explore agent is used for initial context gathering
7. SubAgents are used where parallelization helps
8. TodoWrite is used for multi-step operations
9. Verification steps are concrete and actionable
10. Examples are realistic
11. SKILL.md is under 500 lines
12. Supporting files (references/, scripts/) are created if content is extensive
```

### Phase 8: Write and Report

1. Create the skill directory at appropriate location
2. Create SKILL.md with proper frontmatter and content
3. Create any supporting files (references/, scripts/, assets/)
4. Report what was created
5. Suggest next steps (testing, customization)

## Output

After running this skill, the user will have:

1. A new skill directory in the appropriate skills location
2. A SKILL.md file with proper frontmatter and optimal tool permissions
3. Anti-hallucination guidelines specific to the skill's domain
4. Phase-based workflow with Explore agents and SubAgents
5. Progress tracking with TodoWrite (if applicable)
6. Verification steps to ensure accuracy
7. Supporting files if the skill requires extensive reference material
8. Usage examples and documentation

---

**Reference**: https://code.claude.com/docs/en/skills
**Output Location**: `.claude/skills/<name>/` or `~/.claude/skills/<name>/`
