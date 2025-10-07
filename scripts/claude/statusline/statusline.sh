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

# Robust JSON extraction with multiple fallbacks
extract_json() {
    local json="$1" key="$2"

    # Try jq first (most reliable)
    if command -v jq >/dev/null 2>&1; then
        local result
        result=$(echo "$json" | jq -r ".${key} // empty" 2>/dev/null || echo "")
        if [[ -n "$result" && "$result" != "null" && "$result" != "empty" ]]; then
            echo "$result"
            return 0
        fi
    fi

    # Fallback: simple grep extraction for basic cases
    case "$key" in
        "model.id")
            echo "$json" | grep -o '"id":"[^"]*"' 2>/dev/null | sed 's/"id":"//' | sed 's/"//' | head -1
            ;;
        "model.display_name")
            echo "$json" | grep -o '"display_name":"[^"]*"' 2>/dev/null | sed 's/"display_name":"//' | sed 's/"//' | head -1
            ;;
        "workspace.current_dir")
            echo "$json" | grep -o '"current_dir":"[^"]*"' 2>/dev/null | sed 's/"current_dir":"//' | sed 's/"//' | head -1
            ;;
        "cost.total_cost_usd")
            echo "$json" | grep -o '"total_cost_usd":[0-9.]*' 2>/dev/null | sed 's/"total_cost_usd"://' | head -1
            ;;
        "cost.total_input_tokens")
            echo "$json" | grep -o '"total_input_tokens":[0-9]*' 2>/dev/null | sed 's/"total_input_tokens"://' | head -1
            ;;
        "cost.total_output_tokens")
            echo "$json" | grep -o '"total_output_tokens":[0-9]*' 2>/dev/null | sed 's/"total_output_tokens"://' | head -1
            ;;
        "cost.total_lines_added")
            echo "$json" | grep -o '"total_lines_added":[0-9]*' 2>/dev/null | sed 's/"total_lines_added"://' | head -1
            ;;
        "cost.total_lines_removed")
            echo "$json" | grep -o '"total_lines_removed":[0-9]*' 2>/dev/null | sed 's/"total_lines_removed"://' | head -1
            ;;
        "cost.total_duration_ms")
            echo "$json" | grep -o '"total_duration_ms":[0-9]*' 2>/dev/null | sed 's/"total_duration_ms"://' | head -1
            ;;
        "usage.total_input_tokens")
            echo "$json" | grep -o '"total_input_tokens":[0-9]*' 2>/dev/null | sed 's/"total_input_tokens"://' | head -1
            ;;
        "usage.total_output_tokens")
            echo "$json" | grep -o '"total_output_tokens":[0-9]*' 2>/dev/null | sed 's/"total_output_tokens"://' | head -1
            ;;
        "total_input_tokens")
            echo "$json" | grep -o '"total_input_tokens":[0-9]*' 2>/dev/null | sed 's/"total_input_tokens"://' | head -1
            ;;
        "total_output_tokens")
            echo "$json" | grep -o '"total_output_tokens":[0-9]*' 2>/dev/null | sed 's/"total_output_tokens"://' | head -1
            ;;
        "message.usage.input_tokens")
            echo "$json" | grep -o '"input_tokens":[0-9]*' 2>/dev/null | sed 's/"input_tokens"://' | head -1
            ;;
        "message.usage.output_tokens")
            echo "$json" | grep -o '"output_tokens":[0-9]*' 2>/dev/null | sed 's/"output_tokens"://' | head -1
            ;;
        "usage.input_tokens")
            echo "$json" | grep -o '"input_tokens":[0-9]*' 2>/dev/null | sed 's/"input_tokens"://' | head -1
            ;;
        "usage.output_tokens")
            echo "$json" | grep -o '"output_tokens":[0-9]*' 2>/dev/null | sed 's/"output_tokens"://' | head -1
            ;;
    esac
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

    # We have the lock - start daemon completely asynchronously
    # Spawn in subshell to avoid blocking statusline
    if [[ -x "$DAEMON_SCRIPT" ]]; then
        (
            # Start daemon and clean up lock in background
            "$DAEMON_SCRIPT" start </dev/null >/dev/null 2>&1
            sleep 1
            rmdir "$lock_file" 2>/dev/null || true
        ) &
        # Don't wait - return immediately so statusline is fast
    else
        # No daemon script, release lock immediately
        rmdir "$lock_file" 2>/dev/null || true
    fi
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
            echo "${changes}|${branch}"
            return 0
        elif [[ "$in_repo" == "false" ]]; then
            echo "0|not_a_repo"
            return 0
        fi
    fi

    # Fallback: calculate directly (slower but works if daemon not running)
    local git_info="0|not_a_repo"
    if git rev-parse --git-dir >/dev/null 2>&1; then
        local changes branch
        changes=$(git status --porcelain=v1 -u 2>/dev/null | wc -l | tr -d ' ' || echo "0")
        branch=$(git symbolic-ref --short HEAD 2>/dev/null || git rev-parse --short HEAD 2>/dev/null || echo "detached")
        git_info="${changes}|${branch}"
    fi

    echo "$git_info"
}

