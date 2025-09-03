#!/bin/bash
# Ultra-fast statusline with robust error handling
# Handles all edge cases and fallbacks gracefully

set -e  # Exit on error, but handle unset variables

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

# Robust git operations
get_git_info() {
    local cache_key="git_$(pwd)"
    
    if cache_get "$cache_key" 2>/dev/null; then
        return 0
    fi
    
    local git_info="0|not_a_repo"
    if git rev-parse --git-dir >/dev/null 2>&1; then
        local changes branch
        changes=$(git status --porcelain=v1 -u 2>/dev/null | wc -l | tr -d ' ' || echo "0")
        branch=$(git symbolic-ref --short HEAD 2>/dev/null || git rev-parse --short HEAD 2>/dev/null || echo "detached")
        git_info="${changes}|${branch}"
    fi
    
    cache_set "$cache_key" "$git_info" 2>/dev/null || true
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

# Get token usage from transcript file (Claude Code method)
get_transcript_tokens() {
    local transcript_path="$1"
    
    if [[ ! -f "$transcript_path" ]]; then
        echo "0|0"
        return 0
    fi
    
    # Extract tokens from JSONL transcript file using jq if available
    if command -v jq >/dev/null 2>&1; then
        local input_total output_total
        # Process JSONL file line by line and sum usage tokens
        input_total=$(jq -r 'select(.message.usage.input_tokens != null) | .message.usage.input_tokens // 0' "$transcript_path" 2>/dev/null | awk '{sum += $1} END {print sum + 0}')
        output_total=$(jq -r 'select(.message.usage.output_tokens != null) | .message.usage.output_tokens // 0' "$transcript_path" 2>/dev/null | awk '{sum += $1} END {print sum + 0}')
        echo "${input_total}|${output_total}"
        return 0
    fi
    
    # Fallback: grep extraction for JSONL format
    local input_total=0 output_total=0
    while IFS= read -r line; do
        if [[ "$line" =~ \"input_tokens\":([0-9]+) ]]; then
            input_total=$((input_total + ${BASH_REMATCH[1]}))
        fi
        if [[ "$line" =~ \"output_tokens\":([0-9]+) ]]; then
            output_total=$((output_total + ${BASH_REMATCH[1]}))
        fi
    done < "$transcript_path" 2>/dev/null || true
    
    echo "${input_total}|${output_total}"
}

# Context component
get_context_component() {
    local input_tokens="${1:-0}" output_tokens="${2:-0}"
    
    if [[ "$input_tokens" == "0" && "$output_tokens" == "0" ]] || [[ -z "$input_tokens" || -z "$output_tokens" ]]; then
        echo "📊 N/A"
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
    
    if [[ -z "$cost" || "$cost" == "0" || "$cost" == "null" ]]; then
        echo "💰 Unavailable"
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

# Time component with progress bar
get_time_component() {
    local current_hour current_min
    current_hour=$(date +%H | sed 's/^0//' 2>/dev/null || echo "0")
    current_min=$(date +%M | sed 's/^0//' 2>/dev/null || echo "0")
    
    # Claude's 5-hour windows: 0-5h, 5-9h, 9-14h, 14-19h, 19-24h
    local window_start window_end next_reset_hour
    if (( current_hour >= 0 && current_hour < 5 )); then
        window_start=0; window_end=5; next_reset_hour=5
    elif (( current_hour >= 5 && current_hour < 9 )); then
        window_start=5; window_end=9; next_reset_hour=9
    elif (( current_hour >= 9 && current_hour < 14 )); then
        window_start=9; window_end=14; next_reset_hour=14
    elif (( current_hour >= 14 && current_hour < 19 )); then
        window_start=14; window_end=19; next_reset_hour=19
    else  # 19-24h
        window_start=19; window_end=24; next_reset_hour=24
    fi
    
    # Calculate exact time until reset
    local current_minutes_total next_reset_minutes_total
    current_minutes_total=$((current_hour * 60 + current_min))
    
    if (( next_reset_hour == 24 )); then
        # Reset at midnight (00:00 next day)
        next_reset_minutes_total=$((24 * 60))
    else
        next_reset_minutes_total=$((next_reset_hour * 60))
    fi
    
    local minutes_until_reset
    minutes_until_reset=$((next_reset_minutes_total - current_minutes_total))
    
    # Convert to hours and minutes
    local hours_until minutes_remaining
    hours_until=$((minutes_until_reset / 60))
    minutes_remaining=$((minutes_until_reset % 60))
    
    # Format time display
    local time_display
    if (( hours_until > 0 )); then
        time_display="${hours_until}h ${minutes_remaining}m"
    else
        time_display="${minutes_remaining}m"
    fi
    
    echo "🔄 ${time_display}"
}

# Main statusline builder
build_statusline() {
    local json="${1:-{}}"
    local current_dir="${2:-$(pwd)}"
    
    # Extract all data with error handling
    local model_id model_display cost_usd input_tokens output_tokens lines_added lines_removed transcript_path
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
        input_tokens=$(extract_json "$json" "message.usage.input_tokens" 2>/dev/null || extract_json "$json" "usage.input_tokens" 2>/dev/null || extract_json "$json" "cost.total_input_tokens" 2>/dev/null || echo "0")
        output_tokens=$(extract_json "$json" "message.usage.output_tokens" 2>/dev/null || extract_json "$json" "usage.output_tokens" 2>/dev/null || extract_json "$json" "cost.total_output_tokens" 2>/dev/null || echo "0")
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
    
    comp=$(get_lines_component "$lines_added" "$lines_removed")
    [[ -n "$comp" ]] && components+=("$comp")
    
    comp=$(get_time_component)
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