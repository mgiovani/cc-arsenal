---
description: "Create a new slash command following best practices and prompt engineering techniques"
argument-hint: "<command-name> [description]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash(git *)", "Bash(mkdir *)", "Task", "TodoWrite", "WebFetch"]
---

# Create Slash Command

Generate a new slash command following Claude Code best practices, prompt engineering techniques, and anti-hallucination patterns.

## Reference Documentation

Claude Code slash commands documentation: https://code.claude.com/docs/en/slash-commands.md

## Your Task

### Phase 0: Gather Up-to-Date Documentation (Use claude-code-guide Agent)

**CRITICAL**: Before creating any command, fetch the latest official documentation:

```
Use Task tool with claude-code-guide agent:
- prompt: "I need to create a new Claude Code slash command. Please research and provide:

    1. **COMMAND.md Specification**:
       - Current frontmatter fields (required vs optional)
       - Exact format and syntax for each field
       - Any new fields added recently
       - Any deprecated fields to avoid

    2. **allowed-tools Best Practices**:
       - Complete list of available tools
       - Tool permission patterns (e.g., 'Bash(git *)' syntax)
       - Security recommendations for tool access

    3. **Command Design Patterns**:
       - Current recommended structure for command content
       - Best practices for subagent usage in commands
       - Anti-hallucination patterns

    4. **Recent Changes**:
       - Any breaking changes in command format
       - New features or capabilities

    Return specific, actionable information with examples that match the current API."
- subagent_type: "claude-code-guide"
```

### Phase 1: Understand Requirements (Use Explore Agent)

First, understand what the user wants to create:

```
Use Task tool with Explore agent:
- prompt: "The user wants to create a command called [COMMAND_NAME] with description: [DESCRIPTION]. Search the codebase to understand: 1) Similar existing commands we can reference, 2) Relevant code/configs the command might interact with, 3) What tools the command will likely need. Return findings with file paths."
- subagent_type: "Explore"
- model: "haiku"
```

### Phase 2: Parse Arguments

1. **Extract command name** from `$1` or first word of `$ARGUMENTS`
2. **Extract description** from remaining arguments or ask user
3. **Determine command location**:
   - Project command: `.claude/commands/` (shared with team)
   - User command: `~/.claude/commands/` (personal)
4. **Determine namespace** (subdirectory) if applicable

### Phase 3: Gather Command Requirements

Ask user or infer from context:

```
Questions to determine:
1. What is the primary purpose of this command?
2. What tools does it need? (Bash, Read, Write, Edit, Grep, Glob, Task, TodoWrite, etc.)
3. What arguments does it accept?
4. Should it use SubAgents for complex operations?
5. Should it track progress with TodoWrite?
6. What verification steps are needed?
```

### Phase 4: Analyze Similar Commands (Use SubAgents)

Spawn parallel Explore agents with model: haiku to gather patterns from existing commands:

```
Agent 1 - Analyze Existing Commands:
- prompt: "Read the commands in commands/ directory. Extract common patterns: frontmatter structure, phase organization, tool usage. Return best practices observed."
- subagent_type: "Explore"
- model: "haiku"

Agent 2 - Analyze Tool Requirements:
- prompt: "Based on command description '[DESCRIPTION]', analyze existing commands that have similar functionality. What tools do they use? Return recommended allowed-tools list based on actual usage patterns."
- subagent_type: "Explore"
- model: "haiku"

Agent 3 - Analyze Verification Patterns:
- prompt: "For a command that [DESCRIPTION], search existing commands for anti-hallucination and verification patterns. Return specific verification checks used in similar commands."
- subagent_type: "Explore"
- model: "haiku"
```

### Phase 5: Generate Command Structure

Use TodoWrite to track command creation:

```
TodoWrite:
- [ ] Create command file with frontmatter
- [ ] Add anti-hallucination guidelines
- [ ] Define task phases with Explore/SubAgents
- [ ] Add verification steps
- [ ] Include examples and usage
- [ ] Validate command syntax
```

### Phase 6: Write Command File

Generate the command following this template structure:

```markdown
---
description: "[Clear, concise description - max 80 chars]"
argument-hint: "[argument-pattern]"
allowed-tools: ["Tool1", "Tool2", "Task", "TodoWrite"]
---

# [Command Title]

[Brief description of what this command does]

## Anti-Hallucination Guidelines

**CRITICAL**: [Specific guidelines for this command type]
1. [Verification requirement 1]
2. [Verification requirement 2]
3. [Domain-specific check]

## Your Task

### Phase 1: [Initial Analysis] (Use Explore Agent)

**IMPORTANT**: [Why exploration is needed for this command]

\`\`\`
Use Task tool with Explore agent:
- prompt: "[Specific exploration prompt for this command's domain]"
- subagent_type: "Explore"
\`\`\`

### Phase 2: [Core Logic]

[Main steps of the command]

### Phase 3: Parallel Processing (Use SubAgents)

[If command benefits from parallelization]

\`\`\`
Agent 1 - [Aspect 1]:
- prompt: "[Specific task]"
- subagent_type: "[type]"

Agent 2 - [Aspect 2]:
- prompt: "[Specific task]"
- subagent_type: "[type]"
\`\`\`

### Phase 4: Track Progress (TodoWrite)

[If command has multiple steps to track]

\`\`\`
TodoWrite:
- [ ] Step 1
- [ ] Step 2
- [ ] Step 3
\`\`\`

### Phase 5: Verification

**Before completing, verify**:
\`\`\`
1. [Verification check 1]
2. [Verification check 2]
3. [Final validation]
\`\`\`

## Usage

\`\`\`
/[command-name]
/[command-name] [with arguments]
\`\`\`

## Examples

[Concrete examples of command usage and expected output]

## Important Notes

- [Key consideration 1]
- [Key consideration 2]
- [Safety/security notes if applicable]
```

