# Features

Complete reference for all cc-arsenal skills and optional features.

Skills are the single component type in this repository. Each skill lives in `skills/<name>/SKILL.md`; many bundle `references/`, `scripts/`, `assets/`, and `evals/` alongside it (see [Architecture](architecture.md) for the anatomy).

<!-- gen:skills-features start -->
<!-- generated: edit skills.sh.json or SKILL.md frontmatter, then run `make docs` -->

## Skills (48 total)

Every skill is callable as `/<name>` in Claude Code. **(auto)** marks skills that *also* trigger automatically when Claude detects a relevant task; **(manual)** marks slash-only skills (`disable-model-invocation: true`).

### AI Workflow Tools (7 skills)

Tools that work on your AI agent itself, not on your codebase.

#### `/agent-browser` (auto)
AI-optimized browser automation.
- 93% less context overhead vs Playwright
- Snapshot + refs system
- Web testing and automation

#### `/create-rule` (auto)
Create memory rules for Claude Code.
- CLAUDE.md guidelines
- Memory patterns

#### `/create-skill` (auto)
Specification-driven skill creation with live documentation fetching.
- Fetches latest specifications from agentskills.io
- Interactive clarification with user
- Multi-source example research
- User approval gates before file generation
- Also covers what `create-command` used to (they were merged)

#### `/find-skills` (manual)
Discover third-party skills from skills.sh.
- Skill discovery
- Installation automation
- Community skills

#### `/improve-skill` (auto)
Improve an existing skill to the authoring standard with measured before/after evidence.
- Snapshots the baseline, rewrites to the rubric, authors evals, benchmarks new-vs-old
- Per-dimension restraint gate: an already-compliant skill gets a small diff, not a fresh draft
- Reuses create-skill's validator; never commits (hands off to git-commit/ship)

#### `/render` (manual)
Turn a plan, PRD, review, audit, comparison, brainstorm, explanation or map into an interactive HTML page the user marks up in place.
- Eight modes; every section carries an anchored comment affordance, so feedback returns bound to what it was left on
- Wraps any other skill (`/render /review-code`) without that skill needing to change
- Publishes as an Artifact where available, otherwise writes a self-contained file

#### `/wtf` (auto)
Re-explains the previous message in plain, simplified English (ASD-STE100 style).
- Rewrites what was already said
- No new work, research, or code

### Art & Images (2 skills)

Mascots, logos, hero images, and social cards for a project.

#### `/codex-imagegen` (auto)
The default image generator: polished raster art (logos, mascots, heroes, icons, sprites, mockups) via Codex CLI's `$imagegen`.
- Codex `gpt-6-sol` + GPT Image 2.5 Sunburst `gpt-image-2.5-sunburst`
- Single-quoted invocation, effort budgeting, explicit save paths
- Chroma-key transparency handling (no-despill on pink), pixel-level QC

#### `/project-illustrator` (auto)
Cohesive visual identity for a software project across mascots, heroes, social cards, thumbnails, and supporting illustrations.
- Inspects the product and existing artwork before choosing a visual metaphor
- Presents three meaningful mascot directions when no identity is approved
- Extends the selected character through high-resolution masters and verified derivatives
- Preserves approved compositions during local repairs and checks final art at real display sizes

### Build (5 skills)

Write the feature, fix the bug, restructure the code, cover it with tests.

#### `/clotho-research` (manual)
Find what a change will actually touch before planning it.
- Surfaces the existing code that must change and prior art worth copying
- Reports files, sources, and risks; never proposes an implementation or edits anything

#### `/fix-bug` (auto)
Test-driven debugging with fix verification.
- Root cause analysis
- Regression testing
- Fix verification hook

#### `/implement-feature` (auto)
Feature implementation with parallel subagents and automated test verification.
- Parallel subagent orchestration
- Automated test verification
- SOLID, DRY, and YAGNI principles

#### `/refactor` (auto)
Safe codebase refactoring with characterization tests.
- Characterization test generation
- Safe refactoring patterns
- Regression prevention

#### `/test-suite` (auto)
Test generation and coverage analysis.
- Comprehensive test generation
- Coverage analysis and reporting

### Design (3 skills)

Screens, flows, and design tokens, plus an accessibility-grade UX audit.

#### `/product-design-spec` (manual)
Design specification for an approved PRD.
- Information architecture, user flows, screen inventory
- Per-screen state specs
- Reuses the existing component library; every screen traces to a requirement ID

#### `/product-design-tokens` (manual)
Durable design-token contract for a project.
- W3C DTCG 2025.10 JSON, plus an optional DESIGN.md
- Reuses the project's design system
- Enforces WCAG 2.2 AA contrast

#### `/review-design` (manual)
UX/UI design quality audit.
- Visual and interaction critique
- Accessibility basics
- Consistency checks

### Docs (6 skills)

Architecture records, RFCs, diagrams, and keeping docs honest about the code.

#### `/docs-adr` (manual)
Architecture Decision Records creation.
- ADR templates (full, lightweight, Nygard)
- Decision documentation
- Context and consequences

#### `/docs-check` (auto)
Documentation validation and health scoring.
- Freshness checks
- Completeness analysis
- Quality scoring

#### `/docs-diagram` (manual)
Architecture diagrams (Mermaid).
- System architecture
- Component diagrams
- Flow diagrams

#### `/docs-init` (manual)
Initialize comprehensive documentation structure.
- Standard documentation templates
- Best practices structure

#### `/docs-rfc` (manual)
Request for Comments documentation.
- RFC templates (detailed, minimal, standard)
- Proposal structure
- Review workflow

