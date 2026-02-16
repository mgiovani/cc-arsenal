# Claude Code Arsenal

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Workflow automation skills for Claude Code. Track usage costs, schedule optimal coding windows, and automate development workflows with 32 specialized skills.

## Quick Start

### Install Skills

```bash
# Claude Code (enhanced skills with subagents)
/plugin marketplace add mgiovani/cc-arsenal
/plugin install cc-arsenal@cc-arsenal-marketplace

# Cross-platform (base skills for any AI agent)
npx skills add mgiovani/skills
```

### Optional Features

```bash
make statusline-install    # Track usage and costs
make claude-hi-standard    # Schedule 5-hour windows
```

## What's Included

**32 Skills** organized by category:
- **Development** (12): Feature implementation, bug fixing, testing, refactoring, code review, security review, dependency audit, performance analysis, CI/CD generation, framework docs injection
- **Documentation** (6): ADR, RFC, diagrams, init, check, update
- **Git & GitHub** (4): Conventional commits, PR creation, releases, daily planning
- **Jira** (2): Standup reports, work prioritization
- **Teams** (2): Spec-driven orchestration, multi-agent PR review
- **Utilities** (6): Skill creation, memory rules, browser automation, skill discovery

**Optional Features:**
- **Statusline**: Real-time cost and usage tracking in your prompt
- **Claude Hi**: Automated 5-hour window scheduling

## Documentation

- [Architecture](docs/architecture.md) - Dual-repository model
- [Getting Started](docs/getting-started.md) - Installation and setup
- [Features](docs/features.md) - Complete skill reference
- [Statusline Guide](scripts/claude/statusline/STATUSLINE.md) - Usage tracking
- [Claude Hi Guide](scripts/claude-hi/README.md) - Session scheduling
- [Troubleshooting](docs/troubleshooting.md) - Common issues
- [Changelog](docs/CHANGELOG.md) - Version history

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Where to contribute:**
- **Base skills** (cross-platform): [mgiovani/skills](https://github.com/mgiovani/skills)
- **Enhanced skills** (Claude Code): This repository
- **Optional features**: Statusline, Claude Hi (this repository)

## Support

- 🐛 [Report bugs](https://github.com/mgiovani/cc-arsenal/issues)
- 🔒 [Security vulnerabilities](docs/SECURITY.md)
- 💬 [Discussions](https://github.com/mgiovani/cc-arsenal/discussions)

## License

MIT License - see [LICENSE](LICENSE)

---

*Built with Claude for Claude users*
