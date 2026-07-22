#!/bin/bash
# daemon_lock.sh - Reusable flock-based locking library for statusline daemon
#
# Provides singleton lock acquisition using flock for daemon processes.
# Ensures only one daemon instance runs at a time.

# Prevent multiple sourcing
if [[ -n "${DAEMON_LOCK_LOADED:-}" ]]; then
    return 0
fi
readonly DAEMON_LOCK_LOADED=1

# Lock file location
readonly DAEMON_LOCK_FILE="/tmp/statusline_live_cache/daemon.lock"

# Acquire exclusive daemon lock (non-blocking)
# Returns: 0 if lock acquired, 1 if already locked
acquire_daemon_lock() {
    # Ensure lock directory exists
    mkdir -p "$(dirname "$DAEMON_LOCK_FILE")"

    # Check if flock is available
    if command -v flock >/dev/null 2>&1; then
        # Use file descriptor 200 for locking
        exec 200>"$DAEMON_LOCK_FILE"
        if ! flock -n 200; then
            # Lock failed, someone else holds it
            exec 200>&-
            return 1
        fi
        # Lock acquired successfully
        return 0
    else
        # Fallback for systems without flock (like macOS)
        # Use PID-based lock file
        if [[ -f "$DAEMON_LOCK_FILE" ]]; then
            # Check if the PID in the lock file is still running
            local lock_pid
            lock_pid=$(cat "$DAEMON_LOCK_FILE" 2>/dev/null)
            if [[ -n "$lock_pid" ]] && kill -0 "$lock_pid" 2>/dev/null; then
                # Lock is held by a running process
                return 1
            fi
            # Stale lock file, remove it
            rm -f "$DAEMON_LOCK_FILE" 2>/dev/null || true
        fi

        # Create lock file with current PID
        echo $$ > "$DAEMON_LOCK_FILE"
        return 0
    fi
}

# Release daemon lock
# Returns: 0 on success
release_daemon_lock() {
    if command -v flock >/dev/null 2>&1; then
        # Release flock and close file descriptor
        flock -u 200 2>/dev/null || true
        exec 200>&- 2>/dev/null || true
    fi

    # Remove lock file
    rm -f "$DAEMON_LOCK_FILE" 2>/dev/null || true
    return 0
}

# Check if daemon is locked (someone else holds it)
# Returns: 0 if locked, 1 if available
is_daemon_locked() {
    if command -v flock >/dev/null 2>&1; then
        # Try to acquire lock non-blocking on a different FD to check
        exec 201>"$DAEMON_LOCK_FILE"
        if flock -n 201 2>/dev/null; then
            # Lock was available, release it
            flock -u 201 2>/dev/null || true
            exec 201>&- 2>/dev/null || true
            return 1
        else
            # Lock is held
            exec 201>&- 2>/dev/null || true
            return 0
        fi
    else
        # Fallback for systems without flock
        if [[ ! -f "$DAEMON_LOCK_FILE" ]]; then
            return 1
        fi

        # Check if the PID in the lock file is still running
        local lock_pid
        lock_pid=$(cat "$DAEMON_LOCK_FILE" 2>/dev/null)
        if [[ -n "$lock_pid" ]] && kill -0 "$lock_pid" 2>/dev/null; then
            # Lock is held by a running process
            return 0
        fi

        # Stale lock file
        return 1
    fi
}
