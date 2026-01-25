# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Architecture

This is the **Claude Code Arsenal** - a professional collection of quality automation commands and specialized skills. The codebase is organized using a **symlink architecture** for clean installation and modular configuration.

### Core Components

- **Commands** (`commands/`): Quality automation and workflow commands (13 commands total)
- **Skills** (`skills/`): Model-invoked capabilities that Claude automatically loads when relevant (2 skills)
- **Scripts** (`scripts/`): Professional Python utilities for installation, configuration, and code generation

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
   - **cc-arsenal** - Complete toolkit (all commands and skills)
   - **cc-arsenal-dev** - Development commands only (feature implementation)
   - **cc-arsenal-docs** - Documentation commands only
   - **cc-arsenal-git** - Git workflow commands only
   - **cc-arsenal-skills** - Skills only (Jira CLI, skill creator)
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

This repository uses a "plugin variants" architecture where multiple installation options are provided from a single source repository. All variants point to the same codebase (`"source": "./"`) but expose different subsets of components:

| Plugin | Components Loaded | Use Case |
|--------|------------------|----------|
| `cc-arsenal` | All commands, skills, hooks | Full toolkit for complete workflow automation |
| `cc-arsenal-dev` | `/dev:implement-feature` command | Feature implementation with subagents |
| `cc-arsenal-docs` | `/docs:*` commands (ADR, RFC, diagram, etc.) | Documentation generation only |
| `cc-arsenal-git` | `/git:*` commands (commit, create-pr) | Git workflow automation |
| `cc-arsenal-skills` | Skills only (agent-browser, jira-cli, skill-creator) | Skill-based capabilities without commands |

**How It Works:**
- Single repository with all components in standard locations (`commands/`, `skills/`, `hooks/`)
- Marketplace manifest (`.claude-plugin/marketplace.json`) defines multiple "plugins"
- Each plugin entry specifies which components to load via `commands`, `skills`, `hooks` fields
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
- Discovers all available components from the repository (commands, skills)
- Shows components organized by category
- Lets you interactively select which items to symlink
- **Never modifies** your `~/.claude/settings.json` file
- Creates symlinks only for selected components

**When to use:**
- You only want specific commands (e.g., just git commands, not docs)
- Testing individual components without installing everything
- Creating a lightweight installation with minimal disk usage
- For full installation, use `make install` instead

**Example session:**
```
⚙️  Claude Code Arsenal - Selective Installation
This wizard lets you choose which components to symlink to ~/.claude/

🔍 Discovering available components...
                     CC-Arsenal Components
┌──────────┬──────────────────────────────────────────┬───────┐
│ Category │ Component                                │ Count │
├──────────┼──────────────────────────────────────────┼───────┤
│ commands │                                          │     8 │
│          │   docs: adr, check, diagram, init, ...   │     6 │
│          │   git: commit, create-pr                 │     2 │
│ skills   │                                          │     2 │
│          │   jira-cli, skill-creator                │     2 │
└──────────┴──────────────────────────────────────────┴───────┘

🔧 Select Components to Install
Choose which components to symlink to ~/.claude/

📁 Commands
  Install all 6 items from docs? [y/n] (y): n
    Install adr? [y/n] (n): y
    Install rfc? [y/n] (n): y
    Install diagram? [y/n] (n): n
  Install all 2 items from git? [y/n] (y): y
  ...

📋 Installation Preview
commands (2 items)
  ✨ docs/adr.md
  ✨ docs/rfc.md

📊 Summary: 2 components selected
Proceed with installation? [y/n] (y): y

✅ Installation complete!
🔗 2 components symlinked to ~/.claude
💡 Note: Your settings.json was not modified
```

**How it works:**
- `make install` creates symlinks for **all** components
- `make configure` lets you choose **which** components to symlink
- Both methods create symlinks; the difference is selectivity
- Your `settings.json` controls which symlinked components are *enabled*
- **Never** overwrites or modifies your personal `settings.json`

**Note:** This is separate from the plugin system. Plugin installation always includes everything. Use `make configure` when you want granular control over which files are symlinked.

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
make configure            # Interactive: choose specific commands/skills to enable

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

## Available Components

### Commands (13 total)
Workflow automation commands organized by category:
- **Development** (1 command): `implement-feature`
  - Feature implementation with senior staff engineer best practices
  - Parallel subagent orchestration for complex features
  - Automatic project discovery (Makefile, package.json, pyproject.toml, etc.)
- **Documentation** (6 commands): `adr`, `check`, `diagram`, `init`, `rfc`, `update`
  - ADR (Architecture Decision Records) creation and management
  - RFC (Request for Comments) documentation
  - Architecture diagrams generation
  - Documentation initialization and validation
