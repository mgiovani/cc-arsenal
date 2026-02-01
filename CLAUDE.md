# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Architecture

This is the **Claude Code Arsenal** - a professional collection of skills for development workflow automation. All components are now **skills** (migrated from the legacy commands format in v2.0.0).

### Core Components

- **Skills** (`skills/`): 20 skills covering development, documentation, git, jira, claude utilities, browser automation, and skill discovery
- **Scripts** (`scripts/`): Professional Python utilities for installation, configuration, and code generation
- **Commands** (`commands/`): Legacy commands kept for backward compatibility (skills take precedence)

## Installation

### Plugin System (Recommended)

This is the primary installation method for all users. Register this repository as a Claude Code Plugin marketplace:
```bash
/plugin marketplace add mgiovani/cc-arsenal
```

Then, to install a specific plugin set:
1. Select **Browse and install plugins**
2. Select **cc-arsenal-marketplace**
3. Select one of:
   - **cc-arsenal** - Complete toolkit (all 20 skills)
   - **cc-arsenal-dev** - Development skills only (implement-feature, fix-bug, review-security, inject-nextjs-docs)
   - **cc-arsenal-docs** - Documentation skills only (ADR, RFC, diagrams, init, check, update)
   - **cc-arsenal-git** - Git workflow skills only (commit, create-pr)
   - **cc-arsenal-skills** - Specialty skills only (agent-browser, jira-cli, skill-creator, find-skills)
4. Select **Install now**

Alternatively, directly install via:
```bash
/plugin install cc-arsenal@cc-arsenal-marketplace
```

For local development, add a local marketplace instead:
```bash
/plugin marketplace add /path/to/cc-arsenal
```

**Benefits:**
- Clean, managed installation
- Automatic updates
- Easy to enable/disable
- No system-wide symlinks

**Plugin Variants Pattern:**

This repository uses a "plugin variants" architecture where multiple installation options are provided from a single source repository. All variants point to the same codebase (`"source": "./"`) but expose different subsets of skills:

| Plugin | Skills Loaded | Use Case |
|--------|--------------|----------|
| `cc-arsenal` | All 20 skills | Full toolkit for complete workflow automation |
| `cc-arsenal-dev` | implement-feature, fix-bug, review-security, inject-nextjs-docs | Development workflows with subagents |
| `cc-arsenal-docs` | docs-adr, docs-check, docs-diagram, docs-init, docs-rfc, docs-update | Documentation generation only |
| `cc-arsenal-git` | git-commit, git-create-pr | Git workflow automation |
| `cc-arsenal-skills` | agent-browser, jira-cli, skill-creator, find-skills | Specialty model-invoked capabilities |

**How It Works:**
- Single repository with all skills in `skills/` directory
- Marketplace manifest (`.claude-plugin/marketplace.json`) defines multiple "plugins"
- Each plugin entry specifies which skills to load via the `skills` field
- Users install only what they need without duplicating code

**When to Use Each Variant:**
- **Full installation** (`cc-arsenal`): Development teams wanting complete automation
- **Selective installation** (variant plugins): Minimalist setups, focused workflows, or avoiding namespace pollution
- **Custom combinations**: Install multiple variants (e.g., `cc-arsenal-git` + `cc-arsenal-docs`)

**Troubleshooting Plugin Updates:**

If plugin updates from a local marketplace don't show new components:
```bash
# Clear the plugin cache to force reload
rm -rf ~/.claude/plugins/cache/cc-arsenal-marketplace/

# Then update the plugin in Claude Code
/plugin → Update now
```

This happens when the cache contains an older version and doesn't detect local changes.

### Development Installation (Symlink Method)

**Only use this if you're developing cc-arsenal itself.** Regular users should use the plugin system above.

This method creates symlinks to `~/.claude/` for immediate file updates during development:

```bash
# Install Python dependencies
uv sync --extra dev

# Install to ~/.claude directory (creates symlinks)
uv run python -m scripts.setup.install

# Configure components (optional)
uv run python -m scripts.setup.configure

# Quick start with preview
make dry-run
make install
make configure
```

**Benefits:**
- Immediate file updates (no reinstall needed)
- Better for development and testing
- Direct access to source code

### Team Configuration

For automatic installation across team members, add to `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "cc-arsenal": {
      "source": {
        "source": "github",
        "repo": "mgiovani/cc-arsenal"
      }
    }
  },
  "enabledPlugins": ["cc-arsenal"]
}
```

When team members trust the repository folder, Claude Code automatically installs the marketplace and plugin.

