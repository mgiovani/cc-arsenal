#!/bin/bash
# =============================================================================
# Session Tracking - Claude Code session and window management
# =============================================================================
# Tracks session duration, Claude's 5-hour usage windows, and session state.
# Uses file-based persistence per directory.

# Guard clause - prevent multiple sourcing
if [[ -n "${STATUSLINE_SESSION_LOADED:-}" ]]; then
    return 0
fi
readonly STATUSLINE_SESSION_LOADED=1

# Source dependencies
STATUSLINE_TRACKING_DIR="$(dirname "${BASH_SOURCE[0]}")"
source "$STATUSLINE_TRACKING_DIR/../core/platform.sh"
source "$STATUSLINE_TRACKING_DIR/../core/json.sh"

# =============================================================================
# Configuration
# =============================================================================

# Session start cache for expensive calculations
SESSION_CACHE_FILE="${SESSION_CACHE_FILE:-/tmp/claude_session_start_cache}"
SESSION_CACHE_TTL="${SESSION_CACHE_TTL:-60}"  # 60 seconds

# Session duration (5 hours in seconds)
SESSION_DURATION_SECONDS=18000

# =============================================================================
# Session File Management
# =============================================================================

# Get session file path for current directory
# Returns: path to session file (per-directory)
get_session_file() {
    local dir_hash
    dir_hash=$(hash_string "$PWD")
    echo "/tmp/claude_session_${dir_hash}"
}

# Get session ID file path for current directory
# Returns: path to session ID file
get_session_id_file() {
    local dir_hash
    dir_hash=$(hash_string "$PWD")
    echo "/tmp/claude_session_id_${dir_hash}"
}

# Get window start file path for current directory
# Returns: path to window start file
get_window_start_file() {
    local dir_hash
    dir_hash=$(hash_string "$PWD")
    echo "/tmp/claude_window_start_${dir_hash}"
}

# =============================================================================
# Session ID Tracking
# =============================================================================

# Extract session ID from JSON data
# Usage: get_current_session_id "$json"
get_current_session_id() {
    local json="$1"

    # Try multiple possible session ID fields
    local session_id
    session_id=$(extract_json "$json" "conversation_uuid" 2>/dev/null || \
                  extract_json "$json" "session_id" 2>/dev/null || \
                  extract_json "$json" "conversation_id" 2>/dev/null || \
                  extract_json "$json" "workspace.conversation_uuid" 2>/dev/null || \
                  echo "")

    echo "$session_id"
}

# =============================================================================
# Session Start Tracking
# =============================================================================

# Initialize or get session start time
# Usage: get_session_start "$input_tokens" "$output_tokens" "$json"
get_session_start() {
    local input_tokens="${1:-0}" output_tokens="${2:-0}" json="${3:-}"
    local session_file session_id_file
    session_file=$(get_session_file)
    session_id_file=$(get_session_id_file)

    # Check if we have a session ID and if it's changed
    if [[ -n "$json" ]]; then
        local current_session_id
        current_session_id=$(get_current_session_id "$json")

        if [[ -n "$current_session_id" && "$current_session_id" != "null" ]]; then
            local stored_session_id=""

            if [[ -f "$session_id_file" ]]; then
                stored_session_id=$(cat "$session_id_file" 2>/dev/null || echo "")
            fi

            # If session ID changed, start new session
            if [[ "$current_session_id" != "$stored_session_id" ]]; then
                if [[ "$input_tokens" -gt 0 ]] || [[ "$output_tokens" -gt 0 ]] 2>/dev/null; then
                    date +%s > "$session_file" 2>/dev/null || echo "$(date +%s)" > "$session_file"
                    echo "$current_session_id" > "$session_id_file" 2>/dev/null
                fi
            fi
        fi
    fi

    if [[ ! -f "$session_file" ]]; then
        # For new sessions, only start tracking if we have actual usage
        if [[ "$input_tokens" -gt 0 ]] || [[ "$output_tokens" -gt 0 ]] 2>/dev/null; then
            date +%s > "$session_file" 2>/dev/null || echo "$(date +%s)" > "$session_file"
        fi
    fi

    if [[ -f "$session_file" ]]; then
        cat "$session_file" 2>/dev/null || echo "0"
    else
        echo "0"
    fi
}

