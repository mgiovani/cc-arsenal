#!/bin/bash
# Statusline component builders

source "$(dirname "${BASH_SOURCE[0]}")/colors.sh"
source "$(dirname "${BASH_SOURCE[0]}")/utils.sh"
source "$(dirname "${BASH_SOURCE[0]}")/git_info.sh"

# Model component
get_model_component() {
    local model="$1"
    local model_version="$2"
    local model_short

    # If no model data available, show unavailable
    if [[ "$model" == "unavailable" || -z "$model" ]]; then
        echo "${STATUSLINE_DIM}🤖 Unavailable${STATUSLINE_RESET}"
        return
    fi

    model_short=$(echo "$model" | sed 's/claude-//' | sed 's/-20[0-9]\{6\}//')

    if [[ -n "$model_version" && "$model_version" != "$model" ]]; then
        echo "${STATUSLINE_BRIGHT_BLUE}🤖 ${model_short}${STATUSLINE_GRAY}@${model_version}${STATUSLINE_RESET}"
    else
        echo "${STATUSLINE_BRIGHT_BLUE}🤖 ${model_short}${STATUSLINE_RESET}"
    fi
}

get_model_component_compact() {
    local model="$1"
    local model_short

    # If no model data available, show unavailable
    if [[ "$model" == "unavailable" || -z "$model" ]]; then
        echo "${STATUSLINE_DIM}🤖Unavailable${STATUSLINE_RESET}"
        return
    fi

    model_short=$(echo "$model" | sed 's/claude-/c/' | sed 's/sonnet/s/' | sed 's/haiku/h/' | sed 's/opus/o/' | head -c 10)
    echo "${STATUSLINE_BRIGHT_BLUE}🤖${model_short}${STATUSLINE_RESET}"
}

# Directory component
get_directory_component() {
    local current_dir="$1"
    local dir_display

    # Get display mode from config (default to "short")
    local display_mode
    display_mode=$(get_config '.formatting.directory_display_mode' 'short')

    case "$display_mode" in
        "full")
            dir_display="$current_dir"
            ;;
        "short"|*)
            dir_display=$(shorten_path "$current_dir")
            ;;
    esac

    echo "${STATUSLINE_BRIGHT_CYAN}📁 ${dir_display}${STATUSLINE_RESET}"
}

