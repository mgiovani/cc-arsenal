# 🚀 Claude Hi Cron - Smart Session Scheduler

Replace your manual cron workarounds with intelligent Claude Code session scheduling that automatically triggers 5-hour usage windows at optimal times.

## 🎯 What It Does

The Claude Hi system strategically sends "hi" messages to Claude at specific times to trigger fresh 5-hour usage windows, ensuring you have maximum tokens available during your intensive work periods.

### Key Strategy
- **Trigger**: Send "hi" to start a 5-hour window
- **Hours 1-3**: Light usage (research, planning, documentation)
- **Hours 4-5**: **Heavy intensive work** (complex coding, problem-solving)
- **Reset**: Fresh window starts with new token limits

## 🔧 Quick Start

### Option 1: Interactive Setup
```bash
make claude-hi-setup
```
Choose from preset schedules or create custom patterns.

### Option 2: Quick Presets
```bash
# Standard work hours
make claude-hi-standard    # 9am/2pm/7pm triggers → 2pm/7pm/12am resets

# Extended coverage  
make claude-hi-extended    # 4am/9am/2pm/7pm triggers → 9am/2pm/7pm/12am resets

# Custom patterns
make claude-hi-custom      # Guided custom setup for different work styles
```

## 📅 Schedule Options

### Built-in Presets

**Standard Work Hours (`make claude-hi-standard`)**
- **Triggers**: 9am, 2pm, 7pm
- **Heavy work periods**: 12pm-2pm, 5pm-7pm, 10pm-12am
- **Perfect for**: Traditional 9-5 workers with evening flexibility

**Extended Day (`make claude-hi-extended`)**
- **Triggers**: 4am, 9am, 2pm, 7pm  
- **Heavy coding periods**: **7am-9am**, **12pm-2pm**, 5pm-7pm, **10pm-12am**
- **Perfect for**: Developers who do intensive coding during peak token hours

### Custom Patterns

The system includes guided setup for different work styles:

#### 🌅 Early Bird Schedule
- **Triggers**: `6,11,16` (6am, 11am, 4pm)
- **Heavy work**: 9am-1pm, 2pm-6pm, 7pm-11pm
- **Perfect for**: Those who start early and finish by 11pm

#### 🦉 Night Owl Schedule  
- **Triggers**: `10,15,20` (10am, 3pm, 8pm)
- **Heavy work**: 1pm-5pm, 6pm-10pm, 11pm-3am
- **Perfect for**: Late risers who work into the night

#### 💼 Traditional with Breaks
- **Triggers**: `9,14` (9am, 2pm)
- **Heavy work**: 12pm-2pm, 5pm-7pm
- **Perfect for**: Focused work in short, intense bursts

#### 🎯 Freelancer Flexible
- **Triggers**: `8,13,18` (8am, 1pm, 6pm)
- **Heavy work**: 11am-3pm, 4pm-8pm, 9pm-1am
- **Perfect for**: Flexible schedules with client work

#### ⚡ Heavy User (Maximum Coverage)
- **Triggers**: `6,9,12,15,18` (6am, 9am, 12pm, 3pm, 6pm)
- **5 windows per day**: Maximum possible usage
- **Perfect for**: Power users who need constant access

## 📋 Management Commands

```bash
# Check what's scheduled
make claude-hi-status

# Send 'hi' immediately  
make claude-hi-now

# Remove all schedules
make claude-hi-remove

# Advanced: Direct setup with custom times
make claude-hi-custom    # Interactive custom helper
```

## 🔍 How It Works

### Cron Integration
The system creates clean cron jobs that run daily:
```bash
# Example for standard schedule (9,14,19)
0 9 * * * ~/.claude/send_hi.sh    # 9am trigger
0 14 * * * ~/.claude/send_hi.sh   # 2pm trigger  
0 19 * * * ~/.claude/send_hi.sh   # 7pm trigger
```

