#!/bin/bash
# =============================================================================
# Statusline Builder - Assembles components into final output
# =============================================================================
# Orchestrates component building and formats the final statusline output.

# Guard clause - prevent multiple sourcing
if [[ -n "${STATUSLINE_BUILDER_LOADED:-}" ]]; then
    return 0
fi
readonly STATUSLINE_BUILDER_LOADED=1

# Source dependencies
STATUSLINE_DISPLAY_DIR="$(dirname "${BASH_SOURCE[0]}")"
source "$STATUSLINE_DISPLAY_DIR/components.sh"
source "$STATUSLINE_DISPLAY_DIR/../core/json.sh"
source "$STATUSLINE_DISPLAY_DIR/../tracking/usage.sh"

# =============================================================================
# Configuration
# =============================================================================

# Component separator
STATUSLINE_SEPARATOR="${STATUSLINE_SEPARATOR:-│}"

# =============================================================================
# Debug Logging
# =============================================================================

# Debug logging function
# Usage: debug_log "$json"
debug_log() {
    [[ "${STATUSLINE_DEBUG:-0}" != "1" ]] && return

    local json="$1"
    local log_file="/tmp/claude_statusline_debug.log"

    {
        echo "=== $(date) ==="
        echo "Raw JSON length: ${#json}"
        echo "Raw JSON: $json"
        echo
        echo "Token extractions (context_window priority):"
        echo "  context_window.total_input_tokens: '$(extract_json "$json" "context_window.total_input_tokens" 2>/dev/null || echo "MISSING")'"
        echo "  context_window.total_output_tokens: '$(extract_json "$json" "context_window.total_output_tokens" 2>/dev/null || echo "MISSING")'"
        echo "  context_window.context_window_size: '$(extract_json "$json" "context_window.context_window_size" 2>/dev/null || echo "MISSING")'"
        echo "  cost.total_input_tokens (fallback): '$(extract_json "$json" "cost.total_input_tokens" 2>/dev/null || echo "MISSING")'"
        echo "=================================="
        echo
    } >> "$log_file"
}

# =============================================================================
# Data Extraction
# =============================================================================

# Extract all relevant data from JSON
# Returns values via global variables for efficiency
extract_statusline_data() {
    local json="$1"

    # Model
    MODEL_ID=$(extract_json "$json" "model.id" 2>/dev/null || echo "")
    MODEL_DISPLAY=$(extract_json "$json" "model.display_name" 2>/dev/null || echo "")

    # Cost and lines
    COST_USD=$(extract_json "$json" "cost.total_cost_usd" 2>/dev/null || echo "")
    LINES_ADDED=$(extract_json "$json" "cost.total_lines_added" 2>/dev/null || echo "0")
    LINES_REMOVED=$(extract_json "$json" "cost.total_lines_removed" 2>/dev/null || echo "0")

    # Transcript path
    TRANSCRIPT_PATH=$(extract_json "$json" "transcript_path" 2>/dev/null || echo "")

    # Context window size
    CONTEXT_WINDOW_SIZE=$(extract_json "$json" "context_window.context_window_size" 2>/dev/null || echo "200000")

    # Token usage - prioritize context_window.* fields (new structure), then fallback
    INPUT_TOKENS=$(extract_json "$json" "context_window.total_input_tokens" 2>/dev/null || echo "")
    OUTPUT_TOKENS=$(extract_json "$json" "context_window.total_output_tokens" 2>/dev/null || echo "")

    # If context_window.* fields not available, try transcript file or other locations
    if [[ -z "$INPUT_TOKENS" || "$INPUT_TOKENS" == "null" ]]; then
        if [[ -n "$TRANSCRIPT_PATH" && -f "$TRANSCRIPT_PATH" ]]; then
            local tokens
            tokens=$(get_transcript_tokens "$TRANSCRIPT_PATH")
            INPUT_TOKENS="${tokens%|*}"
            OUTPUT_TOKENS="${tokens#*|}"
        else
            # Fallback: try legacy locations for token data
            INPUT_TOKENS=$(extract_json "$json" "cost.total_input_tokens" 2>/dev/null || \
                            extract_json "$json" "usage.total_input_tokens" 2>/dev/null || \
                            extract_json "$json" "total_input_tokens" 2>/dev/null || \
                            echo "0")
            OUTPUT_TOKENS=$(extract_json "$json" "cost.total_output_tokens" 2>/dev/null || \
                            extract_json "$json" "usage.total_output_tokens" 2>/dev/null || \
                            extract_json "$json" "total_output_tokens" 2>/dev/null || \
                            echo "0")
        fi
    fi

    # Ensure tokens have default values
    INPUT_TOKENS="${INPUT_TOKENS:-0}"
    OUTPUT_TOKENS="${OUTPUT_TOKENS:-0}"

    # Use display name directly if available
    MODEL="${MODEL_DISPLAY:-$MODEL_ID}"
}