#### `/docs-update` (manual)
Documentation sync with codebase.
- Automatic update detection
- Sync recommendations
- Change tracking

### Git (4 skills)

Branch, commit, merge, and tag versions in your own repository.

#### `/git-commit` (auto)
Conventional commits with automated linting.
- Conventional Commits format
- Pre-commit linting hook
- Multi-language linter support

#### `/git-release` (auto)
Release management with automated changelog generation.
- Semantic versioning
- Automated changelog
- Release notes generation

#### `/git-sync` (auto)
Sync the current feature branch with its base or upstream branch.
- Merge or rebase, with conflict detection and stash handling

#### `/gitflow` (auto)
Manage a full gitflow branching workflow.
- Start/finish feature, release, and hotfix branches
- Cut versioned releases with changelog generation
- Emergency hotfix coordination

### GitHub (3 skills)

Open pull requests, drive a branch to merged, and take a project public.

#### `/git-create-pr` (auto)
PR creation with templates and test verification.
- PR templates
- Test verification hook
- Automated checklist

#### `/oss-launch` (auto)
Take a private project to a public GitHub launch.
- Secrets/license pre-flight, review-code fixes, branding, README/description rewrite
- Mention scrub (presents matches, never auto-edits) and a gated history rewrite (private-only, explicit confirm, refuses on already-public repos)
- Flips the repo public with topics set, reports a stage table of real commands

#### `/ship` (auto)
Orchestrates the current branch from "code done" to "merged".
- Runs review-code, project pre-merge checks, git-commit, then git-create-pr
- Optionally watches CI and reports or merges on green

### Jira (1 skill)

Jira from the command line.

#### `/jira-cli` (manual)
Interactive command-line tool for Jira.
- Issue management
- Sprint planning
- Epic tracking

### Multi-agent (1 skill)

Fan a large task out across parallel agents.

#### `/orchestrate` (auto)
Turn any task into a model-tiered multi-agent plan.
- Decompose, classify, map each subtask to the right model (haiku research, opus planning, sonnet impl)
- Parallel tracks under strict one-owner-per-file discipline; orchestrator does synthesis and git
- Declines to orchestrate trivial single-file tasks

### Product (3 skills)

Decide what to build and turn it into tracked, dependency-ordered work.

#### `/prd-to-issues` (manual)
Turn an approved PRD into tracked issues, one per requirement.
- Records the dependencies between issues
- Creates issues in beads or GitHub and reports what it created

#### `/product-prd` (manual)
Right-sized product requirements doc, from a gate-zero check to a full PRD.
- Gate-zero: does this idea even need a doc?
- Brief, one-pager, PR/FAQ, or full PRD by scope
- Mandatory non-goals and testable, traceable requirements

#### `/project-planner` (auto)
Break down large projects into dependency-aware tasks.
- Dependency graph generation
- Task breakdown with estimates
- Mermaid visualization

### Project setup (6 skills)

Containers, environment variables, database migrations, CI pipelines, framework docs.

#### `/ci-generate` (manual)
CI/CD workflow generator.
- GitHub Actions, GitLab CI, CircleCI, Jenkins
- Best practices templates
- Test integration

#### `/ci-local` (auto)
Runs the checks a GitHub Actions workflow would run, locally, when Actions is unavailable or out of quota.
- Parses `.github/workflows/*.yml` and replicates gating steps locally
- Reports a parity table of what could/couldn't be replicated

#### `/db-migrate` (auto)
Create, validate, and manage database migrations across any framework.
- Auto-detects Alembic, Prisma, Knex, Django, Flyway, Rails

#### `/docker-init` (manual)
Generate Dockerfiles and docker-compose.yml.
- Auto-detected services, health checks, security hardening, resource limits

#### `/env-setup` (manual)
Scan a codebase for environment variable usage.
- Generates/syncs `.env.example`, validates completeness, detects leaked secrets

#### `/inject-docs` (manual)
Framework documentation injector.
- Next.js via agents-md
- FastAPI via best practices
- Framework-specific patterns

### Review (7 skills)

Catch problems before they ship: code, plans, security, dependencies, performance, visual regressions, translations.

#### `/i18n-check` (auto)
i18n completeness checker.
- Detects the project's i18n framework and diffs locale files for missing/untranslated/orphan keys
- Scans for hardcoded user-facing strings bypassing the i18n layer

#### `/review-code` (auto)
Multi-agent PR code review with parallel specialists.
- Specialized review agents (correctness, performance, style, tests, error handling, simplicity)
- Comprehensive code quality analysis

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

#### `/review-plan` (manual)
Adversarially review an implementation plan before any code is written.
- Checks the plan against the actual repository, not on its own terms
- Assumes the plan is wrong and reports findings by severity

#### `/review-security` (manual)
OWASP Top 10 2025 security analysis.
- Automated vulnerability scanning
- OWASP compliance checking
- Security best practices

#### `/vrt-check` (auto)
Runs the project's visual regression testing workflow.
- Auto-detects VRT tooling (Playwright, Storybook, Chromatic, Loki, Percy)
- Triages failures as real regressions vs. intended changes
<!-- gen:skills-features end -->

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
🤖 Opus 5.5 │ 📊 66% │ 📁 ~/projects/cc-arsenal │ 🌿 main ● │ 💰 $3.169 │ ⏱️ 21m
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
- **Skills**: All 48 skills, or a focused variant (`cc-arsenal-dev`, `cc-arsenal-product`, `cc-arsenal-review`, `cc-arsenal-docs`, `cc-arsenal-git`, `cc-arsenal-jira`, `cc-arsenal-skills`)
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
