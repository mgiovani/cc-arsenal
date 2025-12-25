#!/bin/bash
# =============================================================================
# Cache Utilities - Simple, fast caching for statusline data
# =============================================================================
# Provides file-based caching with TTL support. Designed for quick operations
# that don't need the complexity of the full cache_manager.sh.

# Guard clause - prevent multiple sourcing
if [[ -n "${STATUSLINE_CACHE_LOADED:-}" ]]; then
    return 0
fi
readonly STATUSLINE_CACHE_LOADED=1

# Source dependencies
STATUSLINE_CORE_DIR="$(dirname "${BASH_SOURCE[0]}")"
source "$STATUSLINE_CORE_DIR/platform.sh"

# =============================================================================
# Configuration
# =============================================================================

# Default cache directory (per-process for isolation)
STATUSLINE_CACHE_DIR="${STATUSLINE_CACHE_DIR:-/tmp/statusline_cache_$$}"

# Default TTL in seconds
STATUSLINE_CACHE_DEFAULT_TTL="${STATUSLINE_CACHE_DEFAULT_TTL:-30}"

# =============================================================================
# Cache Directory Management
# =============================================================================

# Initialize cache directory
# Called automatically on first cache operation
_cache_init() {
    if [[ ! -d "$STATUSLINE_CACHE_DIR" ]]; then
        mkdir -p "$STATUSLINE_CACHE_DIR" 2>/dev/null || {
            # Fallback to /tmp if directory creation fails
            STATUSLINE_CACHE_DIR="/tmp"
        }
    fi
}

# Setup cleanup trap (call once at script start)
cache_setup_cleanup() {
    trap "rm -rf '$STATUSLINE_CACHE_DIR' 2>/dev/null || true" EXIT 2>/dev/null || true
}

# =============================================================================
# Cache Operations
# =============================================================================

# Get value from cache if not expired
# Usage: cache_get "key" [ttl_seconds]
# Returns: cached value or exits with 1 if cache miss/expired
cache_get() {
    local key="$1"
    local ttl="${2:-$STATUSLINE_CACHE_DEFAULT_TTL}"

    _cache_init

    # Sanitize key for filename (replace / with _)
    local cache_file="$STATUSLINE_CACHE_DIR/${key//\//_}"

    if [[ -f "$cache_file" ]] 2>/dev/null; then
        local cache_time current_time cache_age

        cache_time=$(get_file_mtime "$cache_file")
        current_time=$(get_current_epoch)
        cache_age=$((current_time - cache_time))

        if (( cache_age < ttl )); then
            cat "$cache_file" 2>/dev/null && return 0
        fi
    fi

    return 1
}

# Set value in cache
# Usage: cache_set "key" "value"
cache_set() {
    local key="$1"
    local value="$2"

    _cache_init

    # Sanitize key for filename
    local cache_file="$STATUSLINE_CACHE_DIR/${key//\//_}"

    echo "$value" > "$cache_file" 2>/dev/null || true
}

# Get or compute cached value
# Usage: cache_get_or_compute "key" "command" [ttl_seconds]
# If cache miss, runs command and caches result
cache_get_or_compute() {
    local key="$1"
    local command="$2"
    local ttl="${3:-$STATUSLINE_CACHE_DEFAULT_TTL}"

    local cached_value
    if cached_value=$(cache_get "$key" "$ttl"); then
        echo "$cached_value"
        return 0
    fi

    # Cache miss - compute and store
    local value
    value=$(eval "$command") || return 1

    cache_set "$key" "$value"
    echo "$value"
}

# Delete a specific cache entry
# Usage: cache_delete "key"
cache_delete() {
    local key="$1"
    local cache_file="$STATUSLINE_CACHE_DIR/${key//\//_}"
    rm -f "$cache_file" 2>/dev/null || true
}

# Clear all cache entries
# Usage: cache_clear
cache_clear() {
    if [[ -d "$STATUSLINE_CACHE_DIR" && "$STATUSLINE_CACHE_DIR" == /tmp/* ]]; then
        rm -rf "$STATUSLINE_CACHE_DIR"/* 2>/dev/null || true
    fi
}

# =============================================================================
# Specialized Cache Operations
# =============================================================================

# Check if cache file exists and is recent
# Usage: cache_is_valid "key" [ttl_seconds]
# Returns: 0 if valid, 1 otherwise
cache_is_valid() {
    local key="$1"
    local ttl="${2:-$STATUSLINE_CACHE_DEFAULT_TTL}"

    local cache_file="$STATUSLINE_CACHE_DIR/${key//\//_}"

    if [[ -f "$cache_file" ]]; then
        local cache_time current_time cache_age
        cache_time=$(get_file_mtime "$cache_file")
        current_time=$(get_current_epoch)
        cache_age=$((current_time - cache_time))
        (( cache_age < ttl ))
    else
        return 1
    fi
}

# Get cache age in seconds
# Usage: cache_age "key"
# Returns: age in seconds or -1 if not cached
cache_age() {
    local key="$1"
    local cache_file="$STATUSLINE_CACHE_DIR/${key//\//_}"

    if [[ -f "$cache_file" ]]; then
        local cache_time current_time
        cache_time=$(get_file_mtime "$cache_file")
        current_time=$(get_current_epoch)
        echo $((current_time - cache_time))
    else
        echo "-1"
    fi
}
