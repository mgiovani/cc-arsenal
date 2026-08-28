# Contributing to Claude Code Arsenal

We welcome contributions! Please follow these guidelines to ensure a smooth contribution process.

## Quick Start for contributors

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Develop** your changes with tests and documentation
4. **Validate** with our quality checks: `make check`
5. **Submit** a pull request with detailed description

## Development setup

### Prerequisites

- **Python 3.12+** (for modern language features and performance)
- **UV** (for fast Python package management) - **REQUIRED**
  - Install: `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - Docs: https://docs.astral.sh/uv/getting-started/installation/
- **Claude Code** (Anthropic's official Claude CLI)

### Setting up your development environment

```bash
# Clone your fork
git clone https://github.com/your-username/cc-arsenal.git
cd cc-arsenal

# Set up development environment (installs dev dependencies)
make dev

# Install pre-commit hooks for automatic code quality
make pre-commit-install
```

## Development workflow

### Code quality checks

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

### Quality standards

All contributions must meet these standards:

- **Python 3.12+** with modern language features
- **Type hints** for all functions and classes
- **Comprehensive tests** with >90% coverage
- **Rich CLI interfaces** with progress indicators and error handling
- **Detailed documentation** with examples and troubleshooting
- **Security-first** approach with input validation and error handling

## Contributing different types of components

CC-Arsenal's only component type is the **skill** (45 currently, see [docs/features.md](docs/features.md) for the full, categorized list). Every workflow, whether user-invoked (a slash command like `/git-commit`) or model-invoked (auto-loaded like `review-code`), is a skill under `skills/<name>/SKILL.md`.

### Creating new skills

Skills are modular capabilities Claude loads via progressive disclosure. To create a new skill, use the create-skill skill for guidance:

```bash
# The create-skill provides specification-driven creation with live documentation fetching
# See skills/create-skill/SKILL.md for detailed instructions
```

Each skill should have a `SKILL.md` file with YAML frontmatter:

```yaml
---
name: "skill-name"
description: "Skill description"
disable-model-invocation: true  # false/omit for a model-invoked (auto-loading) skill
---

# Skill implementation with progressive disclosure...
```

Skills can bundle `scripts/`, `references/`, and `assets/` in subdirectories. Add `evals/evals.json` (task assertions) and `evals/trigger-eval.json` (trigger/near-miss queries) so the skill's behavior and triggering are testable: see any existing skill's `evals/` directory for the schema.

After creating a skill, add its path to the relevant plugin(s) in `.claude-plugin/marketplace.json` and add its entry to `docs/features.md`.

## Code style guidelines

### Python code style

- Follow PEP 8 with 90-character line length
- Use type hints for all functions and parameters
- Use single quotes for strings (configured in ruff)
- Follow Google-style docstrings
- Use meaningful variable and function names

### Markdown documentation

- Use clear, descriptive headings
- Include code examples with proper syntax highlighting
- Provide both basic and advanced usage examples
- Include troubleshooting sections where appropriate

## Testing guidelines

### Writing tests

- Write tests for all new functionality
- Aim for >90% code coverage
- Use pytest fixtures for common test setup
- Test both success and failure scenarios
- Include integration tests for complex workflows

### Running tests

```bash
# Run all tests
make test

# Run tests with coverage
make coverage

# Run specific test file
uv run pytest scripts/tests/test_install.py

# Run tests with verbose output
uv run pytest -v
```

## Documentation standards

### README updates

When adding new features:
- Update the main README.md with usage examples
- Add appropriate sections to the feature overview
- Include installation notes if required

### Inline documentation

- Add docstrings to all public functions and classes
- Include parameter types and return value descriptions
- Provide usage examples in docstrings for complex functions

## Security considerations

### Security-First development

All code must follow security best practices:

- **Input Validation**: Validate all user inputs
- **No Hardcoded Secrets**: Use environment variables for sensitive data
- **Dependency Security**: Keep dependencies updated and scan for vulnerabilities
- **Error Handling**: Don't expose sensitive information in error messages

### Security review process

Security-related changes require additional review:
- Security hooks and authentication components
- File system operations and path handling
- External API integrations
- Dependency updates

## Pull request guidelines

### PR description template

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

### Review process

1. **Automated Checks**: All CI checks must pass
2. **Code Review**: At least one maintainer review required
3. **Testing**: Verify tests cover new functionality
4. **Documentation**: Ensure documentation is updated

## Release process

### Versioning

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release checklist

- [ ] Version number updated in `pyproject.toml`
- [ ] CHANGELOG.md updated with release notes
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Security review completed (if applicable)

## Getting help

### Communication channels

- **Issues**: [GitHub Issues](https://github.com/mgiovani/cc-arsenal/issues) for bugs and feature requests
- **Discussions**: [GitHub Discussions](https://github.com/mgiovani/cc-arsenal/discussions) for questions and ideas
- **Email**: For security issues, contact e@giovani.dev

### Common issues

- **Installation Problems**: Check UV installation and Python version
- **Test Failures**: Ensure all dependencies are installed with `make dev`
- **Style Issues**: Run `make format` and `make lint`

## Code of Conduct

### Our standards

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

### Enforcement

Instances of unacceptable behavior may be reported to e@giovani.dev. All complaints will be reviewed and investigated promptly and fairly.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
