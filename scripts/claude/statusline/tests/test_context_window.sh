#!/bin/bash
# Unit tests for context_window feature (dynamic context size)

# Test framework setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATUSLINE_SCRIPT="$SCRIPT_DIR/../statusline.sh"

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test helper functions
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

print_results() {
    echo
    echo "=========================================="
    echo "Context Window Tests Results:"
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

# Test context window with 200K context (standard)
test_context_window_200k() {
    echo "Testing context window with 200K context..."

    # 10% usage: 20000 tokens out of 200000
    local json='{
        "model": {"display_name": "Opus"},
        "workspace": {"current_dir": "/test"},
        "context_window": {
            "total_input_tokens": 15000,
            "total_output_tokens": 5000,
            "context_window_size": 200000
        }
    }'

    local output
    output=$(echo "$json" | "$STATUSLINE_SCRIPT" 2>/dev/null)

    # 20000 / 200000 = 10%
    assert_contains "10%" "$output" "200K context: 20000 tokens = 10%"
}

# Test context window with 1M context (Opus 4.5)
test_context_window_1m() {
    echo "Testing context window with 1M context..."

    # Same 20000 tokens but with 1M context = 2%
    local json='{
        "model": {"display_name": "Opus"},
        "workspace": {"current_dir": "/test"},
        "context_window": {
            "total_input_tokens": 15000,
            "total_output_tokens": 5000,
            "context_window_size": 1000000
        }
    }'

    local output
    output=$(echo "$json" | "$STATUSLINE_SCRIPT" 2>/dev/null)

    # 20000 / 1000000 = 2%
    assert_contains "2%" "$output" "1M context: 20000 tokens = 2%"
}

# Test fallback when context_window_size is not provided
test_context_window_fallback() {
    echo "Testing fallback when context_window_size is missing..."

    # No context_window_size provided - should fallback to 200000
    local json='{
        "model": {"display_name": "Sonnet"},
        "workspace": {"current_dir": "/test"},
        "context_window": {
            "total_input_tokens": 40000,
            "total_output_tokens": 10000
        }
    }'

    local output
    output=$(echo "$json" | "$STATUSLINE_SCRIPT" 2>/dev/null)

    # 50000 / 200000 = 25% (fallback)
    assert_contains "25%" "$output" "Missing context_window_size: fallback to 200K"
}

# Test model display name is used directly
test_model_display_name() {
    echo "Testing model display name..."

    local json='{
        "model": {"id": "claude-opus-4-5-20251101", "display_name": "Opus"},
        "workspace": {"current_dir": "/test"},
        "context_window": {
            "total_input_tokens": 1000,
            "total_output_tokens": 500,
            "context_window_size": 200000
        }
    }'

    local output
    output=$(echo "$json" | "$STATUSLINE_SCRIPT" 2>/dev/null)

    assert_contains "Opus" "$output" "Display name Opus is shown directly"
}

# Test with different model display names
test_model_display_names() {
    echo "Testing various model display names..."

    for display_name in "Opus" "Sonnet" "Haiku"; do
        local json="{
            \"model\": {\"display_name\": \"$display_name\"},
            \"workspace\": {\"current_dir\": \"/test\"},
            \"context_window\": {
                \"total_input_tokens\": 1000,
                \"total_output_tokens\": 500,
                \"context_window_size\": 200000
            }
        }"

        local output
        output=$(echo "$json" | "$STATUSLINE_SCRIPT" 2>/dev/null)

        assert_contains "$display_name" "$output" "Display name $display_name is shown"
    done
}

# Test context_window.* fields are prioritized over cost.* fields
test_context_window_priority() {
    echo "Testing context_window.* field priority..."

    # Both context_window and cost have token fields - context_window should win
    local json='{
        "model": {"display_name": "Opus"},
        "workspace": {"current_dir": "/test"},
        "cost": {
            "total_input_tokens": 100000,
            "total_output_tokens": 50000
        },
        "context_window": {
            "total_input_tokens": 10000,
            "total_output_tokens": 5000,
            "context_window_size": 200000
        }
    }'

    local output
    output=$(echo "$json" | "$STATUSLINE_SCRIPT" 2>/dev/null)

    # Should use context_window values: 15000 / 200000 = 7% (not 75% from cost values)
    assert_contains "7%" "$output" "context_window.* fields take priority over cost.*"
}

