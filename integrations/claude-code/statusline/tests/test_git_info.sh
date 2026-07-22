#!/bin/bash
# Unit tests for lib/api/git.sh

# Test framework setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$(cd "$SCRIPT_DIR/../lib" && pwd)"

# Shared assert helpers (assert_equals, assert_not_empty, assert_contains, print_results, ...)
source "$SCRIPT_DIR/lib/assert.sh"

# Source the module under test
source "$LIB_DIR/api/git.sh"

# Known branch name for the isolated test repo - never assume main/master,
# a checkout's default branch name varies by git version and user config.
TEST_BRANCH_NAME="statusline-test-branch-$$"

# Create an isolated /tmp git repository for testing, on a known branch name
setup_test_repo() {
    local test_dir="/tmp/statusline_git_test_$$"
    mkdir -p "$test_dir"
    cd "$test_dir" || return 1

    git init --quiet
    git checkout -b "$TEST_BRANCH_NAME" --quiet 2>/dev/null || \
        git symbolic-ref HEAD "refs/heads/$TEST_BRANCH_NAME"
    git config user.email "test@example.com"
    git config user.name "Test User"

    echo "test content" > test_file.txt
    git add test_file.txt
    git commit --quiet -m "Initial commit"

    echo "$test_dir"
}

cleanup_test_repo() {
    local test_dir="$1"
    if [[ -n "$test_dir" && -d "$test_dir" ]]; then
        rm -rf "$test_dir"
    fi
}

# Test is_git_repo function
test_is_git_repo() {
    echo "Testing is_git_repo function..."

    local test_repo original_dir
    original_dir=$(pwd)
    test_repo=$(setup_test_repo)
    cd "$test_repo"

    TESTS_RUN=$((TESTS_RUN + 1))
    if is_git_repo; then
        echo "✅ PASS: is_git_repo returns true inside a git repo"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: is_git_repo should return true inside a git repo"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi

    cd "$original_dir"
    cleanup_test_repo "$test_repo"

    cd /tmp
    TESTS_RUN=$((TESTS_RUN + 1))
    if ! is_git_repo; then
        echo "✅ PASS: is_git_repo returns false outside a git repo"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: is_git_repo should return false outside a git repo"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi

    cd "$original_dir"
}

# Test get_git_branch function
test_get_git_branch() {
    echo "Testing get_git_branch function..."

    local test_repo original_dir
    original_dir=$(pwd)
    test_repo=$(setup_test_repo)
    cd "$test_repo"

    local result
    result=$(get_git_branch)
    assert_equals "$TEST_BRANCH_NAME" "$result" "get_git_branch returns the known branch name in git repo"

    cd "$original_dir"
    cleanup_test_repo "$test_repo"

    # Test outside git repository
    cd /tmp
    result=$(get_git_branch)
    assert_equals "" "$result" "get_git_branch returns empty outside git repo"

    cd "$original_dir"
}

# Test get_git_changes function
test_get_git_changes() {
    echo "Testing get_git_changes function..."

    local test_repo original_dir
    original_dir=$(pwd)
    test_repo=$(setup_test_repo)
    cd "$test_repo"

    local result
    result=$(get_git_changes)
    assert_equals "0" "$result" "get_git_changes returns 0 for a clean repo"

    echo "modified content" > test_file.txt
    result=$(get_git_changes)
    assert_equals "1" "$result" "get_git_changes returns 1 for one modified file"

    cd "$original_dir"
    cleanup_test_repo "$test_repo"

    # Test outside git repository
    cd /tmp
    result=$(get_git_changes)
    assert_equals "0" "$result" "get_git_changes returns 0 outside git repo"

    cd "$original_dir"
}

# Test get_git_status function
test_get_git_status() {
    echo "Testing get_git_status function..."

    local test_repo original_dir
    original_dir=$(pwd)
    test_repo=$(setup_test_repo)
    cd "$test_repo"

    local result
    result=$(get_git_status)

    # Should return clean status
    assert_contains "✓" "$result" "get_git_status shows clean for committed repo"
    assert_contains "clean" "$result" "get_git_status includes clean status type"

    # Create dirty repository
    echo "modified content" > test_file.txt
    result=$(get_git_status)
    assert_contains "●" "$result" "get_git_status shows dirty for modified repo"
    assert_contains "dirty" "$result" "get_git_status includes dirty status type"

    cd "$original_dir"
    cleanup_test_repo "$test_repo"

    # Test outside git repository
    cd /tmp
    result=$(get_git_status)
    assert_equals "" "$result" "get_git_status returns empty outside git repo"

    cd "$original_dir"
}

# Test get_git_info function (combined changes|branch|worktree)
test_get_git_info() {
    echo "Testing get_git_info function..."

    local test_repo original_dir
    original_dir=$(pwd)
    test_repo=$(setup_test_repo)
    cd "$test_repo"

    local result
    result=$(get_git_info)
    assert_equals "0|${TEST_BRANCH_NAME}|" "$result" "get_git_info reports clean/branch/no-worktree"

    echo "modified content" > test_file.txt
    result=$(get_git_info)
    assert_equals "1|${TEST_BRANCH_NAME}|" "$result" "get_git_info reports change count after edit"

    cd "$original_dir"
    cleanup_test_repo "$test_repo"

    # Test outside git repository
    cd /tmp
    result=$(get_git_info)
    assert_equals "0|not_a_repo|" "$result" "get_git_info reports not_a_repo outside git repo"

    cd "$original_dir"
}

# Test get_git_worktree function
test_get_git_worktree() {
    echo "Testing get_git_worktree function..."

    # Test in main git repository (not a worktree)
    local test_repo original_dir
    original_dir=$(pwd)
    test_repo=$(setup_test_repo)
    cd "$test_repo"

    local result
    result=$(get_git_worktree)

    # Should return empty in main repository (not a worktree)
    assert_equals "" "$result" "get_git_worktree returns empty in main repo"

    # Create a worktree and test
    local worktree_dir="$test_repo-worktree"
    git worktree add --quiet "$worktree_dir" -b test-worktree-branch-$$ 2>/dev/null
    cd "$worktree_dir"

    result=$(get_git_worktree)

    # Should return the worktree name (extracted from git-dir path)
    assert_not_empty "$result" "get_git_worktree returns worktree name in worktree"

    # Verify it's extracting from git-dir path, not PWD
    local git_dir expected_name
    git_dir=$(git rev-parse --git-dir 2>/dev/null)
    if [[ "$git_dir" == *"/worktrees/"* ]]; then
        expected_name="${git_dir##*/worktrees/}"
        expected_name="${expected_name%%/*}"
        assert_equals "$expected_name" "$result" "get_git_worktree extracts name from git-dir path"
    else
        echo "⚠️  SKIP: Could not verify worktree name extraction (git-dir: $git_dir)"
    fi

    # Cleanup
    cd "$original_dir"
    git -C "$test_repo" worktree remove "$worktree_dir" --force 2>/dev/null || rm -rf "$worktree_dir"
    cleanup_test_repo "$test_repo"

    # Test outside git repository
    cd /tmp
    result=$(get_git_worktree)
    assert_equals "" "$result" "get_git_worktree returns empty outside git repo"

    cd "$original_dir"
}

# Run all tests
main() {
    echo "Running Git API Module Tests..."
    echo

    # Save current directory
    local original_dir
    original_dir=$(pwd)

    test_is_git_repo
    test_get_git_branch
    test_get_git_changes
    test_get_git_status
    test_get_git_info
    test_get_git_worktree

    # Restore original directory
    cd "$original_dir"

    print_results "Git Info Tests"
}

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
