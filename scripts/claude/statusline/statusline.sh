#!/bin/bash
# Ultra-fast statusline with robust error handling
# Handles all edge cases and fallbacks gracefully

set -e  # Exit on error, but handle unset variables

# Source required libraries
SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"
if [[ -f "$SCRIPT_DIR/lib/usage_tracker.sh" ]]; then
    source "$SCRIPT_DIR/lib/usage_tracker.sh"
fi

# Performance monitoring
START_TIME=$(date +%s%N 2>/dev/null || date +%s000000000)

# Simple cache (fallback to no cache if creation fails)
CACHE_DIR="/tmp/statusline_cache_$$"
mkdir -p "$CACHE_DIR" 2>/dev/null || CACHE_DIR="/tmp"
trap "rm -rf '$CACHE_DIR' 2>/dev/null || true" EXIT 2>/dev/null || true

# Simple cache functions
cache_get() {
    local key="$1"
    local cache_file="$CACHE_DIR/${key//\//_}"

    if [[ -f "$cache_file" ]] 2>/dev/null; then
        local cache_time current_time
        cache_time=$(stat -f %m "$cache_file" 2>/dev/null || stat -c %Y "$cache_file" 2>/dev/null || echo 0)
        current_time=$(date +%s)

        if (( current_time - cache_time < 30 )); then
            cat "$cache_file" 2>/dev/null && return 0
        fi
    fi
    return 1
}

cache_set() {
    local key="$1" value="$2"
    local cache_file="$CACHE_DIR/${key//\//_}"
    echo "$value" > "$cache_file" 2>/dev/null || true
}

# =============================================================================
# Cross-Platform Helpers
# macOS and Linux have different commands for stat and date parsing
# =============================================================================

# Get file modification time (epoch seconds) - cross-platform
# Usage: get_file_mtime "/path/to/file"
get_file_mtime() {
    local file="$1"
    stat -f %m "$file" 2>/dev/null || stat -c %Y "$file" 2>/dev/null || echo "0"
}

# Parse ISO 8601 timestamp to epoch - cross-platform
# Usage: parse_iso_timestamp "2025-01-01T12:00:00.123Z"
parse_iso_timestamp() {
    local ts="$1"
    # Remove milliseconds and Z suffix: "2025-01-01T12:00:00.123Z" -> "2025-01-01T12:00:00"
    local clean_ts="${ts%.*}"
    clean_ts="${clean_ts%Z}"

    # Try macOS format first, then Linux
    TZ=UTC date -j -f "%Y-%m-%dT%H:%M:%S" "$clean_ts" +%s 2>/dev/null || \
    TZ=UTC date -d "$clean_ts" +%s 2>/dev/null || \
    echo "0"
}

# Floor epoch timestamp to hour boundary - cross-platform
# Usage: floor_epoch_to_hour 1704110400
floor_epoch_to_hour() {
    local epoch="$1"
    # Pure arithmetic: floor to hour (3600 seconds)
    echo $(( (epoch / 3600) * 3600 ))
}

# Convert epoch to formatted date string - cross-platform
# Usage: epoch_to_time_display 1704110400 "+%H:%M"
epoch_to_time_display() {
    local epoch="$1"
    local format="${2:-+%H:%M}"
    # Try macOS format first (-r), then Linux (-d @)
    date -r "$epoch" "$format" 2>/dev/null || \
    date -d "@$epoch" "$format" 2>/dev/null || \
    echo "??:??"
}

# =============================================================================
# JSON Extraction Functions
# Primary: jq (reliable, supports nested paths)
# Fallback: grep patterns (for environments without jq)
# =============================================================================

# Check if jq is available (cached for performance)
HAS_JQ=""
check_jq() {
    if [[ -z "$HAS_JQ" ]]; then
        HAS_JQ=$(command -v jq >/dev/null 2>&1 && echo "true" || echo "false")
    fi
    [[ "$HAS_JQ" == "true" ]]
}

