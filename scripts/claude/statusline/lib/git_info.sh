#!/bin/bash
# Git information utilities

source "$(dirname "${BASH_SOURCE[0]}")/colors.sh"

# Get git branch information
get_git_branch() {
    if git rev-parse --git-dir &>/dev/null; then
        git branch --show-current 2>/dev/null || echo "detached"
    fi
}

# Get git worktree information
# Returns the worktree name if we're in a git worktree (not main working tree)
get_git_worktree() {
    if ! git rev-parse --git-dir &>/dev/null; then
        return
    fi

    # Detect worktree by comparing git-dir with git-common-dir
    # In a worktree, git-dir points to .git/worktrees/<name>
    local git_dir git_common_dir
    git_dir=$(git rev-parse --git-dir 2>/dev/null)
    git_common_dir=$(git rev-parse --git-common-dir 2>/dev/null)

    # If they're the same, we're in the main working tree (not a worktree)
    if [[ -z "$git_dir" || -z "$git_common_dir" || "$git_dir" == "$git_common_dir" ]]; then
        return
    fi

    # Extract worktree name from git-dir path
    # git-dir is typically: /path/to/repo/.git/worktrees/<worktree-name>
    if [[ "$git_dir" == *"/worktrees/"* ]]; then
        local worktree_name
        worktree_name="${git_dir##*/worktrees/}"
        # Remove any trailing slashes or paths
        worktree_name="${worktree_name%%/*}"
        echo "$worktree_name"
    fi
}

# Get git status indicator
get_git_status() {
    if ! git rev-parse --git-dir &>/dev/null; then
        return
    fi

    local git_status=""
    local status_type=""

    # Check for uncommitted changes
    if [[ -n $(git status --porcelain 2>/dev/null) ]]; then
        git_status="●"  # Dirty
        status_type="dirty"
    else
        git_status="✓"  # Clean
        status_type="clean"
    fi

    # Check if ahead/behind remote
    local ahead_behind
    ahead_behind=$(git rev-list --count --left-right "@{upstream}...HEAD" 2>/dev/null || echo "0	0")
    local behind ahead
    behind=$(echo "$ahead_behind" | cut -f1)
    ahead=$(echo "$ahead_behind" | cut -f2)

    if [[ $ahead -gt 0 && $behind -gt 0 ]]; then
        git_status="↕${ahead}↓${behind}"
        status_type="diverged"
    elif [[ $ahead -gt 0 ]]; then
        git_status="↑${ahead}"
        status_type="ahead"
    elif [[ $behind -gt 0 ]]; then
        git_status="↓${behind}"
        status_type="behind"
    fi

    echo "${git_status}|${status_type}"
}

# Get formatted git info component
get_git_component() {
    local branch
    local worktree
    local status_info
    local git_status
    local status_type
    local color

    branch=$(get_git_branch)
    if [[ -z "$branch" ]]; then
        return
    fi

    worktree=$(get_git_worktree)
    status_info=$(get_git_status)
    git_status="${status_info%|*}"
    status_type="${status_info#*|}"
    color=$(get_git_status_color "$status_type")

    local branch_display="$branch"
    if [[ -n "$worktree" ]]; then
        branch_display="${branch}@${worktree}"
    fi

    printf '%s' "${color}🌿 ${branch_display} ${git_status}${STATUSLINE_RESET}"
}

# Get compact git component
get_git_component_compact() {
    local branch
    local worktree
    local status_info
    local git_status
    local status_type
    local color

    branch=$(get_git_branch)
    if [[ -z "$branch" ]]; then
        return
    fi

    worktree=$(get_git_worktree)

    # Build branch display with worktree
    local branch_display="$branch"
    if [[ -n "$worktree" ]]; then
        branch_display="${branch}@${worktree}"
    fi

    # Shorten branch display for compact mode
    if [[ ${#branch_display} -gt 12 ]]; then
        branch_display="${branch_display:0:12}"
    fi

    status_info=$(get_git_status)
    git_status="${status_info%|*}"
    status_type="${status_info#*|}"
    color=$(get_git_status_color "$status_type")

    printf '%s' "${color}🌿${branch_display} ${git_status}${STATUSLINE_RESET}"
}
