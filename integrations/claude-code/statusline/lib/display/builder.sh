#!/bin/bash
# =============================================================================
# Statusline Builder - Assembles components into final output
# =============================================================================
# Orchestrates component building and formats the final statusline output.

# Guard clause - prevent multiple sourcing
if [[ -n "${STATUSLINE_BUILDER_LOADED:-}" ]]; then
    return 0
fi
readonly STATUSLINE_BUILDER_LOADED=1

# Source dependencies
STATUSLINE_DISPLAY_DIR="$(dirname "${BASH_SOURCE[0]}")"
source "$STATUSLINE_DISPLAY_DIR/components.sh"
source "$STATUSLINE_DISPLAY_DIR/../core/json.sh"
source "$STATUSLINE_DISPLAY_DIR/../config.sh"

# =============================================================================
# Configuration
# =============================================================================

# Component separator
STATUSLINE_SEPARATOR="${STATUSLINE_SEPARATOR:-│}"

# =============================================================================
# Debug Logging
# =============================================================================

# Debug logging function
# Usage: debug_log "$json"
debug_log() {
    [[ "${STATUSLINE_DEBUG:-0}" != "1" ]] && return

    local json="$1"
    local log_file="/tmp/claude_statusline_debug.log"

    {
        echo "=== $(date) ==="
        echo "Raw JSON length: ${#json}"
        echo "Raw JSON: $json"
        echo
        echo "Context window extractions:"
        echo "  context_window.used_percentage: '$(extract_json "$json" "context_window.used_percentage" 2>/dev/null || echo "MISSING")'"
        echo "  context_window.remaining_percentage: '$(extract_json "$json" "context_window.remaining_percentage" 2>/dev/null || echo "MISSING")'"
        echo "=================================="
        echo
    } >> "$log_file"
}

# =============================================================================
# Data Extraction
# =============================================================================

# Extract all relevant data from JSON
# Returns values via global variables for efficiency
extract_statusline_data() {
    local json="$1"

    # Model
    MODEL_ID=$(extract_json "$json" "model.id" 2>/dev/null || echo "")
    MODEL_DISPLAY=$(extract_json "$json" "model.display_name" 2>/dev/null || echo "")

    # Cost and lines
    COST_USD=$(extract_json "$json" "cost.total_cost_usd" 2>/dev/null || echo "")
    LINES_ADDED=$(extract_json "$json" "cost.total_lines_added" 2>/dev/null || echo "0")
    LINES_REMOVED=$(extract_json "$json" "cost.total_lines_removed" 2>/dev/null || echo "0")

    # Context window - use percentage from Claude Code
    USED_PERCENTAGE=$(extract_json "$json" "context_window.used_percentage" 2>/dev/null || echo "")

    # Rate limits (native from Claude Code JSON)
    RATE_LIMIT_5H_PERCENT=$(extract_json "$json" "rate_limits.five_hour.used_percentage" 2>/dev/null || echo "")
    RATE_LIMIT_5H_RESETS=$(extract_json "$json" "rate_limits.five_hour.resets_at" 2>/dev/null || echo "")
    RATE_LIMIT_7D_PERCENT=$(extract_json "$json" "rate_limits.seven_day.used_percentage" 2>/dev/null || echo "")
    RATE_LIMIT_7D_RESETS=$(extract_json "$json" "rate_limits.seven_day.resets_at" 2>/dev/null || echo "")

    # Fetched OAuth usage overrides stdin rate limits when a per-account fetch is available
    if [[ -n "${CLAUDE_CODE_OAUTH_TOKEN:-}" ]] && declare -f get_oauth_five_hour_usage >/dev/null 2>&1; then
        local fetched_5h fetched_7d
        fetched_5h=$(get_oauth_five_hour_usage 2>/dev/null)
        if [[ -n "$fetched_5h" && "$fetched_5h" == *"|"* ]]; then
            RATE_LIMIT_5H_PERCENT="${fetched_5h%%|*}"
            RATE_LIMIT_5H_RESETS="${fetched_5h#*|}"
        fi

        fetched_7d=$(get_oauth_seven_day_usage 2>/dev/null)
        if [[ -n "$fetched_7d" && "$fetched_7d" == *"|"* ]]; then
            RATE_LIMIT_7D_PERCENT="${fetched_7d%%|*}"
            RATE_LIMIT_7D_RESETS="${fetched_7d#*|}"
        fi
    fi

    # Worktree (native from Claude Code JSON)
    NATIVE_WORKTREE_NAME=$(extract_json "$json" "worktree.name" 2>/dev/null || echo "")
    NATIVE_WORKTREE_BRANCH=$(extract_json "$json" "worktree.branch" 2>/dev/null || echo "")

    # Use display name directly if available
    MODEL="${MODEL_DISPLAY:-$MODEL_ID}"
}

