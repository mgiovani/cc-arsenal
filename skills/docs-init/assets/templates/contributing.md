# Contributing to {{PROJECT_NAME}}

Thank you for your interest in contributing to {{PROJECT_NAME}}! This document provides guidelines and instructions for contributing.

## Table of contents

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

We are committed to providing a welcoming and inspiring community for all. Please read and follow our Code of Conduct.

**Expected Behavior:**
- Be respectful and inclusive
- Exercise empathy and kindness
- Give and gracefully accept constructive feedback
- Focus on what is best for the community

**Unacceptable Behavior:**
- Harassment, discrimination, or offensive comments
- Trolling, insulting, or derogatory comments
- Public or private harassment
- Publishing others' private information
- Other conduct which could reasonably be considered inappropriate

## Getting started

### Prerequisites

Before you begin, ensure you have:
- {{PREREQUISITES}}
- Git for version control
- Access to the project repository

### Development setup

See [onboarding.md](./onboarding.md) for detailed setup instructions.

Quick start:
```bash
# Clone the repository
git clone {{REPOSITORY_URL}}
cd {{PROJECT_NAME}}

# Install dependencies
{{INSTALL_COMMAND}}

# Run tests
{{TEST_COMMAND}}

# Start development server
{{DEV_COMMAND}}
```

## How to contribute

### Reporting bugs

Before creating a bug report:
1. Check existing issues to avoid duplicates
2. Use the latest version to verify the bug still exists
3. Collect information about your environment

When reporting a bug, include:
- **Description**: Clear description of the issue
- **Steps to Reproduce**: Step-by-step instructions
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Environment**: OS, version, browser, etc.
- **Screenshots**: If applicable

### Suggesting enhancements

Enhancement suggestions are welcome! Include:
- **Use Case**: Why is this enhancement needed?
- **Proposed Solution**: How should it work?
- **Alternatives**: What other solutions were considered?
- **Impact**: Who will benefit from this enhancement?

### Contributing code

1. **Fork the Repository**
   ```bash
   # Fork via GitHub UI, then:
   git clone your-fork-url
   cd {{PROJECT_NAME}}
   git remote add upstream original-repo-url
   ```

2. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bugfix-name
   ```

3. **Make Your Changes**
   - Write clean, readable code
   - Follow coding standards
   - Add tests for new functionality
   - Update documentation as needed

4. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "type(scope): description"
   ```

   Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation only
   - `style:` - Code style changes
   - `refactor:` - Code refactoring
   - `test:` - Adding tests
   - `chore:` - Maintenance tasks

5. **Push and Create Pull Request**
   ```bash
   git push origin your-branch-name
   # Create PR via GitHub UI
   ```

## Pull request process

### Before submitting

- [ ] Code follows project coding standards
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Documentation updated
- [ ] Commit messages follow conventions
- [ ] Branch is up to date with main

### PR guidelines

**Title Format:**
```
type(scope): Brief description
```

**Description Should Include:**
- Summary of changes
- Related issue numbers (Fixes #123)
- Breaking changes (if any)
- Screenshots (for UI changes)

**Review Process:**
1. Automated checks run (CI/CD)
2. Code review by maintainers
3. Address feedback
4. Approval and merge

### After your PR is merged

- Delete your feature branch
- Update your local repository
- Celebrate! 🎉

## Coding standards

### General principles

- **DRY**: Don't Repeat Yourself
- **KISS**: Keep It Simple, Stupid
- **YAGNI**: You Aren't Gonna Need It
- **SOLID**: Follow SOLID principles

### Code style

{{LANGUAGE_SPECIFIC_STYLE}}

**Naming Conventions:**
- Variables: `camelCase` or `snake_case`
- Functions: `camelCase` or `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Files: Descriptive, lowercase

**Comments:**
- Write self-documenting code
- Add comments for complex logic
- Use JSDoc/docstrings for functions
- Keep comments up to date

**File Organization:**
```
{{FILE_STRUCTURE}}
```

## Testing guidelines

### Test requirements

- Unit tests for all new functions/methods
- Integration tests for new features
- E2E tests for critical user flows
- Maintain or improve test coverage

### Writing tests

```{{LANGUAGE}}
# Example test structure
describe('Feature', () => {
  it('should behave correctly', () => {
    // Arrange
    const input = setupInput();

    // Act
    const result = performAction(input);

    // Assert
    expect(result).toBe(expected);
  });
});
```

### Running tests

```bash
# Run all tests
{{TEST_COMMAND}}

# Run specific test file
{{TEST_FILE_COMMAND}}

# Run with coverage
{{COVERAGE_COMMAND}}
```

## Documentation

### Documentation standards

- Update docs with code changes
- Use clear, concise language
- Include code examples
- Keep formatting consistent

### Documentation types

**Code Documentation:**
- Inline comments for complex logic
- Function/method documentation
- README files for modules

**User Documentation:**
- Feature guides
- API documentation
- Tutorials and examples

**Architecture Documentation:**
- Create ADRs for significant decisions
- Update architecture docs
- Keep diagrams current

## Community

### Communication channels

- **GitHub Issues**: Bug reports, feature requests
- **Discussions**: General questions, ideas
- **Pull Requests**: Code review, collaboration

### Getting help

- Check existing documentation
- Search closed issues
- Ask in discussions
- Be patient and respectful

### Recognition

Contributors are recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project README

## License

By contributing to {{PROJECT_NAME}}, you agree that your contributions will be licensed under the project's license.

---

**Thank you for contributing to {{PROJECT_NAME}}!**

For questions or clarifications, please open an issue or discussion.

*Last Updated: {{DATE}}*
