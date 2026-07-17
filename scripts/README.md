# Scripts

Professional Python utilities for managing Claude Code Arsenal installations and configurations.

## Structure

```
scripts/
├── setup/           # Installation and configuration
│   ├── install.py      # Safe installation with symlink management
│   └── configure.py    # Interactive configuration wizard
├── claude/          # Claude Code utilities
│   └── statusline/     # Status line configuration tool
└── claude-hi/       # Smart session scheduler
    └── README.md       # Session window management
```

## Installation

From the project root:

```bash
uv sync
```

## Usage

From the project root:

```bash
# Install template to ~/.claude
uv run python -m scripts.setup.install

# Configure installed components
uv run python -m scripts.setup.configure

# Preview installation without changes
uv run python -m scripts.setup.install --dry-run
```
