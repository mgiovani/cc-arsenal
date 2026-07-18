# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [5.0.0] - 2026-07-18

The authoring-standard overhaul. Every skill was rewritten to the Anthropic skill-authoring standard and gated by a full baseline-vs-new eval loop, four new skills were mined from usage history, and all 45 skills now ship eval coverage. The catalog grew from 41 to 45 skills.

### Added
- **4 new skills** mined from real usage history, each eval-gated new_skill-vs-baseline (all four beat a no-skill baseline):
  - **orchestrate** (15/15 vs 7/15): turn any task into a model-tiered multi-agent plan — decompose, classify each subtask, map it to the right model (haiku research, opus planning, sonnet implementation), run independent tracks in parallel under strict one-owner-per-file discipline, then synthesize yourself. Declines to orchestrate trivial single-file tasks.
  - **oss-launch** (18/22 vs 13/22): private-to-public GitHub launch pipeline — secrets/license pre-flight, review-code fixes, branding, README/description rewrite, mention scrub (presents matches, never auto-edits), a gated history rewrite (private-only, explicit confirmation, refuses on already-public repos), then flips public with a stage table of real commands.
  - **codex-imagegen** (17/18 vs 10/18): polished raster art (logos, mascots, heroes, sprites, mockups) via Codex CLI's `$imagegen`, with chroma-key transparency handling and pixel-level QC; routes quick/photorealistic requests to nanobanana.
  - **improve-skill** (16/17 vs 7/17): evidence-based improvement of an existing skill — snapshot the baseline, rewrite to the rubric, author evals, benchmark new-vs-old, with a per-dimension restraint gate so an already-compliant skill gets a small diff.
- **Full eval coverage**: all 45 skills now ship both `evals/evals.json` (task-completion) and `evals/trigger-eval.json` (description-triggering), up from 24 of 41.
- **cc-arsenal-dev** gains codex-imagegen and oss-launch; **cc-arsenal-skills** gains improve-skill and orchestrate.

### Changed
- **All 41 existing skills rewritten to the Anthropic authoring standard**, each gated by a per-skill baseline-vs-new eval loop (sandboxed executors, deterministic grading, human-reviewed): use-case-first descriptions with explicit "Not for X (use sibling)" disambiguation across every overlapping cluster, sub-500-line imperative bodies with WHY reserved for hard boundaries, heavy detail moved to `references/<topic>.md` with load-when links, anti-hallucination floors (reported numbers must come from a command actually run), and tool-neutral portability with explicit sequential fallbacks for the orchestration skills.
- **Descriptions validated** against their trigger-eval sets — the optimizer kept the rewritten description in every case measured, confirming they already trigger reliably.
- **ship** owns "ship it" for the default feature-branch case; **gitflow** cedes that trigger and keeps release/hotfix-topology cases. ship's description folded to valid YAML and trimmed under the 1024-char cap.
- All plugin versions bumped to 5.0.0; skill counts and variant tables regenerated across AGENTS.md, CLAUDE.md, README.md, and docs (41 → 45).

## [4.0.0] - 2026-07-06