# =============================================================================
# Session Duration
# =============================================================================

# Get session duration formatted
# Usage: get_session_duration "$input_tokens" "$output_tokens" "$json"
# Returns: formatted duration (e.g., "0m", "15m", "2h30m")
get_session_duration() {
    local input_tokens="${1:-0}" output_tokens="${2:-0}" json="${3:-}"
    local session_start
    session_start=$(get_session_start "$input_tokens" "$output_tokens" "$json")

    if [[ "$session_start" == "0" ]]; then
        echo "0"
        return
    fi

    local current_time duration_seconds
    current_time=$(get_current_epoch)
    duration_seconds=$((current_time - session_start))

    # Format duration
    if [[ $duration_seconds -lt 60 ]]; then
        echo "0m"
    elif [[ $duration_seconds -lt 3600 ]]; then
        echo "$((duration_seconds / 60))m"
    else
        local hours minutes
        hours=$((duration_seconds / 3600))
        minutes=$(((duration_seconds % 3600) / 60))
        if [[ $minutes -eq 0 ]]; then
            echo "${hours}h"
        else
            echo "${hours}h${minutes}m"
        fi
    fi
}

# =============================================================================
# Claude Window Tracking (5-hour blocks)
# =============================================================================

# Get Claude session start from JSONL transcripts
# OPTIMIZED: Uses find -mmin (fast) with caching
get_claude_session_start() {
    local current_time
    current_time=$(get_current_epoch)

    # Check cache first (60 second TTL)
    if [[ -f "$SESSION_CACHE_FILE" ]]; then
        local cache_mtime cache_age cached_value
        cache_mtime=$(get_file_mtime "$SESSION_CACHE_FILE")
        cache_age=$((current_time - cache_mtime))
        if [[ "$cache_age" -lt "$SESSION_CACHE_TTL" ]]; then
            cached_value=$(cat "$SESSION_CACHE_FILE" 2>/dev/null)
            if [[ -n "$cached_value" && "$cached_value" != "0" ]]; then
                echo "$cached_value"
                return
            fi
        fi
    fi

    # Cache miss - do the expensive calculation
    local all_timestamps=()
    local cutoff_time=$((current_time - 21600))  # 6 hours ago

    # Use find -mmin for FAST file filtering
    # -mmin -360 = modified within last 360 minutes (6 hours)
    for claude_dir in "$HOME/.config/claude/projects" "$HOME/.claude/projects"; do
        if [[ -d "$claude_dir" ]]; then
            while IFS= read -r jsonl_file; do
                [[ -z "$jsonl_file" ]] && continue
                # Extract timestamps and convert to epoch
                while IFS= read -r timestamp_line; do
                    if [[ -n "$timestamp_line" ]]; then
                        local timestamp_epoch
                        timestamp_epoch=$(parse_iso_timestamp "$timestamp_line")
                        if [[ "$timestamp_epoch" -gt "$cutoff_time" ]]; then
                            all_timestamps+=("$timestamp_epoch")
                        fi
                    fi
                done < <(grep -o '"timestamp":"[^"]*"' "$jsonl_file" 2>/dev/null | cut -d'"' -f4)
            done < <(find "$claude_dir" -name "*.jsonl" -type f -mmin -360 2>/dev/null)
        fi
    done

    # If no timestamps found, return current hour floored
    if [[ ${#all_timestamps[@]} -eq 0 ]]; then
        local result
        result=$(floor_epoch_to_hour "$current_time")
        echo "$result" > "$SESSION_CACHE_FILE" 2>/dev/null
        echo "$result"
        return
    fi

    # Sort timestamps chronologically
    IFS=$'\n' all_timestamps=($(sort -n <<< "${all_timestamps[*]}")); unset IFS

    # Apply session block detection algorithm
    local current_block_start=0
    local last_entry_time=0

    for timestamp in "${all_timestamps[@]}"; do
        if [[ "$current_block_start" -eq 0 ]]; then
            # First timestamp - start new block (floored to hour)
            current_block_start=$(floor_epoch_to_hour "$timestamp")
            last_entry_time="$timestamp"
        else
            # Check if this timestamp should start a new block
            local time_since_block_start=$((timestamp - current_block_start))
            local time_since_last_entry=$((timestamp - last_entry_time))

            # If time since block start > 5h OR time since last entry > 5h, start new block
            if [[ "$time_since_block_start" -gt "$SESSION_DURATION_SECONDS" ]] || \
                [[ "$time_since_last_entry" -gt "$SESSION_DURATION_SECONDS" ]]; then
                current_block_start=$(floor_epoch_to_hour "$timestamp")
            fi
            last_entry_time="$timestamp"
        fi
    done

    # Check if current block is still active
    local result="$current_time"
    if [[ "$current_block_start" -gt 0 ]] && [[ "$last_entry_time" -gt 0 ]]; then
        local time_since_last_activity=$((current_time - last_entry_time))
        local block_end_time=$((current_block_start + SESSION_DURATION_SECONDS))

        # Block is active if: time since last activity < 5h AND current time < block end
        if [[ "$time_since_last_activity" -lt "$SESSION_DURATION_SECONDS" ]] && \
            [[ "$current_time" -lt "$block_end_time" ]]; then
            result="$current_block_start"
        else
            result=$(floor_epoch_to_hour "$current_time")
        fi
    else
        result=$(floor_epoch_to_hour "$current_time")
    fi

    # Save to cache and return
    echo "$result" > "$SESSION_CACHE_FILE" 2>/dev/null
    echo "$result"
}

# Get window start (tracks when 5-hour Claude window started)
# Usage: get_window_start "$input_tokens" "$output_tokens"
get_window_start() {
    local input_tokens="${1:-0}" output_tokens="${2:-0}"

    # First try to get the actual start time from Claude Code session data
    local claude_start
    claude_start=$(get_claude_session_start)

    if [[ "$claude_start" -gt 0 ]]; then
        echo "$claude_start"
        return 0
    fi

    # Fallback to our own tracking if Claude data not available
    local window_file
    window_file=$(get_window_start_file)

    if [[ ! -f "$window_file" ]]; then
        # Check if we have actual usage
        if [[ "$input_tokens" -gt 0 ]] || [[ "$output_tokens" -gt 0 ]] 2>/dev/null; then
            date +%s > "$window_file" 2>/dev/null || echo "$(date +%s)" > "$window_file"
        fi
    fi

    if [[ -f "$window_file" ]]; then
        local window_start current_time
        window_start=$(cat "$window_file" 2>/dev/null || echo "0")
        current_time=$(get_current_epoch)

        # Check if window has expired (more than 5 hours)
        if [[ "$window_start" -gt 0 ]] && [[ $((current_time - window_start)) -gt $SESSION_DURATION_SECONDS ]]; then
            # Window expired, start new one if we have usage
            if [[ "$input_tokens" -gt 0 ]] || [[ "$output_tokens" -gt 0 ]] 2>/dev/null; then
                date +%s > "$window_file" 2>/dev/null || echo "$(date +%s)" > "$window_file"
                cat "$window_file" 2>/dev/null || echo "$current_time"
            else
                echo "0"
            fi
        else
            echo "$window_start"
        fi
    else
        echo "0"  # No window started yet
    fi
}

# =============================================================================
# Utility Functions
# =============================================================================

# Clear session tracking files for current directory
clear_session_tracking() {
    rm -f "$(get_session_file)" 2>/dev/null
    rm -f "$(get_session_id_file)" 2>/dev/null
    rm -f "$(get_window_start_file)" 2>/dev/null
}

# Clear session cache
clear_session_cache() {
    rm -f "$SESSION_CACHE_FILE" 2>/dev/null
}
