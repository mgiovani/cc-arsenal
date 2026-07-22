# Color definitions and utility functions

# ANSI Color codes (statusline specific)
if [[ -z "${STATUSLINE_RED:-}" ]]; then
    readonly STATUSLINE_RED='\033[31m'
    readonly STATUSLINE_GREEN='\033[32m'
    readonly STATUSLINE_YELLOW='\033[33m'
    readonly STATUSLINE_BLUE='\033[34m'
    readonly STATUSLINE_MAGENTA='\033[35m'
    readonly STATUSLINE_CYAN='\033[36m'
    readonly STATUSLINE_WHITE='\033[37m'
    readonly STATUSLINE_GRAY='\033[90m'
    readonly STATUSLINE_DIM='\033[2m'
    readonly STATUSLINE_BRIGHT_GREEN='\033[92m'
    readonly STATUSLINE_BRIGHT_YELLOW='\033[93m'
    readonly STATUSLINE_BRIGHT_BLUE='\033[94m'
    readonly STATUSLINE_BRIGHT_MAGENTA='\033[95m'
    readonly STATUSLINE_BRIGHT_CYAN='\033[96m'
    readonly STATUSLINE_RESET='\033[0m'
fi

# Color utility functions
colorize() {
    local color="$1"
    local text="$2"
    echo -e "${color}${text}${STATUSLINE_RESET}"
}

get_context_color() {
    local percent="$1"
    if [[ $percent -lt 50 ]]; then
        echo "$STATUSLINE_GREEN"
    elif [[ $percent -lt 80 ]]; then
        echo "$STATUSLINE_YELLOW"
    else
        echo "$STATUSLINE_RED"
    fi
}

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
