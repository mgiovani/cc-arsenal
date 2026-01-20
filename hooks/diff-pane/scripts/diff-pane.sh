#!/bin/bash
# Zero-token git diff pane for Claude Code
# Triggered by PostToolUse on Edit|Write|NotebookEdit
#
# This hook automatically opens a tmux side pane showing git diff
# whenever files are modified, providing real-time visibility into changes.
#
# Configuration via environment variables:
#   CLAUDE_DIFF_PANE_WIDTH     - Pane width percentage (default: 40)
#   CLAUDE_DIFF_PANE_POSITION  - Pane position: left or right (default: right)
#   CLAUDE_DIFF_STAGED_ONLY    - Show only staged changes (default: false)
#   CLAUDE_DIFF_TOOL           - Diff tool: delta, diff-so-fancy, or git (default: auto)

set -euo pipefail

# Configuration
PANE_ID_FILE="/tmp/claude-diff-pane-id"
PANE_WIDTH_PERCENT="${CLAUDE_DIFF_PANE_WIDTH:-40}"
PANE_POSITION="${CLAUDE_DIFF_PANE_POSITION:-right}"
STAGED_ONLY="${CLAUDE_DIFF_STAGED_ONLY:-false}"
DIFF_TOOL="${CLAUDE_DIFF_TOOL:-auto}"

# Check if we're in tmux
if [ -z "${TMUX:-}" ]; then
    exit 0  # Silently exit if not in tmux
fi

# Check if git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    exit 0  # Not a git repo, skip
fi

# Function to check if pane exists
pane_exists() {
    local pane_id="$1"
    tmux list-panes -F '#{pane_id}' 2>/dev/null | grep -q "^${pane_id}$"
}

# Function to get or create diff pane
get_or_create_pane() {
    local existing_pane=""

    # Check for existing pane
    if [ -f "$PANE_ID_FILE" ]; then
        existing_pane=$(cat "$PANE_ID_FILE")
        if pane_exists "$existing_pane"; then
            echo "$existing_pane"
            return 0
        fi
    fi

    # Create new pane based on position
    local new_pane
    if [ "$PANE_POSITION" = "left" ]; then
        new_pane=$(tmux split-window -h -b -P -F '#{pane_id}' -l "${PANE_WIDTH_PERCENT}%" \
            "while true; do sleep 86400; done")
    else
        new_pane=$(tmux split-window -h -P -F '#{pane_id}' -l "${PANE_WIDTH_PERCENT}%" \
            "while true; do sleep 86400; done")
    fi

    echo "$new_pane" > "$PANE_ID_FILE"
    echo "$new_pane"
}

# Function to determine diff command
get_diff_command() {
    local base_cmd=""

    # Determine base git diff command
    if [ "$STAGED_ONLY" = "true" ]; then
        base_cmd="git diff --cached --color=always"
    else
        base_cmd="git diff --color=always"
    fi

    # Apply diff tool
    case "$DIFF_TOOL" in
        delta)
            if command -v delta > /dev/null 2>&1; then
                echo "$base_cmd | delta --paging=never"
            else
                echo "$base_cmd"
            fi
            ;;
        diff-so-fancy)
            if command -v diff-so-fancy > /dev/null 2>&1; then
                echo "$base_cmd | diff-so-fancy"
            else
                echo "$base_cmd"
            fi
            ;;
        git)
            echo "$base_cmd"
            ;;
        auto)
            if command -v delta > /dev/null 2>&1; then
                echo "$base_cmd | delta --paging=never"
            elif command -v diff-so-fancy > /dev/null 2>&1; then
                echo "$base_cmd | diff-so-fancy"
            else
                echo "$base_cmd"
            fi
            ;;
        *)
            echo "$base_cmd"
            ;;
    esac
}

# Function to show diff in pane
show_diff() {
    local pane_id="$1"
    local diff_cmd
    diff_cmd=$(get_diff_command)

    # Build header message
    local header="=== Git Diff (auto-updated) ==="
    if [ "$STAGED_ONLY" = "true" ]; then
        header="=== Git Diff --cached (auto-updated) ==="
    fi

    # Send commands to the pane
    tmux send-keys -t "$pane_id" C-c  # Cancel any running command
    sleep 0.1
    tmux send-keys -t "$pane_id" "clear && echo '$header' && echo && $diff_cmd" Enter
}

# Main execution
main() {
    local pane_id
    pane_id=$(get_or_create_pane)
    show_diff "$pane_id"
}

main