# Model component with robust cleanup
get_model_component() {
    local model="${1:-}"

    if [[ -z "$model" || "$model" == "null" ]]; then
        echo "🤖 Unavailable"
        return 0
    fi

    # Safe model cleanup
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
    git_info=$(get_git_info 2>/dev/null || echo "0|not_a_repo")

    local changes="${git_info%|*}"
    local branch="${git_info#*|}"

    if [[ "$branch" == "not_a_repo" ]]; then
        return 0  # No git component
    fi

    local status_symbol=""
    if [[ "$changes" -gt 0 ]] 2>/dev/null; then
        status_symbol=" ●"
    fi

    echo "🌿 $branch$status_symbol"
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

# Context component
get_context_component() {
    local input_tokens="${1:-0}" output_tokens="${2:-0}"

    # For new sessions with no usage, show 0%
    if [[ "$input_tokens" == "0" && "$output_tokens" == "0" ]] || [[ -z "$input_tokens" || -z "$output_tokens" ]]; then
        echo "📊 0%"
        return 0
    fi

    local total=$((input_tokens + output_tokens))
    local percent=$((total * 100 / 200000))
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

# Daily cost component - read from live cache or Claude usage tracking
get_daily_cost() {
    # Try live cache first (instant)
    if [[ -f "$LIVE_CACHE_FILE" ]] && command -v jq >/dev/null 2>&1; then
        local cached_cost=$(jq -r '.cost.daily_cost // empty' "$LIVE_CACHE_FILE" 2>/dev/null || echo "")
        if [[ -n "$cached_cost" && "$cached_cost" != "null" ]]; then
            echo "$cached_cost"
            return 0
        fi
    fi

    # Fallback: read directly from usage tracking
    local usage_file="$HOME/.claude/usage_tracking.json"
    local today=$(date +"%Y-%m-%d")

    if [[ -f "$usage_file" ]] && command -v jq >/dev/null 2>&1; then
        local daily_usage
        daily_usage=$(jq -r ".daily_usage.\"$today\" // 0" "$usage_file" 2>/dev/null || echo "0")

        if [[ "$daily_usage" != "0" ]] && [[ "$daily_usage" =~ ^[0-9.]+$ ]]; then
            printf "%.2f" "$daily_usage"
        else
            echo "0.00"
        fi
    else
        echo "0.00"
    fi
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

# Get current active block start using session block detection
get_claude_session_start() {
    local current_time
    current_time=$(date +%s)
    local session_duration_ms=18000000  # 5 hours in milliseconds
    local session_duration_s=18000      # 5 hours in seconds

    # Collect timestamps from recent session files (last 6 hours)
    local all_timestamps=()
    local cutoff_time=$((current_time - 21600))  # 6 hours ago

    # Check Claude data directories for recent JSONL files
    for claude_dir in "$HOME/.config/claude/projects" "$HOME/.claude/projects"; do
        if [[ -d "$claude_dir" ]]; then
            while IFS= read -r -d '' jsonl_file; do
                if [[ -f "$jsonl_file" ]] && [[ $(stat -f %m "$jsonl_file" 2>/dev/null || echo "0") -gt $cutoff_time ]]; then
                    # Extract timestamps and convert to epoch
                    while IFS= read -r timestamp_line; do
                        if [[ -n "$timestamp_line" ]]; then
                            local timestamp_epoch
                            timestamp_epoch=$(TZ=UTC date -j -f "%Y-%m-%dT%H:%M:%S" "${timestamp_line%.*}" +%s 2>/dev/null || echo "0")
                            if [[ "$timestamp_epoch" -gt $cutoff_time ]]; then
                                all_timestamps+=("$timestamp_epoch")
                            fi
                        fi
                    done < <(grep -o '"timestamp":"[^"]*"' "$jsonl_file" 2>/dev/null | cut -d'"' -f4)
                fi
            done < <(find "$claude_dir" -name "*.jsonl" -type f -print0 2>/dev/null)
        fi
    done

    # If no timestamps found, return current hour floored
    if [[ ${#all_timestamps[@]} -eq 0 ]]; then
        local current_hour_floored
        current_hour_floored=$(TZ=UTC date -r "$current_time" "+%Y-%m-%d %H:00:00")
        TZ=UTC date -j -f "%Y-%m-%d %H:%M:%S" "$current_hour_floored" +%s 2>/dev/null || echo "$current_time"
        return
    fi

    # Sort timestamps chronologically
    IFS=$'\n' all_timestamps=($(sort -n <<< "${all_timestamps[*]}")); unset IFS

    # Apply session block detection algorithm
    local current_block_start=0
    local current_block_entries=()
    local last_entry_time=0

    for timestamp in "${all_timestamps[@]}"; do
        if [[ "$current_block_start" -eq 0 ]]; then
            # First timestamp - start new block (floored to hour)
            current_block_start=$(floor_to_hour "$timestamp")
            last_entry_time="$timestamp"
        else
            # Check if this timestamp should start a new block
            local time_since_block_start=$((timestamp - current_block_start))
            local time_since_last_entry=$((timestamp - last_entry_time))

            # If time since block start > 5h OR time since last entry > 5h, start new block
            if [[ "$time_since_block_start" -gt $session_duration_s ]] || [[ "$time_since_last_entry" -gt $session_duration_s ]]; then
                # Start new block (floored to hour)
                current_block_start=$(floor_to_hour "$timestamp")
            fi
            last_entry_time="$timestamp"
        fi
    done

    # Check if current block is still active
    if [[ "$current_block_start" -gt 0 ]] && [[ "$last_entry_time" -gt 0 ]]; then
        local time_since_last_activity=$((current_time - last_entry_time))
        local block_end_time=$((current_block_start + session_duration_s))

        # Block is active if: time since last activity < 5h AND current time < block end
        if [[ "$time_since_last_activity" -lt $session_duration_s ]] && [[ "$current_time" -lt $block_end_time ]]; then
            echo "$current_block_start"
            return
        fi
    fi

    # No active block found, return current hour floored
    local current_hour_floored
    current_hour_floored=$(TZ=UTC date -r "$current_time" "+%Y-%m-%d %H:00:00")
    TZ=UTC date -j -f "%Y-%m-%d %H:%M:%S" "$current_hour_floored" +%s 2>/dev/null || echo "$current_time"
}

# Helper function to floor timestamp to hour boundary
floor_to_hour() {
    local timestamp="$1"
    local hour_floored
    hour_floored=$(TZ=UTC date -r "$timestamp" "+%Y-%m-%d %H:00:00")
    TZ=UTC date -j -f "%Y-%m-%d %H:%M:%S" "$hour_floored" +%s 2>/dev/null || echo "$timestamp"
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
    local json="${1:-{}}"
    local current_dir="${2:-$(pwd)}"

    # Extract all data with error handling
    local model_id model_display cost_usd lines_added lines_removed transcript_path
    local input_tokens output_tokens
    model_id=$(extract_json "$json" "model.id" 2>/dev/null || echo "")
    model_display=$(extract_json "$json" "model.display_name" 2>/dev/null || echo "")
    cost_usd=$(extract_json "$json" "cost.total_cost_usd" 2>/dev/null || echo "")
    lines_added=$(extract_json "$json" "cost.total_lines_added" 2>/dev/null || echo "0")
    lines_removed=$(extract_json "$json" "cost.total_lines_removed" 2>/dev/null || echo "0")
    transcript_path=$(extract_json "$json" "transcript_path" 2>/dev/null || echo "")

    # Get token usage from transcript file or JSON directly
    if [[ -n "$transcript_path" && -f "$transcript_path" ]]; then
        local tokens
        tokens=$(get_transcript_tokens "$transcript_path")
        input_tokens="${tokens%|*}"
        output_tokens="${tokens#*|}"
    else
        # Fallback: try multiple locations for token data
        input_tokens=$(extract_json "$json" "cost.total_input_tokens" 2>/dev/null ||
                        extract_json "$json" "usage.total_input_tokens" 2>/dev/null ||
                        extract_json "$json" "total_input_tokens" 2>/dev/null ||
                        echo "0")
        output_tokens=$(extract_json "$json" "cost.total_output_tokens" 2>/dev/null ||
                        extract_json "$json" "usage.total_output_tokens" 2>/dev/null ||
                        extract_json "$json" "total_output_tokens" 2>/dev/null ||
                        echo "0")
    fi


    # Use display name if available, fallback to ID
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

    comp=$(get_context_component "$input_tokens" "$output_tokens")
    [[ -n "$comp" ]] && components+=("$comp")

    comp=$(get_cost_component "$cost_usd")
    [[ -n "$comp" ]] && components+=("$comp")

    # Add daily cost component (always show, like session cost)
    local daily_cost="0.00"
    daily_cost=$(get_daily_cost)
    comp="📅 \$${daily_cost}"
    components+=("$comp")

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
        echo "Token extractions:"
        echo "  total_input_tokens: '$(extract_json "$json" "cost.total_input_tokens" 2>/dev/null || echo "MISSING")'"
        echo "  total_output_tokens: '$(extract_json "$json" "cost.total_output_tokens" 2>/dev/null || echo "MISSING")'"
        echo "=================================="
        echo
    } >> "$log_file"
}

# Main function with robust error handling
main() {
    local json=""

    # Auto-start daemon if not running (self-healing, zero-config)
    ensure_daemon_running

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
