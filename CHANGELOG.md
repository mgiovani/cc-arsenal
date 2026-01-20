# Changelog

All notable changes to Claude Code Arsenal will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Git Diff Pane Hook**: Zero-token-cost hook that automatically opens a tmux side pane showing `git diff` whenever files are modified
  - Triggers on `Edit`, `Write`, and `NotebookEdit` tool usage via PostToolUse hook
  - Automatically creates and manages a dedicated tmux pane for git diff output
  - Supports multiple diff tools: `delta` (preferred), `diff-so-fancy`, or standard `git diff`
  - Configuration via environment variables:
    - `CLAUDE_DIFF_PANE_WIDTH`: Pane width percentage (default: 40)
    - `CLAUDE_DIFF_PANE_POSITION`: Pane position - left or right (default: right)
    - `CLAUDE_DIFF_STAGED_ONLY`: Show only staged changes (default: false)
    - `CLAUDE_DIFF_TOOL`: Diff tool selection - delta, diff-so-fancy, or git (default: auto)
  - Installed automatically via plugin system (no manual installation needed)
  - Integrated into cc-arsenal plugin via `hooks.json`
  - Development Makefile targets: `test-diff-pane`, `status-diff-pane`

## [1.2.0] - 2024-01-09

### Added

- Initial plugin marketplace support
- Complete toolkit plugin with all commands and skills
- Specialized plugin bundles (dev, docs, git, skills)

## [1.1.0] - Previous Release

### Added

- Development commands (implement-feature)
- Documentation commands (ADR, RFC, diagrams, init, check, update)
- Git workflow commands (commit, create-pr)
- Claude utilities (create-command, create-rule)
- Jira integration (todo, daily)
- Skills: skill-creator, jira-cli
- Installation and configuration scripts
- Pre-commit hooks integration
- Comprehensive testing suite

[Unreleased]: https://github.com/mgiovani/cc-arsenal/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/mgiovani/cc-arsenal/releases/tag/v1.2.0
[1.1.0]: https://github.com/mgiovani/cc-arsenal/releases/tag/v1.1.0
