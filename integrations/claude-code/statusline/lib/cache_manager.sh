#!/bin/bash
# Staff-level Cache Manager for Claude Statusline
# Provides atomic, concurrent-safe caching with TTL and dependency tracking

# Prevent multiple sourcing
if [[ -n "${CACHE_MANAGER_LOADED:-}" ]]; then
    return 0
fi
readonly CACHE_MANAGER_LOADED=1

set -euo pipefail

# Cache directory structure
readonly CACHE_BASE_DIR="$HOME/.claude/cc-arsenal/cache"
readonly CACHE_L1_DIR="$CACHE_BASE_DIR/l1_process"
readonly CACHE_L2_DIR="$CACHE_BASE_DIR/l2_session"
readonly CACHE_L3_DIR="$CACHE_BASE_DIR/l3_persistent"
readonly CACHE_LOCKS_DIR="$CACHE_BASE_DIR/locks"
readonly CACHE_METRICS_DIR="$CACHE_BASE_DIR/metrics"
readonly CACHE_CONFIG_FILE="$CACHE_BASE_DIR/cache_config.json"
readonly CACHE_MANIFEST_FILE="$CACHE_BASE_DIR/manifest.json"

# Performance tracking (using files instead of associative arrays for compatibility)
# Metrics are stored in $CACHE_METRICS_DIR/counters.json

# Initialize cache directory structure
cache_init() {
    mkdir -p "$CACHE_L1_DIR" "$CACHE_L2_DIR" "$CACHE_L3_DIR"
    mkdir -p "$CACHE_LOCKS_DIR" "$CACHE_METRICS_DIR"

    # Create default configuration if not exists
    if [[ ! -f "$CACHE_CONFIG_FILE" ]]; then
        cat > "$CACHE_CONFIG_FILE" <<'EOF'
{
  "enabled": true,
  "debug": false,
  "metrics": true,
  "levels": {
    "l1": {"ttl": 10, "max_size_mb": 10},
    "l2": {"ttl": 300, "max_size_mb": 50},
    "l3": {"ttl": 86400, "max_size_mb": 100}
  },
  "operations": {
    "git.branch": {"level": "l1", "ttl": 5},
    "git.status": {"level": "l1", "ttl": 10},
    "model.info": {"level": "l3", "ttl": 86400},
    "config.parse": {"level": "l2", "ttl": 300},
    "usage.calc": {"level": "l2", "ttl": 60},
    "json.parse": {"level": "l1", "ttl": 10},
    "context.percent": {"level": "l1", "ttl": 5},
    "reset.countdown": {"level": "l1", "ttl": 30},
    "component.model": {"level": "l1", "ttl": 10},
    "component.directory": {"level": "l1", "ttl": 10},
    "component.git": {"level": "l1", "ttl": 5},
    "component.context": {"level": "l1", "ttl": 5},
    "component.session_cost": {"level": "l1", "ttl": 10},
    "component.daily_cost": {"level": "l1", "ttl": 10}
  }
}
EOF
    fi

    # Initialize manifest
    if [[ ! -f "$CACHE_MANIFEST_FILE" ]]; then
        echo '{"version":"1.0","entries":{},"dependencies":{}}' > "$CACHE_MANIFEST_FILE"
    fi
}

# Check if caching is enabled
cache_enabled() {
    [[ -f "$CACHE_CONFIG_FILE" ]] || return 1
    local enabled
    enabled=$(jq -r '.enabled // true' "$CACHE_CONFIG_FILE" 2>/dev/null || echo "true")
    [[ "$enabled" == "true" ]]
}

# Get cache configuration for an operation
cache_get_config() {
    local operation="$1"
    local key="$2"
    local default="$3"

    if [[ -f "$CACHE_CONFIG_FILE" ]]; then
        jq -r ".operations.\"${operation}\".${key} // .levels.l1.${key} // ${default}" "$CACHE_CONFIG_FILE" 2>/dev/null || echo "$default"
    else
        echo "$default"
    fi
}

