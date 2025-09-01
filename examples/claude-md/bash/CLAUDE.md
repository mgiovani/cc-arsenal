# CLAUDE.md - Bash/Shell Script Project

This file provides guidance to Claude Code (claude.ai/code) when working with Bash scripts and shell-based projects.

## Project Architecture

This is a **Bash/Shell scripting project** following best practices for maintainable, robust shell scripts.

### Project Structure
```
project/
├── bin/                   # Executable scripts
│   ├── main-script       # Main executable (no .sh extension)
│   └── helper-script     # Helper executables
├── lib/                   # Library functions and modules
│   ├── common.sh         # Common utility functions
│   ├── logging.sh        # Logging utilities
│   ├── config.sh         # Configuration management
│   └── validation.sh     # Input validation functions
├── config/                # Configuration files
│   ├── settings.conf     # Main configuration
│   └── environments/     # Environment-specific configs
├── tests/                 # Test scripts
│   ├── test_main.bats    # BATS test files
│   └── fixtures/         # Test data
├── docs/                  # Documentation
├── scripts/               # Build and utility scripts
│   ├── install.sh        # Installation script
│   ├── setup.sh          # Setup script
│   └── build.sh          # Build script
└── Makefile              # Build automation
```

## Development Commands

### Script Execution
```bash
# Make scripts executable
chmod +x bin/*

# Run main script
./bin/main-script

# Run with specific environment
ENV=development ./bin/main-script

# Debug mode
DEBUG=true ./bin/main-script

# Verbose output
VERBOSE=true ./bin/main-script
```

### Testing
```bash
# Install BATS (Bash Automated Testing System)
# On macOS:
brew install bats-core

# On Ubuntu/Debian:
sudo apt-get install bats

# Run all tests
bats tests/

# Run specific test file
bats tests/test_main.bats

# Run with verbose output
bats --verbose tests/
```

### Code Quality
```bash
# Install ShellCheck (static analysis)
# On macOS:
brew install shellcheck

# On Ubuntu/Debian:
sudo apt-get install shellcheck

# Check all scripts
shellcheck bin/* lib/*.sh scripts/*.sh

# Check specific file
shellcheck bin/main-script

# Auto-fix simple issues (if shfmt is installed)
shfmt -w -i 2 bin/* lib/*.sh
```

### Build and Installation
```bash
# Build project
make build

# Install locally
make install

# Install to specific location
make install PREFIX=/usr/local

# Create distribution package
make dist

# Clean build artifacts
make clean
```

## Bash Best Practices

### Script Header Template
```bash
#!/usr/bin/env bash

# Script: script-name
# Description: Brief description of what the script does
# Author: Your Name
# Version: 1.0.0
# Usage: ./script-name [options] [arguments]

set -euo pipefail  # Exit on error, undefined vars, pipe failures
IFS=$'\n\t'        # Secure Internal Field Separator

# Enable debug mode if DEBUG environment variable is set
[[ "${DEBUG:-}" == "true" ]] && set -x

# Script directory and common paths
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
readonly LIB_DIR="${PROJECT_ROOT}/lib"
readonly CONFIG_DIR="${PROJECT_ROOT}/config"

# Source common libraries
source "${LIB_DIR}/common.sh"
source "${LIB_DIR}/logging.sh"
```

### Function Definitions
```bash
# Function template with documentation
#######################################
# Description of what the function does
# Globals:
#   GLOBAL_VAR
# Arguments:
#   $1: First argument description
#   $2: Second argument description
# Outputs:
#   Writes result to stdout
# Returns:
#   0 if successful, non-zero on error
#######################################
function_name() {
  local arg1="${1:-}"
  local arg2="${2:-}"

  # Validate arguments
  if [[ -z "${arg1}" ]]; then
    log_error "First argument is required"
    return 1
  fi

  # Function logic here
  echo "Processing ${arg1} with ${arg2}"
}
```

### Error Handling
```bash
# lib/common.sh - Common utility functions

#######################################
# Display error message and exit
# Arguments:
#   $1: Error message
#   $2: Exit code (optional, defaults to 1)
#######################################
die() {
  local message="${1:-}"
  local code="${2:-1}"

  echo "ERROR: ${message}" >&2
  exit "${code}"
}

#######################################
# Check if command exists
# Arguments:
#   $1: Command name
# Returns:
#   0 if command exists, 1 otherwise
#######################################
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

#######################################
# Check if file is readable
# Arguments:
#   $1: File path
# Returns:
#   0 if file is readable, 1 otherwise
#######################################
is_readable() {
  [[ -r "$1" ]]
}

#######################################
# Cleanup function for trap
#######################################
cleanup() {
  local exit_code=$?

  # Cleanup temporary files
  [[ -n "${TEMP_DIR:-}" ]] && rm -rf "${TEMP_DIR}"

  # Log completion
  if [[ ${exit_code} -eq 0 ]]; then
    log_info "Script completed successfully"
  else
    log_error "Script failed with exit code ${exit_code}"
  fi

  exit ${exit_code}
}

# Set up cleanup trap
trap cleanup EXIT INT TERM
```

