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

## Available Commands

Claude Code Arsenal includes a comprehensive Makefile with automated commands for installation, development, and maintenance. Run `make help` to see all available commands, or use these common ones:

```bash
make dry-run     # Preview installation without making changes
make install     # Install all components to ~/.claude
make dev         # Set up development environment
make test        # Run comprehensive test suite
make clean       # Clean up caches and temporary files
```

## Repository Structure

```
cc-arsenal/
├── README.md                    # This file
├── AGENTS.md                    # Complete agents reference
├── COMMANDS.md                  # Complete commands reference  
├── HOOKS.md                     # Complete hooks reference
├── CLAUDE.md → AGENTS.md        # Backward compatibility symlink
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
   git clone https://github.com/mgiovani/cc-arsenal.git
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

# Test by invoking a specific agent
claude task "Use the security-validator agent to analyze this codebase structure"

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

[→ See complete agents documentation](AGENTS.md)

### ⚡ Commands

Security and quality workflow automation:

- **security-scan**: Automated security vulnerability scanning
- **quality-check**: Code quality and standards validation
- **test-runner**: Comprehensive test execution and reporting

*Advanced workflow commands available for enterprise users - contact for access*

[→ See complete commands documentation](COMMANDS.md)

### 🔒 Hooks

Safety and validation automation:

- **Security**: Authentication, file protection, access control
- **Quality**: Code standards, testing, documentation validation
- **Compliance**: Regulatory requirements, audit trails
- **Project-Specific**: Domain-specific validations (healthcare, finance, etc.)

[→ See complete hooks documentation](HOOKS.md)

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
```bash
# Security validation workflow
claude task "
1. Use security-validator to check authentication patterns
2. Use code-reviewer to analyze implementation security
3. Use test-orchestrator to run comprehensive security tests
"
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
git clone https://github.com/mgiovani/cc-arsenal.git
cd cc-arsenal

# Set up development environment (installs dev dependencies)
make dev

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

- **[AGENTS.md](AGENTS.md)**: Complete reference for all available agents
- **[COMMANDS.md](COMMANDS.md)**: Workflow automation commands and usage
- **[HOOKS.md](HOOKS.md)**: Safety hooks and validation automation
- **[docs/getting-started.md](docs/getting-started.md)**: Detailed setup and configuration guide
- **[docs/agent-development.md](docs/agent-development.md)**: Creating custom agents
- **[docs/troubleshooting.md](docs/troubleshooting.md)**: Common issues and solutions

## Support

### Getting Help
- **🐛 Issues**: [Open a GitHub issue](https://github.com/mgiovani/cc-arsenal/issues) for bugs or feature requests
- **💬 Discussions**: [GitHub Discussions](https://github.com/mgiovani/cc-arsenal/discussions) for questions and ideas
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