# JSON extraction using jq (primary method)
# Supports any nested path like "context_window.total_input_tokens"
extract_json_jq() {
    local json="$1" key="$2"
    local result
    result=$(echo "$json" | jq -r ".${key} // empty" 2>/dev/null) || return 1
    [[ -n "$result" && "$result" != "null" ]] && echo "$result" && return 0
    return 1
}

# DRY helper: extract string value from JSON using grep
# Usage: grep_string "$json" "field_name"
# Handles both compact JSON ("key":"value") and pretty JSON ("key": "value")
grep_string() {
    local json="$1" field="$2"
    echo "$json" | grep -oE "\"${field}\":[[:space:]]*\"[^\"]*\"" 2>/dev/null | sed -E "s/\"${field}\":[[:space:]]*//" | sed 's/^"//' | sed 's/"$//' | head -1
}

# DRY helper: extract numeric value from JSON using grep
# Usage: grep_number "$json" "field_name"
# Handles both compact JSON ("key":123) and pretty JSON ("key": 123)
grep_number() {
    local json="$1" field="$2"
    echo "$json" | grep -oE "\"${field}\":[[:space:]]*[0-9.]+" 2>/dev/null | sed -E "s/\"${field}\":[[:space:]]*//" | head -1
}

# JSON extraction using grep (fallback when jq unavailable)
# Maps JSON paths to their leaf field names for grep extraction
extract_json_grep() {
    local json="$1" key="$2"

    # Map paths to field names and types
    case "$key" in
        # String fields
        "model.id")                     grep_string "$json" "id" ;;
        "model.display_name")           grep_string "$json" "display_name" ;;
        "workspace.current_dir")        grep_string "$json" "current_dir" ;;

        # Numeric fields - cost object
        "cost.total_cost_usd")          grep_number "$json" "total_cost_usd" ;;
        "cost.total_lines_added")       grep_number "$json" "total_lines_added" ;;
        "cost.total_lines_removed")     grep_number "$json" "total_lines_removed" ;;
        "cost.total_duration_ms")       grep_number "$json" "total_duration_ms" ;;

        # Numeric fields - context_window object (primary source for tokens)
        "context_window.total_input_tokens")   grep_number "$json" "total_input_tokens" ;;
        "context_window.total_output_tokens")  grep_number "$json" "total_output_tokens" ;;
        "context_window.context_window_size")  grep_number "$json" "context_window_size" ;;

        # Unknown key - no grep pattern available
        *) return 1 ;;
    esac
}

# Main JSON extraction function
# Uses jq by default, falls back to grep if jq is unavailable
extract_json() {
    local json="$1" key="$2"

    # Primary: use jq for reliable JSON parsing
    if check_jq; then
        local jq_result
        jq_result=$(extract_json_jq "$json" "$key")
        local jq_status=$?
        if [[ $jq_status -eq 0 && -n "$jq_result" ]]; then
            echo "$jq_result"
            return 0
        fi
    fi

    # Fallback: use grep patterns when jq unavailable or fails
    extract_json_grep "$json" "$key"
}

# Live cache from daemon
LIVE_CACHE_FILE="/tmp/statusline_live_cache/live_data.json"
DAEMON_SCRIPT="$SCRIPT_DIR/statusline_daemon.sh"
DAEMON_PID_FILE="/tmp/statusline_live_cache/daemon.pid"

# Auto-start daemon if not running (zero-config, self-healing)
ensure_daemon_running() {
    # Quick check: is daemon already running?
    # Note: kill -0 just checks if process exists, doesn't kill it
    if [[ -f "$DAEMON_PID_FILE" ]]; then
        local pid=$(cat "$DAEMON_PID_FILE" 2>/dev/null || echo "")
        if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
            return 0  # Daemon is running
        fi
    fi

    # Use a lock file to prevent multiple simultaneous starts
    local lock_file="/tmp/statusline_live_cache/start.lock"
    local cache_dir=$(dirname "$lock_file")
    mkdir -p "$cache_dir" 2>/dev/null

    # Try to acquire lock (atomic operation using mkdir)
    if ! mkdir "$lock_file" 2>/dev/null; then
        # Another statusline call is already starting the daemon
        return 0
    fi

    # We have the lock - start daemon using autostart (non-blocking)
    if [[ -x "$DAEMON_SCRIPT" ]]; then
        # Use autostart command which is optimized for non-blocking start
        "$DAEMON_SCRIPT" autostart </dev/null >/dev/null 2>&1 &
        # Don't wait - return immediately
    fi

    # Release lock immediately
    rmdir "$lock_file" 2>/dev/null || true
}

