#!/bin/bash
# Claude Hi Cron - Simple replacement for manual cron "hi" workarounds
# Usage: ./claude_hi_cron.sh setup "9,12,15"  # Sets up hi at 9am, 12pm, 3pm weekdays

set -euo pipefail

HI_SCRIPT="$HOME/.claude/cc-arsenal/claude-hi/send_hi.sh"

# Create the simple hi sender
create_hi_sender() {
    mkdir -p "$(dirname "$HI_SCRIPT")"

    cat > "$HI_SCRIPT" << 'EOF'
#!/bin/bash
# Send "hi" to Claude to trigger 5-hour window
claude -p hi
echo "[$(date)] hi sent to trigger Claude window" >> "$HOME/.claude/cc-arsenal/claude-hi/hi_log.txt"
EOF

    chmod +x "$HI_SCRIPT"
}

# Setup cron jobs
setup_cron() {
    local times="$1"

    echo "Setting up Claude 'hi' cron jobs..."

    create_hi_sender

    # Generate cron entries
    local cron_entries=""
    IFS=',' read -ra HOURS <<< "$times"

    for hour in "${HOURS[@]}"; do
        hour=$(echo "$hour" | tr -d ' ')
        cron_entries+="0 $hour * * * $HI_SCRIPT"$'\n'
    done

    # Update crontab - create a proper temp file
    local temp_cron=$(mktemp)

    # Add existing crontab (excluding old claude entries)
    crontab -l 2>/dev/null | grep -v "$HI_SCRIPT" | grep -v "# Claude Hi Triggers" > "$temp_cron" || true

    # Add our entries
    echo "" >> "$temp_cron"
    echo "# Claude Hi Triggers" >> "$temp_cron"
    echo -n "$cron_entries" >> "$temp_cron"

    # Install the new crontab
    crontab "$temp_cron"
    rm "$temp_cron"

    echo "✅ Scheduled 'hi' at hours: $times (daily)"
    echo "✅ Replaces your manual cron workaround!"
}

# Remove cron jobs
remove_cron() {
    echo "Removing Claude 'hi' cron jobs..."
    crontab -l 2>/dev/null | grep -v "$HI_SCRIPT" | grep -v "# Claude Hi Triggers" | crontab - || true
    echo "✅ Removed all Claude 'hi' schedules"
}

# Show status
show_status() {
    echo "📊 Claude 'Hi' Cron Status"
    echo "========================="
    echo "Active cron jobs:"
    crontab -l 2>/dev/null | grep -E "send_hi.sh|Claude Hi" || echo "  No schedules found"

    echo
    echo "Recent activity:"
    tail -5 "$HOME/.claude/cc-arsenal/claude-hi/hi_log.txt" 2>/dev/null || echo "  No activity logged"
}

# Send hi now
send_now() {
    create_hi_sender
    "$HI_SCRIPT"
    echo "✅ Sent 'hi' to Claude"
}

