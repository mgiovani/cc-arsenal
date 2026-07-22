#!/bin/bash
# Unit tests for lib/display/components.sh (new modular architecture)

# Test framework setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$SCRIPT_DIR/../lib"

# Shared assert helpers (assert_equals, assert_contains, assert_not_contains,
# assert_not_empty, print_results, ...)
source "$SCRIPT_DIR/lib/assert.sh"

# components.sh calls check_jq (defined in core/json.sh) without sourcing it
# itself - only works standalone because statusline.sh happens to source
# core/json.sh first. Source it explicitly here so this unit test doesn't
# depend on that incidental ordering.
source "$LIB_DIR/core/json.sh"

# Source the modules under test
source "$LIB_DIR/config.sh"
source "$LIB_DIR/display/components.sh"

# Test emoji mode components (default)
test_emoji_mode_components() {
    echo "Testing emoji mode components (default)..."

    # Ensure emoji mode is active via environment override
    unset STATUSLINE_TEXT_MODE
    export STATUSLINE_DISPLAY_MODE=emoji

    local result

    # Test model component
    result=$(get_model_component "Opus")
    assert_contains "🤖" "$result" "Emoji mode model has robot emoji"
    assert_contains "Opus" "$result" "Emoji mode model shows name"

    # Test directory component
    result=$(get_directory_component "/home/user/projects")
    assert_contains "📁" "$result" "Emoji mode directory has folder emoji"

    # Test context component
    result=$(get_context_component 45)
    assert_contains "📊" "$result" "Emoji mode context has chart emoji"
    assert_contains "45%" "$result" "Emoji mode context shows percentage"

    # Test cost component
    result=$(get_cost_component "0.123")
    assert_contains "💰" "$result" "Emoji mode cost has money emoji"
    assert_contains "\$0.123" "$result" "Emoji mode cost shows dollar amount"

    # Test lines component
    result=$(get_lines_component 10 5)
    assert_contains "📝" "$result" "Emoji mode lines has pencil emoji"
    assert_contains "+10" "$result" "Emoji mode lines shows additions"

    # Cleanup
    unset STATUSLINE_DISPLAY_MODE
}

# Test text mode components
test_text_mode_components() {
    echo "Testing text mode components..."

    # Enable text mode via environment variable
    unset STATUSLINE_TEXT_MODE
    export STATUSLINE_DISPLAY_MODE=text

    local result

    # Test model component in text mode
    result=$(get_model_component "Opus")
    assert_contains "Mod: " "$result" "Text mode model uses 'Mod: ' prefix"
    assert_not_contains "🤖" "$result" "Text mode model has no emoji"
    assert_contains "Opus" "$result" "Text mode model shows name"

    # Test directory component in text mode
    result=$(get_directory_component "/home/user/projects")
    assert_contains "Dir: " "$result" "Text mode directory uses 'Dir: ' prefix"
    assert_not_contains "📁" "$result" "Text mode directory has no emoji"

    # Test context component in text mode
    result=$(get_context_component 45)
    assert_contains "Ctx: " "$result" "Text mode context uses 'Ctx: ' prefix"
    assert_contains "45%" "$result" "Text mode context shows percentage"
    assert_not_contains "📊" "$result" "Text mode context has no emoji"

    # Test cost component in text mode (no prefix, just $)
    result=$(get_cost_component "0.123")
    assert_contains "\$0.123" "$result" "Text mode cost shows dollar amount"
    assert_not_contains "💰" "$result" "Text mode cost has no emoji"

    # Test lines component in text mode
    result=$(get_lines_component 10 5)
    assert_contains "Δ " "$result" "Text mode lines uses delta symbol"
    assert_contains "+10" "$result" "Text mode lines shows additions"
    assert_not_contains "📝" "$result" "Text mode lines has no emoji"

    # Disable text mode
    unset STATUSLINE_DISPLAY_MODE
}

