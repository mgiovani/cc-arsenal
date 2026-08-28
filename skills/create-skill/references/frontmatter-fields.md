# Frontmatter field reference

Full reference for SKILL.md YAML frontmatter fields beyond the basics covered in Phase 3. Consult this when a skill needs argument substitution or an isolated execution context.

## All fields

```yaml
---
name: my-skill                     # kebab-case, becomes /slash-command
description: "What it does..."     # when Claude should use it — the trigger mechanism
disable-model-invocation: true     # user-invoked only; skip for skills with side effects
argument-hint: "[args]"            # shown in autocomplete
allowed-tools: Read, Write, Bash   # only list tools actually used
license: MIT                       # optional
compatibility: ...                 # optional, rarely used
metadata:                          # optional: author, version, source
  author: name
  version: 1.0.0
context: fork                      # run in an isolated subagent (see below)
agent: Explore                     # subagent type when context: fork is set
hooks:                             # lifecycle hooks scoped to this skill
  PreToolUse:
    - matcher: Bash(git commit*)
      hooks: [...]
---
```

Validate against `scripts/quick_validate.py`: it enforces this exact key set and rejects anything else, since unknown keys silently break skill loading.

## `context: fork` (Isolated subagent pattern)

Used by `docs-adr`, `review-security`, `team-implement`, and others in this repo for skills that should run without the calling conversation's history: the SKILL.md content becomes the *entire* prompt for the subagent, not an addition to context.

```yaml
---
name: pr-summary
description: Summarize changes in a pull request
context: fork
agent: general-purpose
---

## Pull request context
- PR diff: !`gh pr diff`
- PR comments: !`gh pr view --comments`

## Task
Summarize this pull request...
```

Use this when the skill's job is self-contained (e.g., "analyze this PR and report back") rather than conversational. Don't use it for skills that need to reference what the user already said earlier in the session: that context won't be there.

## Argument substitution

| Variable | Description |
|----------|-------------|
| `$ARGUMENTS` | All arguments passed when invoking the skill |
| `$0`, `$1`, `$2`... | Specific argument by 0-based index |

If the skill body never references `$ARGUMENTS`, any arguments passed are appended automatically as `ARGUMENTS: <value>` at the end.

## Dynamic context injection

The `` !`command` `` syntax runs a shell command before the skill content reaches Claude; the command's output replaces the placeholder inline. Used in `docs-init`, `docs-update`, `git-commit`, `git-release` for injecting live repo state (diffs, current file contents) without a separate tool call.

```markdown
## Current state
- Changed files: !`git diff --name-only`
```
