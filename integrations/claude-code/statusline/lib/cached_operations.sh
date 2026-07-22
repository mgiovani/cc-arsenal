#!/bin/bash
# Cached implementations of expensive statusline operations

set -euo pipefail

# Source dependencies
source "$(dirname "${BASH_SOURCE[0]}")/cache_manager.sh"
source "$(dirname "${BASH_SOURCE[0]}")/git_info.sh"
source "$(dirname "${BASH_SOURCE[0]}")/utils.sh"
source "$(dirname "${BASH_SOURCE[0]}")/usage_tracker.sh"

# Cached git branch lookup
get_git_branch_cached() {
    # Skip cache for performance debugging
    if [[ "${STATUSLINE_SKIP_CACHE:-0}" == "1" ]]; then
        get_git_branch
        return
    fi

    local cache_key="git.branch.$(pwd)"
    local deps=(
        ".git/HEAD"
        ".git/refs/heads"
    )

    cache_lazy "$cache_key" "get_git_branch" "${deps[@]}"
}

# Cached git status lookup
get_git_status_cached() {
    # Skip cache for performance debugging
    if [[ "${STATUSLINE_SKIP_CACHE:-0}" == "1" ]]; then
        get_git_status
        return
    fi

    local cache_key="git.status.$(pwd)"
    local deps=(
        ".git/index"
        ".git/HEAD"
    )

    # Only cache if we're in a git repo
    if ! git rev-parse --git-dir &>/dev/null; then
        get_git_status
        return
    fi

    cache_lazy "$cache_key" "get_git_status" "${deps[@]}"
}

# Cached git component (combines branch and status)
get_git_component_cached() {
    # Use fast cache for statusline performance
    local cache_key="git.component.$(pwd)"

    if ! git rev-parse --git-dir &>/dev/null; then
        get_git_component
        return
    fi

    cache_fast "$cache_key" get_git_component
}

# Cached directory resolution
get_directory_cached() {
    local current_dir="$1"
    local cache_key="directory.$(pwd)"

    # Inline the directory display logic
    cache_lazy "$cache_key" "bash -c '
        local dir=\"$current_dir\"
        local display_mode
        display_mode=\$(get_config \".formatting.directory_display_mode\" \"short\")

        case \"\$display_mode\" in
            \"full\")
                echo \"\$dir\"
                ;;
            \"short\"|*)
                shorten_path \"\$dir\"
                ;;
        esac
    '"
}

# Cached configuration parsing
get_config_cached() {
    local key="$1"
    local default="$2"
    local config_file="${ACTIVE_CONFIG_FILE:-$CONFIG_FILE}"
    local cache_key="config.${key}.$(stat -c %Y "$config_file" 2>/dev/null || echo 0)"

    cache_lazy "$cache_key" "get_config $(printf '%q' "$key") $(printf '%q' "$default")" "$config_file"
}

# Cached boolean config parsing
get_config_bool_cached() {
    local key="$1"
    local default="$2"
    local config_file="${ACTIVE_CONFIG_FILE:-$CONFIG_FILE}"
    local cache_key="config_bool.${key}.$(stat -c %Y "$config_file" 2>/dev/null || echo 0)"

    cache_lazy "$cache_key" "get_config_bool $(printf '%q' "$key") $(printf '%q' "$default")" "$config_file"
}

# Cached JSON parsing (batch operations)
parse_json_cached() {
    local json_input="$1"
    local json_hash
    json_hash=$(echo -n "$json_input" | sha256sum | cut -d' ' -f1 | head -c 12)
    local cache_key="json.parse.$json_hash"

    # Create a temporary function that can access the json_input parameter
    # Use base64 encoding to safely pass JSON through shell
    local json_b64
    json_b64=$(echo -n "$json_input" | base64 -w 0 2>/dev/null || echo -n "$json_input" | base64)

    cache_lazy "$cache_key" "echo '$json_b64' | base64 -d | jq -c '{
        model_id: .model.id,
        model_display_name: .model.display_name,
        total_cost_usd: .cost.total_cost_usd,
        current_dir: .workspace.current_dir,
        total_duration_ms: .cost.total_duration_ms,
        api_duration_ms: .cost.total_api_duration_ms,
        lines_added: .cost.total_lines_added,
        lines_removed: .cost.total_lines_removed,
        input_tokens: .cost.total_input_tokens,
        output_tokens: .cost.total_output_tokens
    }' 2>/dev/null"
}

# Cached usage calculations
get_daily_usage_cached() {
    local usage_file="$USAGE_DB"
    local cache_key="usage.daily.$(date +%Y-%m-%d)"
    local deps=("$usage_file")

    [[ -f "$usage_file" ]] && deps+=("$usage_file")

    cache_lazy "$cache_key" "get_daily_usage" "${deps[@]}"
}

# Cached reset time calculation
get_next_reset_time_cached() {
    local usage_file="$USAGE_DB"
    local cache_key="reset.countdown.$(date +%Y-%m-%d-%H-%M)"
    local deps=("$usage_file")

    [[ -f "$usage_file" ]] && deps+=("$usage_file")

    cache_lazy "$cache_key" "get_next_reset_time" "${deps[@]}"
}

# Cached model information extraction
extract_model_info_cached() {
    local json_input="$1"
    local model_id model_display_name

    # Extract model info from cached JSON parse
    local parsed_json
    if parsed_json=$(parse_json_cached "$json_input"); then
        model_id=$(echo "$parsed_json" | jq -r '.model_id // ""')
        model_display_name=$(echo "$parsed_json" | jq -r '.model_display_name // ""')

        # Return structured model info
        echo "$model_display_name|$model_id"
    fi
}