- **Git operations** (2 commands): `commit`, `create-pr`
  - Conventional commit message generation
  - Pull request creation with standardized formats
- **Claude utilities** (2 commands): `create-command`, `create-rule`
  - Create new slash commands from templates
  - Create CLAUDE.md rules and guidelines
- **Jira integration** (2 commands): `todo`, `daily`
  - Todo management synced with Jira issues
  - Daily standup report generation

### Skills (3 total)
Modular, self-contained capabilities that Claude automatically invokes when relevant:
- **agent-browser**: AI-optimized browser automation with 93% less context overhead than Playwright MCP. Uses snapshot + refs system for web testing, form automation, screenshots, and data extraction.
- **skill-creator**: Comprehensive guide for creating effective skills with specialized knowledge, workflows, or tool integrations. Includes scripts for initialization, validation, and packaging.
- **jira-cli**: Interactive command-line tool for Atlassian Jira with comprehensive issue, epic, and sprint management
- Progressive disclosure design: loads only what's needed to save context
- Can bundle scripts, references, and assets for complex tasks

## Development Patterns

### Understanding Component Types

**When to use each component:**

- **Skills** - Model-invoked capabilities that Claude automatically loads when relevant
  - Claude decides when to activate based on context
  - Best for: Domain expertise, tool integrations, specialized workflows
  - Example: skill-creator activates when you want to create a new skill
  - Available skills: `skill-creator`, `jira-cli`

- **Commands** - Explicit user-invoked operations
  - Slash commands (e.g., `/git:commit`, `/docs:adr`)
  - Direct user control
  - Best for: Git operations, documentation generation, testing, utilities
  - 8 commands available across docs and git categories

### Skills Usage

Skills are **automatically invoked** by Claude when relevant to the task - you don't need to explicitly call them. Claude discovers skills through their `name` and `description` in the SKILL.md frontmatter.

### Documentation Guidelines

**IMPORTANT: No README files in component directories**

Do not add README.md files inside key component folders (`commands/`, `skills/`). Claude Code will incorrectly detect them as actual components.

Instead:
- All documentation goes in the `docs/` folder
- Reference documentation in the main project README.md if needed
- Use CLAUDE.md for development guidance
- Individual components use their native format (COMMAND.md, HOOK.md, SKILL.md)

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
├── commands/        # Workflow automation (13 commands)
│   ├── dev/            # Development workflow (1 command)
│   │   └── implement-feature.md  # Feature implementation with subagents
│   ├── docs/           # Documentation generation (6 commands)
│   │   ├── adr.md         # Architecture Decision Records
│   │   ├── check.md       # Documentation validation
│   │   ├── diagram.md     # Architecture diagrams
│   │   ├── init.md        # Documentation initialization
│   │   ├── rfc.md         # Request for Comments
│   │   └── update.md      # Documentation updates
│   ├── git/            # Git operations (2 commands)
│   │   ├── commit.md      # Conventional commits
│   │   └── create-pr.md   # Pull request creation
│   ├── claude/         # Claude utilities (2 commands)
│   │   ├── create-command.md  # Create slash commands
│   │   └── create-rule.md     # Create CLAUDE.md rules
│   └── jira/           # Jira integration (2 commands)
│       ├── todo.md        # Todo management
│       └── daily.md       # Daily standup reports
├── skills/         # Model-invoked capabilities (3 skills)
│   ├── agent-browser/  # Browser automation skill
│   │   ├── SKILL.md       # AI-optimized browser automation guide
│   │   └── references/    # Progressive disclosure documentation
│   │       ├── commands.md   # Complete command reference
│   │       ├── workflows.md  # Automation patterns
│   │       └── advanced.md   # Advanced topics and Playwright comparison
│   ├── skill-creator/  # Guide and tools for creating skills
│   │   ├── SKILL.md       # Comprehensive skill creation guide
│   │   ├── LICENSE.txt    # Apache 2.0 license
│   │   └── scripts/       # Skill management utilities
│   │       ├── init_skill.py      # Generate new skill templates
│   │       ├── quick_validate.py  # Validate skill structure
│   │       └── package_skill.py   # Package skills for distribution
│   └── jira-cli/       # Jira CLI tool integration
│       └── SKILL.md       # Interactive Jira command-line guide
├── resources/      # Templates and assets
│   └── templates/      # ADR, RFC, and doc templates
├── scripts/        # Installation and utilities
│   ├── setup/          # install.py, configure.py
│   ├── generators/     # Code generation utilities
│   ├── claude/         # Claude Code utilities (statusline)
│   └── claude-hi/      # Session management and scheduling
```

## Skills Architecture

Skills are modular capabilities organized with this structure:

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (name, description)
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
