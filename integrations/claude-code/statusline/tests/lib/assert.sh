#!/bin/bash
# =============================================================================
# Shared Test Assertion Helpers
# =============================================================================
# Common assert_* helpers and pass/fail counters used by every test file in
# tests/. Source this instead of redefining the same helpers per file.

# Guard clause - prevent multiple sourcing
if [[ -n "${STATUSLINE_TEST_ASSERT_LOADED:-}" ]]; then
    return 0
fi
readonly STATUSLINE_TEST_ASSERT_LOADED=1

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Remove ANSI color escapes so assertions can match visible text
# Usage: strip_ansi "$colored_output"
strip_ansi() {
    printf '%s' "$1" | sed $'s/\033\\[[0-9;]*m//g'
}

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

assert_not_equals() {
    local not_expected="$1"
    local actual="$2"
    local test_name="$3"

    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ "$not_expected" != "$actual" ]]; then
        echo "✅ PASS: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: $test_name (both were '$actual')"
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

assert_not_contains() {
    local unexpected_substring="$1"
    local actual="$2"
    local test_name="$3"

    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ "$actual" != *"$unexpected_substring"* ]]; then
        echo "✅ PASS: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: $test_name"
        echo "   Unexpected substring: '$unexpected_substring'"
        echo "   Actual:               '$actual'"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Usage: assert_matches "$value" "$pattern" "test name"
assert_matches() {
    local value="$1"
    local pattern="$2"
    local test_name="$3"

    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ "$value" =~ $pattern ]]; then
        echo "✅ PASS: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: $test_name (value: '$value')"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

assert_file_exists() {
    local file="$1"
    local test_name="$2"

    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ -f "$file" || -d "$file" ]]; then
        echo "✅ PASS: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: $test_name (missing: '$file')"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

assert_file_absent() {
    local file="$1"
    local test_name="$2"

    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ ! -f "$file" ]]; then
        echo "✅ PASS: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: $test_name (should not exist: '$file')"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Usage: print_results "Color Tests"
print_results() {
    local suite_name="${1:-Test}"

    echo
    echo "=========================================="
    echo "${suite_name} Results:"
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
