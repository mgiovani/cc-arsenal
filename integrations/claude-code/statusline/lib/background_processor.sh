#!/bin/bash
# Background processor for proactive statusline data preparation
# Implements event-driven cache warming and smart pre-computation

set -euo pipefail

# Import dependencies
source "$(dirname "${BASH_SOURCE[0]}")/memory_cache.sh"
source "$(dirname "${BASH_SOURCE[0]}")/optimized_operations.sh"

BG_PROCESSOR_PID_FILE="/dev/shm/statusline_bg_processor_$$"
FILESYSTEM_WATCH_INTERVAL=2

# Smart cache warming based on current context
intelligent_cache_warm() {
    local current_pwd="$1"

    # Warm cache for current directory context
    {
        # Pre-compute git data in background
        if git rev-parse --git-dir >/dev/null 2>&1; then
            get_git_batch_data >/dev/null 2>&1
        fi

        # Pre-compute common time-based components
        get_current_timestamp_fast >/dev/null 2>&1
        get_reset_time_optimized >/dev/null 2>&1

        # Pre-compute directory component
        get_directory_component_optimized "$current_pwd" >/dev/null 2>&1

    } &

    # Store background job PID for cleanup
    echo $! > "$BG_PROCESSOR_PID_FILE"
}

# Filesystem event watcher (lightweight inotify alternative)
smart_filesystem_watcher() {
    local watch_dir="$1"
    local last_git_mtime=0
    local git_dir="$watch_dir/.git"

    # Only watch if we're in a git repository
    [[ -d "$git_dir" ]] || return 0

    # Background filesystem watching
    {
        while true; do
            # Check git index and HEAD for changes
            local current_mtime=0

            for file in "$git_dir/index" "$git_dir/HEAD"; do
                if [[ -f "$file" ]]; then
                    local file_mtime
                    file_mtime=$(stat -f %m "$file" 2>/dev/null || echo 0)
                    if (( file_mtime > current_mtime )); then
                        current_mtime=$file_mtime
                    fi
                fi
            done

            # If git state changed, invalidate cache
            if (( current_mtime > last_git_mtime )); then
                local git_cache_key="git_batch_$watch_dir"
                rm -f "$MEMORY_CACHE_DIR/${git_cache_key//\//_}" 2>/dev/null || true
                last_git_mtime=$current_mtime

                # Pre-warm new data
                get_git_batch_data >/dev/null 2>&1 &
            fi

            sleep "$FILESYSTEM_WATCH_INTERVAL"
        done
    } &

    # Track watcher PID
    echo $! >> "$BG_PROCESSOR_PID_FILE"
}

# Predictive cache loading based on directory navigation patterns
predictive_cache_warm() {
    local current_dir="$1"

    # Get parent and common sibling directories
    local parent_dir="${current_dir%/*}"
    local siblings=()

    if [[ -d "$parent_dir" && "$parent_dir" != "$current_dir" ]]; then
        # Pre-warm cache for likely navigation targets (non-blocking)
        {
            # Parent directory
            if [[ -d "$parent_dir/.git" ]]; then
                (cd "$parent_dir" && get_git_batch_data >/dev/null 2>&1) &
            fi

            # Common sibling directories (recent access pattern)
            local -a recent_dirs
            if command -v dirs >/dev/null 2>&1; then
                readarray -t recent_dirs < <(dirs -p | head -3)
                for dir in "${recent_dirs[@]}"; do
                    if [[ -d "$dir/.git" && "$dir" != "$current_dir" ]]; then
                        (cd "$dir" && get_git_batch_data >/dev/null 2>&1) &
                    fi
                done
            fi
        } &
    fi
}

# Lazy loading with intelligent fallbacks
lazy_load_component() {
    local component_type="$1"
    shift
    local args=("$@")

    case "$component_type" in
        "model")
            # Model parsing is fast, no lazy loading needed
            get_model_component_optimized "${args[@]}"
            ;;
        "directory")
            # Directory is fast, no lazy loading needed
            get_directory_component_optimized "${args[@]}"
            ;;
        "git")
            # Git can be slow, use lazy loading with cached fallback
            local git_data
            if git_data=$(get_git_batch_data); then
                get_git_component_optimized
            else
                # Fallback: show cached status or minimal info
                echo "🌿 unknown"
            fi
            ;;
        "context")
            # Context calculation is fast
            get_context_component_optimized "${args[@]}"
            ;;
        "reset")
            # Time calculation is fast
            get_reset_time_optimized "${args[@]}"
            ;;
        *)
            echo "Unknown component: $component_type"
            return 1
            ;;
    esac
}

# Circuit breaker for failing operations
circuit_breaker_execute() {
    local operation_name="$1"
    shift
    local command=("$@")

    local failure_cache_key="circuit_breaker_${operation_name}"
    local failure_count=0

    # Check failure count
    if failure_count_str=$(memory_cache_get "$failure_cache_key" 2>/dev/null); then
        failure_count=$failure_count_str
    fi

    # If too many failures, return cached result or fallback
    if (( failure_count > 3 )); then
        echo "Circuit breaker open for $operation_name, using fallback"
        return 1
    fi

    # Execute with timeout and failure tracking
    if timeout 5s "${command[@]}" 2>/dev/null; then
        # Success: reset failure count
        memory_cache_set "$failure_cache_key" "0"
        return 0
    else
        # Failure: increment counter
        memory_cache_set "$failure_cache_key" "$((failure_count + 1))"
        return 1
    fi
}

# Cleanup background processes
cleanup_background_processor() {
    if [[ -f "$BG_PROCESSOR_PID_FILE" ]]; then
        while read -r pid; do
            kill "$pid" 2>/dev/null || true
        done < "$BG_PROCESSOR_PID_FILE"
        rm -f "$BG_PROCESSOR_PID_FILE"
    fi
}

# Initialize background processing
init_background_processing() {
    local current_dir="$1"

    # Cleanup any existing background processes
    cleanup_background_processor

    # Start intelligent cache warming
    intelligent_cache_warm "$current_dir"

    # Start filesystem watching
    smart_filesystem_watcher "$current_dir"

    # Start predictive cache warming
    predictive_cache_warm "$current_dir"

    # Setup cleanup on exit
    trap cleanup_background_processor EXIT INT TERM
}

# Export main functions
export -f lazy_load_component
export -f circuit_breaker_execute
export -f init_background_processing
