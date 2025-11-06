# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Architecture

This is the **Claude Code Arsenal** - a professional collection of security-focused AI agents, quality automation commands, and safety hooks. The codebase is organized using a **symlink architecture** for clean installation and modular configuration.

### Core Components

- **Agents** (`agents/`): AI assistants for specialized development tasks
- **Commands** (`commands/`): Quality automation and workflow commands
- **Hooks** (`hooks/`): Safety and validation scripts that run automatically on Claude Code events
- **Skills** (`skills/`): Model-invoked capabilities that Claude automatically loads when relevant
- **Scripts** (`scripts/`): Professional Python utilities for installation, configuration, and code generation

## Installation

### Method 1: Plugin System (Recommended for Users)

Install cc-arsenal as a Claude Code plugin using the marketplace system:

```bash
# Add the cc-arsenal marketplace
/plugin marketplace add mgiovani/cc-arsenal

# Install the plugin
/plugin install cc-arsenal@cc-arsenal-marketplace

# Or install from local directory
/plugin marketplace add /path/to/cc-arsenal
/plugin install cc-arsenal@cc-arsenal-marketplace
```

**Benefits:**
- Clean, managed installation
- Automatic updates
- Easy to enable/disable
- No system-wide symlinks

### Method 2: Direct Installation (For Development)

For local development with immediate file updates:

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
- Discovers all available components from the repository
- Shows components organized by category (commands, hooks, skills)
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
│ commands │                                          │    20 │
│          │   docs: adr, check, diagram, ...         │    18 │
│          │   git: commit, create-pr                 │     2 │
│ hooks    │                                          │     2 │
│          │   quality: pre_commit_validate           │     1 │
│          │   security: file_protection              │     1 │
└──────────┴──────────────────────────────────────────┴───────┘

🔧 Select Components to Install
Choose which components to symlink to ~/.claude/

📁 Commands
  Install all 18 items from docs? [y/n] (y): n
    Install adr? [y/n] (n): y
    Install rfc? [y/n] (n): y
    Install diagram? [y/n] (n): n
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

### Agents
AI-powered development assistants organized by specialty:
- **Architecture**: System design and technical architecture
- **Development**: Code implementation and debugging
- **Orchestration**: Workflow coordination and automation
- **Product**: Product management and requirements
- **Productivity**: Development efficiency and optimization
- **UX**: User experience and design

### Commands
Workflow automation commands:
- **Documentation**: ADR, RFC, architecture diagrams, and onboarding guides
- **Git operations**: Repository management and conventional commits
- **Testing**: Test automation and quality assurance
- **Utility**: General-purpose development helpers

### Hooks
Safety and validation automation:
- **Security hooks**: Authentication and data protection
- **Quality hooks**: Code standards and pre-commit validation
- **Compliance hooks**: Audit trails and regulatory compliance

### Skills
Modular, self-contained capabilities that Claude automatically invokes when relevant:
- **skill-creator**: Guide for creating effective skills with specialized knowledge, workflows, or tool integrations
- **jira-cli**: Interactive command-line tool for Atlassian Jira with comprehensive issue, epic, and sprint management
- Progressive disclosure design: loads only what's needed to save context
- Can bundle scripts, references, and assets for complex tasks

## Development Patterns

### Understanding Component Types

**When to use each component:**

- **Skills** - Use for model-invoked capabilities that Claude automatically loads when relevant
  - Claude decides when to activate based on context
  - Best for: Domain expertise, tool integrations, specialized workflows
  - Example: skill-creator activates when you want to create a new skill

- **Agents** - Use for complex, multi-step tasks requiring autonomous execution
  - Explicitly invoked via Task tool
  - Stateless, single-shot assistants
  - Best for: Architecture design, code implementation, workflow orchestration

- **Commands** - Use for explicit user-invoked operations
  - Slash commands (e.g., `/commit`, `/test`)
  - Direct user control
  - Best for: Git operations, testing, utilities

- **Hooks** - Use for automatic event-driven validation
  - Triggered by Claude Code events
  - Background safety and quality gates
  - Best for: Security validation, pre-commit checks, compliance audits

### Agent Usage
```bash
# Use specialized agents via Task tool
claude task "Use the development agent to implement user authentication"
```

### Skills Usage

Skills are **automatically invoked** by Claude when relevant to the task - you don't need to explicitly call them. Claude discovers skills through their `name` and `description` in the SKILL.md frontmatter.

### Documentation Guidelines

**IMPORTANT: No README files in component directories**

Do not add README.md files inside key component folders (`agents/`, `commands/`, `hooks/`, `skills/`). Claude Code will incorrectly detect them as actual components.

Instead:
- All documentation goes in the `docs/` folder
- Reference documentation in the main project README.md if needed
- Use CLAUDE.md for development guidance
- Individual components use their native format (AGENT.md, COMMAND.md, HOOK.md, SKILL.md)

### Quality Assurance
All code changes should go through integrated quality gates:
- Security validation via hooks
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
├── agents/           # AI development assistants
│   ├── architecture/    # System design specialists
│   ├── development/     # Code implementation experts
│   ├── orchestration/   # Workflow coordinators
│   ├── product/         # Product management
│   ├── productivity/    # Efficiency optimization
│   └── ux/             # User experience design
├── commands/        # Workflow automation
│   ├── docs/           # Documentation generation (ADR, RFC, diagrams)
│   ├── git/            # Git operations
│   ├── testing/        # Test automation
│   └── utility/        # Development utilities
├── hooks/          # Safety and validation
│   ├── security/       # Authentication and protection
│   ├── quality/        # Code standards and validation
│   └── compliance/     # Audit and regulatory
├── skills/         # Model-invoked capabilities
│   ├── skill-creator/  # Guide and tools for creating skills
│   │   ├── SKILL.md       # Comprehensive skill creation guide
│   │   ├── LICENSE.txt    # Apache 2.0 license
│   │   └── scripts/       # Skill management utilities
│   │       ├── init_skill.py      # Generate new skill templates
│   │       ├── quick_validate.py  # Validate skill structure
│   │       └── package_skill.py   # Package skills for distribution
│   └── jira-cli/       # Jira CLI tool integration
│       └── SKILL.md       # Interactive Jira command-line guide
├── scripts/        # Installation and utilities
│   ├── setup/          # install.py, configure.py
│   ├── generators/     # agent_generator.py
│   ├── claude/         # Claude Code utilities
│   └── claude-hi/      # Session management
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
