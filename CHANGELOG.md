# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **Statusline: staff-level overhaul.** Removed ~3,900 lines of dead code (an entire abandoned cache subsystem, superseded flat modules, rotted dev tools) and retired the background daemon — its output had no consumers and the OAuth refresh now fires directly from the render path, non-blocking. The whole tree is shellcheck-clean, usage percentages are now threshold-colored (green/yellow/red), the test suite was rebuilt against the live modules with shared assert helpers, glob discovery, and full /tmp isolation (9/9 suites), docs were consolidated into STATUSLINE.md and verified against the code, and CI gained a Linux shellcheck+test job.
- **Statusline: context moved next to the model.** Line 1 now renders the context-window percentage (`📊`) immediately after the model instead of after the git/worktree components, so token usage stays glanceable next to what's consuming it. Order is now model → context → directory → git → worktree → cost → session.

### Fixed
- **Statusline: account badge now shows without `CLAUDE_CODE_OAUTH_TOKEN`.** The `CLAUDE_STATUSLINE_ACCOUNT_LABEL` badge was gated on the OAuth-token env var also being set, so accounts switched via a separate credential store (`CLAUDE_SECURESTORAGE_CONFIG_DIR`) got no badge. The label is user-set display text and now renders whenever it's set, independent of how the account was selected. Per-account usage-cache isolation and background OAuth refresh remain keyed on `CLAUDE_CODE_OAUTH_TOKEN`.
- **Plugin manifests:** `.claude-plugin/plugin.json` still carried the pre-v5 marketing description (it had also sat at version 2.0.0 from February through July while `marketplace.json` advanced — the snapshot stale Claude Desktop installs were showing). Descriptions are aligned, and `make validate-plugins` now fails on any version or description drift between the two manifests so a partial bump can't ship again.
- **Statusline (post-review):** the background OAuth fetcher now holds a single-flight lock for the whole fetch, so overlapping renders can't stack concurrent calls against the rate-limited API; the tmux cache write reuses values the render already extracted instead of re-forking `cat`+`jq`; ISO timestamps with explicit UTC offsets parse to the correct epoch instead of being read as UTC; non-numeric values render as-is instead of `printf` garbage like `045%`; `hash_sha256` falls back to MD5 (then `default`) so per-account cache keys stay distinct on minimal systems; the error log is size-capped. The config surface was cut to the keys the code actually honors, `STATUSLINE_CONFIG_OVERRIDE` now really works, `configure_statusline.py` was rewritten to offer only working options (481→80 lines), and the dead `lib/tracking/` modules were removed (~550 lines).
- **Statusline:** `extract_json` returned success with empty output on a grep-fallback miss, making every `||` fallback chain over it unreachable (e.g. session-id lookup never tried `session_id`/`conversation_id`); `lib/display/components.sh` didn't source its own `core/json.sh` dependency; `cache_clear` could expand `rm -rf` against `/*` if its directory variable was ever empty.

### Changed
- **New `integrations/` tier.** Agent-CLI-specific tooling now lives under `integrations/<agent-cli>/`, one subdirectory per agent CLI: the statusline moved from `scripts/claude/statusline` to `integrations/claude-code/statusline` and the claude-hi session scheduler from `scripts/claude-hi` to `integrations/claude-code/claude-hi`. The installed location (`~/.claude/scripts/claude/statusline`) is unchanged, so existing installs and `settings.json` entries keep working without migration.

### Added
- **Statusline: per-account usage reporting.** When Claude Code runs under `CLAUDE_CODE_OAUTH_TOKEN`, the statusline now fetches and displays that account's real 5h/7d rate limits instead of the stored login's stdin values, with per-account cache/backoff isolation (sha256-keyed filenames, tokens never written to disk), an opt-in account badge via `CLAUDE_STATUSLINE_ACCOUNT_LABEL`, and a per-account tmux rate-limits cache file. The default single-account case is unchanged. Works on macOS and Linux.

## [5.0.0] - 2026-07-18

The authoring-standard overhaul. Every skill was rewritten to the Anthropic skill-authoring standard and gated by a full baseline-vs-new eval loop, four new skills were mined from usage history, and all 45 skills now ship eval coverage. The catalog grew from 41 to 45 skills.