# Test high context usage percentage
test_high_context_usage() {
    echo "Testing high context usage..."

    local json='{
        "model": {"display_name": "Sonnet"},
        "workspace": {"current_dir": "/test"},
        "context_window": {
            "total_input_tokens": 150000,
            "total_output_tokens": 30000,
            "context_window_size": 200000
        }
    }'

    local output
    output=$(echo "$json" | "$STATUSLINE_SCRIPT" 2>/dev/null)

    # 180000 / 200000 = 90%
    assert_contains "90%" "$output" "High context usage: 180000/200000 = 90%"
}

# Test context percentage caps at 100%
test_context_caps_at_100() {
    echo "Testing context percentage caps at 100%..."

    local json='{
        "model": {"display_name": "Opus"},
        "workspace": {"current_dir": "/test"},
        "context_window": {
            "total_input_tokens": 180000,
            "total_output_tokens": 50000,
            "context_window_size": 200000
        }
    }'

    local output
    output=$(echo "$json" | "$STATUSLINE_SCRIPT" 2>/dev/null)

    # 230000 / 200000 = 115%, but should cap at 100%
    assert_contains "100%" "$output" "Context percentage caps at 100%"
}

# Test current_usage fields (new JSON structure)
test_current_usage_basic() {
    echo "Testing current_usage fields..."

    local json='{
        "model": {"display_name": "Sonnet"},
        "workspace": {"current_dir": "/test"},
        "context_window": {
            "total_input_tokens": 100000,
            "total_output_tokens": 50000,
            "context_window_size": 200000,
            "current_usage": {
                "input_tokens": 8000,
                "output_tokens": 2000,
                "cache_read_input_tokens": 0,
                "cache_creation_input_tokens": 0
            }
        }
    }'

    local output
    output=$(echo "$json" | "$STATUSLINE_SCRIPT" 2>/dev/null)

    # Should use current_usage: (8000 + 0) + 2000 = 10000 / 200000 = 5%
    assert_contains "5%" "$output" "current_usage: 10000 tokens = 5%"
}

# Test current_usage with cache reads
test_current_usage_with_cache() {
    echo "Testing current_usage with cache reads..."

    local json='{
        "model": {"display_name": "Opus"},
        "workspace": {"current_dir": "/test"},
        "context_window": {
            "context_window_size": 200000,
            "current_usage": {
                "input_tokens": 10000,
                "output_tokens": 5000,
                "cache_read_input_tokens": 5000,
                "cache_creation_input_tokens": 2000
            }
        }
    }'

    local output
    output=$(echo "$json" | "$STATUSLINE_SCRIPT" 2>/dev/null)

    # input + cache_read + output = (10000 + 5000) + 5000 = 20000 / 200000 = 10%
    assert_contains "10%" "$output" "current_usage with cache: 20000 tokens = 10%"
}

# Test current_usage takes priority over total_* fields
test_current_usage_priority() {
    echo "Testing current_usage priority over total_*..."

    local json='{
        "model": {"display_name": "Sonnet"},
        "workspace": {"current_dir": "/test"},
        "context_window": {
            "total_input_tokens": 100000,
            "total_output_tokens": 50000,
            "context_window_size": 200000,
            "current_usage": {
                "input_tokens": 5000,
                "output_tokens": 5000,
                "cache_read_input_tokens": 0
            }
        }
    }'

    local output
    output=$(echo "$json" | "$STATUSLINE_SCRIPT" 2>/dev/null)

    # Should use current_usage: 10000 / 200000 = 5% (not 75% from total_*)
    assert_contains "5%" "$output" "current_usage takes priority over total_*"
}

# Test backward compatibility when current_usage is missing
test_backward_compatibility() {
    echo "Testing backward compatibility without current_usage..."

    local json='{
        "model": {"display_name": "Opus"},
        "workspace": {"current_dir": "/test"},
        "context_window": {
            "total_input_tokens": 15000,
            "total_output_tokens": 5000,
            "context_window_size": 200000
        }
    }'

    local output
    output=$(echo "$json" | "$STATUSLINE_SCRIPT" 2>/dev/null)

    # Falls back to total_*: 20000 / 200000 = 10%
    assert_contains "10%" "$output" "Backward compatibility: uses total_* when current_usage missing"
}

# Run all tests
main() {
    echo "Running Context Window Module Tests..."
    echo

    test_context_window_200k
    test_context_window_1m
    test_context_window_fallback
    test_model_display_name
    test_model_display_names
    test_context_window_priority
    test_high_context_usage
    test_context_caps_at_100
    test_current_usage_basic
    test_current_usage_with_cache
    test_current_usage_priority
    test_backward_compatibility

    print_results
}

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
