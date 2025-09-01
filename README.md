# Claude Code Arsenal

A professional, production-ready collection of Claude Code agents, commands, and hooks. This repository provides essential tools for security, quality control, and development automation that can be easily integrated into any Claude Code project.

## 🚀 Features

- **🤖 Security Agents**: AI agents focused on code security, authentication validation, and vulnerability detection
- **⚡ Quality Commands**: Automated commands for code quality, testing, and development workflows
- **🔒 Safety Hooks**: Security, quality, and compliance validation scripts
- **🛠️ Professional Tooling**: Modern Python scripts with UV, comprehensive error handling, and rich CLI interfaces
- **📚 Comprehensive Documentation**: Detailed guides, examples, and best practices
- **🔗 Symlink Architecture**: Clean installation via symbolic links for easy updates and customization

## 📁 Repository Structure

```
cc-arsenal/
├── 📖 README.md                 # This file
├── 📋 AGENTS.md                 # Complete agents reference
├── 📋 COMMANDS.md               # Complete commands reference  
├── 📋 HOOKS.md                  # Complete hooks reference
├── 🔗 CLAUDE.md → AGENTS.md     # Backward compatibility symlink
│
├── 🤖 agents/                   # AI agents organized by specialty
│   ├── development/             # Development and engineering
│   ├── architecture/            # System design and architecture
│   ├── product/                 # Product management and analysis
│   ├── ux/                      # User experience and design
│   └── orchestration/           # Workflow coordination
│
├── ⚡ commands/                 # Workflow automation commands
│   ├── security/                # Security scanning workflows
│   ├── git/                     # Git operations (coming soon)
│   ├── testing/                 # Testing workflows (coming soon)
│   └── utility/                 # Development utilities (coming soon)
│
├── 🔒 hooks/                    # Safety and validation hooks
│   ├── security/                # Security and access control
│   ├── quality/                 # Code quality and standards
│   ├── compliance/              # Regulatory and audit compliance
│   └── project-specific/        # Domain-specific validations
│
├── 🐍 scripts/                  # Professional Python utilities
│   ├── setup/                   # Installation and configuration
│   ├── generators/              # Code generation tools
│   └── utilities/               # Helper scripts
│
└── 📚 docs/                     # Extended documentation
    ├── getting-started.md
    ├── agent-development.md
    ├── command-authoring.md
    └── troubleshooting.md
```

## 🏃‍♂️ Quick Start

### Prerequisites
- **Python 3.12+** (for modern language features and performance)
- **UV** (for fast Python package management)
- **Claude Code** (Anthropic's official Claude CLI)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/mgiovani/cc-arsenal.git
   cd cc-arsenal
   ```

2. **Install Python dependencies**:
   ```bash
   cd scripts
   uv sync
   ```

3. **Install Claude configuration**:
   ```bash
   uv run setup/install.py
   ```

4. **Configure your setup** (optional):
   ```bash
   uv run setup/configure.py
   ```

5. **Restart Claude Code** to load the new configuration

### Verification

Test your installation by listing available agents:
```bash
claude agents list
```

Or invoke a specific agent:
```bash
claude task "Use the security-validator agent to analyze this codebase structure"
```

## 🎯 Core Components

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

## 🔐 Security-First Development

Claude Code Arsenal emphasizes security and quality in all development workflows:

### Core Principles
- **Security First**: All code changes validated for security vulnerabilities and sensitive data
- **Quality Gates**: Automated quality checks integrated into every workflow
- **Compliance Ready**: Built-in hooks for regulatory compliance (HIPAA, SOX, etc.)
- **Zero-Trust**: Assume all inputs are potentially malicious until validated
- **Documentation-Driven**: Comprehensive logging and audit trails for all operations

## 📖 Usage Examples

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
uv run generators/agent_generator.py --name "crypto-validator" --category "security"

# Configure which components to use
uv run setup/configure.py --quick
```

## 🛠️ Development

### Contributing

We welcome contributions! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Develop** your changes with tests and documentation
4. **Validate** with our quality checks: `uv run scripts/validate.py`
5. **Submit** a pull request with detailed description

### Development Setup

```bash
# Clone for development
git clone https://github.com/mgiovani/cc-arsenal.git
cd cc-arsenal/scripts

# Install with dev dependencies
uv sync --dev

# Set up pre-commit hooks
pre-commit install

# Run tests
pytest

# Code formatting and linting
black .
ruff check .
mypy .
```

### Quality Standards

- **Python 3.12+** with modern language features
- **Type hints** for all functions and classes
- **Comprehensive tests** with >90% coverage
- **Rich CLI interfaces** with progress indicators and error handling
- **Detailed documentation** with examples and troubleshooting
- **Security-first** approach with input validation and error handling

## 📚 Documentation

- **[AGENTS.md](AGENTS.md)**: Complete reference for all available agents
- **[COMMANDS.md](COMMANDS.md)**: Workflow automation commands and usage
- **[HOOKS.md](HOOKS.md)**: Safety hooks and validation automation
- **[docs/getting-started.md](docs/getting-started.md)**: Detailed setup and configuration guide
- **[docs/agent-development.md](docs/agent-development.md)**: Creating custom agents
- **[docs/troubleshooting.md](docs/troubleshooting.md)**: Common issues and solutions

## 🤝 Support

### Getting Help
- **🐛 Issues**: [Open a GitHub issue](https://github.com/mgiovani/cc-arsenal/issues) for bugs or feature requests
- **💬 Discussions**: [GitHub Discussions](https://github.com/mgiovani/cc-arsenal/discussions) for questions and ideas
- **📖 Documentation**: Check the `docs/` directory for detailed guides

### Common Issues
- **Installation Problems**: See [troubleshooting guide](docs/troubleshooting.md)
- **Configuration Issues**: Run `uv run setup/configure.py --help` for options
- **Performance**: Monitor agent usage and consider selective installation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Anthropic** for Claude Code and the Claude API
- **Security Community** for best practices and vulnerability research
- **Contributors** who help improve and extend this arsenal

---

**Ready to secure your Claude Code projects?** Start with `uv run setup/install.py` and deploy enterprise-grade security and quality automation.

*Built with 🔐 for secure development*