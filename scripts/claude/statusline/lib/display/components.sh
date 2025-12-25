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
source "$STATUSLINE_DISPLAY_DIR/../api/oauth.sh"
source "$STATUSLINE_DISPLAY_DIR/../tracking/session.sh"
source "$STATUSLINE_DISPLAY_DIR/../core/platform.sh"

# =============================================================================
# Model Component
# =============================================================================

# Display model name with icon
# Usage: get_model_component "opus" or "claude-opus-4-5-20251101"
get_model_component() {
    local model="${1:-}"

    if [[ -z "$model" || "$model" == "null" ]]; then
        echo "🤖 Unavailable"
        return 0
    fi

    # If model looks like a display name (e.g., "Opus", "Sonnet"), use it directly
    if [[ "$model" =~ ^[A-Z][a-z]+$ ]]; then
        echo "🤖 $model"
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

    echo "🤖 $display"
}

# =============================================================================
# Directory Component
# =============================================================================

# Display current directory with icon
# Usage: get_directory_component "/path/to/dir"
get_directory_component() {
    local dir="${1:-$(pwd)}"
    local short_dir="$dir"

    # Replace home with ~
    if [[ "$dir" == "$HOME"* ]]; then
        short_dir="~${dir#$HOME}"
    fi

    # Truncate if too long
    if [[ ${#short_dir} -gt 30 ]]; then
        local base="${dir##*/}"
        short_dir=".../$base"
    fi

    echo "📁 $short_dir"
}

# =============================================================================
# Git Component
# =============================================================================

# Display git branch with status indicator
# Usage: get_git_component
get_git_component() {
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

    local status_symbol=""
    if [[ "$changes" -gt 0 ]] 2>/dev/null; then
        status_symbol=" ●"
    fi

    echo "🌿 $branch$status_symbol"
}

# =============================================================================
# Worktree Component
# =============================================================================

# Display git worktree name if in a worktree
# Usage: get_worktree_component
get_worktree_component() {
    local git_info
    git_info=$(get_git_info 2>/dev/null || echo "0|not_a_repo|")

    # Parse the pipe-separated values: changes|branch|worktree
    local rest="${git_info#*|}"
    rest="${rest#*|}"
    local worktree="$rest"

    # Only show if we're in a worktree
    if [[ -n "$worktree" ]]; then
        echo "🌳 $worktree"
    fi
}

# =============================================================================
# Context Component
# =============================================================================

# Display context window usage percentage
# Usage: get_context_component "$input_tokens" "$output_tokens" "$context_window_size"
get_context_component() {
    local input_tokens="${1:-0}" output_tokens="${2:-0}" context_window_size="${3:-200000}"

    # For new sessions with no usage, show 0%
    if [[ "$input_tokens" == "0" && "$output_tokens" == "0" ]] || \
        [[ -z "$input_tokens" || -z "$output_tokens" ]]; then
        echo "📊 0%"
        return 0
    fi

    # Ensure context_window_size is valid
    if [[ -z "$context_window_size" || "$context_window_size" == "0" || "$context_window_size" == "null" ]]; then
        context_window_size=200000
    fi

    local total=$((input_tokens + output_tokens))
    local percent=$((total * 100 / context_window_size))
    [[ $percent -gt 100 ]] && percent=100

    echo "📊 ${percent}%"
}

# =============================================================================
# Cost Component
# =============================================================================

# Display session cost
# Usage: get_cost_component "1.25"
get_cost_component() {
    local cost="${1:-}"

    # For new sessions with no cost, show $0.00
    if [[ -z "$cost" || "$cost" == "0" || "$cost" == "null" ]]; then
        echo "💰 \$0.00"
        return 0
    fi

    local formatted
    formatted=$(printf "%.3f" "$cost" 2>/dev/null || echo "$cost")
    echo "💰 \$${formatted}"
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
        echo "📝 $display"
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

    echo "⏱️ $duration_display"
}

# =============================================================================
# Usage Line Component (Second Line)
# =============================================================================

# Build the second line with detailed usage info
# Format: 🔄 5h: 16% → 23:00 │ 📅 7d: 39% → Dec 15
# Usage: get_usage_line "$input_tokens" "$output_tokens"
get_usage_line() {
    local input_tokens="${1:-0}" output_tokens="${2:-0}"
    local current_time
    current_time=$(get_current_epoch)

    # Try OAuth API first (most accurate)
    local usage_json
    usage_json=$(fetch_oauth_usage 2>/dev/null)

    if [[ -n "$usage_json" ]] && check_jq; then
        local five_hour_util five_hour_reset seven_day_util seven_day_reset

        # Extract 5-hour data
        five_hour_util=$(echo "$usage_json" | jq -r '.five_hour.utilization // empty' 2>/dev/null)
        five_hour_reset=$(echo "$usage_json" | jq -r '.five_hour.resets_at // empty' 2>/dev/null)

        # Extract 7-day data
        seven_day_util=$(echo "$usage_json" | jq -r '.seven_day.utilization // empty' 2>/dev/null)
        seven_day_reset=$(echo "$usage_json" | jq -r '.seven_day.resets_at // empty' 2>/dev/null)

        if [[ -n "$five_hour_util" && -n "$five_hour_reset" && "$five_hour_reset" != "null" ]]; then
            # Parse 5-hour reset time
            local clean_ts five_hour_epoch five_hour_display
            clean_ts="${five_hour_reset%.*}"
            clean_ts="${clean_ts%+*}"
            five_hour_epoch=$(parse_iso_timestamp "$clean_ts")

            # Round up to next full hour
            local rounded_epoch
            rounded_epoch=$(( (five_hour_epoch + 3599) / 3600 * 3600 ))
            five_hour_display=$(epoch_to_time_display "$rounded_epoch" "+%H:%M")

            # Parse 7-day reset time (show as date and time)
            local seven_day_display=""
            if [[ -n "$seven_day_reset" && "$seven_day_reset" != "null" ]]; then
                clean_ts="${seven_day_reset%.*}"
                clean_ts="${clean_ts%+*}"
                local seven_day_epoch
                seven_day_epoch=$(parse_iso_timestamp "$clean_ts")

                # Round up to next full hour
                local seven_day_rounded
                seven_day_rounded=$(( (seven_day_epoch + 3599) / 3600 * 3600 ))
                seven_day_display=$(epoch_to_time_display "$seven_day_rounded" "+%b %d %H:%M")
            fi

            # Build the usage line
            local usage_line="🔄 5h: ${five_hour_util}% → ${five_hour_display}"

            if [[ -n "$seven_day_util" && -n "$seven_day_display" ]]; then
                usage_line="${usage_line} │ 📅 7d: ${seven_day_util}% → ${seven_day_display}"
            fi

            echo "$usage_line"
            return 0
        fi
    fi

    # Fallback: Use heuristic calculation from JSONL timestamps
    local window_start
    window_start=$(get_window_start "$input_tokens" "$output_tokens")

    if [[ "$window_start" == "0" ]]; then
        echo "🔄 5h: N/A"
        return 0
    fi

    # Calculate when the window should reset
    local exact_reset_time prev_full_hour reset_timestamp
    exact_reset_time=$((window_start + 18000))
    prev_full_hour=$(( exact_reset_time / 3600 * 3600 ))
    reset_timestamp=$prev_full_hour

    local seconds_until_reset
    seconds_until_reset=$((reset_timestamp - current_time))

    if [[ $seconds_until_reset -le 0 ]]; then
        echo "🔄 5h: Reset"
        return 0
    fi

    # Format reset time as HH:MM
    local reset_time_display
    reset_time_display=$(epoch_to_time_display "$reset_timestamp" "+%H:%M")

    echo "🔄 5h: ??% → ${reset_time_display} (estimated)"
}
