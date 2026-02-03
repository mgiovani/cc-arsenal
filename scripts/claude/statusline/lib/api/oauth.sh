#!/bin/bash
# =============================================================================
# OAuth API - Anthropic OAuth usage API integration
# =============================================================================
# Provides functions for retrieving usage limits and reset times from the
# Anthropic OAuth API. Supports cross-platform credential retrieval.

# Guard clause - prevent multiple sourcing
if [[ -n "${STATUSLINE_OAUTH_LOADED:-}" ]]; then
    return 0
fi
readonly STATUSLINE_OAUTH_LOADED=1

# Source dependencies
STATUSLINE_API_DIR="$(dirname "${BASH_SOURCE[0]}")"
source "$STATUSLINE_API_DIR/../core/platform.sh"
source "$STATUSLINE_API_DIR/../core/json.sh"
source "$STATUSLINE_API_DIR/../core/cache.sh"

# =============================================================================
# Configuration
# =============================================================================

# Cache for OAuth usage data
OAUTH_USAGE_CACHE_FILE="${OAUTH_USAGE_CACHE_FILE:-/tmp/claude_oauth_usage_cache.json}"
OAUTH_USAGE_CACHE_TTL="${OAUTH_USAGE_CACHE_TTL:-60}"  # 60 seconds cache TTL

# API endpoint
ANTHROPIC_OAUTH_USAGE_URL="https://api.anthropic.com/api/oauth/usage"

# =============================================================================
# Credential Retrieval
# =============================================================================

# Get OAuth credentials - cross-platform
# Tries: macOS Keychain -> Linux secret-tool -> File-based fallback
# Returns: JSON credentials or exits with 1 if not found
get_oauth_credentials() {
    local creds=""

    # Method 1: macOS Keychain
    if command -v security >/dev/null 2>&1; then
        creds=$(security find-generic-password -s "Claude Code-credentials" -w 2>/dev/null || echo "")
        if [[ -n "$creds" ]]; then
            echo "$creds"
            return 0
        fi
    fi

    # Method 2: Linux secret-tool (GNOME Keyring / libsecret)
    if command -v secret-tool >/dev/null 2>&1; then
        creds=$(secret-tool lookup service "Claude Code-credentials" 2>/dev/null || echo "")
        if [[ -n "$creds" ]]; then
            echo "$creds"
            return 0
        fi
    fi

    # Method 3: File-based credentials (Linux / fallback)
    # On Linux, Claude Code stores OAuth tokens in ~/.claude/.credentials.json
    local cred_files=(
        "$HOME/.claude/.credentials.json"
        "$HOME/.claude/credentials.json"
        "$HOME/.config/claude-code/credentials.json"
        "$HOME/.local/share/claude-code/credentials.json"
    )
    for cred_file in "${cred_files[@]}"; do
        if [[ -f "$cred_file" ]]; then
            creds=$(cat "$cred_file" 2>/dev/null || echo "")
            if [[ -n "$creds" ]]; then
                echo "$creds"
                return 0
            fi
        fi
    done

    return 1
}

# Extract access token from credentials JSON
# Usage: get_oauth_token "$credentials_json"
get_oauth_token() {
    local creds="$1"

    if ! check_jq; then
        return 1
    fi

    local token
    token=$(echo "$creds" | jq -r '.claudeAiOauth.accessToken // empty' 2>/dev/null)

    if [[ -z "$token" || "$token" == "null" ]]; then
        return 1
    fi

    echo "$token"
}

# =============================================================================
# API Operations
# =============================================================================

# Fetch usage data from cache ONLY (non-blocking, for statusline rendering)
# Returns: JSON from cache or empty if not cached
# This function NEVER makes network calls - use fetch_oauth_usage for background updates
fetch_oauth_usage_cached_only() {
    # Only read from cache, no network calls
    if [[ -f "$OAUTH_USAGE_CACHE_FILE" ]]; then
        cat "$OAUTH_USAGE_CACHE_FILE" 2>/dev/null
        return 0
    fi

    return 1
}

# Fetch usage data from Anthropic OAuth API
# Returns: JSON with five_hour and seven_day usage data
fetch_oauth_usage() {
    local current_time
    current_time=$(get_current_epoch)

    # Check cache first
    if [[ -f "$OAUTH_USAGE_CACHE_FILE" ]]; then
        local cache_mtime cache_age
        cache_mtime=$(get_file_mtime "$OAUTH_USAGE_CACHE_FILE")
        cache_age=$((current_time - cache_mtime))
        if [[ "$cache_age" -lt "$OAUTH_USAGE_CACHE_TTL" ]]; then
            cat "$OAUTH_USAGE_CACHE_FILE" 2>/dev/null
            return 0
        fi
    fi

    # Get OAuth credentials (cross-platform)
    local creds token
    creds=$(get_oauth_credentials)
    if [[ -z "$creds" ]]; then
        return 1
    fi

    # Extract access token
    token=$(get_oauth_token "$creds")
    if [[ -z "$token" ]]; then
        return 1
    fi

    # Call the OAuth usage API
    local response
    response=$(curl -s --max-time 5 "$ANTHROPIC_OAUTH_USAGE_URL" \
        -H "Accept: application/json, text/plain, */*" \
        -H "Content-Type: application/json" \
        -H "User-Agent: claude-code/2.0.67" \
        -H "Authorization: Bearer $token" \
        -H "anthropic-beta: oauth-2025-04-20" 2>/dev/null)

    # Validate response and cache
    if [[ -n "$response" ]] && echo "$response" | jq -e '.five_hour' >/dev/null 2>&1; then
        echo "$response" > "$OAUTH_USAGE_CACHE_FILE" 2>/dev/null
        echo "$response"
        return 0
    fi

    return 1
}

