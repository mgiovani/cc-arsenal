# Getting Started with Claude Code Arsenal

A comprehensive guide to setting up and using the Claude Code Arsenal for secure, automated development workflows.

## Overview

Claude Code Arsenal is a professional collection of quality automation commands and specialized skills designed to enhance your Claude Code development experience with enterprise-grade automation.

## Prerequisites

Before you begin, ensure you have:

### Required Software

- **Python 3.12+** (for modern language features and performance)
- **UV** (for fast Python package management) - **REQUIRED**
- **Claude Code** (Anthropic's official Claude CLI)
- **Git** (for version control)

### Installing UV

UV is required for Python package management:

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
```

For more details, visit: https://docs.astral.sh/uv/getting-started/installation/

### Installing Claude Code

Follow the official installation guide at: https://claude.ai/code

## Installation

### Method 1: Quick Install (Recommended)

```bash
# Clone the repository
git clone https://github.com/mgiovani/cc-arsenal.git
cd cc-arsenal

# Preview what will be installed
make dry-run

# Install all components to ~/.claude
make install

# Optional: Configure your setup interactively
make configure

# Restart Claude Code to load new configuration
```

### Method 2: Step-by-Step Installation

```bash
# 1. Clone and enter directory
git clone https://github.com/mgiovani/cc-arsenal.git
cd cc-arsenal

# 2. Install Python dependencies
uv sync --extra dev

# 3. Install to ~/.claude directory
uv run python -m scripts.setup.install

# 4. Configure components (optional)
uv run python -m scripts.setup.configure
```

### Method 3: Component-Specific Installation

```bash
# Install only specific components
make install-statusline    # Enhanced statusline only
```

## Verification

After installation, verify everything is working:

```bash
# Check if components are installed
ls ~/.claude/commands/
ls ~/.claude/skills/

# Validate installation
make info
make validate-structure
```

## Core Components

### ⚡ Commands

Workflow automation for common development tasks:

#### Available Commands

**Documentation Commands** (`/docs:*`):
- `/docs:init` - Initialize comprehensive documentation structure
- `/docs:adr` - Create numbered ADR for architectural decisions
- `/docs:rfc` - Create numbered RFC for proposing changes
- `/docs:diagram` - Generate Mermaid diagrams from codebase analysis
- `/docs:check` - Validate documentation freshness and completeness
- `/docs:update` - Update documentation by syncing with codebase

**Git Commands** (`/git:*`):
- `/git:commit` - Generate conventional commits following conventionalcommits.org
- `/git:create-pr` - Create PR with conventional commit format and pre-filled template

#### Using Commands

```bash
# Create an architectural decision record
/docs:adr "Use PostgreSQL for primary database"

# Generate architecture diagram
/docs:diagram architecture

# Create a pull request
/git:create-pr --base main
```

### 🎯 Skills

Model-invoked capabilities that Claude automatically loads when relevant:

#### Available Skills

- **skill-creator**: Comprehensive guide for creating effective skills with specialized knowledge, workflows, or tool integrations
- **jira-cli**: Interactive command-line tool for Atlassian Jira with issue, epic, and sprint management

Skills use progressive disclosure - Claude decides when to activate them based on task context.

## Advanced Setup

### Smart Session Scheduling

Replace manual cron workarounds with intelligent scheduling:

```bash
# Navigate to the claude-hi directory
cd scripts/claude-hi

# Interactive setup with guided options
make setup

# Quick presets
make standard    # 9am/2pm/7pm schedule
make extended    # 4am/9am/2pm/7pm schedule

# Check current status
make status
```

### Enhanced Statusline

Add comprehensive usage tracking:

```bash
# Install enhanced statusline
make install-statusline

# The statusline will show:
# - Session costs and token usage
# - Time remaining in current window
# - Usage patterns and optimization tips
```

## Configuration

### Interactive Configuration

```bash
# Run interactive configuration
make configure

# This will help you:
# - Select which components to enable
# - Configure security settings
# - Set up development preferences
```

### Manual Configuration

Configuration is primarily managed through the interactive `make configure` wizard, which helps you select specific components to symlink to `~/.claude/`.

## Development Workflow Integration

### Project Setup

When starting a new project:

```bash
# 1. Initialize documentation structure
/docs:init

# 2. Set up quality checks
make pre-commit-install
```

### Daily Development

Your enhanced workflow will include:

1. **Quality Enforcement**: Code standards validated automatically before commits
2. **Smart Documentation**: Generate ADRs, RFCs, and diagrams with slash commands
3. **Specialized Skills**: Claude automatically invokes relevant skills when needed

### Code Review Process

```bash
# Run comprehensive checks before commits
make check                 # All quality checks (lint + type-check)
make test                  # Full test suite
make pre-commit-run        # Run pre-commit checks manually
```

## Troubleshooting

### Common Installation Issues

#### UV Not Found
```bash
# Reinstall UV
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # or ~/.zshrc
```

#### Permission Errors
```bash
# Fix permissions for ~/.claude directory
chmod -R 755 ~/.claude
```

#### Python Version Issues
```bash
# Verify Python version
python3 --version  # Should be 3.12+

# Install correct Python version if needed
# macOS: brew install python@3.12
# Ubuntu: sudo apt install python3.12
```

### Component Issues

#### Commands Not Working
```bash
# Verify command installation
ls ~/.claude/commands/

# Check command syntax
# In Claude Code: "/help" to see available commands
```

### Performance Issues

#### High Resource Usage
```bash
# Monitor system resources
make status

# Disable unnecessary components
make configure
```

## Next Steps

### Explore Advanced Features

1. **Create Custom Skills**: Use the skill-creator skill to build specialized capabilities
2. **Set Up Team Workflows**: Configure consistent settings across team members
3. **Integrate with CI/CD**: Use commands in automated pipelines
4. **Enhanced Statusline**: Track token usage and session costs with `make install-statusline`

### Community and Support

- **Documentation**: Browse `docs/` for detailed guides
- **Issues**: Report bugs at https://github.com/mgiovani/cc-arsenal/issues
- **Discussions**: Ask questions at https://github.com/mgiovani/cc-arsenal/discussions
- **Updates**: Watch the repository for new features and security updates

### Stay Updated

```bash
# Update to latest version
cd cc-arsenal
git pull origin main
make install

# Check for configuration updates
make configure
```

## Security Best Practices

### Initial Security Setup

1. **Configure Access Controls**: Set up appropriate file protection patterns
2. **Enable Audit Trails**: Turn on compliance logging for regulated environments

### Ongoing Security

- Regularly update the arsenal: `git pull && make install`
- Keep dependencies updated: `uv sync --upgrade`

## Performance Optimization

### Token Usage Optimization

1. **Use Smart Scheduling**: Navigate to `scripts/claude-hi` and run `make setup` for optimal timing
2. **Monitor Usage**: Enhanced statusline shows token consumption patterns (install with `make install-statusline`)
3. **Plan Intensive Work**: Schedule complex tasks during fresh usage windows

### System Performance

- **Selective Installation**: Only install components you need
- **Resource Monitoring**: Use `make status` to check system load

---

You're now ready to leverage the full power of Claude Code Arsenal for secure, automated development workflows!

For detailed guides, see:
- [Troubleshooting](troubleshooting.md)
- [Contributing](../CONTRIBUTING.md)
