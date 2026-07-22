.PHONY: help install configure dev test lint format type-check check coverage clean pre-commit-install pre-commit-run dry-run info validate-structure validate-plugins install-statusline uninstall-statusline bump-version

# Default commands
UV := uv

# Colors for output
BLUE := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

# Check UV installation
check-uv:
	@which $(UV) > /dev/null || { \
		echo "$(RED)Error: UV is required but not installed$(RESET)"; \
		echo "$(YELLOW)Install UV: https://docs.astral.sh/uv/getting-started/installation/$(RESET)"; \
		echo "$(YELLOW)Quick install: curl -LsSf https://astral.sh/uv/install.sh | sh$(RESET)"; \
		exit 1; \
	}

help: ## Show this help message
	@echo "$(BLUE)Claude Code Arsenal - Available Commands$(RESET)"
	@echo
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo
	@echo "$(YELLOW)Quick Start:$(RESET)"
	@echo "  make dev           # Set up development environment"
	@echo "  make test          # Run tests"
	@echo "  make check         # Run all quality checks"
	@echo "  make install       # Install to ~/.claude"
	@echo
	@echo "$(YELLOW)Optional Features:$(RESET)"
	@echo "  make -C integrations/claude-code/statusline help    # Statusline commands"
	@echo "  make -C integrations/claude-code/claude-hi help            # Session scheduler commands"

# ============================================================================
# Installation
# ============================================================================

install: dev ## Install Claude Code Arsenal to ~/.claude
	@echo "$(BLUE)Installing Claude Code Arsenal...$(RESET)"
	$(UV) run python -m scripts.setup.install

configure: dev ## Configure installed Claude Code Arsenal
	@echo "$(BLUE)Configuring Claude Code Arsenal...$(RESET)"
	$(UV) run python -m scripts.setup.configure

dry-run: dev ## Preview what would be installed (no changes made)
	@echo "$(BLUE)Running installation preview...$(RESET)"
	$(UV) run python -m scripts.setup.install --dry-run --verbose

# ============================================================================
# Development
# ============================================================================

dev: check-uv ## Set up development environment with all dependencies
	@echo "$(BLUE)Setting up development environment...$(RESET)"
	@$(UV) sync --extra dev
	@echo "$(GREEN)Development environment ready$(RESET)"
	@echo "$(YELLOW)Next: Run 'make pre-commit-install' to set up pre-commit hooks$(RESET)"

# ============================================================================
# Code Quality
# ============================================================================

pre-commit-install: dev ## Install pre-commit hooks
	@echo "$(BLUE)Installing pre-commit hooks...$(RESET)"
	$(UV) run pre-commit install
	@echo "$(GREEN)Pre-commit hooks installed$(RESET)"

pre-commit-run: dev ## Run pre-commit hooks on all files
	@echo "$(BLUE)Running pre-commit hooks on all files...$(RESET)"
	$(UV) run pre-commit run --all-files

lint: dev ## Run linting checks
	@echo "$(BLUE)Running linting checks...$(RESET)"
	$(UV) run ruff check .

format: dev ## Format code
	@echo "$(BLUE)Formatting code...$(RESET)"
	$(UV) run ruff format .
	$(UV) run ruff check --fix .

type-check: dev ## Run type checking
	@echo "$(BLUE)Running type checks...$(RESET)"
	$(UV) run pyright scripts/

check: lint type-check ## Run all code quality checks
	@echo "$(GREEN)All checks passed!$(RESET)"

# ============================================================================
# Testing
# ============================================================================

test: dev ## Run unit test suite
	@echo "$(BLUE)Running unit tests...$(RESET)"
	$(UV) run pytest scripts/tests/ -v

coverage: dev ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(RESET)"
	$(UV) run pytest scripts/tests/ --cov=scripts --cov-report=html --cov-report=term

# ============================================================================
# Statusline (Essential Commands Only)
# ============================================================================

