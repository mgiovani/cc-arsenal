# CLAUDE.md - Claude Template Repository

This file provides guidance to Claude Code (claude.ai/code) when working with this Claude template repository.

## Repository Architecture

This is a **Claude Code template repository** that provides a professional collection of specialized AI agents, workflow automation commands, and safety hooks. The codebase is organized using a **symlink architecture** for clean installation and modular configuration.

### Core Components

- **Agents** (`agents/`): Specialized AI assistants organized by domain (development, architecture, product, UX, orchestration)
- **Commands** (`commands/`): Security and quality workflow automation
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

## Available Specialized Agents

### Development Agents
- **security-validator**: Authentication validation, access control, and security pattern analysis
- **code-reviewer**: Security-focused code review, vulnerability detection, and quality analysis
- **test-orchestrator**: Automated testing coordination with security and compliance focus

### Compliance Agents
- **compliance-checker**: Regulatory compliance validation (HIPAA, SOX, GDPR)
- **audit-enforcer**: Audit trail generation and compliance reporting
- **data-protector**: PII/PHI detection and data protection validation

*Additional specialized agents available for enterprise users*

## Available Commands

### Security Workflow Commands
- **security-scan**: Comprehensive security vulnerability scanning
- **quality-check**: Code quality validation and standards enforcement
- **compliance-audit**: Regulatory compliance checking and reporting
- **test-runner**: Security-focused test execution and coverage analysis

Usage: `/security:scan "src/auth/"`

*Advanced workflow commands available for enterprise users*

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
# Start new feature development
claude /security:scan "User authentication system with JWT tokens"

# Validate code quality
claude /quality:check "E-commerce platform"

# Check compliance
claude /compliance:audit "src/auth/"
```

### Technology Stack
- **Python 3.12+** with UV package management
- **Rich CLI interfaces** with progress indicators
- **Pydantic** for data validation and settings
- **Type hints** required for all functions
- **Comprehensive testing** with pytest and >90% coverage
