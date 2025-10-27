# Claude Code Arsenal

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Tools to make Claude Code more useful: track your usage costs, schedule optimal coding windows, and organize your AI agents.

## What's included

**Agents, Commands, Skills & Hooks** - Pre-built AI assistants and automation
- 30+ specialized agents (architecture, development, UX, product)
- Git commands with conventional commits and PR creation
- Jira CLI integration and skill creation guide
- File protection hook for sensitive data
- Easy to customize or create your own

**Statusline** - Track your usage and costs in real-time (optional)
- Shows costs, context usage, and time until reset
- Git branch and worktree info
- Example: `🤖 Sonnet 4.5 │ 📁 cc-arsenal │ 🌿 main │ 📊 22% │ 💰 $0.043 │ 🔄 2h15m`

**Claude Hi Scheduler** - Maximize your 5-hour usage windows (optional)
- Auto-triggers fresh windows at optimal times
- Choose from preset schedules or customize your own
- Perfect for planning intensive coding sessions

## Installation

**Prerequisites:** Install UV first
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Install via plugin:**
```bash
/plugin marketplace add mgiovani/cc-arsenal
/plugin install cc-arsenal
```

**Or clone and install:**
```bash
git clone https://github.com/mgiovani/cc-arsenal.git
cd cc-arsenal
make install              # Install all components
make configure            # Optional: interactively choose specific components
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

### 🤖 Agents, Commands, Skills & Hooks

Pre-built AI assistants and automation for your development workflow.

**Agents** - Specialized AI assistants organized by domain:
- **Architecture**: System design, technical planning, infrastructure
- **Development**: Code implementation, debugging, refactoring
- **Orchestration**: Workflow coordination, automation
- **Product**: Requirements, planning, prioritization
- **Productivity**: Development optimization, efficiency
- **UX**: User experience, design systems

**Commands** - Workflow automation via slash commands:
- `/git:commit` - Generate conventional commits automatically
- `/git:create-pr` - Create pull requests with templates

**Skills** - Domain-specific tools Claude loads when needed:
- `jira-cli` - Manage Jira issues, sprints, and epics
- `skill-creator` - Guide for creating custom skills

**Hooks** - Event-driven automation:
- `file_protection` - Prevent committing sensitive files

See the `agents/`, `commands/`, `skills/`, and `hooks/` directories for details.

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
🤖 Sonnet 4.5 │ 📁 ~/projects/cc-arsenal │ 🌿 main ● │ 📊 66% │ 💰 $3.169 │ 📝 +719/-545 │ ⏱️ 21m │ 🔄 4h 23m until reset at 13:00
```

**In a git worktree:**
```
🤖 Sonnet 4.5 │ 📁 ~/projects/feature │ 🌿 feat-branch ● │ 🌳 feature │ 📊 45% │ 💰 $1.234 │ 📝 +120/-80 │ ⏱️ 15m │ 🔄 2h 10m until reset at 14:00
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
- [Agent Development](docs/agent-development.md) - Create custom agents
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