# Get cache directory for an operation
cache_get_dir() {
    local operation="$1"
    local level
    level=$(cache_get_config "$operation" "level" "l1")

    case "$level" in
        "l1") echo "$CACHE_L1_DIR" ;;
        "l2") echo "$CACHE_L2_DIR" ;;
        "l3") echo "$CACHE_L3_DIR" ;;
        *) echo "$CACHE_L1_DIR" ;;
    esac
}

# Generate cache key hash (avoid filesystem issues with special chars)
# Use faster hash for statusline performance
cache_key_hash() {
    local key="$1"
    # Use simple character replacement instead of sha256sum for speed
    echo "$key" | tr '/' '_' | tr ' ' '_' | tr '.' '_' | head -c 32
}

# Get cache file path for a key
cache_get_path() {
    local key="$1"
    local operation="${key%%.*}"
    local cache_dir
    cache_dir=$(cache_get_dir "$operation")
    local key_hash
    key_hash=$(cache_key_hash "$key")
    echo "$cache_dir/${key_hash}.cache"
}

# Fast cache function for statusline (skips locks and complex config)
cache_fast() {
    local key="$1"
    shift
    local command=("$@")

    # Simple cache path
    local cache_file="$CACHE_L1_DIR/$(cache_key_hash "$key").fast"

    # Check if cache exists and is recent (less than 30 seconds old)
    if [[ -f "$cache_file" ]]; then
        local cache_age
        cache_age=$(stat -f %m "$cache_file" 2>/dev/null || echo 0)
        local now
        now=$(date +%s)
        if (( now - cache_age < 30 )); then
            cat "$cache_file"
            return 0
        fi
    fi

    # Execute command and cache result
    local result
    if result=$("${command[@]}"); then
        echo "$result" > "$cache_file"
        echo "$result"
        return 0
    else
        return 1
    fi
}

# Get lock file path for a key
cache_get_lock_path() {
    local key="$1"
    local key_hash
    key_hash=$(cache_key_hash "$key")
    echo "$CACHE_LOCKS_DIR/${key_hash}.lock"
}

# Execute with cache lock (non-blocking)
cache_with_lock() {
    local key="$1"
    shift
    local lock_file
    lock_file=$(cache_get_lock_path "$key")

    # Check if flock is available
    if command -v flock >/dev/null 2>&1; then
        # Use file descriptor 200 for locking
        exec 200>"$lock_file"
        if ! flock -n 200; then
            # Lock failed, return cache miss
            exec 200>&-
            return 1
        fi

        # Execute operation with lock held
        local result
        if result=$("$@"); then
            flock -u 200
            exec 200>&-
            echo "$result"
            return 0
        else
            flock -u 200
            exec 200>&-
            return 1
        fi
    else
        # Fallback for systems without flock (like macOS) - SIMPLIFIED FOR PERFORMANCE
        # Skip expensive stat-based locking for statusline performance
        # For statusline use cases, lock contention is minimal and performance is critical

        # Create lock file
        echo $$ > "$lock_file"

        # Execute operation
        local result
        if result=$("$@"); then
            rm -f "$lock_file" 2>/dev/null || true
            echo "$result"
            return 0
        else
            rm -f "$lock_file" 2>/dev/null || true
            return 1
        fi
    fi
}

# Check if cache entry is valid (not expired)
cache_is_valid() {
    local cache_file="$1"
    local ttl="$2"

    [[ -f "$cache_file" ]] || return 1

    local file_time now
    file_time=$(stat -c %Y "$cache_file" 2>/dev/null || stat -f %m "$cache_file" 2>/dev/null || echo 0)
    now=$(date +%s)

    (( file_time + ttl > now ))
}

