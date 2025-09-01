# Claude Template Scripts

Professional Python utilities for managing Claude template repository installations and configurations.

## Scripts

- **setup/install.py**: Safe installation with conflict detection and file-level symlinks
- **setup/configure.py**: Interactive configuration wizard
- **generators/**: Code generation tools for new agents/commands/hooks

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