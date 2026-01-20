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
# Create a unique pane ID file per Claude session using TTY or PID
CLAUDE_SESSION_ID="${TMUX_PANE:-$$}"
PANE_ID_FILE="/tmp/claude-diff-pane-id-${CLAUDE_SESSION_ID}"
LOCK_FILE="/tmp/claude-diff-pane-lock-${CLAUDE_SESSION_ID}"
PANE_WIDTH_PERCENT="${CLAUDE_DIFF_PANE_WIDTH:-40}"
PANE_POSITION="${CLAUDE_DIFF_PANE_POSITION:-right}"
STAGED_ONLY="${CLAUDE_DIFF_STAGED_ONLY:-false}"
DIFF_TOOL="${CLAUDE_DIFF_TOOL:-auto}"

# Ensure lock is released on exit
trap 'release_lock' EXIT

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

# Function to acquire lock
acquire_lock() {
    local retries=10
    local delay=0.1

    for ((i=0; i<retries; i++)); do
        if mkdir "$LOCK_FILE" 2>/dev/null; then
            return 0
        fi
        sleep "$delay"
    done
    return 1
}

# Function to release lock
release_lock() {
    rmdir "$LOCK_FILE" 2>/dev/null || true
}

# Function to create diff pane (always kills and recreates for clean updates)
create_diff_pane() {
    # Acquire lock to prevent race conditions
    if ! acquire_lock; then
        return 1
    fi

    # Kill existing pane if it exists
    if [ -f "$PANE_ID_FILE" ]; then
        local existing_pane
        existing_pane=$(cat "$PANE_ID_FILE")
        if pane_exists "$existing_pane"; then
            tmux kill-pane -t "$existing_pane" 2>/dev/null || true
        fi
    fi

    # When hook is triggered, TMUX_PANE contains the pane that triggered it
    # This is the Claude pane we want to split from
    local source_pane="${TMUX_PANE}"

    # If TMUX_PANE is not set (manual execution), use current pane
    if [ -z "$source_pane" ]; then
        source_pane=$(tmux display-message -p '#{pane_id}')
    fi

    # Build the diff command
    local diff_cmd
    diff_cmd=$(get_diff_command)

    # Build header message
    local header="=== Git Diff (auto-updated) ==="
    if [ "$STAGED_ONLY" = "true" ]; then
        header="=== Git Diff --cached (auto-updated) ==="
    fi

    # Create new pane with the diff command already running in less
    # This way the pane opens with scrollable content immediately
    local new_pane
    if [ "$PANE_POSITION" = "left" ]; then
        new_pane=$(tmux split-window -t "$source_pane" -h -b -P -F '#{pane_id}' -l "${PANE_WIDTH_PERCENT}%" \
            "echo '$header' && echo && $diff_cmd")
    else
        new_pane=$(tmux split-window -t "$source_pane" -h -P -F '#{pane_id}' -l "${PANE_WIDTH_PERCENT}%" \
            "echo '$header' && echo && $diff_cmd")
    fi

    echo "$new_pane" > "$PANE_ID_FILE"

    release_lock
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

    # Apply diff tool with less for scrolling
    # We recreate the pane on each update, so less doesn't interfere
    case "$DIFF_TOOL" in
        delta)
            if command -v delta > /dev/null 2>&1; then
                echo "$base_cmd | delta | less -R +G"
            else
                echo "$base_cmd | less -R +G"
            fi
            ;;
        diff-so-fancy)
            if command -v diff-so-fancy > /dev/null 2>&1; then
                echo "$base_cmd | diff-so-fancy | less -R +G"
            else
                echo "$base_cmd | less -R +G"
            fi
            ;;
        git)
            echo "$base_cmd | less -R +G"
            ;;
        auto)
            if command -v delta > /dev/null 2>&1; then
                echo "$base_cmd | delta | less -R +G"
            elif command -v diff-so-fancy > /dev/null 2>&1; then
                echo "$base_cmd | diff-so-fancy | less -R +G"
            else
                echo "$base_cmd | less -R +G"
            fi
            ;;
        *)
            echo "$base_cmd | less -R +G"
            ;;
    esac
}

# Main execution
main() {
    # Always recreate the pane with fresh diff output
    # This avoids issues with updating content in less
    create_diff_pane
}

main