### Smart Fallbacks
If direct "hi" sending fails, the system:
1. Creates manual trigger files
2. Tries to copy to clipboard
3. Provides clear instructions
4. Logs all attempts for debugging

### Example Session Flow (Extended Day Pattern: 4,9,14,19)
```
4:00am  → Send "hi" (start 5-hour window)
4-7am   → Light usage: planning, documentation, setup
7-9am   → 💪 HEAVY CODING: complex development, problem-solving
9:00am  → Window resets, send new "hi"
9-12pm  → Light usage: meetings, research, testing  
12-2pm  → 💪 HEAVY CODING: intensive development work
2:00pm  → Window resets, send new "hi"
2-5pm   → Light usage: reviews, documentation
5-7pm   → 💪 CODING: moderate development
7:00pm  → Window resets, send new "hi"
7-10pm  → Light usage: planning, communication
10-12am → 💪 HEAVY CODING: focused late-night development
```

**Your pattern maximizes coding time when tokens are most available!**

## 🛠️ Advanced Usage

### Custom Schedule Creation
```bash
# Interactive custom helper
make claude-hi-custom

# Check current configuration
make claude-hi-status

# Remove current schedule
make claude-hi-remove
```

### Troubleshooting
```bash
# View recent trigger attempts
tail ~/.claude/hi_log.txt

# Check cron jobs
crontab -l | grep send_hi.sh

# Test sending 'hi' manually
make claude-hi-now

# Check current status
make claude-hi-status
```

## 📊 Status and Monitoring

### Check Current Setup
```bash
make claude-hi-status
```

**Example output:**
```
📊 Claude 'Hi' Cron Status
====================
Status: enabled
Schedule: 9,14,19 (daily)

Cron Jobs:
0 9 * * * ~/.claude/send_hi.sh
0 14 * * * ~/.claude/send_hi.sh  
0 19 * * * ~/.claude/send_hi.sh

Recent Activity:
[2024-01-15 09:00:01] hi sent to trigger Claude window
[2024-01-15 14:00:01] hi sent to trigger Claude window
[2024-01-15 19:00:01] hi sent to trigger Claude window
```

## 🔄 Migration from Manual Cron

If you currently have manual cron jobs, the system will:
1. Backup your existing crontab
2. Remove old claude-related entries  
3. Add clean new entries
4. Verify installation

**Your manual cron workarounds become this simple:**
```bash
# Instead of manually editing crontab
make claude-hi-standard

# Instead of remembering complex schedules  
make claude-hi-custom
```

## 💡 Pro Tips

### Maximizing Usage
- **Schedule intensive work** for the last 2 hours of each window
- **Use light queries** for the first 3 hours (research, documentation)
- **Plan complex tasks** around your heavy-usage periods

### Work Pattern Optimization
- **Morning person**: Use early bird schedule (6,11,16)
- **Night worker**: Use night owl schedule (10,15,20)  
- **Focused sprints**: Use traditional schedule (9,14)
- **Maximum productivity**: Use heavy user schedule (6,9,12,15,18)

### Troubleshooting
- Check logs: `tail ~/.claude/hi_log.txt`
- Test manually: `make claude-hi-now`
- Check status: `make claude-hi-status`
- Verify cron: `crontab -l | grep claude`
- Remove and recreate: `make claude-hi-remove` then `make claude-hi-setup`

## 🚀 Integration with Claude Code Arsenal

This system is part of the Claude Code Arsenal and integrates with:
- **Statusline**: Shows current usage and reset times
- **Usage tracking**: Monitors token consumption patterns
- **Configuration**: Unified ~/.claude directory structure

**Install the full arsenal:**
```bash
make install          # Install complete Claude Code Arsenal
make claude-hi-setup  # Add smart session scheduling
```

---

**Replace your manual cron workarounds with intelligent, managed scheduling that actually understands Claude's usage patterns!**