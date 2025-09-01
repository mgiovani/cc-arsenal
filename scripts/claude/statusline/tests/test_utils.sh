#!/bin/bash
# Unit tests for utils.sh

# Test framework setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$SCRIPT_DIR/../lib"

# Source the module under test
source "$LIB_DIR/utils.sh"

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
    echo "Utils Tests Results:"
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

# Test date and timestamp functions
test_date_functions() {
    echo "Testing date and timestamp functions..."
    
    local date_result
    date_result=$(get_current_date)
    assert_not_empty "$date_result" "get_current_date returns non-empty"
    
    # Check date format (YYYY-MM-DD)
    if [[ "$date_result" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
        echo "✅ PASS: get_current_date format is YYYY-MM-DD"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: get_current_date format is not YYYY-MM-DD"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    TESTS_RUN=$((TESTS_RUN + 1))
    
    local timestamp_result
    timestamp_result=$(get_current_timestamp)
    assert_not_empty "$timestamp_result" "get_current_timestamp returns non-empty"
    
    # Check timestamp is numeric
    if [[ "$timestamp_result" =~ ^[0-9]+$ ]]; then
        echo "✅ PASS: get_current_timestamp is numeric"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: get_current_timestamp is not numeric"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    TESTS_RUN=$((TESTS_RUN + 1))
}

# Test JSON parsing functions
test_json_parsing() {
    echo "Testing JSON parsing functions..."
    
    local test_json='{"name":"test","value":42,"nested":{"key":"nested_value"}}'
    
    local result
    result=$(get_json_field "$test_json" '.name' 'default')
    assert_equals "test" "$result" "get_json_field extracts string value"
    
    result=$(get_json_field "$test_json" '.missing' 'default_val')
    assert_equals "default_val" "$result" "get_json_field returns default for missing key"
    
    result=$(get_json_field "$test_json" '.nested.key' 'default')
    assert_equals "nested_value" "$result" "get_json_field extracts nested value"
    
    result=$(get_json_number "$test_json" '.value' 0)
    assert_equals "42" "$result" "get_json_number extracts numeric value"
    
    result=$(get_json_number "$test_json" '.missing' 99)
    assert_equals "99" "$result" "get_json_number returns default for missing key"
}

# Test shorten_path function
test_shorten_path() {
    echo "Testing shorten_path function..."
    
    local result
    
    # Test home directory replacement
    result=$(shorten_path "$HOME/Documents/test" 50)
    assert_equals "~/Documents/test" "$result" "shorten_path replaces home with ~"
    
    # Test path truncation
    result=$(shorten_path "/very/long/path/that/exceeds/the/limit" 20)
    local expected="...exceeds/the/limit"  # Fixed: should be 17 chars + "..." = 20 total
    assert_equals "$expected" "$result" "shorten_path truncates long paths"
    
    # Test short path unchanged
    result=$(shorten_path "/short/path" 50)
    assert_equals "/short/path" "$result" "shorten_path leaves short paths unchanged"
}

# Test format_duration function
test_format_duration() {
    echo "Testing format_duration function..."
    
    local result
    
    result=$(format_duration 3661)  # 1h 1m 1s
    assert_equals "1h1m" "$result" "format_duration handles hours and minutes"
    
    result=$(format_duration 300)   # 5m
    assert_equals "5m" "$result" "format_duration handles minutes only"
    
    result=$(format_duration 0)     # 0m
    assert_equals "0m" "$result" "format_duration handles zero duration"
    
    result=$(format_duration 7200)  # 2h exactly
    assert_equals "2h0m" "$result" "format_duration handles exact hours"
}

# Test calculate_session_duration function
test_calculate_session_duration() {
    echo "Testing calculate_session_duration function..."
    
    # Test with valid ISO timestamp (if python3 is available)
    if command -v python3 &>/dev/null; then
        local result
        result=$(calculate_session_duration "2025-01-01T10:00:00Z")
        
        # Should return some duration (format varies based on actual time difference)
        if [[ -n "$result" && "$result" =~ ^[0-9]+[hm] ]]; then
            echo "✅ PASS: calculate_session_duration returns valid duration format"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo "❌ FAIL: calculate_session_duration format is invalid: '$result'"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
        TESTS_RUN=$((TESTS_RUN + 1))
        
        # Test with invalid timestamp
        result=$(calculate_session_duration "invalid-timestamp")
        assert_equals "" "$result" "calculate_session_duration handles invalid timestamp"
        
        # Test with empty timestamp
        result=$(calculate_session_duration "")
        assert_equals "" "$result" "calculate_session_duration handles empty timestamp"
    else
        echo "⏭️  SKIP: calculate_session_duration tests (python3 not available)"
    fi
}

# Test get_terminal_width function
test_get_terminal_width() {
    echo "Testing get_terminal_width function..."
    
    local result
    result=$(get_terminal_width)
    
    # Should return a positive number
    if [[ "$result" =~ ^[0-9]+$ && $result -gt 0 ]]; then
        echo "✅ PASS: get_terminal_width returns positive number"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: get_terminal_width should return positive number, got: '$result'"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    TESTS_RUN=$((TESTS_RUN + 1))
}

# Run all tests
main() {
    echo "Running Utils Module Tests..."
    echo
    
    test_date_functions
    test_json_parsing
    test_shorten_path
    test_format_duration
    test_calculate_session_duration
    test_get_terminal_width
    
    print_results
}

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi