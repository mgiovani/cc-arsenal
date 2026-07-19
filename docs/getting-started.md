# Getting Started with Claude Code Arsenal

A comprehensive guide to setting up and using the Claude Code Arsenal for automated development workflows.

## Overview

Claude Code Arsenal is a professional collection of 45 skills designed to enhance your Claude Code development experience — covering development, documentation, git/GitHub, Jira, teams, and specialty capabilities. See [Features](features.md) for the full skill list.

## Prerequisites

Before you begin, ensure you have:

- **Claude Code** (Anthropic's official Claude CLI)
- **Git** (for version control)

Everything below only applies if you plan to contribute to cc-arsenal itself:

- **Python 3.12+**
- **UV** (fast Python package management) — `curl -LsSf https://astral.sh/uv/install.sh | sh`

## Installation

### Plugin Marketplace (Recommended)

This is the primary installation method for all users. Register the repository as a Claude Code plugin marketplace, then install the variant you want:

```bash
/plugin marketplace add mgiovani/cc-arsenal
/plugin install cc-arsenal@cc-arsenal-marketplace
```

Or pick a focused variant instead of the full toolkit — see [Features](features.md) for what each plugin includes:

```bash
/plugin install cc-arsenal-dev@cc-arsenal-marketplace     # Development skills only
/plugin install cc-arsenal-docs@cc-arsenal-marketplace    # Documentation skills only
/plugin install cc-arsenal-git@cc-arsenal-marketplace     # Git/GitHub workflow skills only
/plugin install cc-arsenal-skills@cc-arsenal-marketplace  # Specialty skills only
/plugin install cc-arsenal-teams@cc-arsenal-marketplace   # Team orchestration skills
/plugin install cc-arsenal-review@cc-arsenal-marketplace  # Code review and quality skills
```

**Team configuration:** add to `.claude/settings.json` so every team member auto-installs the marketplace on trust:

```json
{
  "extraKnownMarketplaces": {
    "cc-arsenal": {
      "source": { "source": "github", "repo": "mgiovani/cc-arsenal" }
    }
  },
  "enabledPlugins": ["cc-arsenal"]
}
```

### Symlink Install (Contributors Only)

Only use this if you're developing cc-arsenal itself — it creates symlinks into `~/.claude/` so file edits are reflected immediately, without a plugin reinstall:

```bash
git clone https://github.com/mgiovani/cc-arsenal.git
cd cc-arsenal

uv sync --extra dev
make dry-run       # preview what will be installed
make install       # symlink everything to ~/.claude
make configure     # optional: interactively choose which skills to symlink
```

### Optional Feature: Enhanced Statusline

```bash
make install-statusline
```

## Verification

After installation, verify everything is working:

```bash
# Plugin install: check via Claude Code's /plugin command
# Symlink install: check the symlinked skills
ls ~/.claude/skills/

# Validate the repo structure (contributors)
make info
make validate-structure
```

## Core Components

### Skills

Claude Code Arsenal ships 45 skills, split between:

- **User-invoked** skills — explicit slash commands (e.g. `/docs-adr`, `/git-commit`)
- **Model-invoked** skills — Claude loads them automatically when the request matches (e.g. `agent-browser`, `create-skill`, `test-suite`)

Skills use progressive disclosure: Claude reads only the frontmatter until a skill is relevant, then loads its full body and bundled resources (`scripts/`, `references/`, `assets/`, `evals/`) as needed. See [Features](features.md) for the complete, categorized list.

## Advanced Setup

### Smart Session Scheduling

Replace manual cron workarounds with intelligent scheduling:

```bash
make -C scripts/claude-hi setup     # Interactive setup
make -C scripts/claude-hi standard  # Quick 9am/2pm/7pm schedule
make -C scripts/claude-hi status    # Check current schedule
```

### Enhanced Statusline

```bash
make install-statusline
```

Shows session costs, token usage, time remaining in the current 5-hour window, and usage patterns.

## Configuration

Configuration for a symlink install is managed through the interactive `make configure` wizard, which lets you select specific skills to symlink to `~/.claude/`. It never modifies `~/.claude/settings.json`. Plugin installs are managed entirely through `/plugin`.

## Development Workflow Integration

### Daily Development

Your enhanced workflow includes:

1. **Documentation automation**: `/docs-adr`, `/docs-rfc`, `/docs-diagram`, `/docs-update`, `/docs-check`, `/docs-init`
2. **Git automation**: `/git-commit`, `/git-create-pr`, `/git-release`, `/ship`
3. **Specialized skills**: Claude automatically invokes relevant model-invoked skills when needed

### Code Review Process (Contributors)

```bash
make check                 # All quality checks (lint + type-check)
make test                  # Full test suite
make pre-commit-run        # Run pre-commit checks manually
```

## Troubleshooting

See [Troubleshooting](troubleshooting.md) for the full guide. Quick checks:

```bash
# UV not found (contributors)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify skills are installed (symlink method)
ls ~/.claude/skills/

# Check repo structure (contributors)
make info
make validate-structure
```

## Next Steps

1. **Create Custom Skills**: Use the `create-skill` skill to build specialized capabilities
2. **Set Up Team Workflows**: Share the plugin marketplace config across your team
3. **Enhanced Statusline**: Track token usage and session costs with `make install-statusline`

### Community and Support

- **Documentation**: Browse `docs/` for detailed guides
- **Issues**: Report bugs at https://github.com/mgiovani/cc-arsenal/issues
- **Discussions**: Ask questions at https://github.com/mgiovani/cc-arsenal/discussions

### Stay Updated

Plugin installs update via `/plugin` → Update now. For a symlink (contributor) install:

```bash
cd cc-arsenal
git pull origin main
make install
```

---

For detailed guides, see:
- [Features](features.md)
- [Troubleshooting](troubleshooting.md)
- [Contributing](../CONTRIBUTING.md)
