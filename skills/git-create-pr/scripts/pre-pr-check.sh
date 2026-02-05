#!/usr/bin/env bash
# Hook: pre-pr-check
# Purpose: Run tests before creating PR to ensure CI will pass
# Event: PreToolUse (before "gh pr create" command)
#
# This hook:
# 1. Detects the project type and test command
# 2. Runs the test suite
# 3. Blocks PR creation if tests fail
# 4. Allows PR creation if tests pass or no tests configured

set -euo pipefail

# JSON response helper functions
deny_pr() {
  local reason="$1"
  cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "$reason"
  }
}
EOF
  exit 0
}

allow_pr() {
  # Implicit allow - no output needed
  exit 0
}

# Function to detect and run tests
run_tests() {
  local project_root
  project_root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)

  cd "$project_root" || exit 1

  # Check for Makefile with test target (highest priority)
  if [ -f "Makefile" ] && grep -q "^test:" Makefile; then
    echo "🧪 Running: make test" >&2
    if ! make test 2>&1; then
      deny_pr "Tests failed: make test reported failures. Fix failing tests before creating PR."
    fi
    allow_pr
  fi

  # Check for package.json (Node.js project)
  if [ -f "package.json" ]; then
    # Check if test script exists
    if command -v jq >/dev/null 2>&1 && jq -e '.scripts.test' package.json >/dev/null 2>&1; then
      # Skip if test script is just a placeholder
      test_script=$(jq -r '.scripts.test' package.json)
      if [[ "$test_script" == *"no test specified"* ]] || [[ "$test_script" == "echo"* ]]; then
        echo "ℹ️  No test script configured. Allowing PR creation." >&2
        allow_pr
      fi

      echo "🧪 Running: npm test" >&2

      # Detect package manager
      if [ -f "bun.lockb" ] && command -v bun >/dev/null 2>&1; then
        if ! bun test 2>&1; then
          deny_pr "Tests failed: bun test reported failures. Fix failing tests before creating PR."
        fi
      elif [ -f "pnpm-lock.yaml" ] && command -v pnpm >/dev/null 2>&1; then
        if ! pnpm test 2>&1; then
          deny_pr "Tests failed: pnpm test reported failures. Fix failing tests before creating PR."
        fi
      elif [ -f "yarn.lock" ] && command -v yarn >/dev/null 2>&1; then
        if ! yarn test 2>&1; then
          deny_pr "Tests failed: yarn test reported failures. Fix failing tests before creating PR."
        fi
      elif command -v npm >/dev/null 2>&1; then
        if ! npm test 2>&1; then
          deny_pr "Tests failed: npm test reported failures. Fix failing tests before creating PR."
        fi
      fi
      allow_pr
    fi
  fi

  # Check for pyproject.toml (Python project)
  if [ -f "pyproject.toml" ]; then
    # Try pytest
    if command -v pytest >/dev/null 2>&1; then
      echo "🧪 Running: pytest" >&2
      if ! pytest 2>&1; then
        deny_pr "Tests failed: pytest reported failures. Fix failing tests before creating PR."
      fi
      allow_pr
    fi

    # Try uv run pytest
    if command -v uv >/dev/null 2>&1; then
      echo "🧪 Running: uv run pytest" >&2
      if ! uv run pytest 2>&1; then
        deny_pr "Tests failed: uv run pytest reported failures. Fix failing tests before creating PR."
      fi
      allow_pr
    fi

    # Try python -m pytest
    if command -v python >/dev/null 2>&1; then
      echo "🧪 Running: python -m pytest" >&2
      if ! python -m pytest 2>&1; then
        deny_pr "Tests failed: python -m pytest reported failures. Fix failing tests before creating PR."
      fi
      allow_pr
    fi
  fi

  # Check for go.mod (Go project)
  if [ -f "go.mod" ] && command -v go >/dev/null 2>&1; then
    echo "🧪 Running: go test ./..." >&2
    if ! go test ./... 2>&1; then
      deny_pr "Tests failed: go test reported failures. Fix failing tests before creating PR."
    fi
    allow_pr
  fi

  # Check for Cargo.toml (Rust project)
  if [ -f "Cargo.toml" ] && command -v cargo >/dev/null 2>&1; then
    echo "🧪 Running: cargo test" >&2
    if ! cargo test 2>&1; then
      deny_pr "Tests failed: cargo test reported failures. Fix failing tests before creating PR."
    fi
    allow_pr
  fi

  # No test configuration found - allow PR creation
  echo "ℹ️  No test configuration found. Allowing PR creation without running tests." >&2
  allow_pr
}

# Main execution
run_tests
