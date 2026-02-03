#!/usr/bin/env bash
# signal_handler.sh - Signal handling and cleanup utilities for statusline daemon
#
# Provides robust signal handling, background job tracking, and resource cleanup
# for long-running daemon processes.
#
# Features:
# - Track background job PIDs for cleanup
# - Graceful shutdown on SIGTERM, SIGINT, EXIT
# - Resource cleanup (lock files, PID files, temp files)
# - Wait for jobs to finish before exiting

# Guard clause - prevent multiple sourcing
if [[ -n "${STATUSLINE_SIGNAL_HANDLER_LOADED:-}" ]]; then
    return 0
fi
readonly STATUSLINE_SIGNAL_HANDLER_LOADED=1

# ============================================================================
# DEPENDENCIES
# ============================================================================

# Source dependencies
SIGNAL_HANDLER_DIR="$(dirname "${BASH_SOURCE[0]}")"
if [[ -f "$SIGNAL_HANDLER_DIR/daemon_lock.sh" ]]; then
    source "$SIGNAL_HANDLER_DIR/daemon_lock.sh"
fi

# ============================================================================
# CONFIGURATION
# ============================================================================

# Default cache directory and files to clean up
# These can be overridden by the daemon script before sourcing this file
: "${CACHE_DIR:=/tmp/statusline_live_cache}"
: "${STATUSLINE_PID_FILE:=$CACHE_DIR/daemon.pid}"
: "${STATUSLINE_CACHE_FILE:=$CACHE_DIR/live_data.json}"
: "${STATUSLINE_CACHE_FILE_TMP:=${STATUSLINE_CACHE_FILE}.tmp}"
: "${STATUSLINE_LOG_FILE:=$CACHE_DIR/daemon.log}"

# ============================================================================
# JOB TRACKING
# ============================================================================

# Array to track background jobs
declare -a TRACKED_JOBS=()

# Flag to prevent duplicate cleanup
CLEANUP_DONE=0

# Add a background job PID to tracking array
# This allows us to clean up all background jobs on shutdown
#
# Args:
#   $1 - PID of background job to track
# Returns:
#   0 on success
#
# Usage:
#   some_command &
#   track_job $!
track_job() {
    local pid="$1"

    if [[ -z "$pid" ]]; then
        return 1
    fi

    # Add to tracking array
    TRACKED_JOBS+=("$pid")

    return 0
}

# ============================================================================
# JOB CLEANUP
# ============================================================================

# Kill all tracked background jobs and wait for them to complete
# This ensures graceful termination of all child processes
#
# Returns:
#   0 on success
cleanup_tracked_jobs() {
    local killed_count=0

    # Kill all tracked jobs with TERM signal first (graceful)
    for pid in "${TRACKED_JOBS[@]}"; do
        if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
            kill -TERM "$pid" 2>/dev/null || true
            ((killed_count++))
        fi
    done

    # Wait a short time for graceful shutdown
    if [[ $killed_count -gt 0 ]]; then
        sleep 0.5
    fi

    # Force kill any remaining jobs with KILL signal
    for pid in "${TRACKED_JOBS[@]}"; do
        if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
            kill -KILL "$pid" 2>/dev/null || true
        fi
    done

    # Wait for all tracked jobs to exit (reap zombie processes)
    for pid in "${TRACKED_JOBS[@]}"; do
        if [[ -n "$pid" ]]; then
            wait "$pid" 2>/dev/null || true
        fi
    done

    # Clear tracking array
    TRACKED_JOBS=()

    return 0
}

# ============================================================================
# RESOURCE CLEANUP
# ============================================================================

# Clean up all daemon resources (files, locks, jobs)
# This is the main cleanup function called by signal handlers
#
# Cleanup order:
#   1. Kill tracked background jobs
#   2. Find and kill untracked child processes
#   3. Release daemon lock
#   4. Remove PID file
#   5. Remove temporary cache files
#
# Returns:
#   0 on success
cleanup_handler() {
    # Only run cleanup in the daemon process, not parent
    if [[ "${IS_DAEMON_PROCESS:-0}" != "1" ]]; then
        return 0
    fi

    # Prevent multiple cleanup executions
    if [[ $CLEANUP_DONE -eq 1 ]]; then
        return 0
    fi
    CLEANUP_DONE=1

    # Log cleanup start (use external PID_FILE/LOG_FILE if set, otherwise use defaults)
    local log_file="${LOG_FILE:-$STATUSLINE_LOG_FILE}"
    if [[ -f "$log_file" ]]; then
        printf '[%s] Cleanup handler invoked - shutting down daemon\n' \
            "$(date '+%Y-%m-%d %H:%M:%S')" >> "$log_file" 2>/dev/null || true
    fi

    # 1. Kill all tracked background jobs
    cleanup_tracked_jobs

    # 2. Find and kill any remaining child processes using jobs -p
    # This catches background jobs that weren't explicitly tracked
    local child_pids
    child_pids=$(jobs -p 2>/dev/null || true)
    if [[ -n "$child_pids" ]]; then
        for pid in $child_pids; do
            if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
                kill -TERM "$pid" 2>/dev/null || true
            fi
        done

        # Wait briefly for graceful shutdown
        sleep 0.2

        # Force kill any remaining
        for pid in $child_pids; do
            if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
                kill -KILL "$pid" 2>/dev/null || true
            fi
        done
    fi

    # 3. Release daemon lock (if daemon_lock.sh was sourced)
    if command -v release_daemon_lock >/dev/null 2>&1; then
        release_daemon_lock
    fi

    # 4. Remove PID file (use external PID_FILE if set, otherwise use default)
    local pid_file="${PID_FILE:-$STATUSLINE_PID_FILE}"
    rm -f "$pid_file" 2>/dev/null || true

    # 5. Remove temporary cache files
    rm -f "$STATUSLINE_CACHE_FILE_TMP" 2>/dev/null || true

    # Log cleanup completion
    if [[ -f "$log_file" ]]; then
        printf '[%s] Cleanup completed - daemon shutdown complete\n' \
            "$(date '+%Y-%m-%d %H:%M:%S')" >> "$log_file" 2>/dev/null || true
    fi

    return 0
}