### Configuration Management
```bash
# lib/config.sh - Configuration management

#######################################
# Load configuration from file
# Arguments:
#   $1: Config file path
#######################################
load_config() {
  local config_file="${1:-}"

  if [[ ! -r "${config_file}" ]]; then
    log_warn "Config file not found or not readable: ${config_file}"
    return 1
  fi

  # Source configuration file safely
  # shellcheck disable=SC1090
  source "${config_file}"

  log_info "Configuration loaded from ${config_file}"
}

#######################################
# Get configuration value with default
# Arguments:
#   $1: Variable name
#   $2: Default value
# Outputs:
#   Configuration value or default
#######################################
get_config() {
  local var_name="${1:-}"
  local default_value="${2:-}"

  if [[ -n "${!var_name:-}" ]]; then
    echo "${!var_name}"
  else
    echo "${default_value}"
  fi
}

# Default configuration
readonly DEFAULT_CONFIG_FILE="${CONFIG_DIR}/settings.conf"

# Environment-specific overrides
readonly ENV="${ENV:-development}"
readonly ENV_CONFIG_FILE="${CONFIG_DIR}/environments/${ENV}.conf"

# Load configurations
load_config "${DEFAULT_CONFIG_FILE}"
[[ -r "${ENV_CONFIG_FILE}" ]] && load_config "${ENV_CONFIG_FILE}"
```

### Logging System
```bash
# lib/logging.sh - Logging utilities

# Colors for terminal output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Log levels
readonly LOG_LEVEL_ERROR=1
readonly LOG_LEVEL_WARN=2
readonly LOG_LEVEL_INFO=3
readonly LOG_LEVEL_DEBUG=4

# Current log level (can be overridden by environment)
LOG_LEVEL="${LOG_LEVEL:-$LOG_LEVEL_INFO}"

#######################################
# Generic logging function
# Arguments:
#   $1: Log level
#   $2: Color code
#   $3: Message
#######################################
_log() {
  local level="$1"
  local color="$2"
  local message="$3"

  if [[ ${LOG_LEVEL} -ge ${level} ]]; then
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    if [[ -t 1 ]]; then  # If stdout is a terminal
      printf "${color}[%s] %s${NC}\n" "${timestamp}" "${message}" >&2
    else
      printf "[%s] %s\n" "${timestamp}" "${message}" >&2
    fi
  fi
}

log_error() { _log $LOG_LEVEL_ERROR "$RED" "ERROR: $*"; }
log_warn()  { _log $LOG_LEVEL_WARN "$YELLOW" "WARN: $*"; }
log_info()  { _log $LOG_LEVEL_INFO "$GREEN" "INFO: $*"; }
log_debug() { _log $LOG_LEVEL_DEBUG "$BLUE" "DEBUG: $*"; }
```

### Command Line Argument Parsing
```bash
#!/usr/bin/env bash

#######################################
# Display usage information
#######################################
usage() {
  cat << EOF
Usage: ${0##*/} [OPTIONS] [ARGUMENTS]

Description of what this script does.

OPTIONS:
    -h, --help          Show this help message
    -v, --verbose       Enable verbose output
    -d, --debug         Enable debug mode
    -c, --config FILE   Configuration file path
    -o, --output DIR    Output directory

ARGUMENTS:
    input_file          Input file to process

EXAMPLES:
    ${0##*/} --config custom.conf input.txt
    ${0##*/} -v -o /tmp/output data.csv

EOF
}

#######################################
# Parse command line arguments
#######################################
parse_args() {
  while [[ $# -gt 0 ]]; do
    case $1 in
      -h|--help)
        usage
        exit 0
        ;;
      -v|--verbose)
        VERBOSE=true
        LOG_LEVEL=$LOG_LEVEL_DEBUG
        shift
        ;;
      -d|--debug)
        DEBUG=true
        set -x
        shift
        ;;
      -c|--config)
        CONFIG_FILE="$2"
        shift 2
        ;;
      -o|--output)
        OUTPUT_DIR="$2"
        shift 2
        ;;
      --)
        shift
        break
        ;;
      -*)
        die "Unknown option: $1"
        ;;
      *)
        # Positional argument
        POSITIONAL_ARGS+=("$1")
        shift
        ;;
    esac
  done

  # Validate required arguments
  if [[ ${#POSITIONAL_ARGS[@]} -eq 0 ]]; then
    die "Input file is required"
  fi

  INPUT_FILE="${POSITIONAL_ARGS[0]}"
}

# Initialize variables
VERBOSE=false
DEBUG=false
CONFIG_FILE="${DEFAULT_CONFIG_FILE}"
OUTPUT_DIR="/tmp"
POSITIONAL_ARGS=()

# Parse arguments
parse_args "$@"
```

## Testing with BATS

