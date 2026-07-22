# AGENTS.md

This is the canonical, tool-agnostic guidance file for **cc-arsenal** — read natively by Codex, Cursor, Copilot, Gemini CLI, OpenCode, and any other AGENTS.md-aware tool. Claude Code does not read this file directly; `CLAUDE.md` imports it via `@AGENTS.md` and adds Claude-Code-only content on top.

## Repository Architecture

cc-arsenal is a collection of **45 Agent Skills** ([agentskills.io](https://agentskills.io) open standard) for development workflow automation. `skills/` is the single canonical tier — every skill lives there once, written tool-neutral, and any tool that speaks the Agent Skills format can load it directly.

### Core Components

- **Skills** (`skills/`): 45 skills covering development, code review, documentation, git/GitHub, jira, teams, browser automation, project planning, multi-agent orchestration, open-source launch prep, and skill discovery/creation/improvement
- **Scripts** (`scripts/`): Python utilities for installation, configuration, and code generation (Claude-Code-specific; see `CLAUDE.md`)
- **Integrations** (`integrations/`): agent-CLI-specific tooling that doesn't fit the tool-agnostic `skills/` tier — one subdirectory per agent CLI. Today that's `integrations/claude-code/`, holding the statusline and the `claude-hi` session scheduler; future agent CLIs (Codex, Gemini CLI, ...) get sibling directories alongside it as their own tooling needs arise.

## Install in any agent

```bash
# Any Agent-Skills-compatible tool (Codex, Cursor, Gemini CLI, OpenCode, ...)
npx skills add mgiovani/cc-arsenal
```

`npx skills` is the [skills.sh](https://skills.sh) CLI — it copies each skill into the target tool's own skills directory, no plugin system required.

Using Claude Code? See `CLAUDE.md` for the plugin marketplace install, plugin variants, and other Claude-Code-only extras.

## Portability convention

Skills in this repo are written **tool-neutral first**:

- Only `name` and `description` frontmatter are required for a skill to work anywhere.
- Claude-Code-only frontmatter keys (`allowed-tools`, `disable-model-invocation`, `hooks`, `context`, `agent`) are enhancement layers. Other tools ignore unknown frontmatter keys safely — a skill's correctness must never depend on them being honored.
- Orchestration skills (those that spawn subagents/parallel tasks in Claude Code) degrade gracefully to sequential inline execution when no subagent/task tool exists. The instructions describe the sequential fallback explicitly rather than assuming Task/Agent tools are always present.
- Paths and shell commands referenced inside a skill must be real, tool-independent commands (e.g. `git`, `gh`, `make`) — never a Claude-Code-only tool name used as if it were a shell command.

## Skill composition

Skills may build on each other along two distinct axes — keep them separate:

- **Sibling invocation (borrow a *procedure*)**: a skill may invoke another skill by name to reuse its steps, via the Claude Code `Skill` tool where available. Because `Skill` is Claude-Code-only and other CLIs can only read a sibling's `SKILL.md` as text, **every such call must state the tool-neutral fallback in the same sentence** — apply the sibling's documented rules/steps inline. Announce it with a `Using <skill> to <purpose>` line. For example: "use the `git-commit` skill to write the message (via the `Skill` tool where available, otherwise apply its conventional-commit rules inline)".
- **Subagent delegation (spawn a *role*)**: a skill may fan work out to a subagent via the Claude Code `Task`/`Agent` tools. This is the orchestration path the Portability convention already covers, and it degrades to sequential inline execution when no subagent tool exists.

Do not add `uses:`/`composes:` frontmatter and do not route composition through a mandatory dispatcher skill — plain prose naming the sibling, with its in-sentence fallback, is the whole mechanism.

## Available Skills (45 total)

All skills use progressive disclosure (SKILL.md + optional references/scripts/assets directories).

### Development (16 skills)
- **implement-feature**: Feature implementation with senior staff engineer best practices and parallel subagent orchestration where available
- **fix-bug**: Test-driven debugging with strict sequential task chain and dependency enforcement
- **test-suite**: Generate test suites by analyzing coverage gaps and writing tests that match project conventions
- **refactor**: Restructure existing code without changing behavior, verified against the full test suite at each step
- **ci-generate**: Generate a production-ready CI/CD pipeline config (GitHub Actions, GitLab CI, CircleCI, Jenkins)
- **ci-local**: Run the checks a GitHub Actions workflow would run, locally, when Actions is unavailable
- **vrt-check**: Runs the project's visual regression testing workflow, whatever tooling the repo actually uses
- **i18n-check**: i18n completeness checker — detects the project's i18n framework and diffs locale files
- **inject-docs**: Inject compressed framework-specific best practices and docs into CLAUDE.md/AGENTS.md
- **db-migrate**: Create, validate, and manage database migrations across any framework
- **docker-init**: Generate Dockerfiles and docker-compose.yml with auto-detected services and security hardening
- **env-setup**: Scan a codebase for env var usage, sync .env.example, and detect leaked secrets
- **project-planner**: Break down large projects into dependency-aware tasks with Mermaid visualization
- **nanobanana**: Generate and edit images using Nano Banana (Gemini image generation)
- **codex-imagegen**: Generate polished raster art (logos, mascots, heroes, sprites, mockups) via Codex CLI's `$imagegen`, with chroma-key transparency handling and QC
- **oss-launch**: Take a private project to a public GitHub launch — secrets/license pre-flight, review fixes, branding, README/description rewrite, mention scrub, gated history rewrite, then flip public

### Code Review & Quality (5 skills)
- **review-code**: Multi-agent code review across correctness, performance, style, tests, and error handling
- **review-security**: OWASP Top 10 2025 security analysis with parallel scanning agents where available
- **review-deps**: Audit dependencies for vulnerabilities, license risk, and staleness
- **review-perf**: Deep-dive performance audit of queries, algorithmic complexity, and resource leaks
- **review-design**: UX/UI/design quality audit mapped to WCAG 2.2 AA, Material Design 3, and Apple HIG

### Documentation (6 skills)
- **docs-adr**: Architecture Decision Records creation and management
- **docs-check**: Documentation validation and health scoring
- **docs-diagram**: Architecture diagrams generation (Mermaid)
- **docs-init**: Documentation structure initialization
- **docs-rfc**: Request for Comments documentation
- **docs-update**: Documentation sync with codebase state

### Git & GitHub (7 skills)
- **git-commit**: Conventional commit message generation
- **git-create-pr**: Pull request creation with standardized formats
- **git-release**: Semantic version releases with automated changelog generation
- **gitflow**: Manage a gitflow branching workflow (feature/release/hotfix branches)
- **git-sync**: Sync the current feature branch with its base/upstream via merge or rebase
- **ship**: Orchestrates a branch from "code done" to "merged" — runs review-code plus project-specific pre-merge checks
- **gh-daily**: GitHub-based standup report from assigned issues, PRs, and commit history

### Jira (2 skills)
- **jira-daily**: Smart standup report generator with activity analysis
- **jira-todo**: Smart daily work planner with intelligent prioritization

### Teams (2 skills)
- **team-implement**: Spec-driven team orchestration — adaptive development team scaling from 3 to 11 agents based on complexity. Accepts plain text, Jira tickets, GitHub issues, PRs, files, or URLs. Requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` for full mode in Claude Code; degrades to a single-agent sequential run elsewhere.
- **team-review**: Multi-agent PR review team (architecture, security, performance, testing, style, docs/UX, plus an adversary) for security-sensitive or large PRs

### Utilities (7 skills)
- **create-skill**: Specification-driven skill creation with eval system and description optimization
- **create-rule**: Create CLAUDE.md/AGENTS.md rules and memory guidelines
- **improve-skill**: Improve an existing skill to the authoring standard with measured before/after evidence — snapshots the baseline, rewrites to the rubric, and benchmarks new-vs-old
- **orchestrate**: Turn any task into a model-tiered multi-agent plan — decompose, map each subtask to the right model, run independent tracks in parallel under strict file ownership, then synthesize
- **find-skills**: Discover and install third-party agent skills from skills.sh
- **agent-browser**: AI-optimized browser automation with far less context overhead than raw Playwright/DOM tools
- **jira-cli**: Interactive command-line tool for Atlassian Jira

## Skill Anatomy

Skills are modular capabilities organized with this structure:

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (name, description, + optional tool-enhancement keys)
│   └── Markdown instructions
├── evals/ (optional but recommended)
│   ├── evals.json         - task-completion evals: prompt + assertions per scenario
│   └── trigger-eval.json  - description-triggering evals: does the skill fire on the right prompts?
└── Bundled Resources (optional)
    ├── scripts/      - Executable code (Python/Bash/etc.)
    ├── references/   - Documentation loaded as needed
    └── assets/       - Files used in output (templates, etc.)
```

### Progressive Disclosure

Skills use a three-level loading system:
1. **Metadata** (name + description) — always in context (~100 words)
2. **SKILL.md body** — loaded when the skill activates (<5k words)
3. **Bundled resources** — loaded only when the agent needs them

### Eval Convention

Each skill's `evals/evals.json` lists concrete scenarios (`id`, `prompt`, `assertions`) that a run of the skill must satisfy — used to catch regressions when a SKILL.md is edited. `evals/trigger-eval.json` instead tests description-triggering: given a set of realistic user prompts, does the skill's frontmatter `description` cause it to fire (or correctly not fire)? Use the `create-skill` skill's eval tooling to run either against a live agent.

## Development Commands

```bash
# Development Environment
make dev                  # Set up development with all dependencies
make pre-commit-install   # Install pre-commit hooks
make pre-commit-run       # Run pre-commit on all files

# Code Quality
make check                # Run all checks (lint + type-check)
make lint                 # Run ruff linting
make format                # Format code with ruff
make type-check           # Run pyright type checking

# Testing
make test                 # Run unit tests
make coverage             # Tests with coverage report

# Utilities
make clean                # Clean caches and build artifacts
make info                 # Show repository statistics
make validate-structure   # Validate repository structure
make validate-plugins     # Validate plugin manifests
```

Claude-Code-specific install/config commands (`make install`, `make dry-run`, `make configure`, statusline, claude-hi) live in `CLAUDE.md`.

## Contributing

1. **Fork** the repository and create a feature branch
2. **Develop** your skill or change — new skills go under `skills/<name>/SKILL.md`; keep frontmatter to `name` + `description` unless the skill genuinely needs a Claude-Code-only key (see Portability convention above)
3. **Add evals** — new or changed skills should ship an `evals/evals.json` (and `trigger-eval.json` if the description changed)
4. **Validate** with `make check` and `make validate-structure` / `make validate-plugins`
5. **Update CHANGELOG.md** for user-facing changes
6. **Submit** a pull request with a clear description

See `CONTRIBUTING.md` for the full development setup.

## File Organization
```
cc-arsenal/
├── skills/          # All 45 skills (canonical, tool-agnostic)
│   ├── implement-feature/   # Feature implementation with subagents
│   ├── fix-bug/             # Test-driven debugging
│   ├── test-suite/          # Test suite generation
│   ├── refactor/            # Behavior-preserving restructuring
│   ├── ship/                # Code-done-to-merged orchestration
│   ├── ci-generate/         # CI/CD pipeline generation
│   ├── ci-local/            # Run CI checks locally
│   ├── vrt-check/           # Visual regression testing
│   ├── i18n-check/          # i18n completeness checking
│   ├── inject-docs/         # Framework docs injection
│   ├── db-migrate/          # Database migration management
│   ├── docker-init/         # Dockerfile/compose generation
│   ├── env-setup/           # .env.example sync and secret scanning
│   ├── project-planner/     # Dependency-aware task planning
│   ├── nanobanana/          # Image generation (Nano Banana/Gemini)
│   ├── codex-imagegen/      # Raster art via Codex $imagegen
│   ├── oss-launch/          # Private-to-public GitHub launch prep
│   ├── review-code/         # Multi-agent code review
│   ├── review-security/     # OWASP security analysis
│   ├── review-deps/         # Dependency vulnerability/license audit
│   ├── review-perf/         # Performance audit
│   ├── review-design/       # UX/UI/design audit
│   ├── docs-adr/            # Architecture Decision Records
│   ├── docs-check/          # Documentation validation
│   ├── docs-diagram/        # Architecture diagrams
│   ├── docs-init/           # Documentation initialization
│   ├── docs-rfc/            # Request for Comments
│   ├── docs-update/         # Documentation updates
│   ├── git-commit/          # Conventional commits
│   ├── git-create-pr/       # Pull request creation
│   ├── git-release/         # Semantic version releases
│   ├── gitflow/             # Gitflow branching workflow
│   ├── git-sync/            # Branch sync/rebase
│   ├── gh-daily/            # GitHub-based standup reports
│   ├── jira-cli/            # Jira CLI integration
│   ├── jira-daily/          # Daily standup reports
│   ├── jira-todo/           # Work prioritization
│   ├── team-implement/      # Spec-driven team orchestration
│   ├── team-review/         # Multi-agent PR review team
│   ├── create-skill/        # Specification-driven skill creation
│   ├── create-rule/         # Create memory rules
│   ├── improve-skill/       # Evidence-based skill improvement
│   ├── orchestrate/         # Model-tiered multi-agent orchestration
│   ├── find-skills/         # Third-party skill discovery
│   └── agent-browser/       # Browser automation
├── scripts/        # Installation and utilities (see CLAUDE.md for Claude-Code-specific ones)
└── integrations/   # Agent-CLI-specific tooling, one subdirectory per agent CLI
    └── claude-code/    # Statusline and the claude-hi session scheduler
```
