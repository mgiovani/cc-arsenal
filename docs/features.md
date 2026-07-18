# Features

Complete reference for all cc-arsenal skills and optional features.

Skills are the single component type in this repository (the legacy `commands/` format was retired). Each skill lives in `skills/<name>/SKILL.md`; many bundle `references/`, `scripts/`, `assets/`, and `evals/` alongside it (see [Architecture](architecture.md) for the anatomy).

## Skills (45 total)

### Development (21 skills)

#### `/implement-feature`
Feature implementation with parallel subagents and automated test verification.
- Parallel subagent orchestration
- Automated test verification
- SOLID, DRY, and YAGNI principles

#### `/fix-bug`
Test-driven debugging with fix verification.
- Root cause analysis
- Regression testing
- Fix verification hook

#### `test-suite` (model-invoked)
Test generation and coverage analysis.
- Comprehensive test generation
- Coverage analysis and reporting

#### `refactor` (model-invoked)
Safe codebase refactoring with characterization tests.
- Characterization test generation
- Safe refactoring patterns
- Regression prevention

#### `/review-code`
Multi-agent PR code review with parallel specialists.
- Specialized review agents (correctness, performance, style, tests, error handling, simplicity)
- Comprehensive code quality analysis

#### `/review-security`
OWASP Top 10 2025 security analysis.
- Automated vulnerability scanning
- OWASP compliance checking
- Security best practices

#### `/review-deps`
Dependency audit, vulnerability scanning, and upgrade planning.
- Vulnerability detection
- Upgrade recommendations
- Dependency health scoring

#### `/review-perf`
Performance analysis with parallel agents.
- Database optimization
- Algorithm analysis
- Frontend performance
- Resource optimization

#### `/review-design`
UX/UI design quality audit.
- Visual and interaction critique
- Accessibility basics
- Consistency checks

#### `/ci-generate`
CI/CD workflow generator.
- GitHub Actions, GitLab CI, CircleCI, Jenkins
- Best practices templates
- Test integration

#### `ci-local` (model-invoked)
Runs the checks a GitHub Actions workflow would run, locally, when Actions is unavailable or out of quota.
- Parses `.github/workflows/*.yml` and replicates gating steps locally
- Reports a parity table of what could/couldn't be replicated

#### `/inject-docs`
Framework documentation injector.
- Next.js via agents-md
- FastAPI via best practices
- Framework-specific patterns

#### `/project-planner`
Break down large projects into dependency-aware tasks.
- Dependency graph generation
- Task breakdown with estimates
- Mermaid visualization

#### `nanobanana` (model-invoked)
Generate and edit images using Nano Banana (Gemini image generation).
- Creates visuals, mockups, thumbnails, logos, hero images

#### `codex-imagegen` (model-invoked)
Generate polished raster art (logos, mascots, heroes, sprites, mockups) via Codex CLI's `$imagegen`.
- Single-quoted invocation, effort budgeting, explicit save paths
- Chroma-key transparency handling (no-despill on pink), pixel-level QC
- Routes quick/photorealistic requests to nanobanana

#### `oss-launch` (model-invoked)
Take a private project to a public GitHub launch.
- Secrets/license pre-flight, review-code fixes, branding, README/description rewrite
- Mention scrub (presents matches, never auto-edits) and a gated history rewrite (private-only, explicit confirm, refuses on already-public repos)
- Flips the repo public with topics set, reports a stage table of real commands

#### `vrt-check` (model-invoked)
Runs the project's visual regression testing workflow.
- Auto-detects VRT tooling (Playwright, Storybook, Chromatic, Loki, Percy)
- Triages failures as real regressions vs. intended changes

#### `i18n-check` (model-invoked)
i18n completeness checker.
- Detects the project's i18n framework and diffs locale files for missing/untranslated/orphan keys
- Scans for hardcoded user-facing strings bypassing the i18n layer

#### `db-migrate` (user-invoked)
Create, validate, and manage database migrations across any framework.
- Auto-detects Alembic, Prisma, Knex, Django, Flyway, Rails

