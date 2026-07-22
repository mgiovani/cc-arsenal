#!/bin/bash
# =============================================================================
# Display Components - Individual statusline component builders
# =============================================================================
# Provides functions for building each statusline component with consistent
# formatting and error handling.

# Guard clause - prevent multiple sourcing
if [[ -n "${STATUSLINE_COMPONENTS_LOADED:-}" ]]; then
    return 0
fi
readonly STATUSLINE_COMPONENTS_LOADED=1

# Source dependencies
STATUSLINE_DISPLAY_DIR="$(dirname "${BASH_SOURCE[0]}")"
source "$STATUSLINE_DISPLAY_DIR/colors.sh"
source "$STATUSLINE_DISPLAY_DIR/../api/git.sh"
source "$STATUSLINE_DISPLAY_DIR/../core/platform.sh"
source "$STATUSLINE_DISPLAY_DIR/../core/json.sh"
source "$STATUSLINE_DISPLAY_DIR/../config.sh"

# =============================================================================
# Text Mode Helpers
# =============================================================================

# Get component prefix based on display mode
# Usage: get_prefix "🤖" "Mod:" "[M]"
# In emoji mode: returns "🤖 " (emoji + space)
# In text mode:  returns "Mod: " (text + space)
# In ascii mode: returns "[M] " (ascii + space)
get_prefix() {
    local emoji="$1"
    local text="$2"
    local ascii="${3:-$text}"  # Default to text if no ascii provided

    local mode
    mode=$(get_display_mode)
    case "$mode" in
        text)  echo "${text} " ;;
        ascii) echo "${ascii} " ;;
        *)     echo "${emoji} " ;;
    esac
}

# =============================================================================
# Model Component
# =============================================================================