### Phase 7: Validate Generated Command

Before writing, verify:

```
1. Frontmatter is valid YAML
2. description is clear and under 80 characters
3. allowed-tools only includes necessary tools
4. argument-hint matches expected usage
5. Anti-hallucination guidelines are specific to command domain
6. Explore agent is used for initial context gathering
7. SubAgents are used where parallelization helps
8. TodoWrite is used for multi-step operations
9. Verification steps are concrete and actionable
10. Examples are realistic
```

### Phase 8: Write and Report

1. Create the command file at appropriate location
2. Report what was created
3. Suggest next steps (testing, customization)

## Command Design Principles

### Frontmatter Best Practices

```yaml
---
# Required
description: "Clear, action-oriented description"

# Recommended
argument-hint: "[required-arg] [optional-arg]"
allowed-tools: ["Only", "Necessary", "Tools"]

# Optional
model: "claude-3-5-haiku-20241022"  # For simple commands
disable-model-invocation: true      # If shouldn't be called by SlashCommand tool
---
```

### Tool Selection Guide

| Use Case | Recommended Tools |
|----------|-------------------|
| File operations | `Read`, `Write`, `Edit`, `Glob`, `Grep` |
| Git operations | `Bash(git *)` |
| GitHub operations | `Bash(gh *)` |
| Complex analysis | `Task` (with Explore or general-purpose agents) |
| Progress tracking | `TodoWrite` |
| Web research | `WebFetch`, `WebSearch` |
| User interaction | `AskUserQuestion` |

### Anti-Hallucination Patterns

```
For documentation commands:
- Verify files exist before describing them
- Count entities with actual commands, not estimates
- Reference real code, not assumed patterns

For code generation commands:
- Explore existing patterns first
- Verify imports/dependencies exist
- Check naming conventions in codebase

For analysis commands:
- Cross-reference claims with actual files
- Provide evidence (file paths, line numbers)
- Remove claims that cannot be verified
```

### SubAgent Usage Patterns

```
When to use Explore agent:
- Understanding codebase structure
- Finding relevant files/patterns
- Initial context gathering

When to use general-purpose agent:
- Semantic analysis of content
- Complex reasoning tasks
- Multi-step operations

When to parallelize:
- Analyzing multiple files independently
- Checking different aspects of same content
- Gathering information from different sources
```

## Usage

```bash
# Create a new command with name only
/claude:create-command my-command

# Create with description
/claude:create-command my-command "Generate unit tests for modified files"

# Create in a namespace
/claude:create-command testing/generate-tests "Generate unit tests"
```

## Examples

### Example 1: Simple Utility Command

```bash
/claude:create-command cleanup "Remove unused imports and format code"
```

Creates:
```markdown
---
description: "Remove unused imports and format code"
allowed-tools: ["Read", "Edit", "Bash(git diff:*)"]
---

# Code Cleanup

Remove unused imports and format code in modified files.

## Anti-Hallucination Guidelines
...
```

### Example 2: Complex Analysis Command

```bash
/claude:create-command security-audit "Analyze codebase for security vulnerabilities"
```

Creates a command with:
- Explore agent for finding security-relevant code
- Parallel SubAgents for different vulnerability types
- TodoWrite for tracking audit progress
- Verification steps for each finding

## Important Notes

- **Test your command**: After creation, run it to verify it works as expected
- **Iterate**: Commands can be edited; start simple and add complexity
- **Tool permissions**: Be specific with Bash commands (e.g., `Bash(git status:*)` not `Bash(*)`)
- **Documentation**: Good commands are self-documenting with clear examples
- **Namespacing**: Use subdirectories to organize related commands

## Output

After running this command, you will have:

1. A new `.md` file in the appropriate commands directory
2. Properly structured frontmatter with optimal tool permissions
3. Anti-hallucination guidelines specific to your command's domain
4. Phase-based task structure with Explore agents and SubAgents
5. Progress tracking with TodoWrite (if applicable)
6. Verification steps to ensure accuracy
7. Usage examples and documentation

---

**Reference**: https://code.claude.com/docs/en/slash-commands
**Output Location**: `.claude/commands/` or `~/.claude/commands/`
