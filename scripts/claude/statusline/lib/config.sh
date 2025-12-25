#!/bin/bash
# Configuration management

# Prevent multiple sourcing
if [[ -n "${CONFIG_LOADED:-}" ]]; then
    return 0
fi
readonly CONFIG_LOADED=1

readonly CONFIG_DIR="$HOME/.claude/claude_dump"
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
      "lines_changed",
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