#### `docker-init` (user-invoked)
Generate Dockerfiles and docker-compose.yml.
- Auto-detected services, health checks, security hardening, resource limits

#### `env-setup` (user-invoked)
Scan a codebase for environment variable usage.
- Generates/syncs `.env.example`, validates completeness, detects leaked secrets

### Documentation (6 skills)

#### `/docs-init`
Initialize comprehensive documentation structure.
- Standard documentation templates
- Best practices structure

#### `/docs-adr`
Architecture Decision Records creation.
- ADR templates (full, lightweight, Nygard)
- Decision documentation
- Context and consequences

#### `/docs-rfc`
Request for Comments documentation.
- RFC templates (detailed, minimal, standard)
- Proposal structure
- Review workflow

#### `/docs-diagram`
Architecture diagrams (Mermaid).
- System architecture
- Component diagrams
- Flow diagrams

#### `/docs-check`
Documentation validation and health scoring.
- Freshness checks
- Completeness analysis
- Quality scoring

#### `/docs-update`
Documentation sync with codebase.
- Automatic update detection
- Sync recommendations
- Change tracking

### Git & GitHub (7 skills)

#### `/git-commit`
Conventional commits with automated linting.
- Conventional Commits format
- Pre-commit linting hook
- Multi-language linter support

#### `/git-create-pr`
PR creation with templates and test verification.
- PR templates
- Test verification hook
- Automated checklist

#### `/git-release`
Release management with automated changelog generation.
- Semantic versioning
- Automated changelog
- Release notes generation

#### `gitflow` (model-invoked)
Manage a full gitflow branching workflow.
- Start/finish feature, release, and hotfix branches
- Cut versioned releases with changelog generation
- Emergency hotfix coordination

#### `git-sync` (user-invoked)
Sync the current feature branch with its base or upstream branch.
- Merge or rebase, with conflict detection and stash handling

#### `ship` (model-invoked)
Orchestrates the current branch from "code done" to "merged".
- Runs review-code, project pre-merge checks, git-commit, then git-create-pr
- Optionally watches CI and reports or merges on green

#### `/gh-daily`
GitHub Issues daily planner with priority scoring.
- Priority scoring algorithm
- Daily task planning
- Issue organization

### Jira (2 skills)

#### `/jira-daily`
Standup report generator with activity analysis.
- Activity analysis
- Report generation
- Status tracking

#### `/jira-todo`
Work prioritization planner with intelligent prioritization.
- Intelligent prioritization
- Task recommendations
- Workload balancing

### Teams (2 skills)

#### `team-implement` (model-invoked)
Spec-driven team orchestration (3-11 agents).
- Adaptive team scaling
- Spec-driven development
- Multi-phase workflow

#### `team-review` (model-invoked)
Multi-agent PR review team.
- Specialized reviewers
- Adversary reviewer
- Comprehensive analysis

### Specialty (7 skills)

#### `agent-browser` (model-invoked)
AI-optimized browser automation.
- 93% less context overhead vs Playwright
- Snapshot + refs system
- Web testing and automation

#### `find-skills` (model-invoked)
Discover third-party skills from skills.sh.
- Skill discovery
- Installation automation
- Community skills

#### `jira-cli` (model-invoked)
Interactive command-line tool for Jira.
- Issue management
- Sprint planning
- Epic tracking

#### `create-skill` (model-invoked)
Specification-driven skill creation with live documentation fetching.
- Fetches latest specifications from agentskills.io
- Interactive clarification with user
- Multi-source example research
- User approval gates before file generation
- Also covers what `create-command` used to (they were merged)

#### `create-rule` (user-invoked)
Create memory rules for Claude Code.
- CLAUDE.md guidelines
- Memory patterns

#### `improve-skill` (model-invoked)
Improve an existing skill to the authoring standard with measured before/after evidence.
- Snapshots the baseline, rewrites to the rubric, authors evals, benchmarks new-vs-old
- Per-dimension restraint gate — an already-compliant skill gets a small diff, not a fresh draft
- Reuses create-skill's validator; never commits (hands off to git-commit/ship)

