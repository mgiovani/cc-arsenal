#!/bin/bash
# Test runner for all statusline modules

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ANSI colors for output
readonly GREEN='\033[32m'
readonly RED='\033[31m'
readonly YELLOW='\033[33m'
readonly BLUE='\033[34m'
readonly RESET='\033[0m'

# Test tracking
TOTAL_SUITES=0
PASSED_SUITES=0
FAILED_SUITES=0

# Test suite results
declare -a FAILED_SUITES_LIST

print_header() {
    echo -e "${BLUE}================================================"
    echo -e "           STATUSLINE TEST SUITE"
    echo -e "================================================${RESET}"
    echo
}

run_test_suite() {
    local test_file="$1"
    local suite_name="$2"

    echo -e "${YELLOW}Running $suite_name tests...${RESET}"
    echo "----------------------------------------"

    TOTAL_SUITES=$((TOTAL_SUITES + 1))

    if bash "$test_file"; then
        echo -e "${GREEN}✅ $suite_name: ALL TESTS PASSED${RESET}"
        PASSED_SUITES=$((PASSED_SUITES + 1))
    else
        echo -e "${RED}❌ $suite_name: SOME TESTS FAILED${RESET}"
        FAILED_SUITES=$((FAILED_SUITES + 1))
        FAILED_SUITES_LIST+=("$suite_name")
    fi

    echo
}

print_summary() {
    echo -e "${BLUE}================================================"
    echo -e "              TEST RESULTS SUMMARY"
    echo -e "================================================${RESET}"
    echo
    echo "Test Suites Run: $TOTAL_SUITES"
    echo -e "Passed: ${GREEN}$PASSED_SUITES${RESET}"
    echo -e "Failed: ${RED}$FAILED_SUITES${RESET}"
    echo

    if [[ $FAILED_SUITES -gt 0 ]]; then
        echo -e "${RED}Failed Test Suites:${RESET}"
        for suite in "${FAILED_SUITES_LIST[@]}"; do
            echo -e "  ${RED}• $suite${RESET}"
        done
        echo
        echo -e "${RED}💥 SOME TESTS FAILED!${RESET}"
        exit 1
    else
        echo -e "${GREEN}🎉 ALL TEST SUITES PASSED!${RESET}"
        exit 0
    fi
}

check_dependencies() {
    echo "Checking dependencies..."

    local missing_deps=0

    # Check for jq
    if ! command -v jq >/dev/null 2>&1; then
        echo -e "${RED}❌ jq is required but not installed${RESET}"
        missing_deps=$((missing_deps + 1))
    fi

    # Check for git
    if ! command -v git >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  git not found - some git tests may be skipped${RESET}"
    fi

    # Check for bc (for floating point arithmetic)
    if ! command -v bc >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  bc not found - some cost calculation tests may be skipped${RESET}"
    fi

    if [[ $missing_deps -gt 0 ]]; then
        echo -e "${RED}Please install missing dependencies and try again.${RESET}"
        exit 1
    fi

    echo -e "${GREEN}✅ Dependencies OK${RESET}"
    echo
}

run_integration_test() {
    echo -e "${YELLOW}Running integration test...${RESET}"
    echo "----------------------------------------"

    # Test the main statusline script with official Claude Code JSON structure
    # Includes context_window fields for dynamic context size calculation
    local test_json='{
        "hook_event_name": "Status",
        "session_id": "abc123",
        "transcript_path": "/path/to/transcript.json",
        "cwd": "/current/working/directory",
        "model": {
            "id": "claude-opus-5",
            "display_name": "Opus"
        },
        "workspace": {
            "current_dir": "/current/working/directory",
            "project_dir": "/original/project/directory"
        },
        "version": "1.0.80",
        "output_style": {
            "name": "default"
        },
        "cost": {
            "total_cost_usd": 0.01234,
            "total_duration_ms": 45000,
            "total_api_duration_ms": 2300,
            "total_lines_added": 156,
            "total_lines_removed": 23
        },
        "context_window": {
            "total_input_tokens": 15234,
            "total_output_tokens": 4521,
            "context_window_size": 200000
        }
    }'

    local statusline_script="$SCRIPT_DIR/../statusline.sh"

    if [[ ! -f "$statusline_script" ]]; then
        echo -e "${RED}❌ Main statusline script not found: $statusline_script${RESET}"
        return 1
    fi

    # Run statusline and capture output
    local output
    if output=$(echo "$test_json" | "$statusline_script" 2>&1); then
        echo -e "${GREEN}✅ Integration test: Statusline executed successfully${RESET}"
        echo "Output: $output"

        # Validate expected components AND their order: model → context → directory
        # (context is kept right after the model on line 1)
        if [[ "$output" == *"🤖"*"📊"*"📁"* ]]; then
            echo -e "${GREEN}✅ Integration test: Output contains expected components in order${RESET}"
            return 0
        else
            echo -e "${RED}❌ Integration test: Output missing expected components or wrong order${RESET}"
            return 1
        fi
    else
        echo -e "${RED}❌ Integration test: Statusline execution failed${RESET}"
        echo "Error output: $output"
        return 1
    fi
}

suite_name_for() {
    local base
    base="$(basename "$1" .sh)"
    base="${base#test_}"
    base="${base//_/ }"
    # Title-case each word (bash 3.2 safe - no ${var^})
    local word result=""
    for word in $base; do
        result="$result${result:+ }$(echo "${word:0:1}" | tr '[:lower:]' '[:upper:]')${word:1}"
    done
    echo "$result"
}

main() {
    print_header
    check_dependencies

    # Discover and run core module tests (lib/core/, lib/api/, etc.)
    echo -e "${BLUE}=== Core Module Tests ===${RESET}"
    echo
    for test_file in "$SCRIPT_DIR"/core/test_*.sh; do
        [[ -f "$test_file" ]] || continue
        run_test_suite "$test_file" "Core: $(suite_name_for "$test_file") Module"
    done

    # Discover and run top-level module tests
    echo -e "${BLUE}=== Module Tests ===${RESET}"
    echo
    for test_file in "$SCRIPT_DIR"/test_*.sh; do
        [[ -f "$test_file" ]] || continue
        run_test_suite "$test_file" "$(suite_name_for "$test_file") Module"
    done

    # Run integration test
    if run_integration_test; then
        echo -e "${GREEN}✅ Integration Test: PASSED${RESET}"
        TOTAL_SUITES=$((TOTAL_SUITES + 1))
        PASSED_SUITES=$((PASSED_SUITES + 1))
    else
        echo -e "${RED}❌ Integration Test: FAILED${RESET}"
        TOTAL_SUITES=$((TOTAL_SUITES + 1))
        FAILED_SUITES=$((FAILED_SUITES + 1))
        FAILED_SUITES_LIST+=("Integration Test")
    fi
    echo

    print_summary
}

# Execute if run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
