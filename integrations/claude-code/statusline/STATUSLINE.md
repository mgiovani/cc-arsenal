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
- Direct calculation for all components (~50ms)
- No background daemon required
- Minimal resource usage

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

### Manual Installation

1. **Copy the statusline to your Claude directory**:
  ```bash
  mkdir -p ~/.claude/scripts/claude/statusline/
  cp integrations/claude-code/statusline/statusline.sh ~/.claude/scripts/claude/statusline/
  chmod +x ~/.claude/scripts/claude/statusline/statusline.sh
  ```

2. **Configure Claude Code settings**:
  Add to your `~/.claude/settings.local.json`:
  ```json
  {
    "statusline": "bash ~/.claude/scripts/claude/statusline/statusline.sh"
  }
  ```

3. **Restart Claude Code** to apply changes

### Verification

Test the installation:

```bash
# Test the statusline directly
echo '{"model":{"id":"claude-sonnet-4.5"},"workspace":{"current_dir":"'$PWD'"},"cost":{}}' | bash ~/.claude/scripts/claude/statusline/statusline.sh
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

### Optional: Background Daemon (Advanced)

The statusline includes an optional background daemon for caching git information. However, **the daemon is not enabled by default** as direct calculation is fast enough (~50ms).

If you want to enable the daemon for slightly faster performance (~1ms), you can manually start it:

```bash
# Start the daemon manually (optional)
bash ~/.claude/scripts/claude/statusline/statusline_daemon.sh start

# Check daemon status
bash ~/.claude/scripts/claude/statusline/statusline_daemon.sh status

# Stop daemon
bash ~/.claude/scripts/claude/statusline/statusline_daemon.sh stop
```

**Note:** The daemon is completely optional. The statusline works perfectly fine without it.

## Configuration

**Note:** The statusline currently has a fixed component layout and is not user-configurable. A configuration tool (`configure_statusline.py`) exists but is not yet integrated with the statusline script.

The statusline displays these components in order:
- `model` - Model name/version
- `directory` - Current working directory
- `git` - Git branch and status
- `worktree` - Git worktree name (only shown when in a worktree)
- `context` - Context window usage %
- `session_cost` - Current session cost
- `lines_changed` - Lines added/removed (when non-zero)
- `session_duration` - Session duration (when available)
- `reset_countdown` - Time until window reset

The separator is fixed as ` │ ` (vertical bar with spaces).

## Components

### Event-Dependent Components
(from Claude Code events)

- **🤖 Model** - Current model information
- **💰 Session Cost** - Cost of current session in USD
- **📊 Context Usage** - Percentage of 200K context window used
- **⏱️ Session Duration** - Time spent in current session

### Git Components

- **🌿 Git Status** - Branch and uncommitted changes (●)
- **🌳 Worktree** - Worktree name (only when in a worktree)

### Other Components

- **📁 Directory** - Current directory
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

### Simple Direct Calculation Design

The statusline uses a **direct calculation approach** for simplicity and reliability:

**Statusline Script** (`statusline.sh`)
- Called by Claude Code on each interaction
- Calculates all components on-demand
- Response time: ~50ms (fast enough for real-time display)
- No background processes or daemon management needed
- Combines git data with Claude event data

### Optional Cache Support

For advanced users who want faster performance, a daemon is available:

**Live Cache Daemon** (`statusline_daemon.sh`) - **Optional, not enabled by default**
- Updates cache every 60 seconds in background
- Can reduce statusline response to ~1ms
- Battery-efficient: <0.1% CPU usage
- Must be manually started

The statusline will opportunistically use cached data if the daemon is running, but works perfectly fine without it.

### Performance

- **Statusline response**: ~50ms (direct calculation)
- **With optional daemon**: ~1ms (cached)
- **CPU usage**: Negligible (only runs on Claude interactions)
- **Memory**: Minimal (~1-2MB if daemon is used)

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

The statusline typically responds in ~50ms which should be fast enough. If you're experiencing slower performance:

**Optional: Start the cache daemon for faster performance:**
```bash
bash ~/.claude/scripts/claude/statusline/statusline_daemon.sh start
```

This is completely optional and will reduce response time to ~1ms.

#### Incorrect Information

The statusline calculates information directly on each call, so stale data should not occur.

If you're using the optional daemon and see stale data:

**Force cache update:**
```bash
bash ~/.claude/scripts/claude/statusline/statusline_daemon.sh update
```

**Check daemon logs:**
```bash
tail /tmp/statusline_live_cache/daemon.log
```

#### Git Worktree Not Detected

**Verify you're in a worktree:**
```bash
git rev-parse --git-dir
git rev-parse --git-common-dir
```

If these return different paths, you're in a worktree. The statusline should detect this automatically since it calculates git information directly on each call.

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

### Cache Issues (Only if using optional daemon)

If you're using the optional daemon and experiencing issues:

**Inspect cache contents:**
```bash
bash ~/.claude/scripts/claude/statusline/cache_inspector.sh
```

**Clear cache and restart:**
```bash
rm -rf /tmp/statusline_live_cache/
bash ~/.claude/scripts/claude/statusline/statusline_daemon.sh restart
```

**Note:** If you're not using the daemon, there's no cache to troubleshoot.

### Getting Help

If you encounter issues:

1. Check the [troubleshooting section](#troubleshooting) above
2. Test the statusline directly with debug mode enabled
3. If using the optional daemon, check its status: `bash ~/.claude/scripts/claude/statusline/statusline_daemon.sh status`
4. Open an issue on GitHub with:
  - Debug log output (`STATUSLINE_DEBUG=1`)
  - Your Claude Code settings
  - Steps to reproduce the issue

---

**Questions or issues?** Open an issue on [GitHub](https://github.com/mgiovani/cc-arsenal/issues) or check the main [cc-arsenal documentation](../../../README.md).
