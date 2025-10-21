# Claude Code Enhanced Statusline

A comprehensive bash+jq statusline that displays model info, git status, costs, and system information with beautiful colors and emojis.

## Usage
```bash
# Add to your Claude Code settings
"statusline": "bash ~/.claude/scripts/claude/statusline/statusline.sh"
```

## Features
- 🤖 Model name and version
- 🌿 Git branch with uncommitted changes (●)
- 🌳 Git worktree name
- 📁 Current directory
- 💰 Session costs
- 🔄 5-hour window reset countdown
- 📊 Context window usage
- ⏰ Session duration

👉 **[Complete documentation →](STATUSLINE.md)**

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
- **5-Hour Windows**: Tracks sessions to calculate when your 5-hour usage window resets
- **Reset Countdown**: Shows time remaining until your usage window resets
  - 🔴 Red: Less than 1 hour remaining
  - 🟡 Yellow: 1-2 hours remaining
  - 🔵 Blue: More than 2 hours remaining
  - 🟢 Green: Reset available now

## Architecture & Performance

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

1. **Live Cache Daemon** (`statusline_daemon.sh`)
  - Auto-starts on first statusline call
  - Updates cache every 60 seconds in background
  - Maintains fresh data for event-independent components
  - Battery-efficient: <0.1% CPU usage
  - Auto-restarts after system reboot

2. **Statusline Script** (`statusline.sh`)
  - Called by Claude Code (max 300ms refresh rate per docs)
  - Ensures daemon is running (auto-start if needed)
  - Reads from live cache if available (instant, ~1ms)
  - Falls back to direct calculation if cache not ready (~50ms)
  - Combines cached data with Claude event data

### Component Types

**Event-Dependent** (from Claude Code events):
- 🤖 Model information
- 💰 Session cost
- 📊 Context usage
- ⏱️ Session duration

**Event-Independent** (cached by daemon):
- 🌿 **Git status** - Branch and uncommitted changes (●)
- 🌳 **Worktree** - Worktree name (only when in a worktree)
- 📁 **Directory** - Current directory

**Always Calculated** (lightweight):
- 🔄 **Window reset timer** - Countdown to next 5-hour reset

### Quick Start

**No setup required!** Just install and use Claude Code - everything works automatically.

The daemon auto-starts when you first use the statusline and keeps running in the background.

### Daemon Management (Optional)

You can manually control the daemon if needed:

```bash
# Check daemon status and view cache
~/.claude/scripts/claude/statusline/statusline_daemon.sh status

# Manually stop daemon (auto-restarts on next statusline call)
~/.claude/scripts/claude/statusline/statusline_daemon.sh stop

# Manually restart daemon
~/.claude/scripts/claude/statusline/statusline_daemon.sh restart

# Force cache update (for testing)
~/.claude/scripts/claude/statusline/statusline_daemon.sh update
```

**Note:** Manual control is rarely needed - the daemon auto-starts and self-heals automatically.

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
