# SKILL.md Frontmatter Reference

Complete reference for all available YAML frontmatter fields in SKILL.md files.

## All Frontmatter Fields

```yaml
---
name: my-skill                     # Display name, becomes /slash-command
description: "What it does"         # When to use it (third-person, recommended)
disable-model-invocation: true      # Prevent Claude from auto-loading (default: false)
user-invocable: false               # Hide from / menu (default: true)
argument-hint: "[args]"             # Hint shown in autocomplete
allowed-tools: Read, Write, Bash    # Tools Claude can use without asking
model: claude-3-5-haiku-20241022    # Model override for this skill
context: fork                       # Run in a forked subagent context
agent: Explore                      # Agent type when context: fork is set
---
```

### Field Details

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `name` | No | Directory name | Lowercase letters, numbers, hyphens only (max 64 chars). Becomes the `/slash-command` |
| `description` | Recommended | First paragraph | What the skill does and when to use it. Claude uses this for auto-invocation decisions |
| `disable-model-invocation` | No | `false` | Set `true` for skills with side effects (file creation, deployments, git operations) |
| `user-invocable` | No | `true` | Set `false` for background knowledge skills that should not appear in `/` menu |
| `argument-hint` | No | None | Displayed during autocomplete. Example: `[issue-number]` or `[filename] [format]` |
| `allowed-tools` | No | None | Comma-separated list of tools Claude can use without per-use approval |
| `model` | No | Current model | Override the model used when this skill is active |
| `context` | No | None | Set to `fork` to run in an isolated subagent context |
| `agent` | No | `general-purpose` | Which subagent to use with `context: fork`. Options: `Explore`, `Plan`, `general-purpose`, or custom agent name |
| `hooks` | No | None | Hooks scoped to this skill's lifecycle |

### Invocation Matrix

| Frontmatter | User Can Invoke | Claude Can Invoke | Context Loading |
|-------------|----------------|-------------------|-----------------|
| (default) | Yes | Yes | Description always in context; full skill loads when invoked |
| `disable-model-invocation: true` | Yes | No | Description NOT in context; loads only when user invokes |
| `user-invocable: false` | No | Yes | Description always in context; loads when Claude invokes |

## String Substitution Variables

| Variable | Description |
|----------|-------------|
| `$ARGUMENTS` | All arguments passed when invoking the skill |
| `$ARGUMENTS[N]` | Specific argument by 0-based index (e.g., `$ARGUMENTS[0]`) |
| `$N` | Shorthand for `$ARGUMENTS[N]` (e.g., `$0`, `$1`) |
| `${CLAUDE_SESSION_ID}` | Current session ID for logging or session-specific files |

**Behavior when `$ARGUMENTS` is absent**: If the skill content does not contain `$ARGUMENTS`, any arguments passed are automatically appended as `ARGUMENTS: <value>` at the end of the skill content.

## Dynamic Context Injection

The `` !`command` `` syntax runs shell commands before skill content is sent to Claude. The command output replaces the placeholder.

```yaml
---
name: pr-summary
description: Summarize changes in a pull request
context: fork
agent: Explore
---

## Pull request context
- PR diff: !`gh pr diff`
- PR comments: !`gh pr view --comments`

## Task
Summarize this pull request...
```

## allowed-tools Patterns

### Common Tool Names

| Tool | Purpose |
|------|---------|
| `Read` | Read files |
| `Write` | Write/create files |
| `Edit` | Edit existing files |
| `Grep` | Search file contents |
| `Glob` | Find files by pattern |
| `Bash` | Execute shell commands (use patterns below) |
| `Task` | Spawn subagents |
| `TodoWrite` | Track progress with todo lists |
| `WebFetch` | Fetch web content |
| `WebSearch` | Search the web |
| `AskUserQuestion` | Ask the user a question |
| `EnterPlanMode` | Switch to planning mode |

### Bash Permission Patterns

```yaml
# Specific command prefixes
allowed-tools: Bash(git *), Bash(npm *), Bash(make *)

# Multiple patterns
allowed-tools: Bash(git *), Bash(gh *), Bash(mkdir *)

# Avoid overly broad patterns
# Bad:  Bash(*)
# Good: Bash(git *), Bash(npm test *)
```

## Best Practices

### Description Writing

- Write in **third-person imperative** form
- Include **when to use** the skill (trigger conditions)
- Be specific enough for Claude to make good auto-invocation decisions
- Example: "Create numbered Architecture Decision Records (ADR) documenting architectural decisions. This skill should be used when users want to document an architectural decision, create an ADR, or record technical choices."

### disable-model-invocation

Set to `true` when the skill:
- Creates files or directories
- Modifies git state (commits, branches)
- Performs deployments
- Sends messages or notifications
- Has any side effects the user should control

### allowed-tools

- Only include tools the skill actually needs
- Be specific with Bash patterns
- Include `Task` if the skill uses subagents
- Include `TodoWrite` if the skill tracks multi-step progress
