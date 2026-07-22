#!/bin/bash
# =============================================================================
# Tests for multi-account OAuth support (token precedence, cache-key isolation,
# rate-limit backoff, and rendering) across oauth.sh / oauth_fetcher.sh /
# statusline.sh
# =============================================================================

# Test environment setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$(cd "$SCRIPT_DIR/../lib" && pwd)"
STATUSLINE_SH="$SCRIPT_DIR/../statusline.sh"

# Only for computing expected hashes in assertions - never sourced again
# inside a subshell (that would let its guard clause skip re-derivation)
source "$LIB_DIR/core/platform.sh"

# Shared assert helpers (assert_equals, assert_not_equals, assert_matches,
# assert_contains, assert_not_contains, assert_file_exists, assert_file_absent,
# print_results, ...)
source "$SCRIPT_DIR/lib/assert.sh"

# =============================================================================
# Isolated scratch space + mock command shims
# =============================================================================

MA_TMP_DIR="/tmp/statusline_ma_test_$$"
MOCK_MARKER_DIR="$MA_TMP_DIR/markers"
MOCK_BIN_DIR="$MA_TMP_DIR/bin"
export MOCK_MARKER_DIR

# Dummy tokens embed $$ so their derived per-account state files never
# collide with another concurrent test run
TOK_A="acctA-$$"
TOK_B="acctB-$$"
TOK_RL="acctRL-$$"
TOK_RENDER="acctRender-$$"
TOK_FETCH="acctFetch-$$"

cleanup() {
    rm -rf "$MA_TMP_DIR" 2>/dev/null || true

    local tok hash
    for tok in "$TOK_A" "$TOK_B" "$TOK_RL" "$TOK_RENDER" "$TOK_FETCH"; do
        hash=$(hash_sha256 "$tok")
        rm -f "/tmp/claude_oauth_usage_cache.${hash}.json" 2>/dev/null || true
        rm -f "/tmp/claude_rate_limits_cache.${hash}.json" 2>/dev/null || true
        rm -f "/tmp/statusline_live_cache/oauth_backoff.${hash}" 2>/dev/null || true
        rm -f "/tmp/statusline_live_cache/oauth_backoff_count.${hash}" 2>/dev/null || true
        rm -f "/tmp/statusline_live_cache/oauth_cache.lock.${hash}" 2>/dev/null || true
    done
}
trap cleanup EXIT

setup_mocks() {
    mkdir -p "$MOCK_BIN_DIR" "$MOCK_MARKER_DIR"

    cat > "$MOCK_BIN_DIR/curl" <<'EOF'
#!/bin/bash
touch "$MOCK_MARKER_DIR/curl_called" 2>/dev/null || true
if [[ -n "${MOCK_CURL_BODY:-}" ]]; then
    printf '%s' "$MOCK_CURL_BODY"
fi
exit "${MOCK_CURL_EXIT:-0}"
EOF

    cat > "$MOCK_BIN_DIR/security" <<'EOF'
#!/bin/bash
touch "$MOCK_MARKER_DIR/security_called" 2>/dev/null || true
if [[ -n "${MOCK_CREDS_JSON:-}" ]]; then
    printf '%s' "$MOCK_CREDS_JSON"
    exit 0
fi
exit 1
EOF

    cat > "$MOCK_BIN_DIR/secret-tool" <<'EOF'
#!/bin/bash
touch "$MOCK_MARKER_DIR/secret-tool_called" 2>/dev/null || true
if [[ -n "${MOCK_CREDS_JSON:-}" ]]; then
    printf '%s' "$MOCK_CREDS_JSON"
    exit 0
fi
exit 1
EOF

    chmod +x "$MOCK_BIN_DIR/curl" "$MOCK_BIN_DIR/security" "$MOCK_BIN_DIR/secret-tool"
}

reset_markers() {
    rm -f "$MOCK_MARKER_DIR"/curl_called "$MOCK_MARKER_DIR"/security_called "$MOCK_MARKER_DIR"/secret-tool_called
}

