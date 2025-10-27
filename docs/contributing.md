# Contributing to Claude Code Arsenal

Thank you for your interest in contributing to Claude Code Arsenal! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Community](#community)

## Code of Conduct

We are committed to providing a welcoming and inspiring community for all. Please read and follow our [Code of Conduct](./CODE_OF_CONDUCT.md).

**Expected Behavior:**
- Be respectful and inclusive
- Exercise empathy and kindness
- Give and gracefully accept constructive feedback
- Focus on what is best for the community
- Assume positive intent

**Unacceptable Behavior:**
- Harassment, discrimination, or offensive comments
- Trolling, insulting, or derogatory comments
- Public or private harassment
- Publishing others' private information
- Other conduct which could reasonably be considered inappropriate

## Getting Started

### Prerequisites

Before you begin, ensure you have:
- **Python 3.12+**: Modern Python version with latest features
- **UV Package Manager**: Fast, modern Python package installer
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- **Git**: For version control
- **Claude Code**: Host environment for testing
- **GitHub Account**: With repository access for PRs

### Development Setup

See [onboarding.md](./onboarding.md) for detailed setup instructions.

Quick start:
```bash
# Fork and clone the repository
git clone https://github.com/YOUR-USERNAME/cc-arsenal.git
cd cc-arsenal

# Install dependencies
uv sync --extra dev

# Install to Claude Code
make install

# Run tests
make test

# Run all quality checks
make check
```

## How to Contribute

### Reporting Bugs

Before creating a bug report:
1. **Check existing issues** to avoid duplicates
2. **Use the latest version** to verify the bug still exists
3. **Collect environment information**:
   - Python version: `python --version`
   - UV version: `uv --version`
   - Claude Code version
   - Operating system

When reporting a bug, include:
- **Description**: Clear, concise description of the issue
- **Steps to Reproduce**: Step-by-step instructions
  ```
  1. Install cc-arsenal via make install
  2. Run /git:commit command
  3. Error occurs: "..."
  ```
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Environment**: OS, Python version, Claude Code version
- **Logs**: Relevant error messages or logs
- **Screenshots**: If applicable (especially for CLI output)

**Use the Bug Report Template:**
```markdown
**Bug Description**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. ...
2. ...

**Expected Behavior**
A clear description of what you expected to happen.

**Environment**
- OS: [e.g., macOS 14.0]
- Python: [e.g., 3.12.0]
- UV: [e.g., 0.1.0]
- Claude Code: [e.g., 1.0.0]

**Additional Context**
Any other context about the problem.
```

### Suggesting Enhancements

Enhancement suggestions are welcome! Include:

- **Use Case**: Why is this enhancement needed?
  - What problem does it solve?
  - Who will benefit from it?

- **Proposed Solution**: How should it work?
  - Detailed description of the feature
  - Example usage or API
  - UI/UX considerations (for commands/CLI)

- **Alternatives**: What other solutions were considered?
  - Why is your proposal better?
  - Trade-offs and considerations

- **Impact**: Who will benefit from this enhancement?
  - User personas (agent creators, contributors, end users)
  - Priority level (critical, high, medium, low)

### Contributing Code

#### 1. Fork and Clone

```bash
# Fork via GitHub UI, then:
git clone https://github.com/YOUR-USERNAME/cc-arsenal.git
cd cc-arsenal

# Add upstream remote
git remote add upstream https://github.com/mgiovani/cc-arsenal.git
```

#### 2. Create a Branch

```bash
# For new features
git checkout -b feature/descriptive-name

# For bug fixes
git checkout -b fix/descriptive-name

# For documentation
git checkout -b docs/descriptive-name
```

**Branch Naming:**
- `feature/docs-diagram-command` - New command
- `feature/jira-skill-enhancement` - New skill feature
- `fix/file-protection-pattern` - Bug fix
- `docs/contributing-guide` - Documentation
- `refactor/generator-cleanup` - Code refactoring

#### 3. Make Your Changes

**For New Commands:**
```bash
# Create command file in appropriate category
vim commands/utility/my-command.md

# Add YAML frontmatter and implementation
# Test in Claude Code
```

**For New Skills:**
```bash
# Create skill directory
mkdir -p skills/my-skill

# Create SKILL.md with frontmatter
vim skills/my-skill/SKILL.md

# Add bundled resources if needed
mkdir -p skills/my-skill/scripts
```

**General Guidelines:**
- Follow existing patterns and conventions
- Write clean, readable code
- Add type hints to all Python functions
- Include docstrings for public APIs
- Update documentation as needed

#### 4. Add Tests

```bash
# Create test file
vim tests/test_my_feature.py

# Write comprehensive tests
# Aim for >90% coverage for new code
```

**Test Structure:**
```python
"""Tests for my feature."""

import pytest


class TestMyFeature:
    """Test suite for my feature."""

    def test_basic_functionality(self) -> None:
        """Test basic functionality works correctly."""
        # Arrange
        input_data = "test"

        # Act
        result = my_function(input_data)

        # Assert
        assert result == "expected"

    def test_error_handling(self) -> None:
        """Test error handling works correctly."""
        with pytest.raises(ValueError):
            my_function(None)
```

#### 5. Run Quality Checks

```bash
# Run all checks (lint, format, type-check, test)
make check

# Fix auto-fixable issues
make format

# Run tests with coverage
make coverage
```

#### 6. Commit Your Changes

```bash
git add .
git commit -m "type(scope): description"
```

Follow [Conventional Commits](https://www.conventionalcommits.org/):

**Commit Format:**
```
type(scope): subject

[optional body]

[optional footer]
```

**Types:**
- `feat:` - New feature (agent, command, hook, skill)
- `fix:` - Bug fix
- `docs:` - Documentation only
- `style:` - Code style (formatting, no logic change)
- `refactor:` - Code refactoring (no functional change)
- `test:` - Adding or updating tests
- `chore:` - Maintenance (dependencies, tooling)

**Scopes:**
- `commands` - Command-related changes
- `hooks` - Hook-related changes
- `skills` - Skill-related changes
- `plugin` - Plugin configuration changes
- `scripts` - Installation/generation scripts
- `tests` - Test infrastructure
- `docs` - Documentation

**Examples:**
```bash
git commit -m "feat(commands): add docs:api command for API documentation"
git commit -m "feat(skills): add Linear integration skill"
git commit -m "fix(hooks): correct file protection regex pattern"
git commit -m "docs(onboarding): add troubleshooting section"
git commit -m "test(commands): add integration tests for git:commit"
git commit -m "chore(deps): update pydantic to 2.5.1"
```

#### 7. Push and Create Pull Request

```bash
# Push your branch
git push origin your-branch-name

# Create PR via GitHub UI
# Fill out the PR template
```

## Pull Request Process

### Before Submitting

Use this checklist:

- [ ] Code follows project coding standards
- [ ] All tests pass locally (`make test`)
- [ ] New tests added for new functionality
- [ ] Test coverage >90% for new code (`make coverage`)
- [ ] Type checking passes (`make type-check`)
- [ ] Linting passes (`make lint`)
- [ ] Documentation updated (README, CLAUDE.md, docs/)
- [ ] Commit messages follow conventional format
- [ ] Branch is up to date with main
- [ ] No merge conflicts

### PR Guidelines

**Title Format:**
```
type(scope): Brief description
```

**Description Template:**
```markdown
## Summary
Brief description of what this PR does.

## Changes
- Change 1
- Change 2
- Change 3

## Related Issues
Fixes #123
Closes #456

## Testing
How was this tested?
- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing in Claude Code

## Screenshots (if applicable)
[Add screenshots for CLI output or UI changes]

## Breaking Changes
[Describe any breaking changes, or "None"]

## Checklist
- [ ] Tests pass
- [ ] Documentation updated
- [ ] Follows coding standards
```

**Review Process:**
1. **Automated Checks**: CI/CD runs linting, type checking, tests
2. **Code Review**: Maintainers review code quality and design
3. **Feedback**: Address review comments
4. **Approval**: At least one maintainer approval required
5. **Merge**: Squash and merge to main

### After Your PR is Merged

```bash
# Delete your feature branch
git branch -d feature/my-feature

# Update your fork
git checkout main
git pull upstream main
git push origin main

# Celebrate! 🎉
```

## Coding Standards

### General Principles

- **DRY**: Don't Repeat Yourself
- **KISS**: Keep It Simple, Stupid
- **YAGNI**: You Aren't Gonna Need It
- **SOLID**: Follow SOLID principles
- **Separation of Concerns**: Clear module boundaries

### Python Code Style

**Follow PEP 8 with project customizations:**

- **Line Length**: 90 characters (not 79)
- **Quotes**: Single quotes for strings (except docstrings)
- **Indentation**: 4 spaces (no tabs)
- **Type Hints**: Required for all function signatures
- **Docstrings**: Google-style for public APIs

**Naming Conventions:**
```python
# Variables and functions: snake_case
user_name = "John"
def calculate_total() -> int:
    pass

# Classes: PascalCase
class UserManager:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3
API_URL = "https://api.example.com"

# Private members: _leading_underscore
def _internal_helper() -> None:
    pass
```

**Type Hints:**
```python
from typing import List, Dict, Optional

def process_data(
    items: List[str],
    config: Dict[str, Any],
    max_count: Optional[int] = None
) -> List[Dict[str, str]]:
    """Process data with configuration.

    Args:
        items: List of items to process
        config: Configuration dictionary
        max_count: Maximum items to process (optional)

    Returns:
        Processed data as list of dictionaries
    """
    ...
```

**Docstrings:**
```python
def my_function(arg1: str, arg2: int) -> bool:
    """Brief description of what the function does.

    More detailed description if needed. Explain the purpose,
    behavior, and any important considerations.

    Args:
        arg1: Description of first argument
        arg2: Description of second argument

    Returns:
        Description of return value

    Raises:
        ValueError: When arg2 is negative
        TypeError: When arg1 is not a string
    """
    ...
```

**Comments:**
- Write self-documenting code (good variable/function names)
- Add comments for complex logic or non-obvious decisions
- Keep comments up to date with code changes
- Use `# TODO:` for future improvements
- Use `# FIXME:` for known issues

**File Organization:**
```python
"""Module docstring describing the module."""

# Standard library imports
import os
import sys
from typing import List

# Third-party imports
import click
from rich.console import Console

# Local imports
from scripts.config import Config
from scripts.utils import validate_path

# Constants
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30

# Classes and functions
class MyClass:
    """Class docstring."""
    ...

def my_function() -> None:
    """Function docstring."""
    ...

# Main execution
if __name__ == '__main__':
    main()
```

## Testing Guidelines

### Test Requirements

- **Coverage**: >90% for new code, maintain overall coverage
- **Unit Tests**: All new functions/methods
- **Integration Tests**: New features and workflows
- **Test Organization**: Mirror source structure in tests/

### Writing Tests

**Test Structure:**
```python
"""Tests for agent generator."""

import pytest
from pathlib import Path

from scripts.generators.agent_generator import generate_agent


class TestAgentGenerator:
    """Test suite for agent generator."""

    def test_generate_basic_agent(self, tmp_path: Path) -> None:
        """Test generating a basic agent."""
        # Arrange
        name = "test-agent"
        category = "development"

        # Act
        result = generate_agent(name, category, output_dir=tmp_path)

        # Assert
        assert result.exists()
        assert result.name == f"{name}.md"

    def test_generate_agent_with_custom_description(self) -> None:
        """Test generating agent with custom description."""
        ...

    def test_generate_agent_invalid_category(self) -> None:
        """Test error handling for invalid category."""
        with pytest.raises(ValueError, match="Invalid category"):
            generate_agent("test", "invalid")


@pytest.fixture
def sample_agent_file(tmp_path: Path) -> Path:
    """Create a sample agent file for testing."""
    agent_file = tmp_path / "test-agent.md"
    agent_file.write_text("# Test Agent\n")
    return agent_file
```

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
uv run pytest tests/test_agent_generator.py -v

# Run tests matching pattern
uv run pytest -k "test_agent" -v

# Run with coverage
make coverage

# Run with verbose output
uv run pytest -vv

# Run with print statements visible
uv run pytest -s
```

## Documentation

### Documentation Standards

- **Update with code**: Documentation changes with code changes
- **Clear language**: Simple, concise, actionable
- **Code examples**: Include examples for complex features
- **Consistent formatting**: Follow existing documentation patterns

### Documentation Types

**Code Documentation:**
- Inline comments for complex logic
- Docstrings for functions/classes (Google-style)
- Type hints for all public APIs
- README files for major modules

**Component Documentation:**
- `AGENT.md` - Agent instructions and capabilities
- `COMMAND.md` - Command usage and examples
- `HOOK.md` - Hook triggers and validation logic
- `SKILL.md` - Skill description and bundled resources

**User Documentation:**
- `README.md` - Project overview and quick start
- `docs/onboarding.md` - Developer setup guide
- `docs/architecture.md` - System architecture
- `docs/troubleshooting.md` - Common issues and solutions

**Architecture Documentation:**
- Create ADRs for significant decisions
- Update architecture docs for major changes
- Keep diagrams current (Mermaid format)

## Community

### Communication Channels

- **GitHub Issues**: Bug reports, feature requests
- **GitHub Discussions**: General questions, ideas, community chat
- **Pull Requests**: Code review, collaboration

### Getting Help

- Check [onboarding.md](./onboarding.md) for setup issues
- Check [troubleshooting.md](./troubleshooting.md) for common problems
- Search [closed issues](https://github.com/mgiovani/cc-arsenal/issues?q=is%3Aissue+is%3Aclosed)
- Ask in [GitHub Discussions](https://github.com/mgiovani/cc-arsenal/discussions)
- Be patient and respectful when asking for help

### Recognition

Contributors are recognized in:
- [CONTRIBUTORS.md](../CONTRIBUTORS.md) file
- Release notes and changelogs
- Project README
- Special mentions for significant contributions

## License

By contributing to Claude Code Arsenal, you agree that your contributions will be licensed under the [MIT License](../LICENSE).

---

**Thank you for contributing to Claude Code Arsenal!**

For questions or clarifications, please open an issue or start a discussion.

*Last Updated: 2025-10-27*
