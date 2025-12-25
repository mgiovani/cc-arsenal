#!/bin/bash
# =============================================================================
# Usage Tracking - Token and cost tracking for Claude Code sessions
# =============================================================================
# Tracks daily API costs, token usage, and provides transcript parsing.

# Guard clause - prevent multiple sourcing
if [[ -n "${STATUSLINE_USAGE_LOADED:-}" ]]; then
    return 0
fi
readonly STATUSLINE_USAGE_LOADED=1

# Source dependencies
STATUSLINE_TRACKING_DIR="$(dirname "${BASH_SOURCE[0]}")"
source "$STATUSLINE_TRACKING_DIR/../core/platform.sh"
source "$STATUSLINE_TRACKING_DIR/../core/json.sh"

# =============================================================================
# Configuration
# =============================================================================

# Usage tracking directory and database
USAGE_DIR="${TEST_USAGE_DIR:-$HOME/.claude/cc-arsenal}"
USAGE_DB="${TEST_USAGE_DB:-$USAGE_DIR/usage_tracking.json}"

# =============================================================================
# Setup
# =============================================================================

# Initialize usage tracking database
setup_usage_tracking() {
    mkdir -p "$USAGE_DIR" 2>/dev/null || true

    if [[ ! -f "$USAGE_DB" ]]; then
        echo '{"daily_usage":{},"window_start":""}' > "$USAGE_DB" 2>/dev/null || true
    fi
}

# =============================================================================
# Daily Usage Tracking
# =============================================================================

