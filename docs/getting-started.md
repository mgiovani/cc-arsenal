# Getting Started with Claude Code Arsenal

A comprehensive guide to setting up and using the Claude Code Arsenal for secure, automated development workflows.

## Overview

Claude Code Arsenal is a professional collection of security-focused AI agents, quality automation commands, and safety hooks designed to enhance your Claude Code development experience with enterprise-grade security and automation.

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
make install-agents        # AI agents only
make install-hooks         # Safety hooks only
```

## Verification

After installation, verify everything is working:

```bash
# Check if components are installed
ls ~/.claude/agents/
ls ~/.claude/commands/
ls ~/.claude/hooks/

# Validate installation
make info
make validate-structure

# Test agent availability (in Claude Code)
# Request an agent like: "Use the bmad-dev agent to help with authentication"
```

## Core Components

### 🤖 AI Agents

Specialized AI assistants organized by domain:

#### Available Categories

- **Architecture**: System design and technical architecture specialists
- **Development**: Code implementation and debugging experts
- **Orchestration**: Workflow coordination and automation masters
- **Product**: Product management and requirements analysts
- **Productivity**: Development efficiency and optimization specialists
- **UX**: User experience and design experts

#### Using Agents

Request agents directly in Claude Code:

```
Use the bmad-dev agent to implement user authentication with JWT tokens
```

```
Use the security-validator to check authentication patterns in the codebase
```

### ⚡ Commands

Workflow automation for common development tasks:

#### Available Commands

- **Security Scan**: Automated vulnerability scanning
- **Quality Check**: Code standards validation
- **Test Runner**: Comprehensive test execution

#### Using Commands

```bash
# Run security scan
claude /security:scan "src/"

# Validate code quality
claude /quality:check "src/auth/"

# Run comprehensive tests
claude /test:runner "--coverage --security"
```

### 🔒 Hooks

Automated safety and validation:

#### Hook Categories

- **Security**: Authentication, file protection, access control
- **Quality**: Code standards, testing, documentation validation
- **Compliance**: Regulatory requirements, audit trails

#### Hook Configuration

Configure hooks via `~/.claude/hook-config.yaml`:

```yaml
file_protection:
  enabled: true
  protected_patterns:
    - "*.env*"
    - "secrets.*"

audit_enforcer:
  enabled: true
  compliance_standards:
    - "GDPR"
    - "SOX"
```

## Advanced Setup

### Smart Session Scheduling

Replace manual cron workarounds with intelligent scheduling:

```bash
# Interactive setup with guided options
make claude-hi-setup

# Quick presets
make claude-hi-standard    # 9am/2pm/7pm schedule
make claude-hi-extended    # 4am/9am/2pm/7pm schedule

# Check current status
make claude-hi-status
```

### Enhanced Statusline

Add comprehensive usage tracking:

```bash
# Install enhanced statusline
make statusline-install

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
# - Choose hook policies
```

### Manual Configuration

Edit configuration files directly:

```bash
# Agent configuration
~/.claude/agent-config.yaml

# Hook configuration
~/.claude/hook-config.yaml

# Command configuration
~/.claude/command-config.yaml
```

## Development Workflow Integration

### Project Setup

When starting a new project:

```bash
# 1. Initialize your project with quality tools
make project-init

# 2. Set up security scanning
claude /security:scan --setup

# 3. Configure quality gates
claude /quality:check --setup

# 4. Enable relevant hooks for your project type
make configure-hooks
```

### Daily Development

Your enhanced workflow will include:

1. **Automatic Security Validation**: Hooks prevent commits with secrets or vulnerabilities
2. **Quality Enforcement**: Code standards validated automatically
3. **Smart Session Management**: Optimal timing for intensive coding work
4. **AI Agent Assistance**: Specialized help for different development tasks

### Code Review Process

```bash
# Run comprehensive checks before commits
make check                 # All quality checks
make security-scan         # Security vulnerability scan
make test                  # Full test suite

# Use AI agents for review
# "Use code-reviewer to analyze this authentication implementation"
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

#### Agents Not Available
```bash
# Verify agent installation
ls ~/.claude/agents/

# Reinstall if needed
make install-agents

# Test specific agent
# In Claude Code: "List available agents"
```

#### Hooks Not Triggering
```bash
# Check hook configuration
cat ~/.claude/hook-config.yaml

# Verify hook permissions
ls -la ~/.claude/hooks/

# Test hook manually
echo '{"test": true}' | ~/.claude/hooks/security/auth_checker.py
```

#### Commands Not Working
```bash
# Verify command installation
ls ~/.claude/commands/

# Check command syntax
# In Claude Code: "/help" to see available commands
```

### Performance Issues

#### Slow Agent Response
- Check available tokens: Enhanced statusline shows usage
- Consider using lighter agents for simple tasks
- Schedule intensive work during fresh usage windows

#### High Resource Usage
```bash
# Monitor system resources
make status

# Disable unnecessary components
make configure
```

## Next Steps

### Explore Advanced Features

1. **Create Custom Agents**: Use `make generate-agent` to create specialized agents
2. **Set Up Team Workflows**: Configure consistent settings across team members
3. **Integrate with CI/CD**: Use hooks and commands in automated pipelines
4. **Monitor Security**: Set up automated security scanning and compliance

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

1. **Review Hook Configuration**: Ensure appropriate security policies are enabled
2. **Test Secret Detection**: Verify hooks prevent committing sensitive data
3. **Configure Access Controls**: Set up appropriate file protection patterns
4. **Enable Audit Trails**: Turn on compliance logging for regulated environments

### Ongoing Security

- Regularly update the arsenal: `git pull && make install`
- Review security scan results: `claude /security:scan`
- Monitor hook logs for security events
- Keep dependencies updated: `uv sync --upgrade`

## Performance Optimization

### Token Usage Optimization

1. **Use Smart Scheduling**: `make claude-hi-setup` for optimal timing
2. **Choose Appropriate Agents**: Use specialized agents for specific tasks
3. **Monitor Usage**: Enhanced statusline shows token consumption patterns
4. **Plan Intensive Work**: Schedule complex tasks during fresh usage windows

### System Performance

- **Selective Installation**: Only install components you need
- **Hook Optimization**: Disable unnecessary hooks for faster operations
- **Resource Monitoring**: Use `make status` to check system load

---

You're now ready to leverage the full power of Claude Code Arsenal for secure, automated development workflows!

For detailed component guides, see:
- [Agent Development](agent-development.md)
- [Troubleshooting](troubleshooting.md)
- [Contributing](../CONTRIBUTING.md)
