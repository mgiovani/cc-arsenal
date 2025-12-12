#!/bin/bash
# Unit tests for git_info.sh

# Test framework setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$SCRIPT_DIR/../lib"

# Source the modules under test
source "$LIB_DIR/colors.sh"
source "$LIB_DIR/git_info.sh"

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test helper functions
assert_equals() {
    local expected="$1"
    local actual="$2"
    local test_name="$3"

    TESTS_RUN=$((TESTS_RUN + 1))

    if [[ "$expected" == "$actual" ]]; then
        echo "✅ PASS: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: $test_name"
        echo "   Expected: '$expected'"
        echo "   Actual:   '$actual'"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

assert_not_empty() {
    local actual="$1"
    local test_name="$2"

    TESTS_RUN=$((TESTS_RUN + 1))

    if [[ -n "$actual" ]]; then
        echo "✅ PASS: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: $test_name (expected non-empty value)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

assert_contains() {
    local expected_substring="$1"
    local actual="$2"
    local test_name="$3"

    TESTS_RUN=$((TESTS_RUN + 1))

    if [[ "$actual" == *"$expected_substring"* ]]; then
        echo "✅ PASS: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: $test_name"
        echo "   Expected substring: '$expected_substring'"
        echo "   Actual:             '$actual'"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

print_results() {
    echo
    echo "=========================================="
    echo "Git Info Tests Results:"
    echo "  Total:  $TESTS_RUN"
    echo "  Passed: $TESTS_PASSED"
    echo "  Failed: $TESTS_FAILED"
    echo "=========================================="

    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo "🎉 All tests passed!"
        exit 0
    else
        echo "💥 Some tests failed!"
        exit 1
    fi
}

# Create a temporary git repository for testing
setup_test_repo() {
    local test_dir="/tmp/statusline_git_test_$$"
    mkdir -p "$test_dir"
    cd "$test_dir"

    git init --quiet
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

# Test get_git_branch function
test_get_git_branch() {
    echo "Testing get_git_branch function..."

    # Test in git repository
    local test_repo
    test_repo=$(setup_test_repo)

    local result
    result=$(get_git_branch)

    # Should return main or master (depending on git version)
    if [[ "$result" == "main" || "$result" == "master" ]]; then
        echo "✅ PASS: get_git_branch returns branch name in git repo"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: get_git_branch should return main/master, got: '$result'"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    TESTS_RUN=$((TESTS_RUN + 1))

    cleanup_test_repo "$test_repo"

    # Test outside git repository
    cd /tmp
    result=$(get_git_branch)
    assert_equals "" "$result" "get_git_branch returns empty outside git repo"
}

# Test get_git_status function
test_get_git_status() {
    echo "Testing get_git_status function..."

    # Test in clean git repository
    local test_repo original_dir
    original_dir=$(pwd)
    test_repo=$(setup_test_repo)
    cd "$test_repo"  # Ensure we're in the test repo

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

    cd "$original_dir"  # Return to original directory
    cleanup_test_repo "$test_repo"

    # Test outside git repository
    cd /tmp
    result=$(get_git_status)
    assert_equals "" "$result" "get_git_status returns empty outside git repo"
}

# Test get_git_component function
test_get_git_component() {
    echo "Testing get_git_component function..."

    # Test in git repository
    local test_repo original_dir
    original_dir=$(pwd)
    test_repo=$(setup_test_repo)
    cd "$test_repo"  # Ensure we're in the test repo

    local result
    result=$(get_git_component)

    # Should contain git emoji, branch name, and status
    assert_contains "🌿" "$result" "get_git_component includes git emoji"
    # Branch name could be "main" or "master" depending on git version
    if [[ "$result" == *"main"* || "$result" == *"master"* ]]; then
        echo "✅ PASS: get_git_component includes branch name (main or master)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: get_git_component should include branch name"
        echo "   Actual: '$result'"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    TESTS_RUN=$((TESTS_RUN + 1))
    assert_contains "✓" "$result" "get_git_component includes status indicator"

    # Should include ANSI color codes
    assert_contains "$STATUSLINE_RESET" "$result" "get_git_component includes reset color"

    cd "$original_dir"  # Return to original directory
    cleanup_test_repo "$test_repo"

    # Test outside git repository
    cd /tmp
    result=$(get_git_component)
    assert_equals "" "$result" "get_git_component returns empty outside git repo"
}

# Test get_git_component_compact function
test_get_git_component_compact() {
    echo "Testing get_git_component_compact function..."

    # Test in git repository
    local test_repo original_dir
    original_dir=$(pwd)
    test_repo=$(setup_test_repo)
    cd "$test_repo"  # Ensure we're in the test repo

    local result
    result=$(get_git_component_compact)

    # Should be more compact than regular version
    assert_contains "🌿" "$result" "get_git_component_compact includes git emoji"
    assert_contains "✓" "$result" "get_git_component_compact includes status indicator"

    # Test with long branch name
    git checkout -b very_long_branch_name_that_exceeds_limit --quiet
    result=$(get_git_component_compact)

    # Branch name should be truncated in compact mode
    local branch_part
    branch_part=$(echo "$result" | sed 's/.*🌿\([^ ]*\) .*/\1/')

    # Code truncates to 12 chars (see lib/git_info.sh line 131)
    if [[ ${#branch_part} -le 12 ]]; then
        echo "✅ PASS: get_git_component_compact truncates long branch names"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: get_git_component_compact should truncate branch names to 12 chars, got: '$branch_part' (${#branch_part} chars)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    TESTS_RUN=$((TESTS_RUN + 1))

    cd "$original_dir"  # Return to original directory
    cleanup_test_repo "$test_repo"
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
    git worktree add --quiet "$worktree_dir" -b test-worktree-branch 2>/dev/null
    cd "$worktree_dir"

    result=$(get_git_worktree)

    # Should return the worktree name (extracted from git-dir path)
    # The worktree name is the basename of the git-dir inside .git/worktrees/
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
}

# Run all tests
main() {
    echo "Running Git Info Module Tests..."
    echo

    # Save current directory
    local original_dir
    original_dir=$(pwd)

    test_get_git_branch
    test_get_git_status
    test_get_git_worktree
    test_get_git_component
    test_get_git_component_compact

    # Restore original directory
    cd "$original_dir"

    print_results
}

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
