#!/bin/bash
# Unit tests for colors.sh

# Test framework setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$SCRIPT_DIR/../lib"

# Source the module under test
source "$LIB_DIR/colors.sh"

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

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

print_results() {
    echo
    echo "=========================================="
    echo "Color Tests Results:"
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

# Test color constants are defined
test_color_constants() {
    echo "Testing color constants..."

    assert_not_empty "$STATUSLINE_RED" "STATUSLINE_RED is defined"
    assert_not_empty "$STATUSLINE_GREEN" "STATUSLINE_GREEN is defined"
    assert_not_empty "$STATUSLINE_YELLOW" "STATUSLINE_YELLOW is defined"
    assert_not_empty "$STATUSLINE_BLUE" "STATUSLINE_BLUE is defined"
    assert_not_empty "$STATUSLINE_RESET" "STATUSLINE_RESET is defined"
}

# Test colorize function
test_colorize() {
    echo "Testing colorize function..."

    local result
    local expected

    # Test colorize with red - use printf to avoid echo interpretation issues
    result=$(colorize "$STATUSLINE_RED" "test")
    expected=$(printf "${STATUSLINE_RED}test${STATUSLINE_RESET}")
    assert_equals "$expected" "$result" "colorize with red"

    # Test colorize with green
    result=$(colorize "$STATUSLINE_GREEN" "success")
    expected=$(printf "${STATUSLINE_GREEN}success${STATUSLINE_RESET}")
    assert_equals "$expected" "$result" "colorize with green"
}

# Test get_context_color
test_get_context_color() {
    echo "Testing get_context_color function..."

    local result
    result=$(get_context_color 25)
    assert_equals "$STATUSLINE_GREEN" "$result" "context color for 25% (green)"

    result=$(get_context_color 50)
    assert_equals "$STATUSLINE_YELLOW" "$result" "context color for 50% (yellow)"

    result=$(get_context_color 75)
    assert_equals "$STATUSLINE_YELLOW" "$result" "context color for 75% (yellow)"

    result=$(get_context_color 90)
    assert_equals "$STATUSLINE_RED" "$result" "context color for 90% (red)"
}

# Test get_reset_color
test_get_reset_color() {
    echo "Testing get_reset_color function..."

    local result
    result=$(get_reset_color "0h30m")
    assert_equals "$STATUSLINE_RED" "$result" "reset color for 0h30m (red)"

    result=$(get_reset_color "1h15m")
    assert_equals "$STATUSLINE_YELLOW" "$result" "reset color for 1h15m (yellow)"

    result=$(get_reset_color "3h45m")
    assert_equals "$STATUSLINE_BLUE" "$result" "reset color for 3h45m (blue)"
}

# Test get_git_status_color
test_get_git_status_color() {
    echo "Testing get_git_status_color function..."

    local result
    result=$(get_git_status_color "clean")
    assert_equals "$STATUSLINE_GREEN" "$result" "git status color for clean"

    result=$(get_git_status_color "dirty")
    assert_equals "$STATUSLINE_YELLOW" "$result" "git status color for dirty"

    result=$(get_git_status_color "ahead")
    assert_equals "$STATUSLINE_BLUE" "$result" "git status color for ahead"

    result=$(get_git_status_color "behind")
    assert_equals "$STATUSLINE_CYAN" "$result" "git status color for behind"

    result=$(get_git_status_color "diverged")
    assert_equals "$STATUSLINE_MAGENTA" "$result" "git status color for diverged"

    result=$(get_git_status_color "unknown")
    assert_equals "$STATUSLINE_GRAY" "$result" "git status color for unknown"
}

# Run all tests
main() {
    echo "Running Color Module Tests..."
    echo

    test_color_constants
    test_colorize
    test_get_context_color
    test_get_reset_color
    test_get_git_status_color

    print_results
}

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
