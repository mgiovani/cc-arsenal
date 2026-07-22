# cc-arsenal

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

An [Agent Skills](https://agentskills.io) arsenal of **45 skills** for development workflow automation — feature implementation, bug fixing, code review, docs, git/GitHub, Jira, multi-agent orchestration, open-source launch prep, and more. Works with Claude Code, Codex, Cursor, Gemini CLI, OpenCode, and any other spec-compatible agent.

## Quick Start

```bash
# Any Agent-Skills-compatible tool (Codex, Cursor, Gemini CLI, OpenCode, ...)
npx skills add mgiovani/cc-arsenal

# Claude Code — unlocks plugin variants, hooks, and subagent orchestration
/plugin marketplace add mgiovani/cc-arsenal
/plugin install cc-arsenal@cc-arsenal-marketplace
```

### Optional Features (Claude Code only)

```bash
make install-statusline           # Track usage and costs
make -C integrations/claude-code/claude-hi standard # Schedule 5-hour windows
```

## What's Included

**45 Skills** organized by category:
- **Development** (16): Feature implementation, bug fixing, testing, refactoring, CI/CD generation and local runs, visual regression and i18n checks, framework docs injection, DB migrations, Docker/env setup, project planning, image generation (Gemini and Codex), open-source launch prep
- **Code Review & Quality** (5): Code review, security review, dependency audit, performance analysis, design/UX audit
- **Documentation** (6): ADR, RFC, diagrams, init, check, update
- **Git & GitHub** (7): Conventional commits, PR creation, releases, gitflow, branch sync, shipping, daily planning
- **Jira** (2): Standup reports, work prioritization
- **Teams** (2): Spec-driven orchestration, multi-agent PR review
- **Utilities** (7): Skill creation, memory rules, skill improvement, multi-agent orchestration, browser automation, skill discovery, Jira CLI

**Claude Code unlocks extras:**
- 8 plugin variants (install just the category you need — see `CLAUDE.md`)
- Per-skill hooks (e.g. auto-closing a browser session on stop)
- Parallel subagent orchestration for review/team skills
- Statusline (usage/cost tracking) and Claude Hi (5-hour window scheduling)

Every skill still works standalone in any Agent-Skills-compatible tool — the Claude Code layer is additive, never required.

## Documentation

- [Getting Started](docs/getting-started.md) - Installation and setup
- [Features](docs/features.md) - Complete skill reference
- [Statusline Guide](integrations/claude-code/statusline/STATUSLINE.md) - Usage tracking (Claude Code)
- [Claude Hi Guide](integrations/claude-code/claude-hi/README.md) - Session scheduling (Claude Code)
- [Troubleshooting](docs/troubleshooting.md) - Common issues
- [Changelog](CHANGELOG.md) - Version history
- [AGENTS.md](AGENTS.md) - Canonical, tool-agnostic skill guidance
- [CLAUDE.md](CLAUDE.md) - Claude-Code-specific additions

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. New skills go under `skills/<name>/SKILL.md` — see `AGENTS.md` for the skill anatomy and portability convention.

## Support

- 🐛 [Report bugs](https://github.com/mgiovani/cc-arsenal/issues)
- 🔒 [Security vulnerabilities](docs/SECURITY.md)
- 💬 [Discussions](https://github.com/mgiovani/cc-arsenal/discussions)

## License

MIT License - see [LICENSE](LICENSE)
