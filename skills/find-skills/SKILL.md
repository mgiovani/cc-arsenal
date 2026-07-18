---
name: find-skills
description: Search, install, update, and remove third-party Agent Skills from skills.sh or any GitHub/GitLab repo via the `npx skills` CLI. Use when the user wants to "find a skill", "install a skill from github", "search skills.sh", or add third-party capabilities to Claude Code/Cursor/other agents. Not for authoring new skills (see create-skill).
disable-model-invocation: true
---

# Find Skills

Discover and install third-party agent skills from the open Agent Skills ecosystem powered by skills.sh.

## Overview

The **Agent Skills** format is an open standard for packaging procedural knowledge, workflows, and tools that AI agents load on demand. The `npx skills` CLI (maintained by Vercel Labs) serves as "npm for AI agents" -- enabling discovery and installation of community skills from any Git repository.

**skills.sh** is the public directory and leaderboard for the ecosystem, hosting thousands of skills across categories like frontend, backend, DevOps, and more.

Before installing a third-party skill, check `ls skills/` in this repo (or run `/find-skills` again after browsing) -- cc-arsenal may already cover the same ground, and a hardcoded list here would just go stale.

## Ask First, Never Mutate to "Show" Something

`add`, `remove`/`rm`, and `update` all touch the user's real filesystem (project `.claude/skills/` or global `~/.claude/skills/`) -- a wrong guess costs the user real state, not a free re-run. Two hard stops, both end the turn on a question rather than acting and reporting after:

- **Scope or target is ambiguous.** If it isn't clear which skill/repo to install, or whether it belongs at project vs. global scope, end your response with the clarifying question. Don't run `npx skills add` first and confirm after, and don't install to a throwaway/local mock "just to show the flow" -- that still runs a real command against the user's real directories. Ask, stop, and install only in a later turn once the user answers.
- **Any removal, one skill or all of them.** Removal is destructive and not undoable via the CLI. Run `npx skills list` (and `-g` if scope is unclear) to show what's actually installed, then end your response asking the user to confirm exactly what gets removed. Run `remove`/`rm`/`--all` only in a later turn, after the user replies with an explicit yes. The request is never the confirmation: "remove the foo skill, I don't use it anymore" names the action but does not green-light it -- if you catch yourself reasoning "the user already confirmed by naming it", that reasoning is exactly the failure this rule exists to stop.

If a source can't be verified (repo doesn't exist, network/auth error), report the failure and stop -- never substitute a synthetic local repo and install it to demonstrate what would have happened.

## Quick Start

### 1. Find Skills

```bash
# Interactive fuzzy search across skills.sh
npx skills find

# Search by keyword
npx skills find typescript
npx skills find react
npx skills find testing
```

### 2. Review Available Skills in a Repository

```bash
# List skills in a repository without installing
npx skills add owner/repo --list

# Example: list Vercel's official skills
npx skills add vercel-labs/agent-skills --list

# Example: list Anthropic's skills
npx skills add anthropics/skills --list
```

### 3. Install Skills

```bash
# Interactive installation (choose skills and target agents)
npx skills add owner/repo

# Install a specific skill for Claude Code
npx skills add owner/repo --skill skill-name -a claude-code

# Install globally (available across all projects)
npx skills add owner/repo --skill skill-name -a claude-code -g

# Install all skills from a repo to all detected agents
npx skills add owner/repo --all
```

## Worked Examples

Map the user's request to the right subcommand and scope before running anything:

| User says | Command |
|---|---|
| "find a skill for testing" | `npx skills find testing` |
| "install the frontend-design skill from vercel-labs/agent-skills for this project" | `npx skills add vercel-labs/agent-skills --skill frontend-design -a claude-code` |
| "install code-review globally so I have it everywhere" | `npx skills add owner/repo --skill code-review -a claude-code -g` |
| "what skills do I have installed?" | `npx skills list` |
| "remove the web-design-guidelines skill" | `npx skills list` to confirm it's installed, then ask "remove web-design-guidelines -- confirm?" and run `npx skills remove web-design-guidelines` only after a yes |

See "Ask First, Never Mutate to 'Show' Something" above for exactly when to end the turn on a question instead of running the command.

## Essential Commands

| Command | Purpose |
|---------|---------|
| `npx skills find [query]` | Search skills.sh directory |
| `npx skills add <source>` | Install skills from a repository |
| `npx skills list` | View installed skills |
| `npx skills check` | Check for available updates |
| `npx skills update` | Update all installed skills |
| `npx skills remove [name]` | Uninstall a skill |
| `npx skills init [name]` | Create a new skill template |

## Installation Scopes

**Project scope** (default): Installs to `.claude/skills/` in the current project directory. Committed with the project and shared with team members.

**Global scope** (`-g` flag): Installs to `~/.claude/skills/` in the home directory. Available across all projects for the current user.

**Recommendation**: Install domain-specific skills (e.g., a framework skill) at project scope. Install general-purpose skills (e.g., code review, testing patterns) at global scope.

## Source Formats

The `add` command accepts multiple source formats:

```bash
# GitHub shorthand (most common)
npx skills add owner/repo

# Full GitHub URL
npx skills add https://github.com/owner/repo

# Direct path to a specific skill
npx skills add https://github.com/owner/repo/tree/main/skills/skill-name

# GitLab URL
npx skills add https://gitlab.com/org/repo

# Local directory (for development)
npx skills add ./my-local-skills
```

## Key Repositories

| Repository | Description |
|------------|-------------|
| `vercel-labs/agent-skills` | Vercel's official skill collection (React, Next.js, design) |
| `anthropics/skills` | Anthropic's example skills |
| `mgiovani/cc-arsenal` | This repository -- see AGENTS.md or `ls skills/` for the current catalog |

## Reference Files

For detailed command reference, load: [references/commands.md](./references/commands.md)
- All CLI subcommands with complete flag documentation
- Source format details and installation paths
- Troubleshooting common issues

For discovery patterns and best practices, load: [references/workflows.md](./references/workflows.md)
- Discovery strategies by domain and framework
- Global vs project installation guidance
- Security review of skill sources
- Combining third-party skills with cc-arsenal
- Managing updates and versions

## Resources

- **Directory**: https://skills.sh
- **CLI Repository**: https://github.com/vercel-labs/skills
- **Open Specification**: https://agentskills.io
- **Anthropic Skills Docs**: https://code.claude.com/docs/en/skills
