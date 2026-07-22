#!/bin/bash
# Configuration management

# Prevent multiple sourcing
if [[ -n "${CONFIG_LOADED:-}" ]]; then
    return 0
fi
readonly CONFIG_LOADED=1

readonly CONFIG_DIR="$HOME/.claude/cc-arsenal"
readonly CONFIG_FILE="$CONFIG_DIR/statusline_config.json"

# Default configuration
get_default_config() {
    cat <<'EOF'
{
  "components": {
    "order": [
      "model",
      "directory",
      "git",
      "context",
      "session_cost",
      "daily_cost",
      "duration_info",
      "reset_countdown"
    ],
    "enabled": {
      "model": true,
      "directory": true,
      "git": true,
      "context": true,
      "session_cost": true,
      "daily_cost": true,
      "reset_countdown": true,
      "duration_info": false,
      "lines_changed": false
    }
  },
  "display": {
    "display_mode": "emoji",
    "separator": " │ ",
    "compact_separator": "│",
    "max_width": 120,
    "compact_threshold": 80
  },
  "formatting": {
    "directory_max_length": 25,
    "git_branch_max_length": 15,
    "cost_decimal_places": 3,
    "daily_cost_decimal_places": 2
  }
}
EOF
}

# Initialize config file
setup_config() {
    # Use override config if provided (for preview functionality)
    if [[ -n "${STATUSLINE_CONFIG_OVERRIDE:-}" && -f "${STATUSLINE_CONFIG_OVERRIDE:-}" ]]; then
        readonly ACTIVE_CONFIG_FILE="$STATUSLINE_CONFIG_OVERRIDE"
        return
    fi

    readonly ACTIVE_CONFIG_FILE="$CONFIG_FILE"
    mkdir -p "$CONFIG_DIR"
    if [[ ! -f "$CONFIG_FILE" ]]; then
        get_default_config > "$CONFIG_FILE"
    fi
}

# Get config value
get_config() {
    local key="$1"
    local default="$2"

    local config_file="${ACTIVE_CONFIG_FILE:-$CONFIG_FILE}"

    if [[ -f "$config_file" ]]; then
        jq -r "$key // \"$default\"" "$config_file" 2>/dev/null || echo "$default"
    else
        echo "$default"
    fi
}

# Get boolean config value
get_config_bool() {
    local key="$1"
    local default="$2"

    local config_file="${ACTIVE_CONFIG_FILE:-$CONFIG_FILE}"

    if [[ -f "$config_file" ]]; then
        local value
        value=$(jq -r "$key // $default" "$config_file" 2>/dev/null || echo "$default")
        [[ "$value" == "true" ]] && echo "true" || echo "false"
    else
        echo "$default"
    fi
}

# Get display mode (emoji, text, or ascii)
# Checks environment override first, then config
# Usage: mode=$(get_display_mode)
get_display_mode() {
    # Environment variable override takes precedence
    if [[ -n "${STATUSLINE_DISPLAY_MODE:-}" ]]; then
        echo "$STATUSLINE_DISPLAY_MODE"
        return
    fi

    # Legacy environment variable support
    if [[ -n "${STATUSLINE_TEXT_MODE:-}" ]]; then
        if [[ "$STATUSLINE_TEXT_MODE" == "true" || "$STATUSLINE_TEXT_MODE" == "1" ]]; then
            echo "text"
            return
        fi
    fi

    # Check config setting (new display_mode or legacy text_mode)
    local display_mode
    display_mode=$(get_config ".display.display_mode" "")

    if [[ -n "$display_mode" && "$display_mode" != "null" ]]; then
        echo "$display_mode"
        return
    fi

    # Legacy fallback: check text_mode boolean
    local text_mode
    text_mode=$(get_config_bool ".display.text_mode" "false")
    if [[ "$text_mode" == "true" ]]; then
        echo "text"
    else
        echo "emoji"
    fi
}

# Check if text mode is enabled (via config or environment override)
# Usage: if is_text_mode; then ... fi
is_text_mode() {
    [[ "$(get_display_mode)" == "text" ]]
}

# Check if ascii mode is enabled
# Usage: if is_ascii_mode; then ... fi
is_ascii_mode() {
    [[ "$(get_display_mode)" == "ascii" ]]
}

# Check if emoji mode is enabled (default)
# Usage: if is_emoji_mode; then ... fi
is_emoji_mode() {
    local mode
    mode=$(get_display_mode)
    [[ "$mode" == "emoji" || -z "$mode" ]]
}
