# CLI Command Reference

Complete reference for the `npx skills` CLI tool (npm package: `skills`, maintained by Vercel Labs).

## Installation

The CLI requires no installation -- run directly via `npx`:

```bash
npx skills <command> [options]
```

Or install globally for faster execution:

```bash
npm install -g skills
skills <command> [options]
```

---

## Commands

### `find` -- Search the skills.sh Directory

Search for skills across the skills.sh ecosystem.

```bash
npx skills find              # Interactive fuzzy search (fzf-style)
npx skills find <query>      # Search by keyword
```

**Examples:**
```bash
npx skills find typescript
npx skills find react hooks
npx skills find "code review"
npx skills find testing
```

---

### `add` -- Install Skills from Repositories

Install skills from Git repositories into agent skill directories.

```bash
npx skills add <source> [options]
```

**Source formats:**

| Format | Example |
|--------|---------|
| GitHub shorthand | `owner/repo` |
| GitHub URL | `https://github.com/owner/repo` |
| Direct skill path | `https://github.com/owner/repo/tree/main/skills/name` |
| GitLab URL | `https://gitlab.com/org/repo` |
| Git SSH URL | `git@github.com:owner/repo.git` |
| Local directory | `./my-local-skills` |

**Flags:**

| Flag | Short | Description |
|------|-------|-------------|
| `--global` | `-g` | Install to home directory instead of project |
| `--agent <agents...>` | `-a` | Target specific agents (e.g., `claude-code`, `cursor`) |
| `--skill <skills...>` | `-s` | Install specific skills by name |
| `--list` | `-l` | List available skills without installing |
| `--yes` | `-y` | Skip confirmation prompts |
| `--all` | | Install all skills to all agents (no prompts) |

**Examples:**

```bash
# List available skills in a repo
npx skills add vercel-labs/agent-skills --list

# Interactive install (prompts for skill and agent selection)
npx skills add vercel-labs/agent-skills

# Install specific skill to Claude Code
npx skills add vercel-labs/agent-skills --skill frontend-design -a claude-code

# Install globally
npx skills add owner/repo --skill my-skill -a claude-code -g

# Non-interactive (for CI/CD or scripting)
npx skills add vercel-labs/agent-skills --skill frontend-design -g -a claude-code -y

# Install all skills to all detected agents
npx skills add vercel-labs/agent-skills --all

# Install from a local directory
npx skills add ./my-skills-repo
```

**Installation methods** (prompted during interactive install):
- **Symlink** (recommended): Creates symbolic links to a canonical copy. Single source of truth, easy to update.
- **Copy**: Creates independent copies for each agent. Use when symlinks are not supported.

---

### `list` (alias: `ls`) -- View Installed Skills

Display all installed skills across agents.

```bash
npx skills list [options]
npx skills ls [options]
```

**Flags:**

| Flag | Short | Description |
|------|-------|-------------|
| `--global` | `-g` | Show global skills only |
| `--agent <agents...>` | `-a` | Filter by specific agents |

**Examples:**

```bash
# All installed skills (project + global)
npx skills list

# Global skills only
npx skills ls -g

# Filter by agent
npx skills ls -a claude-code
npx skills ls -a claude-code -a cursor
```

---

### `remove` (alias: `rm`) -- Uninstall Skills

Remove installed skills.

```bash
npx skills remove [name] [options]
npx skills rm [name] [options]
```

**Flags:**

| Flag | Short | Description |
|------|-------|-------------|
| `--global` | `-g` | Remove from global scope |
| `--agent <agents...>` | `-a` | Target specific agents; use `'*'` for all |
| `--skill <skills...>` | `-s` | Specify skills to remove; use `'*'` for all |
| `--yes` | `-y` | Skip confirmation prompts |
| `--all` | | Shorthand for `--skill '*' --agent '*' -y` |

**Examples:**

```bash
# Interactive removal
npx skills remove

# Remove specific skill
npx skills remove web-design-guidelines

# Remove from global scope
npx skills remove --global web-design-guidelines

# Remove from specific agents
npx skills remove --agent claude-code my-skill

# Remove all skills (no confirmation)
npx skills remove --all

# Remove all skills from one agent
npx skills rm --skill '*' -a cursor
```

---

### `check` -- Check for Updates

Check whether installed skills have newer versions available.

```bash
npx skills check
```

---

### `update` -- Update Installed Skills

Update all installed skills to their latest versions.

```bash
npx skills update
```

---

### `init` -- Create a New Skill

Generate a new skill template with proper SKILL.md structure.

```bash
npx skills init              # Create SKILL.md in current directory
npx skills init my-skill     # Create in a named subdirectory
```

---

## Installation Paths (Claude Code)

| Scope | Path |
|-------|------|
| Project | `.claude/skills/<skill-name>/SKILL.md` |
| Global | `~/.claude/skills/<skill-name>/SKILL.md` |

The CLI also supports Cursor, Codex, Gemini CLI, GitHub Copilot, and other agents -- it auto-detects installed agents and prompts for target selection. Run `npx skills add <source> --help` or check `npx skills --help` for the full, current agent list rather than relying on a list here, which will drift out of sync with the CLI.

---

## Troubleshooting

### Skills not found in a repository

Verify the repository contains `SKILL.md` files in expected locations:
```bash
# List skills before installing
npx skills add owner/repo --list
```

If no skills appear, the repository may not follow the Agent Skills directory convention. Check for `SKILL.md` files in the repo root or `skills/` directory.

### Permission errors on global install

Ensure write access to the home directory agent paths:
```bash
ls -la ~/.claude/skills/
```

### Symlink vs copy issues

On Windows or restricted filesystems, symlinks may fail. Use copy mode when prompted, or reinstall with the copy method.

### Stale skills after update

If `npx skills update` does not reflect changes, remove and reinstall:
```bash
npx skills remove my-skill
npx skills add owner/repo --skill my-skill -a claude-code
```
