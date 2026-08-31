# Features

Complete reference for all cc-arsenal skills and optional features.

Skills are the single component type in this repository. Each skill lives in `skills/<name>/SKILL.md`; many bundle `references/`, `scripts/`, `assets/`, and `evals/` alongside it (see [Architecture](architecture.md) for the anatomy).

## Skills (46 total)

Every skill is callable as `/<name>` in Claude Code. **(auto)** marks skills that *also* trigger automatically when Claude detects a relevant task; **(manual)** marks slash-only skills (`disable-model-invocation: true`).

### Development (21 skills)

#### `/implement-feature` (auto)
Feature implementation with parallel subagents and automated test verification.
- Parallel subagent orchestration
- Automated test verification
- SOLID, DRY, and YAGNI principles

#### `/fix-bug` (auto)
Test-driven debugging with fix verification.
- Root cause analysis
- Regression testing
- Fix verification hook

#### `/test-suite` (auto)
Test generation and coverage analysis.
- Comprehensive test generation
- Coverage analysis and reporting

#### `/refactor` (auto)
Safe codebase refactoring with characterization tests.
- Characterization test generation
- Safe refactoring patterns
- Regression prevention

#### `/review-code` (auto)
Multi-agent PR code review with parallel specialists.
- Specialized review agents (correctness, performance, style, tests, error handling, simplicity)
- Comprehensive code quality analysis

#### `/review-security` (manual)
OWASP Top 10 2025 security analysis.
- Automated vulnerability scanning
- OWASP compliance checking
- Security best practices

#### `/review-deps` (manual)
Dependency audit, vulnerability scanning, and upgrade planning.
- Vulnerability detection
- Upgrade recommendations
- Dependency health scoring

#### `/review-perf` (manual)
Performance analysis with parallel agents.
- Database optimization
- Algorithm analysis
- Frontend performance
- Resource optimization

#### `/review-design` (manual)
UX/UI design quality audit.
- Visual and interaction critique
- Accessibility basics
- Consistency checks

#### `/ci-generate` (manual)
CI/CD workflow generator.
- GitHub Actions, GitLab CI, CircleCI, Jenkins
- Best practices templates
- Test integration

#### `/ci-local` (auto)
Runs the checks a GitHub Actions workflow would run, locally, when Actions is unavailable or out of quota.
- Parses `.github/workflows/*.yml` and replicates gating steps locally
- Reports a parity table of what could/couldn't be replicated

#### `/inject-docs` (manual)
Framework documentation injector.
- Next.js via agents-md
- FastAPI via best practices
- Framework-specific patterns

#### `/project-planner` (auto)
Break down large projects into dependency-aware tasks.
- Dependency graph generation
- Task breakdown with estimates
- Mermaid visualization

#### `/nanobanana` (auto)
Generate and edit images via the Nano Banana / Gemini API (a real, billed call).
- Fires only on explicit mentions (nano banana, GEMINI_API_KEY); `codex-imagegen` is the default for generic image requests

#### `/codex-imagegen` (auto)
The default image generator: polished raster art (logos, mascots, heroes, icons, sprites, mockups) via Codex CLI's `$imagegen`.
- Single-quoted invocation, effort budgeting, explicit save paths
- Chroma-key transparency handling (no-despill on pink), pixel-level QC

#### `/oss-launch` (auto)
Take a private project to a public GitHub launch.
- Secrets/license pre-flight, review-code fixes, branding, README/description rewrite
- Mention scrub (presents matches, never auto-edits) and a gated history rewrite (private-only, explicit confirm, refuses on already-public repos)
- Flips the repo public with topics set, reports a stage table of real commands

#### `/vrt-check` (auto)
Runs the project's visual regression testing workflow.
- Auto-detects VRT tooling (Playwright, Storybook, Chromatic, Loki, Percy)
- Triages failures as real regressions vs. intended changes