# Read live cached data or fallback to direct calculation
get_live_cache() {
    local key="$1"
    if [[ -f "$LIVE_CACHE_FILE" ]] && command -v jq >/dev/null 2>&1; then
        local value=$(jq -r ".$key // empty" "$LIVE_CACHE_FILE" 2>/dev/null || echo "")
        if [[ -n "$value" && "$value" != "null" ]]; then
            echo "$value"
            return 0
        fi
    fi
    return 1
}

# Robust git operations - reads from live cache or calculates directly
get_git_info() {
    # Try live cache first (instant)
    if [[ -f "$LIVE_CACHE_FILE" ]] && command -v jq >/dev/null 2>&1; then
        local in_repo=$(jq -r '.git.in_repo // false' "$LIVE_CACHE_FILE" 2>/dev/null || echo "false")
        if [[ "$in_repo" == "true" ]]; then
            local branch=$(jq -r '.git.branch // "main"' "$LIVE_CACHE_FILE" 2>/dev/null || echo "main")
            local changes=$(jq -r '.git.changes // 0' "$LIVE_CACHE_FILE" 2>/dev/null || echo "0")
            local worktree=$(jq -r '.git.worktree // ""' "$LIVE_CACHE_FILE" 2>/dev/null || echo "")
            echo "${changes}|${branch}|${worktree}"
            return 0
        elif [[ "$in_repo" == "false" ]]; then
            echo "0|not_a_repo|"
            return 0
        fi
    fi

    # Fallback: calculate directly (slower but works if daemon not running)
    local git_info="0|not_a_repo|"
    if git rev-parse --git-dir >/dev/null 2>&1; then
        local changes branch worktree
        changes=$(git status --porcelain=v1 -u 2>/dev/null | wc -l | tr -d ' ' || echo "0")
        branch=$(git symbolic-ref --short HEAD 2>/dev/null || git rev-parse --short HEAD 2>/dev/null || echo "detached")

        # Detect if we're in a worktree (not the main working tree)
        # Compare git-dir with git-common-dir: in a worktree, git-dir is .git/worktrees/<name>
        worktree=""
        local git_dir git_common_dir
        git_dir=$(git rev-parse --git-dir 2>/dev/null)
        git_common_dir=$(git rev-parse --git-common-dir 2>/dev/null)

        # If git-dir != git-common-dir, we're in a worktree
        if [[ -n "$git_dir" && -n "$git_common_dir" && "$git_dir" != "$git_common_dir" ]]; then
            # Extract worktree name from git-dir path
            # git-dir is typically: /path/to/repo/.git/worktrees/<worktree-name>
            if [[ "$git_dir" == *"/worktrees/"* ]]; then
                worktree="${git_dir##*/worktrees/}"
                # Remove any trailing slashes or paths
                worktree="${worktree%%/*}"
            fi
        fi

        git_info="${changes}|${branch}|${worktree}"
    fi

    echo "$git_info"
}