install-statusline: validate-structure ## Install statusline to ~/.claude
	@echo "$(BLUE)Installing statusline...$(RESET)"
	@make -C integrations/claude-code/statusline install

uninstall-statusline: ## Remove statusline from ~/.claude
	@echo "$(BLUE)Uninstalling statusline...$(RESET)"
	@make -C integrations/claude-code/statusline uninstall

# ============================================================================
# Utilities
# ============================================================================

clean: ## Clean up test environments and caches
	@echo "$(BLUE)Cleaning up...$(RESET)"
	@rm -rf .venv __pycache__ .pytest_cache htmlcov .coverage .ruff_cache .mypy_cache
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete$(RESET)"

info: ## Show repository information
	@echo "$(BLUE)Claude Code Arsenal Information$(RESET)"
	@echo "Skills:   $$(find skills -name 'SKILL.md' 2>/dev/null | wc -l) files"
	@echo "Scripts:  $$(find scripts -maxdepth 2 -name '*.py' -not -path '*/__pycache__/*' -not -path '*/.*' -not -name 'test_*' -not -name '__init__.py' 2>/dev/null | wc -l) files"

validate-structure: ## Validate repository structure
	@echo "$(BLUE)Validating repository structure...$(RESET)"
	@errors=0; \
	for dir in skills scripts; do \
		if [ ! -d "$$dir" ]; then \
			echo "$(RED)Missing directory: $$dir$(RESET)"; \
			errors=$$((errors + 1)); \
		fi; \
	done; \
	for file in README.md CLAUDE.md; do \
		if [ ! -f "$$file" ]; then \
			echo "$(RED)Missing file: $$file$(RESET)"; \
			errors=$$((errors + 1)); \
		fi; \
	done; \
	if [ $$errors -eq 0 ]; then \
		echo "$(GREEN)Repository structure is valid$(RESET)"; \
	else \
		echo "$(RED)Found $$errors structural issues$(RESET)"; \
		exit 1; \
	fi

validate-plugins: ## Validate both marketplace and plugin manifests
	@echo "$(BLUE)Validating Claude Code plugin manifests...$(RESET)"
	@echo
	@echo "$(BLUE)1. Validating marketplace manifest...$(RESET)"
	@if claude plugin validate . 2>&1 | tee /tmp/marketplace-validation.log; then \
		echo "$(GREEN)✔ Marketplace manifest validation passed$(RESET)"; \
		marketplace_valid=1; \
	else \
		echo "$(RED)✘ Marketplace manifest validation failed$(RESET)"; \
		marketplace_valid=0; \
	fi; \
	echo; \
	echo "$(BLUE)2. Validating plugin manifest...$(RESET)"; \
	if claude plugin validate .claude-plugin/plugin.json 2>&1 | tee /tmp/plugin-validation.log; then \
		echo "$(GREEN)✔ Plugin manifest validation passed$(RESET)"; \
		plugin_valid=1; \
	else \
		echo "$(RED)✘ Plugin manifest validation failed$(RESET)"; \
		plugin_valid=0; \
	fi; \
	echo; \
	if [ $$marketplace_valid -eq 1 ] && [ $$plugin_valid -eq 1 ]; then \
		echo "$(GREEN)✅ All plugin manifests are valid!$(RESET)"; \
		exit 0; \
	else \
		echo "$(RED)❌ Plugin validation failed$(RESET)"; \
		[ $$marketplace_valid -eq 0 ] && echo "  • Marketplace manifest has errors"; \
		[ $$plugin_valid -eq 0 ] && echo "  • Plugin manifest has errors"; \
		exit 1; \
	fi

bump-version: ## Bump all versions declared in .version-bump.json (usage: make bump-version VERSION=x.y.z)
	@if [ -z "$(VERSION)" ]; then echo "$(RED)Error: VERSION is required, e.g. make bump-version VERSION=4.1.0$(RESET)"; exit 1; fi
	$(UV) run python -m scripts.bump_version $(VERSION)

# Default target
.DEFAULT_GOAL := help
