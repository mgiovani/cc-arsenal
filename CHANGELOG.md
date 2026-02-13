# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [3.1.0] - 2026-02-13

### Changed - Dual Repository Architecture Migration

#### Skills Cross-Platform Publishing
- **Migration**: Extracted 22 skills to separate [mgiovani/skills](https://github.com/mgiovani/skills) repository for cross-platform distribution
- **Architecture**: Dual-repository model with sync workflow
  - **skills-upstream/** (git submodule): Cross-platform base SKILL.md files from mgiovani/skills
  - **enhancements/**: Claude Code-specific enhancements (hooks, tools, contexts)
  - **skills/** (merged): Synced output combining base + enhancements
- **Sync Workflow**: `make sync-skills` merges upstream changes with local enhancements
- **Benefits**:
  - Skills publishable to skills.sh marketplace
  - Compatible with Claude Code, Cursor, Windsurf, and other agents
  - Maintains Claude Code-specific features through enhancement layer

#### Migrated Skills (22 total)
- **Documentation (6)**: docs-adr, docs-check, docs-diagram, docs-init, docs-rfc, docs-update
- **Git (3)**: git-commit, git-create-pr, git-release
- **Reviews (4)**: review-security, review-code, review-deps, review-perf
- **Jira/GitHub (3)**: jira-daily, jira-todo, gh-daily
- **Utilities (2)**: create-command, create-rule
- **Development (4)**: ci-generate, project-planner, inject-docs, inject-nextjs-docs

#### New Infrastructure
- **sync_skills.py**: Automated sync script with status tracking and SYNC.md metadata
- **Makefile commands**: `make sync-skills`, `make sync-skills-status`
- **Git submodule**: skills-upstream tracks mgiovani/skills repository
- **ENHANCEMENT.md format**: Separate enhancement files for Claude Code-specific features
- **Marketplace integration**: Updated plugin manifests for both repositories

#### Skills Exclusive to cc-arsenal (10 remaining)
- **Development**: implement-feature, fix-bug, team-implement
- **Specialty**: agent-browser, find-skills, skill-creator, jira-cli

### Fixed
- Auto-fixed 5 linting errors in utility scripts (import ordering, type annotations)

### Technical Details
- **Release**: mgiovani/skills v1.0.0 published to GitHub
- **Installation**: `npx skills add mgiovani/skills` or `/plugin install skills@skills-marketplace`
- **Sync format**: Base SKILL.md + ENHANCEMENT.md → Merged output
- **14 enhanced skills** (with Claude Code features) + **8 base-only skills**

## [3.0.0] - 2026-02-06

### Added

#### inject-docs - Framework Documentation Injector
- **Category**: Development (cc-arsenal-dev)
- **Type**: User-invoked
- **Purpose**: Inject framework-specific best practices into CLAUDE.md/AGENTS.md for passive AI agent access
- **Frameworks supported**:
  - Next.js: Uses Vercel's agents-md codemod (version-aware, pipe-delimited compression)
  - FastAPI: Injects zhanymkanov/fastapi-best-practices (domain-driven structure, async patterns, Pydantic validation)
- **Features**:
  - Auto-detects framework from package.json/pyproject.toml/requirements.txt
  - Non-destructive: updates existing sections without overwriting
  - Target file priority: CLAUDE.md → AGENTS.md → CLAUDE.md (create)
- **Usage**: `/inject-docs` (auto-detect) or `/inject-docs [nextjs|fastapi]` (explicit)
- **Components**:
  - SKILL.md with complete workflow (detection, injection, verification)
  - references/fastapi-best-practices.md (13KB reference content)
  - scripts/inject_fastapi_docs.py (Python injection script)

### Enhanced

#### inject-nextjs-docs - Deprecated in favor of inject-docs
- Legacy skill now superseded by the more general inject-docs skill
- Existing functionality preserved for backward compatibility

## [3.0.0] - 2026-02-06

### Added - Tier 1: Must-Build Critical Skills

#### review-code - Multi-Agent PR Code Review
- **Category**: Development (cc-arsenal-dev)
- **Type**: User-invoked
- 6-phase workflow with 5 parallel Explore agents analyzing: correctness/logic, performance, code style/patterns, test coverage gaps, error handling/edge cases
- Severity ranking: Critical/Major/Minor/Nit with file:line references
- **Unique feature**: Iterative diff-only re-scan after fixes showing resolved/remaining/new findings
- Focus mode: `--focus [correctness|performance|style|tests|errors]` to run subset of agents

#### test-suite - Test Generation and Coverage Analysis
- **Category**: Development (cc-arsenal-dev)
- **Type**: Model-invoked (activates on "write tests", "add coverage", etc.)
- 6-phase workflow: project discovery → coverage gap analysis → test plan → parallel test generation → quality verification → commit
- Supports pytest, vitest, jest, Go testing, Rust cargo test with idiomatic patterns
- Stop hook verification: runs tests, checks coverage improvement, lints test files
- Framework-specific patterns for fixtures, mocking, parametrized tests

#### refactor - Safe Codebase Refactoring
- **Category**: Development (cc-arsenal-dev)
- **Type**: Model-invoked (activates on "refactor", "clean up", "extract method", etc.)
- 6-phase workflow with TDD discipline: characterization tests FIRST, then incremental refactoring with test after each step
- 2 parallel Explore agents for dependency/caller analysis and test coverage mapping
- Stop hook verification after each change
- Catalog of 8 refactoring patterns with step-by-step procedures

### Added - Tier 2: High Value Skills

#### git-release - Release Management and Changelog
- **Category**: Git (cc-arsenal-git)
- **Type**: User-invoked
- 5-phase workflow: collect commits since last tag → auto-detect version bump → generate CHANGELOG.md → user approval → execute
- Leverages conventional commits for automatic semver bumping (breaking→major, feat→minor, fix→patch)
- Supports 8 version file formats: package.json, pyproject.toml, Cargo.toml, setup.cfg, VERSION, build.gradle, and more
- Generates grouped CHANGELOG entries: Breaking Changes → Features → Bug Fixes → Performance → Documentation → Other
- Creates GitHub releases via `gh release create`

#### gh-daily - GitHub Issues Daily Planner
- **Category**: Git/GitHub (cc-arsenal-git)
- **Type**: User-invoked
- 5-phase workflow: auto-detect repo/user → gather data → priority scoring → 3 parallel agents → report generation
- Data sources: assigned issues, authored PRs, review requests, notifications, git log
- Priority scoring: label weights, milestone proximity, age, blocking status
- Output formats: detailed, brief, slack
- Cross-repo support: `--all-repos` flag for multi-repository activity tracking

#### review-deps - Dependency Audit and Upgrade
- **Category**: Development (cc-arsenal-dev)
- **Type**: User-invoked
- 6-phase workflow with 3 parallel Explore agents: vulnerabilities (CVE severity), licenses (compliance risk), staleness (upgrade complexity)
- Supports 10 ecosystems: npm/yarn/pnpm, pip/uv, cargo, go, composer, bundler, .NET, Maven/Gradle, plus Dependabot
- Composite health score (0-100) with weighted dimensions
- Prioritized action plan: immediate/short-term/medium-term/long-term upgrades
- Scope filters: `--scope [vulnerabilities|licenses|staleness|all]`

### Added - Tier 3: Nice-to-Have Skills

#### ci-generate - CI/CD Workflow Generator
- **Category**: Development (cc-arsenal-dev)
- **Type**: User-invoked
- 5-phase workflow: parse arguments → stack detection → research best practices → design pipeline → generate & validate
- Supports 4 platforms: GitHub Actions, GitLab CI, CircleCI, Jenkins
- Auto-detects: language, package manager, test framework, build system, deployment targets
- Standard stages: lint/format/type-check → test with coverage → build → security scan → deploy
- Comprehensive reference templates for Node.js, Python, Docker, monorepos, matrix testing

#### review-perf - Performance Analysis
- **Category**: Development (cc-arsenal-dev)
- **Type**: User-invoked
- 7-phase workflow with 4 parallel Explore agents: Database (N+1, indexes), Algorithm (Big O), Frontend (bundle, rendering), Resources (memory, leaks)
- Severity ranking: Critical/High/Medium/Low with performance-specific criteria
- Includes profiling recommendations and optimization suggestions
- ORM-specific patterns for Django, Prisma, SQLAlchemy, Hibernate, TypeORM
- Core Web Vitals impact analysis for frontend findings

#### team-review - Multi-Agent PR Review Team
- **Category**: Teams (cc-arsenal-teams)
- **Type**: User-invoked
- Premium team orchestration with 7 specialized reviewers: Architecture (opus), Security (sonnet), Performance (sonnet), Testing (sonnet), Style & Patterns (sonnet), Docs & UX (haiku), Adversary (sonnet)
- **Unique adversary reviewer**: Waits for other findings, then challenges assumptions and finds blind spots
- Lite mode: 4 combined agents via Task subagents for cost efficiency
- Auto-detects complexity to choose full vs lite mode
- Requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` for full mode
- Report includes reviewer consensus table, cross-cutting concerns, adversary challenges, and overall verdict

### Added - New Plugin Variant

#### cc-arsenal-review
New plugin variant bundling all code review and quality skills:
- `review-code` - Multi-agent PR code review
- `review-security` - OWASP security analysis (existing)
- `review-deps` - Dependency audit and upgrade planning
- `review-perf` - Performance analysis

Target audience: Teams focused on code quality and compliance

### Changed

- **Version**: 2.3.0 → 3.0.0 (major release)
- **Total skills**: 22 → 31 skills (+9 new skills, +41% growth)
- **cc-arsenal** plugin: Updated description to reflect 31 skills
- **cc-arsenal-dev** plugin: Added 6 new skills (review-code, test-suite, refactor, review-deps, ci-generate, review-perf)
- **cc-arsenal-git** plugin: Added 2 new skills (git-release, gh-daily), updated description to include GitHub workflow
- **cc-arsenal-teams** plugin: Added team-review skill, updated description

## [2.3.0] - 2025-01-XX

### Added
- Initial release with 22 skills
- Plugin variants: cc-arsenal, cc-arsenal-dev, cc-arsenal-docs, cc-arsenal-git, cc-arsenal-skills, cc-arsenal-teams

[3.0.0]: https://github.com/mgiovani/cc-arsenal/compare/v2.3.0...v3.0.0
[2.3.0]: https://github.com/mgiovani/cc-arsenal/releases/tag/v2.3.0
