#!/bin/bash
# =============================================================================
# Platform Utilities - Cross-platform helpers for macOS and Linux
# =============================================================================
# Provides consistent interfaces for system operations that differ between
# macOS (BSD) and Linux (GNU) implementations.

# Guard clause - prevent multiple sourcing
if [[ -n "${STATUSLINE_PLATFORM_LOADED:-}" ]]; then
    return 0
fi
readonly STATUSLINE_PLATFORM_LOADED=1

# =============================================================================
# Platform Detection
# =============================================================================

# Detect current platform
# Returns: "darwin" for macOS, "linux" for Linux, or uname output
get_platform() {
    uname -s | tr '[:upper:]' '[:lower:]'
}

# Check if running on macOS
is_macos() {
    [[ "$(get_platform)" == "darwin" ]]
}

# Check if running on Linux
is_linux() {
    [[ "$(get_platform)" == "linux" ]]
}

# =============================================================================
# File System Operations
# =============================================================================

# Get file modification time (epoch seconds) - cross-platform
# Usage: get_file_mtime "/path/to/file"
# Returns: epoch seconds or "0" if file doesn't exist
get_file_mtime() {
    local file="$1"
    # macOS: stat -f %m
    # Linux: stat -c %Y
    stat -f %m "$file" 2>/dev/null || stat -c %Y "$file" 2>/dev/null || echo "0"
}

# =============================================================================
# Date/Time Operations
# =============================================================================

# Parse ISO 8601 timestamp to epoch - cross-platform
# Usage: parse_iso_timestamp "2025-01-01T12:00:00.123Z"
# Returns: epoch seconds or "0" if parsing fails
parse_iso_timestamp() {
    local ts="$1"

    # Remove milliseconds and Z suffix: "2025-01-01T12:00:00.123Z" -> "2025-01-01T12:00:00"
    local clean_ts="${ts%.*}"
    clean_ts="${clean_ts%Z}"
    # Also remove timezone offset if present
    clean_ts="${clean_ts%+*}"

    # macOS: date -j -f format
    # Linux: date -d string
    TZ=UTC date -j -f "%Y-%m-%dT%H:%M:%S" "$clean_ts" +%s 2>/dev/null || \
    TZ=UTC date -d "$clean_ts" +%s 2>/dev/null || \
    echo "0"
}

# Floor epoch timestamp to hour boundary
# Usage: floor_epoch_to_hour 1704110400
# Returns: epoch seconds floored to the previous hour
floor_epoch_to_hour() {
    local epoch="$1"
    # Pure arithmetic: floor to hour (3600 seconds)
    echo $(( (epoch / 3600) * 3600 ))
}

# Convert epoch to formatted date string - cross-platform
# Usage: epoch_to_time_display 1704110400 "+%H:%M"
# Returns: formatted time string or "??:??" if conversion fails
epoch_to_time_display() {
    local epoch="$1"
    local format="${2:-+%H:%M}"

    # macOS: date -r epoch
    # Linux: date -d @epoch
    date -r "$epoch" "$format" 2>/dev/null || \
    date -d "@$epoch" "$format" 2>/dev/null || \
    echo "??:??"
}

# Get current timestamp in epoch seconds
get_current_epoch() {
    date +%s
}

# Get current timestamp in nanoseconds (for performance timing)
# Returns: nanoseconds or seconds*10^9 if nanoseconds not supported
get_current_nanos() {
    date +%s%N 2>/dev/null || echo "$(date +%s)000000000"
}

# Get current date in YYYY-MM-DD format
get_current_date() {
    date +%Y-%m-%d
}

# =============================================================================
# Hash Operations
# =============================================================================

# Generate MD5 hash of a string - cross-platform
# Usage: hash_string "some string"
# Returns: MD5 hash
hash_string() {
    local str="$1"
    # macOS: md5 -q
    # Linux: md5sum | cut
    echo "$str" | md5 -q 2>/dev/null || echo "$str" | md5sum 2>/dev/null | cut -d' ' -f1 || echo "default"
}
