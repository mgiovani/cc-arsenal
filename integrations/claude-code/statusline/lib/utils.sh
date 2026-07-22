#!/bin/bash
# Utility functions for statusline

get_current_date() {
    date +"%Y-%m-%d"
}

get_current_timestamp() {
    date +"%s"
}

get_terminal_width() {
    tput cols 2>/dev/null || echo 80
}

# JSON parsing utilities
get_json_field() {
    local json="$1"
    local field="$2"
    local default="$3"
    local result
    result=$(echo "$json" | jq -r "if ($field | type) == \"string\" then $field else \"$default\" end" 2>/dev/null)
    if [[ -n "$result" && "$result" != "null" ]]; then
        echo "$result"
    else
        echo "$default"
    fi
}

get_json_number() {
    local json="$1"
    local field="$2"
    local default="$3"
    local result
    # Handle both number and string types that can be converted to numbers
    # Note: \\\\. is needed to produce \\. in jq for literal dot match
    result=$(echo "$json" | jq -r "if ($field | type) == \"number\" then $field elif ($field | type) == \"string\" and ($field | test(\"^[0-9]*\\\\.?[0-9]+\$\")) then ($field | tonumber) else $default end" 2>/dev/null)
    if [[ -n "$result" && "$result" != "null" ]]; then
        echo "$result"
    else
        echo "$default"
    fi
}

# Path utilities
shorten_path() {
    local path="$1"
    local max_length="${2:-25}"
    local home_dir="$HOME"

    # Replace home with ~
    if [[ "$path" == "$home_dir"* ]]; then
        path="~${path#$home_dir}"
    fi

    # Truncate if too long
    if [[ ${#path} -gt $max_length ]]; then
        path="...${path: -$((max_length - 3))}"
    fi

    echo "$path"
}

# Format time duration
format_duration() {
    local seconds="$1"
    local hours=$((seconds / 3600))
    local minutes=$(((seconds % 3600) / 60))

    if [[ $hours -gt 0 ]]; then
        echo "${hours}h${minutes}m"
    else
        echo "${minutes}m"
    fi
}

# Calculate session duration from ISO timestamp
calculate_session_duration() {
    local start_time="$1"

    if [[ -n "$start_time" && "$start_time" != "null" ]]; then
        if command -v python3 &>/dev/null; then
            python3 -c "
import datetime
try:
    start = datetime.datetime.fromisoformat('$start_time'.replace('Z', '+00:00'))
    now = datetime.datetime.now(datetime.timezone.utc)
    diff = now - start
    total_seconds = int(diff.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    if hours > 0:
        print(f'{hours}h{minutes:02d}m')
    else:
        print(f'{minutes}m')
except:
    pass
" 2>/dev/null
        fi
    fi
}