# Test text mode environment variable toggle (legacy support)
test_text_mode_toggle() {
    echo "Testing text mode toggle (legacy env var)..."

    local result

    # Start with emoji mode (explicit)
    unset STATUSLINE_TEXT_MODE
    export STATUSLINE_DISPLAY_MODE=emoji
    result=$(get_model_component "Opus")
    assert_contains "🤖" "$result" "Explicit emoji mode works"

    # Switch to text mode using legacy env var
    unset STATUSLINE_DISPLAY_MODE
    export STATUSLINE_TEXT_MODE=true
    result=$(get_model_component "Opus")
    assert_contains "Mod: " "$result" "STATUSLINE_TEXT_MODE=true enables text mode"
    assert_not_contains "🤖" "$result" "Text mode has no emoji"

    # Test with "1" value
    export STATUSLINE_TEXT_MODE=1
    result=$(get_model_component "Opus")
    assert_contains "Mod: " "$result" "STATUSLINE_TEXT_MODE=1 also enables text mode"

    # Switch back to emoji mode (explicit)
    unset STATUSLINE_TEXT_MODE
    export STATUSLINE_DISPLAY_MODE=emoji
    result=$(get_model_component "Opus")
    assert_contains "🤖" "$result" "Explicit emoji mode restores emoji"

    # Cleanup
    unset STATUSLINE_DISPLAY_MODE
}

# Test get_prefix helper function
test_get_prefix_helper() {
    echo "Testing get_prefix helper..."

    local result

    # Test emoji mode (explicit)
    unset STATUSLINE_TEXT_MODE
    export STATUSLINE_DISPLAY_MODE=emoji
    result=$(get_prefix "🤖" "Mod:" "[M]")
    assert_equals "🤖 " "$result" "get_prefix returns emoji in emoji mode"

    # Test text mode (legacy env var)
    unset STATUSLINE_DISPLAY_MODE
    export STATUSLINE_TEXT_MODE=true
    result=$(get_prefix "🤖" "Mod:" "[M]")
    assert_equals "Mod: " "$result" "get_prefix returns text in text mode (legacy)"
    unset STATUSLINE_TEXT_MODE

    # Test text mode (new env var)
    export STATUSLINE_DISPLAY_MODE=text
    result=$(get_prefix "🤖" "Mod:" "[M]")
    assert_equals "Mod: " "$result" "get_prefix returns text with STATUSLINE_DISPLAY_MODE=text"

    # Test ascii mode
    export STATUSLINE_DISPLAY_MODE=ascii
    result=$(get_prefix "🤖" "Mod:" "[M]")
    assert_equals "[M] " "$result" "get_prefix returns ascii with STATUSLINE_DISPLAY_MODE=ascii"

    unset STATUSLINE_DISPLAY_MODE
}

# Test session duration component
test_session_component_text_mode() {
    echo "Testing session duration in text mode..."

    # Create mock JSON with duration
    local mock_json='{"cost":{"total_duration_ms":65000}}'

    # Test emoji mode (explicit)
    unset STATUSLINE_TEXT_MODE
    export STATUSLINE_DISPLAY_MODE=emoji
    local result
    result=$(get_session_component "$mock_json")
    assert_contains "⏱️" "$result" "Emoji mode duration has clock emoji"
    assert_contains "1m" "$result" "Duration shows 1 minute"

    # Test text mode (no prefix for duration)
    export STATUSLINE_DISPLAY_MODE=text
    result=$(get_session_component "$mock_json")
    assert_not_contains "⏱️" "$result" "Text mode duration has no emoji"
    assert_contains "1m" "$result" "Text mode duration shows time"

    # Test ascii mode (no prefix for duration)
    export STATUSLINE_DISPLAY_MODE=ascii
    result=$(get_session_component "$mock_json")
    assert_not_contains "⏱️" "$result" "ASCII mode duration has no emoji"
    assert_contains "1m" "$result" "ASCII mode duration shows time"

    unset STATUSLINE_DISPLAY_MODE
}