# ============================================================================
# SIGNAL HANDLERS
# ============================================================================

# Handle SIGTERM (graceful shutdown from systemd/kill command)
handle_sigterm() {
    local log_file="${LOG_FILE:-$STATUSLINE_LOG_FILE}"
    if [[ -f "$log_file" ]]; then
        printf '[%s] Received SIGTERM, shutting down gracefully\n' \
            "$(date '+%Y-%m-%d %H:%M:%S')" >> "$log_file" 2>/dev/null || true
    fi
    cleanup_handler
    exit 0
}

# Handle SIGINT (Ctrl+C)
handle_sigint() {
    local log_file="${LOG_FILE:-$STATUSLINE_LOG_FILE}"
    if [[ -f "$log_file" ]]; then
        printf '[%s] Received SIGINT, shutting down\n' \
            "$(date '+%Y-%m-%d %H:%M:%S')" >> "$log_file" 2>/dev/null || true
    fi
    cleanup_handler
    exit 0
}

# Set up signal handlers for graceful daemon shutdown
# Traps SIGTERM, SIGINT, and EXIT signals
#
# Signal handling:
#   SIGTERM - Clean shutdown from systemd/kill command
#   SIGINT  - Clean shutdown from Ctrl+C
#   EXIT    - Catch-all for any exit (includes errors)
#
# Returns:
#   0 on success
#
# Usage:
#   setup_signal_handlers
#   # daemon main loop here
setup_signal_handlers() {
    # Trap SIGTERM (systemd, kill command)
    trap 'handle_sigterm' TERM

    # Trap SIGINT (Ctrl+C)
    trap 'handle_sigint' INT

    # Trap EXIT (any exit, including errors)
    # This ensures cleanup even if the daemon crashes
    trap 'cleanup_handler' EXIT

    return 0
}

# ============================================================================
# GRACEFUL SHUTDOWN
# ============================================================================

# Gracefully shut down the daemon with timeout
# Attempts clean shutdown first, then forces termination
#
# Args:
#   $1 - Timeout in seconds (default: 5)
# Returns:
#   0 on success, 1 on timeout
#
# Usage:
#   graceful_shutdown 10  # 10 second timeout
graceful_shutdown() {
    local timeout="${1:-5}"
    local elapsed=0
    local log_file="${LOG_FILE:-$STATUSLINE_LOG_FILE}"

    # Log shutdown request
    if [[ -f "$log_file" ]]; then
        printf '[%s] Graceful shutdown requested (timeout: %ds)\n' \
            "$(date '+%Y-%m-%d %H:%M:%S')" "$timeout" >> "$log_file" 2>/dev/null || true
    fi

    # Send TERM signal to tracked jobs
    for pid in "${TRACKED_JOBS[@]}"; do
        if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
            kill -TERM "$pid" 2>/dev/null || true
        fi
    done

    # Wait for jobs to finish (with timeout)
    while [[ $elapsed -lt $timeout ]]; do
        local all_done=1

        for pid in "${TRACKED_JOBS[@]}"; do
            if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
                all_done=0
                break
            fi
        done

        if [[ $all_done -eq 1 ]]; then
            # All jobs finished
            return 0
        fi

        # Still running, wait a bit
        sleep 0.5
        ((elapsed++))
    done

    # Timeout - force kill remaining jobs
    if [[ -f "$log_file" ]]; then
        printf '[%s] Graceful shutdown timeout - forcing termination\n' \
            "$(date '+%Y-%m-%d %H:%M:%S')" >> "$log_file" 2>/dev/null || true
    fi

    for pid in "${TRACKED_JOBS[@]}"; do
        if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
            kill -KILL "$pid" 2>/dev/null || true
        fi
    done

    return 1
}

# ============================================================================
# HEALTH CHECK
# ============================================================================

# Check if all tracked jobs are still running
# Useful for monitoring daemon health
#
# Returns:
#   0 if all jobs running, 1 if any job died
#
# Usage:
#   if ! check_jobs_health; then
#       echo "Warning: some background jobs died"
#   fi
check_jobs_health() {
    local failed=0

    for pid in "${TRACKED_JOBS[@]}"; do
        if [[ -n "$pid" ]] && ! kill -0 "$pid" 2>/dev/null; then
            failed=1
        fi
    done

    return $failed
}
