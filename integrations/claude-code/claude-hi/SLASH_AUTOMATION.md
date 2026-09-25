# Claude slash command automation

Automate your custom Claude Code slash commands on a daily schedule! Perfect for workflows like daily standups, automated reviews, security scans, and performance monitoring.

## Overview

Just like you automate PR reviews with cron, now you can automate any Claude Code custom slash command to run at scheduled times. This creates a proactive AI workflow layer that handles routine tasks automatically.

## Quick start

```bash
# Interactive setup
make claude-slash-setup

# Check what's automated
make claude-slash-status

# List all automations
make claude-slash-list

# Remove automation
make claude-slash-remove
```

## Common use cases

### Daily standups
```bash
# Automate daily standup at 9am
./claude_slash_cron.sh setup '/daily-standup' '9'
```

### Code reviews
```bash
# Review PRs twice daily
./claude_slash_cron.sh setup '/review-prs' '10,16' '/path/to/project'
```

### Security scans
```bash
# Security audit every morning
./claude_slash_cron.sh setup '/security-scan' '8'
```

### Performance monitoring
```bash
# Performance checks at business hours
./claude_slash_cron.sh setup '/perf-check' '9,12,15,17'
```

### Deployment verification
```bash
# Check deployments after typical deploy times
./claude_slash_cron.sh setup '/check-deploy' '11,17'
```

## Advanced usage

### Project-specific automation
```bash
# Run command in specific project directory
./claude_slash_cron.sh setup '/daily-standup' '9' '~/myproject' 'project-standup'

# Different projects for different commands
./claude_slash_cron.sh setup '/review-backend' '10' '~/backend-repo'
./claude_slash_cron.sh setup '/review-frontend' '11' '~/frontend-repo'
./claude_slash_cron.sh setup '/deploy-check' '14' '/var/www/production'
```

### Directory selection guide

| Option | Behavior |
| --- | --- |
| Current directory | Leave empty; the command runs wherever you are when it executes |
| Specific project | Enter a full path; the command always runs in that project folder |
| Tilde expansion | `~/myproject` expands to `/Users/yourname/myproject` |
| Relative paths | `../other-project` resolves relative to the current directory |
| Validation | The system checks whether the directory exists and offers to create it |

### Multiple schedules
```bash
# Different commands at different times
./claude_slash_cron.sh setup '/morning-brief' '8'
./claude_slash_cron.sh setup '/afternoon-review' '15'
./claude_slash_cron.sh setup '/evening-summary' '18'
```

## Schedule formats

The schedule argument accepts one or more comma-separated hours (0-23, 24-hour clock), and the cron job fires once for each hour listed:

- Single time: `'9'` (9am daily)
- Multiple times: `'9,17'` (9am and 5pm daily)
- Business hours: `'9,12,15,17'` (every 3 hours)
- Frequent: `'8,10,12,14,16,18'` (every 2 hours)

## Management commands

### Setup new automation
```bash
# Interactive setup
make claude-slash-setup

# Direct setup
./claude_slash_cron.sh setup <command> <schedule> [project_dir] [name]
```

### Monitor status
```bash
# Show all automations and recent activity
make claude-slash-status

# List configurations
make claude-slash-list
```

### Remove automation
```bash
# Interactive removal
make claude-slash-remove

# Direct removal
./claude_slash_cron.sh remove <name>
```

## File locations

Setup writes three files under `~/.claude`, and every automation reads and appends to them on each run:

- Execution script: `~/.claude/run_slash_command.sh`
- Configurations: `~/.claude/slash_cron/*.conf`
- Activity log: `~/.claude/slash_cron.log`

## Integration with existing workflows

This system works alongside your existing cron jobs. For example:

```bash
# Your existing PR review test
0 10 * * * /path/to/pr-review-test.sh

# New automated Claude slash commands
0 9 * * * ~/.claude/run_slash_command.sh "/daily-standup"
0 10 * * * ~/.claude/run_slash_command.sh "/review-prs"
```

## Security & reliability

- Timeout protection: commands timeout after 5 minutes
- Full logging: all executions logged with timestamps
- Error handling: failed commands don't break the schedule
- Context awareness: commands run in the correct project directories

## Example workflow: full day automation

```bash
# Morning briefing
./claude_slash_cron.sh setup '/morning-brief' '8' '' 'morning'

# Mid-morning code review
./claude_slash_cron.sh setup '/review-prs' '10' '/path/to/project' 'code-review'

# Lunch break summary
./claude_slash_cron.sh setup '/progress-check' '12' '' 'midday'

# Afternoon security scan
./claude_slash_cron.sh setup '/security-scan' '14' '/path/to/project' 'security'

# End-of-day wrap-up
./claude_slash_cron.sh setup '/daily-summary' '17' '' 'summary'
```

This creates a fully automated AI-powered workday with:
- 8am: Morning briefing and planning
- 10am: Automated code reviews
- 12pm: Progress check and blocker identification
- 2pm: Security and compliance verification
- 5pm: Daily summary and next-day preparation

## Troubleshooting

### Command not running
```bash
# Check cron jobs are installed
crontab -l | grep "Claude Slash"

# Check recent activity
tail ~/.claude/slash_cron.log
```

### Execution errors
```bash
# Test command manually
~/.claude/run_slash_command.sh "/your-command"

# Check logs
make claude-slash-status
```

### Permission issues
```bash
# Ensure script is executable
chmod +x ~/.claude/run_slash_command.sh

# Recreate execution script
./claude_slash_cron.sh create-script
```

## Pro tips

1. Start simple: begin with one automation and expand gradually
2. Use descriptive names: makes management easier with multiple automations
3. Test first: run commands manually before automating
4. Monitor logs: check activity regularly to ensure smooth operation
5. Combine with claude-hi: use both systems for comprehensive Claude automation

Transform your development workflow with intelligent, scheduled AI assistance!
