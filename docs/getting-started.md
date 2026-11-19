# Getting started with Claude Code Arsenal

A comprehensive guide to setting up and using the Claude Code Arsenal for automated development workflows.

## Overview

Claude Code Arsenal is a professional collection of 56 skills designed to enhance your Claude Code development experience, covering development, documentation, git/GitHub, Jira, and specialty capabilities. See [Features](features.md) for the full skill list.

## Prerequisites

Before you begin, ensure you have:

- Claude Code (Anthropic's official Claude CLI)
- Git (for version control)

Everything below only applies if you plan to contribute to ai-arsenal itself:

- Python 3.12+
- UV (fast Python package management): `curl -LsSf https://astral.sh/uv/install.sh | sh`

## Installation

### Plugin marketplace (recommended)

This is the primary installation method for all users. Register the repository as a Claude Code plugin marketplace, then install the variant you want:

```bash
/plugin marketplace add mgiovani/ai-arsenal
/plugin install ai-arsenal@ai-arsenal-marketplace
```

Or pick a focused variant instead of the full toolkit, see [Features](features.md) for what each plugin includes:

```bash
/plugin install ai-arsenal-dev@ai-arsenal-marketplace     # Development skills only
/plugin install ai-arsenal-product@ai-arsenal-marketplace # Product and design skills only
/plugin install ai-arsenal-docs@ai-arsenal-marketplace    # Documentation skills only
/plugin install ai-arsenal-git@ai-arsenal-marketplace     # Git/GitHub workflow skills only
/plugin install ai-arsenal-jira@ai-arsenal-marketplace    # Jira CLI only
/plugin install ai-arsenal-skills@ai-arsenal-marketplace  # Specialty skills only
/plugin install ai-arsenal-review@ai-arsenal-marketplace  # Code review and quality skills
```

Team configuration: add to `.claude/settings.json` so every team member auto-installs the marketplace on trust:

```json
{
  "extraKnownMarketplaces": {
    "ai-arsenal": {
      "source": { "source": "github", "repo": "mgiovani/ai-arsenal" }
    }
  },
  "enabledPlugins": ["ai-arsenal"]
}
```

### Symlink install (Contributors only)

Only use this if you're developing ai-arsenal itself: it creates symlinks into `~/.claude/` so file edits are reflected immediately, without a plugin reinstall:

```bash
git clone https://github.com/mgiovani/ai-arsenal.git
cd ai-arsenal

uv sync --extra dev
make dry-run       # preview what will be installed
make install       # symlink everything to ~/.claude
make configure     # optional: interactively choose which skills to symlink
```

### Optional feature: enhanced statusline

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

## Core components

### Skills

Claude Code Arsenal ships 56 skills, split between:

- User-invoked skills: explicit slash commands (e.g. `/docs-adr`, `/git-commit`)
- Model-invoked skills: Claude loads them automatically when the request matches (e.g. `agent-browser`, `create-skill`, `test-suite`)

Skills use progressive disclosure: Claude reads only the frontmatter until a skill is relevant, then loads its full body and bundled resources (`scripts/`, `references/`, `assets/`, `evals/`) as needed. See [Features](features.md) for the complete, categorized list.

## Advanced setup

### Enhanced statusline

```bash
make install-statusline
```

Shows session costs, token usage, time remaining in the current 5-hour window, and usage patterns.

## Configuration

Configuration for a symlink install is managed through the interactive `make configure` wizard, which lets you select specific skills to symlink to `~/.claude/`. It never modifies `~/.claude/settings.json`. Plugin installs are managed entirely through `/plugin`.

## Development workflow integration

### Daily development

Your enhanced workflow includes:

1. Documentation automation: `/docs-adr`, `/docs-rfc`, `/docs-diagram`, `/docs-update`, `/docs-check`, `/docs-init`
2. Git automation: `/git-commit`, `/git-create-pr`, `/git-release`, `/ship`
3. Specialized skills: Claude automatically invokes relevant model-invoked skills when needed

### Code review process (Contributors)

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

## Next steps

1. Create custom skills: use the `create-skill` skill to build specialized capabilities
2. Set up team workflows: share the plugin marketplace config across your team
3. Enhanced statusline: track token usage and session costs with `make install-statusline`

### Community and support

- Documentation: browse `docs/` for detailed guides
- Issues: report bugs at https://github.com/mgiovani/ai-arsenal/issues
- Discussions: ask questions at https://github.com/mgiovani/ai-arsenal/discussions

### Stay updated

Plugin installs update via `/plugin` → Update now. For a symlink (contributor) install:

```bash
cd ai-arsenal
git pull origin main
make install
```

---

For detailed guides, see:
- [Features](features.md)
- [Troubleshooting](troubleshooting.md)
- [Contributing](../CONTRIBUTING.md)
