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

## Development Commands

### Development Environment
```bash
# Set up development environment
make dev

# Run quality checks
make check                # Run all checks
make lint                 # Linting only
make format               # Code formatting
make type-check           # Type checking

# Run tests
make test                 # Unit tests
make coverage             # Tests with coverage report
```

### Project Management
```bash
# Generate new agent
make generate-agent NAME=my-agent CATEGORY=development
uv run python -m scripts.generators.agent_generator --name "agent-name" --category "development"

# Validate repository structure
make validate-structure

# Show repository information
make info
make show-structure
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