#### `orchestrate` (model-invoked)
Turn any task into a model-tiered multi-agent plan.
- Decompose, classify, map each subtask to the right model (haiku research, opus planning, sonnet impl)
- Parallel tracks under strict one-owner-per-file discipline; orchestrator does synthesis and git
- Declines to orchestrate trivial single-file tasks

## Optional Features

### Statusline

Real-time cost and usage tracking in your Claude Code prompt.

**Shows:**
- Model name and version
- Current directory
- Git branch with uncommitted changes (●)
- Git worktree name
- Context window usage percentage
- Session costs
- Lines changed (+added/-removed)
- Session duration
- Time until 5-hour reset

**Example:**
```
🤖 Opus 4.5 │ 📁 ~/projects/cc-arsenal │ 🌿 main ● │ 📊 66% │ 💰 $3.169 │ 📝 +719/-545 │ ⏱️ 21m │ 🔄 4h 23m until reset at 13:00
```

**Installation:**
```bash
make install-statusline
```

**Documentation:** [Statusline Guide](../scripts/claude/statusline/STATUSLINE.md)

### Claude Hi Scheduler

Automatically start fresh 5-hour windows before your peak coding times.

**Features:**
- Preset schedules (9am/2pm/7pm standard)
- Custom schedule creation
- Automated window triggers
- Peak productivity optimization

**Installation:**
```bash
make -C scripts/claude-hi setup     # Interactive setup
make -C scripts/claude-hi standard  # Quick 9am/2pm/7pm schedule
```

**Documentation:** [Claude Hi Guide](../scripts/claude-hi/README.md)

## Installation Options

### Plugin Marketplace (Claude Code)
- **Installation**: `/plugin install cc-arsenal@cc-arsenal-marketplace`
- **Skills**: All 45 skills, or a focused variant (`cc-arsenal-dev`, `cc-arsenal-docs`, `cc-arsenal-git`, `cc-arsenal-skills`, `cc-arsenal-teams`, `cc-arsenal-review`)
- See [Getting Started](getting-started.md) for the full variant list

### Symlink Install (Contributors)
- **Use case**: Developing cc-arsenal itself
- **Installation**: `make install` (or `make configure` to select specific skills)

## Using with Other Agents

cc-arsenal skills follow the open [Agent Skills standard](https://agentskills.io): a `SKILL.md` with just `name` + `description` frontmatter is portable to any tool that supports it, not only Claude Code.

**Install for any agent:**
```bash
npx skills add mgiovani/cc-arsenal
```

**Per-tool install directories** (where the CLI places skill files):
- Claude Code: `.claude/skills/`
- Other agents (Codex, Cursor, OpenCode, Gemini CLI, etc.): `.agents/skills/`

**Claude Code-only features** (ignored by other tools, since they read only `name`/`description`):
- Plugin variants via `/plugin marketplace add mgiovani/cc-arsenal` (`.claude-plugin/marketplace.json`)
- `hooks`, `allowed-tools`, `disable-model-invocation`, `context`, `agent` frontmatter keys
- Statusline and Claude Hi scheduler (see Optional Features above)
- Subagent (Task tool) orchestration used by skills like `implement-feature` and `review-code`

There is no separate "base" skill set to keep in sync — the same `skills/<name>/SKILL.md` files serve both the agnostic and Claude Code-enhanced use cases.

## Model-Invoked vs User-Invoked Skills

**User-Invoked** (slash commands):
- Triggered explicitly by user (e.g., `/git-commit`, `/docs-adr`)
- Workflow automation for specific tasks

**Model-Invoked** (automatic):
- Claude detects context and loads automatically
- No confirmation dialogs
- Examples: `agent-browser`, `jira-cli`, `create-skill`, `find-skills`, `test-suite`, `refactor`, `ship`, `ci-local`, `nanobanana`, `vrt-check`, `i18n-check`

The exact split is defined per-skill by the `disable-model-invocation` frontmatter field — see [Architecture](architecture.md) for the current authoritative count, since it changes as skills are added.
