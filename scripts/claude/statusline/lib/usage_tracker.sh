#!/bin/bash
# Usage tracking utilities

# Prevent multiple sourcing
if [[ -n "${USAGE_TRACKER_LOADED:-}" ]]; then
    return 0
fi
readonly USAGE_TRACKER_LOADED=1

source "$(dirname "${BASH_SOURCE[0]}")/utils.sh"

# Constants (allow test overrides)
readonly USAGE_DIR="${TEST_USAGE_DIR:-$HOME/.claude/claude_dump}"
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
            .daily_usage[$date] = ((.daily_usage[$date] // 0) + ($cost | tonumber))
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