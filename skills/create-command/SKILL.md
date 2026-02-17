---
name: create-command
description: Create a new slash command (skill) following best practices and prompt
  engineering techniques. This skill should be used when users want to create a new
  slash command, skill, or custom workflow for Claude Code.
metadata:
  author: mgiovani
  version: 1.0.0
  source: https://github.com/mgiovani/skills
disable-model-invocation: true
argument-hint: <command-name> [description]
allowed-tools: Read, Write, Grep, Glob, Bash(git *), Bash(mkdir *), Task, TodoWrite,
  WebFetch
---

# Create Command

> **Deprecated**: Prefer `/create-skill` which fetches live specifications, researches multi-source examples, and uses interactive planning with user approval gates. `create-command` is maintained for backward compatibility but lacks the modern workflow and up-to-date documentation fetching of `create-skill`.

> **Cross-Platform AI Agent Skill**
> This skill works with any AI agent platform that supports the skills.sh standard.

# Create Skill (Slash Command)

Generate a new skill following Claude Code best practices, prompt engineering techniques, and anti-hallucination patterns.

> **Note**: Claude Code has merged commands into skills (v2.1.3+). Files in `.claude/commands/` still work, but the recommended approach is to create skills in `.claude/skills/` which support additional features: supporting files (references/, scripts/, assets/), model invocation control, subagent execution, and progressive disclosure. This skill generates skills by default.
>
> **Relationship to skill-creator**: The `skill-creator` skill provides *guidance* on creating skills. This skill (`create-command`) *generates* the actual skill files. They complement each other.

## Reference Documentation

- Official skills documentation: https://code.claude.com/docs/en/skills
- For complete frontmatter field reference, see [references/frontmatter-guide.md](references/frontmatter-guide.md)
- For design patterns (SubAgent, TodoWrite, anti-hallucination), see [references/design-patterns.md](references/design-patterns.md)

## Your Task

### Phase 0: Gather Up-to-Date Documentation (Use claude-code-guide Agent)

**CRITICAL**: Before creating any skill, fetch the latest official documentation:

### Phase 1: Understand Requirements (Explore Codebase)

Understand what the user wants to create:

### Phase 2: Parse Arguments

1. **Extract skill name** from `$1` or first word of `command arguments`
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
### Phase 4: Analyze Similar Skills (Use Parallel Analysis)

Spawn parallel Explore agents with model: haiku to gather patterns from existing skills:

```
Agent 1 - Analyze Existing Skills:
- prompt: "Read the skills in .claude/skills/ directory. Extract common patterns: frontmatter structure, phase organization, tool usage. Return best practices observed."
- agent-type: "Explore"
- model: "haiku"

Agent 2 - Analyze Tool Requirements:
- prompt: "Based on skill description '[DESCRIPTION]', analyze existing skills that have similar functionality. What tools do they use? Return recommended required-capabilities list based on actual usage patterns."
- agent-type: "Explore"
- model: "haiku"

Agent 3 - Analyze Verification Patterns:
- prompt: "For a skill that [DESCRIPTION], search existing skills for anti-hallucination and verification patterns. Return specific verification checks used in similar skills."
- agent-type: "Explore"
- model: "haiku"
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
### Phase 6: Write Skill Files

Generate the skill following the template structure. For the complete template and all frontmatter options, see [references/frontmatter-guide.md](references/frontmatter-guide.md). For design patterns, see [references/design-patterns.md](references/design-patterns.md).

**Skill directory structure:**

```
skill-name/
├── SKILL.md # Core instructions (required, keep under 500 lines)
├── references/ # Documentation loaded as needed (optional)
│ └── *.md
├── scripts/ # Executable code (optional)
│ └── *.py / *.sh
└── assets/ # Files used in output (optional)
 └── templates, images, etc.
**SKILL.md template:**

```markdown

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
