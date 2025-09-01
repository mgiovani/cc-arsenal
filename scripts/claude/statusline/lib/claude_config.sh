#!/bin/bash
# Claude Code settings.json integration

# Constants
readonly CLAUDE_SETTINGS="$HOME/.claude/settings.json"
readonly STATUSLINE_SCRIPT="$HOME/.claude/scripts/claude/statusline/statusline.sh"

# Backup settings before modification
backup_claude_settings() {
    if [[ -f "$CLAUDE_SETTINGS" ]]; then
        local backup_file="$CLAUDE_SETTINGS.backup-$(date +%s)"
        cp "$CLAUDE_SETTINGS" "$backup_file"
        echo "Backed up existing settings to: $backup_file"
        echo "$backup_file"
    fi
}

# Check if statusline is already configured
is_statusline_configured() {
    if [[ -f "$CLAUDE_SETTINGS" ]]; then
        jq -e '.statusLine' "$CLAUDE_SETTINGS" >/dev/null 2>&1
    else
        return 1
    fi
}

# Get current statusline configuration
get_current_statusline() {
    if [[ -f "$CLAUDE_SETTINGS" ]]; then
        jq -r '.statusLine.command // empty' "$CLAUDE_SETTINGS" 2>/dev/null
    fi
}

# Create default Claude settings structure
create_default_settings() {
    cat <<'EOF'
{
  "statusLine": {
    "type": "command",
    "command": "bash ~/.claude/scripts/claude/statusline/statusline.sh",
    "padding": 0
  }
}
EOF
}

# Add statusline configuration to existing settings
add_statusline_to_settings() {
    local temp_file
    temp_file=$(mktemp)

    if [[ -f "$CLAUDE_SETTINGS" ]]; then
        # Merge with existing settings
        jq '. + {
            "statusLine": {
                "type": "command",
                "command": "bash ~/.claude/scripts/claude/statusline/statusline.sh",
                "padding": 0
            }
        }' "$CLAUDE_SETTINGS" > "$temp_file"
    else
        # Create new settings file
        create_default_settings > "$temp_file"
    fi

    # Validate JSON before applying
    if jq . "$temp_file" >/dev/null 2>&1; then
        mkdir -p "$(dirname "$CLAUDE_SETTINGS")"
        mv "$temp_file" "$CLAUDE_SETTINGS"
        return 0
    else
        rm -f "$temp_file"
        return 1
    fi
}

# Remove statusline configuration
remove_statusline_from_settings() {
    if [[ -f "$CLAUDE_SETTINGS" ]]; then
        local temp_file
        temp_file=$(mktemp)

        jq 'del(.statusLine)' "$CLAUDE_SETTINGS" > "$temp_file"

        if jq . "$temp_file" >/dev/null 2>&1; then
            mv "$temp_file" "$CLAUDE_SETTINGS"
            return 0
        else
            rm -f "$temp_file"
            return 1
        fi
    fi
}

# Install statusline configuration
install_statusline_config() {
    local force="$1"
    local backup_file=""

    echo "🔧 Configuring Claude Code settings..."

    # Check if already configured
    if is_statusline_configured; then
        local current_command
        current_command=$(get_current_statusline)

        if [[ "$force" != "true" && "$force" != "force" ]]; then
            echo "⚠️  Statusline already configured:"
            echo "   Current: $current_command"
            echo
            read -p "Replace existing statusline configuration? (y/N): " replace
            if [[ "$replace" != "y" && "$replace" != "Y" ]]; then
                echo "❌ Statusline configuration cancelled"
                return 1
            fi
        fi

        # Create backup
        backup_file=$(backup_claude_settings)
    fi

    # Install new configuration
    if add_statusline_to_settings; then
        echo "✅ Successfully configured Claude Code statusline!"
        echo "📍 Settings file: $CLAUDE_SETTINGS"
        echo "🎯 Statusline script: $STATUSLINE_SCRIPT"

        if [[ -n "$backup_file" ]]; then
            echo "💾 Backup created: $backup_file"
        fi

        return 0
    else
        echo "❌ Failed to configure statusline"

        # Restore backup if exists
        if [[ -n "$backup_file" && -f "$backup_file" ]]; then
            echo "🔄 Restoring backup..."
            mv "$backup_file" "$CLAUDE_SETTINGS"
        fi

        return 1
    fi
}

# Uninstall statusline configuration
uninstall_statusline_config() {
    echo "🔧 Removing statusline configuration..."

    if ! is_statusline_configured; then
        echo "ℹ️  No statusline configuration found"
        return 0
    fi

    # Create backup
    local backup_file
    backup_file=$(backup_claude_settings)

    if remove_statusline_from_settings; then
        echo "✅ Statusline configuration removed"
        echo "💾 Backup created: $backup_file"
        return 0
    else
        echo "❌ Failed to remove statusline configuration"
        return 1
    fi
}

# Show current statusline configuration
show_statusline_config() {
    echo "📋 Current Claude Code Statusline Configuration:"
    echo

    if [[ -f "$CLAUDE_SETTINGS" ]]; then
        if is_statusline_configured; then
            echo "✅ Statusline is configured"

            local command
            command=$(get_current_statusline)
            echo "📍 Command: $command"

            # Check if the script exists
            if [[ -f "$STATUSLINE_SCRIPT" ]]; then
                echo "🎯 Script: Available"
            else
                echo "⚠️  Script: Missing ($STATUSLINE_SCRIPT)"
            fi

            # Show full configuration
            echo
            echo "Full configuration:"
            jq '.statusLine' "$CLAUDE_SETTINGS" 2>/dev/null || echo "Error reading configuration"
        else
            echo "❌ Statusline is not configured"
            echo "💡 Run installation to configure it"
        fi
    else
        echo "❌ No Claude Code settings file found"
        echo "📁 Expected location: $CLAUDE_SETTINGS"
    fi
}

# Main function for command-line usage
main() {
    local action="$1"
    local force="$2"

    case "$action" in
        "install")
            install_statusline_config "$force"
            ;;
        "uninstall")
            uninstall_statusline_config
            ;;
        "show"|"status")
            show_statusline_config
            ;;
        "is-configured")
            is_statusline_configured
            ;;
        *)
            echo "Usage: $0 {install|uninstall|show|is-configured} [force]"
            echo
            echo "Commands:"
            echo "  install      - Configure Claude Code statusline"
            echo "  uninstall    - Remove statusline configuration"
            echo "  show         - Show current configuration"
            echo "  is-configured - Check if statusline is configured (exit code)"
            echo
            echo "Options:"
            echo "  force        - Skip confirmation prompts"
            exit 1
            ;;
    esac
}

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
