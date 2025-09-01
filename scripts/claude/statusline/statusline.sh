#!/bin/bash

# Claude Code Enhanced Statusline - Modular Architecture
# Displays model info, git status, costs, daily usage, and 5-hour reset info
# Usage: Add "statusline": "bash ~/.claude/scripts/claude/statusline/statusline.sh" to Claude Code settings

set -euo pipefail

# Get the directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source all library modules
source "$SCRIPT_DIR/lib/colors.sh"
source "$SCRIPT_DIR/lib/utils.sh"
source "$SCRIPT_DIR/lib/git_info.sh"
source "$SCRIPT_DIR/lib/usage_tracker.sh"
source "$SCRIPT_DIR/lib/components.sh"
source "$SCRIPT_DIR/lib/config.sh"
source "$SCRIPT_DIR/lib/cache_manager.sh"
source "$SCRIPT_DIR/lib/cached_operations.sh"
source "$SCRIPT_DIR/lib/data_reader.sh"

# Main statusline function
build_statusline() {
    local json_input="$1"

    # Initialize systems
    setup_config
    setup_usage_tracking
    cleanup_old_data
    update_window_tracking

    cache_warm_statusline

    # Extract data from JSON using correct Claude Code structure
    local model_id model_display_name total_cost_usd current_dir
    local total_duration_ms api_duration_ms lines_added lines_removed
    local session_cost daily_usage next_reset context_percent
    local session_cost_display daily_cost_display

    # Extract data from JSON using official Claude Code structure
    model_id=$(get_json_field "$json_input" '.model.id' '')
    model_display_name=$(get_json_field "$json_input" '.model.display_name' '')
    total_cost_usd=$(get_json_number "$json_input" '.cost.total_cost_usd' 0)

    # Directory handling - prioritize workspace.current_dir, fallback to cwd, then pwd
    current_dir=$(get_json_field "$json_input" '.workspace.current_dir' '')
    if [[ -z "$current_dir" || "$current_dir" == "null" ]]; then
        current_dir=$(get_json_field "$json_input" '.cwd' "$(pwd)")
    fi

    # Check if Claude Code provided insufficient data (empty model or zero cost)
    local use_enhanced_data=false
    if [[ -z "$model_id" || "$model_id" == "null" || "$model_id" == "{}" ]] && [[ "$total_cost_usd" == "0" || -z "$total_cost_usd" ]]; then
        use_enhanced_data=true
    fi

    # If Claude Code data is insufficient, try to get enhanced data from usage files
    if [[ "$use_enhanced_data" == "true" ]]; then
        local enhanced_data
        enhanced_data=$(get_enhanced_usage_data "$current_dir" 2>/dev/null || echo "{}")

        if [[ -n "$enhanced_data" && "$enhanced_data" != "{}" ]]; then
            # Override with enhanced data if available
            model_id=$(echo "$enhanced_data" | jq -r '.model.id // empty' 2>/dev/null || echo '')
            model_display_name=$(echo "$enhanced_data" | jq -r '.model.display_name // empty' 2>/dev/null || echo '')
            total_cost_usd=$(echo "$enhanced_data" | jq -r '.cost.total_cost_usd // 0' 2>/dev/null || echo '0')

            # Get token data for context calculation
            local input_tokens output_tokens
            input_tokens=$(echo "$enhanced_data" | jq -r '.tokens.input // 0' 2>/dev/null || echo '0')
            output_tokens=$(echo "$enhanced_data" | jq -r '.tokens.output // 0' 2>/dev/null || echo '0')

            # Calculate context percentage if we have token data
            if [[ "$input_tokens" != "0" || "$output_tokens" != "0" ]]; then
                local tokens_used context_window_size
                tokens_used=$((input_tokens + output_tokens))
                context_window_size=200000  # 200K tokens for paid Claude plans
                context_percent=$((100 - (tokens_used * 100 / context_window_size)))
                [[ $context_percent -lt 0 ]] && context_percent=0
            else
                context_percent="unavailable"
            fi
        else
            context_percent="unavailable"
        fi
    else
        # Use original logic for context percentage from token data if available
        local input_tokens output_tokens
        input_tokens=$(get_json_number "$json_input" '.cost.total_input_tokens' 0)
        output_tokens=$(get_json_number "$json_input" '.cost.total_output_tokens' 0)

        if [[ $input_tokens -gt 0 || $output_tokens -gt 0 ]]; then
            local tokens_used context_window_size
            tokens_used=$((input_tokens + output_tokens))
            context_window_size=200000
            context_percent=$((100 - (tokens_used * 100 / context_window_size)))
            [[ $context_percent -lt 0 ]] && context_percent=0
        else
            context_percent="unavailable"
        fi
    fi

    # Duration and line change data
    total_duration_ms=$(get_json_number "$json_input" '.cost.total_duration_ms' 0)
    api_duration_ms=$(get_json_number "$json_input" '.cost.total_api_duration_ms' 0)
    lines_added=$(get_json_number "$json_input" '.cost.total_lines_added' 0)
    lines_removed=$(get_json_number "$json_input" '.cost.total_lines_removed' 0)

    # Extract additional fields for potential future use
    session_id=$(get_json_field "$json_input" '.session_id' '')
    claude_version=$(get_json_field "$json_input" '.version' '')
    output_style=$(get_json_field "$json_input" '.output_style.name' '')

    # Determine model display string
    local model_display=""
    local model_version=""

    if [[ -n "$model_display_name" && "$model_display_name" != "null" && "$model_display_name" != "" ]]; then
        model_display="$model_display_name"
        # Don't show version when we have a clean display name
    elif [[ -n "$model_id" && "$model_id" != "null" && "$model_id" != "" ]]; then
        # Clean up model ID for display
        model_display=$(echo "$model_id" | sed 's/claude-//' | sed 's/-[0-9]\{8\}//')
        # Extract version from model ID if present (only when using ID)
        if [[ "$model_id" =~ -([0-9]{8})$ ]]; then
            model_version="${BASH_REMATCH[1]}"
        fi
    else
        model_display="unavailable"
    fi

    session_cost="$total_cost_usd"

    # Update usage tracking
    update_daily_usage "$session_cost"

    # Get calculated values directly
    daily_usage=$(get_daily_usage)
    next_reset=$(get_next_reset_time)

    # Format cost displays - use Claude Code values directly
    session_cost_display=""
    daily_cost_display=""

    # Use session cost directly as provided by Claude Code
    if [[ -n "$total_cost_usd" && "$total_cost_usd" != "0" && "$total_cost_usd" != "0.000" ]]; then
        session_cost_display="$total_cost_usd"
    fi

    if (( $(echo "$daily_usage > 0" | bc -l 2>/dev/null || echo "0") )); then
        local daily_decimal_places
        daily_decimal_places=$(get_config '.formatting.daily_cost_decimal_places' '2')
        daily_cost_display=$(printf "%.${daily_decimal_places}f" "$daily_usage")
    fi

    # current_dir already extracted from JSON above

    # Build components based on configuration order
    local components=()
    local compact_components=()

    # Get component order from config (handle array properly)
    local component_order_json config_file
    config_file="${ACTIVE_CONFIG_FILE:-$CONFIG_FILE}"

    if [[ -f "$config_file" ]]; then
        component_order_json=$(jq '.components.order // ["model","directory","git","session_cost","daily_cost","lines_changed","duration_info","reset_countdown","schedule"]' "$config_file" 2>/dev/null)
    else
        component_order_json='["model","directory","git","session_cost","daily_cost","lines_changed","duration_info","reset_countdown","schedule"]'
    fi

    # Process each component in the specified order
    while IFS= read -r component; do
        component=$(echo "$component" | tr -d '"' | tr -d ' ')
        [[ -z "$component" || "$component" == "null" ]] && continue

        # Check if component is enabled
        if [[ "$(get_config_bool ".components.enabled.$component" 'false')" == "true" ]]; then
            local full_component=""
            local compact_component=""

            case "$component" in
                "model")
                    full_component=$(get_model_component_cached "$model_display" "$model_version")
                    compact_component=$(get_model_component_cached "$model_display")
                    ;;
                "directory")
                    full_component=$(get_directory_component_cached "$current_dir")
                    compact_component=$(get_directory_component_cached "$current_dir")
                    ;;
                "git")
                    full_component=$(get_git_component_cached)
                    compact_component=$(get_git_component_cached)
                    ;;
                "context")
                    full_component=$(get_context_component_cached "$context_percent")
                    compact_component=$(get_context_component_cached "$context_percent")
                    ;;
                "session_cost")
                    full_component=$(get_session_cost_component_cached "$session_cost_display")
                    compact_component=$(get_session_cost_component_cached "$session_cost_display")
                    ;;
                "daily_cost")
                    full_component=$(get_daily_cost_component_cached "$daily_cost_display")
                    compact_component=$(get_daily_cost_component_cached "$daily_cost_display")
                    ;;
                "reset_countdown")
                    full_component=$(get_reset_component "$next_reset")
                    compact_component=$(get_reset_component_compact "$next_reset")
                    ;;
                "duration_info")
                    full_component=$(get_duration_info_component "$total_duration_ms" "$api_duration_ms")
                    compact_component=$(get_duration_info_component_compact "$total_duration_ms")
                    ;;
                "lines_changed")
                    full_component=$(get_lines_changed_component "$lines_added" "$lines_removed")
                    compact_component=$(get_lines_changed_component_compact "$lines_added" "$lines_removed")
                    ;;
                "schedule")
                    full_component=$(get_schedule_component "")
                    compact_component=$(get_schedule_component_compact "")
                    ;;
            esac

            # Add non-empty components
            [[ -n "$full_component" ]] && components+=("$full_component")
            [[ -n "$compact_component" ]] && compact_components+=("$compact_component")
        fi
    done < <(echo "$component_order_json" | jq -r '.[]' 2>/dev/null)


    # Determine if we should use compact format
    local terminal_width max_width compact_threshold
    terminal_width=$(get_terminal_width)
    max_width=$(get_config '.display.max_width' '120')
    compact_threshold=$(get_config '.display.compact_threshold' '80')

    local separator status_line

    if [[ $terminal_width -lt $compact_threshold ]]; then
        # Use compact format
        separator=$(get_config '.display.compact_separator' '│')
        separator="${STATUSLINE_GRAY}${separator}${STATUSLINE_RESET}"

        status_line=""
        for i in "${!compact_components[@]}"; do
            if [[ $i -gt 0 ]]; then
                status_line+="$separator"
            fi
            status_line+="${compact_components[$i]}"
        done
    else
        # Use full format
        separator=$(get_config '.display.separator' ' │ ')
        separator="${STATUSLINE_GRAY}${separator}${STATUSLINE_RESET}"

        status_line=""
        for i in "${!components[@]}"; do
            if [[ $i -gt 0 ]]; then
                status_line+="$separator"
            fi
            status_line+="${components[$i]}"
        done
    fi

    echo -e "$status_line"
}

