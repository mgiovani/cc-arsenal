# Claude Code Arsenal

🚀 **Lock and load your Claude Code workflow** with a fully-stocked arsenal of AI agents, commands, and security hooks. Deploy your coding firepower in minutes, not hours.

✨ **Armed with excellence, one `make install` away** ✨

## Features

- **Security Agents**: AI agents focused on code security, authentication validation, and vulnerability detection
- **Quality Commands**: Automated commands for code quality, testing, and development workflows
- **Safety Hooks**: Security, quality, and compliance validation scripts
- **Professional Tooling**: Modern Python scripts with UV, comprehensive error handling, and rich CLI interfaces
- **Comprehensive Documentation**: Detailed guides, examples, and best practices
- **Symlink Architecture**: Clean installation via symbolic links for easy updates and customization

## ⚡ Quick Start

### 1. Install the Arsenal
```bash
make install              # Install Claude Code Arsenal to ~/.claude
```

### 2. Replace Manual Cron Workarounds
```bash
make claude-hi-setup      # Interactive smart scheduling setup
# OR
make claude-hi-standard   # Quick 9am/2pm/7pm schedule
```

### 3. Add Enhanced Statusline (Optional)
```bash
make statusline-install   # Enhanced statusline with usage tracking
```

## 🕐 Claude Hi Cron - Smart Session Scheduler

**Stop manually managing cron jobs!** The Claude Hi system automatically triggers Claude's 5-hour usage windows at optimal times.

### Key Benefits
- **🎯 Strategic Timing**: Triggers 5 hours before resets for maximum token availability
- **⚡ Heavy Work Periods**: Last 2 hours of each window = intensive coding time
- **🔄 Clean Management**: Replace ugly cron workarounds with smart scheduling
- **📊 Multiple Patterns**: Early bird, night owl, traditional, freelancer, power user

### Quick Setup Options
```bash
make claude-hi-setup      # Interactive setup with guided options
make claude-hi-standard   # 9am/2pm/7pm → 2pm/7pm/12am resets
make claude-hi-extended   # 4am/9am/2pm/7pm → full day coverage
make claude-hi-custom     # Custom patterns for different work styles
make claude-hi-status     # Check current schedule
```

**Example**: Extended schedule triggers "hi" at 4am, 9am, 2pm, 7pm daily
- **Light usage**: 4-7am, 9am-12pm, 2-5pm, 7-10pm
- **Heavy coding**: **7-9am**, **12-2pm**, 5-7pm, **10pm-12am** (maximum tokens available)

*Perfect for developers who do intensive coding during peak token periods!*

👉 **[Complete Claude Hi Documentation →](scripts/claude-hi/README.md)**

## 🛠️ Available Commands

Claude Code Arsenal includes a comprehensive Makefile with automated commands for installation, development, and maintenance. Run `make help` to see all available commands, or use these common ones:

```bash
# Installation & Setup
make install              # Install all components to ~/.claude
make dry-run              # Preview installation without making changes
make claude-hi-setup      # Smart session scheduler (replaces cron)

# Development
make dev                  # Set up development environment
make test                 # Run comprehensive test suite
make clean                # Clean up caches and temporary files
```

## Repository Structure

```
cc-arsenal/
├── README.md                    # This file
├── CLAUDE.md                     # Claude Code configuration
│
├── agents/                      # AI agents organized by specialty
│   ├── development/             # Development and engineering
│   ├── architecture/            # System design and architecture
│   ├── product/                 # Product management and analysis
│   ├── ux/                      # User experience and design
│   └── orchestration/           # Workflow coordination
│
├── commands/                    # Workflow automation commands
│   ├── security/                # Security scanning workflows
│   ├── git/                     # Git operations (coming soon)
│   ├── testing/                 # Testing workflows (coming soon)
│   └── utility/                 # Development utilities (coming soon)
│
├── hooks/                       # Safety and validation hooks
│   ├── security/                # Security and access control
│   ├── quality/                 # Code quality and standards
│   ├── compliance/              # Regulatory and audit compliance
│   └── project-specific/        # Domain-specific validations
│
├── scripts/                     # Professional Python utilities
│   ├── setup/                   # Installation and configuration
│   ├── generators/              # Code generation tools
│   └── utilities/               # Helper scripts
│
└── docs/                        # Extended documentation
    ├── getting-started.md
    ├── agent-development.md
    ├── command-authoring.md
    └── troubleshooting.md
```

## Quick Start

### Prerequisites
- **Python 3.12+** (for modern language features and performance)
- **UV** (for fast Python package management) - **REQUIRED**
  - Install: `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - Docs: https://docs.astral.sh/uv/getting-started/installation/
- **Claude Code** (Anthropic's official Claude CLI)

### Installation

1. **Clone the repository**:
  ```bash
  git clone https://github.com/your-org/cc-arsenal.git
  cd cc-arsenal
  ```

2. **Quick start with preview**:
  ```bash
  make dry-run          # Preview what will be installed
  ```

3. **Install to Claude Code**:
  ```bash
  make install          # Install all components to ~/.claude
  ```

4. **Configure your setup** (optional):
  ```bash
  make configure        # Interactive configuration
  ```

5. **Restart Claude Code** to load the new configuration

### Alternative Installation Methods

For more control over the installation process:

```bash
# Force install without prompts
make force-install