# Test ASCII mode components
test_ascii_mode_components() {
    echo "Testing ASCII mode components..."

    # Enable ascii mode via environment variable
    export STATUSLINE_DISPLAY_MODE=ascii

    local result

    # Test model component in ascii mode
    result=$(get_model_component "Opus")
    assert_contains "[M] " "$result" "ASCII mode model uses '[M] ' prefix"
    assert_not_contains "🤖" "$result" "ASCII mode model has no emoji"
    assert_not_contains "Mod:" "$result" "ASCII mode model doesn't use text prefix"
    assert_contains "Opus" "$result" "ASCII mode model shows name"

    # Test directory component in ascii mode
    result=$(get_directory_component "/home/user/projects")
    assert_contains "[D] " "$result" "ASCII mode directory uses '[D] ' prefix"
    assert_not_contains "📁" "$result" "ASCII mode directory has no emoji"
    assert_not_contains "Dir:" "$result" "ASCII mode directory doesn't use text prefix"

    # Test context component in ascii mode
    result=$(get_context_component 45)
    assert_contains "[C] " "$result" "ASCII mode context uses '[C] ' prefix"
    assert_contains "45%" "$result" "ASCII mode context shows percentage"
    assert_not_contains "📊" "$result" "ASCII mode context has no emoji"
    assert_not_contains "Ctx:" "$result" "ASCII mode context doesn't use text prefix"

    # Test cost component in ascii mode (no prefix, just $)
    result=$(get_cost_component "0.123")
    assert_contains "\$0.123" "$result" "ASCII mode cost shows dollar amount"
    assert_not_contains "💰" "$result" "ASCII mode cost has no emoji"

    # Test lines component in ascii mode
    result=$(get_lines_component 10 5)
    assert_contains "+/- " "$result" "ASCII mode lines uses '+/- ' prefix"
    assert_contains "+10" "$result" "ASCII mode lines shows additions"
    assert_not_contains "📝" "$result" "ASCII mode lines has no emoji"
    assert_not_contains "Δ" "$result" "ASCII mode lines doesn't use delta symbol"

    # Disable ascii mode
    unset STATUSLINE_DISPLAY_MODE
}

# Test display mode environment variable toggle
test_display_mode_toggle() {
    echo "Testing display mode toggle..."

    local result

    # Start with emoji mode (explicit - config may have different default)
    unset STATUSLINE_TEXT_MODE
    export STATUSLINE_DISPLAY_MODE=emoji
    result=$(get_model_component "Opus")
    assert_contains "🤖" "$result" "Explicit emoji mode works"

    # Switch to text mode
    export STATUSLINE_DISPLAY_MODE=text
    result=$(get_model_component "Opus")
    assert_contains "Mod: " "$result" "STATUSLINE_DISPLAY_MODE=text enables text mode"
    assert_not_contains "🤖" "$result" "Text mode has no emoji"

    # Switch to ascii mode
    export STATUSLINE_DISPLAY_MODE=ascii
    result=$(get_model_component "Opus")
    assert_contains "[M] " "$result" "STATUSLINE_DISPLAY_MODE=ascii enables ascii mode"
    assert_not_contains "🤖" "$result" "ASCII mode has no emoji"
    assert_not_contains "Mod:" "$result" "ASCII mode doesn't use text prefix"

    # Switch back to emoji mode explicitly
    export STATUSLINE_DISPLAY_MODE=emoji
    result=$(get_model_component "Opus")
    assert_contains "🤖" "$result" "STATUSLINE_DISPLAY_MODE=emoji restores emoji mode"

    # Cleanup
    unset STATUSLINE_DISPLAY_MODE
}

# Test git dirty indicator spacing
test_git_dirty_spacing() {
    echo "Testing git dirty indicator spacing..."

    # This test requires mocking get_git_info, so we test the pattern indirectly
    # by checking that text and ascii mode have different indicators

    local result

    # The space before ● should be present in emoji and text modes
    # ASCII mode should use " *" instead

    # Test with explicit emoji mode first
    export STATUSLINE_DISPLAY_MODE=emoji
    unset STATUSLINE_TEXT_MODE

    # Note: We can't easily test this without mocking git, but we can test
    # that the is_ascii_mode function works correctly
    if is_ascii_mode; then
        echo "❌ FAIL: is_ascii_mode should be false in emoji mode"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    else
        echo "✅ PASS: is_ascii_mode is false in emoji mode"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    fi
    TESTS_RUN=$((TESTS_RUN + 1))

    export STATUSLINE_DISPLAY_MODE=ascii
    if is_ascii_mode; then
        echo "✅ PASS: is_ascii_mode is true when STATUSLINE_DISPLAY_MODE=ascii"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: is_ascii_mode should be true when STATUSLINE_DISPLAY_MODE=ascii"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    TESTS_RUN=$((TESTS_RUN + 1))

    unset STATUSLINE_DISPLAY_MODE
}

# Run all tests
main() {
    echo "Running Display Components Module Tests..."
    echo

    test_emoji_mode_components
    test_text_mode_components
    test_ascii_mode_components
    test_text_mode_toggle
    test_display_mode_toggle
    test_get_prefix_helper
    test_session_component_text_mode
    test_git_dirty_spacing

    print_results "Display Components Tests"
}

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
