#!/usr/bin/env bash
# =============================================================================
# OAuth Fetcher - Isolated OAuth update script with error handling
# =============================================================================
# Standalone script for fetching OAuth usage data with:
# - File locking during cache writes to prevent race conditions
# - Comprehensive error logging for all failure types
# - Timeout protection and graceful degradation
# - Proper exit codes for automation

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source dependencies
source "$SCRIPT_DIR/api/oauth.sh"

# Logging and locking configuration
LOG_DIR="/tmp/statusline_live_cache"
LOG_FILE="$LOG_DIR/oauth_errors.log"
CACHE_LOCK_FILE="$LOG_DIR/oauth_cache.lock"
CACHE_LOCK_FD=201  # Use different FD than daemon lock (200)
BACKOFF_FILE="$LOG_DIR/oauth_backoff"
BACKOFF_COUNT_FILE="$LOG_DIR/oauth_backoff_count"

# Ensure log directory exists
mkdir -p "$LOG_DIR" 2>/dev/null || true

# =============================================================================
# Logging Functions
# =============================================================================

# Log with timestamp
# Usage: log_oauth_error "message"
log_oauth_error() {
    local message="$1"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $message" >> "$LOG_FILE" 2>/dev/null || true
}

# Log success message
log_oauth_success() {
    local message="$1"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] SUCCESS: $message" >> "$LOG_FILE" 2>/dev/null || true
}

# =============================================================================
# File Locking Functions
# =============================================================================

# Acquire exclusive lock on cache file (blocking with timeout)
# Returns: 0 if lock acquired, 1 if timeout
acquire_cache_lock() {
    local timeout="${1:-10}"  # Default 10 second timeout

    # Ensure lock file exists
    touch "$CACHE_LOCK_FILE" 2>/dev/null || true

    if command -v flock >/dev/null 2>&1; then
        # Use flock with timeout
        eval "exec ${CACHE_LOCK_FD}>\"$CACHE_LOCK_FILE\""
        if ! flock -w "$timeout" "$CACHE_LOCK_FD"; then
            log_oauth_error "Failed to acquire cache lock after ${timeout}s timeout"
            eval "exec ${CACHE_LOCK_FD}>&-" 2>/dev/null || true
            return 1
        fi
        return 0
    else
        # Fallback for systems without flock (like macOS without util-linux)
        # Use a simple PID-based lock with timeout
        local elapsed=0
        while [[ -f "$CACHE_LOCK_FILE.pid" ]] && [[ $elapsed -lt $timeout ]]; do
            local lock_pid
            lock_pid=$(cat "$CACHE_LOCK_FILE.pid" 2>/dev/null || echo "")
            if [[ -n "$lock_pid" ]] && kill -0 "$lock_pid" 2>/dev/null; then
                sleep 0.1
                elapsed=$((elapsed + 1))
            else
                # Stale lock, remove it
                rm -f "$CACHE_LOCK_FILE.pid" 2>/dev/null || true
                break
            fi
        done

        if [[ -f "$CACHE_LOCK_FILE.pid" ]]; then
            log_oauth_error "Failed to acquire cache lock after ${timeout}s timeout (fallback method)"
            return 1
        fi

        # Create lock
        echo $$ > "$CACHE_LOCK_FILE.pid"
        return 0
    fi
}

# Release cache lock
release_cache_lock() {
    if command -v flock >/dev/null 2>&1; then
        flock -u "$CACHE_LOCK_FD" 2>/dev/null || true
        eval "exec ${CACHE_LOCK_FD}>&-" 2>/dev/null || true
    else
        rm -f "$CACHE_LOCK_FILE.pid" 2>/dev/null || true
    fi
}

# =============================================================================
# Rate-Limit Backoff Functions
# =============================================================================

# Check if we are currently in a backoff period
# Returns: 0 if in backoff (should skip fetch), 1 if ok to fetch
check_backoff() {
    [[ -f "$BACKOFF_FILE" ]] || return 1

    local backoff_mtime current_time elapsed backoff_duration failure_count
    backoff_mtime=$(stat -c %Y "$BACKOFF_FILE" 2>/dev/null || stat -f %m "$BACKOFF_FILE" 2>/dev/null || echo 0)
    current_time=$(date +%s)
    elapsed=$((current_time - backoff_mtime))

    failure_count=$(cat "$BACKOFF_COUNT_FILE" 2>/dev/null || echo 1)

    # Backoff schedule: 1st=120s, 2nd=300s, 3rd+=600s
    if [[ "$failure_count" -le 1 ]]; then
        backoff_duration=120
    elif [[ "$failure_count" -eq 2 ]]; then
        backoff_duration=300
    else
        backoff_duration=600
    fi

    if [[ "$elapsed" -lt "$backoff_duration" ]]; then
        log_oauth_error "Rate-limit backoff active (failure #${failure_count}, ${elapsed}/${backoff_duration}s elapsed) — skipping fetch"
        return 0
    fi

    return 1
}