# =============================================================================
# Group 1: Token precedence
# =============================================================================
test_token_precedence() {
    echo "--- Testing token precedence ---"

    # Env var set: echoed directly, credential helpers never invoked
    reset_markers
    local result
    result=$( ( export PATH="$MOCK_BIN_DIR:$PATH"
                unset OAUTH_USAGE_CACHE_FILE MOCK_CREDS_JSON
                export CLAUDE_CODE_OAUTH_TOKEN="env-tok-$$"
                source "$LIB_DIR/api/oauth.sh"
                get_active_oauth_token ) 2>/dev/null )
    assert_equals "env-tok-$$" "$result" "get_active_oauth_token echoes env var when set"
    assert_file_absent "$MOCK_MARKER_DIR/security_called" "security not invoked when env var set"
    assert_file_absent "$MOCK_MARKER_DIR/secret-tool_called" "secret-tool not invoked when env var set"

    # Env var unset: falls through to stored credentials (JSON shape via jq)
    reset_markers
    result=$( ( export PATH="$MOCK_BIN_DIR:$PATH"
                unset CLAUDE_CODE_OAUTH_TOKEN OAUTH_USAGE_CACHE_FILE
                export MOCK_CREDS_JSON='{"claudeAiOauth":{"accessToken":"stored-tok"}}'
                source "$LIB_DIR/api/oauth.sh"
                get_active_oauth_token ) 2>/dev/null )
    assert_equals "stored-tok" "$result" "get_active_oauth_token falls back to stored credentials"
    assert_file_exists "$MOCK_MARKER_DIR/security_called" "security was invoked when env var unset"
}

# =============================================================================
# Group 2: Cache-key isolation
# =============================================================================
test_cache_key_isolation() {
    echo "--- Testing cache-key isolation ---"

    local result_a result_b result_unset
    result_a=$( ( unset OAUTH_USAGE_CACHE_FILE
                  export CLAUDE_CODE_OAUTH_TOKEN="$TOK_A"
                  source "$LIB_DIR/api/oauth.sh"
                  echo "$OAUTH_USAGE_CACHE_FILE" ) 2>/dev/null )
    result_b=$( ( unset OAUTH_USAGE_CACHE_FILE
                  export CLAUDE_CODE_OAUTH_TOKEN="$TOK_B"
                  source "$LIB_DIR/api/oauth.sh"
                  echo "$OAUTH_USAGE_CACHE_FILE" ) 2>/dev/null )
    result_unset=$( ( unset OAUTH_USAGE_CACHE_FILE CLAUDE_CODE_OAUTH_TOKEN
                      source "$LIB_DIR/api/oauth.sh"
                      echo "$OAUTH_USAGE_CACHE_FILE" ) 2>/dev/null )

    assert_not_equals "$result_a" "$result_b" "token A and B derive different cache paths"
    assert_not_equals "$result_a" "$result_unset" "token A differs from legacy unset path"
    assert_matches "$result_a" "^/tmp/claude_oauth_usage_cache\.[a-f0-9]{12}\.json$" "token A path shape is <hash>.json"
    assert_matches "$result_b" "^/tmp/claude_oauth_usage_cache\.[a-f0-9]{12}\.json$" "token B path shape is <hash>.json"
    assert_not_contains "$TOK_A" "$result_a" "token A path does not contain the raw token"
    assert_not_contains "$TOK_B" "$result_b" "token B path does not contain the raw token"
    assert_equals "/tmp/claude_oauth_usage_cache.json" "$result_unset" "unset token uses the legacy cache path"

    # Explicit override always wins over a set token
    local custom_path="$MA_TMP_DIR/custom_cache.json"
    local result_override
    result_override=$( ( export CLAUDE_CODE_OAUTH_TOKEN="$TOK_A"
                          export OAUTH_USAGE_CACHE_FILE="$custom_path"
                          source "$LIB_DIR/api/oauth.sh"
                          echo "$OAUTH_USAGE_CACHE_FILE" ) 2>/dev/null )
    assert_equals "$custom_path" "$result_override" "explicit OAUTH_USAGE_CACHE_FILE overrides a set token"

    # oauth_fetcher.sh's BACKOFF_FILE carries the same account hash
    local expected_hash backoff_result
    expected_hash=$(hash_sha256 "$TOK_A")
    backoff_result=$( ( unset OAUTH_USAGE_CACHE_FILE
                        export CLAUDE_CODE_OAUTH_TOKEN="$TOK_A"
                        source "$LIB_DIR/oauth_fetcher.sh"
                        echo "$BACKOFF_FILE" ) 2>/dev/null )
    assert_contains ".${expected_hash}" "$backoff_result" "oauth_fetcher BACKOFF_FILE carries the account hash suffix"
}

