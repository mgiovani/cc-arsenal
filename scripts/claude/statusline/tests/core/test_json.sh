#!/bin/bash
# =============================================================================
# Tests for lib/core/json.sh
# =============================================================================

# Test environment setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$(cd "$SCRIPT_DIR/../../lib" && pwd)"

# Source dependencies
source "$LIB_DIR/core/platform.sh"
source "$LIB_DIR/core/json.sh"

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
    local value="$1"
    local test_name="$2"

    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ -n "$value" ]]; then
        echo "✅ PASS: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: $test_name (value is empty)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# =============================================================================
# Test: check_jq
# =============================================================================
test_check_jq() {
    echo "--- Testing check_jq ---"

    TESTS_RUN=$((TESTS_RUN + 1))
    if command -v jq >/dev/null 2>&1; then
        if check_jq; then
            echo "✅ PASS: check_jq returns true when jq is available"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo "❌ FAIL: check_jq should return true (jq is installed)"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    else
        if ! check_jq; then
            echo "✅ PASS: check_jq returns false when jq is not available"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo "❌ FAIL: check_jq should return false (jq not installed)"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    fi
}

# =============================================================================
# Test: extract_json with simple values
# =============================================================================
test_extract_json_simple() {
    echo "--- Testing extract_json (simple values) ---"

    local json='{"name":"test","count":42,"enabled":true}'

    # String extraction
    local result
    result=$(extract_json "$json" "name")
    assert_equals "test" "$result" "extract_json extracts string value"

    # This test requires jq for nested paths, so only run if jq available
    if check_jq; then
        # Number extraction
        result=$(extract_json "$json" "count")
        assert_equals "42" "$result" "extract_json extracts number value"
    fi
}

# =============================================================================
# Test: extract_json with nested values
# =============================================================================
test_extract_json_nested() {
    echo "--- Testing extract_json (nested values) ---"

    local json='{"model":{"id":"claude-opus","display_name":"Opus"},"cost":{"total_cost_usd":1.25}}'

    # Nested string extraction
    local result
    result=$(extract_json "$json" "model.id")
    assert_equals "claude-opus" "$result" "extract_json extracts nested string"

    result=$(extract_json "$json" "model.display_name")
    assert_equals "Opus" "$result" "extract_json extracts nested display_name"

    # Nested number extraction
    if check_jq; then
        result=$(extract_json "$json" "cost.total_cost_usd")
        assert_equals "1.25" "$result" "extract_json extracts nested number"
    fi
}

# =============================================================================
# Test: extract_json with context_window fields
# =============================================================================
test_extract_json_context_window() {
    echo "--- Testing extract_json (context_window fields) ---"

    local json='{"context_window":{"total_input_tokens":1000,"total_output_tokens":500,"context_window_size":200000}}'

    local result
    result=$(extract_json "$json" "context_window.total_input_tokens")
    assert_equals "1000" "$result" "extract_json extracts total_input_tokens"

    result=$(extract_json "$json" "context_window.total_output_tokens")
    assert_equals "500" "$result" "extract_json extracts total_output_tokens"

    result=$(extract_json "$json" "context_window.context_window_size")
    assert_equals "200000" "$result" "extract_json extracts context_window_size"
}

# =============================================================================
# Test: extract_json with missing values
# =============================================================================
test_extract_json_missing() {
    echo "--- Testing extract_json (missing values) ---"

    local json='{"name":"test"}'

    # Missing key should return empty/fail
    local result
    result=$(extract_json "$json" "nonexistent" 2>/dev/null || echo "")

    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ -z "$result" ]]; then
        echo "✅ PASS: extract_json returns empty for missing key"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: extract_json should return empty for missing key"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# =============================================================================
# Test: grep_string
# =============================================================================
test_grep_string() {
    echo "--- Testing grep_string ---"

    local json='{"name":"test_value","other":"data"}'

    local result
    result=$(grep_string "$json" "name")
    assert_equals "test_value" "$result" "grep_string extracts string value"

    # Test compact JSON
    json='{"name":"compact"}'
    result=$(grep_string "$json" "name")
    assert_equals "compact" "$result" "grep_string works with compact JSON"
}

# =============================================================================
# Test: grep_number
# =============================================================================
test_grep_number() {
    echo "--- Testing grep_number ---"

    local json='{"count":42,"rate":3.14}'

    local result
    result=$(grep_number "$json" "count")
    assert_equals "42" "$result" "grep_number extracts integer"

    result=$(grep_number "$json" "rate")
    assert_equals "3.14" "$result" "grep_number extracts float"
}

# =============================================================================
# Test: is_valid_json
# =============================================================================
test_is_valid_json() {
    echo "--- Testing is_valid_json ---"

    TESTS_RUN=$((TESTS_RUN + 1))
    if is_valid_json '{"valid":"json"}'; then
        echo "✅ PASS: is_valid_json returns true for valid JSON"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: is_valid_json should return true"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi

    TESTS_RUN=$((TESTS_RUN + 1))
    if is_valid_json '[1,2,3]'; then
        echo "✅ PASS: is_valid_json returns true for array"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: is_valid_json should return true for array"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi

    TESTS_RUN=$((TESTS_RUN + 1))
    if ! is_valid_json 'not json'; then
        echo "✅ PASS: is_valid_json returns false for invalid JSON"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: is_valid_json should return false for invalid"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# =============================================================================
# Test: Real-world Claude Code JSON
# =============================================================================
test_real_world_json() {
    echo "--- Testing with real-world Claude Code JSON ---"

    local json='{
        "model": {"id": "claude-opus-4-5-20251101", "display_name": "Opus"},
        "workspace": {"current_dir": "/Users/test/project"},
        "cost": {"total_cost_usd": 1.234, "total_lines_added": 100, "total_lines_removed": 50},
        "context_window": {"total_input_tokens": 50000, "total_output_tokens": 10000, "context_window_size": 200000}
    }'

    local result

    result=$(extract_json "$json" "model.display_name")
    assert_equals "Opus" "$result" "Real JSON: model.display_name"

    result=$(extract_json "$json" "workspace.current_dir")
    assert_equals "/Users/test/project" "$result" "Real JSON: workspace.current_dir"

    if check_jq; then
        result=$(extract_json "$json" "cost.total_cost_usd")
        assert_equals "1.234" "$result" "Real JSON: cost.total_cost_usd"

        result=$(extract_json "$json" "context_window.total_input_tokens")
        assert_equals "50000" "$result" "Real JSON: context_window.total_input_tokens"
    fi
}

# =============================================================================
# Run all tests
# =============================================================================
main() {
    echo "========================================"
    echo "Running tests for lib/core/json.sh"
    echo "========================================"
    echo
    echo "jq available: $(command -v jq >/dev/null 2>&1 && echo 'yes' || echo 'no')"
    echo

    test_check_jq
    echo
    test_extract_json_simple
    echo
    test_extract_json_nested
    echo
    test_extract_json_context_window
    echo
    test_extract_json_missing
    echo
    test_grep_string
    echo
    test_grep_number
    echo
    test_is_valid_json
    echo
    test_real_world_json

    echo
    echo "========================================"
    echo "Test Results: $TESTS_PASSED/$TESTS_RUN passed"
    if [[ $TESTS_FAILED -gt 0 ]]; then
        echo "FAILED: $TESTS_FAILED tests"
        exit 1
    else
        echo "All tests passed!"
        exit 0
    fi
}

main "$@"
