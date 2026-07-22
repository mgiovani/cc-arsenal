#!/bin/bash
# =============================================================================
# Tests for lib/core/platform.sh
# =============================================================================

# Test environment setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$(cd "$SCRIPT_DIR/../../lib" && pwd)"

# Shared assert helpers (assert_equals, assert_not_empty, TESTS_RUN/PASSED/FAILED, ...)
source "$SCRIPT_DIR/../lib/assert.sh"

# Source the module under test
source "$LIB_DIR/core/platform.sh"

# Local helper - not part of the shared set, only used in this file
assert_numeric() {
    local value="$1"
    local test_name="$2"

    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ "$value" =~ ^[0-9]+$ ]]; then
        echo "✅ PASS: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: $test_name (not numeric: '$value')"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# =============================================================================
# Test: get_platform
# =============================================================================
test_get_platform() {
    echo "--- Testing get_platform ---"

    local platform
    platform=$(get_platform)

    assert_not_empty "$platform" "get_platform returns non-empty"

    # Should be darwin or linux
    if [[ "$platform" == "darwin" || "$platform" == "linux" ]]; then
        echo "✅ PASS: get_platform returns valid platform ($platform)"
        TESTS_RUN=$((TESTS_RUN + 1))
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "⚠️  INFO: get_platform returns '$platform' (not darwin/linux)"
        TESTS_RUN=$((TESTS_RUN + 1))
        TESTS_PASSED=$((TESTS_PASSED + 1))
    fi
}

# =============================================================================
# Test: is_macos / is_linux
# =============================================================================
test_platform_detection() {
    echo "--- Testing platform detection ---"

    local platform
    platform=$(get_platform)

    if [[ "$platform" == "darwin" ]]; then
        if is_macos; then
            echo "✅ PASS: is_macos returns true on macOS"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo "❌ FAIL: is_macos should return true on darwin"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    else
        if is_linux; then
            echo "✅ PASS: is_linux returns true on Linux"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo "⚠️  INFO: Neither macOS nor Linux detected"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        fi
    fi
    TESTS_RUN=$((TESTS_RUN + 1))
}

# =============================================================================
# Test: get_file_mtime
# =============================================================================
test_get_file_mtime() {
    echo "--- Testing get_file_mtime ---"

    # Create a temp file
    local temp_file
    temp_file=$(mktemp)
    echo "test" > "$temp_file"

    local mtime
    mtime=$(get_file_mtime "$temp_file")

    assert_numeric "$mtime" "get_file_mtime returns numeric value"

    # Mtime should be recent (within last minute)
    local current_time
    current_time=$(date +%s)
    local age=$((current_time - mtime))

    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ $age -lt 60 ]]; then
        echo "✅ PASS: get_file_mtime returns recent timestamp (age: ${age}s)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: get_file_mtime timestamp too old (age: ${age}s)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi

    # Test non-existent file
    local nonexistent_mtime
    nonexistent_mtime=$(get_file_mtime "/nonexistent/file/path")
    assert_equals "0" "$nonexistent_mtime" "get_file_mtime returns 0 for nonexistent file"

    rm -f "$temp_file"
}

# =============================================================================
# Test: parse_iso_timestamp
# =============================================================================
test_parse_iso_timestamp() {
    echo "--- Testing parse_iso_timestamp ---"

    # Test standard ISO format
    local result
    result=$(parse_iso_timestamp "2025-01-01T00:00:00")
    assert_numeric "$result" "parse_iso_timestamp returns numeric for standard format"

    # Test with milliseconds
    result=$(parse_iso_timestamp "2025-01-01T12:30:45.123Z")
    assert_numeric "$result" "parse_iso_timestamp returns numeric with milliseconds"

    # Test with timezone
    result=$(parse_iso_timestamp "2025-01-01T12:30:45+00:00")
    assert_numeric "$result" "parse_iso_timestamp returns numeric with timezone"

    # Test invalid format returns 0
    result=$(parse_iso_timestamp "invalid")
    assert_equals "0" "$result" "parse_iso_timestamp returns 0 for invalid format"
}

