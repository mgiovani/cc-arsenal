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

# =============================================================================
# Daemon Auto-Start (Non-blocking)
# =============================================================================

# Auto-start daemon if not running (flock-based singleton ensures no duplicates)
if [[ -f "$SCRIPT_DIR/statusline_daemon.sh" ]]; then
    "$SCRIPT_DIR/statusline_daemon.sh" autostart >/dev/null 2>&1 &
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
    if check_jq && echo "$json" | jq -e '.rate_limits.five_hour' >/dev/null 2>&1; then
        echo "$json" | jq -c '.rate_limits // empty' > /tmp/claude_rate_limits_cache.json 2>/dev/null || true
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
