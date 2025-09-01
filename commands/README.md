# Commands

Security and quality workflow automation commands for Claude Code.

## Structure

```
commands/
├── git/         # Git operations and repository management
├── testing/     # Test automation and quality assurance
└── utility/     # General-purpose development utilities
```

## Usage

Commands use slash syntax in Claude Code:
```
/command:name "arguments"
```

## Installation

Commands are automatically symlinked to `~/.claude/commands/` when running:
```bash
uv run scripts/setup/install.py
```

## Development

Each command should be a `.md` file with YAML frontmatter:

```yaml
---
description: "Command description"
argument-hint: "<argument_format>"
allowed-tools: ["Tool1", "Tool2"]
---

# Command implementation...
```
