# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Architecture

This is the **Claude Code Arsenal** - a professional collection of security-focused AI agents, quality automation commands, and safety hooks. The codebase is organized using a **symlink architecture** for clean installation and modular configuration.

### Core Components

- **Agents** (`agents/`): Security-focused AI assistants for code validation, quality control, and compliance
- **Commands** (`commands/`): Quality automation and security scanning workflows  
- **Hooks** (`hooks/`): Safety and validation scripts that run automatically on Claude Code events
- **Scripts** (`scripts/`): Professional Python utilities for installation, configuration, and code generation

### Security-First Integration

This repository implements **Security-First Development** through coordinated security and quality agents:

```
🔍 Security Scan → 🧪 Quality Check → 📋 Compliance Validation → ✅ Approval → 🚀 Deploy
       ↓               ↓                      ↓                   ↓         ↓
security-validator  code-reviewer      compliance-checker   test-orchestrator  deploy-safe
```

## Development Commands

### Installation and Setup
```bash
# Install Python dependencies
cd scripts && uv sync

# Install to ~/.claude directory
uv run scripts/setup/install.py

# Configure components (optional)
uv run scripts/setup/configure.py

# Quick start with preview
make dry-run
make install
make configure
```

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
uv run scripts/generators/agent_generator.py --name "agent-name" --category "development"

# Validate repository structure
make validate-structure

# Show repository information
make info
make show-structure
```

### Backup and Restore
```bash
# Backup current ~/.claude
make backup

# List available backups
make list-backups

# Restore latest backup
make restore-latest
```

## Available Security Agents

### Core Security Agents
- **security-validator**: Authentication validation, access control, and security pattern analysis
- **code-reviewer**: Security-focused code review, vulnerability detection, and quality analysis
- **test-orchestrator**: Automated testing coordination with security and compliance focus

### Compliance Agents
- **compliance-checker**: Regulatory compliance validation (HIPAA, SOX, GDPR)
- **audit-enforcer**: Audit trail generation and compliance reporting
- **data-protector**: PII/PHI detection and data protection validation

*Additional specialized agents available for enterprise users - contact for access*

## Available Commands

### Security Workflow Commands
- **security-scan**: Comprehensive security vulnerability scanning
- **quality-check**: Code quality validation and standards enforcement
- **compliance-audit**: Regulatory compliance checking and reporting
- **test-runner**: Security-focused test execution and coverage analysis

Usage: `/security:scan "src/auth/"`

*Advanced workflow commands available for enterprise users - contact for access*

## Development Patterns

### Agent Usage
```bash
# Direct agent invocation
claude task "Use security-validator to review authentication implementation"

# Multi-agent security workflow
claude task "
1. Use security-validator to analyze authentication patterns
2. Use code-reviewer to scan for security vulnerabilities
3. Use test-orchestrator to run comprehensive security tests
4. Use compliance-checker to validate regulatory requirements
"
```

### Command Workflows
```bash
# Run security scan
claude /security:scan "src/auth/"

# Validate code quality
claude /quality:check "src/"

# Check compliance
claude /compliance:audit "--standard=HIPAA"
```

### Quality Assurance
All code changes should go through the integrated quality gates:
- Security validation via hooks
- Code quality enforcement via pre-commit hooks
- Comprehensive testing via test-orchestrator agent
- Documentation validation

### Technology Stack
- **Python 3.12+** with UV package management
- **Rich CLI interfaces** with progress indicators
- **Pydantic** for data validation and settings
- **Type hints** required for all functions
- **Comprehensive testing** with pytest and >90% coverage

### File Organization
```
cc-arsenal/
├── agents/           # Security-focused AI agents
│   ├── security/     # security-validator, code-reviewer
│   ├── compliance/   # compliance-checker, audit-enforcer
│   ├── quality/      # test-orchestrator, data-protector
│   └── examples/     # Example agent implementations
├── commands/        # Security workflow automation
│   └── security/     # Security scanning and validation workflows
├── hooks/          # Safety and validation
│   ├── security/   # auth_checker, file_protection
│   ├── quality/    # pre_commit_validate
│   └── compliance/ # audit_enforcer, migration_safety
├── scripts/        # Installation and utilities
│   ├── setup/      # install.py, configure.py
│   └── generators/ # agent_generator.py
```