# Record a rate-limit failure and set backoff
set_backoff() {
    local failure_count
    failure_count=$(cat "$BACKOFF_COUNT_FILE" 2>/dev/null || echo 0)
    failure_count=$((failure_count + 1))
    echo "$failure_count" > "$BACKOFF_COUNT_FILE"
    touch "$BACKOFF_FILE"
    log_oauth_error "Rate limit detected — entering backoff (failure #${failure_count})"
}

# Clear backoff state on success
clear_backoff() {
    rm -f "$BACKOFF_FILE" "$BACKOFF_COUNT_FILE" 2>/dev/null || true
}

# =============================================================================
# OAuth Fetch with Error Handling
# =============================================================================

# Fetch OAuth data with comprehensive error logging
# Returns: 0 on success, 1 on failure
fetch_oauth_with_logging() {
    local start_time
    start_time=$(date +%s)

    # Check rate-limit backoff before doing anything
    if check_backoff; then
        return 1
    fi

    # Respect cache TTL — skip fetch if cache is still fresh
    if [[ -f "$OAUTH_USAGE_CACHE_FILE" ]]; then
        local cache_mtime cache_age
        cache_mtime=$(stat -c %Y "$OAUTH_USAGE_CACHE_FILE" 2>/dev/null || stat -f %m "$OAUTH_USAGE_CACHE_FILE" 2>/dev/null || echo 0)
        cache_age=$(( start_time - cache_mtime ))
        if [[ "$cache_age" -lt "${OAUTH_USAGE_CACHE_TTL:-300}" ]]; then
            return 0  # Cache still fresh, skip network call
        fi
    fi

    # Check for OAuth credentials
    local creds
    creds=$(get_oauth_credentials 2>/dev/null) || true

    if [[ -z "$creds" ]]; then
        log_oauth_error "OAuth credentials not found - user not logged in?"
        return 1
    fi

    # Extract access token
    local token
    token=$(get_oauth_token "$creds" 2>/dev/null) || true

    if [[ -z "$token" ]]; then
        log_oauth_error "Failed to extract OAuth token from credentials"
        return 1
    fi

    # Call the OAuth API with timeout protection
    local response curl_exit_code
    response=$(curl -s --max-time 5 "$ANTHROPIC_OAUTH_USAGE_URL" \
        -H "Accept: application/json, text/plain, */*" \
        -H "Content-Type: application/json" \
        -H "User-Agent: claude-code/2.0.67" \
        -H "Authorization: Bearer $token" \
        -H "anthropic-beta: oauth-2025-04-20" 2>/dev/null) || curl_exit_code=$?

    # Check for network timeout (curl exit code 28)
    if [[ ${curl_exit_code:-0} -eq 28 ]]; then
        log_oauth_error "OAuth API request timed out after 5s"
        return 1
    elif [[ ${curl_exit_code:-0} -ne 0 ]]; then
        log_oauth_error "OAuth API request failed with curl exit code: ${curl_exit_code}"
        return 1
    fi

    # Validate response JSON
    if [[ -z "$response" ]]; then
        log_oauth_error "OAuth API returned empty response"
        return 1
    fi

    # Check for rate-limit response before validating structure
    if echo "$response" | grep -q '"rate_limit_error"' 2>/dev/null; then
        set_backoff
        return 1
    fi

    # Check if response contains expected data structure
    if ! echo "$response" | jq -e '.five_hour' >/dev/null 2>&1; then
        log_oauth_error "OAuth API returned invalid JSON (missing .five_hour field)"
        # Log first 200 chars of response for debugging
        local response_preview="${response:0:200}"
        log_oauth_error "Response preview: $response_preview"
        return 1
    fi

    # Acquire lock before writing to cache
    if ! acquire_cache_lock 10; then
        log_oauth_error "Failed to acquire lock for cache write"
        return 1
    fi

    # Write to cache (atomic operation)
    local cache_write_success=0
    if echo "$response" > "$OAUTH_USAGE_CACHE_FILE.tmp" 2>/dev/null; then
        if mv "$OAUTH_USAGE_CACHE_FILE.tmp" "$OAUTH_USAGE_CACHE_FILE" 2>/dev/null; then
            cache_write_success=1
        else
            log_oauth_error "Failed to move temporary cache file to final location"
            rm -f "$OAUTH_USAGE_CACHE_FILE.tmp" 2>/dev/null || true
        fi
    else
        log_oauth_error "Failed to write OAuth response to temporary cache file"
    fi

    # Release lock
    release_cache_lock

    if [[ $cache_write_success -eq 0 ]]; then
        return 1
    fi

    # Calculate elapsed time
    local end_time elapsed
    end_time=$(date +%s)
    elapsed=$((end_time - start_time))

    # Clear any active backoff on success
    clear_backoff

    # Log success with timing
    log_oauth_success "OAuth cache updated successfully (took ${elapsed}s)"
    return 0
}

# =============================================================================
# Main Entry Point
# =============================================================================

main() {
    # Trap errors to ensure lock is always released
    trap 'release_cache_lock' EXIT ERR

    # Fetch OAuth data with error logging
    if fetch_oauth_with_logging; then
        exit 0
    else
        exit 1
    fi
}

# Run main if executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