# =============================================================================
# Line Building
# =============================================================================

# Build the first line (main statusline)
# Returns: formatted statusline string
build_line_one() {
    local json="$1"
    local current_dir="$2"

    local components=()
    local comp

    # Model
    comp=$(get_model_component "$MODEL")
    [[ -n "$comp" ]] && components+=("$comp")

    # Directory
    comp=$(get_directory_component "$current_dir")
    [[ -n "$comp" ]] && components+=("$comp")

    # Git
    comp=$(get_git_component)
    [[ -n "$comp" ]] && components+=("$comp")

    # Worktree
    comp=$(get_worktree_component)
    [[ -n "$comp" ]] && components+=("$comp")

    # Context
    comp=$(get_context_component "$INPUT_TOKENS" "$OUTPUT_TOKENS" "$CONTEXT_WINDOW_SIZE")
    [[ -n "$comp" ]] && components+=("$comp")

    # Cost
    comp=$(get_cost_component "$COST_USD")
    [[ -n "$comp" ]] && components+=("$comp")

    # Lines changed
    comp=$(get_lines_component "$LINES_ADDED" "$LINES_REMOVED")
    [[ -n "$comp" ]] && components+=("$comp")

    # Session duration
    comp=$(get_session_component "$json")
    [[ -n "$comp" ]] && components+=("$comp")

    # Assemble line
    local statusline=""
    local first=1

    for comp in "${components[@]}"; do
        if (( first )); then
            statusline="$comp"
            first=0
        else
            statusline="$statusline $STATUSLINE_SEPARATOR $comp"
        fi
    done

    echo "$statusline"
}

# Build the second line (usage details)
# Returns: usage line string
build_line_two() {
    get_usage_line "$INPUT_TOKENS" "$OUTPUT_TOKENS"
}

# =============================================================================
# Main Builder
# =============================================================================

# Build complete statusline (both lines)
# Usage: build_statusline "$json" "$current_dir"
build_statusline() {
    local json="$1"
    local current_dir="${2:-$(pwd)}"

    [[ -z "$json" ]] && json='{}'

    # Debug logging
    debug_log "$json"

    # Extract all data from JSON
    extract_statusline_data "$json"

    # Output line 1
    build_line_one "$json" "$current_dir"

    # Output line 2 (usage details)
    local usage_line
    usage_line=$(build_line_two)
    if [[ -n "$usage_line" ]]; then
        echo "$usage_line"
    fi
}

# Build minimal statusline (fallback)
# Usage: build_minimal_statusline
build_minimal_statusline() {
    local branch
    branch=$(git symbolic-ref --short HEAD 2>/dev/null || echo "main")
    echo "🤖 Claude $STATUSLINE_SEPARATOR 📁 $(basename "$PWD") $STATUSLINE_SEPARATOR 🌿 $branch $STATUSLINE_SEPARATOR 🔄 5h"
}
