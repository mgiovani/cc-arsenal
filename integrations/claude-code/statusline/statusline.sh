#!/bin/bash
# =============================================================================
# Claude Code Statusline - Ultra-fast statusline with modular architecture
# =============================================================================
# A professional statusline for Claude Code that displays model info, git
# status, context usage, costs, and API rate limit information.
#
# Architecture:
#   lib/core/      - Foundation modules (platform, json, cache)
#   lib/api/       - External integrations (oauth, git)
#   lib/tracking/  - Session and usage tracking
#   lib/display/   - UI components and builder
#
# Usage:
#   echo '{"model":{"id":"claude-opus"}}' | ./statusline.sh
#   ./statusline.sh  # Interactive mode with defaults

set -e  # Exit on error

# =============================================================================
# Script Location
# =============================================================================

SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"

# =============================================================================
# Source Libraries
# =============================================================================

# Core modules (foundation)
source "$SCRIPT_DIR/lib/core/platform.sh"
source "$SCRIPT_DIR/lib/core/json.sh"
source "$SCRIPT_DIR/lib/core/cache.sh"

# Configuration
if [[ -f "$SCRIPT_DIR/lib/config.sh" ]]; then
    source "$SCRIPT_DIR/lib/config.sh"
fi

# API modules
source "$SCRIPT_DIR/lib/api/git.sh"
source "$SCRIPT_DIR/lib/api/oauth.sh"

# Tracking modules
source "$SCRIPT_DIR/lib/tracking/session.sh"
source "$SCRIPT_DIR/lib/tracking/usage.sh"

# Display modules
source "$SCRIPT_DIR/lib/display/colors.sh"
source "$SCRIPT_DIR/lib/display/components.sh"
source "$SCRIPT_DIR/lib/display/builder.sh"

# =============================================================================
# Performance Monitoring
# =============================================================================

START_TIME=$(get_current_nanos)

# Setup cache cleanup on exit
cache_setup_cleanup

# Trigger a background OAuth usage refresh when the account cache is stale
# (fetcher handles its own locking/backoff; this just decides when to fire it)
if [[ -n "${CLAUDE_CODE_OAUTH_TOKEN:-}" ]] && [[ -f "$SCRIPT_DIR/lib/oauth_fetcher.sh" ]]; then
    OAUTH_CACHE_MTIME=$(get_file_mtime "$OAUTH_USAGE_CACHE_FILE")
    OAUTH_CACHE_AGE=$(( $(get_current_epoch) - OAUTH_CACHE_MTIME ))
    if [[ "$OAUTH_CACHE_AGE" -ge "$OAUTH_USAGE_CACHE_TTL" ]]; then
        "$SCRIPT_DIR/lib/oauth_fetcher.sh" >/dev/null 2>&1 &
    fi
fi

# =============================================================================
# Main Function
# =============================================================================

main() {
    local json=""

    # Read input: from stdin if piped, otherwise use defaults
    if [[ -t 0 ]]; then
        # Interactive mode - create minimal JSON
        json='{"model":{},"workspace":{"current_dir":"'"${PWD}"'"},"cost":{}}'
    else
        # Piped input - read JSON from stdin
        json=$(cat 2>/dev/null || echo '{}')
    fi

    # Get current directory from JSON or fallback to PWD
    local current_dir
    current_dir=$(extract_json "$json" "workspace.current_dir" 2>/dev/null || echo "$PWD")

    # Build and output statusline
    build_statusline "$json" "$current_dir"

    # Persist rate_limits to cache file for external consumers (e.g., tmux statusbar)
    if [[ -z "${CLAUDE_CODE_OAUTH_TOKEN:-}" ]]; then
        if check_jq && echo "$json" | jq -e '.rate_limits.five_hour' >/dev/null 2>&1; then
            echo "$json" | jq -c '.rate_limits // empty' > /tmp/claude_rate_limits_cache.json 2>/dev/null || true
        fi
    else
        local acct
        acct=$(hash_sha256 "$CLAUDE_CODE_OAUTH_TOKEN")

        local five_hour_usage seven_day_usage
        if fetch_oauth_usage_cached_only >/dev/null 2>&1 && \
           five_hour_usage=$(get_oauth_five_hour_usage 2>/dev/null) && [[ -n "$five_hour_usage" ]] && \
           seven_day_usage=$(get_oauth_seven_day_usage 2>/dev/null) && [[ -n "$seven_day_usage" ]]; then
            local five_hour_pct five_hour_resets seven_day_pct seven_day_resets
            five_hour_pct="${five_hour_usage%%|*}"
            five_hour_resets="${five_hour_usage##*|}"
            seven_day_pct="${seven_day_usage%%|*}"
            seven_day_resets="${seven_day_usage##*|}"

            printf '{"five_hour":{"used_percentage":%s,"resets_at":%s},"seven_day":{"used_percentage":%s,"resets_at":%s}}' \
                "$five_hour_pct" "$five_hour_resets" "$seven_day_pct" "$seven_day_resets" \
                > "/tmp/claude_rate_limits_cache.${acct}.json" 2>/dev/null || true
        fi
    fi

    # Performance monitoring (optional)
    if [[ "${STATUSLINE_PERF:-0}" == "1" ]]; then
        local end_time duration_ms
        end_time=$(get_current_nanos)
        duration_ms=$(( (end_time - START_TIME) / 1000000 ))
        echo "[perf] ${duration_ms}ms" >&2
    fi
}

# =============================================================================
# Execute
# =============================================================================

main "$@" 2>/dev/null || {
    # Ultimate fallback - show minimal statusline
    build_minimal_statusline 2>/dev/null || \
    echo "🤖 Claude │ 📁 $(basename "$PWD") │ 🌿 $(git symbolic-ref --short HEAD 2>/dev/null || echo "main")"
}
