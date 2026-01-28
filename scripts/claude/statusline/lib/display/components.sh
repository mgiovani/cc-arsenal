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
# Usage: get_model_component "opus" or "claude-opus-4-5-20251101"
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
# Usage Line Component (Second Line)
# =============================================================================

# Build the second line with detailed usage info
# Format (emoji): 🔄 5h: 16% → 23:00 │ 📅 7d: 39% → Dec 15
# Format (text):  5h: 16% → 23:00 │ 7d: 39% → Dec 15
# Usage: get_usage_line "$input_tokens" "$output_tokens"
get_usage_line() {
    local input_tokens="${1:-0}" output_tokens="${2:-0}"
    local current_time
    current_time=$(get_current_epoch)

    # Determine display mode
    local display_mode
    display_mode=$(get_display_mode)
    local use_emoji=true
    [[ "$display_mode" == "text" || "$display_mode" == "ascii" ]] && use_emoji=false

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

            # Build the usage line based on display mode
            local usage_line
            if $use_emoji; then
                usage_line="🔄 5h: ${five_hour_util}% → ${five_hour_display}"
            else
                usage_line="5h: ${five_hour_util}% → ${five_hour_display}"
            fi

            if [[ -n "$seven_day_util" && -n "$seven_day_display" ]]; then
                if $use_emoji; then
                    usage_line="${usage_line} │ 📅 7d: ${seven_day_util}% → ${seven_day_display}"
                else
                    usage_line="${usage_line} │ 7d: ${seven_day_util}% → ${seven_day_display}"
                fi
            fi

            # Add extra model-specific limits (Sonnet, Opus, etc.)
            local extra_limits
            extra_limits=$(get_oauth_extra_limits 2>/dev/null)

            if [[ -n "$extra_limits" ]]; then
                while IFS='|' read -r limit_name limit_util limit_reset; do
                    [[ -z "$limit_name" ]] && continue

                    # Parse reset time if available
                    local limit_display=""
                    if [[ -n "$limit_reset" && "$limit_reset" != "null" ]]; then
                        local limit_clean_ts limit_epoch
                        limit_clean_ts="${limit_reset%.*}"
                        limit_clean_ts="${limit_clean_ts%+*}"
                        limit_epoch=$(parse_iso_timestamp "$limit_clean_ts")

                        if [[ "$limit_epoch" -gt 0 ]]; then
                            # Round up to next full hour
                            local limit_rounded
                            limit_rounded=$(( (limit_epoch + 3599) / 3600 * 3600 ))
                            limit_display=$(epoch_to_time_display "$limit_rounded" "+%b %d")
                        fi
                    fi

                    # Append to usage line based on display mode
                    if [[ -n "$limit_display" ]]; then
                        if $use_emoji; then
                            usage_line="${usage_line} │ 🎯 ${limit_name}: ${limit_util}% → ${limit_display}"
                        else
                            usage_line="${usage_line} │ ${limit_name}: ${limit_util}% → ${limit_display}"
                        fi
                    else
                        if $use_emoji; then
                            usage_line="${usage_line} │ 🎯 ${limit_name}: ${limit_util}%"
                        else
                            usage_line="${usage_line} │ ${limit_name}: ${limit_util}%"
                        fi
                    fi
                done <<< "$extra_limits"
            fi

            echo "$usage_line"
            return 0
        fi
    fi

    # Fallback: Use heuristic calculation from JSONL timestamps
    local window_start
    window_start=$(get_window_start "$input_tokens" "$output_tokens")

    if [[ "$window_start" == "0" ]]; then
        if $use_emoji; then
            echo "🔄 5h: N/A"
        else
            echo "5h: N/A"
        fi
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
        if $use_emoji; then
            echo "🔄 5h: Reset"
        else
            echo "5h: Reset"
        fi
        return 0
    fi

    # Format reset time as HH:MM
    local reset_time_display
    reset_time_display=$(epoch_to_time_display "$reset_timestamp" "+%H:%M")

    if $use_emoji; then
        echo "🔄 5h: ??% → ${reset_time_display} (estimated)"
    else
        echo "5h: ??% → ${reset_time_display} (estimated)"
    fi
}