### Selective Installation (Advanced)

By default, `make install` installs **all components** by symlinking everything to `~/.claude/`. If you want to selectively install only specific components, use the interactive configuration wizard:

```bash
# Interactive configuration - choose specific components to symlink
make configure
```

**What it does:**
- Discovers all available skills from the repository
- Shows skills organized by category
- Lets you interactively select which items to symlink
- **Never modifies** your `~/.claude/settings.json` file
- Creates symlinks only for selected components

**When to use:**
- You only want specific skills (e.g., just git skills, not docs)
- Testing individual components without installing everything
- Creating a lightweight installation with minimal disk usage
- For full installation, use `make install` instead

**Note:** This is separate from the plugin system. Plugin installation uses the variant definitions from marketplace.json. Use `make configure` when you want granular control over which files are symlinked.

## Development Commands

The repository uses a **modular Makefile architecture** with focused command sets:

- **Core Makefile** (19 commands): Essential development, testing, and installation
- **Feature Makefiles**: Optional tools with their own command sets
  - `scripts/claude/statusline/Makefile` (9 commands): Statusline management
  - `scripts/claude-hi/Makefile` (12 commands): Session scheduler and automation

### Core Development Workflow

```bash
# Development Environment
make dev                  # Set up development with all dependencies
make pre-commit-install   # Install pre-commit hooks
make pre-commit-run       # Run pre-commit on all files

# Code Quality
make check                # Run all checks (lint + type-check)
make lint                 # Run ruff linting
make format               # Format code with ruff
make type-check           # Run pyright type checking

# Testing
make test                 # Run unit tests
make coverage             # Tests with coverage report

# Installation
make install              # Install all components to ~/.claude
make dry-run              # Preview installation
make configure            # Interactive: choose specific skills to enable

# Utilities
make clean                # Clean caches and build artifacts
make info                 # Show repository statistics
make validate-structure   # Validate repository structure
make validate-plugins     # Validate plugin manifests
```

### Optional Features

```bash
# Statusline Management
make install-statusline           # Install statusline (delegates to feature Makefile)
make uninstall-statusline         # Uninstall statusline (delegates to feature Makefile)
make -C scripts/claude/statusline help           # Show all statusline commands
make -C scripts/claude/statusline status         # Show statusline configuration
make -C scripts/claude/statusline test           # Test statusline
make -C scripts/claude/statusline list-backups   # List backups

# Session Scheduler (Claude Hi)
make -C scripts/claude-hi help      # Show all scheduler commands
make -C scripts/claude-hi standard  # Set up 9am/2pm/7pm schedule
make -C scripts/claude-hi status    # Check current schedule
make -C scripts/claude-hi remove    # Remove schedule
make -C scripts/claude-hi now       # Send 'hi' immediately
```

## Available Skills (20 total)

All components are skills with progressive disclosure (SKILL.md + optional references/scripts/assets directories).

### Development (4 skills)
- **implement-feature**: Feature implementation with senior staff engineer best practices and parallel subagent orchestration
- **fix-bug**: Test-driven debugging and verification workflow
- **review-security**: OWASP Top 10 2025 security analysis with parallel scanning agents
- **inject-nextjs-docs**: Run Next.js agents-md codemod to inject framework docs

### Documentation (6 skills)
- **docs-adr**: Architecture Decision Records creation and management
- **docs-check**: Documentation validation and health scoring
- **docs-diagram**: Architecture diagrams generation (Mermaid)
- **docs-init**: Documentation structure initialization
- **docs-rfc**: Request for Comments documentation
- **docs-update**: Documentation sync with codebase state

### Git Operations (2 skills)
- **git-commit**: Conventional commit message generation
- **git-create-pr**: Pull request creation with standardized formats

### Jira Integration (2 skills)
- **jira-daily**: Smart standup report generator with activity analysis
- **jira-todo**: Smart daily work planner with intelligent prioritization

### Claude Utilities (2 skills)
- **create-command**: Create new skills (slash commands) from templates
- **create-rule**: Create CLAUDE.md rules and memory guidelines

### Specialty Skills (4 skills)
- **agent-browser**: AI-optimized browser automation with 93% less context overhead than Playwright MCP
- **find-skills**: Discover and install third-party agent skills from skills.sh
- **skill-creator**: Comprehensive guide for creating effective skills
- **jira-cli**: Interactive command-line tool for Atlassian Jira

## Development Patterns

### Understanding Skills

All components in cc-arsenal are **skills**. Skills come in two flavors:

- **User-invoked skills** (`disable-model-invocation: true`): Explicit slash commands that users run directly
  - Examples: `/git-commit`, `/docs-adr`, `/implement-feature`
  - Best for: Git operations, documentation generation, feature implementation
  - 16 user-invoked skills available

- **Model-invoked skills** (`disable-model-invocation: false` or unset): Capabilities Claude automatically loads when relevant
  - Examples: agent-browser, jira-cli, skill-creator, find-skills
  - Claude decides when to activate based on context
  - Best for: Domain expertise, tool integrations, specialized workflows
  - 4 model-invoked skills available

### Skills Architecture

Skills are modular capabilities organized with this structure:

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (name, description, allowed-tools, etc.)
│   └── Markdown instructions
└── Bundled Resources (optional)
    ├── scripts/      - Executable code (Python/Bash/etc.)
    ├── references/   - Documentation loaded as needed
    └── assets/       - Files used in output (templates, etc.)
```

### Progressive Disclosure

Skills use a three-level loading system:
1. **Metadata** (name + description) - Always in context (~100 words)
2. **SKILL.md body** - Loaded when skill activates (<5k words)
3. **Bundled resources** - Loaded only when Claude needs them

### Local Development Cache Management

**CRITICAL: When developing with a local directory marketplace, you must manually clear the cache after any changes.**

Local directory marketplaces (`"source": "directory"`) do NOT support auto-update or version detection. After creating new skills or bumping versions:

```bash
# Clear the plugin cache to force reload
rm -rf ~/.claude/plugins/cache/cc-arsenal-marketplace/

# Then update the plugin in Claude Code
/plugin → Update now
```

**Why this is needed:**
- Claude Code caches the marketplace.json metadata on first install
- Changes to local files don't trigger cache invalidation
- Auto-update and manual "Update now" only work for remote GitHub sources
- Without clearing cache, new components won't appear

**Alternative:** Use GitHub remote marketplace for automatic updates (recommended for production use).

### Documentation Guidelines

**IMPORTANT: No README files in component directories**

Do not add README.md files inside the `skills/` directory. Claude Code will incorrectly detect them as actual components.

Instead:
- All documentation goes in the `docs/` folder
- Reference documentation in the main project README.md if needed
- Use CLAUDE.md for development guidance
- Individual skills use SKILL.md as their native format

### Quality Assurance
All code changes should go through integrated quality gates:
- Code quality enforcement via pre-commit hooks
- Comprehensive testing and validation
- Documentation requirements
- **CHANGELOG updates**: Update CHANGELOG.md after big changes or when opening PRs

### Technology Stack
- **Python 3.12+** with UV package management
- **Rich CLI interfaces** with progress indicators
- **Pydantic** for data validation and settings
- **Type hints** required for all functions
- **Comprehensive testing** with pytest and >90% coverage

## File Organization
```
cc-arsenal/
├── skills/          # All 20 skills (primary component type)
│   ├── implement-feature/   # Feature implementation with subagents
│   ├── fix-bug/             # Test-driven debugging
│   ├── review-security/     # OWASP security analysis
│   ├── inject-nextjs-docs/  # Next.js docs injection
│   ├── docs-adr/            # Architecture Decision Records
│   ├── docs-check/          # Documentation validation
│   ├── docs-diagram/        # Architecture diagrams
│   ├── docs-init/           # Documentation initialization
│   ├── docs-rfc/            # Request for Comments
│   ├── docs-update/         # Documentation updates
│   ├── git-commit/          # Conventional commits
│   ├── git-create-pr/       # Pull request creation
│   ├── jira-daily/          # Daily standup reports
│   ├── jira-todo/           # Work prioritization
│   ├── create-command/      # Create new skills
│   ├── create-rule/         # Create memory rules
│   ├── agent-browser/       # Browser automation
│   ├── find-skills/         # Third-party skill discovery
│   ├── skill-creator/       # Skill creation guide
│   └── jira-cli/            # Jira CLI integration
├── commands/        # Legacy commands (backward compatibility)
│   ├── dev/            # Development commands
│   ├── docs/           # Documentation commands
│   ├── git/            # Git commands
│   ├── claude/         # Claude utility commands
│   └── jira/           # Jira commands
├── resources/      # Templates and assets
│   └── templates/      # ADR, RFC, and doc templates
├── scripts/        # Installation and utilities
│   ├── setup/          # install.py, configure.py
│   ├── generators/     # Code generation utilities
│   ├── claude/         # Claude Code utilities (statusline)
│   └── claude-hi/      # Session management and scheduling
```
