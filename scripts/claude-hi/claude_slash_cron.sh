#!/bin/bash
# Claude Slash Command Cron - Automated execution of custom slash commands
# Usage: ./claude_slash_cron.sh setup "/daily-standup" "9,17"  # Run daily standup at 9am and 5pm

set -e

# Configuration
CLAUDE_CODE_BIN="${CLAUDE_CODE_BIN:-claude}"
SLASH_SCRIPT="$HOME/.claude/run_slash_command.sh"
CONFIG_DIR="$HOME/.claude/slash_cron"
LOG_FILE="$HOME/.claude/slash_cron.log"

# Ensure config directory exists
mkdir -p "$CONFIG_DIR"

# Create the slash command execution script
create_slash_script() {
    cat > "$SLASH_SCRIPT" << 'EOF'
#!/bin/bash
# Automated slash command executor
set -e

COMMAND="$1"
PROJECT_DIR="${2:-$PWD}"
LOG_FILE="$HOME/.claude/slash_cron.log"

# Logging function
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Change to project directory if specified
if [[ -n "$PROJECT_DIR" && -d "$PROJECT_DIR" ]]; then
    cd "$PROJECT_DIR"
fi

log_message "Executing slash command: $COMMAND in $(pwd)"

# Execute the slash command with timeout
timeout 300 claude "$COMMAND" 2>&1 | while IFS= read -r line; do
    log_message "OUTPUT: $line"
done

exit_code=${PIPESTATUS[0]}

if [[ $exit_code -eq 0 ]]; then
    log_message "✅ Successfully executed: $COMMAND"
else
    log_message "❌ Failed to execute: $COMMAND (exit code: $exit_code)"
fi

exit $exit_code
EOF

    chmod +x "$SLASH_SCRIPT"
    echo "✅ Created slash command execution script: $SLASH_SCRIPT"
}

# Setup cron jobs for slash commands
setup_slash_cron() {
    local command="$1"
    local schedule="$2"
    local project_dir="${3:-}"
    local name="${4:-$(echo "$command" | sed 's/[^a-zA-Z0-9]/_/g')}"

    if [[ -z "$command" || -z "$schedule" ]]; then
        echo "❌ Usage: setup_slash_cron <command> <schedule> [project_dir] [name]"
        echo "   Example: setup_slash_cron '/daily-standup' '9,17' '/path/to/project' 'standup'"
        return 1
    fi

    echo "Setting up automated slash command: $command"
    echo "Schedule: $schedule"
    [[ -n "$project_dir" ]] && echo "Project directory: $project_dir"

    # Create slash execution script if it doesn't exist
    [[ ! -f "$SLASH_SCRIPT" ]] && create_slash_script

    # Store configuration
    local config_file="$CONFIG_DIR/${name}.conf"
    cat > "$config_file" << EOF
COMMAND='$command'
SCHEDULE='$schedule'
PROJECT_DIR='$project_dir'
NAME='$name'
CREATED='$(date '+%Y-%m-%d %H:%M:%S')'
EOF

    # Generate cron entries
    local cron_entries=""
    IFS=',' read -ra HOURS <<< "$schedule"

    for hour in "${HOURS[@]}"; do
        hour=$(echo "$hour" | xargs)  # trim whitespace
        if [[ "$hour" =~ ^[0-9]+$ && "$hour" -ge 0 && "$hour" -le 23 ]]; then
            if [[ -n "$project_dir" ]]; then
                cron_entries+="0 $hour * * * $SLASH_SCRIPT \"$command\" \"$project_dir\""$'\n'
            else
                cron_entries+="0 $hour * * * $SLASH_SCRIPT \"$command\""$'\n'
            fi
        else
            echo "⚠️  Invalid hour: $hour (skipping)"
        fi
    done

    if [[ -z "$cron_entries" ]]; then
        echo "❌ No valid hours found in schedule"
        return 1
    fi

    # Update crontab
    local temp_cron=$(mktemp)
    local comment_marker="# Claude Slash: $name"

    # Add existing crontab (excluding old entries for this slash command)
    crontab -l 2>/dev/null | grep -v "$comment_marker" > "$temp_cron" || true

    # Add new entries
    echo "" >> "$temp_cron"
    echo "$comment_marker" >> "$temp_cron"
    echo -n "$cron_entries" >> "$temp_cron"

    # Install the new crontab
    crontab "$temp_cron"
    rm "$temp_cron"

    echo "✅ Automated slash command scheduled successfully!"
    echo "📝 Configuration saved: $config_file"
    echo "📊 Use './claude_slash_cron.sh status' to check active commands"
    echo "🛑 Use './claude_slash_cron.sh remove $name' to stop this automation"
}

