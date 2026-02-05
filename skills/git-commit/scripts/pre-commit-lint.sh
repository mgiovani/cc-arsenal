#!/usr/bin/env bash
# Hook: pre-commit-lint
# Purpose: Run linter before git commit to ensure code quality
# Event: PreToolUse (before "git commit" command)
#
# This hook:
# 1. Detects the project type (Node.js, Python, etc.)
# 2. Runs the appropriate linter if configured
# 3. Blocks commit if linting fails
# 4. Allows commit if linting passes or no linter is configured

set -euo pipefail

# JSON response helper functions
deny_commit() {
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

allow_commit() {
  # Implicit allow - no output needed
  exit 0
}

# Function to detect and run linter
run_linter() {
  local project_root
  project_root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)

  cd "$project_root" || exit 1

  # Check for Makefile with lint target (highest priority)
  if [ -f "Makefile" ] && grep -q "^lint:" Makefile; then
    echo "🔍 Running: make lint" >&2
    if ! make lint 2>&1; then
      deny_commit "Linting failed: make lint reported errors. Fix lint errors before committing."
    fi
    allow_commit
  fi

  # Check for package.json (Node.js project)
  if [ -f "package.json" ]; then
    # Check if lint script exists
    if command -v jq >/dev/null 2>&1 && jq -e '.scripts.lint' package.json >/dev/null 2>&1; then
      echo "🔍 Running: npm run lint" >&2

      # Detect package manager
      if [ -f "bun.lockb" ] && command -v bun >/dev/null 2>&1; then
        if ! bun run lint 2>&1; then
          deny_commit "Linting failed: bun run lint reported errors. Fix lint errors before committing."
        fi
      elif [ -f "pnpm-lock.yaml" ] && command -v pnpm >/dev/null 2>&1; then
        if ! pnpm run lint 2>&1; then
          deny_commit "Linting failed: pnpm run lint reported errors. Fix lint errors before committing."
        fi
      elif [ -f "yarn.lock" ] && command -v yarn >/dev/null 2>&1; then
        if ! yarn run lint 2>&1; then
          deny_commit "Linting failed: yarn run lint reported errors. Fix lint errors before committing."
        fi
      elif command -v npm >/dev/null 2>&1; then
        if ! npm run lint 2>&1; then
          deny_commit "Linting failed: npm run lint reported errors. Fix lint errors before committing."
        fi
      fi
      allow_commit
    fi

    # Fallback: Try running eslint directly
    if command -v eslint >/dev/null 2>&1; then
      echo "🔍 Running: eslint ." >&2
      if ! eslint . 2>&1; then
        deny_commit "Linting failed: eslint reported errors. Fix lint errors before committing."
      fi
      allow_commit
    fi

    # If bun is available, try bunx eslint
    if [ -f "bun.lockb" ] && command -v bunx >/dev/null 2>&1; then
      echo "🔍 Running: bunx eslint ." >&2
      if ! bunx eslint . 2>&1; then
        deny_commit "Linting failed: bunx eslint reported errors. Fix lint errors before committing."
      fi
      allow_commit
    fi
  fi

  # Check for pyproject.toml (Python project)
  if [ -f "pyproject.toml" ]; then
    # Check for ruff (modern, fast linter)
    if command -v ruff >/dev/null 2>&1; then
      echo "🔍 Running: ruff check ." >&2
      if ! ruff check . 2>&1; then
        deny_commit "Linting failed: ruff check reported errors. Fix lint errors before committing."
      fi
      allow_commit
    fi

    # Fallback to uv run ruff
    if command -v uv >/dev/null 2>&1; then
      echo "🔍 Running: uv run ruff check ." >&2
      if ! uv run ruff check . 2>&1; then
        deny_commit "Linting failed: uv run ruff check reported errors. Fix lint errors before committing."
      fi
      allow_commit
    fi

    # Fallback to flake8
    if command -v flake8 >/dev/null 2>&1; then
      echo "🔍 Running: flake8 ." >&2
      if ! flake8 . 2>&1; then
        deny_commit "Linting failed: flake8 reported errors. Fix lint errors before committing."
      fi
      allow_commit
    fi
  fi

  # Check for .rubocop.yml (Ruby project)
  if [ -f ".rubocop.yml" ] && command -v rubocop >/dev/null 2>&1; then
    echo "🔍 Running: rubocop" >&2
    if ! rubocop 2>&1; then
      deny_commit "Linting failed: rubocop reported errors. Fix lint errors before committing."
    fi
    allow_commit
  fi

  # Check for .golangci.yml (Go project)
  if [ -f ".golangci.yml" ] && command -v golangci-lint >/dev/null 2>&1; then
    echo "🔍 Running: golangci-lint run" >&2
    if ! golangci-lint run 2>&1; then
      deny_commit "Linting failed: golangci-lint reported errors. Fix lint errors before committing."
    fi
    allow_commit
  fi

  # No linter configuration found - allow commit
  echo "ℹ️  No linter configuration found. Allowing commit without linting." >&2
  allow_commit
}

# Main execution
run_linter