### Added
- **4 new skills** mined from real usage history, each eval-gated new_skill-vs-baseline (all four beat a no-skill baseline):
  - **orchestrate** (15/15 vs 7/15): turn any task into a model-tiered multi-agent plan — decompose, classify each subtask, map it to the right model (haiku research, opus planning, sonnet implementation), run independent tracks in parallel under strict one-owner-per-file discipline, then synthesize yourself. Declines to orchestrate trivial single-file tasks.
  - **oss-launch** (18/22 vs 13/22): private-to-public GitHub launch pipeline — secrets/license pre-flight, review-code fixes, branding, README/description rewrite, mention scrub (presents matches, never auto-edits), a gated history rewrite (private-only, explicit confirmation, refuses on already-public repos), then flips public with a stage table of real commands.
  - **codex-imagegen** (17/18 vs 10/18): polished raster art (logos, mascots, heroes, sprites, mockups) via Codex CLI's `$imagegen`, with chroma-key transparency handling and pixel-level QC; the default image generator for illustrated assets.
  - **improve-skill** (16/17 vs 7/17): evidence-based improvement of an existing skill — snapshot the baseline, rewrite to the rubric, author evals, benchmark new-vs-old, with a per-dimension restraint gate so an already-compliant skill gets a small diff.
- **Full eval coverage**: all 45 skills now ship both `evals/evals.json` (task-completion) and `evals/trigger-eval.json` (description-triggering), up from 24 of 41.
- **cc-arsenal-dev** gains codex-imagegen and oss-launch; **cc-arsenal-skills** gains improve-skill and orchestrate.

### Changed
- **All 41 existing skills rewritten to the Anthropic authoring standard**, each gated by a per-skill baseline-vs-new eval loop (sandboxed executors, deterministic grading, human-reviewed): use-case-first descriptions with explicit "Not for X (use sibling)" disambiguation across every overlapping cluster, sub-500-line imperative bodies with WHY reserved for hard boundaries, heavy detail moved to `references/<topic>.md` with load-when links, anti-hallucination floors (reported numbers must come from a command actually run), and tool-neutral portability with explicit sequential fallbacks for the orchestration skills.
- **Descriptions validated** against their trigger-eval sets — the optimizer kept the rewritten description in every case measured, confirming they already trigger reliably.
- **ship** owns "ship it" for the default feature-branch case; **gitflow** cedes that trigger and keeps release/hotfix-topology cases. ship's description folded to valid YAML and trimmed under the 1024-char cap.
- All plugin versions bumped to 5.0.0; skill counts and variant tables regenerated across AGENTS.md, CLAUDE.md, README.md, and docs (41 → 45).
- **Image-generation routing**: **codex-imagegen** is now the default image generator for any implicit "generate an image / logo / hero / mascot" request (covered by the Codex subscription, no marginal cost), and **nanobanana** is narrowed to explicit-invocation only since it makes a real, billed Gemini API call — triggering only on "nanobanana"/"nano banana"/"gemini image generation"/`GEMINI_API_KEY`. codex-imagegen no longer references nanobanana, and oss-launch's brand stage no longer auto-falls-back to it.
- **features.md labeling convention**: every skill is documented as `#### /<name>` with a single `— auto` (also model-triggered) or `— manual` (`disable-model-invocation: true`, slash-only) marker matched to frontmatter, plus a one-line legend — replacing the inconsistent `(model-invoked)`/`(user-invoked)` suffixes (13 of which disagreed with frontmatter).
- **Skill composition convention** added to `AGENTS.md`: a skill may invoke a sibling via the Claude Code `Skill` tool, but must state the tool-neutral fallback in the same sentence (other CLIs read the sibling's `SKILL.md` as text) — distinct from Task-tool subagent delegation. `ship`, `oss-launch`, `test-suite`, `git-create-pr`, and `team-implement` follow it.

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

## [1.2.0 -> 2.0.0 development]

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

[3.0.0]: https://github.com/mgiovani/cc-arsenal/compare/v2.3.0...v3.0.0
[2.3.0]: https://github.com/mgiovani/cc-arsenal/compare/v2.2.0...v2.3.0
[2.2.0]: https://github.com/mgiovani/cc-arsenal/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/mgiovani/cc-arsenal/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/mgiovani/cc-arsenal/compare/v1.2.0...v2.0.0
[1.2.0]: https://github.com/mgiovani/cc-arsenal/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/mgiovani/cc-arsenal/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/mgiovani/cc-arsenal/releases/tag/v1.0.0