# =============================================================================
# Line Building
# =============================================================================

# Build the first line (main statusline)
# Returns: formatted statusline string
build_line_one() {
    local json="$1"
    local current_dir="$2"

    local components=()
    local comp

    # Model
    comp=$(get_model_component "$MODEL")
    [[ -n "$comp" ]] && components+=("$comp")

    # Directory
    comp=$(get_directory_component "$current_dir")
    [[ -n "$comp" ]] && components+=("$comp")

    # Git - use native worktree.branch when available to avoid git subprocess
    comp=$(get_git_component "$NATIVE_WORKTREE_BRANCH")
    [[ -n "$comp" ]] && components+=("$comp")

    # Worktree - prefer native JSON, fallback to git detection
    comp=$(get_worktree_component "$NATIVE_WORKTREE_NAME")
    [[ -n "$comp" ]] && components+=("$comp")

    # Context
    comp=$(get_context_component "$USED_PERCENTAGE")
    [[ -n "$comp" ]] && components+=("$comp")

    # Cost
    comp=$(get_cost_component "$COST_USD")
    [[ -n "$comp" ]] && components+=("$comp")

    # Lines changed (disabled by default)
    if [[ "$(get_config_bool '.components.enabled.lines_changed' 'false')" == "true" ]]; then
        comp=$(get_lines_component "$LINES_ADDED" "$LINES_REMOVED")
        [[ -n "$comp" ]] && components+=("$comp")
    fi

    # Session duration
    comp=$(get_session_component "$json")
    [[ -n "$comp" ]] && components+=("$comp")

    # Assemble line
    local statusline=""
    local first=1

    for comp in "${components[@]}"; do
        if (( first )); then
            statusline="$comp"
            first=0
        else
            statusline="$statusline $STATUSLINE_SEPARATOR $comp"
        fi
    done

    echo "$statusline"
}

# Build the second line (usage details)
# Returns: usage line string
build_line_two() {
    local usage_line
    usage_line=$(get_usage_line "$RATE_LIMIT_5H_PERCENT" "$RATE_LIMIT_5H_RESETS" \
        "$RATE_LIMIT_7D_PERCENT" "$RATE_LIMIT_7D_RESETS")

    local account
    account=$(get_account_component)
    if [[ -n "$account" ]]; then
        if [[ -n "$usage_line" ]]; then
            echo "$account $STATUSLINE_SEPARATOR $usage_line"
        else
            echo "$account"
        fi
    else
        echo "$usage_line"
    fi
}

# =============================================================================
# Main Builder
# =============================================================================

# Build complete statusline (both lines)
# Usage: build_statusline "$json" "$current_dir"
build_statusline() {
    local json="$1"
    local current_dir="${2:-$(pwd)}"

    [[ -z "$json" ]] && json='{}'

    # Debug logging
    debug_log "$json"

    # Extract all data from JSON
    extract_statusline_data "$json"

    # Output line 1
    build_line_one "$json" "$current_dir"

    # Output line 2 (usage details)
    local usage_line
    usage_line=$(build_line_two)
    if [[ -n "$usage_line" ]]; then
        echo "$usage_line"
    fi
}

# Build minimal statusline (fallback)
# Usage: build_minimal_statusline
build_minimal_statusline() {
    local branch
    branch=$(git symbolic-ref --short HEAD 2>/dev/null || echo "main")

    if is_text_mode; then
        echo "Mod: Claude $STATUSLINE_SEPARATOR Dir: $(basename "$PWD") $STATUSLINE_SEPARATOR Git: $branch $STATUSLINE_SEPARATOR 5h"
    else
        echo "🤖 Claude $STATUSLINE_SEPARATOR 📁 $(basename "$PWD") $STATUSLINE_SEPARATOR 🌿 $branch $STATUSLINE_SEPARATOR 🔄 5h"
    fi
}
