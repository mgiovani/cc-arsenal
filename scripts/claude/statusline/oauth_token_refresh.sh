#!/usr/bin/env bash
# =============================================================================
# OAuth Token Refresh - Manual token refresh for testing
# =============================================================================
# Exchanges the current refresh token for a new access+refresh token pair.
#
# !! WARNING !!
# Saving the new tokens will INVALIDATE Claude Code's current session because
# the old refresh token is one-time use. Claude Code will get a 401 and force
# a /login. Only use --force if you are prepared to re-authenticate.
#
# Usage:
#   ./oauth_token_refresh.sh           # Dry-run only (safe, no writes)
#   ./oauth_token_refresh.sh --force   # Actually refresh + save (will break session)
#   ./oauth_token_refresh.sh --status  # Show current token expiry + test endpoint
#
# Reference: https://github.com/anthropics/claude-code/issues/31021
#   Rate limits are per-access-token. A fresh token gets a fresh limit window.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# =============================================================================
# Configuration
# =============================================================================

ANTHROPIC_TOKEN_URL="https://console.anthropic.com/v1/oauth/token"
ANTHROPIC_CLIENT_ID="9d1c250a-e61b-44d9-88ed-5944d1962f5e"

CRED_FILES=(
    "$HOME/.claude/.credentials.json"
    "$HOME/.claude/credentials.json"
    "$HOME/.config/claude-code/credentials.json"
    "$HOME/.local/share/claude-code/credentials.json"
)

DRY_RUN=1  # Default: safe dry-run. Use --force to actually write tokens.

# =============================================================================
# Helpers
# =============================================================================

log()  { echo "[$(date '+%H:%M:%S')] $*"; }
ok()   { echo "[$(date '+%H:%M:%S')] OK: $*"; }
err()  { echo "[$(date '+%H:%M:%S')] ERROR: $*" >&2; }
die()  { err "$*"; exit 1; }

find_cred_file() {
    for f in "${CRED_FILES[@]}"; do
        [[ -f "$f" ]] && echo "$f" && return 0
    done
    return 1
}

# Read a field from credentials JSON using jq or python3 fallback
read_cred_field() {
    local file="$1" field="$2"
    if command -v jq >/dev/null 2>&1; then
        jq -r "$field // empty" "$file" 2>/dev/null
    else
        python3 -c "
import json, sys
d = json.load(open('$file'))
keys = '$field'.lstrip('.').split('.')
for k in keys:
    d = d.get(k, {}) if isinstance(d, dict) else {}
print(d if d else '', end='')
" 2>/dev/null
    fi
}

# Write updated tokens back to credentials file
write_tokens() {
    local file="$1" access_token="$2" refresh_token="$3" expires_in="$4"

    # expires_in is seconds from now; convert to epoch milliseconds
    local expires_at_ms
    expires_at_ms=$(( ($(date +%s) + expires_in) * 1000 ))

    if command -v jq >/dev/null 2>&1; then
        local tmp
        tmp=$(mktemp)
        jq --arg at "$access_token" \
          --arg rt "$refresh_token" \
          --argjson ea "$expires_at_ms" \
          '.claudeAiOauth.accessToken = $at
            | .claudeAiOauth.refreshToken = $rt
            | .claudeAiOauth.expiresAt = $ea' \
          "$file" > "$tmp" && mv "$tmp" "$file"
    else
        python3 - "$file" "$access_token" "$refresh_token" "$expires_at_ms" <<'PYEOF'
import json, sys
file, access_token, refresh_token, expires_at = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
with open(file) as f:
    d = json.load(f)
d['claudeAiOauth']['accessToken'] = access_token
d['claudeAiOauth']['refreshToken'] = refresh_token
d['claudeAiOauth']['expiresAt'] = expires_at
with open(file, 'w') as f:
    json.dump(d, f, indent=2)
    f.write('\n')
PYEOF
    fi
}

show_status() {
    local cred_file
    cred_file=$(find_cred_file) || die "No credentials file found"

    local expires_at_ms access_token_prefix
    expires_at_ms=$(read_cred_field "$cred_file" '.claudeAiOauth.expiresAt')
    access_token_prefix=$(read_cred_field "$cred_file" '.claudeAiOauth.accessToken' | cut -c1-20)

    if [[ -z "$expires_at_ms" ]]; then
        err "Could not read token expiry from $cred_file"
        exit 1
    fi

    local now_ms expires_in_s
    now_ms=$(( $(date +%s) * 1000 ))
    expires_in_s=$(( (expires_at_ms - now_ms) / 1000 ))

    log "Credentials file : $cred_file"
    log "Token prefix     : ${access_token_prefix}..."
    if [[ $expires_in_s -gt 0 ]]; then
        log "Token expires in : ${expires_in_s}s ($(( expires_in_s / 60 ))m)"
    else
        log "Token expired    : ${expires_in_s}s ago"
    fi

    # Test if endpoint is reachable with current token
    local access_token response
    access_token=$(read_cred_field "$cred_file" '.claudeAiOauth.accessToken')
    log "Testing /api/oauth/usage endpoint..."
    response=$(curl -s --max-time 5 "https://api.anthropic.com/api/oauth/usage" \
        -H "Authorization: Bearer $access_token" \
        -H "anthropic-beta: oauth-2025-04-20" 2>/dev/null || echo '{"error":"curl_failed"}')

    if echo "$response" | grep -q '"five_hour"'; then
        ok "Endpoint responding — five_hour utilization: $(echo "$response" | python3 -c "import json,sys; print(json.load(sys.stdin)['five_hour']['utilization'])" 2>/dev/null || echo '?')%"
    elif echo "$response" | grep -q '"rate_limit_error"'; then
        err "Endpoint rate limited (429) — token needs refresh"
    else
        err "Unexpected response: ${response:0:120}"
    fi
}

