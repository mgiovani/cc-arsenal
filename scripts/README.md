# Scripts

Professional Python utilities for managing Claude Code Arsenal installations and configurations.

## Structure

```
scripts/
├── setup/           # Installation and configuration
│   ├── install.py      # Safe installation with symlink management
│   └── configure.py    # Interactive configuration wizard
├── generators/      # Code generation tools
│   └── agent_generator.py  # Generate new agents
├── claude/          # Claude Code utilities
│   └── statusline/     # Status line configuration tool
└── claude-hi/       # Smart session scheduler
    └── README.md       # Session window management
```

## Installation

```bash
uv sync
```

## Usage

```bash
# Install template to ~/.claude
uv run setup/install.py

# Configure installed components
uv run setup/configure.py

# Preview installation without changes
uv run setup/install.py --dry-run
```
