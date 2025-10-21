# Claude Code Arsenal

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Tools to make Claude Code more useful: track your usage costs, schedule optimal coding windows, and organize your AI agents.

## What's included

**Statusline** - See your usage and costs in real-time
- Shows costs, context usage, and time until reset
- Git branch and worktree info
- Example: `🤖 Sonnet 4.5 │ 📁 cc-arsenal │ 🌿 main │ 📊 22% │ 💰 $0.043 │ 🔄 2h15m`

**Claude Hi Scheduler** - Maximize your 5-hour usage windows
- Auto-triggers fresh windows at optimal times
- Choose from preset schedules or customize your own
- Perfect for planning intensive coding sessions

**Agents, Commands & Skills** - Pre-built AI assistants and tools
- Security validation, code review, testing
- Jira CLI integration, skill creation guide
- Organized by specialty: development, architecture, UX, product
- Easy to customize or create your own

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
make install
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

### 📊 Statusline

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

### 🕐 Claude Hi Scheduler

Automatically start fresh 5-hour windows before your peak coding times:

```bash
make claude-hi-setup      # Choose your schedule
make claude-hi-standard   # Quick 9am/2pm/7pm setup
```

👉 [Claude Hi documentation](scripts/claude-hi/README.md)

### 🤖 Agents, Commands, Skills & Hooks

Pre-configured AI assistants and automation:
- **Agents**: Specialized assistants (security, architecture, UX, product)
- **Commands**: Workflow automation (security scans, quality checks, testing)
- **Skills**: Domain-specific tools (Jira CLI, skill creation guide)
- **Hooks**: Event-driven validation (security, quality, compliance)

See the `agents/`, `commands/`, `skills/`, and `hooks/` directories.

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
