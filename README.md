# Claude Code Arsenal

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Tools to make Claude Code more useful: track your usage costs, schedule optimal coding windows, and automate common workflows.

## What's included

**31 Skills** - Workflow automation for development, docs, git, github, code review, testing, and more
- Development: feature implementation, bug fixing, testing, refactoring, code review, security review, dependency audit, performance analysis, CI/CD generation, project planning
- Documentation: ADR, RFC, diagrams, init, check, update
- Git & GitHub: conventional commits, PR creation, release management, GitHub Issues daily planner
- Jira: daily standup reports and work prioritization
- Teams: spec-driven development team and multi-agent PR review team (experimental)
- Browser automation, skill discovery, and more
- Easy to customize or create your own

**Statusline** - Track your usage and costs in real-time (optional)
- Shows costs, context usage, and time until reset
- Git branch and worktree info
- Example: `🤖 Opus 4.5 │ 📁 cc-arsenal │ 🌿 main │ 📊 22% │ 💰 $0.043 │ 🔄 2h15m`

**Claude Hi Scheduler** - Maximize your 5-hour usage windows (optional)
- Auto-triggers fresh windows at optimal times
- Choose from preset schedules or customize your own
- Perfect for planning intensive coding sessions

## Installation

### Option 1: Claude Code Plugin (recommended)

Add the marketplace and select which plugins to install:
```bash
/plugin marketplace add mgiovani/cc-arsenal
```

This opens the plugin browser where you can select:

| Plugin | What's Included | Best For |
|--------|----------------|----------|
| **cc-arsenal** | All 31 skills | Complete workflow automation |
| **cc-arsenal-dev** | implement-feature, fix-bug, test-suite, refactor, review-code, review-security, review-deps, review-perf, ci-generate, inject-nextjs-docs, project-planner | Development workflows with code quality, testing, and CI/CD |
| **cc-arsenal-docs** | docs-adr, docs-check, docs-diagram, docs-init, docs-rfc, docs-update | Documentation generation |
| **cc-arsenal-git** | git-commit, git-create-pr, git-release, gh-daily | Git & GitHub workflows: commits, PRs, releases, issue planning |
| **cc-arsenal-review** | review-code, review-security, review-deps, review-perf | Code review, security, dependencies, performance analysis |
| **cc-arsenal-skills** | agent-browser, jira-cli, skill-creator, find-skills | Specialty model-invoked capabilities |
| **cc-arsenal-teams** | team-implement, team-review | Spec-driven team orchestration (experimental) |

> **Plugin Variants Pattern:** All variants install from the same repository but load different subsets of skills. Install the complete toolkit OR pick individual variants based on your needs. You can also install multiple variants together (e.g., git + docs).

**Quick install (complete toolkit):**
```bash
/plugin install cc-arsenal@cc-arsenal-marketplace
```

After installing, use skills like `/cc-arsenal:git-commit`, `/cc-arsenal:docs-adr`, `/cc-arsenal:implement-feature`, etc. Specialty skills (agent-browser, jira-cli, etc.) activate automatically when relevant.

### Option 2: Agent Skills (`npx skills`)

