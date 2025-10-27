---
description: "Generate conventional commits following conventionalcommits.org specification"
argument-hint: ""
allowed-tools: ["Bash(git *)", "Read", "Edit", "Write"]
---

# Conventional Commit Command

Generate a conventional commit message following https://www.conventionalcommits.org/en/v1.0.0/ specification and create commits automatically.

## Your Task

1. **Analyze Changes**: Run `git status` and `git diff --staged` to understand current changes
2. **Group Related Changes**: Identify logically separate changes that should be committed individually (e.g., separate feature additions from bug fixes, documentation updates from code changes)
3. **For Each Logical Group**:
  - Determine the appropriate commit type:
    - `feat`: New feature for the user
    - `fix`: Bug fix for the user
    - `docs`: Documentation only changes
    - `style`: Code style changes (formatting, missing semi-colons, etc.)
    - `refactor`: Code change that neither fixes a bug nor adds a feature
    - `perf`: Performance improvements
    - `test`: Adding missing tests or correcting existing tests
    - `build`: Changes to build system or external dependencies
    - `ci`: Changes to CI configuration files and scripts
    - `chore`: Other changes that don't modify src or test files
    - `revert`: Reverts a previous commit
  - Identify the scope if applicable (component, module, or area affected)
  - Write a concise description in imperative mood (max 50 characters)
  - Add a detailed body if the change is complex (wrap at 72 characters)
  - Include breaking change footer if applicable: `BREAKING CHANGE: description`
  - Format as: `type(scope): description`

4. **Commit Strategy**:
  - If changes represent a single logical unit: create one commit
  - If changes span multiple concerns: create separate commits for each logical group
  - Stage files appropriately for each commit using `git add`
  - Create each commit with the generated message

## Example Formats

```
feat(auth): add OAuth2 login support
fix(api): resolve null pointer in user endpoint
docs: update installation instructions
chore(deps): bump lodash to 4.17.21
refactor(parser): extract validation logic to separate module

feat(shopping-cart)!: remove deprecated calculate() method

BREAKING CHANGE: calculate() has been removed, use computeTotal() instead
```

## Important Notes

- **Multiple Commits**: If you identify different types of changes (e.g., feat + fix + docs), create separate commits for each type
- **Staging**: Use `git add <specific-files>` to stage only relevant files for each commit
- **Imperative Mood**: Use "add" not "added", "fix" not "fixed"
- **Breaking Changes**: Append an exclamation mark after type/scope and add a `BREAKING CHANGE:` footer
- **Scope**: Optional but recommended for clarity (e.g., component name, module name)
- **Body**: Use for complex changes to explain the "what" and "why", not "how"
- **Pre-commit Hooks**: NEVER use `--no-verify` to skip pre-commit hooks - it's a bad practice that bypasses important quality gates

Generate the most appropriate commit message(s) based on the changes and commit automatically. Ask for confirmation before committing if the changes are complex or span multiple concerns.
