#!/bin/bash
# Data reader for Claude usage files
# Simplified version inspired by claude-monitor

# Get Claude data directory
get_claude_data_dir() {
    local data_dir="$HOME/.claude/projects"
    if [[ -d "$data_dir" ]]; then
        echo "$data_dir"
    else
        echo ""
    fi
}

# Find project directory based on current working directory
get_project_data_dir() {
    local current_dir="$1"
    local data_dir
    data_dir=$(get_claude_data_dir)
    
    if [[ -z "$data_dir" ]]; then
        echo ""
        return
    fi
    
    # Convert current directory path to project directory format
    # Claude Code uses path format like: -Users-giovani-moutinho-projects-cc-arsenal
    local project_path
    project_path=$(echo "$current_dir" | sed 's|^/|-|' | sed 's|/|-|g')
    
    local project_dir="$data_dir/$project_path"
    if [[ -d "$project_dir" ]]; then
        echo "$project_dir"
    else
        # Try to find a similar directory (in case of slight naming differences)
        local basename_project
        basename_project=$(basename "$current_dir")
        find "$data_dir" -type d -name "*$basename_project*" | head -1
    fi
}

# Get latest session data from current project
get_latest_session_data() {
    local current_dir="$1"
    local project_dir
    project_dir=$(get_project_data_dir "$current_dir")
    
    if [[ -z "$project_dir" ]]; then
        return 1
    fi
    
    # Find the most recent JSONL file
    local latest_file
    latest_file=$(find "$project_dir" -name "*.jsonl" -type f -exec stat -f "%m %N" {} \; 2>/dev/null | sort -nr | head -1 | cut -d' ' -f2-)
    
    if [[ -z "$latest_file" || ! -f "$latest_file" ]]; then
        return 1
    fi
    
    # Get the last assistant message (most recent usage data)
    local last_entry
    last_entry=$(tail -10 "$latest_file" | grep '"type":"assistant"' | tail -1)
    
    if [[ -z "$last_entry" ]]; then
        return 1
    fi
    
    echo "$last_entry"
}

# Extract model information from session data
extract_model_info() {
    local json_data="$1"
    
    # Extract model from message.model field
    local model
    model=$(echo "$json_data" | jq -r '.message.model // empty' 2>/dev/null)
    
    if [[ -n "$model" && "$model" != "null" ]]; then
        echo "$model"
    else
        echo ""
    fi
}

# Extract token usage from session data
extract_token_usage() {
    local json_data="$1"
    
    # Extract tokens from message.usage including cache tokens
    local input_tokens output_tokens cache_creation_tokens cache_read_tokens
    input_tokens=$(echo "$json_data" | jq -r '.message.usage.input_tokens // 0' 2>/dev/null)
    output_tokens=$(echo "$json_data" | jq -r '.message.usage.output_tokens // 0' 2>/dev/null)
    cache_creation_tokens=$(echo "$json_data" | jq -r '.message.usage.cache_creation_input_tokens // 0' 2>/dev/null)
    cache_read_tokens=$(echo "$json_data" | jq -r '.message.usage.cache_read_input_tokens // 0' 2>/dev/null)
    
    # Total input tokens includes direct input + cache creation + cache read
    local total_input_tokens
    total_input_tokens=$((input_tokens + cache_creation_tokens + cache_read_tokens))
    
    echo "${total_input_tokens:-0} ${output_tokens:-0}"
}

# Calculate session cost from recent entries
calculate_session_cost() {
    local current_dir="$1"
    local project_dir
    project_dir=$(get_project_data_dir "$current_dir")
    
    if [[ -z "$project_dir" ]]; then
        echo "0"
        return
    fi
    
    # Find the most recent JSONL file  
    local latest_file
    latest_file=$(find "$project_dir" -name "*.jsonl" -type f -exec stat -f "%m %N" {} \; 2>/dev/null | sort -nr | head -1 | cut -d' ' -f2-)
    
    if [[ -z "$latest_file" || ! -f "$latest_file" ]]; then
        echo "0"
        return
    fi
    
    # Calculate total cost from all assistant messages in the session - simplified approach
    local total_cost
    total_cost=$(grep '"type":"assistant"' "$latest_file" 2>/dev/null | \
        jq -s 'map(.message.usage | (.input_tokens // 0) * 3 + (.output_tokens // 0) * 15) | add / 1000000' 2>/dev/null || echo "0")
    
    # Format to 2 decimal places
    if command -v bc >/dev/null 2>&1 && [[ "$total_cost" != "null" ]]; then
        printf "%.2f" "$total_cost" 2>/dev/null || echo "0"
    else
        echo "0"
    fi
}

# Get enhanced usage data for status line
get_enhanced_usage_data() {
    local current_dir="$1"
    local session_data model tokens_info session_cost
    
    # Get latest session data
    session_data=$(get_latest_session_data "$current_dir")
    
    if [[ -z "$session_data" ]]; then
        # No data available - return empty structure
        echo '{"model":{},"cost":{"total_cost_usd":0},"tokens":{"input":0,"output":0}}'
        return
    fi
    
    # Extract information
    model=$(extract_model_info "$session_data")
    local token_result input_tokens output_tokens
    token_result=$(extract_token_usage "$session_data")
    read -r input_tokens output_tokens <<< "$token_result"
    session_cost=$(calculate_session_cost "$current_dir")
    
    # Build enhanced JSON structure
    local model_json="{}"
    if [[ -n "$model" ]]; then
        # Clean up model name for display
        local model_display
        model_display=$(echo "$model" | sed 's/claude-//' | sed 's/-[0-9]\{8\}//')
        model_json="{\"id\":\"$model\",\"display_name\":\"$model_display\"}"
    fi
    
    # Build complete JSON
    cat <<EOF
{
  "model": $model_json,
  "workspace": {"current_dir": "$current_dir"},
  "cost": {"total_cost_usd": $session_cost},
  "tokens": {"input": ${input_tokens:-0}, "output": ${output_tokens:-0}},
  "enhanced": true
}
EOF
}