Install skills using the open [Agent Skills](https://skills.sh) ecosystem. Works with Claude Code, Cursor, Codex, and 30+ other AI agents:

```bash
# Install all skills
npx skills add mgiovani/cc-arsenal

# List available skills first
npx skills add mgiovani/cc-arsenal --list

# Install a specific skill
npx skills add mgiovani/cc-arsenal --skill agent-browser

# Install globally (available across all projects)
npx skills add mgiovani/cc-arsenal -g
```

## Optional Features

After installation, add these features if you want them:

**Statusline** (track usage, cost, and other useful info):
```bash
make statusline-install
```

**Claude Hi Scheduler** (manage 5-hour windows):
```bash
make claude-hi-setup      # Interactive setup
make claude-hi-standard   # Quick 9am/2pm/7pm schedule
```

## Features

### 🛠️ Skills

All 31 skills organized by category:

**Development** (11 skills):
- `/implement-feature` - Feature implementation with parallel subagents and automated test verification
- `/fix-bug` - Test-driven debugging with fix verification
- `/test-suite` - Test generation and coverage analysis (model-invoked)
- `/refactor` - Safe codebase refactoring with characterization tests (model-invoked)
- `/review-code` - Multi-agent PR code review with 5 parallel specialists
- `/review-security` - OWASP Top 10 2025 security analysis
- `/review-deps` - Dependency audit, vulnerability scanning, and upgrade planning
- `/review-perf` - Performance analysis with 4 parallel agents (database, algorithm, frontend, resources)
- `/ci-generate` - CI/CD workflow generator (GitHub Actions, GitLab CI, CircleCI, Jenkins)
- `/inject-nextjs-docs` - Next.js agents-md codemod
- `/project-planner` - Break down large projects into dependency-aware tasks

**Documentation** (6 skills):
- `/docs-init`, `/docs-adr`, `/docs-rfc`, `/docs-diagram`, `/docs-check`, `/docs-update`

**Git & GitHub** (4 skills):
- `/git-commit` - Conventional commits with automated linting
- `/git-create-pr` - PR with templates and test verification
- `/git-release` - Release management with automated changelog generation
- `/gh-daily` - GitHub Issues daily planner with priority scoring

**Jira** (2 skills):
- `/jira-daily` - Standup report generator
- `/jira-todo` - Work prioritization planner

**Claude Utilities** (2 skills):
- `/create-command` - Create new skills
- `/create-rule` - Create memory rules

**Teams** (2 skills — experimental):
- `/team-implement` - Spec-driven team orchestration that scales from 3 to 11 agents based on project complexity. Accepts plain text, Jira tickets, GitHub issues, files, or URLs as input.
- `/team-review` - Multi-agent PR review team with 7 specialized reviewers + adversary reviewer

**Specialty** (4 model-invoked skills):
- `agent-browser` - AI-optimized browser automation (93% less context than Playwright)
- `find-skills` - Discover and install third-party skills from [skills.sh](https://skills.sh)
- `jira-cli` - Manage Jira issues, sprints, and epics
- `skill-creator` - Guide for creating custom skills

See the `skills/` directory for details.

### 📊 Statusline (Optional)

Track costs and usage in your Claude Code prompt:
- Model name and version
- Current directory
- Git branch with uncommitted changes (●)
- Git worktree name (when in worktrees)
- Context window usage percentage
- Session costs
- Lines changed (+added/-removed)
- Session duration
- Time until 5-hour reset

**Example:**
```
🤖 Opus 4.5 │ 📁 ~/projects/cc-arsenal │ 🌿 main ● │ 📊 66% │ 💰 $3.169 │ 📝 +719/-545 │ ⏱️ 21m │ 🔄 4h 23m until reset at 13:00
```

**In a git worktree:**
```
🤖 Opus 4.5 │ 📁 ~/projects/feature │ 🌿 feat-branch ● │ 🌳 feature │ 📊 45% │ 💰 $1.234 │ 📝 +120/-80 │ ⏱️ 15m │ 🔄 2h 10m until reset at 14:00
```

👉 [Statusline documentation](scripts/claude/statusline/STATUSLINE.md)

### 🕐 Claude Hi Scheduler (Optional)

Automatically start fresh 5-hour windows before your peak coding times:

```bash
make claude-hi-setup      # Choose your schedule
make claude-hi-standard   # Quick 9am/2pm/7pm setup
```

👉 [Claude Hi documentation](scripts/claude-hi/README.md)

## Documentation

- [Getting Started](docs/getting-started.md) - Setup and configuration
- [Statusline Guide](scripts/claude/statusline/STATUSLINE.md) - Usage tracking and configuration
- [Claude Hi Guide](scripts/claude-hi/README.md) - Session scheduling
- [Troubleshooting](docs/troubleshooting.md) - Common issues
- [Security Policy](docs/SECURITY.md) - Vulnerability reporting
- [Changelog](docs/CHANGELOG.md) - Version history
- [Code of Conduct](docs/CODE_OF_CONDUCT.md) - Community guidelines

## Contributing

Contributions welcome! Fork the repo, make your changes, and submit a PR.

```bash
git clone https://github.com/mgiovani/cc-arsenal.git
cd cc-arsenal
make dev        # Set up development environment
make test       # Run tests
make check      # Run quality checks
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for details. Please also review our [Code of Conduct](docs/CODE_OF_CONDUCT.md).

## Support

- 🐛 [Report bugs](https://github.com/mgiovani/cc-arsenal/issues)
- 🔒 [Report security vulnerabilities](docs/SECURITY.md)
- 💬 [Discussions](https://github.com/mgiovani/cc-arsenal/discussions)
- 📖 Check `docs/` for guides

## License

MIT License - see [LICENSE](LICENSE) for details.

---

*Built with Claude for Claude users*
