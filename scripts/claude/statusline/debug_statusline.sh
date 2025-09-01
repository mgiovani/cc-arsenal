#!/bin/bash
# Debug statusline data extraction - captures and logs real Claude Code data

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/utils.sh"
source "$SCRIPT_DIR/lib/colors.sh"

LOG_FILE="/tmp/claude_statusline_debug.log"

debug_json_extraction() {
    local json_input="$1"
    
    # Log to file for persistent debugging
    {
        echo "=== $(date) ==="
        echo "Raw input length: ${#json_input}"
        echo "Raw input (first 200 chars): ${json_input:0:200}"
        echo
        echo "JSON validity test:"
        if echo "$json_input" | jq . >/dev/null 2>&1; then
            echo "✅ Valid JSON"
        else
            echo "❌ Invalid JSON"
            echo "jq error: $(echo "$json_input" | jq . 2>&1)"
        fi
        echo
        
        echo "=== Field Extraction ==="
        echo "model.id: '$(get_json_field "$json_input" '.model.id' 'NULL')'"
        echo "model.display_name: '$(get_json_field "$json_input" '.model.display_name' 'NULL')'"
        echo "cost.total_cost_usd: '$(get_json_number "$json_input" '.cost.total_cost_usd' 'NULL')'"
        echo "workspace.current_dir: '$(get_json_field "$json_input" '.workspace.current_dir' 'NULL')'"
        echo "cwd: '$(get_json_field "$json_input" '.cwd' 'NULL')'"
        echo
        
        echo "=== Detailed JSON Structure ==="
        echo "$json_input" | jq . 2>/dev/null || echo "Cannot parse JSON"
        echo
        echo "=================================="
        echo
    } >> "$LOG_FILE"
    
    # Also output to console for immediate feedback
    echo "=== STATUSLINE DEBUG ==="
    echo "Logging to: $LOG_FILE"
    echo "Input JSON length: ${#json_input}"
    
    if echo "$json_input" | jq . >/dev/null 2>&1; then
        echo "✅ Valid JSON received"
        
        # Test key extractions
        local model_id model_name session_cost
        model_id=$(get_json_field "$json_input" '.model.id' '')
        model_name=$(get_json_field "$json_input" '.model.display_name' '')
        session_cost=$(get_json_number "$json_input" '.cost.total_cost_usd' 0)
        
        echo "Model ID: '$model_id'"
        echo "Model Name: '$model_name'" 
        echo "Session Cost: '$session_cost'"
        
        # Test component logic
        if [[ "$model_name" == "null" || -z "$model_name" ]]; then
            if [[ "$model_id" == "null" || -z "$model_id" ]]; then
                echo "❌ Both model fields are empty - will show N/A"
            else
                echo "⚠️ Using model ID: '$model_id'"
            fi
        else
            echo "✅ Using model display name: '$model_name'"
        fi
        
        if [[ -z "$session_cost" || "$session_cost" == "0" || "$session_cost" == "null" ]]; then
            echo "❌ Session cost is empty/zero - will show N/A"
        else
            echo "✅ Session cost available: '$session_cost'"
        fi
    else
        echo "❌ Invalid JSON received"
    fi
    echo "========================="
}

# Read JSON from stdin
json_input=""
while IFS= read -r line; do
    json_input+="$line"
done

debug_json_extraction "$json_input"