# =============================================================================
# Main Refresh Logic
# =============================================================================

do_refresh() {
    local cred_file
    cred_file=$(find_cred_file) || die "No credentials file found at ${CRED_FILES[*]}"
    log "Credentials file: $cred_file"

    local refresh_token
    refresh_token=$(read_cred_field "$cred_file" '.claudeAiOauth.refreshToken')
    [[ -n "$refresh_token" ]] || die "No refresh token found in $cred_file"
    log "Refresh token   : ${refresh_token:0:20}..."

    if [[ $DRY_RUN -eq 1 ]]; then
        log "[dry-run] Would POST to $ANTHROPIC_TOKEN_URL"
        log "[dry-run] Would save new tokens to $cred_file"
        return 0
    fi

    log "Calling token refresh endpoint..."
    local response http_code
    response=$(curl -s -w "\n%{http_code}" --max-time 15 \
        -X POST "$ANTHROPIC_TOKEN_URL" \
        -H "Content-Type: application/json" \
        -H "User-Agent: claude-code/2.0.67" \
        -d "{\"grant_type\":\"refresh_token\",\"refresh_token\":\"${refresh_token}\",\"client_id\":\"${ANTHROPIC_CLIENT_ID}\"}" \
        2>/dev/null) || die "curl failed (network error)"

    http_code=$(echo "$response" | tail -1)
    response=$(echo "$response" | head -n -1)

    if [[ "$http_code" != "200" ]]; then
        err "HTTP $http_code from token endpoint"
        err "Response: ${response:0:200}"
        exit 1
    fi

    # Parse new tokens
    local new_access new_refresh expires_in
    if command -v jq >/dev/null 2>&1; then
        new_access=$(echo "$response"  | jq -r '.access_token  // empty')
        new_refresh=$(echo "$response" | jq -r '.refresh_token // empty')
        expires_in=$(echo "$response"  | jq -r '.expires_in    // 3600')
    else
        new_access=$(python3  -c "import json,sys; print(json.loads(sys.argv[1]).get('access_token',''))"  "$response" 2>/dev/null)
        new_refresh=$(python3 -c "import json,sys; print(json.loads(sys.argv[1]).get('refresh_token',''))" "$response" 2>/dev/null)
        expires_in=$(python3  -c "import json,sys; print(json.loads(sys.argv[1]).get('expires_in',3600))"  "$response" 2>/dev/null)
    fi

    [[ -n "$new_access"  ]] || die "No access_token in response: ${response:0:200}"
    [[ -n "$new_refresh" ]] || die "No refresh_token in response (one-time use — already consumed!)"

    ok "New access token : ${new_access:0:20}..."
    ok "New refresh token: ${new_refresh:0:20}..."
    ok "Expires in       : ${expires_in}s ($(( expires_in / 60 ))m)"

    # Save immediately — refresh tokens are one-time use
    write_tokens "$cred_file" "$new_access" "$new_refresh" "$expires_in"
    ok "Saved to $cred_file"
    echo ""
    echo "  NOTE: Your current Claude Code session will get a 401 and require /login."
    echo ""

    # Also clear the oauth usage cache so fetcher uses new token immediately
    local cache_file="${OAUTH_USAGE_CACHE_FILE:-/tmp/claude_oauth_usage_cache.json}"
    rm -f "$cache_file" /tmp/statusline_live_cache/oauth_backoff /tmp/statusline_live_cache/oauth_backoff_count 2>/dev/null || true
    ok "Cleared usage cache and backoff state"

    # Quick smoke test with new token
    log "Smoke test with new token..."
    local test_response
    test_response=$(curl -s --max-time 5 "https://api.anthropic.com/api/oauth/usage" \
        -H "Authorization: Bearer $new_access" \
        -H "anthropic-beta: oauth-2025-04-20" 2>/dev/null || echo '{}')

    if echo "$test_response" | grep -q '"five_hour"'; then
        ok "Endpoint responding with fresh token"
    elif echo "$test_response" | grep -q '"rate_limit_error"'; then
        err "Still rate limited with new token — wait and try again"
    else
        err "Unexpected smoke test response: ${test_response:0:120}"
    fi
}

# =============================================================================
# Entry Point
# =============================================================================

case "${1:-}" in
    --force)    DRY_RUN=0; do_refresh ;;
    --status)   show_status ;;
    "")
        echo "WARNING: This will invalidate your active Claude Code session (forces /login)."
        echo "Running in dry-run mode by default. Use --force to actually save tokens."
        echo ""
        DRY_RUN=1; do_refresh
        ;;
    *)          echo "Usage: $0 [--force | --status]"; exit 1 ;;
esac
