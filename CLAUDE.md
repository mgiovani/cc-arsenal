# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Architecture

This is the **Claude Code Arsenal** - a professional collection of security-focused AI agents, quality automation commands, and safety hooks. The codebase is organized using a **symlink architecture** for clean installation and modular configuration.

### Core Components

- **Agents** (`agents/`): AI assistants for specialized development tasks
- **Commands** (`commands/`): Quality automation and workflow commands
- **Hooks** (`hooks/`): Safety and validation scripts that run automatically on Claude Code events
- **Scripts** (`scripts/`): Professional Python utilities for installation, configuration, and code generation

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
Workflow automation commands (currently in development):
- **Git operations**: Repository management
- **Testing**: Test automation and quality assurance
- **Utility**: General-purpose development helpers

### Hooks
Safety and validation automation:
- **Security hooks**: Authentication and data protection
- **Quality hooks**: Code standards and pre-commit validation
- **Compliance hooks**: Audit trails and regulatory compliance

## Development Patterns

### Agent Usage
```bash
# Use specialized agents via Task tool
claude task "Use the bmad-dev agent to implement user authentication"
```

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
│   ├── git/            # Git operations
│   ├── testing/        # Test automation
│   └── utility/        # Development utilities
├── hooks/          # Safety and validation
│   ├── security/       # Authentication and protection
│   ├── quality/        # Code standards and validation
│   └── compliance/     # Audit and regulatory
├── scripts/        # Installation and utilities
│   ├── setup/          # install.py, configure.py
│   ├── generators/     # agent_generator.py
│   ├── claude/         # Claude Code utilities
│   └── claude-hi/      # Session management
```