# Update daily usage with new cost
# Usage: update_daily_usage 0.15
update_daily_usage() {
    local cost="${1:-0}"
    local current_date
    current_date=$(get_current_date)

    setup_usage_tracking

    if ! check_jq; then
        return 1
    fi

    local temp_file
    temp_file=$(mktemp)

    jq --arg date "$current_date" --arg cost "$cost" '
        .daily_usage[$date] = ((((.daily_usage[$date] // 0) + ($cost | tonumber)) * 10000) | round) / 10000
    ' "$USAGE_DB" > "$temp_file" 2>/dev/null && mv "$temp_file" "$USAGE_DB"
}

# Get daily usage total
# Returns: cost in USD (e.g., "1.25")
get_daily_usage() {
    local current_date
    current_date=$(get_current_date)

    setup_usage_tracking

    if ! check_jq; then
        echo "0"
        return
    fi

    jq -r --arg date "$current_date" '.daily_usage[$date] // 0' "$USAGE_DB" 2>/dev/null || echo "0"
}

# =============================================================================
# Token Extraction
# =============================================================================

# Get token usage from transcript file
# Usage: get_transcript_tokens "/path/to/transcript.jsonl"
# Returns: "input_tokens|output_tokens"
get_transcript_tokens() {
    local transcript_path="$1"

    if [[ ! -f "$transcript_path" ]]; then
        echo "0|0"
        return 0
    fi

    # Extract tokens from JSONL transcript file using jq if available
    if check_jq; then
        # Get the latest message's context tokens
        local latest_context_tokens latest_output_tokens
        latest_context_tokens=$(tail -1 "$transcript_path" | jq -r 'select(.message.usage) | .message.usage | ((.input_tokens // 0) + (.cache_read_input_tokens // 0))' 2>/dev/null || echo "0")
        latest_output_tokens=$(tail -1 "$transcript_path" | jq -r 'select(.message.usage) | .message.usage.output_tokens // 0' 2>/dev/null || echo "0")
        echo "${latest_context_tokens}|${latest_output_tokens}"
        return 0
    fi

    # Fallback: get latest message context tokens using grep
    local latest_input=0 latest_cache=0 latest_output=0
    local last_line
    last_line=$(tail -1 "$transcript_path" 2>/dev/null || echo "")

    if [[ "$last_line" =~ \"input_tokens\":([0-9]+) ]]; then
        latest_input=${BASH_REMATCH[1]}
    fi
    if [[ "$last_line" =~ \"cache_read_input_tokens\":([0-9]+) ]]; then
        latest_cache=${BASH_REMATCH[1]}
    fi
    if [[ "$last_line" =~ \"output_tokens\":([0-9]+) ]]; then
        latest_output=${BASH_REMATCH[1]}
    fi

    local total_context=$((latest_input + latest_cache))
    echo "${total_context}|${latest_output}"
}

# =============================================================================
# Window Tracking (integrated with usage)
# =============================================================================

# Update window tracking timestamp
update_window_tracking() {
    setup_usage_tracking

    if ! check_jq; then
        return 1
    fi

    local current_time
    current_time=$(get_current_epoch)

    local temp_file
    temp_file=$(mktemp)

    jq --arg time "$current_time" '.window_start = $time' "$USAGE_DB" > "$temp_file" 2>/dev/null && \
        mv "$temp_file" "$USAGE_DB"
}

# Get window start from usage tracking
get_tracked_window_start() {
    setup_usage_tracking

    if ! check_jq; then
        echo "0"
        return
    fi

    jq -r '.window_start // "0"' "$USAGE_DB" 2>/dev/null || echo "0"
}

# =============================================================================
# Data Cleanup
# =============================================================================

# Clean up old usage data (older than 30 days)
cleanup_old_data() {
    setup_usage_tracking

    if ! check_jq; then
        return 1
    fi

    local cutoff_date
    # Calculate date 30 days ago
    if is_macos; then
        cutoff_date=$(date -v-30d +%Y-%m-%d 2>/dev/null)
    else
        cutoff_date=$(date -d "30 days ago" +%Y-%m-%d 2>/dev/null)
    fi

    if [[ -z "$cutoff_date" ]]; then
        return 1
    fi

    local temp_file
    temp_file=$(mktemp)

    jq --arg cutoff "$cutoff_date" '
        .daily_usage = (.daily_usage | to_entries | map(select(.key >= $cutoff)) | from_entries)
    ' "$USAGE_DB" > "$temp_file" 2>/dev/null && mv "$temp_file" "$USAGE_DB"
}

# =============================================================================
# Utility Functions
# =============================================================================

# Get usage summary for a date range
# Usage: get_usage_summary [days_back]
get_usage_summary() {
    local days_back="${1:-7}"

    setup_usage_tracking

    if ! check_jq; then
        echo "{}"
        return
    fi

    local start_date
    if is_macos; then
        start_date=$(date -v-${days_back}d +%Y-%m-%d 2>/dev/null)
    else
        start_date=$(date -d "${days_back} days ago" +%Y-%m-%d 2>/dev/null)
    fi

    if [[ -z "$start_date" ]]; then
        jq '.daily_usage' "$USAGE_DB" 2>/dev/null
        return
    fi

    jq --arg start "$start_date" '
        .daily_usage | to_entries | map(select(.key >= $start)) | from_entries
    ' "$USAGE_DB" 2>/dev/null
}

# Get total usage for current week
get_weekly_usage() {
    setup_usage_tracking

    if ! check_jq; then
        echo "0"
        return
    fi

    local start_date
    if is_macos; then
        start_date=$(date -v-7d +%Y-%m-%d 2>/dev/null)
    else
        start_date=$(date -d "7 days ago" +%Y-%m-%d 2>/dev/null)
    fi

    if [[ -z "$start_date" ]]; then
        echo "0"
        return
    fi

    jq -r --arg start "$start_date" '
        [.daily_usage | to_entries | map(select(.key >= $start)) | .[].value] | add // 0
    ' "$USAGE_DB" 2>/dev/null || echo "0"
}

# Reset usage tracking (for testing)
reset_usage_tracking() {
    rm -f "$USAGE_DB" 2>/dev/null
    setup_usage_tracking
}
