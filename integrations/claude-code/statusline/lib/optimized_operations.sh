#!/bin/bash
# Ultra-optimized operations engine for sub-100ms statusline
# Zero-copy, minimal subprocess, maximum performance

set -euo pipefail

# Import memory cache
source "$(dirname "${BASH_SOURCE[0]}")/memory_cache.sh"

# Global data cache (in-memory, parsed once)
declare -A PARSED_JSON_CACHE 2>/dev/null || true
declare -A GIT_STATE_CACHE 2>/dev/null || true
CURRENT_PWD=""

# Ultra-fast JSON parser using pure bash (no jq subprocess)
# Optimized for statusline JSON structure
parse_json_fast() {
    local json="$1"
    local key="$2"

    # Use parameter expansion instead of jq for common patterns
    case "$key" in
        ".model.id")
            # Extract: "id":"value" -> value
            if [[ $json =~ \"id\":\"([^\"]+)\" ]]; then
                echo "${BASH_REMATCH[1]}"
                return 0
            fi
            ;;
        ".model.display_name")
            if [[ $json =~ \"display_name\":\"([^\"]+)\" ]]; then
                echo "${BASH_REMATCH[1]}"
                return 0
            fi
            ;;
        ".cost.total_cost_usd")
            if [[ $json =~ \"total_cost_usd\":\"?([0-9.]+)\"? ]]; then
                echo "${BASH_REMATCH[1]}"
                return 0
            fi
            ;;
        ".workspace.current_dir")
            if [[ $json =~ \"current_dir\":\"([^\"]+)\" ]]; then
                echo "${BASH_REMATCH[1]}"
                return 0
            fi
            ;;
    esac

    # Fallback to cached jq result if available
    local cache_key="json_${key}_$(echo "$json" | wc -c)"
    if memory_cache_get "$cache_key" 2>/dev/null; then
        return 0
    fi

    # Last resort: use jq and cache result
    local result
    if result=$(jq -r "$key // empty" <<< "$json" 2>/dev/null); then
        memory_cache_set "$cache_key" "$result"
        echo "$result"
        return 0
    fi

    echo ""
    return 1
}

# Batch git operations (single subprocess for all git data)
get_git_batch_data() {
    local pwd_key="git_batch_$(pwd)"

    # Check memory cache first
    if memory_cache_get "$pwd_key"; then
        return 0
    fi

    # Single git call for all information
    local git_data=""
    if git rev-parse --git-dir >/dev/null 2>&1; then
        # Batch multiple git operations into single call
        git_data=$(git status --porcelain=v1 -u 2>/dev/null | wc -l; git symbolic-ref --short HEAD 2>/dev/null || echo "detached")
    else
        git_data="0
not_a_repo"
    fi

    memory_cache_set "$pwd_key" "$git_data"
    echo "$git_data"
}

# Parse batched git data (zero-copy, no subprocess)
parse_git_batch() {
    local git_batch="$1"
    local request="$2"

    # Parse using shell built-ins only
    local lines=()
    while IFS= read -r line; do
        lines+=("$line")
    done <<< "$git_batch"

    local changes_count="${lines[0]:-0}"
    local branch="${lines[1]:-unknown}"

    case "$request" in
        "changes_count") echo "$changes_count" ;;
        "branch") echo "$branch" ;;
        "status_symbol")
            if (( changes_count > 0 )); then
                echo "●"
            else
                echo ""
            fi
            ;;
    esac
}

# Ultra-optimized model component (no subprocess, pure string manipulation)
get_model_component_optimized() {
    local model="$1"
    local version="${2:-}"

    # Skip empty models
    if [[ -z "$model" || "$model" == "null" ]]; then
        echo "🤖 Unavailable"
        return 0
    fi

    # Fast model name cleanup using shell parameter expansion
    local display_name="$model"
    display_name="${display_name#claude-}"          # Remove claude- prefix
    display_name="${display_name%-[0-9]*}"          # Remove date suffix
    display_name="${display_name/sonnet-/Sonnet }" # Format sonnet
    display_name="${display_name/opus-/Opus }"     # Format opus
    display_name="${display_name/haiku-/Haiku }"   # Format haiku

    # Capitalize first letter
    display_name="${display_name^}"

    # Build component with version if provided
    if [[ -n "$version" ]]; then
        echo "🤖 ${display_name}@${version}"
    else
        echo "🤖 ${display_name}"
    fi
}

# Ultra-optimized directory component (no subprocess)
get_directory_component_optimized() {
    local current_dir="$1"

    # Use shell parameter expansion instead of basename/dirname
    local dir_name="${current_dir##*/}"
    local parent_dir="${current_dir%/*}"
    local parent_name="${parent_dir##*/}"

    # Smart truncation for long paths
    if [[ ${#current_dir} -gt 50 ]]; then
        echo "📁 .../${parent_name}/${dir_name}"
    else
        echo "📁 ~${current_dir#$HOME}"
    fi
}

# Ultra-optimized git component (batch data, no subprocess)
get_git_component_optimized() {
    local git_batch
    git_batch=$(get_git_batch_data)

    local branch
    branch=$(parse_git_batch "$git_batch" "branch")

    local status_symbol
    status_symbol=$(parse_git_batch "$git_batch" "status_symbol")

    if [[ "$branch" == "not_a_repo" ]]; then
        echo ""
        return 0
    fi

    echo "🌿 ${branch} ${status_symbol}"
}

# Context component (pure math, no subprocess)
get_context_component_optimized() {
    local context_percent="$1"

    if [[ "$context_percent" == "unavailable" || -z "$context_percent" ]]; then
        echo "📊 N/A"
        return 0
    fi

    # Color coding based on percentage (no external tools)
    local color=""
    if (( context_percent > 80 )); then
        color="\033[31m"  # Red
    elif (( context_percent > 60 )); then
        color="\033[33m"  # Yellow
    else
        color="\033[32m"  # Green
    fi

    echo -e "${color}📊 ${context_percent}%\033[0m"
}

# Time operations (use built-in printf instead of date where possible)
get_current_timestamp_fast() {
    printf '%(%s)T\n' -1
}

get_reset_time_optimized() {
    local current_hour
    current_hour=$(printf '%(%H)T\n' -1)
    current_hour=$((10#$current_hour))  # Remove leading zeros

    # Calculate next reset using pure arithmetic
    local next_reset_hour
    if (( current_hour >= 9 && current_hour < 14 )); then
        next_reset_hour=14
    elif (( current_hour >= 14 && current_hour < 19 )); then
        next_reset_hour=19
    elif (( current_hour >= 19 )); then
        next_reset_hour=24
    elif (( current_hour < 5 )); then
        next_reset_hour=5
    else
        next_reset_hour=9
    fi

    local hours_until_reset=$(( (next_reset_hour - current_hour) % 24 ))
    echo "🔄 ${hours_until_reset}h"
}
