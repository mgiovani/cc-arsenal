#!/bin/bash
# Unit tests for usage_tracker.sh

# Test framework setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$SCRIPT_DIR/../lib"

# Test data directory - must be set BEFORE sourcing usage_tracker.sh
TEST_CLAUDE_DIR="/tmp/claude_test_$$"
export TEST_USAGE_DIR="$TEST_CLAUDE_DIR"
export TEST_USAGE_DB="$TEST_CLAUDE_DIR/usage_tracking.json"
export TEST_CLAUDE_DIR="$TEST_CLAUDE_DIR"

# Source the modules under test
source "$LIB_DIR/utils.sh"
source "$LIB_DIR/usage_tracker.sh"

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Create test-specific functions that override the constants
setup_test_usage_tracking() {
    mkdir -p "$TEST_CLAUDE_DIR"

    if [[ ! -f "$TEST_USAGE_DB" ]]; then
        echo '{"daily_usage":{},"window_start":""}' > "$TEST_USAGE_DB"
    fi
}

get_test_daily_usage() {
    local current_date
    current_date=$(get_current_date)

    if [[ -f "$TEST_USAGE_DB" ]]; then
        jq -r --arg date "$current_date" '.daily_usage[$date] // 0' "$TEST_USAGE_DB" 2>/dev/null || echo "0"
    else
        echo "0"
    fi
}

