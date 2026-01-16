#!/bin/bash
# Enterprise-grade in-memory cache for sub-100ms statusline performance
# Uses tmpfs-backed memory cache with zero-copy operations

set -euo pipefail

# Memory cache configuration
if [[ -z "${MEMORY_CACHE_DIR:-}" ]]; then
    readonly MEMORY_CACHE_DIR="/dev/shm/statusline_cache_$$"
fi
CACHE_EXPIRY=30
MAX_CACHE_SIZE=1048576  # 1MB limit

# Initialize memory cache (in RAM, not disk)
memory_cache_init() {
    # Create cache directory in shared memory
    mkdir -p "$MEMORY_CACHE_DIR" 2>/dev/null || return 0

    # Set memory-only filesystem properties if possible
    if command -v mount >/dev/null; then
        mount -t tmpfs -o size=10M tmpfs "$MEMORY_CACHE_DIR" 2>/dev/null || true
    fi

    # Cleanup on exit
    trap "rm -rf '$MEMORY_CACHE_DIR' 2>/dev/null || true" EXIT
}

# Ultra-fast memory cache get (direct file read from RAM)
memory_cache_get() {
    local key="$1"
    local cache_file="$MEMORY_CACHE_DIR/${key//\//_}"

    # Check if cache exists and is fresh
    if [[ -f "$cache_file" ]]; then
        local cache_time
        cache_time=$(stat -f %m "$cache_file" 2>/dev/null || echo 0)
        local current_time
        current_time=$(date +%s)

        if (( current_time - cache_time < CACHE_EXPIRY )); then
            cat "$cache_file"
            return 0
        fi
    fi

    return 1
}

# Ultra-fast memory cache set (direct write to RAM)
memory_cache_set() {
    local key="$1"
    local value="$2"
    local cache_file="$MEMORY_CACHE_DIR/${key//\//_}"

    # Write directly to memory, no fsync for max speed
    echo "$value" > "$cache_file"
}

# Atomic cache update with command execution
memory_cache_get_or_set() {
    local key="$1"
    shift
    local command=("$@")

    # Try cache first
    local cached_result
    if cached_result=$(memory_cache_get "$key"); then
        echo "$cached_result"
        return 0
    fi

    # Execute command and cache result
    local result
    if result=$("${command[@]}"); then
        memory_cache_set "$key" "$result"
        echo "$result"
        return 0
    else
        return 1
    fi
}

# Batch operations for maximum efficiency
memory_cache_batch_get() {
    local -A results
    local key

    for key in "$@"; do
        if result=$(memory_cache_get "$key"); then
            results["$key"]="$result"
        fi
    done

    # Output results as key=value pairs
    for key in "${!results[@]}"; do
        echo "$key=${results[$key]}"
    done
}

# Precompute expensive operations in background
memory_cache_precompute() {
    local pwd_cache="git_status_$(pwd)"
    local git_cache="git_branch_$(pwd)"

    # Background precomputation (non-blocking)
    {
        if git rev-parse --git-dir >/dev/null 2>&1; then
            git status --porcelain=v1 -u 2>/dev/null | memory_cache_set "$pwd_cache" "$(cat)"
            git symbolic-ref --short HEAD 2>/dev/null | memory_cache_set "$git_cache" "$(cat)"
        fi
    } &
}

# Initialize on first load
if [[ -z "${MEMORY_CACHE_INITIALIZED:-}" ]]; then
    memory_cache_init
    readonly MEMORY_CACHE_INITIALIZED=1
fi
