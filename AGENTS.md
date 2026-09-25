# AGENTS.md

This is the canonical, tool-agnostic guidance file for **cc-arsenal**. Any AGENTS.md-aware tool reads it natively, including Codex, Cursor, Copilot, Gemini CLI and OpenCode. Claude Code does not read this file directly; `CLAUDE.md` imports it via `@AGENTS.md` and adds Claude-Code-only content on top.

## Repository Architecture

cc-arsenal is a collection of **49 Agent Skills** ([agentskills.io](https://agentskills.io) open standard) for development workflow automation. `skills/` is the single canonical tier: every skill lives there once, written tool-neutral, and any tool that speaks the Agent Skills format can load it directly.

### Core Components

- **Skills** (`skills/`): 49 skills covering development, code review, documentation, git/GitHub, jira, browser automation, project planning, product specs, multi-agent orchestration, open-source launch prep, and skill discovery/creation/improvement
- **Scripts** (`scripts/`): Python utilities for installation and configuration, plus code generation (Claude-Code-specific; see `CLAUDE.md`)
- **Integrations** (`integrations/`): agent-CLI-specific tooling that doesn't fit the tool-agnostic `skills/` tier, one subdirectory per agent CLI. Today that's `integrations/claude-code/`, holding the statusline and the `claude-hi` session scheduler; future agent CLIs (Codex, Gemini CLI, ...) get sibling directories alongside it as their own tooling needs arise.

## Install in any agent

```bash
# Any Agent-Skills-compatible tool (Codex, Cursor, Gemini CLI, OpenCode, ...)
npx skills add mgiovani/cc-arsenal
```

`npx skills` is the [skills.sh](https://skills.sh) CLI: it copies each skill into the target tool's own skills directory, no plugin system required.

Using Claude Code? See `CLAUDE.md` for the plugin marketplace install and plugin variants, plus other Claude-Code-only extras.

## Portability convention

Skills in this repo are written **tool-neutral first**:

- Only `name` and `description` frontmatter are required for a skill to work anywhere.
- Claude-Code-only frontmatter keys (`allowed-tools`, `disable-model-invocation`, `hooks`, `context`, `agent`) are enhancement layers. Other tools ignore unknown frontmatter keys safely: a skill's correctness must never depend on them being honored.
- Orchestration skills (those that spawn subagents/parallel tasks in Claude Code) degrade gracefully to sequential inline execution when no subagent/task tool exists. The instructions describe the sequential fallback explicitly rather than assuming Task/Agent tools are always present.
- Paths and shell commands referenced inside a skill must be real, tool-independent commands (e.g. `git`, `gh`, `make`): never a Claude-Code-only tool name used as if it were a shell command.

## Skill composition

Skills may build on each other along two distinct axes, keep them separate:

- **Sibling invocation (borrow a *procedure*)**: a skill may invoke another skill by name to reuse its steps, via the Claude Code `Skill` tool where available. Because `Skill` is Claude-Code-only and other CLIs can only read a sibling's `SKILL.md` as text, **every such call must state the tool-neutral fallback in the same sentence**: apply the sibling's documented rules/steps inline. Announce it with a `Using <skill> to <purpose>` line. For example: "use the `git-commit` skill to write the message (via the `Skill` tool where available, otherwise apply its conventional-commit rules inline)".
- **Subagent delegation (spawn a *role*)**: a skill may fan work out to a subagent via the Claude Code `Task`/`Agent` tools. This is the orchestration path the Portability convention already covers, and it degrades to sequential inline execution when no subagent tool exists.

Do not add `uses:`/`composes:` frontmatter and do not route composition through a mandatory dispatcher skill: plain prose naming the sibling, with its in-sentence fallback, is the whole mechanism.

<!-- gen:skills-agents start -->
<!-- generated: edit skills.sh.json or SKILL.md frontmatter, then run `make docs` -->

## Available Skills (49 total)

All skills use progressive disclosure (SKILL.md + optional references/scripts/assets directories).

### AI Workflow Tools (8 skills)

Tools that work on your AI agent itself, not on your codebase.

- `agent-browser`: AI-optimized browser automation with far less context overhead than raw Playwright/DOM tools
- `create-rule`: Create CLAUDE.md/AGENTS.md rules and memory guidelines
- `create-skill`: Specification-driven skill creation with eval system and description optimization
- `find-skills`: Discover and install third-party agent skills from skills.sh
- `improve-skill`: Rewrite an existing skill to the authoring standard, with baseline-vs-new eval evidence
- `optimize-ai-setup`: Measure token waste across installed AI coding tools and rank the fixes
- `render`: Turn any output into an interactive HTML page you mark up in place, then read the marks back
- `wtf`: Re-explain your own previous message in plain, simplified English (ASD-STE100 style) when the user didn't understand it

### Art & Images (2 skills)

Mascots and logos, plus hero images and social cards for a project.

- `codex-imagegen`: Polished raster art (logos, mascots, heroes, sprites, mockups) via Codex CLI's $imagegen
- `project-illustrator`: A cohesive art system for a project: mascot, heroes, social cards and thumbnails with one character

### Build (5 skills)

Feature work and bug fixes, plus refactors and test coverage for code you already have.

- `clotho-research`: Find what a change will actually touch before planning it: the code and prior art it meets, and the risks it carries
- `fix-bug`: Test-driven debugging with strict sequential task chain and dependency enforcement
- `implement-feature`: Feature implementation with senior staff engineer best practices and parallel subagent orchestration where available
- `refactor`: Restructure existing code without changing behavior, verified against the full test suite at each step
- `test-suite`: Generate test suites by analyzing coverage gaps and writing tests that match project conventions

### Design (3 skills)

Screens and flows, alongside design tokens and an accessibility-grade UX audit.

- `product-design-spec`: Information architecture, user flows, screen inventory and per-screen states for an approved PRD
- `product-design-tokens`: A durable W3C DTCG design-token contract, reusing your design system and enforcing WCAG 2.2 AA contrast
- `review-design`: UX/UI/design quality audit mapped to WCAG 2.2 AA plus the Material Design 3 and Apple HIG guidelines

### Docs (6 skills)

Architecture records and RFCs, plus diagrams and keeping docs honest about the code.

- `docs-adr`: Architecture Decision Records creation and management
- `docs-check`: Documentation validation and health scoring
- `docs-diagram`: Architecture diagrams generation (Mermaid)
- `docs-init`: Documentation structure initialization
- `docs-rfc`: Request for Comments documentation
- `docs-update`: Documentation sync with codebase state

### Git (4 skills)

Branching and committing, plus merging and tagging versions in your own repository.

- `git-commit`: Conventional commit message generation
- `git-release`: Semantic version releases with automated changelog generation
- `git-sync`: Sync the current feature branch with its base/upstream via merge or rebase
- `gitflow`: Manage a gitflow branching workflow (feature/release/hotfix branches)

### GitHub (3 skills)

Pull requests and merges, then taking a project public.

- `git-create-pr`: Pull request creation with standardized formats
- `oss-launch`: Take a private project public: secrets and license pre-flight, branding, README rewrite, then flip it
- `ship`: Orchestrates a branch from "code done" to "merged" (runs review-code plus project-specific pre-merge checks)

### Jira (1 skill)

Jira from the command line.

- `jira-cli`: Interactive command-line tool for Atlassian Jira

### Multi-agent (1 skill)

Fan a large task out across parallel agents.

- `orchestrate`: Decompose a task, map each part to the right model, run independent tracks in parallel, then synthesize

### Product (3 skills)

Decide what to build and turn it into tracked, dependency-ordered work.

- `prd-to-issues`: Turn an approved PRD into tracked issues, one per requirement ID, with dependencies recorded
- `product-prd`: Right-sized PRD from an idea: brief, one-pager, PR/FAQ or full doc, with non-goals and testable requirements
- `project-planner`: Break down large projects into dependency-aware tasks with Mermaid visualization

### Project setup (6 skills)

Containers and environment variables, database migrations and CI pipelines, as well as framework docs.

- `ci-generate`: Generate a production-ready CI/CD pipeline config (GitHub Actions, GitLab CI, CircleCI, Jenkins)
- `ci-local`: Run the checks a GitHub Actions workflow would run, locally, when Actions is unavailable
- `db-migrate`: Create and validate database migrations, then manage them across any framework
- `docker-init`: Generate Dockerfiles and docker-compose.yml with auto-detected services and security hardening
- `env-setup`: Scan a codebase for env var usage, sync .env.example, and detect leaked secrets
- `inject-docs`: Inject compressed framework-specific best practices and docs into CLAUDE.md/AGENTS.md

### Review (7 skills)

Code and plans, security and dependencies, performance and visual regressions, and translations.

- `i18n-check`: i18n completeness checker, detects the project's i18n framework and diffs locale files
- `review-code`: Multi-agent code review across six dimensions, from correctness and performance to tests and error handling
- `review-deps`: Audit dependencies for vulnerabilities, license risk, and staleness
- `review-perf`: Deep-dive performance audit of queries, algorithmic complexity, and resource leaks
- `review-plan`: Adversarially review an implementation plan against the actual repository before any code is written
- `review-security`: OWASP Top 10 2025 security analysis with parallel scanning agents where available
- `vrt-check`: Runs the project's visual regression testing workflow, whatever tooling the repo actually uses
<!-- gen:skills-agents end -->

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
1. **Metadata** (name + description): always in context (~100 words)
2. **SKILL.md body**: loaded when the skill activates (<5k words)
3. **Bundled resources**: loaded only when the agent needs them

### Eval Convention

Each skill's `evals/evals.json` lists concrete scenarios (`id`, `prompt`, `assertions`) that a run of the skill must satisfy, used to catch regressions when a SKILL.md is edited. `evals/trigger-eval.json` instead tests description-triggering: given a set of realistic user prompts, does the skill's frontmatter `description` cause it to fire (or correctly not fire)? Use the `create-skill` skill's eval tooling to run either against a live agent.

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
2. **Develop** your skill or change: new skills go under `skills/<name>/SKILL.md`; keep frontmatter to `name` + `description` plus a one-line `metadata.summary` (what the generated catalogs show), unless the skill genuinely needs a Claude-Code-only key (see Portability convention above)
3. **Assign it a group** in `skills.sh.json`, the single source of truth for how skills are grouped on skills.sh and in every catalog in this repo. `make docs` then regenerates the lists in `README.md`, `AGENTS.md` and `docs/features.md`; `make check` fails if you forget. Every skill must belong to exactly one group
4. **Add evals**: new or changed skills should ship an `evals/evals.json` (and `trigger-eval.json` if the description changed)
5. **Validate** with `make check` and `make validate-structure` / `make validate-plugins`
6. **Update CHANGELOG.md** for user-facing changes
7. **Submit** a pull request with a clear description

See `CONTRIBUTING.md` for the full development setup.

## File Organization
```
cc-arsenal/
├── skills/          # All 49 skills (canonical, tool-agnostic)
│   └── <name>/          # SKILL.md + optional references/, scripts/, assets/, evals/
├── scripts/         # Installation and utilities (see CLAUDE.md for Claude-Code-specific ones)
└── integrations/    # Agent-CLI-specific tooling, one subdirectory per agent CLI
    └── claude-code/     # Statusline and the claude-hi session scheduler
```
