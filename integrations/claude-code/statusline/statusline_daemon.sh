#!/bin/bash
# Statusline Live Cache Daemon - Rewritten with flock singleton
#
# Design Principles:
# - Single Responsibility: Each function does one thing well
# - Performance: Minimal subshells, efficient data collection
# - Resource Conscious: 60s update interval to preserve battery
# - Fail-Safe: Graceful degradation if components fail
# - DRY: Reusable collection functions
# - Process Safety: flock-based singleton, signal handling, job tracking
#
# Architecture:
# - Daemon maintains a single JSON cache file
# - Statusline reads cache (fast) with fallback to direct calculation
# - Updates run every 60 seconds to balance freshness and efficiency
# - OAuth updates run in background jobs to prevent blocking

set -euo pipefail

# ============================================================================
# SCRIPT LOCATION AND DEPENDENCIES
# ============================================================================

SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"

# Source daemon utilities
source "$SCRIPT_DIR/lib/daemon_lock.sh"
source "$SCRIPT_DIR/lib/signal_handler.sh"

# ============================================================================
# CONFIGURATION
# ============================================================================

readonly UPDATE_INTERVAL=60  # Update every 60 seconds (battery-friendly)
readonly CACHE_DIR="/tmp/statusline_live_cache"
readonly CACHE_FILE="$CACHE_DIR/live_data.json"
readonly CACHE_FILE_TMP="${CACHE_FILE}.tmp"
readonly PID_FILE="$CACHE_DIR/daemon.pid"
readonly LOG_FILE="$CACHE_DIR/daemon.log"

# ============================================================================
# INITIALIZATION
# ============================================================================

# Ensure cache directory exists (fail silently if we can't create it)
mkdir -p "$CACHE_DIR" 2>/dev/null || true

# ============================================================================
# UTILITY FUNCTIONS (Single Responsibility)
# ============================================================================

# Logs a timestamped message to the log file
# Args: $@ - Message to log
log_message() {
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >> "$LOG_FILE" 2>/dev/null || true
}

# Checks if the daemon process is currently running
# Returns: 0 if running, 1 if not
# NOTE: This is now a wrapper around daemon lock status check
is_running() {
    # Check if daemon lock is held
    is_daemon_locked
}

# ============================================================================
# DATA COLLECTION FUNCTIONS (Interface Segregation)
# ============================================================================

# Collects git repository information
# Returns: JSON string with git status or error state
# Performance: Single git command, minimal subshells
get_git_data() {
    # Fast check: are we in a git repo?
    git rev-parse --git-dir >/dev/null 2>&1 || {
        printf '{"in_repo":false}'
        return 0
    }

    # Collect data efficiently (parallel execution where possible)
    local branch changes worktree
    branch=$(git symbolic-ref --short HEAD 2>/dev/null || git rev-parse --short HEAD 2>/dev/null || printf "detached")
    changes=$(git status --porcelain=v1 -u 2>/dev/null | wc -l | tr -d ' ')

    # Detect worktree: compare git-dir with git-common-dir
    # In a worktree, git-dir points to .git/worktrees/<name>, common-dir points to .git
    worktree=""
    local git_dir git_common_dir
    git_dir=$(git rev-parse --git-dir 2>/dev/null)
    git_common_dir=$(git rev-parse --git-common-dir 2>/dev/null)

    if [[ -n "$git_dir" && -n "$git_common_dir" && "$git_dir" != "$git_common_dir" ]]; then
        # We're in a worktree - extract name from git-dir path
        # git-dir is typically: /path/to/repo/.git/worktrees/<worktree-name>
        if [[ "$git_dir" == *"/worktrees/"* ]]; then
            worktree="${git_dir##*/worktrees/}"
            # Remove any trailing slashes or paths
            worktree="${worktree%%/*}"
        fi
    fi

    # Output as JSON (using printf for efficiency)
    if [[ -n "$worktree" ]]; then
        printf '{"in_repo":true,"branch":"%s","changes":%d,"worktree":"%s"}' "$branch" "${changes:-0}" "$worktree"
    else
        printf '{"in_repo":true,"branch":"%s","changes":%d}' "$branch" "${changes:-0}"
    fi
}