# =============================================================================
# Usage Data Extraction
# =============================================================================

# Get five-hour usage info from OAuth API
# Returns: "utilization|resets_at_epoch" or exits with 1 if unavailable
get_oauth_five_hour_usage() {
    local usage_json
    usage_json=$(fetch_oauth_usage 2>/dev/null)

    if [[ -z "$usage_json" ]]; then
        return 1
    fi

    local utilization resets_at resets_at_epoch
    utilization=$(echo "$usage_json" | jq -r '.five_hour.utilization // empty' 2>/dev/null)
    resets_at=$(echo "$usage_json" | jq -r '.five_hour.resets_at // empty' 2>/dev/null)

    if [[ -z "$utilization" || -z "$resets_at" || "$resets_at" == "null" ]]; then
        return 1
    fi

    # Parse the ISO 8601 timestamp to epoch
    # Format: "2025-12-13T01:59:59.874295+00:00"
    local clean_ts
    clean_ts="${resets_at%.*}"  # Remove fractional seconds
    clean_ts="${clean_ts%+*}"   # Remove timezone offset (treat as UTC)

    resets_at_epoch=$(parse_iso_timestamp "$clean_ts")

    if [[ "$resets_at_epoch" -gt 0 ]]; then
        echo "${utilization}|${resets_at_epoch}"
        return 0
    fi

    return 1
}

# Get seven-day usage info from OAuth API
# Returns: "utilization|resets_at_epoch" or exits with 1 if unavailable
get_oauth_seven_day_usage() {
    local usage_json
    usage_json=$(fetch_oauth_usage 2>/dev/null)

    if [[ -z "$usage_json" ]]; then
        return 1
    fi

    local utilization resets_at resets_at_epoch
    utilization=$(echo "$usage_json" | jq -r '.seven_day.utilization // empty' 2>/dev/null)
    resets_at=$(echo "$usage_json" | jq -r '.seven_day.resets_at // empty' 2>/dev/null)

    if [[ -z "$utilization" || -z "$resets_at" || "$resets_at" == "null" ]]; then
        return 1
    fi

    # Parse the ISO 8601 timestamp to epoch
    local clean_ts
    clean_ts="${resets_at%.*}"
    clean_ts="${clean_ts%+*}"

    resets_at_epoch=$(parse_iso_timestamp "$clean_ts")

    if [[ "$resets_at_epoch" -gt 0 ]]; then
        echo "${utilization}|${resets_at_epoch}"
        return 0
    fi

    return 1
}

# Get full usage data parsed
# Returns: JSON-like string with parsed data or empty
get_oauth_usage_parsed() {
    local usage_json
    usage_json=$(fetch_oauth_usage 2>/dev/null)

    if [[ -z "$usage_json" ]]; then
        return 1
    fi

    if check_jq; then
        echo "$usage_json" | jq -c '{
            five_hour: {
                utilization: .five_hour.utilization,
                resets_at: .five_hour.resets_at
            },
            seven_day: {
                utilization: .seven_day.utilization,
                resets_at: .seven_day.resets_at
            }
        }' 2>/dev/null
    else
        echo "$usage_json"
    fi
}

# =============================================================================
# Utility Functions
# =============================================================================

# Check if OAuth credentials are available
# Returns: 0 if available, 1 otherwise
has_oauth_credentials() {
    local creds
    creds=$(get_oauth_credentials 2>/dev/null)
    [[ -n "$creds" ]]
}

# Clear OAuth usage cache
clear_oauth_cache() {
    rm -f "$OAUTH_USAGE_CACHE_FILE" 2>/dev/null || true
}

# Get OAuth cache age in seconds
# Returns: age in seconds or -1 if not cached
get_oauth_cache_age() {
    if [[ -f "$OAUTH_USAGE_CACHE_FILE" ]]; then
        local cache_time current_time
        cache_time=$(get_file_mtime "$OAUTH_USAGE_CACHE_FILE")
        current_time=$(get_current_epoch)
        echo $((current_time - cache_time))
    else
        echo "-1"
    fi
}

# =============================================================================
# Extra Model-Specific Limits
# =============================================================================

# Get all extra model-specific limits (non-null seven_day_* fields)
# Returns: pipe-separated list of "name|utilization|resets_at" entries, one per line
# Supported fields: seven_day_sonnet, seven_day_opus, seven_day_oauth_apps, seven_day_cowork
get_oauth_extra_limits() {
    local usage_json
    usage_json=$(fetch_oauth_usage 2>/dev/null)

    if [[ -z "$usage_json" ]] || ! check_jq; then
        return 1
    fi

    # Extract all seven_day_* fields (excluding base seven_day) that have non-null utilization
    # Output format: name|utilization|resets_at per line
    echo "$usage_json" | jq -r '
        to_entries
        | map(select(.key | startswith("seven_day_")))
        | map(select(.value != null and .value.utilization != null))
        | map(
            (.key | sub("seven_day_"; "") | split("_") | map((.[0:1] | ascii_upcase) + .[1:]) | join(" "))
            + "|" +
            (.value.utilization | tostring)
            + "|" +
            (.value.resets_at // "")
          )
        | .[]
    ' 2>/dev/null
}