# Debug logging function
debug_log() {
    local json_input="$1"
    local log_file="/tmp/claude_statusline_debug.log"

    {
        echo "=== $(date) ==="
        echo "Raw JSON length: ${#json_input}"
        echo "Raw JSON: $json_input"
        echo

        # Test extractions
        echo "Extractions:"
        echo "  model.id: '$(get_json_field "$json_input" '.model.id' 'MISSING')'"
        echo "  model.display_name: '$(get_json_field "$json_input" '.model.display_name' 'MISSING')'"
        echo "  cost.total_cost_usd: '$(get_json_number "$json_input" '.cost.total_cost_usd' 'MISSING')'"
        echo "=================================="
        echo
    } >> "$log_file"
}

# Main execution
main() {
    # Read JSON input from stdin
    local json_input=""
    while IFS= read -r line; do
        json_input+="$line"
    done

    # Log the actual data for debugging (temporary)
    if [[ -n "$json_input" ]]; then
        debug_log "$json_input"
    fi

    # Fallback if no JSON input - use minimal valid structure
    if [[ -z "$json_input" ]]; then
        json_input='{"model":{},"workspace":{"current_dir":"'$(pwd)'"},"cost":{}}'
    fi

    build_statusline "$json_input"
}

# Execute main function
main "$@"
