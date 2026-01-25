# Changelog

All notable changes to cc-arsenal will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **agent-browser Skill**: Browser automation skill with 93% less context overhead than Playwright MCP
  - Core SKILL.md with progressive disclosure design (<1.5k words)
  - Comprehensive command reference (commands.md, ~500 lines)
  - Practical workflow patterns (workflows.md, ~350 lines)
  - Advanced topics and Playwright comparison (advanced.md, ~400 lines)
  - Uses snapshot + refs system for AI-optimized element selection
  - Covers navigation, interaction, data extraction, authentication, debugging
  - Detailed Playwright MCP comparison table showing context overhead differences
- **Root Plugin Manifest**: Added `.claude-plugin/plugin.json` with complete metadata (name, version, description, author, homepage, repository, license, keywords)
- **Enhanced Marketplace Manifest**: Updated all plugin variants with consistent author metadata, keywords, and URLs for better discoverability
- **Plugin Variants Documentation**: Added comprehensive documentation in CLAUDE.md and README.md explaining the plugin variants pattern

### Fixed

- **Plugin Installation Issues**: Fixed multiple installation blockers:
  - Removed root `.venv/` directory (118MB) causing EACCES permission errors
  - Removed `scripts/.venv/` directory causing EACCES permission errors
  - Removed circular symlink `scripts/claude/statusline/statusline` causing ENOENT symlink errors
  - Deleted unsupported `.claudeignore` file (Claude Code doesn't support this feature)
- **Development Artifacts Cleanup**: Ensured development files (.venv, build artifacts, symlinks) are properly excluded from plugin distribution
- **Statusline Gitignore**: Allowed statusline lib directory to be tracked for proper plugin distribution

### Changed

- **Marketplace Metadata**: All 5 plugin variants now include complete author information (name, email, URL) and targeted keywords
- **Documentation Structure**: Enhanced installation instructions with clear plugin variant comparison tables
- **Hooks Architecture**: Refactored to consolidated `hooks/hooks.json` for better scalability
  - Moved from `hooks/diff-pane/hooks.json` to `hooks/hooks.json`
  - Centralized location supports multiple hook groups
  - Old location marked as deprecated but kept for reference
- **Plugin Architecture (2026 Best Practices)**: Aligned with current Claude Code standards
  - Root `plugin.json` contains only metadata (no component paths)
  - All component paths specified in `marketplace.json` variants
  - Complete variant now includes explicit `commands`, `skills`, and `hooks` fields
  - Enables proper selective installation per variant
- **Statusline Context Calculation**: Now uses Claude Code's `used_percentage` field directly when available
  - Eliminates manual percentage calculation
  - More accurate with server-provided data
  - Falls back to local calculation when field not available

## [1.2.0] - 2025-12-12

### Added

- **Selective Plugin Installation**: Multiple installable plugin sets from single marketplace
  - `cc-arsenal` - Complete toolkit (all commands and skills)
  - `cc-arsenal-docs` - Documentation commands only (ADR, RFC, diagrams)
  - `cc-arsenal-git` - Git workflow commands only (commits, PRs)
  - `cc-arsenal-skills` - Skills only (Jira CLI, skill creator)
- **Plugin Browser Integration**: `marketplace add` now opens interactive plugin selector
- **Resources Directory**: New `resources/templates/` for non-command assets

### Changed

- **Plugin Architecture**: Removed `plugin.json` in favor of marketplace-only configuration
  - All plugins now use `strict: false` with explicit component paths
  - Follows anthropics/skills pattern for better compatibility
- **Templates Location**: Moved from `commands/docs/templates/` to `resources/templates/`
  - Prevents templates from being discovered as commands
  - Cleaner separation of assets from executable commands
- **README Installation Instructions**: Simplified plugin installation flow
  - Single command opens interactive plugin browser
  - Table showing available plugin options
  - Warning about not installing complete + selective plugins together
- **Command Prefix**: Plugin commands now use `cc-arsenal:` prefix (e.g., `/cc-arsenal:docs:adr`)

### Fixed

- **Conflicting Manifests Error**: Resolved "both plugin.json and marketplace entry specify components" error
- **Duplicate Commands**: Fixed templates appearing as commands in plugin discovery
- **Template Path References**: Updated all 5 documentation commands to use `resources/templates/`
- **Plugin Cache Issues**: Documented cache clearing for troubleshooting stale installations

### Documentation

- Updated CLAUDE.md with selective install options
- Updated README with plugin browser workflow and options table
- Updated docs/architecture.md with new plugin installation steps
- Added note about avoiding duplicate installations

## [1.1.0] - 2025-12-12

### Added

- **Statusline Context Window Support**: Dynamic context size calculation from Claude Code's `context_window` JSON fields
  - Uses `context_window.context_window_size` for accurate percentage calculation (supports 200K and 1M contexts)
  - Prioritizes `context_window.total_input_tokens` and `context_window.total_output_tokens` over legacy fields
  - Fallback to 200K context size when not provided
- **Statusline Model Display Name**: Uses `model.display_name` directly when provided by Claude Code (e.g., "Opus", "Sonnet")
- **Statusline Context Window Tests**: Comprehensive test suite (`test_context_window.sh`) for the new context window feature
- **Documentation Plugin**: Comprehensive documentation generation and management system
  - 6 slash commands: `/docs:init`, `/docs:adr`, `/docs:rfc`, `/docs:diagram`, `/docs:check`, `/docs:update`
  - 12 templates for ADRs, RFCs, architecture, onboarding, data models, API docs, etc.
  - Zero-config with smart project detection and Git-aware freshness tracking
  - Mermaid diagram generation from codebase analysis (ER, architecture, deployment, security)
  - Health scoring and validation for documentation quality
- **Modular Makefile Architecture**: Feature-specific commands in dedicated Makefiles
  - `scripts/claude/statusline/Makefile`: 9 commands for statusline management
  - `scripts/claude-hi/Makefile`: 12 commands for session scheduler
  - Core Makefile delegates to feature Makefiles for clean organization
- **Plugin Validation**: `make validate-plugins` target for marketplace and plugin manifest validation
- **Meta-ADR**: ADR-0001 documenting the decision to use Architecture Decision Records
- **Selective Installation Guide**: Documentation for `make configure` to choose specific components
- **Architecture Documentation**: Comprehensive system design documentation in docs/architecture.md

### Changed

- **Statusline JSON Extraction**: Refactored to use DRY helpers (`grep_string`, `grep_number`) for cleaner fallback parsing
  - Cached jq availability check for performance
  - Better handling of nested JSON paths
- **Statusline Worktree Detection**: Fixed to extract worktree name from git-dir path instead of PWD basename
  - Now correctly identifies worktree name from `.git/worktrees/<name>` path structure
  - Added worktree detection to daemon (`statusline_daemon.sh`)
- **Makefile Simplification**: Core Makefile reduced from 300+ to 120 lines
  - Removed commands: `backup`, `restore`, `list-backups`, `uv-*`, `debug-install`, `show-structure`, `generate-agent`, `docs`, `quick-start`
  - Core workflows: dev, pre-commit, quality (lint/format/type-check), testing, installation, utilities
  - Use `make -C <feature-dir> help` to access feature-specific commands
- **Hook System Simplified**: Focused on essential security and quality validation
  - Kept: `file_protection.py` (sensitive file protection), `pre_commit_validate.py` (quality gates)
  - Removed: `auth_checker.py`, `audit_enforcer.py`, `migration_safety.py`
  - Extracted hook configuration to dedicated `hooks/hooks.json` file
  - Added explicit tool matchers, timeouts, and descriptions
- **Templates Relocated**: Moved from user config (`.claude/`) to plugin resources (`resources/templates/`)
- **Plugin Structure**: `plugin.json` moved to `.claude-plugin/` directory (required location)
- **Configure Script**: Now reads components from repository source instead of ~/.claude installation
  - Allows configuration before installation
  - Filters out README.md files from component lists
  - Added skills discovery support
- **CI Workflow**: Uses Makefile targets for consistency, pinned Python 3.13, switched to pyright

### Fixed

- **Statusline Git Tests**: Fixed branch name assertion to handle both "main" and "master" defaults
- **Statusline Git Tests**: Corrected truncation test expectation (12 chars, not 8) to match actual implementation
- **configure.py**: Now reads from repository source, enabling pre-installation configuration
- **create-pr command**: Reordered workflow, fixed hardcoded base branch, fixed body file reference
- **Plugin validation errors**: Corrected plugin.json location and command organization
- Template path references in all 5 documentation commands
- Line length issues in configure.py (90 char limit compliance)
- Indentation compliance with editorconfig (2-space multiples)

### Removed

- **Component README files**: Removed from `agents/`, `commands/`, `skills/`, `hooks/` directories
  - Claude Code was incorrectly loading them as components
  - Documentation moved to `docs/` directory instead
- **Specialized hooks**: `auth_checker`, `audit_enforcer`, `migration_safety` (simplified to core security/quality)
- **Outdated methodology references**: Cleaned up marketplace metadata and descriptions

### Documentation

- Added comprehensive installation methods (plugin system + direct installation)
- Updated all examples to use generic agent category references
- Added pre-commit hook best practice notes (never use `--no-verify`)
- Synchronized CLAUDE.md, README.md, and architecture.md with new structure
- Updated troubleshooting examples to reference actual files
- Documented changes and migration paths

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
- Security hook: file protection for sensitive data

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

[Unreleased]: https://github.com/mgiovani/cc-arsenal/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/mgiovani/cc-arsenal/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/mgiovani/cc-arsenal/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/mgiovani/cc-arsenal/releases/tag/v1.0.0
