#!/bin/bash
# Usage tracking utilities

# Prevent multiple sourcing
if [[ -n "${USAGE_TRACKER_LOADED:-}" ]]; then
    return 0
fi
readonly USAGE_TRACKER_LOADED=1

source "$(dirname "${BASH_SOURCE[0]}")/utils.sh"

# Constants (allow test overrides)
readonly USAGE_DIR="${TEST_USAGE_DIR:-$HOME/.claude/cc-arsenal}"
readonly USAGE_DB="${TEST_USAGE_DB:-$USAGE_DIR/usage_tracking.json}"
readonly CLAUDE_DIR="${TEST_CLAUDE_DIR:-$HOME/.claude}"

# Initialize usage tracking
setup_usage_tracking() {
    mkdir -p "$USAGE_DIR"

    if [[ ! -f "$USAGE_DB" ]]; then
        echo '{"daily_usage":{},"window_start":""}' > "$USAGE_DB"
    fi
}

# Update daily usage
update_daily_usage() {
    local cost="$1"
    local current_date
    current_date=$(get_current_date)

    if [[ -z "$cost" || "$cost" == "0" || "$cost" == "null" ]]; then
        return
    fi

    local temp_file
    temp_file=$(mktemp)

    if [[ -f "$USAGE_DB" ]]; then
        jq --arg date "$current_date" --arg cost "$cost" '
            .daily_usage[$date] = ((((.daily_usage[$date] // 0) + ($cost | tonumber)) * 10000) | round) / 10000
        ' "$USAGE_DB" > "$temp_file" && mv "$temp_file" "$USAGE_DB"
    fi
}

# Get daily usage
get_daily_usage() {
    local current_date
    current_date=$(get_current_date)

    if [[ -f "$USAGE_DB" ]]; then
        jq -r --arg date "$current_date" '.daily_usage[$date] // 0' "$USAGE_DB" 2>/dev/null || echo "0"
    else
        echo "0"
    fi
}


# Update 5-hour window tracking
update_window_tracking() {
    local current_timestamp
    current_timestamp=$(get_current_timestamp)

    local temp_file
    temp_file=$(mktemp)

    if [[ -f "$USAGE_DB" ]]; then
        local window_start
        window_start=$(jq -r '.window_start // empty' "$USAGE_DB" 2>/dev/null)

        if [[ -z "$window_start" || "$window_start" == "null" ]]; then
            # Start new 5-hour window
            jq --arg timestamp "$current_timestamp" '
                .window_start = $timestamp
            ' "$USAGE_DB" > "$temp_file" && mv "$temp_file" "$USAGE_DB"
        else
            # Check if current window has expired (more than 5 hours old)
            local window_age=$((current_timestamp - window_start))
            if [[ $window_age -gt 18000 ]]; then  # 5 hours = 18000 seconds
                # Window expired, start new one
                jq --arg timestamp "$current_timestamp" '
                    .window_start = $timestamp
                ' "$USAGE_DB" > "$temp_file" && mv "$temp_file" "$USAGE_DB"
            fi
        fi
    fi
}

# Get next reset time (based on 5-hour windows starting at hour boundaries)
get_next_reset_time() {
    local current_timestamp current_hour_start hours_since_start
    current_timestamp=$(get_current_timestamp)

    # Find current hour boundary
    if command -v date >/dev/null 2>&1; then
        # Get the timestamp of the current hour start (e.g., if it's 15:12, get 15:00:00)
        current_hour_start=$(date -j -f "%H:%M:%S" "$(date +%H):00:00" +%s 2>/dev/null)

        if [[ -z "$current_hour_start" ]]; then
            echo "5h0m"
            return
        fi

        # Find which 5-hour window we're in
        # Claude's windows appear to be: 9-14h, 14-19h, 19-24h, 0-5h, 5-9h
        local current_hour
        current_hour=$(date +%H | sed 's/^0//')  # Remove leading zero

        # Calculate which window we're in and when it ends
        local next_window_hour
        if [[ $current_hour -ge 9 && $current_hour -lt 14 ]]; then
            next_window_hour=14  # 9-14h window, resets at 14:00
        elif [[ $current_hour -ge 14 && $current_hour -lt 19 ]]; then
            next_window_hour=19  # 14-19h window, resets at 19:00
        elif [[ $current_hour -ge 19 ]]; then
            next_window_hour=24  # 19-24h window, resets at 0:00
        elif [[ $current_hour -ge 0 && $current_hour -lt 5 ]]; then
            next_window_hour=5   # 0-5h window, resets at 5:00
        else
            next_window_hour=9   # 5-9h window, resets at 9:00
        fi

        # Calculate next reset time
        local next_reset_timestamp
        if [[ $next_window_hour -eq 24 ]]; then
            # Next day at midnight
            next_reset_timestamp=$(date -j -f "%Y-%m-%d %H:%M:%S" "$(date -v+1d +%Y-%m-%d) 00:00:00" +%s 2>/dev/null)
        else
            # Today at the next window hour
            next_reset_timestamp=$(date -j -f "%H:%M:%S" "$(printf "%02d:00:00" $next_window_hour)" +%s 2>/dev/null)
        fi

        if [[ -n "$next_reset_timestamp" ]]; then
            local time_until_reset=$((next_reset_timestamp - current_timestamp))

            if [[ $time_until_reset -gt 0 ]]; then
                format_duration "$time_until_reset"
            else
                echo "now"
            fi
        else
            echo "5h0m"
        fi
    else
        echo "5h0m"
    fi
}

# Extract model name from multiple data sources
extract_model_name() {
    local json_input="$1"

    # Try multiple model extraction paths - Claude Code uses different structures
    local model_candidates=(
        "$(get_json_field "$json_input" '.model.id' '')"
        "$(get_json_field "$json_input" '.model.display_name' '')"
        "$(get_json_field "$json_input" '.message.model' '')"
        "$(get_json_field "$json_input" '.Model' '')"
        "$(get_json_field "$json_input" '.usage.model' '')"
        "$(get_json_field "$json_input" '.request.model' '')"
        "$(get_json_field "$json_input" '.modelName' '')"
        "$(get_json_field "$json_input" '.model_name' '')"
        "$(get_json_field "$json_input" '.model' '')"
    )

    # Return first non-empty candidate, or empty if none found
    for candidate in "${model_candidates[@]}"; do
        if [[ -n "$candidate" && "$candidate" != "null" && "$candidate" != "" ]]; then
            echo "$candidate"
            return
        fi
    done

    # No model found - return empty instead of fake data
    echo ""
}

# Normalize model name for consistent usage
normalize_model_name() {
    local model="$1"

    if [[ -z "$model" ]]; then
        echo ""
        return
    fi

    local model_lower
    model_lower=$(echo "$model" | tr '[:upper:]' '[:lower:]')

    # Handle various model name formats and map to standard keys
    if [[ "$model_lower" == *"opus"* ]]; then
        if [[ "$model_lower" == *"3.5"* ]]; then
            echo "claude-3-5-opus"
        elif [[ "$model_lower" == *"4"* ]]; then
            echo "claude-4-opus"
        else
            echo "claude-3-opus"
        fi
    elif [[ "$model_lower" == *"sonnet"* ]]; then
        if [[ "$model_lower" == *"3.5"* ]]; then
            echo "claude-3-5-sonnet"
        elif [[ "$model_lower" == *"4"* ]]; then
            echo "claude-4-sonnet"
        else
            echo "claude-3-sonnet"
        fi
    elif [[ "$model_lower" == *"haiku"* ]]; then
        if [[ "$model_lower" == *"3.5"* ]]; then
            echo "claude-3-5-haiku"
        elif [[ "$model_lower" == *"4"* ]]; then
            echo "claude-4-haiku"
        else
            echo "claude-3-haiku"
        fi
    else
        # Remove common prefixes and suffixes, keep essential parts
        echo "$model_lower" | sed 's/^claude-//' | sed 's/-[0-9]\{8\}$//'
    fi
}

# Calculate session cost from active session data
calculate_session_cost() {
    local json_input="$1"

    # Extract session cost from active block data
    local session_cost
    session_cost=$(get_json_field "$json_input" '.costUSD' '')

    # If not found, try alternative Claude Code format
    if [[ -z "$session_cost" || "$session_cost" == "null" || "$session_cost" == "0" ]]; then
        session_cost=$(get_json_field "$json_input" '.cost.total_cost_usd' '0')
    fi

    # Validate we have real cost data
    if [[ "$session_cost" != "0" && "$session_cost" != "0.000" && "$session_cost" != "null" && -n "$session_cost" ]]; then
        echo "$session_cost"
    else
        echo "0"
    fi
}

# Calculate daily cost by aggregating usage entries from Claude Code data
calculate_daily_cost() {
    # Simply return our own tracking data for now (real data only)
    # File system search was causing performance issues
    get_daily_usage
}

# Get enhanced usage data from Claude dump files
get_enhanced_usage_data() {
    local current_dir="$1"

    # Try to find the most recent Claude dump file in the usage directory
    if [[ ! -d "$USAGE_DIR" ]]; then
        echo "{}"
        return
    fi

    # Look for recent dump files (within last hour)
    local recent_file=""
    local current_timestamp
    current_timestamp=$(get_current_timestamp)

    # Find the most recent file that's not too old (within last hour = 3600 seconds)
    while IFS= read -r -d '' file; do
        if [[ -f "$file" ]]; then
            local file_timestamp
            file_timestamp=$(stat -f "%m" "$file" 2>/dev/null || stat -c "%Y" "$file" 2>/dev/null || echo "0")

            if [[ $((current_timestamp - file_timestamp)) -lt 3600 ]]; then
                if [[ -z "$recent_file" || "$file_timestamp" -gt "$(stat -f "%m" "$recent_file" 2>/dev/null || stat -c "%Y" "$recent_file" 2>/dev/null || echo "0")" ]]; then
                    recent_file="$file"
                fi
            fi
        fi
    done < <(find "$USAGE_DIR" -name "*.json" -print0 2>/dev/null)

    # If we found a recent file, try to extract usage data from it
    if [[ -n "$recent_file" && -f "$recent_file" ]]; then
        # Try to extract Claude Code session data from the dump file
        local enhanced_data
        enhanced_data=$(jq -c '{
            model: .model,
            cost: .cost,
            tokens: {
                input: (.cost.total_input_tokens // 0),
                output: (.cost.total_output_tokens // 0)
            }
        }' "$recent_file" 2>/dev/null || echo "{}")

        # Validate that we got meaningful data
        local model_id cost_value
        model_id=$(echo "$enhanced_data" | jq -r '.model.id // empty' 2>/dev/null)
        cost_value=$(echo "$enhanced_data" | jq -r '.cost.total_cost_usd // "0"' 2>/dev/null)

        if [[ -n "$model_id" && "$model_id" != "null" ]] || [[ "$cost_value" != "0" && "$cost_value" != "0.000" ]]; then
            echo "$enhanced_data"
            return
        fi
    fi

    # No enhanced data available
    echo "{}"
}

# Clean up old data
cleanup_old_data() {
    local current_date
    current_date=$(get_current_date)
    local thirty_days_ago
    thirty_days_ago=$(date -d "$current_date - 30 days" +"%Y-%m-%d" 2>/dev/null || date -v-30d +"%Y-%m-%d" 2>/dev/null)

    if [[ -f "$USAGE_DB" && -n "$thirty_days_ago" ]]; then
        local temp_file
        temp_file=$(mktemp)

        jq --arg cutoff "$thirty_days_ago" '
            .daily_usage = (.daily_usage | to_entries | map(select(.key >= $cutoff)) | from_entries)
        ' "$USAGE_DB" > "$temp_file" && mv "$temp_file" "$USAGE_DB"
    fi
}