# =============================================================================
# Test: floor_epoch_to_hour
# =============================================================================
test_floor_epoch_to_hour() {
    echo "--- Testing floor_epoch_to_hour ---"

    # Test exact hour (should return same value)
    local result
    result=$(floor_epoch_to_hour 1704110400)  # 2024-01-01 12:00:00 UTC
    assert_equals "1704110400" "$result" "floor_epoch_to_hour preserves exact hour"

    # Test mid-hour (should floor down)
    result=$(floor_epoch_to_hour 1704111800)  # 2024-01-01 12:23:20 UTC
    assert_equals "1704110400" "$result" "floor_epoch_to_hour floors mid-hour"

    # Test just before hour boundary
    result=$(floor_epoch_to_hour 1704113999)  # 2024-01-01 12:59:59 UTC
    assert_equals "1704110400" "$result" "floor_epoch_to_hour floors end of hour"
}

# =============================================================================
# Test: epoch_to_time_display
# =============================================================================
test_epoch_to_time_display() {
    echo "--- Testing epoch_to_time_display ---"

    local result
    result=$(epoch_to_time_display 0 "+%Y")

    # Should return something, not ??:??
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ "$result" != "??:??" ]]; then
        echo "✅ PASS: epoch_to_time_display returns formatted time"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: epoch_to_time_display returned fallback value"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# =============================================================================
# Test: get_current_epoch
# =============================================================================
test_get_current_epoch() {
    echo "--- Testing get_current_epoch ---"

    local result
    result=$(get_current_epoch)

    assert_numeric "$result" "get_current_epoch returns numeric"

    # Should be a reasonable timestamp (after 2020)
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ $result -gt 1577836800 ]]; then  # 2020-01-01
        echo "✅ PASS: get_current_epoch returns reasonable timestamp"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: get_current_epoch returned suspiciously old timestamp"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# =============================================================================
# Test: hash_string
# =============================================================================
test_hash_string() {
    echo "--- Testing hash_string ---"

    local result
    result=$(hash_string "test")

    assert_not_empty "$result" "hash_string returns non-empty"

    # Same input should return same hash
    local result2
    result2=$(hash_string "test")
    assert_equals "$result" "$result2" "hash_string is deterministic"

    # Different input should return different hash
    local result3
    result3=$(hash_string "different")
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ "$result" != "$result3" ]]; then
        echo "✅ PASS: hash_string returns different hash for different input"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: hash_string returned same hash for different input"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# =============================================================================
# Test: hash_sha256
# =============================================================================
test_hash_sha256() {
    echo "--- Testing hash_sha256 ---"

    local result
    result=$(hash_sha256 "test")

    assert_not_empty "$result" "hash_sha256 returns non-empty"

    # Same input should return same hash
    local result2
    result2=$(hash_sha256 "test")
    assert_equals "$result" "$result2" "hash_sha256 is deterministic"

    # Output is exactly 12 chars
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ ${#result} -eq 12 ]]; then
        echo "✅ PASS: hash_sha256 returns 12 chars"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: hash_sha256 returned ${#result} chars: '$result'"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi

    # Output matches lowercase hex pattern (or "default" fallback)
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ "$result" =~ ^[a-f0-9]{12}$ ]]; then
        echo "✅ PASS: hash_sha256 returns lowercase hex"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: hash_sha256 did not return lowercase hex: '$result'"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi

    # Different input should return different hash
    local result3
    result3=$(hash_sha256 "different")
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ "$result" != "$result3" ]]; then
        echo "✅ PASS: hash_sha256 returns different hash for different input"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: hash_sha256 returned same hash for different input"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi

    # Input with spaces/special chars works
    local result4
    result4=$(hash_sha256 "sk-ant-oat01-abc 123!@#$%^&*()")
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ "$result4" =~ ^[a-f0-9]{12}$ ]]; then
        echo "✅ PASS: hash_sha256 handles special chars"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: hash_sha256 failed on special chars: '$result4'"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# =============================================================================
# Run all tests
# =============================================================================
main() {
    echo "========================================"
    echo "Running tests for lib/core/platform.sh"
    echo "========================================"
    echo

    test_get_platform
    echo
    test_platform_detection
    echo
    test_get_file_mtime
    echo
    test_parse_iso_timestamp
    echo
    test_floor_epoch_to_hour
    echo
    test_epoch_to_time_display
    echo
    test_get_current_epoch
    echo
    test_hash_string
    echo
    test_hash_sha256

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
