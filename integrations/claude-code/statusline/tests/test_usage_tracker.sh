#!/bin/bash
# Unit tests for lib/tracking/usage.sh and lib/tracking/session.sh

# Test framework setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$(cd "$SCRIPT_DIR/../lib" && pwd)"

# Isolated test data directories - must be set BEFORE sourcing the tracking
# modules, since they read these env vars once at source time.
TEST_CLAUDE_DIR="/tmp/claude_test_$$"
export TEST_USAGE_DIR="$TEST_CLAUDE_DIR"
export TEST_USAGE_DB="$TEST_CLAUDE_DIR/usage_tracking.json"
export SESSION_CACHE_FILE="$TEST_CLAUDE_DIR/session_start_cache_$$"

# Shared assert helpers (assert_equals, assert_not_empty, assert_matches, print_results, ...)
source "$SCRIPT_DIR/lib/assert.sh"

# Source the modules under test
source "$LIB_DIR/tracking/usage.sh"
source "$LIB_DIR/tracking/session.sh"

# Isolated PWD for session-tracking tests: get_session_file/get_window_start_file
# key off hash_string "$PWD", so a unique directory keeps them from colliding
# with any other concurrent test run or the real session state.
SESSION_TEST_DIR="/tmp/statusline_session_test_$$"

cleanup_all() {
    rm -rf "$TEST_CLAUDE_DIR" "$SESSION_TEST_DIR" 2>/dev/null || true
}
trap cleanup_all EXIT

# Setup and teardown for usage.sh tests
setup_test_env() {
    mkdir -p "$TEST_CLAUDE_DIR"
}

cleanup_test_env() {
    rm -rf "$TEST_CLAUDE_DIR" 2>/dev/null || true
}

# =============================================================================
# Group 1: usage.sh - setup and daily usage tracking
# =============================================================================
test_setup_usage_tracking() {
    echo "Testing setup_usage_tracking function..."

    setup_usage_tracking

    assert_file_exists "$TEST_CLAUDE_DIR" "Claude directory created"
    assert_file_exists "$TEST_USAGE_DB" "Usage database file created"

    local daily_usage
    daily_usage=$(jq -r '.daily_usage' "$TEST_USAGE_DB" 2>/dev/null)
    assert_equals "{}" "$daily_usage" "Initial daily_usage is empty object"

    local window_start
    window_start=$(jq -r '.window_start' "$TEST_USAGE_DB" 2>/dev/null)
    assert_equals '' "$window_start" "Initial window_start is empty string"
}

test_daily_usage_tracking() {
    echo "Testing daily usage tracking functions..."

    setup_usage_tracking

    local result
    result=$(get_daily_usage)
    assert_equals "0" "$result" "Initial daily usage is 0"

    update_daily_usage "1.50"
    result=$(get_daily_usage)
    assert_equals "1.5" "$result" "Daily usage updated to 1.5"

    update_daily_usage "2.25"
    result=$(get_daily_usage)
    assert_equals "3.75" "$result" "Daily usage accumulated to 3.75"

    update_daily_usage "0"
    result=$(get_daily_usage)
    assert_equals "3.75" "$result" "Zero cost does not change daily usage"

    update_daily_usage ""
    result=$(get_daily_usage)
    assert_equals "3.75" "$result" "Empty cost does not change daily usage"
}

# =============================================================================
# Group 2: usage.sh - window tracking
# =============================================================================
test_window_tracking() {
    echo "Testing window tracking functions..."

    setup_usage_tracking
    update_window_tracking

    local window_start
    window_start=$(get_tracked_window_start)
    assert_not_empty "$window_start" "Window start timestamp set"

    # Subsequent calls update the timestamp again (usage.sh always overwrites -
    # unlike the old session-level window file, there is no 5h guard here)
    update_window_tracking
    local second_window_start
    second_window_start=$(get_tracked_window_start)
    assert_not_empty "$second_window_start" "Window start still set after second update"
}

# =============================================================================
# Group 3: usage.sh - cleanup and edge cases
# =============================================================================
test_cleanup_old_data() {
    echo "Testing cleanup_old_data function..."

    setup_usage_tracking

    local current_date
    current_date=$(get_current_date)

    jq --arg current "$current_date" '
        .daily_usage = {
            ($current): 5.0,
            "2023-01-01": 2.0,
            "2023-01-02": 3.0
        }
    ' "$TEST_USAGE_DB" > "$TEST_USAGE_DB.tmp" && mv "$TEST_USAGE_DB.tmp" "$TEST_USAGE_DB"

    cleanup_old_data

    local current_usage
    current_usage=$(jq -r --arg current "$current_date" '.daily_usage[$current] // 0' "$TEST_USAGE_DB" 2>/dev/null)
    assert_equals "5.0" "$current_usage" "Current date usage preserved after cleanup"

    local old_usage
    old_usage=$(jq -r '.daily_usage["2023-01-01"] // "null"' "$TEST_USAGE_DB" 2>/dev/null)
    assert_equals "null" "$old_usage" "Old usage data cleaned up"
}