### Test File Template
```bash
#!/usr/bin/env bats

# tests/test_main.bats

# Setup function run before each test
setup() {
  # Create temporary directory for test
  export TEST_TEMP_DIR="$(mktemp -d)"

  # Source the script functions
  source "${BATS_TEST_DIRNAME}/../lib/common.sh"

  # Set up test data
  echo "test data" > "${TEST_TEMP_DIR}/test_file.txt"
}

# Teardown function run after each test
teardown() {
  # Clean up temporary directory
  [[ -n "${TEST_TEMP_DIR:-}" ]] && rm -rf "${TEST_TEMP_DIR}"
}

@test "function returns success for valid input" {
  run function_name "valid_input"

  [ "$status" -eq 0 ]
  [ "${lines[0]}" = "Expected output" ]
}

@test "function fails with invalid input" {
  run function_name ""

  [ "$status" -eq 1 ]
  [[ "$output" =~ "ERROR:" ]]
}

@test "script processes file correctly" {
  local test_file="${TEST_TEMP_DIR}/test_file.txt"

  run "${BATS_TEST_DIRNAME}/../bin/main-script" "${test_file}"

  [ "$status" -eq 0 ]
  [ -f "${TEST_TEMP_DIR}/output.txt" ]
}

@test "script handles missing file gracefully" {
  run "${BATS_TEST_DIRNAME}/../bin/main-script" "nonexistent.txt"

  [ "$status" -ne 0 ]
  [[ "$output" =~ "File not found" ]]
}
```

## Makefile Template

```makefile
# Makefile for Bash project

SHELL := /bin/bash
.DEFAULT_GOAL := help
.PHONY: help install test lint clean build dist

# Configuration
PREFIX ?= /usr/local
BIN_DIR = $(PREFIX)/bin
LIB_DIR = $(PREFIX)/lib
CONFIG_DIR = $(PREFIX)/etc

# Colors
RED := \033[31m
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
NC := \033[0m

help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'

install: ## Install scripts to system
	@echo "$(BLUE)Installing to $(PREFIX)...$(NC)"
	@install -d $(BIN_DIR) $(LIB_DIR) $(CONFIG_DIR)
	@install -m 755 bin/* $(BIN_DIR)/
	@install -m 644 lib/* $(LIB_DIR)/
	@install -m 644 config/*.conf $(CONFIG_DIR)/
	@echo "$(GREEN)Installation complete$(NC)"

test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	@if command -v bats >/dev/null 2>&1; then \
		bats tests/; \
	else \
		echo "$(RED)BATS is not installed. Install it first.$(NC)"; \
		exit 1; \
	fi

lint: ## Check scripts with shellcheck
	@echo "$(BLUE)Linting scripts...$(NC)"
	@if command -v shellcheck >/dev/null 2>&1; then \
		shellcheck bin/* lib/*.sh scripts/*.sh; \
		echo "$(GREEN)Linting complete$(NC)"; \
	else \
		echo "$(RED)ShellCheck is not installed. Install it first.$(NC)"; \
		exit 1; \
	fi

format: ## Format scripts with shfmt
	@echo "$(BLUE)Formatting scripts...$(NC)"
	@if command -v shfmt >/dev/null 2>&1; then \
		shfmt -w -i 2 bin/* lib/*.sh scripts/*.sh; \
		echo "$(GREEN)Formatting complete$(NC)"; \
	else \
		echo "$(YELLOW)shfmt is not installed. Skipping formatting.$(NC)"; \
	fi

build: lint test ## Build and validate project
	@echo "$(GREEN)Build complete$(NC)"

clean: ## Clean build artifacts
	@echo "$(BLUE)Cleaning...$(NC)"
	@rm -rf dist/
	@rm -f *.tar.gz
	@echo "$(GREEN)Clean complete$(NC)"

dist: build ## Create distribution package
	@echo "$(BLUE)Creating distribution...$(NC)"
	@mkdir -p dist
	@tar -czf dist/project-$(shell date +%Y%m%d).tar.gz \
		bin/ lib/ config/ docs/ README.md LICENSE
	@echo "$(GREEN)Distribution created$(NC)"

dev-setup: ## Set up development environment
	@echo "$(BLUE)Setting up development environment...$(NC)"
	@./scripts/setup.sh
	@echo "$(GREEN)Development setup complete$(NC)"
```

## Environment Variables

```bash
# Common environment variables for shell scripts

# Application settings
export APP_NAME="${APP_NAME:-my-app}"
export APP_VERSION="${APP_VERSION:-1.0.0}"
export APP_ENV="${APP_ENV:-development}"

# Paths
export CONFIG_DIR="${CONFIG_DIR:-./config}"
export LOG_DIR="${LOG_DIR:-./logs}"
export DATA_DIR="${DATA_DIR:-./data}"
export TEMP_DIR="${TEMP_DIR:-/tmp}"

# Logging
export LOG_LEVEL="${LOG_LEVEL:-3}"  # 1=error, 2=warn, 3=info, 4=debug
export LOG_FILE="${LOG_FILE:-${LOG_DIR}/${APP_NAME}.log}"

# Debugging
export DEBUG="${DEBUG:-false}"
export VERBOSE="${VERBOSE:-false}"

# Performance
export PARALLEL_JOBS="${PARALLEL_JOBS:-4}"
export TIMEOUT="${TIMEOUT:-300}"  # 5 minutes

# Security
export UMASK="${UMASK:-077}"  # Restrictive permissions by default
```
