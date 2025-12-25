#!/bin/bash
# =============================================================================
# Git API - Git repository operations
# =============================================================================
# Provides functions for querying git repository state including branch,
# status, and worktree information.

# Guard clause - prevent multiple sourcing
if [[ -n "${STATUSLINE_GIT_LOADED:-}" ]]; then
    return 0
fi
readonly STATUSLINE_GIT_LOADED=1

# Source dependencies
STATUSLINE_API_DIR="$(dirname "${BASH_SOURCE[0]}")"
source "$STATUSLINE_API_DIR/../core/cache.sh"

# =============================================================================
# Repository Detection
# =============================================================================

# Check if current directory is a git repository
# Returns: 0 if in git repo, 1 otherwise
is_git_repo() {
    git rev-parse --git-dir >/dev/null 2>&1
}

# =============================================================================
# Branch Information
# =============================================================================

# Get current git branch name
# Returns: branch name, "detached" if detached HEAD, empty if not in repo
get_git_branch() {
    if ! is_git_repo; then
        return
    fi

    git symbolic-ref --short HEAD 2>/dev/null || \
    git rev-parse --short HEAD 2>/dev/null || \
    echo "detached"
}

# =============================================================================
# Worktree Information
# =============================================================================

# Get worktree name if in a git worktree (not main working tree)
# Returns: worktree name or empty if in main working tree
get_git_worktree() {
    if ! is_git_repo; then
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

# =============================================================================
# Status Information
# =============================================================================

# Get count of uncommitted changes
# Returns: number of changed files
get_git_changes() {
    if ! is_git_repo; then
        echo "0"
        return
    fi

    git status --porcelain=v1 -u 2>/dev/null | wc -l | tr -d ' '
}

# Get git status indicator
# Returns: "status_symbol|status_type" (e.g., "●|dirty", "✓|clean")
get_git_status() {
    if ! is_git_repo; then
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

# =============================================================================
# Combined Information
# =============================================================================

# Get all git info in a single call (optimized)
# Returns: "changes|branch|worktree" or "0|not_a_repo|" if not in repo
get_git_info() {
    if ! is_git_repo; then
        echo "0|not_a_repo|"
        return 0
    fi

    local changes branch worktree

    changes=$(get_git_changes)
    branch=$(get_git_branch)
    worktree=$(get_git_worktree)

    echo "${changes}|${branch}|${worktree}"
}

# Get all git info with caching
# Usage: get_git_info_cached [ttl_seconds]
get_git_info_cached() {
    local ttl="${1:-30}"
    local cache_key="git_info_$(hash_string "$PWD")"

    cache_get_or_compute "$cache_key" "get_git_info" "$ttl"
}

# =============================================================================
# Utility Functions
# =============================================================================

# Check if there are any uncommitted changes
# Returns: 0 if dirty, 1 if clean
is_git_dirty() {
    if ! is_git_repo; then
        return 1
    fi
    [[ -n $(git status --porcelain 2>/dev/null) ]]
}

# Get the remote tracking branch
# Returns: remote/branch or empty
get_git_upstream() {
    if ! is_git_repo; then
        return
    fi
    git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null
}

# Get root directory of git repository
# Returns: absolute path to repo root
get_git_root() {
    if ! is_git_repo; then
        return
    fi
    git rev-parse --show-toplevel 2>/dev/null
}
