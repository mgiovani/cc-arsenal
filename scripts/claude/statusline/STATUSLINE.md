# Claude Code Statusline

Shows usage tracking, git status, and session information in your Claude Code prompt.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Components](#components)
- [Architecture](#architecture)
- [Troubleshooting](#troubleshooting)

## Overview

Shows session information at a glance:
- Token usage and costs
- Git status with worktree detection
- Context window usage
- 5-hour window reset countdown
- Session duration

## Features

### What it shows
- 🤖 Model name and version
- 📁 Current directory
- 🌿 Git branch and uncommitted changes
- 🌳 Git worktree name
- 📊 Context window usage
- 💰 Session costs
- 🔄 Time until 5-hour reset
- ⏱️ Session duration

### How it works
- Updates automatically with each Claude interaction
- Background daemon caches git info for speed (<1ms)
- Auto-restarts if needed
- Low resource usage (<0.1% CPU)

## Installation

### Prerequisites

The statusline requires:
- **jq** - JSON processing (usually pre-installed on macOS/Linux)
- **git** - For repository information (if using git features)

### Quick Install

From the cc-arsenal project root:

```bash
make statusline-install
```

This will:
1. Install the statusline script to `~/.claude/scripts/claude/statusline/`
2. Configure Claude Code to use the statusline
3. Start the background daemon (auto-managed)

### Manual Installation

1. **Copy the statusline to your Claude directory**:
  ```bash
  mkdir -p ~/.claude/scripts/claude/statusline/
  cp scripts/claude/statusline/statusline.sh ~/.claude/scripts/claude/statusline/
  cp scripts/claude/statusline/statusline_daemon.sh ~/.claude/scripts/claude/statusline/
  chmod +x ~/.claude/scripts/claude/statusline/*.sh
  ```

2. **Configure Claude Code settings**:
  Add to your `~/.claude/settings.local.json`:
  ```json
  {
    "statusline": "bash ~/.claude/scripts/claude/statusline/statusline.sh"
  }
  ```

3. **Restart Claude Code** to apply changes

The daemon will auto-start on first use - no manual configuration needed!

### Verification

Test the installation:

```bash
# Test the statusline directly
echo '{"model":{"id":"claude-sonnet-4.5"},"workspace":{"current_dir":"'$PWD'"},"cost":{}}' | bash ~/.claude/scripts/claude/statusline/statusline.sh

# Check daemon status
bash ~/.claude/scripts/claude/statusline/statusline_daemon.sh status
```

## Usage

### Basic Usage

The statusline runs automatically - Claude Code calls it on every interaction. No manual intervention needed!

### Example Output

**Regular repository:**
```bash
🤖 Sonnet 4.5 │ 📁 cc-arsenal │ 🌿 main │ 📊 22% │ 💰 $0.043 │ 🔄 2h15m
```

**With uncommitted changes:**
```bash
🤖 Sonnet 4.5 │ 📁 cc-arsenal │ 🌿 main ● │ 📊 22% │ 💰 $0.043 │ 🔄 2h15m
```

**In a git worktree:**
```bash
🤖 Sonnet 4.5 │ 📁 feature-impl │ 🌿 feature-branch │ 🌳 feature-impl │ 📊 22% │ 💰 $0.043 │ 🔄 2h15m
```

**Worktree with uncommitted changes:**
```bash
🤖 Sonnet 4.5 │ 📁 feature-impl │ 🌿 feature-branch ● │ 🌳 feature-impl │ 📊 22% │ 💰 $0.043 │ 🔄 2h15m
```

### Daemon Management

While the daemon auto-manages itself, you can control it manually if needed:

```bash
# Check daemon status and view cache
bash ~/.claude/scripts/claude/statusline/statusline_daemon.sh status

# Manually stop daemon (auto-restarts on next statusline call)
bash ~/.claude/scripts/claude/statusline/statusline_daemon.sh stop

# Manually restart daemon
bash ~/.claude/scripts/claude/statusline/statusline_daemon.sh restart

# Force cache update (for testing)
bash ~/.claude/scripts/claude/statusline/statusline_daemon.sh update
```

**Note:** Manual control is rarely needed - the daemon auto-starts and self-heals automatically.

## Configuration

### Interactive Configuration

Use the configuration tool for easy customization:

```bash
python ~/.claude/scripts/claude/statusline/configure_statusline.py
```

This allows you to:
- Enable/disable specific components
- Reorder component display
- Customize separators and formatting
- Set display thresholds
- Configure truncation behavior

### Component Configuration

**Available Components:**
- `model` - Model name/version
- `directory` - Current working directory
- `git` - Git branch and status
- `worktree` - Git worktree name (only shown when in a worktree)
- `context` - Context window usage %
- `session_cost` - Current session cost
- `lines_changed` - Lines added/removed
- `duration_info` - Request processing time
- `reset_countdown` - Time until window reset

### Display Settings

**Separators:**
- Default: ` │ ` (vertical bar with spaces)
- Options: `|`, `•`, `▶`, `→`, or custom

**Width Management:**
- `max_width`: Maximum statusline width (default: 120)
- `compact_threshold`: When to switch to compact mode (default: 80)

**Formatting Options:**
- `directory_max_length`: Truncate directory names (default: 25)
- `directory_display_mode`: `short` (~/projects) or `full` (/Users/you/projects)
- `git_branch_max_length`: Truncate long branch names (default: 15)
- `cost_decimal_places`: Cost precision (default: 3)

### Manual Configuration

Edit `~/.claude/cc-arsenal/statusline_config.json`:

```json
{
  "components": {
    "order": [
      "model",
      "directory",
      "git",
      "context",
      "session_cost",
      "reset_countdown"
    ],
    "enabled": {
      "model": true,
      "directory": true,
      "git": true,
      "context": true,
      "session_cost": true,
      "reset_countdown": true,
      "lines_changed": false,
      "duration_info": false
    }
  },
  "display": {
    "separator": " │ ",
    "compact_separator": "│",
    "max_width": 120,
    "compact_threshold": 80
  },
  "formatting": {
    "directory_max_length": 25,
    "directory_display_mode": "short",
    "git_branch_max_length": 15,
    "cost_decimal_places": 3
  }
}
```

## Components

### Event-Dependent Components
(from Claude Code events)

- **🤖 Model** - Current model information
- **💰 Session Cost** - Cost of current session in USD
- **📊 Context Usage** - Percentage of 200K context window used
- **⏱️ Session Duration** - Time spent in current session

### Event-Independent Components
(cached by daemon)

- **🌿 Git Status** - Branch and uncommitted changes (●)
- **🌳 Worktree** - Worktree name (only when in a worktree)
- **📁 Directory** - Current directory

### Always Calculated Components
(calculated on-demand)

- **🔄 Window Reset Timer** - Time until 5-hour reset
  - Format: `2h15m until reset at 14:00`

### Git Worktree Detection

Automatically detects when you're in a git worktree:

**Regular repo:**
```bash
🌿 main
```

**In a worktree:**
```bash
🌿 feature-branch │ 🌳 feature-impl
```

**Worktree with changes:**
```bash
🌿 feature-branch ● │ 🌳 feature-impl
```

The 🌳 worktree indicator only appears when needed.

## Architecture

### Zero-Config Design

The statusline **automatically manages everything** - no setup required!

When you first use Claude Code, the statusline:
1. Detects the daemon is not running
2. Auto-starts it silently in the background
3. Uses fallback calculation until cache is ready
4. Subsequent calls use the live cache (instant)

**Self-Healing:** If your system restarts or the daemon crashes, the next statusline call automatically restarts it.

### Two-Tier Architecture

The statusline uses a **cache-based architecture** for optimal performance:

**1. Live Cache Daemon** (`statusline_daemon.sh`)
- Auto-starts on first statusline call
- Updates cache every 60 seconds in background
- Maintains fresh data for event-independent components
- Battery-efficient: <0.1% CPU usage
- Auto-restarts after system reboot

**2. Statusline Script** (`statusline.sh`)
- Called by Claude Code (max 300ms refresh rate per docs)
- Ensures daemon is running (auto-start if needed)
- Reads from live cache if available (instant, ~1ms)
- Falls back to direct calculation if cache not ready (~50ms)
- Combines cached data with Claude event data

### Performance & Battery Impact

- **Update interval**: 60 seconds (configurable)
- **CPU usage**: <0.1% average
- **Memory**: ~2MB
- **Battery impact**: Negligible (equivalent to checking time every minute)
- **Statusline response**: <1ms with cache, ~50ms without

### Design Principles

- **SOLID**: Single responsibility, dependency inversion, interface segregation
- **DRY**: Reusable functions, no code duplication
- **Fail-Safe**: Graceful degradation if any component fails
- **Performance**: Minimal subshells, atomic writes, efficient JSON generation

## Troubleshooting

### Common Issues

#### Statusline Not Showing

**Check Claude Code configuration:**
```bash
cat ~/.claude/settings.local.json | grep statusline
```

Should show:
```json
"statusline": "bash ~/.claude/scripts/claude/statusline/statusline.sh"
```

**Verify file exists and is executable:**
```bash
ls -l ~/.claude/scripts/claude/statusline/statusline.sh
chmod +x ~/.claude/scripts/claude/statusline/statusline.sh
```

#### Slow Performance

**Check if daemon is running:**
```bash
bash ~/.claude/scripts/claude/statusline/statusline_daemon.sh status
```

**If not running, start it:**
```bash
bash ~/.claude/scripts/claude/statusline/statusline_daemon.sh start
```

The daemon should auto-start, but you can restart it manually if needed.

#### Incorrect Information

**Force cache update:**
```bash
bash ~/.claude/scripts/claude/statusline/statusline_daemon.sh update
```

**Check daemon logs:**
```bash
tail ~/.claude/scripts/claude/statusline/daemon.log
```

#### Git Worktree Not Detected

**Verify you're in a worktree:**
```bash
git rev-parse --git-dir
git rev-parse --git-common-dir
```

If these return different paths, you're in a worktree. If the statusline still doesn't show it, restart the daemon:
```bash
bash ~/.claude/scripts/claude/statusline/statusline_daemon.sh restart
```

### Debug Mode

Enable debug logging:

```bash
export STATUSLINE_DEBUG=1
echo '{"model":{"id":"test"}}' | bash ~/.claude/scripts/claude/statusline/statusline.sh
cat /tmp/claude_statusline_debug.log
```

Enable performance monitoring:

```bash
export STATUSLINE_PERF=1
echo '{"model":{"id":"test"}}' | bash ~/.claude/scripts/claude/statusline/statusline.sh
```

### Cache Issues

**Inspect cache contents:**
```bash
bash ~/.claude/scripts/claude/statusline/cache_inspector.sh
```

**Clear cache and restart:**
```bash
rm -rf /tmp/statusline_live_cache/
bash ~/.claude/scripts/claude/statusline/statusline_daemon.sh restart
```

### Getting Help

If you encounter issues:

1. Check the [troubleshooting section](#troubleshooting) above
2. Review daemon status: `bash ~/.claude/scripts/claude/statusline/statusline_daemon.sh status`
3. Check logs in `/tmp/statusline_live_cache/` and `~/.claude/scripts/claude/statusline/`
4. Open an issue on GitHub with:
  - Output of `status` command
  - Relevant log files
  - Steps to reproduce the issue

---

**Questions or issues?** Open an issue on [GitHub](https://github.com/mgiovani/cc-arsenal/issues) or check the main [cc-arsenal documentation](../../../README.md).