# Model component - uses display_name directly when provided by Claude Code
get_model_component() {
    local model="${1:-}"

    if [[ -z "$model" || "$model" == "null" ]]; then
        echo "🤖 Unavailable"
        return 0
    fi

    # If model looks like a display name (e.g., "Opus", "Sonnet"), use it directly
    # Claude Code now provides model.display_name in the JSON
    if [[ "$model" =~ ^[A-Z][a-z]+$ ]]; then
        echo "🤖 $model"
        return 0
    fi

    # Fallback: process model.id for backwards compatibility
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

# Directory component
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

# Git component
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

# Worktree component - separate from git branch
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

# Session duration tracking - use persistent identifier (not tied to 5-hour windows)
get_session_file() {
    local dir_hash
    dir_hash=$(echo "$PWD" | md5 -q 2>/dev/null || echo "$PWD" | md5sum | cut -d' ' -f1 2>/dev/null || echo "default")
    echo "/tmp/claude_session_${dir_hash}"
}

# Get session ID file for tracking current session
get_session_id_file() {
    local dir_hash
    dir_hash=$(echo "$PWD" | md5 -q 2>/dev/null || echo "$PWD" | md5sum | cut -d' ' -f1 2>/dev/null || echo "default")
    echo "/tmp/claude_session_id_${dir_hash}"
}

# Extract session ID from JSON data
get_current_session_id() {
    local json="$1"

    # Try multiple possible session ID fields
    local session_id
    session_id=$(extract_json "$json" "conversation_uuid" 2>/dev/null ||
                  extract_json "$json" "session_id" 2>/dev/null ||
                  extract_json "$json" "conversation_id" 2>/dev/null ||
                  extract_json "$json" "workspace.conversation_uuid" 2>/dev/null ||
                  echo "")

    echo "$session_id"
}

# Initialize or get session start time
get_session_start() {
    # If we have valid usage data (tokens > 0), session has started
    local input_tokens="$1" output_tokens="$2" json="${3:-}"
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
            # Start new session
            date +%s > "$session_file" 2>/dev/null || echo "$(date +%s)" > "$session_file"
        fi
    fi

    if [[ -f "$session_file" ]]; then
        cat "$session_file" 2>/dev/null || echo "0"
    else
        echo "0"
    fi
}

# Get session duration
get_session_duration() {
    local input_tokens="$1" output_tokens="$2" json="${3:-}"
    local session_start
    session_start=$(get_session_start "$input_tokens" "$output_tokens" "$json")

    if [[ "$session_start" == "0" ]]; then
        echo "0"
        return
    fi

    local current_time duration_seconds
    current_time=$(date +%s)
    duration_seconds=$((current_time - session_start))

    # Format duration as minutes (or hours:minutes if > 60 min)
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

# Get token usage from transcript file (Claude Code method)
get_transcript_tokens() {
    local transcript_path="$1"

    if [[ ! -f "$transcript_path" ]]; then
        echo "0|0"
        return 0
    fi

    # Extract tokens from JSONL transcript file using jq if available
    if command -v jq >/dev/null 2>&1; then
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

# Context component - now uses dynamic context_window_size from Claude Code
get_context_component() {
    local input_tokens="${1:-0}" output_tokens="${2:-0}" context_window_size="${3:-200000}"

    # For new sessions with no usage, show 0%
    if [[ "$input_tokens" == "0" && "$output_tokens" == "0" ]] || [[ -z "$input_tokens" || -z "$output_tokens" ]]; then
        echo "📊 0%"
        return 0
    fi

    # Ensure context_window_size is valid (fallback to 200000 if invalid)
    if [[ -z "$context_window_size" || "$context_window_size" == "0" || "$context_window_size" == "null" ]]; then
        context_window_size=200000
    fi

    local total=$((input_tokens + output_tokens))
    local percent=$((total * 100 / context_window_size))
    [[ $percent -gt 100 ]] && percent=100

    echo "📊 ${percent}%"
}

# Cost component
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

# Lines component
get_lines_component() {
    local added="${1:-0}" removed="${2:-0}"

    if [[ "$added" == "0" && "$removed" == "0" ]] || [[ -z "$added" || -z "$removed" ]]; then
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

# Session duration component using Claude Code's total_duration_ms
get_session_component() {
    local json="${1:-}"
    local duration_ms
    duration_ms=$(extract_json "$json" "cost.total_duration_ms" 2>/dev/null || echo "0")

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

# Get actual Claude window start time (when first tokens were received)
get_window_start_file() {
    local dir_hash
    dir_hash=$(echo "$PWD" | md5 -q 2>/dev/null || echo "$PWD" | md5sum | cut -d' ' -f1 2>/dev/null || echo "default")
    echo "/tmp/claude_window_start_${dir_hash}"
}

# Session start cache configuration
SESSION_CACHE_FILE="/tmp/claude_session_start_cache"
SESSION_CACHE_TTL=60  # 60 seconds max

# Get current active block start using session block detection
# OPTIMIZED: Uses find -mmin (fast) instead of stat loop, with 60s caching
get_claude_session_start() {
    local current_time
    current_time=$(date +%s)

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
    local session_duration_s=18000  # 5 hours in seconds
    local all_timestamps=()
    local cutoff_time=$((current_time - 21600))  # 6 hours ago

    # Use find -mmin for FAST file filtering (instead of slow stat loop)
    # -mmin -360 = modified within last 360 minutes (6 hours)
    for claude_dir in "$HOME/.config/claude/projects" "$HOME/.claude/projects"; do
        if [[ -d "$claude_dir" ]]; then
            while IFS= read -r jsonl_file; do
                [[ -z "$jsonl_file" ]] && continue
                # Extract timestamps and convert to epoch using cross-platform helper
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
            if [[ "$time_since_block_start" -gt "$session_duration_s" ]] || [[ "$time_since_last_entry" -gt "$session_duration_s" ]]; then
                current_block_start=$(floor_epoch_to_hour "$timestamp")
            fi
            last_entry_time="$timestamp"
        fi
    done

    # Check if current block is still active
    local result="$current_time"
    if [[ "$current_block_start" -gt 0 ]] && [[ "$last_entry_time" -gt 0 ]]; then
        local time_since_last_activity=$((current_time - last_entry_time))
        local block_end_time=$((current_block_start + session_duration_s))

        # Block is active if: time since last activity < 5h AND current time < block end
        if [[ "$time_since_last_activity" -lt "$session_duration_s" ]] && [[ "$current_time" -lt "$block_end_time" ]]; then
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

# Legacy helper - now uses cross-platform floor_epoch_to_hour
floor_to_hour() {
    floor_epoch_to_hour "$1"
}

# Track when the 5-hour Claude window actually started (using Claude Code session data)
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
        # Check if we have actual usage (successful API response)
        if [[ "$input_tokens" -gt 0 ]] || [[ "$output_tokens" -gt 0 ]] 2>/dev/null; then
            # Window started - record timestamp
            date +%s > "$window_file" 2>/dev/null || echo "$(date +%s)" > "$window_file"
        fi
    fi

    if [[ -f "$window_file" ]]; then
        local window_start current_time
        window_start=$(cat "$window_file" 2>/dev/null || echo "0")
        current_time=$(date +%s)

        # Check if window has expired (more than 5 hours = 18000 seconds)
        if [[ "$window_start" -gt 0 ]] && [[ $((current_time - window_start)) -gt 18000 ]]; then
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

# Time component with actual Claude window tracking
get_time_component() {
    local input_tokens="${1:-0}" output_tokens="${2:-0}"
    local window_start
    window_start=$(get_window_start "$input_tokens" "$output_tokens")

    if [[ "$window_start" == "0" ]]; then
        echo "🔄 N/A"  # No active window
        return 0
    fi

    # Claude uses a 5-hour rolling window that resets at the top of full hours
    local current_time reset_timestamp
    current_time=$(date +%s)

    # Calculate when the window should reset (next full hour after 5 hours from start)
    local exact_reset_time next_full_hour
    exact_reset_time=$((window_start + 18000))  # 5 hours = 18000 seconds

    # Round down to the previous full hour (Claude resets at or before the 5-hour mark)
    prev_full_hour=$(( exact_reset_time / 3600 * 3600 ))
    reset_timestamp=$prev_full_hour

    local seconds_until_reset
    seconds_until_reset=$((reset_timestamp - current_time))

    if [[ $seconds_until_reset -le 0 ]]; then
        echo "🔄 Reset"  # Window expired
        return 0
    fi

    # Convert to hours and minutes for remaining time
    local hours_until minutes_remaining
    hours_until=$((seconds_until_reset / 3600))
    minutes_remaining=$(((seconds_until_reset % 3600) / 60))

    # Calculate progress percentage based on actual window duration
    local total_window_seconds elapsed_seconds progress_pct
    total_window_seconds=$((reset_timestamp - window_start))
    elapsed_seconds=$((current_time - window_start))
    progress_pct=$((elapsed_seconds * 100 / total_window_seconds))

    # Ensure progress percentage is within bounds
    if (( progress_pct < 0 )); then
        progress_pct=0
    elif (( progress_pct > 100 )); then
        progress_pct=100
    fi

    # Format reset time as HH:MM
    local reset_time_display
    if command -v date >/dev/null 2>&1; then
        # Try macOS format first, then Linux format
        reset_time_display=$(date -r "$reset_timestamp" "+%H:%M" 2>/dev/null || date -d "@$reset_timestamp" "+%H:%M" 2>/dev/null || echo "??:??")
    else
        reset_time_display="??:??"
    fi

    # Format remaining time display
    local time_display
    if (( hours_until > 0 )); then
        if (( minutes_remaining > 0 )); then
            time_display="${hours_until}h ${minutes_remaining}m"
        else
            time_display="${hours_until}h"
        fi
    else
        time_display="${minutes_remaining}m"
    fi

    echo "🔄 ${time_display} until reset at ${reset_time_display}"
}

# Main statusline builder
build_statusline() {
    local json="$1"
    local current_dir="${2:-$(pwd)}"
    [[ -z "$json" ]] && json='{}'


    # Extract all data with error handling
    local model_id model_display cost_usd lines_added lines_removed transcript_path
    local input_tokens output_tokens context_window_size
    model_id=$(extract_json "$json" "model.id" 2>/dev/null || echo "")
    model_display=$(extract_json "$json" "model.display_name" 2>/dev/null || echo "")
    cost_usd=$(extract_json "$json" "cost.total_cost_usd" 2>/dev/null || echo "")
    lines_added=$(extract_json "$json" "cost.total_lines_added" 2>/dev/null || echo "0")
    lines_removed=$(extract_json "$json" "cost.total_lines_removed" 2>/dev/null || echo "0")
    transcript_path=$(extract_json "$json" "transcript_path" 2>/dev/null || echo "")

    # Extract context window size (new in Claude Code JSON structure)
    context_window_size=$(extract_json "$json" "context_window.context_window_size" 2>/dev/null || echo "200000")

    # Get token usage - prioritize context_window.* fields (new structure), then fallback
    input_tokens=$(extract_json "$json" "context_window.total_input_tokens" 2>/dev/null || echo "")
    output_tokens=$(extract_json "$json" "context_window.total_output_tokens" 2>/dev/null || echo "")

    # If context_window.* fields not available, try transcript file or other locations
    if [[ -z "$input_tokens" || "$input_tokens" == "null" ]]; then
        if [[ -n "$transcript_path" && -f "$transcript_path" ]]; then
            local tokens
            tokens=$(get_transcript_tokens "$transcript_path")
            input_tokens="${tokens%|*}"
            output_tokens="${tokens#*|}"
        else
            # Fallback: try legacy locations for token data
            input_tokens=$(extract_json "$json" "cost.total_input_tokens" 2>/dev/null ||
                            extract_json "$json" "usage.total_input_tokens" 2>/dev/null ||
                            extract_json "$json" "total_input_tokens" 2>/dev/null ||
                            echo "0")
            output_tokens=$(extract_json "$json" "cost.total_output_tokens" 2>/dev/null ||
                            extract_json "$json" "usage.total_output_tokens" 2>/dev/null ||
                            extract_json "$json" "total_output_tokens" 2>/dev/null ||
                            echo "0")
        fi
    fi

    # Ensure tokens have default values
    input_tokens="${input_tokens:-0}"
    output_tokens="${output_tokens:-0}"

    # Use display name directly if available (Claude Code now provides this)
    local model="${model_display:-$model_id}"

    # Build components
    local components=()
    local comp

    comp=$(get_model_component "$model")
    [[ -n "$comp" ]] && components+=("$comp")

    comp=$(get_directory_component "$current_dir")
    [[ -n "$comp" ]] && components+=("$comp")

    comp=$(get_git_component)
    [[ -n "$comp" ]] && components+=("$comp")

    comp=$(get_worktree_component)
    [[ -n "$comp" ]] && components+=("$comp")

    comp=$(get_context_component "$input_tokens" "$output_tokens" "$context_window_size")
    [[ -n "$comp" ]] && components+=("$comp")

    comp=$(get_cost_component "$cost_usd")
    [[ -n "$comp" ]] && components+=("$comp")

    comp=$(get_lines_component "$lines_added" "$lines_removed")
    [[ -n "$comp" ]] && components+=("$comp")

    comp=$(get_session_component "$json")
    [[ -n "$comp" ]] && components+=("$comp")

    comp=$(get_time_component "$input_tokens" "$output_tokens")
    [[ -n "$comp" ]] && components+=("$comp")

    # Assemble statusline
    local statusline=""
    local first=1

    for comp in "${components[@]}"; do
        if (( first )); then
            statusline="$comp"
            first=0
        else
            statusline="$statusline │ $comp"
        fi
    done

    echo "$statusline"
}

# Debug logging function
debug_log() {
    [[ "${STATUSLINE_DEBUG:-0}" != "1" ]] && return

    local json="$1"
    local log_file="/tmp/claude_statusline_debug.log"

    {
        echo "=== $(date) ==="
        echo "Raw JSON length: ${#json}"
        echo "Raw JSON: $json"
        echo
        echo "Token extractions (context_window priority):"
        echo "  context_window.total_input_tokens: '$(extract_json "$json" "context_window.total_input_tokens" 2>/dev/null || echo "MISSING")'"
        echo "  context_window.total_output_tokens: '$(extract_json "$json" "context_window.total_output_tokens" 2>/dev/null || echo "MISSING")'"
        echo "  context_window.context_window_size: '$(extract_json "$json" "context_window.context_window_size" 2>/dev/null || echo "MISSING")'"
        echo "  cost.total_input_tokens (fallback): '$(extract_json "$json" "cost.total_input_tokens" 2>/dev/null || echo "MISSING")'"
        echo "=================================="
        echo
    } >> "$log_file"
}

# Main function with robust error handling
main() {
    local json=""

    # Daemon disabled - direct calculation is fast enough (<50ms)
    # Git operations are quick and Claude calls statusline frequently
    # No need for background daemon complexity

    # Read input safely
    if [[ -t 0 ]]; then
        json='{"model":{},"workspace":{"current_dir":"'${PWD}'"},"cost":{}}'
    else
        json=$(cat 2>/dev/null || echo '{}')
    fi

    # Debug logging
    debug_log "$json"

    # Get current directory safely
    local current_dir
    current_dir=$(extract_json "$json" "workspace.current_dir" 2>/dev/null || echo "$PWD")

    # Build and output statusline
    build_statusline "$json" "$current_dir"

    # Performance monitoring (optional)
    if [[ "${STATUSLINE_PERF:-0}" == "1" ]]; then
        local end_time duration_ms
        end_time=$(date +%s%N 2>/dev/null || date +%s000000000)
        duration_ms=$(( (end_time - START_TIME) / 1000000 ))
        echo "Robust statusline: ${duration_ms}ms" >&2
    fi
}

# Execute
main "$@" 2>/dev/null || {
    # Ultimate fallback
    echo "🤖 Claude │ 📁 $(basename "$PWD") │ 🌿 $(git symbolic-ref --short HEAD 2>/dev/null || echo "main") │ 🔄 5h"
}