# Display model name with icon
# Usage: get_model_component "opus" or "claude-opus-4-6"
get_model_component() {
    local model="${1:-}"
    local prefix
    prefix=$(get_prefix "🤖" "Mod:" "[M]")

    if [[ -z "$model" || "$model" == "null" ]]; then
        echo "${prefix}Unavailable"
        return 0
    fi

    # If model looks like a display name (e.g., "Opus", "Sonnet"), use it directly
    if [[ "$model" =~ ^[A-Z][a-z]+$ ]]; then
        echo "${prefix}$model"
        return 0
    fi

    # Process model.id for backwards compatibility
    local display="$model"
    display="${display#claude-}"
    display="${display%-[0-9]*}"
    display="${display/sonnet-/Sonnet }"
    display="${display/opus-/Opus }"
    display="${display/haiku-/Haiku }"

    # Safe capitalization
    if [[ ${#display} -gt 0 ]]; then
        local first="${display:0:1}"
        local rest="${display:1}"
        first=$(echo "$first" | tr '[:lower:]' '[:upper:]' 2>/dev/null || echo "$first")
        display="${first}${rest}"
    fi

    echo "${prefix}$display"
}

# =============================================================================
# Directory Component
# =============================================================================

# Display current directory with icon
# Usage: get_directory_component "/path/to/dir"
get_directory_component() {
    local dir="${1:-$(pwd)}"
    local short_dir="$dir"
    local prefix
    prefix=$(get_prefix "📁" "Dir:" "[D]")

    # Replace home with ~
    if [[ "$dir" == "$HOME"* ]]; then
        short_dir="~${dir#$HOME}"
    fi

    # Truncate if too long
    if [[ ${#short_dir} -gt 30 ]]; then
        local base="${dir##*/}"
        short_dir=".../$base"
    fi

    echo "${prefix}$short_dir"
}

# =============================================================================
# Git Component
# =============================================================================

# Display git branch with status indicator
# Usage: get_git_component ["native_branch"]
get_git_component() {
    local native_branch="${1:-}"

    # Priority 1: Native worktree.branch from Claude Code JSON
    if [[ -n "$native_branch" && "$native_branch" != "null" ]]; then
        local prefix
        prefix=$(get_prefix "🌿" "Git:" "[G]")
        echo "${prefix}${native_branch}"
        return 0
    fi

    # Priority 2: Git-based detection (fallback)
    local git_info
    git_info=$(get_git_info 2>/dev/null || echo "0|not_a_repo|")

    # Parse the pipe-separated values: changes|branch|worktree
    local changes branch worktree
    changes="${git_info%%|*}"
    local rest="${git_info#*|}"
    branch="${rest%%|*}"
    worktree="${rest#*|}"

    if [[ "$branch" == "not_a_repo" ]]; then
        return 0  # No git component
    fi

    local prefix
    prefix=$(get_prefix "🌿" "Git:" "[G]")

    local status_symbol=""
    if [[ "$changes" -gt 0 ]] 2>/dev/null; then
        if is_ascii_mode; then
            status_symbol=" *"
        else
            status_symbol=" ●"
        fi
    fi

    echo "${prefix}${branch}${status_symbol}"
}

# =============================================================================
# Worktree Component
# =============================================================================

# Display git worktree name if in a worktree
# Usage: get_worktree_component ["native_name"]
get_worktree_component() {
    local native_name="${1:-}"

    # Priority 1: Native worktree.name from Claude Code JSON
    if [[ -n "$native_name" && "$native_name" != "null" ]]; then
        local prefix
        prefix=$(get_prefix "🌳" "Wt:" "[W]")
        echo "${prefix}$native_name"
        return 0
    fi

    # Priority 2: Git-based detection (fallback)
    local git_info
    git_info=$(get_git_info 2>/dev/null || echo "0|not_a_repo|")

    # Parse the pipe-separated values: changes|branch|worktree
    local rest="${git_info#*|}"
    rest="${rest#*|}"
    local worktree="$rest"

    # Only show if we're in a worktree
    if [[ -n "$worktree" ]]; then
        local prefix
        prefix=$(get_prefix "🌳" "Wt:" "[W]")
        echo "${prefix}$worktree"
    fi
}

# =============================================================================
# Context Component
# =============================================================================

# Display context window usage percentage
# Usage: get_context_component "$used_percentage"
get_context_component() {
    local used_percentage="${1:-}"
    local prefix
    prefix=$(get_prefix "📊" "Ctx:" "[C]")

    # Use percentage from Claude Code
    if [[ -n "$used_percentage" && "$used_percentage" != "null" ]]; then
        # Round to integer for display (add 0.5 and truncate using awk)
        local percent
        percent=$(awk -v n="$used_percentage" 'BEGIN { printf "%d", n + 0.5 }' 2>/dev/null || echo "${used_percentage%.*}")
        echo "${prefix}${percent}%"
        return 0
    fi

    # Fallback: show 0% for new sessions
    echo "${prefix}0%"
}

# =============================================================================
# Cost Component
# =============================================================================

# Display session cost
# Usage: get_cost_component "1.25"
get_cost_component() {
    local cost="${1:-}"

    # Cost already has $ prefix, so no text/ascii label needed
    local prefix
    local mode
    mode=$(get_display_mode)
    case "$mode" in
        text|ascii) prefix="" ;;  # No prefix, $ is self-explanatory
        *)          prefix="💰 " ;;
    esac

    # For new sessions with no cost, show $0.00
    if [[ -z "$cost" || "$cost" == "0" || "$cost" == "null" ]]; then
        echo "${prefix}\$0.00"
        return 0
    fi

    local formatted
    formatted=$(printf "%.3f" "$cost" 2>/dev/null || echo "$cost")
    echo "${prefix}\$${formatted}"
}

# =============================================================================
# Lines Changed Component
# =============================================================================

# Display lines added/removed
# Usage: get_lines_component "$added" "$removed"
get_lines_component() {
    local added="${1:-0}" removed="${2:-0}"

    if [[ "$added" == "0" && "$removed" == "0" ]] || \
        [[ -z "$added" || -z "$removed" ]]; then
        return 0  # No component
    fi

    # Use delta symbol (Δ) for text mode, +/- for ascii mode
    local prefix
    if is_ascii_mode; then
        prefix="+/- "
    else
        prefix=$(get_prefix "📝" "Δ" "+/-")
    fi

    local display=""
    if [[ "$added" -gt 0 ]] 2>/dev/null; then
        display="+$added"
    fi
    if [[ "$removed" -gt 0 ]] 2>/dev/null; then
        if [[ -n "$display" ]]; then
            display="$display/-$removed"
        else
            display="-$removed"
        fi
    fi

    if [[ -n "$display" ]]; then
        echo "${prefix}$display"
    fi
}

# =============================================================================
# Session Duration Component
# =============================================================================

# Display session duration from Claude Code's total_duration_ms
# Usage: get_session_component "$json"
get_session_component() {
    local json="${1:-}"
    local duration_ms

    # Try to extract duration from JSON
    if [[ -n "$json" ]] && check_jq 2>/dev/null; then
        duration_ms=$(echo "$json" | jq -r '.cost.total_duration_ms // 0' 2>/dev/null || echo "0")
    else
        duration_ms="0"
    fi

    if [[ "$duration_ms" == "0" || -z "$duration_ms" || "$duration_ms" == "null" ]]; then
        return 0  # Don't show component until session starts
    fi

    # Convert milliseconds to human readable format
    local seconds=$((duration_ms / 1000))
    local minutes=$((seconds / 60))
    local hours=$((minutes / 60))

    local duration_display
    if [[ $hours -gt 0 ]]; then
        local remaining_minutes=$((minutes % 60))
        if [[ $remaining_minutes -gt 0 ]]; then
            duration_display="${hours}h${remaining_minutes}m"
        else
            duration_display="${hours}h"
        fi
    elif [[ $minutes -gt 0 ]]; then
        duration_display="${minutes}m"
    else
        duration_display="${seconds}s"
    fi

    # Duration is self-explanatory, no prefix needed in text/ascii mode
    local mode
    mode=$(get_display_mode)
    case "$mode" in
        text|ascii) echo "$duration_display" ;;
        *)          echo "⏱️ $duration_display" ;;
    esac
}

# =============================================================================
# Account Badge Component
# =============================================================================

# Display the active account label when multi-account mode is configured
# Usage: get_account_component
get_account_component() {
    if [[ -z "${CLAUDE_CODE_OAUTH_TOKEN:-}" || -z "${CLAUDE_STATUSLINE_ACCOUNT_LABEL:-}" ]]; then
        return 0
    fi

    if is_ascii_mode; then
        colorize "$STATUSLINE_CYAN" "[${CLAUDE_STATUSLINE_ACCOUNT_LABEL}]"
        return 0
    fi

    local prefix
    prefix=$(get_prefix "👤" "acct:")
    colorize "$STATUSLINE_CYAN" "${prefix}${CLAUDE_STATUSLINE_ACCOUNT_LABEL}"
}

# =============================================================================
# Usage Line Component (Second Line)
# =============================================================================

# Build the second line with detailed usage info
# Format (emoji): 🔄 5h: 16% → 23:00 │ 📅 7d: 39% → Dec 15
# Format (text):  5h: 16% → 23:00 │ 7d: 39% → Dec 15
# Usage: get_usage_line "5h_percent" "5h_resets" "7d_percent" "7d_resets"
get_usage_line() {
    local native_5h_percent="${1:-}" native_5h_resets="${2:-}"
    local native_7d_percent="${3:-}" native_7d_resets="${4:-}"

    # No rate_limits data available
    if [[ -z "$native_5h_percent" || "$native_5h_percent" == "null" ]]; then
        return 0
    fi

    # Determine display mode
    local display_mode
    display_mode=$(get_display_mode)
    local use_emoji=true
    [[ "$display_mode" == "text" || "$display_mode" == "ascii" ]] && use_emoji=false

    # Round percentage to integer
    local five_hour_pct
    five_hour_pct=$(printf '%.0f' "$native_5h_percent" 2>/dev/null || echo "$native_5h_percent")

    # Format 5-hour reset time (use exact epoch; Claude may reset off the hour)
    local five_hour_display=""
    if [[ -n "$native_5h_resets" && "$native_5h_resets" != "null" && "$native_5h_resets" != "0" ]]; then
        five_hour_display=$(epoch_to_time_display "$native_5h_resets" "+%H:%M")
    fi

    # Build usage line - color the percentage by usage threshold (green/bright-green/yellow/red)
    local five_hour_token
    five_hour_token=$(colorize "$(get_usage_color "$five_hour_pct")" "${five_hour_pct}%")

    local usage_line
    if $use_emoji; then
        usage_line="🔄 5h: ${five_hour_token}"
    else
        usage_line="5h: ${five_hour_token}"
    fi
    [[ -n "$five_hour_display" ]] && usage_line="${usage_line} → ${five_hour_display}"

    # Add 7-day data if available
    if [[ -n "$native_7d_percent" && "$native_7d_percent" != "null" ]]; then
        local seven_day_pct
        seven_day_pct=$(printf '%.0f' "$native_7d_percent" 2>/dev/null || echo "$native_7d_percent")

        local seven_day_display=""
        if [[ -n "$native_7d_resets" && "$native_7d_resets" != "null" && "$native_7d_resets" != "0" ]]; then
            seven_day_display=$(epoch_to_time_display "$native_7d_resets" "+%b %d %H:%M")
        fi

        local seven_day_token
        seven_day_token=$(colorize "$(get_usage_color "$seven_day_pct")" "${seven_day_pct}%")

        if $use_emoji; then
            usage_line="${usage_line} │ 📅 7d: ${seven_day_token}"
        else
            usage_line="${usage_line} │ 7d: ${seven_day_token}"
        fi
        [[ -n "$seven_day_display" ]] && usage_line="${usage_line} → ${seven_day_display}"
    fi

    echo "$usage_line"
}