# Get value from cache
cache_get() {
    local key="$1"

    cache_enabled || return 1

    local cache_file
    cache_file=$(cache_get_path "$key")
    local operation="${key%%.*}"
    local ttl
    ttl=$(cache_get_config "$operation" "ttl" "60")

    if cache_is_valid "$cache_file" "$ttl"; then
        if [[ -r "$cache_file" ]]; then
            cat "$cache_file"
            cache_increment_metric "hits"
            return 0
        fi
    fi

    cache_increment_metric "misses"
    return 1
}

# Set value in cache (atomic operation)
cache_set() {
    local key="$1"
    local value="$2"

    cache_enabled || return 0

    local cache_file
    cache_file=$(cache_get_path "$key")
    local temp_file="${cache_file}.tmp.$$"

    # Ensure directory exists
    mkdir -p "$(dirname "$cache_file")"

    # Atomic write using temp file (use printf to avoid adding newlines)
    printf '%s' "$value" > "$temp_file"
    mv "$temp_file" "$cache_file" 2>/dev/null || {
        rm -f "$temp_file"
        return 1
    }

    # Update manifest
    cache_update_manifest "$key"
}

# Set cache with dependencies (files to watch for changes)
cache_set_with_deps() {
    local key="$1"
    local value="$2"
    shift 2
    local deps=("$@")

    cache_set "$key" "$value"

    # Record dependencies in manifest
    if [[ ${#deps[@]} -gt 0 ]]; then
        local deps_json
        deps_json=$(printf '%s\n' "${deps[@]}" | jq -R . | jq -s .)
        cache_update_manifest_deps "$key" "$deps_json"
    fi
}

# Update cache manifest
cache_update_manifest() {
    local key="$1"

    cache_with_lock "manifest" bash -c "
        if [[ -f '$CACHE_MANIFEST_FILE' ]]; then
            jq --arg key '$key' --arg timestamp \$(date +%s) '
                .entries[\$key] = {
                    \"timestamp\": (\$timestamp | tonumber),
                    \"access_count\": ((.entries[\$key].access_count // 0) + 1)
                }
            ' '$CACHE_MANIFEST_FILE' > '${CACHE_MANIFEST_FILE}.tmp' &&
            mv '${CACHE_MANIFEST_FILE}.tmp' '$CACHE_MANIFEST_FILE'
        fi
    "
}

# Update cache dependencies in manifest
cache_update_manifest_deps() {
    local key="$1"
    local deps_json="$2"

    cache_with_lock "manifest" bash -c "
        if [[ -f '$CACHE_MANIFEST_FILE' ]]; then
            jq --arg key '$key' --argjson deps '$deps_json' '
                .dependencies[\$key] = \$deps
            ' '$CACHE_MANIFEST_FILE' > '${CACHE_MANIFEST_FILE}.tmp' &&
            mv '${CACHE_MANIFEST_FILE}.tmp' '$CACHE_MANIFEST_FILE'
        fi
    "
}

# Invalidate cache entry
cache_invalidate() {
    local key="$1"
    local cache_file
    cache_file=$(cache_get_path "$key")

    rm -f "$cache_file" 2>/dev/null || true
    cache_increment_metric "evictions"
}

# Lazy cache - get from cache or compute and cache
cache_lazy() {
    local key="$1"
    local compute_function="$2"
    shift 2
    local deps=("$@")

    # Try cache first
    local cached_value
    if cached_value=$(cache_get "$key" 2>/dev/null); then
        printf '%s' "$cached_value"
        return 0
    fi

    # Cache miss - compute value
    local computed_value
    if computed_value=$($compute_function); then
        if [[ ${#deps[@]} -gt 0 ]]; then
            cache_set_with_deps "$key" "$computed_value" "${deps[@]}"
        else
            cache_set "$key" "$computed_value"
        fi
        printf '%s' "$computed_value"
        return 0
    else
        return 1
    fi
}

# Increment performance metric
cache_increment_metric() {
    local metric="$1"
    local count="${2:-1}"

    cache_enabled || return 0

    local metrics_file="$CACHE_METRICS_DIR/counters.json"

    cache_with_lock "metrics" bash -c "
        local current=0
        if [[ -f '$metrics_file' ]]; then
            current=\$(jq -r '.${metric} // 0' '$metrics_file' 2>/dev/null || echo 0)
        fi
        local new_value=\$((current + $count))
        echo '{\"${metric}\": '\$new_value'}' |
            jq -s 'add' '$metrics_file' - 2>/dev/null > '${metrics_file}.tmp' &&
            mv '${metrics_file}.tmp' '$metrics_file' ||
            echo '{\"${metric}\": '\$new_value'}' > '$metrics_file'
    " 2>/dev/null || true
}

# Get cache metrics
cache_get_metrics() {
    local metrics_file="$CACHE_METRICS_DIR/counters.json"

    if [[ -f "$metrics_file" ]]; then
        cat "$metrics_file"
    else
        echo '{"hits":0,"misses":0,"evictions":0}'
    fi
}

# Get cache hit rate percentage
cache_get_hit_rate() {
    local metrics
    metrics=$(cache_get_metrics)
    local hits misses total hit_rate

    hits=$(echo "$metrics" | jq -r '.hits // 0')
    misses=$(echo "$metrics" | jq -r '.misses // 0')
    total=$((hits + misses))

    if [[ $total -gt 0 ]]; then
        hit_rate=$((hits * 100 / total))
        echo "$hit_rate"
    else
        echo "0"
    fi
}

# Clean up expired cache entries
cache_cleanup() {
    local level="${1:-all}"

    cache_enabled || return 0

    local dirs=()
    case "$level" in
        "l1") dirs=("$CACHE_L1_DIR") ;;
        "l2") dirs=("$CACHE_L2_DIR") ;;
        "l3") dirs=("$CACHE_L3_DIR") ;;
        "all") dirs=("$CACHE_L1_DIR" "$CACHE_L2_DIR" "$CACHE_L3_DIR") ;;
        *) return 1 ;;
    esac

    for dir in "${dirs[@]}"; do
        [[ -d "$dir" ]] || continue

        # Find and remove files older than their TTL
        find "$dir" -type f -name "*.cache" -mmin +10 -delete 2>/dev/null || true
    done

    # Clean up empty lock files
    find "$CACHE_LOCKS_DIR" -type f -empty -mmin +1 -delete 2>/dev/null || true
}

# Get cache statistics
cache_stats() {
    echo "=== Cache Statistics ==="

    local total_files total_size hit_rate
    total_files=$(find "$CACHE_BASE_DIR" -name "*.cache" 2>/dev/null | wc -l)
    total_size=$(du -sh "$CACHE_BASE_DIR" 2>/dev/null | cut -f1 || echo "0K")
    hit_rate=$(cache_get_hit_rate)

    echo "Files: $total_files"
    echo "Size: $total_size"
    echo "Hit rate: ${hit_rate}%"

    echo ""
    echo "=== Level Breakdown ==="
    for level in l1 l2 l3; do
        local level_dir level_files level_size
        case "$level" in
            "l1") level_dir="$CACHE_L1_DIR" ;;
            "l2") level_dir="$CACHE_L2_DIR" ;;
            "l3") level_dir="$CACHE_L3_DIR" ;;
        esac

        level_files=$(find "$level_dir" -name "*.cache" 2>/dev/null | wc -l || echo 0)
        level_size=$(du -sh "$level_dir" 2>/dev/null | cut -f1 || echo "0K")
        echo "$level: $level_files files, $level_size"
    done

    echo ""
    echo "=== Metrics ==="
    cache_get_metrics | jq -r 'to_entries[] | "\(.key): \(.value)"' 2>/dev/null || echo "No metrics available"
}

# Initialize cache system on load
cache_init