get_directory_component_compact() {
    local current_dir="$1"
    local dir_short

    dir_short=$(basename "$current_dir")
    if [[ ${#dir_short} -gt 12 ]]; then
        dir_short="${dir_short:0:9}..."
    fi
    echo "${STATUSLINE_BRIGHT_CYAN}📁${dir_short}${STATUSLINE_RESET}"
}

# Context component
get_context_component() {
    local context_percent="$1"
    local color

    # Handle unavailable context data
    if [[ "$context_percent" == "unavailable" ]]; then
        echo "${STATUSLINE_DIM}📊 N/A${STATUSLINE_RESET}"
        return
    fi

    # If context_percent is empty or not a number, show unavailable
    if [[ -z "$context_percent" || ! "$context_percent" =~ ^[0-9]+$ ]]; then
        echo "${STATUSLINE_DIM}📊 N/A${STATUSLINE_RESET}"
        return
    fi

    color=$(get_context_color "$context_percent")
    echo "${color}📊 ${context_percent}%${STATUSLINE_RESET}"
}

get_context_component_compact() {
    local context_percent="$1"
    local color

    # Handle unavailable context data
    if [[ "$context_percent" == "unavailable" ]]; then
        echo "${STATUSLINE_DIM}📊N/A${STATUSLINE_RESET}"
        return
    fi

    # If context_percent is empty or not a number, show unavailable
    if [[ -z "$context_percent" || ! "$context_percent" =~ ^[0-9]+$ ]]; then
        echo "${STATUSLINE_DIM}📊N/A${STATUSLINE_RESET}"
        return
    fi

    color=$(get_context_color "$context_percent")
    echo "${color}📊${context_percent}%${STATUSLINE_RESET}"
}

# Cost components
get_session_cost_component() {
    local session_cost_display="$1"

    if [[ -n "$session_cost_display" && "$session_cost_display" != "0.000" && "$session_cost_display" != "0.00" ]]; then
        if [[ "$session_cost_display" =~ ^[0-9]+→[0-9]+$ ]]; then
            echo "${STATUSLINE_YELLOW}🎯 ${session_cost_display}${STATUSLINE_RESET}"
        else
            echo "${STATUSLINE_YELLOW}💰 \$${session_cost_display}${STATUSLINE_RESET}"
        fi
    else
        echo "${STATUSLINE_DIM}💰 Unavailable${STATUSLINE_RESET}"
    fi
}

get_session_cost_component_compact() {
    local session_cost_display="$1"

    if [[ -n "$session_cost_display" && "$session_cost_display" != "0.000" && "$session_cost_display" != "0.00" ]]; then
        if [[ "$session_cost_display" =~ ^[0-9]+→[0-9]+$ ]]; then
            echo "${STATUSLINE_YELLOW}🎯${session_cost_display}${STATUSLINE_RESET}"
        else
            echo "${STATUSLINE_YELLOW}💰\$${session_cost_display}${STATUSLINE_RESET}"
        fi
    else
        echo "${STATUSLINE_DIM}💰Unavailable${STATUSLINE_RESET}"
    fi
}

# Daily cost component
get_daily_cost_component() {
    local daily_cost_display="$1"

    if [[ -n "$daily_cost_display" && "$daily_cost_display" != "0.00" ]]; then
        echo "${STATUSLINE_BRIGHT_YELLOW}📅 \$${daily_cost_display}${STATUSLINE_RESET}"
    else
        echo "${STATUSLINE_GRAY}📅 \$0.00${STATUSLINE_RESET}"
    fi
}

get_daily_cost_component_compact() {
    local daily_cost_display="$1"

    if [[ -n "$daily_cost_display" && "$daily_cost_display" != "0.00" ]]; then
        echo "${STATUSLINE_BRIGHT_YELLOW}📅\$${daily_cost_display}${STATUSLINE_RESET}"
    else
        echo "${STATUSLINE_GRAY}📅\$0.00${STATUSLINE_RESET}"
    fi
}

# Duration info component (from Claude Code API timing)
get_duration_info_component() {
    local total_duration_ms="$1"
    local api_duration_ms="$2"

    if [[ -z "$total_duration_ms" || "$total_duration_ms" == "0" ]]; then
        return
    fi

    # Convert to seconds for display
    local total_sec=$((total_duration_ms / 1000))
    local api_sec=$((api_duration_ms / 1000))

    if [[ $total_sec -gt 0 ]]; then
        if [[ $api_sec -gt 0 ]]; then
            echo "${STATUSLINE_GRAY}⏱️ ${total_sec}s (${api_sec}s)${STATUSLINE_RESET}"
        else
            echo "${STATUSLINE_GRAY}⏱️ ${total_sec}s${STATUSLINE_RESET}"
        fi
    fi
}

get_duration_info_component_compact() {
    local total_duration_ms="$1"

    if [[ -z "$total_duration_ms" || "$total_duration_ms" == "0" ]]; then
        return
    fi

    local total_sec=$((total_duration_ms / 1000))
    if [[ $total_sec -gt 0 ]]; then
        echo "${STATUSLINE_GRAY}⏱️${total_sec}s${STATUSLINE_RESET}"
    fi
}

# Lines changed component (from Claude Code API data)
get_lines_changed_component() {
    local lines_added="$1"
    local lines_removed="$2"

    if [[ -z "$lines_added" || "$lines_added" == "0" ]] && [[ -z "$lines_removed" || "$lines_removed" == "0" ]]; then
        return
    fi

    local display=""
    if [[ "$lines_added" != "0" && -n "$lines_added" ]]; then
        display="${STATUSLINE_GREEN}+${lines_added}${STATUSLINE_RESET}"
    fi
    if [[ "$lines_removed" != "0" && -n "$lines_removed" ]]; then
        if [[ -n "$display" ]]; then
            display="${display}/${STATUSLINE_RED}-${lines_removed}${STATUSLINE_RESET}"
        else
            display="${STATUSLINE_RED}-${lines_removed}${STATUSLINE_RESET}"
        fi
    fi

    if [[ -n "$display" ]]; then
        echo "${STATUSLINE_GRAY}📝 ${display}${STATUSLINE_RESET}"
    fi
}

get_lines_changed_component_compact() {
    local lines_added="$1"
    local lines_removed="$2"

    if [[ -z "$lines_added" || "$lines_added" == "0" ]] && [[ -z "$lines_removed" || "$lines_removed" == "0" ]]; then
        return
    fi

    local display=""
    if [[ "$lines_added" != "0" && -n "$lines_added" ]]; then
        display="${STATUSLINE_GREEN}+${lines_added}${STATUSLINE_RESET}"
    fi
    if [[ "$lines_removed" != "0" && -n "$lines_removed" ]]; then
        if [[ -n "$display" ]]; then
            display="${display}${STATUSLINE_RED}-${lines_removed}${STATUSLINE_RESET}"
        else
            display="${STATUSLINE_RED}-${lines_removed}${STATUSLINE_RESET}"
        fi
    fi

    if [[ -n "$display" ]]; then
        echo "${STATUSLINE_GRAY}📝${display}${STATUSLINE_RESET}"
    fi
}

# Reset countdown component
get_reset_component() {
    local next_reset="$1"
    local reset_color

    if [[ -n "$next_reset" && "$next_reset" != "5h0m" ]]; then
        if [[ "$next_reset" == "now" ]]; then
            echo "${STATUSLINE_BRIGHT_GREEN}🔄 reset!${STATUSLINE_RESET}"
        else
            reset_color=$(get_reset_color "$next_reset")
            echo "${reset_color}🔄 ${next_reset}${STATUSLINE_RESET}"
        fi
    fi
}

get_reset_component_compact() {
    local next_reset="$1"
    local reset_color

    if [[ -n "$next_reset" && "$next_reset" != "5h0m" ]]; then
        if [[ "$next_reset" == "now" ]]; then
            echo "${STATUSLINE_BRIGHT_GREEN}🔄!${STATUSLINE_RESET}"
        else
            reset_color=$(get_reset_color "$next_reset")
            echo "${reset_color}🔄${next_reset}${STATUSLINE_RESET}"
        fi
    fi
}

# Session duration component
get_session_duration_component() {
    local session_duration="$1"

    if [[ -n "$session_duration" ]]; then
        echo "${STATUSLINE_GRAY}⏰ ${session_duration}${STATUSLINE_RESET}"
    fi
}

# Schedule component - shows next scheduled task or current window info
get_schedule_component() {
    local schedule_info="$1"

    if [[ -z "$schedule_info" || "$schedule_info" == "null" ]]; then
        # Try to get schedule info from the scheduler
        schedule_info=$(get_current_schedule_info 2>/dev/null || echo "")
    fi

    if [[ -n "$schedule_info" ]]; then
        echo "${STATUSLINE_BRIGHT_PURPLE}📅 ${schedule_info}${STATUSLINE_RESET}"
    fi
}

get_schedule_component_compact() {
    local schedule_info="$1"

    if [[ -z "$schedule_info" || "$schedule_info" == "null" ]]; then
        schedule_info=$(get_current_schedule_info 2>/dev/null || echo "")
    fi

    if [[ -n "$schedule_info" ]]; then
        # Compact format - truncate if too long
        local compact_info="$schedule_info"
        if [[ ${#compact_info} -gt 15 ]]; then
            compact_info="${compact_info:0:12}..."
        fi
        echo "${STATUSLINE_BRIGHT_PURPLE}📅${compact_info}${STATUSLINE_RESET}"
    fi
}

# Helper function to get current schedule information
get_current_schedule_info() {
    local schedule_dir="$HOME/.claude/schedule"
    local schedule_config="$schedule_dir/config.json"
    local schedule_tasks="$schedule_dir/tasks.json"

    # Check if scheduler is configured
    if [[ ! -f "$schedule_config" ]]; then
        return
    fi

    # Check for next scheduled task
    if [[ -f "$schedule_tasks" ]] && command -v jq >/dev/null 2>&1; then
        local next_task
        next_task=$(jq -r '
            .tasks[]?
            | select(.enabled == true and .status == "pending" and .next_run != null)
            | {name: .name, next_run: .next_run, priority: .priority}
        ' "$schedule_tasks" 2>/dev/null | jq -r '
            select(.next_run > now | todate)
            | "\(.name) @ \(.next_run | fromdateiso8601 | strftime("%H:%M"))"
        ' 2>/dev/null | head -1)

        if [[ -n "$next_task" ]]; then
            echo "$next_task"
            return
        fi
    fi

    # Fallback: show current Claude window info
    local current_hour
    current_hour=$(date +%H | sed 's/^0//')

    if [[ $current_hour -ge 9 && $current_hour -lt 14 ]]; then
        echo "Morning Window"
    elif [[ $current_hour -ge 14 && $current_hour -lt 19 ]]; then
        echo "Afternoon Window"
    elif [[ $current_hour -ge 19 ]]; then
        echo "Evening Window"
    elif [[ $current_hour -ge 0 && $current_hour -lt 5 ]]; then
        echo "Night Window"
    else
        echo "Early Morning Window"
    fi
}