# =============================================================================
# Group 3: Rate-limit degradation
# =============================================================================
test_rate_limit_degradation() {
    echo "--- Testing rate-limit degradation ---"

    local hash="$(hash_sha256 "$TOK_RL")"
    local backoff_file="/tmp/statusline_live_cache/oauth_backoff.${hash}"
    local backoff_count_file="/tmp/statusline_live_cache/oauth_backoff_count.${hash}"
    local cache_file="/tmp/claude_oauth_usage_cache.${hash}.json"

    rm -f "$backoff_file" "$backoff_count_file" "$cache_file" 2>/dev/null || true

    local rc=0
    ( export PATH="$MOCK_BIN_DIR:$PATH"
      unset OAUTH_USAGE_CACHE_FILE
      export CLAUDE_CODE_OAUTH_TOKEN="$TOK_RL"
      export MOCK_CURL_BODY='{"type":"error","error":{"type":"rate_limit_error","message":"rate limited"}}'
      export MOCK_CURL_EXIT=0
      bash "$LIB_DIR/oauth_fetcher.sh" ) >/dev/null 2>&1 || rc=$?

    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ "$rc" -ne 0 ]]; then
        echo "✅ PASS: oauth_fetcher exits non-zero on rate-limit response"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: oauth_fetcher should exit non-zero on rate-limit response"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi

    assert_file_exists "$backoff_file" "backoff file created with account suffix"
    assert_file_exists "$backoff_count_file" "backoff count file created with account suffix"
    assert_file_absent "$cache_file" "cache file NOT created on rate-limit failure"
}

# =============================================================================
# Group 4: Fail-soft render
# =============================================================================
test_failsoft_render() {
    echo "--- Testing fail-soft render ---"

    local hash="$(hash_sha256 "$TOK_RENDER")"
    rm -f "/tmp/claude_oauth_usage_cache.${hash}.json" 2>/dev/null || true

    local future_epoch=4102444800
    local stdin_json='{"model":{"display_name":"Sonnet"},"workspace":{"current_dir":"/tmp"},"cost":{},"rate_limits":{"five_hour":{"used_percentage":42,"resets_at":'"$future_epoch"'}}}'

    # Token set, label unset, no cache present - stdin numbers still render, no badge
    local output
    output=$( ( export PATH="$MOCK_BIN_DIR:$PATH"
                unset OAUTH_USAGE_CACHE_FILE CLAUDE_STATUSLINE_ACCOUNT_LABEL
                export CLAUDE_CODE_OAUTH_TOKEN="$TOK_RENDER"
                echo "$stdin_json" | bash "$STATUSLINE_SH" ) 2>/dev/null )
    assert_contains "42%" "$output" "stdin 5h percentage renders with no cache present"
    assert_not_contains "👤" "$output" "no account badge when label is unset"

    # Token set AND label set - badge appears
    output=$( ( export PATH="$MOCK_BIN_DIR:$PATH"
                unset OAUTH_USAGE_CACHE_FILE
                export CLAUDE_CODE_OAUTH_TOKEN="$TOK_RENDER"
                export CLAUDE_STATUSLINE_ACCOUNT_LABEL="testacct"
                echo "$stdin_json" | bash "$STATUSLINE_SH" ) 2>/dev/null )
    assert_contains "testacct" "$output" "account badge renders when both token and label are set"

    # Label set, NO token - securestorage/alt-account switch (CLAUDE_SECURESTORAGE_CONFIG_DIR):
    # the badge is user-set display text and must render without CLAUDE_CODE_OAUTH_TOKEN
    output=$( ( export PATH="$MOCK_BIN_DIR:$PATH"
                unset OAUTH_USAGE_CACHE_FILE CLAUDE_CODE_OAUTH_TOKEN
                export CLAUDE_STATUSLINE_ACCOUNT_LABEL="altacct"
                echo "$stdin_json" | bash "$STATUSLINE_SH" ) 2>/dev/null )
    assert_contains "altacct" "$output" "account badge renders with label set but no token (securestorage switch)"

    # Both unset - default single-account rendering, no label
    output=$( ( unset OAUTH_USAGE_CACHE_FILE CLAUDE_CODE_OAUTH_TOKEN CLAUDE_STATUSLINE_ACCOUNT_LABEL
                echo "$stdin_json" | bash "$STATUSLINE_SH" ) 2>/dev/null )
    assert_contains "42%" "$output" "stdin numbers render with no account env set"
    assert_not_contains "testacct" "$output" "no label leaks when account env is fully unset"

    rm -f "/tmp/claude_oauth_usage_cache.${hash}.json" 2>/dev/null || true
}

