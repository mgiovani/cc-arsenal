#!/bin/bash
# Unit tests for components.sh

# Test framework setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$SCRIPT_DIR/../lib"

# Source the modules under test
source "$LIB_DIR/colors.sh"
source "$LIB_DIR/utils.sh"
source "$LIB_DIR/git_info.sh"
source "$LIB_DIR/components.sh"

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

assert_contains() {
    local expected_substring="$1"
    local actual="$2"
    local test_name="$3"

    TESTS_RUN=$((TESTS_RUN + 1))

    if [[ "$actual" == *"$expected_substring"* ]]; then
        echo "✅ PASS: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: $test_name"
        echo "   Expected substring: '$expected_substring'"
        echo "   Actual:             '$actual'"
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
    echo "Components Tests Results:"
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

# Test model components
test_model_components() {
    echo "Testing model components..."

    local result

    # Test basic model component
    result=$(get_model_component "claude-3-5-sonnet-20241022" "20241022")
    assert_contains "🤖" "$result" "Model component includes robot emoji"
    assert_contains "3-5-sonnet" "$result" "Model component includes simplified model name"
    assert_contains "20241022" "$result" "Model component includes version"
    assert_contains "$STATUSLINE_BRIGHT_BLUE" "$result" "Model component uses bright blue color"

    # Test model without version
    result=$(get_model_component "claude-3-5-sonnet" "")
    assert_contains "🤖" "$result" "Model component without version includes emoji"
    assert_contains "3-5-sonnet" "$result" "Model component without version includes model name"

    # Test compact model component
    result=$(get_model_component_compact "claude-3-5-sonnet-20241022")
    assert_contains "🤖" "$result" "Compact model component includes emoji"
    assert_contains "c3-5-s" "$result" "Compact model component abbreviates name"
}

# Test directory components
test_directory_components() {
    echo "Testing directory components..."

    local result

    # Test directory component
    result=$(get_directory_component "/home/user/projects/test")
    assert_contains "📁" "$result" "Directory component includes folder emoji"
    assert_contains "/home/user/projects/test" "$result" "Directory component includes path"
    assert_contains "$STATUSLINE_BRIGHT_CYAN" "$result" "Directory component uses bright cyan color"

    # Test with home directory
    result=$(get_directory_component "$HOME/Documents")
    assert_contains "📁" "$result" "Home directory component includes emoji"

    # Test compact directory component
    result=$(get_directory_component_compact "/very/long/path/to/project/directory")
    assert_contains "📁" "$result" "Compact directory component includes emoji"

    # Should show only basename
    if [[ "$result" == *"directory"* ]]; then
        echo "✅ PASS: Compact directory shows basename"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: Compact directory should show basename 'directory'"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    TESTS_RUN=$((TESTS_RUN + 1))
}

# Test context components
test_context_components() {
    echo "Testing context components..."

    local result

    # Test low context usage (green)
    result=$(get_context_component 25)
    assert_contains "📊" "$result" "Context component includes chart emoji"
    assert_contains "25%" "$result" "Context component includes percentage"
    assert_contains "$STATUSLINE_GREEN" "$result" "Low context usage uses green color"

    # Test medium context usage (yellow)
    result=$(get_context_component 65)
    assert_contains "65%" "$result" "Medium context component includes percentage"
    assert_contains "$STATUSLINE_YELLOW" "$result" "Medium context usage uses yellow color"

    # Test high context usage (red)
    result=$(get_context_component 95)
    assert_contains "95%" "$result" "High context component includes percentage"
    assert_contains "$STATUSLINE_RED" "$result" "High context usage uses red color"

    # Test compact context component
    result=$(get_context_component_compact 50)
    assert_contains "📊" "$result" "Compact context component includes emoji"
    assert_contains "50%" "$result" "Compact context component includes percentage"
}

# Test cost components
test_cost_components() {
    echo "Testing cost components..."

    local result

    # Test session cost with dollar amount
    result=$(get_session_cost_component "0.045")
    assert_contains "💰" "$result" "Session cost component includes money emoji"
    assert_contains "\$0.045" "$result" "Session cost component includes dollar amount"
    assert_contains "$STATUSLINE_YELLOW" "$result" "Session cost uses yellow color"

    # Test session cost with token format
    result=$(get_session_cost_component "1500→950")
    assert_contains "🎯" "$result" "Token cost component includes target emoji"
    assert_contains "1500→950" "$result" "Token cost component includes token counts"

    # Test empty cost components (should show N/A after our improvements)
    result=$(get_session_cost_component "")
    assert_contains "💰 N/A" "$result" "Empty session cost shows unavailable"
}

# Test reset components
test_reset_components() {
    echo "Testing reset components..."

    local result

    # Test reset countdown
    result=$(get_reset_component "2h30m")
    assert_contains "🔄" "$result" "Reset component includes refresh emoji"
    assert_contains "2h30m" "$result" "Reset component includes time"
    assert_contains "$STATUSLINE_BLUE" "$result" "Long reset time uses blue color"

    # Test urgent reset countdown (red)
    result=$(get_reset_component "0h15m")
    assert_contains "🔄" "$result" "Urgent reset component includes emoji"
    assert_contains "0h15m" "$result" "Urgent reset component includes time"
    assert_contains "$STATUSLINE_RED" "$result" "Urgent reset time uses red color"

    # Test reset now
    result=$(get_reset_component "now")
    assert_contains "🔄" "$result" "Reset now component includes emoji"
    assert_contains "reset!" "$result" "Reset now component includes reset message"
    assert_contains "$STATUSLINE_BRIGHT_GREEN" "$result" "Reset now uses bright green color"

    # Test compact reset component
    result=$(get_reset_component_compact "1h30m")
    assert_contains "🔄" "$result" "Compact reset component includes emoji"
    assert_contains "1h30m" "$result" "Compact reset component includes time"

    # Test compact reset now
    result=$(get_reset_component_compact "now")
    assert_contains "🔄!" "$result" "Compact reset now shows abbreviated format"
}

# Test session duration component
test_session_duration_component() {
    echo "Testing session duration component..."

    local result

    # Test with duration
    result=$(get_session_duration_component "2h15m")
    assert_contains "⏰" "$result" "Session duration component includes clock emoji"
    assert_contains "2h15m" "$result" "Session duration component includes time"
    assert_contains "$STATUSLINE_GRAY" "$result" "Session duration uses gray color"

    # Test with empty duration
    result=$(get_session_duration_component "")
    assert_equals "" "$result" "Empty session duration returns empty"
}

# Test component color consistency
test_component_colors() {
    echo "Testing component color consistency..."

    # All components should end with RESET
    local components=(
        "$(get_model_component "claude-3-5-sonnet" "")"
        "$(get_directory_component "/test/path")"
        "$(get_context_component 50)"
        "$(get_session_cost_component "0.05")"
        "$(get_reset_component "2h30m")"
        "$(get_session_duration_component "1h30m")"
    )

    local component_names=(
        "model"
        "directory"
        "context"
        "session_cost"
        "reset"
        "session_duration"
    )

    for i in "${!components[@]}"; do
        local component="${components[$i]}"
        local name="${component_names[$i]}"

        if [[ -n "$component" ]]; then
            assert_contains "$STATUSLINE_RESET" "$component" "$name component ends with reset"
        fi
    done
}

# Run all tests
main() {
    echo "Running Components Module Tests..."
    echo

    test_model_components
    test_directory_components
    test_context_components
    test_cost_components
    test_reset_components
    test_session_duration_component
    test_component_colors

    print_results
}

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