# Install specific components
make install-statusline  # Just the statusline component

# Backup and restore
make backup             # Backup current ~/.claude
make restore-latest     # Restore latest backup

# See all available commands
make help
```

### Verification

Test your installation by checking if the agents are installed:
```bash
# Check if agents are installed in ~/.claude
ls ~/.claude/agents/

# Test by requesting an agent in Claude Code
# (Direct request in Claude Code CLI - no shell command needed)

# Or check installation status
make info              # Show repository information
make validate-structure # Validate installation
```

## Core Components

### 🤖 Agents

Specialized AI assistants for different domains:

- **security-validator**: Authentication and access control validation
- **code-reviewer**: Code quality analysis and security scanning
- **test-orchestrator**: Test automation and quality assurance coordination

*Additional specialized agents available for enterprise users - contact for access*

See agents/ directory for available AI assistants

### ⚡ Commands

Security and quality workflow automation:

- **security-scan**: Automated security vulnerability scanning
- **quality-check**: Code quality and standards validation
- **test-runner**: Comprehensive test execution and reporting

*Advanced workflow commands available for enterprise users - contact for access*

See commands/ directory for workflow automation

### 🔒 Hooks

Safety and validation automation:

- **Security**: Authentication, file protection, access control
- **Quality**: Code standards, testing, documentation validation
- **Compliance**: Regulatory requirements, audit trails
- **Project-Specific**: Domain-specific validations (healthcare, finance, etc.)

See hooks/ directory for safety and validation

## Security-First Development

Claude Code Arsenal emphasizes security and quality in all development workflows:

### Core Principles
- **Security First**: All code changes validated for security vulnerabilities and sensitive data
- **Quality Gates**: Automated quality checks integrated into every workflow
- **Compliance Ready**: Built-in hooks for regulatory compliance (HIPAA, SOX, etc.)
- **Zero-Trust**: Assume all inputs are potentially malicious until validated
- **Documentation-Driven**: Comprehensive logging and audit trails for all operations

## Usage Examples

### Development Workflow
```bash
# Run security scan
claude /security:scan "src/"

# Validate code quality
claude /quality:check "src/auth/"

# Run comprehensive tests
claude /test:runner "--coverage --security"
```

### Agent Collaboration
```
# Security validation workflow (direct request to Claude Code)
"Use security-validator to check authentication patterns, then code-reviewer to analyze implementation security, then test-orchestrator to run comprehensive security tests"
```

### Customization
```bash
# Generate a new security agent for your domain
make generate-agent NAME=crypto-validator CATEGORY=security

# Configure which components to use
make configure
```

## Development

### Contributing

We welcome contributions! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Develop** your changes with tests and documentation
4. **Validate** with our quality checks: `make check`
5. **Submit** a pull request with detailed description

### Development Setup

```bash
# Clone for development
git clone https://github.com/your-org/cc-arsenal.git
cd cc-arsenal

# Set up development environment (installs dev dependencies)
make dev

# Install pre-commit hooks for automatic code quality
make pre-commit-install

# Run all quality checks
make check           # Runs lint + type-check
make lint           # Linting only
make format         # Code formatting
make type-check     # Type checking only

# Run tests
make test           # Unit tests
make coverage       # Tests with coverage report

# Validate repository structure
make validate-structure

# See all available development commands
make help
```

### Quality Standards

- **Python 3.12+** with modern language features
- **Type hints** for all functions and classes
- **Comprehensive tests** with >90% coverage
- **Rich CLI interfaces** with progress indicators and error handling
- **Detailed documentation** with examples and troubleshooting
- **Security-first** approach with input validation and error handling

## Documentation

- **agents/**: AI development assistants organized by specialty
- **commands/**: Workflow automation and development utilities
- **hooks/**: Safety validation and quality enforcement
- **[docs/getting-started.md](docs/getting-started.md)**: Detailed setup and configuration guide
- **[docs/agent-development.md](docs/agent-development.md)**: Creating custom agents
- **[docs/troubleshooting.md](docs/troubleshooting.md)**: Common issues and solutions

## Support

### Getting Help
- **🐛 Issues**: [Open a GitHub issue](https://github.com/your-org/cc-arsenal/issues) for bugs or feature requests
- **💬 Discussions**: [GitHub Discussions](https://github.com/your-org/cc-arsenal/discussions) for questions and ideas
- **📖 Documentation**: Check the `docs/` directory for detailed guides

### Common Issues
- **Installation Problems**: See [troubleshooting guide](docs/troubleshooting.md)
- **Configuration Issues**: Run `make configure` for interactive setup or `make help` for all options
- **Performance**: Monitor agent usage and consider selective installation

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Anthropic** for Claude Code and the Claude API
- **Security Community** for best practices and vulnerability research
- **Contributors** who help improve and extend this arsenal

---

**Ready to secure your Claude Code projects?** Start with `make install` and deploy enterprise-grade security and quality automation.

*Built with Claude for Claude*