# Interactive setup
interactive_setup() {
    echo "🚀 Claude 'Hi' Cron Setup"
    echo "========================="
    echo "This replaces your manual cron workaround with automatic 'hi' scheduling"
    echo "to trigger Claude's 5-hour usage windows at optimal times."
    echo

    echo "Choose your schedule (triggers 5 hours before Claude resets):"
    echo "1) Extended Day (4,9,14,19)     - 4am, 9am, 2pm, 7pm triggers (resets: 9am, 2pm, 7pm, 12am) [RECOMMENDED]"
    echo "2) Work Hours (9,14,19)         - 9am, 2pm, 7pm triggers (resets: 2pm, 7pm, 12am)"
    echo "3) Business Hours (9,14)        - 9am, 2pm triggers (resets: 2pm, 7pm)"
    echo "4) Custom times"
    echo

    read -r -p "Choice (1-4): " choice

    case "$choice" in
        1)
            times="4,9,14,19"
            desc="Extended Day (triggers at 4am/9am/2pm/7pm, resets at 9am/2pm/7pm/12am)"
            ;;
        2)
            times="9,14,19"
            desc="Work Hours (triggers at 9am/2pm/7pm, resets at 2pm/7pm/12am)"
            ;;
        3)
            times="9,14"
            desc="Business Hours (triggers at 9am/2pm, resets at 2pm/7pm)"
            ;;
        4)
            echo
            echo "🕐 Custom Schedule Setup"
            echo "========================"
            echo "Enter the hours when you want to send 'hi' (triggers 5 hours before reset)"
            echo
            echo "💡 Popular patterns:"
            echo "• Early bird: 6,11,16 (work 9am-1pm, 2pm-6pm, 7pm-11pm)"
            echo "• Night owl: 10,15,20 (work 1pm-5pm, 6pm-10pm, 11pm-3am)"
            echo "• Freelancer: 8,13,18 (work 11am-3pm, 4pm-8pm, 9pm-1am)"
            echo "• Part-time: 9,14 (work 12pm-2pm, 5pm-7pm)"
            echo "• Heavy user: 6,9,12,15,18 (5 windows per day)"
            echo
            echo "⚡ Strategy: Last 2 hours of each window = intensive work!"
            echo "📝 Format: 24-hour, comma-separated (e.g., 9,14,19)"
            echo
            read -r -p "Your custom hours: " times

            # Validate input
            if [[ ! "$times" =~ ^[0-9,]+$ ]]; then
                echo "❌ Invalid format. Use numbers and commas only (e.g., 9,14,19)"
                exit 1
            fi

            desc="Custom schedule ($times)"
            ;;
        *)
            echo "Invalid choice"
            exit 1
            ;;
    esac

    echo
    echo "📅 Schedule: $desc"
    echo "⏰ Times: $times"
    echo "🌍 Frequency: Daily"
    echo "📝 Message: 'hi'"
    echo

    # Show coverage with reset times
    echo "🕐 Window schedule (last 2 hours = heavy usage):"
    IFS=',' read -ra HOURS <<< "$times"
    for hour in "${HOURS[@]}"; do
        hour=$(echo "$hour" | tr -d ' ')
        reset_hour=$((hour + 5))
        heavy_start=$((hour + 3))
        printf "   %02d:00 'hi' → %02d:00-%02d:00 heavy work → %02d:00 reset\n" "$hour" "$heavy_start" "$reset_hour" "$reset_hour"
    done
    echo

    read -r -p "Confirm setup? (y/n): " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        setup_cron "$times"
        echo
        echo "🎉 Setup complete! Your Claude windows will trigger automatically."
        echo "💡 Use 'make claude-hi-status' to check what's scheduled"
        echo "🛑 Use 'make claude-hi-remove' to stop the schedule"
    else
        echo "Setup cancelled"
    fi
}

# Custom setup helper
custom_setup_helper() {
    echo "🕐 Claude 'Hi' Custom Schedule Helper"
    echo "===================================="
    echo "This tool helps you create a custom schedule based on your work pattern."
    echo

    echo "What's your work style?"
    echo "1) Early bird (start early, finish early)"
    echo "2) Developer Pro (intensive coding 7-9am, 12-2pm, 10pm-12am)"
    echo "3) Traditional 9-5 with breaks"
    echo "4) Night owl (start late, work late)"
    echo "5) Heavy user (maximum windows)"
    echo "6) I know exactly what I want"
    echo

    read -r -p "Choice (1-6): " style

    case "$style" in
        1)
            suggested="6,11,16"
            pattern="Early Bird"
            explanation="Triggers at 6am, 11am, 4pm → Heavy work 9am-1pm, 2pm-6pm, 7pm-11pm"
            ;;
        2)
            suggested="4,9,14,19"
            pattern="Developer Pro (like the creator)"
            explanation="Triggers at 4am/9am/2pm/7pm → Heavy coding 7-9am, 12-2pm, 5-7pm, 10pm-12am"
            ;;
        3)
            suggested="9,14"
            pattern="Traditional with breaks"
            explanation="Triggers at 9am, 2pm → Heavy work 12pm-2pm, 5pm-7pm"
            ;;
        4)
            suggested="10,15,20"
            pattern="Night Owl"
            explanation="Triggers at 10am, 3pm, 8pm → Heavy work 1pm-5pm, 6pm-10pm, 11pm-3am"
            ;;
        5)
            suggested="6,9,12,15,18"
            pattern="Heavy user (5 windows)"
            explanation="Maximum coverage with 5 windows per day"
            ;;
        6)
            echo
            echo "Enter your exact trigger times (24-hour format, comma-separated):"
            echo "Example: 7,12,17,22"
            read -r -p "Times: " suggested
            pattern="Custom"
            explanation="Your custom schedule"
            ;;
        *)
            echo "Invalid choice"
            exit 1
            ;;
    esac

    echo
    echo "📅 Suggested schedule: $pattern"
    echo "⏰ Trigger times: $suggested"
    echo "💡 $explanation"
    echo

    read -r -p "Use this schedule? (y/n): " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        setup_cron "$suggested"
    else
        echo "Setup cancelled. Run again to try different options."
    fi
}

# Main
case "${1:-status}" in
    setup)
        if [[ -n "${2:-}" ]]; then
            # Direct setup with times
            setup_cron "$2"
        else
            # Interactive setup
            interactive_setup
        fi
        ;;
    custom)
        custom_setup_helper
        ;;
    remove|stop)
        remove_cron
        ;;
    now)
        send_now
        ;;
    status|*)
        show_status
        ;;
esac