# =============================================================================
# Group 5: Fetched-over-stdin
# =============================================================================
test_fetched_over_stdin() {
    echo "--- Testing fetched usage overrides stdin ---"

    local hash="$(hash_sha256 "$TOK_FETCH")"
    local cache_file="/tmp/claude_oauth_usage_cache.${hash}.json"
    local fetched_json='{"five_hour":{"utilization":77,"resets_at":"2099-01-01T00:00:00.000000+00:00"},"seven_day":{"utilization":55,"resets_at":"2099-01-02T00:00:00.000000+00:00"}}'
    printf '%s' "$fetched_json" > "$cache_file"

    local stdin_json='{"model":{"display_name":"Sonnet"},"workspace":{"current_dir":"/tmp"},"cost":{},"rate_limits":{"five_hour":{"used_percentage":13,"resets_at":4102444800}}}'

    local output
    output=$( ( export PATH="$MOCK_BIN_DIR:$PATH"
                unset OAUTH_USAGE_CACHE_FILE
                export CLAUDE_CODE_OAUTH_TOKEN="$TOK_FETCH"
                echo "$stdin_json" | bash "$STATUSLINE_SH" ) 2>/dev/null )

    assert_contains "77%" "$output" "fetched per-account usage renders"
    assert_not_contains "13%" "$output" "stdin usage is overridden, not rendered"

    # The render must also persist the fetched numbers (never the stdin ones)
    # to the per-account rate-limits file for external consumers (tmux)
    local tmux_file="/tmp/claude_rate_limits_cache.${hash}.json"
    assert_file_exists "$tmux_file" "per-account rate-limits file written for tmux"
    local tmux_content
    tmux_content=$(cat "$tmux_file" 2>/dev/null)
    assert_contains '"used_percentage":77' "$tmux_content" "tmux file carries fetched 5h percentage"
    assert_contains '"used_percentage":55' "$tmux_content" "tmux file carries fetched 7d percentage"
    assert_not_contains '13' "$tmux_content" "tmux file never carries stdin numbers"
    echo "$tmux_content" | jq -e '.five_hour.resets_at' >/dev/null 2>&1
    assert_equals "0" "$?" "tmux file is valid JSON with the stdin-compatible shape"

    rm -f "$cache_file" "$tmux_file" 2>/dev/null || true
}

# =============================================================================
# Run all tests
# =============================================================================
main() {
    echo "========================================"
    echo "Running Multi-Account Tests"
    echo "========================================"
    echo

    setup_mocks

    test_token_precedence
    echo
    test_cache_key_isolation
    echo
    test_rate_limit_degradation
    echo
    test_failsoft_render
    echo
    test_fetched_over_stdin

    print_results "Multi-Account Tests"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
