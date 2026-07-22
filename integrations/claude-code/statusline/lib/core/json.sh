#!/bin/bash
# =============================================================================
# JSON Utilities - JSON parsing with jq primary, grep fallback
# =============================================================================
# Provides reliable JSON extraction that works with or without jq installed.
# Uses jq when available for accuracy, falls back to grep patterns for
# environments without jq.

# Guard clause - prevent multiple sourcing
if [[ -n "${STATUSLINE_JSON_LOADED:-}" ]]; then
    return 0
fi
readonly STATUSLINE_JSON_LOADED=1

# =============================================================================
# jq Detection
# =============================================================================

# Cached jq availability (empty = not checked, "true"/"false" = result)
_STATUSLINE_HAS_JQ=""

# Check if jq is available (cached for performance)
# Returns: 0 if jq available, 1 otherwise
check_jq() {
    if [[ -z "$_STATUSLINE_HAS_JQ" ]]; then
        _STATUSLINE_HAS_JQ=$(command -v jq >/dev/null 2>&1 && echo "true" || echo "false")
    fi
    [[ "$_STATUSLINE_HAS_JQ" == "true" ]]
}

# =============================================================================
# jq-based Extraction (Primary Method)
# =============================================================================

# JSON extraction using jq
# Supports any nested path like "context_window.total_input_tokens"
# Usage: extract_json_jq '{"a":1}' "a"
# Returns: extracted value or exits with 1 if not found
extract_json_jq() {
    local json="$1" key="$2"
    local result

    result=$(echo "$json" | jq -r ".${key} // empty" 2>/dev/null) || return 1
    [[ -n "$result" && "$result" != "null" ]] && echo "$result" && return 0
    return 1
}

# =============================================================================
# grep-based Extraction (Fallback Method)
# =============================================================================

# Extract string value from JSON using grep
# Usage: grep_string '{"name":"value"}' "name"
# Handles both compact JSON ("key":"value") and pretty JSON ("key": "value")
grep_string() {
    local json="$1" field="$2"
    echo "$json" | grep -oE "\"${field}\":[[:space:]]*\"[^\"]*\"" 2>/dev/null | \
        sed -E "s/\"${field}\":[[:space:]]*//" | \
        sed 's/^"//' | sed 's/"$//' | head -1
}

# Extract numeric value from JSON using grep
# Usage: grep_number '{"count":42}' "count"
# Handles both compact JSON ("key":123) and pretty JSON ("key": 123)
grep_number() {
    local json="$1" field="$2"
    echo "$json" | grep -oE "\"${field}\":[[:space:]]*[0-9.]+" 2>/dev/null | \
        sed -E "s/\"${field}\":[[:space:]]*//" | head -1
}

# Extract boolean value from JSON using grep
# Usage: grep_bool '{"enabled":true}' "enabled"
grep_bool() {
    local json="$1" field="$2"
    echo "$json" | grep -oE "\"${field}\":[[:space:]]*(true|false)" 2>/dev/null | \
        sed -E "s/\"${field}\":[[:space:]]*//" | head -1
}

# JSON extraction using grep patterns (fallback when jq unavailable)
# Maps JSON paths to their leaf field names for grep extraction
# Usage: extract_json_grep '{"model":{"id":"claude"}}' "model.id"
extract_json_grep() {
    local json="$1" key="$2"

    # Map paths to field names and types
    case "$key" in
        # String fields
        "model.id")                     grep_string "$json" "id" ;;
        "model.display_name")           grep_string "$json" "display_name" ;;
        "workspace.current_dir")        grep_string "$json" "current_dir" ;;
        "transcript_path")              grep_string "$json" "transcript_path" ;;
        "conversation_uuid")            grep_string "$json" "conversation_uuid" ;;
        "session_id")                   grep_string "$json" "session_id" ;;
        "conversation_id")              grep_string "$json" "conversation_id" ;;

        # Numeric fields - cost object
        "cost.total_cost_usd")          grep_number "$json" "total_cost_usd" ;;
        "cost.total_lines_added")       grep_number "$json" "total_lines_added" ;;
        "cost.total_lines_removed")     grep_number "$json" "total_lines_removed" ;;
        "cost.total_duration_ms")       grep_number "$json" "total_duration_ms" ;;
        "cost.total_input_tokens")      grep_number "$json" "total_input_tokens" ;;
        "cost.total_output_tokens")     grep_number "$json" "total_output_tokens" ;;

        # Numeric fields - context_window object
        "context_window.total_input_tokens")   grep_number "$json" "total_input_tokens" ;;
        "context_window.total_output_tokens")  grep_number "$json" "total_output_tokens" ;;
        "context_window.context_window_size")  grep_number "$json" "context_window_size" ;;

        # Numeric fields - context_window.current_usage object
        "context_window.current_usage.input_tokens")              grep_number "$json" "input_tokens" ;;
        "context_window.current_usage.output_tokens")             grep_number "$json" "output_tokens" ;;
        "context_window.current_usage.cache_creation_input_tokens") grep_number "$json" "cache_creation_input_tokens" ;;
        "context_window.current_usage.cache_read_input_tokens")   grep_number "$json" "cache_read_input_tokens" ;;

        # Numeric fields - usage object
        "usage.total_input_tokens")     grep_number "$json" "total_input_tokens" ;;
        "usage.total_output_tokens")    grep_number "$json" "total_output_tokens" ;;

        # Root level numeric fields
        "total_input_tokens")           grep_number "$json" "total_input_tokens" ;;
        "total_output_tokens")          grep_number "$json" "total_output_tokens" ;;

        # rate_limits fields - require jq (grep would collide with context_window.used_percentage)
        "rate_limits.five_hour.used_percentage")   return 1 ;;
        "rate_limits.five_hour.resets_at")         return 1 ;;
        "rate_limits.seven_day.used_percentage")   return 1 ;;
        "rate_limits.seven_day.resets_at")         return 1 ;;

        # worktree fields - require jq (grep would collide with other name/branch fields)
        "worktree.name")                           return 1 ;;
        "worktree.branch")                         return 1 ;;

        # Unknown key - no grep pattern available
        *) return 1 ;;
    esac
}

# =============================================================================
# Main JSON Extraction Function
# =============================================================================

# Main JSON extraction function
# Uses jq by default, falls back to grep if jq is unavailable
# Usage: extract_json '{"model":{"id":"claude"}}' "model.id"
# Returns: extracted value or exits with 1 if not found
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

# =============================================================================
# JSON Validation
# =============================================================================

# Check if string is valid JSON
# Usage: is_valid_json '{"a":1}'
# Returns: 0 if valid, 1 otherwise
is_valid_json() {
    local json="$1"

    if check_jq; then
        echo "$json" | jq -e . >/dev/null 2>&1
    else
        # Basic check: starts with { or [ and ends with } or ]
        [[ "$json" =~ ^\{.*\}$ ]] || [[ "$json" =~ ^\[.*\]$ ]]
    fi
}

# =============================================================================
# JSON Array Operations
# =============================================================================

# Get length of JSON array
# Usage: json_array_length '[1,2,3]'
# Returns: array length or 0
json_array_length() {
    local json="$1"

    if check_jq; then
        echo "$json" | jq -r 'length // 0' 2>/dev/null || echo "0"
    else
        # Basic count: count commas + 1 (rough approximation)
        local count=$(echo "$json" | tr -cd ',' | wc -c)
        echo $((count + 1))
    fi
}