#### `/i18n-check` (auto)
i18n completeness checker.
- Detects the project's i18n framework and diffs locale files for missing/untranslated/orphan keys
- Scans for hardcoded user-facing strings bypassing the i18n layer

#### `/db-migrate` (auto)
Create, validate, and manage database migrations across any framework.
- Auto-detects Alembic, Prisma, Knex, Django, Flyway, Rails

#### `/docker-init` (manual)
Generate Dockerfiles and docker-compose.yml.
- Auto-detected services, health checks, security hardening, resource limits

#### `/env-setup` (manual)
Scan a codebase for environment variable usage.
- Generates/syncs `.env.example`, validates completeness, detects leaked secrets

### Documentation (6 skills)

#### `/docs-init` (manual)
Initialize comprehensive documentation structure.
- Standard documentation templates
- Best practices structure

#### `/docs-adr` (manual)
Architecture Decision Records creation.
- ADR templates (full, lightweight, Nygard)
- Decision documentation
- Context and consequences

#### `/docs-rfc` (manual)
Request for Comments documentation.
- RFC templates (detailed, minimal, standard)
- Proposal structure
- Review workflow

#### `/docs-diagram` (manual)
Architecture diagrams (Mermaid).
- System architecture
- Component diagrams
- Flow diagrams

#### `/docs-check` (auto)
Documentation validation and health scoring.
- Freshness checks
- Completeness analysis
- Quality scoring

#### `/docs-update` (manual)
Documentation sync with codebase.
- Automatic update detection
- Sync recommendations
- Change tracking

### Git & GitHub (7 skills)

#### `/git-commit` (auto)
Conventional commits with automated linting.
- Conventional Commits format
- Pre-commit linting hook
- Multi-language linter support

#### `/git-create-pr` (auto)
PR creation with templates and test verification.
- PR templates
- Test verification hook
- Automated checklist

#### `/git-release` (auto)
Release management with automated changelog generation.
- Semantic versioning
- Automated changelog
- Release notes generation

#### `/gitflow` (auto)
Manage a full gitflow branching workflow.
- Start/finish feature, release, and hotfix branches
- Cut versioned releases with changelog generation
- Emergency hotfix coordination

#### `/git-sync` (auto)
Sync the current feature branch with its base or upstream branch.
- Merge or rebase, with conflict detection and stash handling

#### `/ship` (auto)
Orchestrates the current branch from "code done" to "merged".
- Runs review-code, project pre-merge checks, git-commit, then git-create-pr
- Optionally watches CI and reports or merges on green

#### `/gh-daily` (manual)
GitHub Issues daily planner with priority scoring.
- Priority scoring algorithm
- Daily task planning
- Issue organization

### Jira (2 skills)

#### `/jira-daily` (manual)
Standup report generator with activity analysis.
- Activity analysis
- Report generation
- Status tracking

#### `/jira-todo` (manual)
Work prioritization planner with intelligent prioritization.
- Intelligent prioritization
- Task recommendations
- Workload balancing

### Teams (2 skills)

#### `/team-implement` (manual)
Spec-driven team orchestration (3-11 agents).
- Adaptive team scaling
- Spec-driven development
- Multi-phase workflow

#### `/team-review` (manual)
Multi-agent PR review team.
- Specialized reviewers
- Adversary reviewer
- Comprehensive analysis

### Utilities (8 skills)

#### `/agent-browser` (auto)
AI-optimized browser automation.
- 93% less context overhead vs Playwright
- Snapshot + refs system
- Web testing and automation

#### `/find-skills` (manual)
Discover third-party skills from skills.sh.
- Skill discovery
- Installation automation
- Community skills

#### `/jira-cli` (manual)
Interactive command-line tool for Jira.
- Issue management
- Sprint planning
- Epic tracking

#### `/create-skill` (auto)
Specification-driven skill creation with live documentation fetching.
- Fetches latest specifications from agentskills.io
- Interactive clarification with user
- Multi-source example research
- User approval gates before file generation
- Also covers what `create-command` used to (they were merged)

