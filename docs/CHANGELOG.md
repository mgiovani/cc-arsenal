# Changelog

All notable changes to cc-arsenal will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.1.0] - 2026-02-13

### Added

- **Cross-platform skills**: 22 base skills available via [mgiovani/skills](https://github.com/mgiovani/skills) repository
  - Install with `npx skills add mgiovani/skills` for use across any AI agent platform
  - Works with Claude Code, Cursor, Windsurf, and 30+ other AI agents
  - Published to [skills.sh](https://skills.sh) marketplace for easy discovery
- **Sync workflow**: `make sync-skills` command to keep skills synchronized with base repository
  - Automated merge of base skills with Claude Code enhancements
  - Status tracking with `make sync-skills-status`
  - Submodule auto-initialization in installation flow
- **Enhancement system**: Claude Code-specific features layered on top of base skills
  - 25 enhancement files in `enhancements/` directory
  - Subagent orchestration, Task Management System integration, hooks
  - Preserved all Claude Code optimizations while enabling cross-platform distribution

### Changed

- **Architecture**: Dual-repository model with `skills-upstream/` submodule
  - Base skills maintained in separate repository for cross-platform use
  - Enhanced skills in cc-arsenal add Claude Code-specific features
  - Automated sync keeps both aligned
- **Installation**: Git submodule initialization automatic during `make install`
- **Plugin variants**: All marketplace plugins updated to v3.1.0

### Technical Details

- **Submodule**: `skills-upstream/` points to [mgiovani/skills](https://github.com/mgiovani/skills)
- **Sync script**: `scripts/sync_skills.py` handles merging and SYNC.md metadata
- **Skill count**: 22 cross-platform base skills + 10 Claude Code-exclusive skills = 32 total

## [2.3.0] - 2026-02-05

### Added

- **team-implement**: Spec-driven team orchestration skill — adaptive development team that scales from 3 agents (lite) to 11 agents (full) based on project complexity
  - **Multi-source input**: Accepts plain text, Jira tickets (`PROJ-123`), GitHub issues (`#42`), PRs (`!123`), files, directories, or URLs
  - **Adaptive complexity**: Automatic scoring matrix evaluates 6 signals to recommend lite (Task subagents) or full (Teammate API) mode
  - **Namespaced specs**: Each invocation creates `.specs/<short-id>/` with proposal, design, review, tasks, and decisions artifacts
  - **Two macro phases**: Complete planning (Phases 0-5) with user approval gate before any code changes (Phases 6-9)
  - **11 specialized agent roles**: Product Manager, Scrum Master, Architect (opus), Frontend Dev, Backend Dev, QA Engineer, Security Engineer, Performance Engineer, Infrastructure/DevOps, Tech Writer, Adversary Reviewer
  - **3 lite-mode combined roles**: Product Analyst, Architect/Developer, QA/Reviewer
  - **Wave-based spawning**: Agents spawn per phase and shut down when done to minimize cost
  - **Adversarial review**: Dedicated review phases with BLOCKER/WARNING/SUGGESTION ratings and max 2 revision cycles
  - **Quality gates**: 6 gates between phases (clarifying questions, spec review, adversarial review, user approval, quality verification, final delivery)
  - **Spec-only mode**: Users can save planning artifacts without implementing
  - **Reference documentation**: agent-catalog.md, spec-workflow.md, communication-patterns.md, spec-templates.md
- **cc-arsenal-teams**: New plugin variant for team orchestration skills
- Marketplace version bumped to 2.3.0 (22 skills total)

## [2.2.0] - 2026-02-04

### Added

- **Quality Gates with Hooks**: Automated code quality verification before critical operations
  - **git-commit**: PreToolUse hook runs linter before creating commits
    - Supports Node.js (npm/bun/pnpm/yarn), Python (ruff/flake8), Ruby (rubocop), Go (golangci-lint)
    - Blocks commits if linting fails, allows if passes or no linter configured
    - Hook script: `skills/git-commit/scripts/pre-commit-lint.sh` (60s timeout)
    - Auto-detects project type and runs appropriate linter
  - **implement-feature**: Stop hook verifies implementation completeness before finishing
    - Runs tests, linting, and type-checking using commands discovered in Phase 0
    - Blocks completion if any check fails, provides clear error details
    - Agent-based hook (180s timeout) for multi-step verification
    - Enforces test-driven development discipline
  - **fix-bug**: Stop hook ensures bug is actually fixed before completion
    - Verifies originally failing test now passes
    - Runs full regression suite to catch new bugs
    - Validates root cause was addressed, not just symptoms
    - Agent-based hook (120s timeout) for comprehensive verification
  - **git-create-pr**: PreToolUse hook runs test suite before creating PR
    - Supports Node.js, Python, Go, Rust test runners
    - Blocks PR creation if tests fail, prevents broken CI builds
    - Hook script: `skills/git-create-pr/scripts/pre-pr-check.sh` (120s timeout)
    - Skips placeholder test scripts ("no test specified")
  - **agent-browser**: Stop hook automatically closes browser sessions
    - Prevents resource leaks from open browser processes
    - Command hook with `once: true` (10s timeout)
    - Runs `agent-browser close` on completion, ignores errors

- **Context Optimization with Fork**: Isolated execution for verbose operations
  - **10 skills now use `context: fork`** for clean main conversation:
    - `review-security`: Security scans isolated, only findings summary returned
    - `docs-check`: Documentation validation isolated, only health report returned
    - `docs-diagram`: Diagram generation isolated, only final diagram returned
    - `docs-adr`: ADR creation isolated, only completed ADR returned
    - `docs-rfc`: RFC creation isolated, only completed RFC returned
    - `docs-init`: Documentation setup isolated, only summary returned
    - `docs-update`: Documentation sync isolated, only update summary returned
    - `jira-daily`: Jira CLI output isolated, only standup report returned
    - `jira-todo`: Jira CLI output isolated, only task list returned
    - `project-planner`: Project analysis isolated, only plan/diagram returned
  - **All forked skills use `agent: general-purpose`** for complex reasoning
    - Changed from `agent: Explore` (Haiku 4.5) to `general-purpose` (Sonnet)
    - Necessary for security analysis, documentation writing, and complex planning
    - Explore agent only for simple read-only codebase navigation

### Changed

- **Hook Scripts**: Added two reusable quality gate scripts
  - `skills/git-commit/scripts/pre-commit-lint.sh`: Multi-language linter detection and execution
  - `skills/git-create-pr/scripts/pre-pr-check.sh`: Multi-language test runner detection and execution

- **Skill Frontmatter**: Updated 13 skills with new Claude Code v2.1.0+ frontmatter features
  - 5 skills with hooks: git-commit, implement-feature, fix-bug, git-create-pr, agent-browser
  - 10 skills with context: fork for isolated execution
  - All forked skills specify agent: general-purpose for Sonnet-powered reasoning

- **Quality Documentation**: Added "Quality Gates" sections to relevant skills
  - git-commit/SKILL.md: Documented pre-commit linting behavior, supported languages
  - implement-feature/SKILL.md: Documented completion verification, example blocked output
  - fix-bug/SKILL.md: Documented fix verification, regression checking

### Technical Details

- **Hook Types Used**:
  - Command hooks: `pre-commit-lint.sh`, `pre-pr-check.sh`, `agent-browser close`
  - Agent hooks: `implement-feature` Stop hook, `fix-bug` Stop hook
  - Both types return JSON decisions for allow/deny/block
- **Context Fork Benefits**:
  - Reduces main conversation context overhead by ~70-90%
  - Keeps verbose tool output (grep, CLI commands) isolated
  - Returns only user-relevant summaries to main conversation
- **Agent Selection Rationale**:
  - `general-purpose` (Sonnet): For all forked skills requiring reasoning
  - `Explore` (Haiku): Reserved for future simple read-only exploration

## [2.1.0] - 2026-02-03

### Added

- **Auto-Invocation Support**: `implement-feature` and `fix-bug` now support model invocation for automatic workflow activation
  - Changed `disable-model-invocation: false` to allow Claude to detect relevant context automatically
  - Updated descriptions to be context-detection friendly ("Automatically activates when users want to...")
  - No confirmation dialog - users can naturally say "let's implement X" or "fix this bug"
  - Users can abort with natural language ("wait, stop" or "no, don't do that") if auto-detection triggers inappropriately
  - Still works with explicit `/implement-feature` or `/fix-bug` commands
  - Skill distribution: 15 user-invoked (explicit `/` commands), 6 model-invoked (context-aware)

- **Task Management System Integration**: Migrated `implement-feature` and `fix-bug` skills from `TodoWrite` to Claude Code v2.1.16's new Task Management System
  - **TaskCreate, TaskUpdate, TaskList, TaskGet** tools replace TodoWrite for dependency-aware task tracking
  - **implement-feature**: 6-phase workflow with strict sequential dependencies (Discovery → Research → Planning → Implementation → Verification → Commit)
  - **fix-bug**: 6-phase workflow with strict sequential chain enforcing test-driven development discipline
  - **Model Selection Strategy**: Haiku for token-efficient discovery/research/analysis agents, Sonnet (default) for code implementation
  - **Parallel task support** in implement-feature Phase 3 for independent subagent work (API, UI, tests)
  - **Progress visualization** using `TaskList` after each phase completion
  - **Dependency patterns**: Sequential chains, parallel with convergence, blocking relationships with `addBlockedBy`
  - **Task metadata tracking**: Subagent ownership, component types, parent-child relationships, blocker reasons

- **project-planner Skill**: New skill for breaking down large projects into dependency-aware tasks (21 total skills now)
  - **5-phase workflow**: Project Analysis → Task Breakdown → Dependency Mapping → Visualization → Progress Tracking
  - **Mermaid diagram generation**: Visual dependency graphs showing critical paths and parallel work
  - **Task templates** for common project types (Web Feature, API Development, Database Migration, Refactoring, Authentication System)
  - **Multi-phase projects**: Support for epics and milestones with metadata hierarchies
  - **Risk assessment**: High-risk task identification with metadata tracking
  - **Resource allocation**: Team ownership and time estimation support
  - **Progressive disclosure**: SKILL.md + `references/task-patterns.md` (12 patterns) + `references/dependency-examples.md` (6 complex scenarios)
  - Added to `cc-arsenal` (full) and `cc-arsenal-dev` plugin variants

- **Task Management Best Practices Guide**: Comprehensive reference for `implement-feature` skill
  - `skills/implement-feature/references/task-best-practices.md` (400+ lines)
  - When to use tasks vs simple execution (granularity guidelines)
  - Dependency patterns: Sequential chain, parallel with convergence, diamond pattern
  - Handling task failures: Test failures, external blockers, changing requirements
  - Resuming sessions with existing tasks using `TaskList` and `TaskGet`
  - Progress visualization patterns and metadata enrichment strategies
  - Common antipatterns and comprehensive checklist

### Changed

- **implement-feature Skill**: Replaced TodoWrite with Task Management System
  - Updated `allowed-tools`: Removed `TodoWrite`, added `TaskCreate, TaskUpdate, TaskList, TaskGet`
  - Added "Task Management" section explaining when to use tasks vs simple execution
  - Phase 0 now creates complete task structure with 6 tasks and dependencies upfront
  - Each phase includes explicit task status updates (`in_progress` → `completed`)
  - Phase 3 demonstrates parallel subagent task tracking with metadata
  - Added Haiku model specification for discovery/research agents (Phases 0-1)
  - All phases end with `TaskList` call to show progress

- **fix-bug Skill**: Replaced TodoWrite with strict sequential task chain
  - Updated `allowed-tools`: Removed `TodoWrite`, added `TaskCreate, TaskUpdate, TaskList, TaskGet`
  - Added "Task Management" section emphasizing strict sequential dependencies
  - Phase 0 creates 6 tasks with strict chain (each blocked by previous)
  - Root cause analysis agents (Phase 1) use Haiku model for token efficiency
  - Task chain enforces test-driven development (cannot skip phases)
  - Updated `references/examples.md` with task tracking examples and quality checklist
  - Added task chain setup example and phase progression pattern

- **Plugin Manifests**: Bumped all plugin versions to 2.1.0
  - `cc-arsenal`: Updated description to "21 skills" (from 20)
  - `cc-arsenal-dev`: Added `./skills/project-planner/` to skills list
  - All variant plugins (`cc-arsenal-docs`, `cc-arsenal-git`, `cc-arsenal-skills`) updated to 2.1.0

- **Argument Syntax Documentation**: Updated to recommend `$N` shorthand over `$ARGUMENTS[N]`
  - `skills/create-command/references/frontmatter-guide.md`: Reordered variable table to promote `$0, $1, $2...` shorthand, marked `$ARGUMENTS[N]` as legacy syntax
  - `skills/create-command/references/design-patterns.md`: Updated example from `$ARGUMENTS` to `$0` for single argument access
  - `skills/skill-creator/SKILL.md`: Updated variable reference order to `$0, $1, $ARGUMENTS for all args`
  - `skills/create-command/SKILL.md`: Updated variable reference order to match recommended syntax
  - Claude Code v2.1.19 introduced cleaner `$N` shorthand for indexed argument access

### Technical Details

- **Task Lifecycle**: `pending` → `in_progress` → `completed` (or `deleted` for removal)
- **Dependency Enforcement**: Tasks with `blockedBy` cannot start until dependencies complete
- **Metadata Usage**: Track subagent ownership, component types, parent tasks, risk levels, time estimates
- **Model Selection**: `model: "haiku"` for exploration/research, default (Sonnet) for code generation
- **Progressive Disclosure**: Large reference files loaded on-demand to minimize initial context

## [2.0.0] - 2026-02-01

### Changed

- **BREAKING: Commands migrated to Skills**: All 16 commands migrated to the skills format (Claude Code v2.1.3+)
  - Commands in `commands/` are kept for backward compatibility but skills take precedence
  - All component references now use `skills` field instead of `commands` in marketplace.json
  - Plugin variants updated to reference skill directories instead of command directories
  - Version bumped to 2.0.0 to signal the architectural change

- **New skills created from commands** (16 total):
  - `implement-feature` - from commands/dev/implement-feature.md
  - `fix-bug` - from commands/dev/fix-bug.md (with references/examples.md)
  - `review-security` - from commands/dev/review-security.md (with references/agent-prompts.md, report-template.md)
  - `inject-nextjs-docs` - from commands/dev/inject-nextjs-docs.md
  - `docs-adr` - from commands/docs/adr.md
  - `docs-check` - from commands/docs/check.md (with references/scoring-criteria.md, verification-patterns.md)
  - `docs-diagram` - from commands/docs/diagram.md (with references/detection-patterns.md, mermaid-patterns.md)
  - `docs-init` - from commands/docs/init.md
  - `docs-rfc` - from commands/docs/rfc.md
  - `docs-update` - from commands/docs/update.md (with references/change-detection.md, update-strategies.md)
  - `git-commit` - from commands/git/commit.md
  - `git-create-pr` - from commands/git/create-pr.md
  - `jira-daily` - from commands/jira/daily.md (with references/output-formats.md)
  - `jira-todo` - from commands/jira/todo.md (with references/output-formats.md)
  - `create-command` - from commands/claude/create-command.md (with references/frontmatter-guide.md, design-patterns.md)
  - `create-rule` - from commands/claude/create-rule.md (with references/memory-hierarchy.md, rule-examples.md)

- **All migrated skills use `disable-model-invocation: true`** since they are user-triggered workflows
- **Progressive disclosure applied**: Large commands split into SKILL.md + references/ for on-demand loading
- **Skills use standard frontmatter**: name, description, disable-model-invocation, argument-hint, allowed-tools

- **Plugin manifests updated to v2.0.0**:
  - `plugin.json`: Removed `commands` field, kept `skills` pointing to `./skills/`
  - `marketplace.json`: All variant plugins now use `skills` field instead of `commands`
  - `cc-arsenal-dev`: Points to 4 specific skill directories
  - `cc-arsenal-docs`: Points to 6 specific skill directories
  - `cc-arsenal-git`: Points to 2 specific skill directories
  - `cc-arsenal-skills`: Points to 4 specific specialty skill directories (was loading all skills from directory)
  - `cc-arsenal`: Full toolkit, loads all 20 skills

- **Documentation updated**: CLAUDE.md, README.md reflect skills-first architecture
  - Unified "Available Skills (20 total)" section replaces separate Commands/Skills sections
  - Plugin variants table updated with skill names instead of command paths
  - File organization tree shows skills/ as primary, commands/ as legacy

## [Unreleased]

### Added

- **/dev:inject-nextjs-docs Command**: Run `@next/codemod agents-md` to inject compressed Next.js framework documentation into CLAUDE.md or AGENTS.md
  - Phase 0: Project validation (Next.js detection, version check, target file detection)
  - Phase 1: Non-interactive codemod execution with `--output` flag
  - Phase 2: Result verification and content validation
  - Injects ~8KB compressed pipe-delimited index from ~40KB of docs (100% eval pass rate vs 53% baseline)
  - Anti-hallucination guidelines enforce evidence-based reporting
- **find-skills Skill**: Discover and install third-party agent skills from the open skills.sh ecosystem
  - SKILL.md with quick start, essential commands, installation scopes, and source formats
  - `references/commands.md` - Complete `npx skills` CLI reference (find, add, list, remove, check, update, init)
  - `references/workflows.md` - Discovery patterns, security review checklist, and cc-arsenal integration guidance
  - Lists built-in cc-arsenal skills to avoid redundant installs
  - Progressive disclosure design following skill-creator guidelines
- **Agent Skills Installation Method**: Added `npx skills add mgiovani/cc-arsenal` as a second installation option in README
  - Works with Claude Code, Cursor, Codex, and 30+ other AI agents via the open Agent Skills ecosystem
  - Installs skills only (commands/hooks require the Claude Code Plugin method)
- **/dev:review-security Command**: Comprehensive security review command targeting OWASP Top 10 2025 and bytecode vulnerabilities
  - Phase 0: Scan Scope Determination - Supports PR numbers, commit SHAs, or entire codebase scanning
  - Phase 1: Technology Discovery - Auto-discovers tech stack to prioritize relevant vulnerabilities
  - Phase 2: Progress Tracking - TodoWrite-based tracking for all OWASP categories and bytecode analysis
  - Phase 3: Parallel Vulnerability Scanning - 6 parallel agents for comprehensive coverage:
    - Agent 1: Access Control & Authentication (A01, A07)
    - Agent 2: Configuration & Insecure Design (A02, A06)
    - Agent 3: Injection & Data Integrity (A05, A08)
    - Agent 4: Cryptography & Supply Chain (A04, A03)
    - Agent 5: Bytecode Security (Python .pyc, JS/TS compilation, Java bytecode)
    - Agent 6: Logging & Exception Handling (A09, A10)
  - Phase 4: Findings Consolidation - Deduplication, severity prioritization, OWASP categorization
  - Phase 5: Security Report Generation - Comprehensive markdown report with statistics, fixes, and references
  - Phase 6: Verification & Quality Check - 10-point quality checklist before report delivery
  - **Analysis-only approach**: Identifies vulnerabilities, explains findings, suggests multiple fix approaches (no code changes)
  - Anti-hallucination guidelines enforce evidence-based findings (file paths, line numbers, code snippets)
  - Covers all OWASP Top 10 2025 categories (including 2 new: Supply Chain, Exception Handling)
  - Bytecode-specific scanning for Python, JavaScript/TypeScript, and Java compiled code vulnerabilities
  - Scope options: `--scope [web|api|mobile|backend|frontend]` for focused analysis
  - References latest CVEs, CWEs, and security best practices (2025 research)
  - Comprehensive tooling recommendations (SAST, SCA, secret scanning)
- **/dev:fix-bug Command**: Comprehensive bug fixing command with test-driven debugging workflow
  - Phase 0: Project Discovery - Auto-discovers test/lint/dev commands from any project type
  - Phase 1: Bug Analysis & Reproduction - TDD approach requiring failing test verification
  - Phase 2: Fix Planning - Minimal, focused solution design with user approval for non-trivial fixes
  - Phase 3: Implementation - Fix with comprehensive test coverage
  - Phase 4: Quality Verification - All tests pass, no lint/type errors
  - Phase 5: Conventional Commit - Proper git commit with `fix:` type
  - Phase 6: Optional browser testing integration with agent-browser skill
  - Anti-hallucination guidelines enforce evidence-based debugging (file paths, line numbers)
  - Parallel subagents for bug location, impact analysis, and fix design
  - Works across Python (pytest), Node.js (npm/bun test), and other ecosystems
  - Quality gates ensure no regressions introduced
  - Optional `--branch`, `--interactive`, and `--test-only` flags
  - Based on /dev:implement-feature pattern with debugging-specific phases
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

[Unreleased]: https://github.com/mgiovani/cc-arsenal/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/mgiovani/cc-arsenal/compare/v1.2.0...v2.0.0
[1.2.0]: https://github.com/mgiovani/cc-arsenal/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/mgiovani/cc-arsenal/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/mgiovani/cc-arsenal/releases/tag/v1.0.0
