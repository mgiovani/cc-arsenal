# CLAUDE.md - Claude template repository

This file provides guidance to Claude Code (claude.ai/code) when working with this Claude template repository.

## Repository architecture

This is a Claude Code template repository. It packages a professional set of specialized AI agents, plus the commands and hooks that wire them into a project. The codebase uses a symlink architecture for clean installation and modular configuration.

### Core components

| Component | Path | Purpose |
|---|---|---|
| Agents | `agents/` | Specialized AI assistants organized by domain (development, architecture, product, UX, orchestration) |
| Commands | `commands/` | Security and quality workflow automation |
| Hooks | `hooks/` | Safety and validation scripts that run automatically on Claude Code events |
| Scripts | `scripts/` | Professional Python utilities for installation, configuration, and code generation |

### Security-first integration

This repository implements security-first development through coordinated security and quality agents:

```
🔍 Security Scan → 🧪 Quality Check → 📋 Compliance Validation → ✅ Approval → 🚀 Deploy
        ↓               ↓                      ↓                   ↓         ↓
security-validator  code-reviewer      compliance-checker   test-orchestrator  deploy-safe
```

## Development commands

### Installation and setup
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

### Development environment
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

### Project management
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

## Available specialized agents

| Category | Agent | Purpose |
|---|---|---|
| Development | `security-validator` | Validates authentication and access control, and analyzes security patterns |
| Development | `code-reviewer` | Security-focused code review that also covers vulnerability detection and quality analysis |
| Development | `test-orchestrator` | Automated testing coordination with security and compliance focus |
| Compliance | `compliance-checker` | Regulatory compliance validation (HIPAA, SOX, GDPR) |
| Compliance | `audit-enforcer` | Audit trail generation and compliance reporting |
| Compliance | `data-protector` | PII/PHI detection and data protection validation |

*Additional specialized agents available for enterprise users*

## Available commands

| Command | Purpose |
|---|---|
| `security-scan` | Comprehensive security vulnerability scanning |
| `quality-check` | Code quality validation and standards enforcement |
| `compliance-audit` | Regulatory compliance checking and reporting |
| `test-runner` | Security-focused test execution and coverage analysis |

Usage: `/security:scan "src/auth/"`

*Advanced workflow commands available for enterprise users*

## Development patterns

### Agent usage
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

### Command workflows
```bash
# Start new feature development
claude /security:scan "User authentication system with JWT tokens"

# Validate code quality
claude /quality:check "E-commerce platform"

# Check compliance
claude /compliance:audit "src/auth/"
```

### Technology stack

| Aspect | Detail |
|---|---|
| Language | Python 3.12+ with UV package management |
| CLI | Rich CLI interfaces with progress indicators |
| Validation | Pydantic for data validation and settings |
| Typing | Type hints required for all functions |
| Testing | Comprehensive testing with pytest and >90% coverage |
