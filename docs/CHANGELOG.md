# Changelog

All notable changes to cc-arsenal will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Nothing yet.

## [1.0.0] - 2025-10-21

### Added

**Statusline**
- Real-time usage tracking showing model, costs, and context usage
- Git integration with branch, uncommitted changes, and worktree detection
- Session tracking with duration and lines changed
- 5-hour window reset countdown with precise timing
- Background daemon for instant updates (<1ms response time)
- Comprehensive configuration tool for customization

**Claude Hi Scheduler**
- Automatic 5-hour window triggering at optimal times
- Multiple preset schedules (standard, extended, early bird, night owl)
- Custom schedule builder with interactive setup
- Smart fallback mechanisms for reliability
- Integration with statusline for window tracking

**Agents**
- Architecture agents for system design and technical planning
- Development agents for code implementation and debugging
- Orchestration agents for workflow coordination
- Product agents for requirements and planning
- Productivity agents for development optimization
- UX agents for user experience and design

**Commands**
- `/git:commit` - Generate conventional commits with smart message creation
- `/git:create-pr` - Create pull requests with pre-filled templates
- Security scanning and quality check commands
- Test automation and execution commands

**Skills**
- `skill-creator` - Guide for creating effective skills with templates
- `jira-cli` - Interactive Jira command-line tool integration
- Skill packaging and validation utilities

**Hooks**
- Security hooks: authentication validation, file protection
- Quality hooks: pre-commit validation, code standards
- Compliance hooks: audit enforcement, migration safety
- Project-specific hooks for domain validation

**Documentation**
- Comprehensive installation and setup guides
- Component-specific documentation (statusline, Claude Hi, agents)
- Agent development guide with best practices
- Troubleshooting guide for common issues
- Security policy and vulnerability reporting process
- Contributing guidelines with code of conduct

**Infrastructure**
- Python 3.12+ with UV package management
- Rich CLI interfaces with progress indicators
- Pydantic models for configuration validation
- Comprehensive test suite (13 tests)
- GitHub Actions CI/CD pipeline
- Pre-commit hooks for code quality
- Symlink-based installation architecture

### Security

- No hardcoded credentials or sensitive data
- Secure file protection hooks
- Authentication pattern validation
- Audit trail enforcement
- Clean git history with sensitive data removed

### Developer Experience

- One-command installation via plugin marketplace
- Alternative manual installation via make
- Interactive configuration tools
- Self-healing daemon that auto-restarts
- Comprehensive error handling and validation
- Extensive examples and documentation

---

## Version History

[Unreleased]: https://github.com/mgiovani/cc-arsenal/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/mgiovani/cc-arsenal/releases/tag/v1.0.0