test_reset_usage_tracking() {
    echo "Testing reset_usage_tracking function..."

    setup_usage_tracking
    update_daily_usage "9.99"

    local result
    result=$(get_daily_usage)
    assert_equals "9.99" "$result" "Usage recorded before reset"

    reset_usage_tracking
    result=$(get_daily_usage)
    assert_equals "0" "$result" "Usage tracking database reset to 0"
}

test_edge_cases() {
    echo "Testing edge cases..."

    # Corrupted JSON file
    mkdir -p "$TEST_CLAUDE_DIR"
    echo "invalid json" > "$TEST_USAGE_DB"

    local result
    result=$(get_daily_usage)
    assert_equals "0" "$result" "get_daily_usage handles corrupted JSON"

    # Missing file
    rm -f "$TEST_USAGE_DB"
    result=$(get_daily_usage)
    assert_equals "0" "$result" "get_daily_usage handles missing file"
}

# =============================================================================
# Group 4: session.sh - session id, start, and duration
# =============================================================================
test_get_current_session_id() {
    echo "Testing get_current_session_id function..."

    local result
    result=$(get_current_session_id '{"conversation_uuid":"uuid-1"}')
    assert_equals "uuid-1" "$result" "get_current_session_id extracts conversation_uuid"

    result=$(get_current_session_id '{"session_id":"abc123"}')
    assert_equals "abc123" "$result" "get_current_session_id falls back to session_id"

    result=$(get_current_session_id '{"other":"field"}')
    assert_equals "" "$result" "get_current_session_id returns empty when no id field present"
}

test_session_start_and_duration() {
    echo "Testing get_session_start and get_session_duration..."

    local original_dir
    original_dir=$(pwd)
    mkdir -p "$SESSION_TEST_DIR"
    cd "$SESSION_TEST_DIR" || return 1
    clear_session_tracking

    # No usage yet - no session file created, start is "0"
    local result
    result=$(get_session_start "0" "0" "")
    assert_equals "0" "$result" "get_session_start returns 0 with no tokens and no prior session"

    result=$(get_session_duration "0" "0" "")
    assert_equals "0" "$result" "get_session_duration returns 0 with no session started"

    # Real usage starts a session
    result=$(get_session_start "100" "50" "")
    assert_not_empty "$result" "get_session_start returns a timestamp once usage is seen"
    assert_matches "$result" "^[0-9]+$" "get_session_start returns a numeric epoch"

    result=$(get_session_duration "100" "50" "")
    assert_matches "$result" "^([0-9]+m|[0-9]+h[0-9]*m?)$" "get_session_duration returns a formatted duration once started"

    clear_session_tracking
    cd "$original_dir" || true
}

test_session_id_change_resets_session() {
    echo "Testing session start resets when session id changes..."

    local original_dir
    original_dir=$(pwd)
    mkdir -p "$SESSION_TEST_DIR"
    cd "$SESSION_TEST_DIR" || return 1
    clear_session_tracking

    local first_start
    first_start=$(get_session_start "10" "5" '{"session_id":"session-a"}')
    assert_not_empty "$first_start" "First session start recorded"

    # New session id with real usage should start tracking anew
    local second_start
    second_start=$(get_session_start "20" "10" '{"session_id":"session-b"}')
    assert_not_empty "$second_start" "New session id starts a new session"

    clear_session_tracking
    cd "$original_dir" || true
}

# =============================================================================
# Run all tests
# =============================================================================
main() {
    echo "Running Usage/Session Tracker Module Tests..."
    echo

    setup_test_env
    test_setup_usage_tracking
    cleanup_test_env
    setup_test_env

    test_daily_usage_tracking
    cleanup_test_env
    setup_test_env

    test_window_tracking
    cleanup_test_env
    setup_test_env

    test_cleanup_old_data
    cleanup_test_env
    setup_test_env

    test_reset_usage_tracking
    cleanup_test_env
    setup_test_env

    test_edge_cases
    cleanup_test_env

    test_get_current_session_id
    test_session_start_and_duration
    test_session_id_change_resets_session

    print_results "Usage Tracker Tests"
}

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