One repo, any agent. cc-arsenal is now a single agent-agnostic skills repository following the [Agent Skills](https://agentskills.io) open standard, with Claude Code features (plugin variants, hooks, subagent orchestration) as an optional layer. Install from any compatible tool with `npx skills add mgiovani/cc-arsenal`, or from Claude Code with `/plugin marketplace add mgiovani/cc-arsenal`.

### Added
- **4 new skills** mined from real usage history:
  - **ship**: "Ship train" orchestrator — review → project pre-merge checks → conventional commit → PR → CI-green, reusing the sibling git/review skills.
  - **vrt-check**: Visual regression workflow — detects the project's VRT tooling (justfile targets, Storybook test-runner, Playwright, Chromatic, Loki), triages diffs as regression vs intended change before updating snapshots.
  - **ci-local**: Replicates GitHub Actions jobs locally when Actions is unavailable or out of quota, with a parity report for steps it can't reproduce.
  - **i18n-check**: Locale completeness checker — missing/untranslated/orphan keys across locales plus hardcoded-string detection, per-framework references bundled.
- **Eval coverage**: 17 new eval packs (`evals/evals.json` + `evals/trigger-eval.json`) — every new skill plus agent-browser, ci-generate, docs-adr, docs-check, env-setup, git-commit, git-create-pr, git-release, review-deps, review-perf, review-security, team-implement, team-review; completed gitflow's missing assertions and review-design's missing trigger evals. 24 of 41 skills now have evals.
- **cc-arsenal-jira** plugin variant (jira-cli, jira-daily, jira-todo).
- **Portability convention**: skill bodies are tool-neutral; Claude Code-only frontmatter (`allowed-tools`, `disable-model-invocation`, `hooks`, `context`, `agent`) is enhancement other tools safely ignore. The 8 orchestration-heavy skills now document sequential-inline fallback when no subagent/task tools exist.
- **Version tooling**: `.version-bump.json` + `scripts/bump_version.py` + `make bump-version VERSION=x.y.z` keep all manifest version fields in lockstep.
- **Reusable audit workflow**: `.claude/workflows/arsenal-audit.js` — re-runnable multi-agent repo audit (per-skill grading, manifest drift, usage-gap mining, ranked action plan).

### Changed
- **All 41 skills audited; 32 improved**: corrupted SKILL.md bodies repaired (duplicated sections, unclosed code fences introduced by the retired sync pipeline), descriptions rewritten for reliable triggering with sibling-skill disambiguation, phantom subagent references removed, over-engineered fan-outs collapsed to inline steps, oversized bodies cut (e.g. project-planner 557→248 lines, git-commit 271→75).
- **AGENTS.md is now the canonical repo doc** (read natively by Codex, Cursor, Copilot, Gemini CLI); CLAUDE.md reduced to an `@AGENTS.md` import plus Claude Code-only content. README repositioned agnostic-first.
- **Docs regenerated from ground truth**: accurate skill counts (41) and variant tables everywhere, plugin-marketplace install as the primary path, real `make` target names in troubleshooting/features docs.
- All plugin versions bumped to 4.0.0.

### Fixed
- `plugin.json` no longer declares `skills` alongside marketplace variant entries (documented manifest-conflict risk); auto-discovery is the single authority for the full plugin.
- 8 previously unreachable skills (absent from every plugin variant) are now installable via variants.
- All 27 ruff lint errors fixed; `pyright` added to dev dependencies and type-check green; installer tests updated for the skills-only layout.
- `${CLAUDE_PLUGIN_ROOT}`-relative hook path in git-commit so the pre-commit lint hook resolves from any project.

### Removed
- **BREAKING**: `create-command` skill (merged into `create-skill`) and `inject-nextjs-docs` skill (merged into `inject-docs`).
- **skills-upstream submodule and sync pipeline** (`scripts/sync_skills.py`, `scripts/extract_enhancements.py`, all `SYNC.md` files): the sync script was corrupting SKILL.md files by concatenating upstream + enhancement content; the separate mgiovani/skills repo is retired in favor of this single repo.
- Legacy `commands/` directory (16 pre-v2 files, all superseded by skills), `enhancements/` (24 already-shipped enhancement docs), `resources/templates/` + empty `templates/` (dead duplicate trees), empty scaffold dirs (`agents/`, `references/`), deprecated hooks, and `docs/agent-development.md` (documented a framework that never existed).

## [3.3.0] - 2026-07-02

### Added
- **Lean Code discipline**: Added a shared "lean, never negligent" checklist to the 5 dev skills (`implement-feature`, `fix-bug`, `refactor`, `test-suite`, `review-code`) — write the smallest change that fully does the job without ever cutting validation, error/data-loss handling, security, or accessibility. Deliberate shortcuts are marked inline with `LEAN-DEBT:` instead of left as a silent gap.
  - **implement-feature**: Full `## Lean Code` section, a Phase 2 planning hook, and propagation into the Step 3.3 parallel-subagent prompt template so implementation subagents apply the discipline directly. Also deduplicated the two conflicting `## Quality Gates` headers into `## Verification Gates` and `## Subagent Quality Checklist`.
  - **review-code**: New `enhancements/review-code/ENHANCEMENT.md` adds a 6th parallel "Simplicity & Over-Engineering" specialist (`OE-` findings, tags `[delete]/[reuse]/[stdlib]/[builtin]/[unneeded]/[simplify]`) with a static, non-benchmark lines-removable count and an explicit ban on fabricated performance/token/percentage savings claims.
  - **fix-bug**, **refactor**, **test-suite**: Light-touch deltas — never-negligent floor callouts, deletion-over-addition and root-cause-once-in-the-shared-function guidance, and lean test-coverage guidance (test behavior and boundaries, not trivial getters or coverage-only snapshots).
- **Skill evals**: Added `evals/evals.json` (task assertions) and `evals/trigger-eval.json` (~20 queries each, with realistic near-miss negatives) for the 5 dev skills, converging on the schema `create-skill`'s `quick_validate.py`/`run_eval.py` already support. Tightened each skill's `description` frontmatter to be active, concrete, and explicit about "use when" contexts, since Claude tends to undertrigger vague descriptions.
- **review-design**: New UX/UI design quality audit skill, added to the `cc-arsenal-review` plugin variant.
- **gitflow**: New skill covering the full gitflow branching model — starting/finishing feature branches, cutting versioned releases with changelog generation, coordinating emergency hotfixes, and keeping `main`/`dev` in sync. Added to the `cc-arsenal-git` plugin variant.
- **AGENTS.md**: Root-level mirror of CLAUDE.md's repository guidance for Codex and other AGENTS.md-aware coding assistants.

### Changed
- **agent-browser**: Session-close hook now scopes to the current project's session instead of closing every daemon, preventing parallel Claude Code sessions from tearing down each other's browsers. Documented Homebrew install, the `doctor` health check, Lightpanda vs. Chrome engine selection, and new env vars (`AGENT_BROWSER_IDLE_TIMEOUT_MS`, `AGENT_BROWSER_ENGINE`, `AGENT_BROWSER_ENCRYPTION_KEY`).
- **skills-upstream**: Bumped submodule to [v1.1.0](https://github.com/mgiovani/skills/releases/tag/v1.1.0), pulling in the nanobanana skill mirror and a README cleanup.

### Fixed
- **statusline**: Show rate-limit reset times exactly, without rounding.
- **skills**: Removed a buggy completion-verification `Stop` hook.
- **ci**: Corrected a make target from `setup-dev` to `dev`.

### Removed
- **forge suite**: Removed the 7 abandoned `forge-*` skills (`forge-brief`, `forge-architect`, `forge-story`, `forge-dev`, `forge-qa`, `forge-review`, `forge-security`) and their enhancements. No other skill, doc, or plugin variant referenced them.

## [3.2.0] - 2026-02-16

### Added
- **create-skill**: Specification-driven skill creation with live documentation fetching
  - Fetches latest specifications from agentskills.io and platform.claude.com every run
  - Interactive clarification using AskUserQuestion for core identity and technical details
  - Multi-source example research (skills.sh, anthropics/skills, mgiovani/skills, cc-arsenal)
  - Skill composition discovery (identifies existing skills to reference/invoke)
  - User approval gate via EnterPlanMode before generating any files
  - Model-invocable for automatic activation during larger workflows
  - Task Management System for transparent progress tracking
  - Validation using bundled quick_validate.py script

### Changed
- **create-command**: Soft-deprecated in favor of create-skill (maintained for backward compatibility)
- **Marketplace**: Updated cc-arsenal-skills variant to include create-skill instead of skill-creator
- **Version**: Bumped all plugin variants from 3.1.0 to 3.2.0

### Removed
- **skill-creator**: Replaced by create-skill
  - Absorbed useful parts: quick_validate.py script, folder naming guidance
  - Eliminated stale bundled documentation in favor of live fetching
  - Removed init_skill.py and package_skill.py (niche use cases)

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