# Cached context percentage calculation
calculate_context_percentage_cached() {
    local input_tokens="$1"
    local output_tokens="$2"
    local cache_key="context.calc.$input_tokens.$output_tokens"

    # Simple calculation - create inline command with variables substituted
    cache_lazy "$cache_key" "bash -c '
        local tokens_used=\$(($input_tokens + $output_tokens))
        local context_window_size=200000

        if [[ \$tokens_used -gt 0 ]]; then
            local context_percent=\$((100 - (\$tokens_used * 100 / \$context_window_size)))
            [[ \$context_percent -lt 0 ]] && context_percent=0
            echo \"\$context_percent\"
        else
            echo \"100\"
        fi
    '"
}

# Cached terminal width detection
get_terminal_width_cached() {
    local cache_key="terminal.width"

    # Cache terminal width briefly (it rarely changes during session)
    cache_lazy "$cache_key" "get_terminal_width"
}

# Cached path shortening
shorten_path_cached() {
    local path="$1"
    local cache_key="path.short.$(echo -n "$path" | sha256sum | cut -d' ' -f1 | head -c 12)"

    cache_lazy "$cache_key" "shorten_path $(printf '%q' "$path")"
}

# Performance profiling wrapper
cache_profile_operation() {
    local operation_name="$1"
    shift

    local start_time end_time duration
    start_time=$(date +%s%N)

    # Execute the operation
    local result
    result=$("$@")

    end_time=$(date +%s%N)
    duration=$(((end_time - start_time) / 1000000))  # Convert to milliseconds

    # Log timing metric
    cache_increment_metric "timing.${operation_name}" "$duration"

    echo "$result"
}

# Batch cache warming for common operations
cache_warm_statusline() {
    # Pre-warm frequently accessed cache entries
    {
        get_git_branch_cached >/dev/null 2>&1 &
        get_terminal_width_cached >/dev/null 2>&1 &
        get_daily_usage_cached >/dev/null 2>&1 &
        wait
    } || true
}

# Cache-aware component builders
get_model_component_cached() {
    local model="$1"
    local model_version="${2:-}"
    local cache_key="component.model.$model"

    # Use fast cache for better performance
    if [[ -n "$model_version" ]]; then
        cache_fast "$cache_key" get_model_component "$model" "$model_version"
    else
        cache_fast "$cache_key" get_model_component "$model"
    fi
}

get_directory_component_cached() {
    local current_dir="$1"
    local cache_key="component.directory.$(pwd)"

    cache_fast "$cache_key" get_directory_component "$current_dir"
}

get_context_component_cached() {
    local context_percent="$1"
    local cache_key="component.context.$context_percent"

    cache_fast "$cache_key" get_context_component "$context_percent"
}

get_session_cost_component_cached() {
    local session_cost_display="$1"
    local cache_key="component.session_cost.$session_cost_display"

    # Handle empty strings properly for caching
    if [[ -z "$session_cost_display" ]]; then
        cache_lazy "$cache_key" "get_session_cost_component ''"
    else
        cache_lazy "$cache_key" "get_session_cost_component $(printf '%q' "$session_cost_display")"
    fi
}

get_daily_cost_component_cached() {
    local daily_cost_display="$1"
    local cache_key="component.daily_cost.$daily_cost_display"

    # Handle empty string properly - pass empty string without quotes
    if [[ -n "$daily_cost_display" ]]; then
        cache_lazy "$cache_key" "get_daily_cost_component $(printf '%q' "$daily_cost_display")"
    else
        cache_lazy "$cache_key" "get_daily_cost_component"
    fi
}

get_reset_component_cached() {
    local next_reset="$1"
    local cache_key="reset.countdown.component.$next_reset"

    cache_lazy "$cache_key" "get_reset_component $(printf '%q' "$next_reset")"
}

# Cache invalidation helpers
invalidate_git_cache() {
    local pwd_hash
    pwd_hash=$(echo -n "$(pwd)" | sha256sum | cut -d' ' -f1 | head -c 16)

    cache_invalidate "git.branch.$(pwd)"
    cache_invalidate "git.status.$(pwd)"
    cache_invalidate "git.component.$(pwd)"
}

invalidate_config_cache() {
    # Invalidate all config-related cache entries
    find "$CACHE_L2_DIR" -name "*config*" -delete 2>/dev/null || true
}

invalidate_usage_cache() {
    # Invalidate usage-related cache entries
    cache_invalidate "usage.daily.$(date +%Y-%m-%d)"
    cache_invalidate "usage.reset.$(date +%Y-%m-%d-%H)"
}

# Debug function to inspect cache for a key
cache_debug_key() {
    local key="$1"
    local cache_file
    cache_file=$(cache_get_path "$key")
    local operation="${key%%.*}"
    local ttl
    ttl=$(cache_get_config "$operation" "ttl" "60")

    echo "=== Cache Debug: $key ==="
    echo "Operation: $operation"
    echo "TTL: ${ttl}s"
    echo "Cache file: $cache_file"

    if [[ -f "$cache_file" ]]; then
        local file_age
        file_age=$(stat -c %Y "$cache_file" 2>/dev/null || stat -f %m "$cache_file" 2>/dev/null)
        echo "File exists: Yes"
        echo "File age: $(($(date +%s) - file_age))s"
        echo "Is valid: $(cache_is_valid "$cache_file" "$ttl" && echo "Yes" || echo "No")"
        echo "Content:"
        cat "$cache_file" 2>/dev/null | head -3
    else
        echo "File exists: No"
    fi
}