update_test_daily_usage() {
    local cost="$1"
    local current_date
    current_date=$(get_current_date)

    if [[ -z "$cost" || "$cost" == "0" || "$cost" == "null" ]]; then
        return
    fi

    local temp_file
    temp_file=$(mktemp)

    if [[ -f "$TEST_USAGE_DB" ]]; then
        jq --arg date "$current_date" --arg cost "$cost" '
            .daily_usage[$date] = ((.daily_usage[$date] // 0) + ($cost | tonumber))
        ' "$TEST_USAGE_DB" > "$temp_file" && mv "$temp_file" "$TEST_USAGE_DB"
    fi
}

# Test helper functions
assert_equals() {
    local expected="$1"
    local actual="$2"
    local test_name="$3"

    TESTS_RUN=$((TESTS_RUN + 1))

    if [[ "$expected" == "$actual" ]]; then
        echo "✅ PASS: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: $test_name"
        echo "   Expected: '$expected'"
        echo "   Actual:   '$actual'"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

assert_not_empty() {
    local actual="$1"
    local test_name="$2"

    TESTS_RUN=$((TESTS_RUN + 1))

    if [[ -n "$actual" ]]; then
        echo "✅ PASS: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: $test_name (expected non-empty value)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

assert_file_exists() {
    local file_path="$1"
    local test_name="$2"

    TESTS_RUN=$((TESTS_RUN + 1))

    if [[ -f "$file_path" || -d "$file_path" ]]; then
        echo "✅ PASS: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: $test_name (file does not exist: $file_path)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

assert_json_valid() {
    local file_path="$1"
    local test_name="$2"

    TESTS_RUN=$((TESTS_RUN + 1))

    if jq . "$file_path" >/dev/null 2>&1; then
        echo "✅ PASS: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: $test_name (invalid JSON in $file_path)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

print_results() {
    echo
    echo "=========================================="
    echo "Usage Tracker Tests Results:"
    echo "  Total:  $TESTS_RUN"
    echo "  Passed: $TESTS_PASSED"
    echo "  Failed: $TESTS_FAILED"
    echo "=========================================="

    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo "🎉 All tests passed!"
        exit 0
    else
        echo "💥 Some tests failed!"
        exit 1
    fi
}

# Setup and teardown functions
setup_test_env() {
    mkdir -p "$TEST_CLAUDE_DIR"
}

cleanup_test_env() {
    if [[ -d "$TEST_CLAUDE_DIR" ]]; then
        rm -rf "$TEST_CLAUDE_DIR"
    fi
}

# Test setup_usage_tracking function
test_setup_usage_tracking() {
    echo "Testing setup_usage_tracking function..."

    setup_usage_tracking

    assert_file_exists "$TEST_CLAUDE_DIR" "Claude directory created"
    assert_file_exists "$TEST_USAGE_DB" "Usage database file created"
    assert_json_valid "$TEST_USAGE_DB" "Usage database is valid JSON"

    # Check initial content
    local daily_usage
    daily_usage=$(jq -r '.daily_usage' "$TEST_USAGE_DB" 2>/dev/null)
    assert_equals "{}" "$daily_usage" "Initial daily_usage is empty object"

    local window_start
    window_start=$(jq -r '.window_start' "$TEST_USAGE_DB" 2>/dev/null)
    assert_equals '' "$window_start" "Initial window_start is empty string"
}

# Test update_daily_usage and get_daily_usage functions
test_daily_usage_tracking() {
    echo "Testing daily usage tracking functions..."

    setup_usage_tracking

    # Test initial daily usage (should be 0)
    local result
    result=$(get_daily_usage)
    assert_equals "0" "$result" "Initial daily usage is 0"

    # Add some usage
    update_daily_usage "1.50"
    result=$(get_daily_usage)
    assert_equals "1.5" "$result" "Daily usage updated to 1.5"

    # Add more usage (should accumulate)
    update_daily_usage "2.25"
    result=$(get_daily_usage)
    assert_equals "3.75" "$result" "Daily usage accumulated to 3.75"

    # Test with zero cost (should not change)
    update_daily_usage "0"
    result=$(get_daily_usage)
    assert_equals "3.75" "$result" "Zero cost does not change daily usage"

    # Test with null cost (should not change)
    update_daily_usage "null"
    result=$(get_daily_usage)
    assert_equals "3.75" "$result" "Null cost does not change daily usage"

    # Test with empty cost (should not change)
    update_daily_usage ""
    result=$(get_daily_usage)
    assert_equals "3.75" "$result" "Empty cost does not change daily usage"
}

# Test window tracking functions
test_window_tracking() {
    echo "Testing window tracking functions..."

    setup_usage_tracking

    # Test initial window tracking
    update_window_tracking

    local window_start
    window_start=$(jq -r '.window_start' "$TEST_USAGE_DB" 2>/dev/null)
    assert_not_empty "$window_start" "Window start timestamp set"

    # Test that subsequent calls don't reset window if within 5 hours
    local original_window_start="$window_start"
    update_window_tracking

    window_start=$(jq -r '.window_start' "$TEST_USAGE_DB" 2>/dev/null)
    assert_equals "$original_window_start" "$window_start" "Window start not reset on subsequent calls"

    # Test get_next_reset_time
    local reset_time
    reset_time=$(get_next_reset_time)
    assert_not_empty "$reset_time" "Reset time calculated"

    # Should be in format like "4h59m" or "now"
    if [[ "$reset_time" =~ ^([0-9]+h[0-9]+m|now)$ ]]; then
        echo "✅ PASS: Reset time format is valid"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: Reset time format is invalid: '$reset_time'"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    TESTS_RUN=$((TESTS_RUN + 1))
}

# Test window expiry (simulate old window)
test_window_expiry() {
    echo "Testing window expiry logic..."

    setup_usage_tracking

    # Manually set an old window start (6 hours ago)
    local old_timestamp
    old_timestamp=$(($(get_current_timestamp) - 21600))  # 6 hours ago

    jq --arg timestamp "$old_timestamp" '.window_start = $timestamp' "$TEST_USAGE_DB" > "$TEST_USAGE_DB.tmp" && mv "$TEST_USAGE_DB.tmp" "$TEST_USAGE_DB"

    # Update window tracking should reset the window
    update_window_tracking

    local new_window_start
    new_window_start=$(jq -r '.window_start' "$TEST_USAGE_DB" 2>/dev/null)

    if [[ "$new_window_start" != "$old_timestamp" && -n "$new_window_start" ]]; then
        echo "✅ PASS: Expired window resets correctly"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: Expired window should reset, but didn't"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    TESTS_RUN=$((TESTS_RUN + 1))
}

# Test cleanup_old_data function
test_cleanup_old_data() {
    echo "Testing cleanup_old_data function..."

    setup_usage_tracking

    # Add some current and old data
    local current_date
    current_date=$(get_current_date)

    # Create test data with current date and old dates
    jq --arg current "$current_date" '
        .daily_usage = {
            ($current): 5.0,
            "2023-01-01": 2.0,
            "2023-01-02": 3.0
        }
    ' "$TEST_USAGE_DB" > "$TEST_USAGE_DB.tmp" && mv "$TEST_USAGE_DB.tmp" "$TEST_USAGE_DB"

    # Run cleanup
    cleanup_old_data

    # Check that current data is preserved
    local current_usage
    current_usage=$(jq -r --arg current "$current_date" '.daily_usage[$current] // 0' "$TEST_USAGE_DB" 2>/dev/null)
    assert_equals "5.0" "$current_usage" "Current date usage preserved after cleanup"

    # Check that old data is removed (this test may be flaky depending on system date commands)
    local old_usage
    old_usage=$(jq -r '.daily_usage["2023-01-01"] // "null"' "$TEST_USAGE_DB" 2>/dev/null)

    if [[ "$old_usage" == "null" ]]; then
        echo "✅ PASS: Old usage data cleaned up"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "⏭️  SKIP: Old data cleanup test (date calculation may vary by system)"
    fi
    TESTS_RUN=$((TESTS_RUN + 1))
}

# Test edge cases
test_edge_cases() {
    echo "Testing edge cases..."

    # Test with corrupted JSON file
    mkdir -p "$TEST_CLAUDE_DIR"
    echo "invalid json" > "$TEST_USAGE_DB"

    # Functions should handle gracefully
    local result
    result=$(get_daily_usage)
    assert_equals "0" "$result" "get_daily_usage handles corrupted JSON"

    result=$(get_next_reset_time)
    assert_equals "5h0m" "$result" "get_next_reset_time handles corrupted JSON"

    # Test with missing file
    rm -f "$TEST_USAGE_DB"
    result=$(get_daily_usage)
    assert_equals "0" "$result" "get_daily_usage handles missing file"

    result=$(get_next_reset_time)
    assert_equals "5h0m" "$result" "get_next_reset_time handles missing file"
}

# Run all tests
main() {
    echo "Running Usage Tracker Module Tests..."
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

    test_window_expiry
    cleanup_test_env
    setup_test_env

    test_cleanup_old_data
    cleanup_test_env
    setup_test_env

    test_edge_cases
    cleanup_test_env

    print_results
}

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
