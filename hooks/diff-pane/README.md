# Git Diff Pane Hook

A **zero-token-cost** Claude Code hook that automatically opens a tmux side pane showing `git diff` whenever files are modified. This provides real-time visibility into changes without consuming API tokens.

## Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                              tmux                                    │
├────────────────────────────────┬────────────────────────────────────┤
│                                │                                     │
│     Claude Code (main)         │      Git Diff Pane (side)          │
│                                │                                     │
│  User: "Fix the bug in..."     │  diff --git a/src/app.ts           │
│  Claude: Editing file...       │  @@ -10,6 +10,8 @@                 │
│                                │  - const old = ...                  │
│  [PostToolUse hook triggers]   │  + const new = ...                  │
│           │                    │                                     │
│           └──────────────────> │  [auto-refreshes on each edit]     │
│                                │                                     │
└────────────────────────────────┴────────────────────────────────────┘
```

## Features

- **Zero token cost**: Runs entirely outside Claude's context
- **Automatic pane management**: Creates and reuses a dedicated tmux pane
- **Smart diff tool selection**: Prefers `delta` > `diff-so-fancy` > `git diff`
- **PostToolUse hook**: Triggers after `Edit`, `Write`, or `NotebookEdit` operations
- **Configurable**: Environment variables control behavior
- **Resilient**: Handles edge cases (no tmux, not git repo, pane closed manually)

## Installation

The diff-pane hook is included in the **cc-arsenal** plugin:

```bash
/plugin install cc-arsenal@cc-arsenal-marketplace
```

That's it! The hook is automatically registered and will start working immediately when you edit files.

## Usage

Once installed, the hook runs automatically when Claude modifies files. No action needed!

### Requirements

- **tmux**: Must be running Claude Code inside a tmux session
- **git repository**: Must be in a git-tracked directory
- **delta** (optional but recommended): For enhanced diff output

## Configuration

Customize behavior via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAUDE_DIFF_PANE_WIDTH` | `40` | Pane width percentage (1-99) |
| `CLAUDE_DIFF_PANE_POSITION` | `right` | Pane position: `left` or `right` |
| `CLAUDE_DIFF_STAGED_ONLY` | `false` | Show only staged changes (`git diff --cached`) |
| `CLAUDE_DIFF_TOOL` | `auto` | Diff tool: `delta`, `diff-so-fancy`, `git`, or `auto` |

### Example Configuration

Add to your shell profile (`.bashrc`, `.zshrc`, etc.):

```bash
# Diff pane on the left, wider, with delta
export CLAUDE_DIFF_PANE_WIDTH=50
export CLAUDE_DIFF_PANE_POSITION=left
export CLAUDE_DIFF_TOOL=delta
```

## Installing Delta

For the best diff experience, install [delta](https://github.com/dandavison/delta):

```bash
# Cargo (Rust)
cargo install git-delta

# Homebrew (macOS)
brew install git-delta

# apt (Debian/Ubuntu)
apt install git-delta

# pacman (Arch)
pacman -S git-delta
```

Check installation:
```bash
make check-delta
```

## Development Commands

For testing and development:

```bash
# From cc-arsenal root
make test-diff-pane       # Test the hook manually
make status-diff-pane     # Show configuration and status

# Or from hooks/diff-pane directory
cd hooks/diff-pane
make test                 # Test the hook
make status               # Show status
make check-delta          # Check if delta is installed
make clean                # Clean up temporary files
make help                 # Show all commands
```

## How It Works

1. **Hook Registration**: Configured as `PostToolUse` hook with matcher `Edit|Write|NotebookEdit`
2. **Trigger**: Fires after Claude finishes modifying a file
3. **Pane Check**: Looks for existing diff pane ID in `/tmp/claude-diff-pane-id`
4. **Pane Creation**: Creates new tmux pane if needed (split-window)
5. **Diff Display**: Runs `git diff` (via delta if available) in the pane

### Pane Management

- **Reuse**: Uses the same pane across multiple file edits
- **Recovery**: Automatically recreates pane if manually closed
- **Position**: Configurable left/right placement
- **Persistence**: Pane stays open until manually closed or tmux exits

## Edge Cases

| Scenario | Behavior |
|----------|----------|
| Not in tmux | Silently exits (no error) |
| Not a git repo | Silently exits |
| Pane closed manually | Creates new pane on next trigger |
| Multiple Claude sessions | Each gets its own pane (future: per-session tracking) |
| Large diffs | delta/git diff handles pagination naturally |
| No changes | Shows empty diff (clean state) |

## Troubleshooting

### Pane doesn't appear

1. Check you're in tmux: `echo $TMUX` (should output something)
2. Check you're in a git repo: `git status` (should work)
3. Test the hook manually: `make test-diff-pane`
4. Check plugin is installed: `/plugin list` (should show cc-arsenal)

### Diff output looks wrong

1. Check diff tool: `make status-diff-pane`
2. Install delta: `make check-delta`
3. Set explicit tool: `export CLAUDE_DIFF_TOOL=git`

### Pane appears in wrong position

```bash
export CLAUDE_DIFF_PANE_POSITION=left  # or right
```

### Want to see only staged changes

```bash
export CLAUDE_DIFF_STAGED_ONLY=true
```

## Technical Details

### Files

```
hooks/diff-pane/
├── scripts/
│   └── diff-pane.sh      # Main hook script
├── hooks.json            # Hook configuration (for plugin system)
├── Makefile              # Development/testing targets
└── README.md             # This file
```

### Hook Configuration

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write|NotebookEdit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/diff-pane/scripts/diff-pane.sh",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### Pane ID Storage

- Location: `/tmp/claude-diff-pane-id`
- Format: tmux pane ID (e.g., `%123`)
- Lifetime: Until system reboot (tmpfs)
- Purpose: Allows pane reuse across hook invocations

## Future Enhancements

- **Per-session pane tracking**: Each Claude session gets its own pane
- **File-specific diff**: Show diff only for the file that was just edited
- **Diff stats header**: Show `git diff --stat` summary at top
- **Watch mode**: Continuous updates using `watch`
- **SessionEnd cleanup**: Automatically close pane when Claude exits

## License

MIT License - Part of [Claude Code Arsenal](https://github.com/mgiovani/cc-arsenal)

## Contributing

Issues and pull requests welcome at https://github.com/mgiovani/cc-arsenal