# Collects current directory information
# Returns: JSON string with directory paths
# Performance: Pure bash string operations, no subshells
get_directory_data() {
    local dir="$PWD"
    local short_dir="$dir"

    # Replace home with ~ (efficient string substitution)
    [[ "$dir" == "$HOME"* ]] && short_dir="~${dir#"$HOME"}"

    # Truncate if too long (efficient length check)
    [[ ${#short_dir} -gt 30 ]] && short_dir=".../${dir##*/}"

    printf '{"current_dir":"%s","full_path":"%s"}' "$short_dir" "$dir"
}

# ============================================================================
# CACHE MANAGEMENT (Open/Closed Principle - easy to extend)
# ============================================================================

# Update OAuth cache in background (non-blocking)
# Spawns oauth_fetcher.sh as a background job
update_oauth_cache_background() {
    # Check if oauth_fetcher script exists
    if [[ ! -x "$SCRIPT_DIR/lib/oauth_fetcher.sh" ]]; then
        return 0
    fi

    # Launch oauth_fetcher in background and track the job
    "$SCRIPT_DIR/lib/oauth_fetcher.sh" &
    track_job $!
}

# Updates the cache file with fresh data
# Performance: Atomic write using temp file, single write operation
# Reliability: Graceful degradation if any component fails
update_cache() {
    local -r timestamp=$(date +%s)

    # Collect all data (fail-safe: use defaults if collection fails)
    local git_data dir_data oauth_data
    git_data=$(get_git_data 2>/dev/null || printf '{"in_repo":false}')
    dir_data=$(get_directory_data 2>/dev/null || printf '{"current_dir":"~"}')

    # Collect OAuth data in background (non-blocking for this daemon)
    # This updates the OAuth cache file separately, which statusline reads
    update_oauth_cache_background 2>/dev/null || true

    # Assemble JSON in a single operation (no heredoc for performance)
    printf '{"timestamp":%d,"git":%s,"directory":%s}\n' \
        "$timestamp" "$git_data" "$dir_data" > "$CACHE_FILE_TMP" 2>/dev/null || return 1

    # Atomic move (ensures readers never see partial data)
    mv "$CACHE_FILE_TMP" "$CACHE_FILE" 2>/dev/null
}

# ============================================================================
# DAEMON CONTROL (Dependency Inversion - control flow separated from logic)
# ============================================================================

# Internal function to start daemon loop (for auto-start)
# This function never returns - it runs the daemon loop
# NOTE: Lock should already be acquired by caller (daemon_start or daemon_autostart)
_daemon_loop() {
    # Mark this process as the daemon (prevents parent cleanup)
    export IS_DAEMON_PROCESS=1

    # Write PID file
    printf "%d" $$ > "$PID_FILE" 2>/dev/null || {
        printf "[ERROR] Failed to write PID file\n" >> "$LOG_FILE"
        exit 1
    }
    log_message "Daemon started with PID $$"

    # Setup signal handlers for graceful shutdown
    setup_signal_handlers

    # Initial cache update
    update_cache || log_message "WARNING: Initial cache update failed"

    # Main event loop
    while true; do
        sleep "$UPDATE_INTERVAL"
        update_cache || log_message "ERROR: Cache update failed"
    done

    # This line should never be reached
    log_message "ERROR: Daemon loop exited unexpectedly!"
}

# Starts the daemon background process
# Returns: 0 on success, 1 if already running
daemon_start() {
    # Acquire lock FIRST to prevent race conditions
    if ! acquire_daemon_lock; then
        printf "Statusline daemon already running\n"
        return 1
    fi

    printf "Starting statusline daemon...\n"

    # Run daemon in a new session using setsid (or nohup as fallback)
    # This properly detaches it from the controlling terminal
    if command -v setsid >/dev/null 2>&1; then
        setsid "$0" _daemon_loop_wrapper </dev/null >/dev/null 2>&1 &
    else
        nohup "$0" _daemon_loop_wrapper </dev/null >/dev/null 2>&1 &
    fi

    sleep 0.5  # Give daemon time to initialize
    printf "Statusline daemon started\n"
    printf "Live data refreshing every %ds\n" "$UPDATE_INTERVAL"
}

# Silent start for auto-start (no output, fork-safe, non-blocking)
daemon_autostart() {
    # Acquire lock - if already running, silently exit
    acquire_daemon_lock || return 0

    # Run daemon in a new session
    if command -v setsid >/dev/null 2>&1; then
        setsid "$0" _daemon_loop_wrapper </dev/null >/dev/null 2>&1 &
    else
        nohup "$0" _daemon_loop_wrapper </dev/null >/dev/null 2>&1 &
    fi
}

# Stops the daemon background process
# Returns: 0 on success
daemon_stop() {
    if ! [[ -f "$PID_FILE" ]]; then
        printf "Statusline daemon is not running\n"
        return 0
    fi

    local pid
    pid=$(cat "$PID_FILE" 2>/dev/null)

    if [[ -n "$pid" ]]; then
        printf "Stopping statusline daemon (PID: %s)...\n" "$pid"
        log_message "Stopping daemon PID $pid"

        # Send SIGTERM - signal handler will cleanup
        kill -TERM "$pid" 2>/dev/null || log_message "WARNING: Failed to send SIGTERM to PID $pid"

        # Wait for daemon to exit (up to 3 seconds)
        local waited=0
        while [[ $waited -lt 30 ]] && kill -0 "$pid" 2>/dev/null; do
            sleep 0.1
            waited=$((waited + 1))
        done

        # Force kill if still running
        if kill -0 "$pid" 2>/dev/null; then
            log_message "WARNING: Daemon did not exit gracefully, forcing SIGKILL"
            kill -KILL "$pid" 2>/dev/null || true
        fi

        printf "Statusline daemon stopped\n"
    fi
}

# Displays daemon status information
# Returns: 0 if running, 1 if not
daemon_status() {
    if ! is_running; then
        printf "Statusline daemon is not running\n"
        return 1
    fi

    local -r pid=$(cat "$PID_FILE")
    printf "Statusline daemon is running (PID: %s)\n" "$pid"
    printf "Update interval: %ds\n" "$UPDATE_INTERVAL"
    printf "Cache file: %s\n" "$CACHE_FILE"

    if [[ -f "$CACHE_FILE" ]] && command -v jq >/dev/null 2>&1; then
        local last_update current_time age
        last_update=$(jq -r '.timestamp // 0' "$CACHE_FILE" 2>/dev/null)
        current_time=$(date +%s)
        age=$((current_time - last_update))

        printf "Cache last updated: %ds ago\n" "$age"

        # Show cache contents
        printf "\nCurrent cache data:\n"
        jq . "$CACHE_FILE" 2>/dev/null || cat "$CACHE_FILE"
    fi
}

# ============================================================================
# COMMAND ROUTER (Liskov Substitution - consistent command interface)
# ============================================================================

# Main entry point - routes commands to appropriate handlers
main() {
    local -r command="${1:-start}"

    case "$command" in
        _daemon_loop_wrapper)
            # Internal command: run daemon loop (called by setsid/nohup)
            _daemon_loop
            ;;
        start)
            daemon_start
            ;;
        autostart)
            # Silent auto-start (called by statusline)
            daemon_autostart
            ;;
        stop)
            daemon_stop
            ;;
        restart)
            daemon_stop
            sleep 1
            daemon_start
            ;;
        status)
            daemon_status
            ;;
        update)
            # Manual cache update (useful for testing)
            if update_cache; then
                printf "Cache updated successfully\n"
            else
                printf "ERROR: Cache update failed\n" >&2
                return 1
            fi
            ;;
        *)
            printf "Usage: %s {start|stop|restart|status|update}\n" "$0" >&2
            printf "\nCommands:\n"
            printf "  start   - Start the background daemon (interactive)\n"
            printf "  autostart - Auto-start daemon (silent, fork-safe)\n"
            printf "  stop    - Stop the background daemon\n"
            printf "  restart - Restart the daemon\n"
            printf "  status  - Show daemon status and cache contents\n"
            printf "  update  - Manually update cache once\n"
            return 1
            ;;
    esac
}

# Execute main with all arguments (only if script is executed, not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
