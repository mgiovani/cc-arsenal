#!/bin/bash
# =============================================================================
# Color Definitions - ANSI color codes and utility functions
# =============================================================================
# Provides consistent color theming across the statusline components.

# Guard clause - prevent multiple sourcing
if [[ -n "${STATUSLINE_COLORS_LOADED:-}" ]]; then
    return 0
fi
readonly STATUSLINE_COLORS_LOADED=1

# =============================================================================
# ANSI Color Codes
# =============================================================================

# Base colors
readonly STATUSLINE_RED='\033[31m'
readonly STATUSLINE_GREEN='\033[32m'
readonly STATUSLINE_YELLOW='\033[33m'
readonly STATUSLINE_BLUE='\033[34m'
readonly STATUSLINE_MAGENTA='\033[35m'
readonly STATUSLINE_CYAN='\033[36m'
readonly STATUSLINE_WHITE='\033[37m'
readonly STATUSLINE_GRAY='\033[90m'

# Modifiers
readonly STATUSLINE_DIM='\033[2m'
readonly STATUSLINE_BOLD='\033[1m'

# Bright colors
readonly STATUSLINE_BRIGHT_GREEN='\033[92m'
readonly STATUSLINE_BRIGHT_YELLOW='\033[93m'
readonly STATUSLINE_BRIGHT_BLUE='\033[94m'
readonly STATUSLINE_BRIGHT_MAGENTA='\033[95m'
readonly STATUSLINE_BRIGHT_CYAN='\033[96m'
readonly STATUSLINE_BRIGHT_PURPLE='\033[95m'

# Reset
readonly STATUSLINE_RESET='\033[0m'

# =============================================================================
# Color Utility Functions
# =============================================================================

# Wrap text in color codes
# Usage: colorize "$STATUSLINE_RED" "text"
colorize() {
    local color="$1"
    local text="$2"
    echo -e "${color}${text}${STATUSLINE_RESET}"
}

# Get color based on context percentage
# Usage: get_context_color 75
get_context_color() {
    local percent="$1"

    if [[ ! "$percent" =~ ^[0-9]+$ ]]; then
        echo "$STATUSLINE_GRAY"
        return
    fi

    if [[ $percent -lt 50 ]]; then
        echo "$STATUSLINE_GREEN"
    elif [[ $percent -lt 80 ]]; then
        echo "$STATUSLINE_YELLOW"
    else
        echo "$STATUSLINE_RED"
    fi
}

# Get color based on reset time remaining
# Usage: get_reset_color "2h30m"
get_reset_color() {
    local time_str="$1"

    if [[ "$time_str" =~ ^0h ]]; then
        echo "$STATUSLINE_RED"
    elif [[ "$time_str" =~ ^1h ]]; then
        echo "$STATUSLINE_YELLOW"
    else
        echo "$STATUSLINE_BLUE"
    fi
}

# Get color based on git status
# Usage: get_git_status_color "dirty"
get_git_status_color() {
    local status="$1"

    case "$status" in
        "clean") echo "$STATUSLINE_GREEN" ;;
        "dirty") echo "$STATUSLINE_YELLOW" ;;
        "ahead") echo "$STATUSLINE_BLUE" ;;
        "behind") echo "$STATUSLINE_CYAN" ;;
        "diverged") echo "$STATUSLINE_MAGENTA" ;;
        *) echo "$STATUSLINE_GRAY" ;;
    esac
}

# Get color based on usage percentage
# Usage: get_usage_color 45
get_usage_color() {
    local percent="$1"

    if [[ ! "$percent" =~ ^[0-9]+$ ]]; then
        echo "$STATUSLINE_GRAY"
        return
    fi

    if [[ $percent -lt 30 ]]; then
        echo "$STATUSLINE_GREEN"
    elif [[ $percent -lt 60 ]]; then
        echo "$STATUSLINE_BRIGHT_GREEN"
    elif [[ $percent -lt 80 ]]; then
        echo "$STATUSLINE_YELLOW"
    else
        echo "$STATUSLINE_RED"
    fi
}

# Get color based on cost
# Usage: get_cost_color "1.50"
get_cost_color() {
    local cost="$1"

    # Remove dollar sign if present
    cost="${cost#\$}"

    if [[ ! "$cost" =~ ^[0-9.]+$ ]]; then
        echo "$STATUSLINE_GRAY"
        return
    fi

    # Compare as integer (cost * 100)
    local cost_cents
    cost_cents=$(echo "$cost * 100" | bc 2>/dev/null || echo "0")
    cost_cents="${cost_cents%.*}"

    if [[ $cost_cents -lt 50 ]]; then
        echo "$STATUSLINE_GRAY"
    elif [[ $cost_cents -lt 200 ]]; then
        echo "$STATUSLINE_YELLOW"
    else
        echo "$STATUSLINE_BRIGHT_YELLOW"
    fi
}