# Remove slash command automation
remove_slash_cron() {
    local name="$1"

    if [[ -z "$name" ]]; then
        echo "❌ Usage: remove_slash_cron <name>"
        echo "📊 Use './claude_slash_cron.sh list' to see available automations"
        return 1
    fi

    local config_file="$CONFIG_DIR/${name}.conf"
    local comment_marker="# Claude Slash: $name"

    # Remove from crontab
    crontab -l 2>/dev/null | grep -v "$comment_marker" | crontab - || true

    # Remove config file
    [[ -f "$config_file" ]] && rm "$config_file"

    echo "✅ Removed slash command automation: $name"
}

# List all automated slash commands
list_slash_commands() {
    echo "📋 Automated Slash Commands"
    echo "=========================="

    if [[ ! -d "$CONFIG_DIR" ]] || [[ -z "$(ls -A "$CONFIG_DIR" 2>/dev/null)" ]]; then
        echo "No automated slash commands configured."
        return 0
    fi

    for config_file in "$CONFIG_DIR"/*.conf; do
        [[ ! -f "$config_file" ]] && continue

        echo
        # shellcheck source=/dev/null
        source "$config_file"

        echo "Name: $NAME"
        echo "Command: $COMMAND"
        echo "Schedule: $SCHEDULE (hours)"
        [[ -n "$PROJECT_DIR" ]] && echo "Directory: $PROJECT_DIR"
        echo "Created: $CREATED"
        echo "Status: $(crontab -l 2>/dev/null | grep -q "# Claude Slash: $NAME" && echo "✅ Active" || echo "❌ Inactive")"
    done
}

# Show status and recent activity
show_status() {
    echo "📊 Claude Slash Command Automation Status"
    echo "========================================"

    # Count active automations
    local count=0
    if [[ -d "$CONFIG_DIR" ]]; then
        count=$(find "$CONFIG_DIR" -name "*.conf" 2>/dev/null | wc -l | xargs)
    fi

    echo "Active automations: $count"
    echo

    # Show cron jobs
    echo "Active Cron Jobs:"
    crontab -l 2>/dev/null | grep -E "Claude Slash:|run_slash_command.sh" || echo "  No slash command cron jobs found"

    echo
    echo "Recent Activity (last 20 entries):"
    if [[ -f "$LOG_FILE" ]]; then
        tail -20 "$LOG_FILE" | while IFS= read -r line; do
            echo "  $line"
        done
    else
        echo "  No activity logged yet"
    fi
}

# Interactive setup
interactive_setup() {
    echo "🔧 Claude Slash Command Automation Setup"
    echo "========================================"
    echo
    echo "This tool automates execution of your custom Claude Code slash commands"
    echo "on a daily schedule, perfect for workflows like:"
    echo
    echo "• Daily standups (/daily-standup)"
    echo "• Code reviews (/review-prs)"
    echo "• Deployment checks (/check-deploy)"
    echo "• Security audits (/security-scan)"
    echo "• Performance monitoring (/perf-check)"
    echo

    read -r -p "Enter your slash command (e.g., /daily-standup): " command
    if [[ -z "$command" ]]; then
        echo "❌ Command cannot be empty"
        return 1
    fi

    echo
    echo "💡 Popular schedules:"
    echo "• Daily morning: 9"
    echo "• Twice daily: 9,17"
    echo "• Business hours: 9,12,15,17"
    echo "• Custom: enter comma-separated hours (0-23)"
    echo

    read -r -p "Enter schedule (hours, comma-separated): " schedule
    if [[ -z "$schedule" ]]; then
        echo "❌ Schedule cannot be empty"
        return 1
    fi

    echo
    echo "🗂️  Project Directory Selection:"
    echo "• Leave empty: Use current directory when command runs"
    echo "• Enter path: Run command in specific project directory"
    echo "• Examples: ~/myproject, /path/to/repo, ../other-project"
    echo
    read -r -p "Project directory (leave empty for current): " project_dir

    # Validate directory if provided
    if [[ -n "$project_dir" ]]; then
        # Expand tilde and resolve path
        project_dir="${project_dir/#\~/$HOME}"
        project_dir=$(realpath "$project_dir" 2>/dev/null || echo "$project_dir")

        if [[ ! -d "$project_dir" ]]; then
            echo "⚠️  Directory doesn't exist: $project_dir"
            read -r -p "Create it? (y/n): " create_dir
            if [[ "$create_dir" =~ ^[Yy]$ ]]; then
                mkdir -p "$project_dir" || {
                    echo "❌ Failed to create directory"
                    return 1
                }
                echo "✅ Created directory: $project_dir"
            else
                echo "❌ Using non-existent directory may cause command failures"
            fi
        else
            echo "✅ Directory exists: $project_dir"
        fi
    fi

    echo
    read -r -p "Automation name (leave empty for auto-generated): " name

    # Generate name if not provided
    if [[ -z "$name" ]]; then
        name=$(echo "$command" | sed 's/[^a-zA-Z0-9]/_/g' | sed 's/^_//' | sed 's/_$//')
    fi

    echo
    echo "📋 Summary:"
    echo "Command: $command"
    echo "Schedule: $schedule"
    echo "Directory: ${project_dir:-current directory}"
    echo "Name: $name"
    echo

    read -r -p "Create this automation? (y/n): " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        setup_slash_cron "$command" "$schedule" "$project_dir" "$name"
    else
        echo "❌ Automation cancelled"
    fi
}

# Main command handling
case "${1:-}" in
    "setup")
        if [[ $# -ge 3 ]]; then
            setup_slash_cron "$2" "$3" "$4" "$5"
        else
            interactive_setup
        fi
        ;;
    "remove")
        remove_slash_cron "$2"
        ;;
    "list")
        list_slash_commands
        ;;
    "status")
        show_status
        ;;
    "create-script")
        create_slash_script
        ;;
    *)
        echo "🤖 Claude Slash Command Automation"
        echo "================================="
        echo
        echo "Automate your Claude Code custom slash commands on a daily schedule!"
        echo
        echo "Usage:"
        echo "  $0 setup [command] [schedule] [project_dir] [name]"
        echo "  $0 remove <name>"
        echo "  $0 list"
        echo "  $0 status"
        echo "  $0 create-script"
        echo
        echo "Examples:"
        echo "  $0 setup                                    # Interactive setup"
        echo "  $0 setup '/daily-standup' '9,17'           # Standup at 9am and 5pm (current dir)"
        echo "  $0 setup '/review-prs' '10' '~/myproject'  # PR review at 10am in ~/myproject"
        echo "  $0 setup '/deploy-check' '14' '/var/www'   # Deploy check at 2pm in /var/www"
        echo "  $0 remove standup                          # Remove standup automation"
        echo "  $0 status                                   # Show current automations"
        echo
        echo "📁 Directory Usage:"
        echo "• Current directory: Command runs wherever you are when it executes"
        echo "• Specific directory: Command always runs in the specified project folder"
        echo "• Use absolute paths (/home/user/project) or tilde (~user/project)"
        echo
        echo "💡 Perfect for automating:"
        echo "• Daily standups and team updates"
        echo "• Automated code reviews and PR checks"
        echo "• Security scans and compliance checks"
        echo "• Performance monitoring and alerts"
        echo "• Deployment verification workflows"
        ;;
esac
