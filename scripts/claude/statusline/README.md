# Claude Code Enhanced Statusline

A comprehensive bash+jq statusline that displays model info, git status, costs, and system information with beautiful colors and emojis.

## Usage
```bash
# Add to your Claude Code settings
"statusline": "bash ~/.claude/scripts/claude/statusline/statusline.sh"
```

## Features
- 🤖 Current model and version
- 🌿 Git branch and status with ahead/behind indicators
- 📁 Current directory (shortened for long paths)
- 💰 Session costs and token usage
- 📅 Daily usage total with persistent tracking
- 🔄 5-hour window reset countdown with color coding
- 📊 Context remaining percentage
- ⏰ Session duration (if available)
- 🎨 ANSI colors and emojis
- 📱 Responsive width adjustment with compact format

## Script Location
`~/.claude/scripts/claude/statusline/statusline.sh`

## JSON Input
The script receives Claude Code session data as JSON via stdin and parses it with jq to extract:
- Model information and version
- Session costs (total_cost_usd or total_cost)
- Token usage (input_tokens, output_tokens)
- Context usage (used/total)
- Session start time for duration calculation

## Usage Tracking
- **Daily Usage**: Persistent tracking of daily costs in `~/.claude/usage_tracking.json`
- **5-Hour Windows**: Tracks sessions to calculate when your 5-hour usage window resets
- **Reset Countdown**: Shows time remaining until your usage window resets
  - 🔴 Red: Less than 1 hour remaining
  - 🟡 Yellow: 1-2 hours remaining
  - 🔵 Blue: More than 2 hours remaining
  - 🟢 Green: Reset available now

## Architecture & Performance

### Two-Tier Architecture

The statusline uses a **cache-based architecture** for optimal performance:

1. **Live Cache Daemon** (`statusline_daemon.sh`) - Optional but recommended
  - Run once after installation: `~/.claude/scripts/claude/statusline/statusline_daemon.sh start`
  - Updates cache every 60 seconds in background
  - Maintains fresh data for event-independent components
  - Battery-efficient: <0.1% CPU usage
  - Survives system restarts (add to login items if desired)

2. **Statusline Script** (`statusline.sh`)
  - Called by Claude Code (max 300ms refresh rate per docs)
  - Reads from live cache if available (instant, ~1ms)
  - Falls back to direct calculation if daemon not running (~50ms)
  - Combines cached data with Claude event data

### Component Types

**Event-Dependent** (from Claude Code events):
- 🤖 Model information
- 💰 Session cost
- 📊 Context usage
- ⏱️ Session duration

**Event-Independent** (cached by daemon):
- 🌿 **Git status** - Current branch and uncommitted changes
- 📅 **Daily cost** - Read from `~/.claude/usage_tracking.json`
- 📁 **Current directory** - With home directory shortening

**Always Calculated** (lightweight):
- 🔄 **Window reset timer** - Countdown to next 5-hour reset

### Quick Start

After installation, start the live cache daemon once:

```bash
~/.claude/scripts/claude/statusline/statusline_daemon.sh start
```

That's it! The daemon runs in the background and keeps your statusline data fresh.

### Daemon Management

```bash
# Start daemon (run once after installation)
~/.claude/scripts/claude/statusline/statusline_daemon.sh start

# Check daemon status and view cache
~/.claude/scripts/claude/statusline/statusline_daemon.sh status

# Stop daemon
~/.claude/scripts/claude/statusline/statusline_daemon.sh stop

# Restart daemon
~/.claude/scripts/claude/statusline/statusline_daemon.sh restart

# Force cache update (for testing)
~/.claude/scripts/claude/statusline/statusline_daemon.sh update
```

**Note:** The statusline works perfectly without the daemon (using direct calculation). The daemon is optional but recommended for best performance.

**Performance & Battery Impact:**
- Update interval: 60 seconds (configurable)
- CPU usage: <0.1% average
- Memory: ~2MB
- Battery impact: Negligible (equivalent to checking time every minute)

**Design Principles:**
- **SOLID**: Single responsibility, dependency inversion, interface segregation
- **DRY**: Reusable functions, no code duplication
- **Fail-Safe**: Graceful degradation if any component fails
- **Performance**: Minimal subshells, atomic writes, efficient JSON generation

## Customization
Edit the script to add/remove information or change colors and formatting to match your terminal theme.

## Example Output
```bash
🤖 c3-5-s-202 │ 🌿 main● │ 📁 cc-arsenal │ 📊 22% │ 💰 $0.043 │ 📅 $1.23 │ 🔄 2h15m
```
