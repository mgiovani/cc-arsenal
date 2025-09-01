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

## Customization
Edit the script to add/remove information or change colors and formatting to match your terminal theme.

## Example Output
```bash
🤖 c3-5-s-202 │ 🌿 main● │ 📁 claude-dump │ 📊 22% │ 💰 $0.043 │ 📅 $1.23 │ 🔄 2h15m
```