#### `/create-rule` (auto)
Create memory rules for Claude Code.
- CLAUDE.md guidelines
- Memory patterns

#### `/improve-skill` (auto)
Improve an existing skill to the authoring standard with measured before/after evidence.
- Snapshots the baseline, rewrites to the rubric, authors evals, benchmarks new-vs-old
- Per-dimension restraint gate: an already-compliant skill gets a small diff, not a fresh draft
- Reuses create-skill's validator; never commits (hands off to git-commit/ship)

#### `/orchestrate` (auto)
Turn any task into a model-tiered multi-agent plan.
- Decompose, classify, map each subtask to the right model (haiku research, opus planning, sonnet impl)
- Parallel tracks under strict one-owner-per-file discipline; orchestrator does synthesis and git
- Declines to orchestrate trivial single-file tasks

#### `/render` (manual)
Turn a plan, PRD, review, audit, comparison, brainstorm, explanation or map into an interactive HTML page the user marks up in place.
- Eight modes; every section carries an anchored comment affordance, so feedback returns bound to what it was left on
- Wraps any other skill (`/render /review-code`) without that skill needing to change
- Publishes as an Artifact where available, otherwise writes a self-contained file

## Optional Features

### Statusline

Real-time cost and usage tracking in your Claude Code prompt, computed fresh on each call, no background daemon.

**Shows:**
- Model name and version
- Current directory
- Git branch with uncommitted changes (●)
- Git worktree name
- Context window usage percentage
- Session costs
- Lines changed (+added/-removed), disabled by default, enable via `make configure`
- Session duration
- 5-hour and 7-day usage windows (second line)
- Optional multi-account badge when `CLAUDE_CODE_OAUTH_TOKEN`/`CLAUDE_STATUSLINE_ACCOUNT_LABEL` are set

**Example:**
```
🤖 Opus 5 │ 📊 66% │ 📁 ~/projects/cc-arsenal │ 🌿 main ● │ 💰 $3.169 │ ⏱️ 21m
🔄 5h: 16% → 21:00 │ 📅 7d: 39% → Dec 31 21:00
```

**Installation:**
```bash
make install-statusline
```

**Documentation:** [Statusline Guide](../integrations/claude-code/statusline/STATUSLINE.md)

### Claude Hi Scheduler

Automatically start fresh 5-hour windows before your peak coding times.

**Features:**
- Preset schedules (9am/2pm/7pm standard)
- Custom schedule creation
- Automated window triggers
- Peak productivity optimization

**Installation:**
```bash
make -C integrations/claude-code/claude-hi setup     # Interactive setup
make -C integrations/claude-code/claude-hi standard  # Quick 9am/2pm/7pm schedule
```

**Documentation:** [Claude Hi Guide](../integrations/claude-code/claude-hi/README.md)

## Installation Options

### Plugin Marketplace (Claude Code)
- **Installation**: `/plugin install cc-arsenal@cc-arsenal-marketplace`
- **Skills**: All 46 skills, or a focused variant (`cc-arsenal-dev`, `cc-arsenal-docs`, `cc-arsenal-git`, `cc-arsenal-skills`, `cc-arsenal-teams`, `cc-arsenal-review`)
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

The same `skills/<name>/SKILL.md` files serve both the agnostic and Claude Code-enhanced use cases.

## Auto-trigger vs. manual skills

In Claude Code every skill is callable as `/<name>`. The only difference is whether Claude may *also* load it automatically:

- **(auto)**: auto-triggers when Claude detects a relevant task (no confirmation dialog) *and* runs as `/<name>`.
- **(manual)**: `/<name>` only; `disable-model-invocation: true` in the skill's frontmatter suppresses auto-triggering.

The split is defined per-skill by the `disable-model-invocation` frontmatter field (authoritative); see [Architecture](architecture.md) for the current count, since it changes as skills are added.
