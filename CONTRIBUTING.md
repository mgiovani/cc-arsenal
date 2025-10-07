# Contributing to Claude Code Arsenal

We welcome contributions! Please follow these guidelines to ensure a smooth contribution process.

## Quick Start for Contributors

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Develop** your changes with tests and documentation
4. **Validate** with our quality checks: `make check`
5. **Submit** a pull request with detailed description

## Development Setup

### Prerequisites

- **Python 3.12+** (for modern language features and performance)
- **UV** (for fast Python package management) - **REQUIRED**
  - Install: `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - Docs: https://docs.astral.sh/uv/getting-started/installation/
- **Claude Code** (Anthropic's official Claude CLI)

### Setting Up Your Development Environment

```bash
# Clone your fork
git clone https://github.com/your-username/cc-arsenal.git
cd cc-arsenal

# Set up development environment (installs dev dependencies)
make dev

# Install pre-commit hooks for automatic code quality
make pre-commit-install
```

## Development Workflow

### Code Quality Checks

Before submitting any changes, ensure your code passes all quality checks:

```bash
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
```

### Quality Standards

All contributions must meet these standards:

- **Python 3.12+** with modern language features
- **Type hints** for all functions and classes
- **Comprehensive tests** with >90% coverage
- **Rich CLI interfaces** with progress indicators and error handling
- **Detailed documentation** with examples and troubleshooting
- **Security-first** approach with input validation and error handling

## Contributing Different Types of Components

### Creating New Agents

Generate a new agent using the built-in generator:

```bash
# Generate a new security agent
make generate-agent NAME=crypto-validator CATEGORY=security

# Generate using Python module directly
uv run python -m scripts.generators.agent_generator --name "agent-name" --category "development"
```

Each agent should be a `.md` file with YAML frontmatter:

```yaml
---
name: "agent-name"
description: "Agent description"
capabilities: ["capability1", "capability2"]
tools: ["Tool1", "Tool2"]
---

# Agent implementation...
```

### Creating New Commands

Commands should be placed in the appropriate category under `commands/`:

```yaml
---
description: "Command description"
argument-hint: "<argument_format>"
allowed-tools: ["Tool1", "Tool2"]
---

# Command implementation...
```

### Creating New Hooks

Hooks are Python scripts that receive JSON input via stdin and return JSON responses:

```python
#!/usr/bin/env python3
import sys
import json

def main():
    event_data = json.loads(sys.stdin.read())
    # Hook logic here
    result = {"allowed": True, "message": "OK"}
    print(json.dumps(result))
    sys.exit(0 if result["allowed"] else 1)

if __name__ == "__main__":
    main()
```

## Code Style Guidelines

### Python Code Style

- Follow PEP 8 with 90-character line length
- Use type hints for all functions and parameters
- Use single quotes for strings (configured in ruff)
- Follow Google-style docstrings
- Use meaningful variable and function names

### Markdown Documentation

- Use clear, descriptive headings
- Include code examples with proper syntax highlighting
- Provide both basic and advanced usage examples
- Include troubleshooting sections where appropriate

## Testing Guidelines

### Writing Tests

- Write tests for all new functionality
- Aim for >90% code coverage
- Use pytest fixtures for common test setup
- Test both success and failure scenarios
- Include integration tests for complex workflows

### Running Tests

```bash
# Run all tests
make test

# Run tests with coverage
make coverage

# Run specific test file
uv run pytest tests/test_specific.py

# Run tests with verbose output
uv run pytest -v
```

## Documentation Standards

### README Updates

When adding new features:
- Update the main README.md with usage examples
- Add appropriate sections to the feature overview
- Include installation notes if required

### Inline Documentation

- Add docstrings to all public functions and classes
- Include parameter types and return value descriptions
- Provide usage examples in docstrings for complex functions

## Security Considerations

### Security-First Development

All code must follow security best practices:

- **Input Validation**: Validate all user inputs
- **No Hardcoded Secrets**: Use environment variables for sensitive data
- **Dependency Security**: Keep dependencies updated and scan for vulnerabilities
- **Error Handling**: Don't expose sensitive information in error messages

### Security Review Process

Security-related changes require additional review:
- Security hooks and authentication components
- File system operations and path handling
- External API integrations
- Dependency updates

## Pull Request Guidelines

### PR Description Template

```markdown
## Summary
Brief description of the changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or properly documented)
```

### Review Process

1. **Automated Checks**: All CI checks must pass
2. **Code Review**: At least one maintainer review required
3. **Testing**: Verify tests cover new functionality
4. **Documentation**: Ensure documentation is updated

## Release Process

### Versioning

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

- [ ] Version number updated in `pyproject.toml`
- [ ] CHANGELOG.md updated with release notes
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Security review completed (if applicable)

## Getting Help

### Communication Channels

- **Issues**: [GitHub Issues](https://github.com/mgiovani/cc-arsenal/issues) for bugs and feature requests
- **Discussions**: [GitHub Discussions](https://github.com/mgiovani/cc-arsenal/discussions) for questions and ideas
- **Email**: For security issues, contact e@giovani.dev

### Common Issues

- **Installation Problems**: Check UV installation and Python version
- **Test Failures**: Ensure all dependencies are installed with `make dev`
- **Style Issues**: Run `make format` and `make lint`

## Code of Conduct

### Our Standards

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

### Enforcement

Instances of unacceptable behavior may be reported to e@giovani.dev. All complaints will be reviewed and investigated promptly and fairly.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
