.PHONY: help install configure test clean dev lint format check dry-run backup restore check-uv setup-dev pre-commit-install pre-commit-update validate-plugins

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
	@echo "$(YELLOW)Quick Start Examples:$(RESET)"
	@echo "  make install              # Install Claude Code Arsenal"
	@echo "  make claude-hi-setup      # Replace cron workarounds with smart scheduling"
	@echo "  make claude-hi-standard   # Quick 9am/2pm/7pm schedule"
	@echo "  make claude-slash-setup   # Automate custom slash commands daily"
	@echo "  make statusline-install   # Add enhanced statusline"
	@echo
	@echo "$(YELLOW)Development Examples:$(RESET)"
	@echo "  make dev                  # Set up development environment"
	@echo "  make pre-commit-install   # Install pre-commit hooks"
	@echo "  make lint                 # Run code quality checks"
	@echo "  make test                 # Run unit tests"
	@echo "  make dry-run              # Preview installation"

# Installation
install: setup-dev ## Install Claude Code Arsenal to ~/.claude
	@echo "$(BLUE)Installing Claude Code Arsenal...$(RESET)"
	$(UV) run python -m scripts.setup.install

configure: setup-dev ## Configure installed Claude Code Arsenal
	@echo "$(BLUE)Configuring Claude Code Arsenal...$(RESET)"
	$(UV) run python -m scripts.setup.configure

force-install: setup-dev ## Force install without prompts
	@echo "$(YELLOW)Force installing (no prompts)...$(RESET)"
	$(UV) run python -m scripts.setup.install --force --conflict-resolution backup

dry-run: setup-dev ## Preview what would be installed (no changes made)
	@echo "$(BLUE)Running installation preview...$(RESET)"
	$(UV) run python -m scripts.setup.install --dry-run --verbose

# Backup
backup: ## Backup current ~/.claude configuration
	@echo "$(BLUE)Creating backup of ~/.claude...$(RESET)"
	@if [ -d ~/.claude ]; then \
		cp -r ~/.claude ~/.claude-backup-$$(date +%s); \
		echo "$(GREEN)Backup created: ~/.claude-backup-$$(date +%s)$(RESET)"; \
	else \
		echo "$(YELLOW)No ~/.claude directory found$(RESET)"; \
	fi

restore-latest: ## Restore latest ~/.claude backup
	@echo "$(BLUE)Restoring latest ~/.claude backup...$(RESET)"
	@LATEST=$$(ls -t ~/.claude-backup-* 2>/dev/null | head -1); \
	if [ -n "$$LATEST" ]; then \
		rm -rf ~/.claude; \
		cp -r "$$LATEST" ~/.claude; \
		echo "$(GREEN)Restored from: $$LATEST$(RESET)"; \
	else \
		echo "$(RED)No backup found$(RESET)"; \
	fi

list-backups: ## List available ~/.claude backups
	@echo "$(BLUE)Available ~/.claude backups:$(RESET)"
	@ls -la ~/.claude-backup-* 2>/dev/null || echo "$(YELLOW)No backups found$(RESET)"

# Development
setup-dev: check-uv ## Set up development environment with all dependencies
	@echo "$(BLUE)Setting up development environment...$(RESET)"
	@$(UV) sync --extra dev
	@echo "$(GREEN)Development environment ready$(RESET)"
	@echo "$(YELLOW)Run 'make pre-commit-install' to set up pre-commit hooks$(RESET)"

dev: setup-dev ## Alias for setup-dev
	@echo "$(GREEN)Development setup complete$(RESET)"

# Pre-commit management
pre-commit-install: setup-dev ## Install pre-commit hooks
	@echo "$(BLUE)Installing pre-commit hooks...$(RESET)"
	$(UV) run pre-commit install
	@echo "$(GREEN)Pre-commit hooks installed$(RESET)"

pre-commit-update: setup-dev ## Update pre-commit hooks to latest versions
	@echo "$(BLUE)Updating pre-commit hooks...$(RESET)"
	$(UV) run pre-commit autoupdate
	@echo "$(GREEN)Pre-commit hooks updated$(RESET)"

pre-commit-run: setup-dev ## Run pre-commit hooks on all files
	@echo "$(BLUE)Running pre-commit hooks on all files...$(RESET)"
	$(UV) run pre-commit run --all-files

# Quality
lint: setup-dev ## Run linting checks
	@echo "$(BLUE)Running linting checks...$(RESET)"
	$(UV) run ruff check .

format: setup-dev ## Format code
	@echo "$(BLUE)Formatting code...$(RESET)"
	$(UV) run ruff format .
	$(UV) run ruff check --fix .

type-check: setup-dev ## Run type checking
	@echo "$(BLUE)Running type checks...$(RESET)"
	$(UV) run pyright scripts/

check: lint type-check ## Run all code quality checks
	@echo "$(GREEN)All checks passed!$(RESET)"

# Testing
test: setup-dev ## Run unit test suite
	@echo "$(BLUE)Running unit tests...$(RESET)"
	$(UV) run pytest scripts/tests/ -v

coverage: setup-dev ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(RESET)"
	$(UV) run pytest scripts/tests/ --cov=scripts --cov-report=html --cov-report=term

# Utility
clean: ## Clean up test environments and caches
	@echo "$(BLUE)Cleaning up...$(RESET)"
	@rm -rf test-env/
	@rm -rf .venv
	@rm -rf __pycache__
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .pytest_cache
	@rm -rf htmlcov
	@rm -rf .coverage
	@rm -rf .ruff_cache
	@echo "$(GREEN)Cleanup complete$(RESET)"

# UV-specific commands
uv-sync: check-uv ## Sync dependencies (basic)
	@echo "$(BLUE)Syncing UV dependencies...$(RESET)"
	$(UV) sync

uv-sync-dev: check-uv ## Sync dependencies with dev extras
	@echo "$(BLUE)Syncing UV dependencies with dev extras...$(RESET)"
	$(UV) sync --extra dev

uv-add: check-uv ## Add a dependency (usage: make uv-add PACKAGE=package-name)
	@if [ -z "$(PACKAGE)" ]; then \
		echo "$(RED)Usage: make uv-add PACKAGE=package-name$(RESET)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Adding package: $(PACKAGE)$(RESET)"
	$(UV) add $(PACKAGE)

uv-add-dev: check-uv ## Add a dev dependency (usage: make uv-add-dev PACKAGE=package-name)
	@if [ -z "$(PACKAGE)" ]; then \
		echo "$(RED)Usage: make uv-add-dev PACKAGE=package-name$(RESET)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Adding dev package: $(PACKAGE)$(RESET)"
	$(UV) add --group dev $(PACKAGE)

uv-remove: check-uv ## Remove a dependency (usage: make uv-remove PACKAGE=package-name)
	@if [ -z "$(PACKAGE)" ]; then \
		echo "$(RED)Usage: make uv-remove PACKAGE=package-name$(RESET)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Removing package: $(PACKAGE)$(RESET)"
	$(UV) remove $(PACKAGE)

uv-update: check-uv ## Update all dependencies
	@echo "$(BLUE)Updating UV dependencies...$(RESET)"
	$(UV) sync --upgrade

uv-lock: check-uv ## Update lock file
	@echo "$(BLUE)Updating UV lock file...$(RESET)"
	$(UV) lock

uv-tree: setup-dev ## Show dependency tree
	@echo "$(BLUE)UV Dependency Tree:$(RESET)"
	$(UV) tree

uv-run: setup-dev ## Run a command in UV environment (usage: make uv-run CMD="command")
	@if [ -z "$(CMD)" ]; then \
		echo "$(RED)Usage: make uv-run CMD=\"command\"$(RESET)"; \
		echo "$(YELLOW)Example: make uv-run CMD=\"python --version\"$(RESET)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Running: $(CMD)$(RESET)"
	$(UV) run $(CMD)

show-structure: ## Show repository structure
	@echo "$(BLUE)Repository structure:$(RESET)"
	@tree -I '__pycache__|.venv|.git|*.pyc' . || find . -type d -name ".git" -prune -o -type d -name "__pycache__" -prune -o -type f -print | head -30

validate-structure: ## Validate repository structure
	@echo "$(BLUE)Validating repository structure...$(RESET)"
	@errors=0; \
	for dir in agents commands hooks scripts; do \
		if [ ! -d "$$dir" ]; then \
			echo "$(RED)Missing directory: $$dir$(RESET)"; \
			errors=$$((errors + 1)); \
		fi; \
	done; \
	for file in README.md; do \
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

# Generation
generate-agent: setup-dev ## Generate a new agent (make generate-agent NAME=my-agent CATEGORY=development)
	@if [ -z "$(NAME)" ]; then \
		echo "$(RED)Usage: make generate-agent NAME=agent-name CATEGORY=development$(RESET)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Generating agent: $(NAME)$(RESET)"
	$(UV) run python -m scripts.generators.agent_generator --name "$(NAME)" --category "$(or $(CATEGORY),development)"

# Statusline Management
install-statusline-force: ## Install statusline to ~/.claude (symlink with conflict resolution, skip validation)
	@echo "$(BLUE)Installing statusline to ~/.claude...$(RESET)"
	@if [ ! -d ~/.claude ]; then \
		echo "$(YELLOW)Creating ~/.claude directory$(RESET)"; \
		mkdir -p ~/.claude; \
	fi
	@# Check for existing statusline installation
	@if [ -L ~/.claude/scripts/claude/statusline ] || [ -d ~/.claude/scripts/claude/statusline ]; then \
		echo "$(YELLOW)⚠️  Existing statusline installation found$(RESET)"; \
		if [ -L ~/.claude/scripts/claude/statusline ]; then \
			echo "  Current installation: $$(readlink ~/.claude/scripts/claude/statusline) (symlink)"; \
		else \
			echo "  Current installation: ~/.claude/scripts/claude/statusline (directory)"; \
		fi; \
		echo; \
		read -p "Do you want to replace the existing installation? (y/N): " replace; \
		if [ "$$replace" != "y" ] && [ "$$replace" != "Y" ]; then \
			echo "$(YELLOW)Installation cancelled by user$(RESET)"; \
			exit 0; \
		fi; \
		echo; \
		read -p "Create backup of existing installation? (Y/n): " backup; \
		if [ "$$backup" != "n" ] && [ "$$backup" != "N" ]; then \
			mkdir -p ~/.claude/backups/statusline; \
			backup_name="backup-$$(date +%s)"; \
			echo "$(BLUE)Creating backup: ~/.claude/backups/statusline/$$backup_name$(RESET)"; \
			if [ -L ~/.claude/scripts/claude/statusline ]; then \
				echo "Existing installation is a symlink, copying target content"; \
				cp -r "$$(readlink ~/.claude/scripts/claude/statusline)" ~/.claude/backups/statusline/$$backup_name; \
			else \
				cp -r ~/.claude/scripts/claude/statusline ~/.claude/backups/statusline/$$backup_name; \
			fi; \
			echo "$(GREEN)Backup created: ~/.claude/backups/statusline/$$backup_name$(RESET)"; \
		else \
			echo "$(YELLOW)Skipping backup creation$(RESET)"; \
		fi; \
		echo "$(YELLOW)Removing existing statusline installation$(RESET)"; \
		rm -rf ~/.claude/scripts/claude/statusline; \
	fi
	@echo "$(GREEN)Creating statusline symlink$(RESET)"
	@mkdir -p ~/.claude/scripts/claude
	@ln -sf "$$(pwd)/scripts/claude/statusline" ~/.claude/scripts/claude/statusline
	@echo "$(GREEN)🔧 Configuring Claude Code settings...$(RESET)"
	@scripts/claude/statusline/lib/claude_config.sh install force
	@echo "$(GREEN)✅ Statusline fully installed and configured!$(RESET)"
	@echo
	@echo "$(BLUE)🎉 Ready to use:$(RESET)"
	@echo "  • Statusline is automatically active in Claude Code"
	@echo "  • No manual configuration needed"
	@echo "  • Restart Claude Code to see the statusline"
	@echo
	@echo "$(BLUE)💡 Files created:$(RESET)"
	@echo "  • Settings: ~/.claude/settings.json"
	@echo "  • Config: ~/.claude/cc-arsenal/statusline_config.json"
	@echo "  • Usage data: ~/.claude/cc-arsenal/usage_tracking.json"

install-statusline: validate-structure ## Install statusline to ~/.claude (symlink with conflict resolution)
	@echo "$(BLUE)Installing statusline to ~/.claude...$(RESET)"
	@if [ ! -d ~/.claude ]; then \
		echo "$(YELLOW)Creating ~/.claude directory$(RESET)"; \
		mkdir -p ~/.claude; \
	fi
	@# Check for existing statusline installation
	@if [ -L ~/.claude/scripts/claude/statusline ] || [ -d ~/.claude/scripts/claude/statusline ]; then \
		echo "$(YELLOW)⚠️  Existing statusline installation found$(RESET)"; \
		if [ -L ~/.claude/scripts/claude/statusline ]; then \
			echo "  Current installation: $$(readlink ~/.claude/scripts/claude/statusline) (symlink)"; \
		else \
			echo "  Current installation: ~/.claude/scripts/claude/statusline (directory)"; \
		fi; \
		echo; \
		read -p "Do you want to replace the existing installation? (y/N): " replace; \
		if [ "$$replace" != "y" ] && [ "$$replace" != "Y" ]; then \
			echo "$(YELLOW)Installation cancelled by user$(RESET)"; \
			exit 0; \
		fi; \
		echo; \
		read -p "Create backup of existing installation? (Y/n): " backup; \
		if [ "$$backup" != "n" ] && [ "$$backup" != "N" ]; then \
			mkdir -p ~/.claude/backups/statusline; \
			backup_name="backup-$$(date +%s)"; \
			echo "$(BLUE)Creating backup: ~/.claude/backups/statusline/$$backup_name$(RESET)"; \
			if [ -L ~/.claude/scripts/claude/statusline ]; then \
				echo "Existing installation is a symlink, copying target content"; \
				cp -r "$$(readlink ~/.claude/scripts/claude/statusline)" ~/.claude/backups/statusline/$$backup_name; \
			else \
				cp -r ~/.claude/scripts/claude/statusline ~/.claude/backups/statusline/$$backup_name; \
			fi; \
			echo "$(GREEN)Backup created: ~/.claude/backups/statusline/$$backup_name$(RESET)"; \
		else \
			echo "$(YELLOW)Skipping backup creation$(RESET)"; \
		fi; \
		echo "$(YELLOW)Removing existing statusline installation$(RESET)"; \
		rm -rf ~/.claude/scripts/claude/statusline; \
	fi
	@echo "$(GREEN)Creating statusline symlink$(RESET)"
	@mkdir -p ~/.claude/scripts/claude
	@ln -sf "$$(pwd)/scripts/claude/statusline" ~/.claude/scripts/claude/statusline
	@echo "$(GREEN)🔧 Configuring Claude Code settings...$(RESET)"
	@scripts/claude/statusline/lib/claude_config.sh install force
	@echo "$(GREEN)✅ Statusline fully installed and configured!$(RESET)"
	@echo
	@echo "$(BLUE)🎉 Ready to use:$(RESET)"
	@echo "  • Statusline is automatically active in Claude Code"
	@echo "  • No manual configuration needed"
	@echo "  • Restart Claude Code to see the statusline"
	@echo
	@echo "$(BLUE)💡 Files created:$(RESET)"
	@echo "  • Settings: ~/.claude/settings.json"
	@echo "  • Config: ~/.claude/cc-arsenal/statusline_config.json"
	@echo "  • Usage data: ~/.claude/cc-arsenal/usage_tracking.json"

force-install-statusline: validate-structure ## Force install statusline without prompts (with backup)
	@echo "$(YELLOW)Force installing statusline (no prompts)...$(RESET)"
	@if [ ! -d ~/.claude ]; then \
		echo "$(YELLOW)Creating ~/.claude directory$(RESET)"; \
		mkdir -p ~/.claude; \
	fi
	@# Create backup if existing installation found
	@if [ -L ~/.claude/scripts/claude/statusline ] || [ -d ~/.claude/scripts/claude/statusline ]; then \
		mkdir -p ~/.claude/backups/statusline; \
		backup_name="backup-$$(date +%s)"; \
		echo "$(BLUE)Creating automatic backup: ~/.claude/backups/statusline/$$backup_name$(RESET)"; \
		if [ -L ~/.claude/scripts/claude/statusline ]; then \
			echo "Existing installation is a symlink, copying target content"; \
			cp -r "$$(readlink ~/.claude/scripts/claude/statusline)" ~/.claude/backups/statusline/$$backup_name; \
		else \
			cp -r ~/.claude/scripts/claude/statusline ~/.claude/backups/statusline/$$backup_name; \
		fi; \
		echo "$(GREEN)Backup created: ~/.claude/backups/statusline/$$backup_name$(RESET)"; \
		echo "$(YELLOW)Removing existing statusline installation$(RESET)"; \
		rm -rf ~/.claude/scripts/claude/statusline; \
	fi
	@echo "$(GREEN)Creating statusline symlink$(RESET)"
	@mkdir -p ~/.claude/scripts/claude
	@ln -sf "$$(pwd)/scripts/claude/statusline" ~/.claude/scripts/claude/statusline
	@echo "$(GREEN)🔧 Configuring Claude Code settings...$(RESET)"
	@scripts/claude/statusline/lib/claude_config.sh install force
	@echo "$(GREEN)✅ Statusline force-installed and configured!$(RESET)"
	@echo "$(BLUE)🎉 Automatically configured - just restart Claude Code!$(RESET)"

uninstall-statusline: ## Remove statusline from ~/.claude
	@echo "$(BLUE)Uninstalling statusline...$(RESET)"
	@if [ -L ~/.claude/scripts/claude/statusline ] || [ -d ~/.claude/scripts/claude/statusline ]; then \
		echo "$(YELLOW)Found existing statusline installation$(RESET)"; \
		read -p "Are you sure you want to uninstall? (y/N): " confirm; \
		if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
			echo "$(BLUE)Removing Claude Code settings...$(RESET)"; \
			scripts/claude/statusline/lib/claude_config.sh uninstall; \
			echo "$(BLUE)Removing statusline files...$(RESET)"; \
			rm -rf ~/.claude/scripts/claude/statusline; \
			echo "$(GREEN)Statusline completely uninstalled$(RESET)"; \
		else \
			echo "$(YELLOW)Uninstall cancelled$(RESET)"; \
		fi; \
	else \
		echo "$(YELLOW)Statusline not found$(RESET)"; \
	fi

configure-statusline: ## Configure statusline interactively
	@echo "$(BLUE)Configuring Claude Code Statusline...$(RESET)"
	@if [ ! -f scripts/claude/statusline/configure_statusline.py ]; then \
		echo "$(RED)Configuration script not found$(RESET)"; \
		exit 1; \
	fi
	@python3 scripts/claude/statusline/configure_statusline.py

statusline-status: ## Show current statusline configuration status
	@echo "$(BLUE)Claude Code Statusline Status$(RESET)"
	@scripts/claude/statusline/lib/claude_config.sh show

list-statusline-backups: ## List available statusline backups
	@echo "$(BLUE)Available statusline backups:$(RESET)"
	@if [ -d ~/.claude/backups/statusline ] && ls ~/.claude/backups/statusline/backup-* 2>/dev/null | head -10; then \
		echo; \
		echo "$(YELLOW)To restore a backup:$(RESET)"; \
		echo "  1. Run 'make uninstall-statusline'"; \
		echo "  2. Copy backup: cp -r ~/.claude/backups/statusline/backup-TIMESTAMP ~/.claude/scripts/claude/statusline"; \
		echo "  3. Or run 'make install-statusline' to install fresh version"; \
	else \
		echo "$(YELLOW)No statusline backups found$(RESET)"; \
	fi

test-statusline: ## Test statusline with official Claude Code JSON structure
	@echo "$(BLUE)Testing statusline...$(RESET)"
	@echo "{\"hook_event_name\":\"Status\",\"session_id\":\"test123\",\"model\":{\"id\":\"claude-opus-4-1\",\"display_name\":\"Opus\"},\"workspace\":{\"current_dir\":\"$$(pwd)\",\"project_dir\":\"$$(pwd)\"},\"version\":\"1.0.80\",\"output_style\":{\"name\":\"default\"},\"cost\":{\"total_cost_usd\":0.01234,\"total_duration_ms\":45000,\"total_api_duration_ms\":2300,\"total_lines_added\":156,\"total_lines_removed\":23}}" | scripts/claude/statusline/statusline.sh

test-statusline-units: ## Run comprehensive unit tests for statusline modules
	@echo "$(BLUE)Running statusline unit tests...$(RESET)"
	@scripts/claude/statusline/tests/run_tests.sh

# Docs
docs: ## Generate documentation
	@echo "$(BLUE)Generating documentation...$(RESET)"
	@echo "$(YELLOW)Documentation generation not implemented yet$(RESET)"

# Debug
debug-install: setup-env ## Debug installation issues
	@echo "$(BLUE)Debugging installation...$(RESET)"
	@echo "Repository root: $$(pwd)"
	@echo "Python version: $$($(PYTHON) --version)"
	@echo "UV version: $$($(UV) --version)"
	@echo "Claude directory: ~/.claude"
	@echo "Claude directory exists: $$(test -d ~/.claude && echo 'Yes' || echo 'No')"
	@echo "Available agents: $$(find agents -name '*.md' | wc -l)"
	@echo "Available commands: $$(find commands -name '*.md' | wc -l)"
	@echo "Available hooks: $$(find hooks -name '*.py' | wc -l)"

info: ## Show repository information
	@echo "$(BLUE)Claude Code Arsenal Information$(RESET)"
	@echo "Agents:   $$(find agents -name '*.md' 2>/dev/null | wc -l) files"
	@echo "Commands: $$(find commands -name '*.md' 2>/dev/null | wc -l) files"
	@echo "Hooks:    $$(find hooks -name '*.py' 2>/dev/null | wc -l) files"
	@echo "Scripts:  $$(find scripts -maxdepth 2 -name '*.py' -not -path '*/__pycache__/*' -not -path '*/.*' -not -name 'test_*' -not -name '__init__.py' 2>/dev/null | wc -l) files"

quick-start: validate-structure setup-env dry-run ## Complete quick start setup
	@echo "$(GREEN)Quick start complete!$(RESET)"
	@echo "Next steps:"
	@echo "  1. Review the dry-run output above"
	@echo "  2. Run 'make install' to install"
	@echo "  3. Run 'make configure' to customize"

# Claude Hi Cron - Simple session trigger replacement
claude-hi-setup: ## Interactive setup for Claude 'hi' cron scheduler
	@echo "$(BLUE)Setting up Claude 'Hi' Cron Scheduler...$(RESET)"
	@chmod +x scripts/claude-hi/claude_hi_cron.sh
	@scripts/claude-hi/claude_hi_cron.sh setup

claude-hi-status: ## Show Claude 'hi' cron status
	@echo "$(BLUE)Claude 'Hi' Cron Status:$(RESET)"
	@chmod +x scripts/claude-hi/claude_hi_cron.sh
	@scripts/claude-hi/claude_hi_cron.sh status

claude-hi-remove: ## Remove Claude 'hi' cron schedule
	@echo "$(YELLOW)Removing Claude 'Hi' Cron Schedule...$(RESET)"
	@chmod +x scripts/claude-hi/claude_hi_cron.sh
	@scripts/claude-hi/claude_hi_cron.sh remove
	@echo "$(GREEN)Claude 'hi' schedule removed$(RESET)"

claude-hi-now: ## Send 'hi' to Claude right now
	@echo "$(BLUE)Sending 'hi' to Claude...$(RESET)"
	@chmod +x scripts/claude-hi/claude_hi_cron.sh
	@scripts/claude-hi/claude_hi_cron.sh now

claude-hi-standard: ## Quick setup work hours (9,14,19) - triggers 5h before resets
	@echo "$(BLUE)Setting up work hours schedule...$(RESET)"
	@chmod +x scripts/claude-hi/claude_hi_cron.sh
	@scripts/claude-hi/claude_hi_cron.sh setup "9,14,19"
	@echo "$(GREEN)Work schedule: 9am/2pm/7pm triggers → 2pm/7pm/12am resets$(RESET)"

claude-hi-extended: ## Quick setup extended day (4,9,14,19) - full coverage
	@echo "$(BLUE)Setting up extended day schedule...$(RESET)"
	@chmod +x scripts/claude-hi/claude_hi_cron.sh
	@scripts/claude-hi/claude_hi_cron.sh setup "4,9,14,19"
	@echo "$(GREEN)Extended schedule: 4am/9am/2pm/7pm triggers → 9am/2pm/7pm/12am resets$(RESET)"

claude-hi-custom: ## Custom schedule helper for different work patterns
	@echo "$(BLUE)Custom Schedule Helper...$(RESET)"
	@chmod +x scripts/claude-hi/claude_hi_cron.sh
	@scripts/claude-hi/claude_hi_cron.sh custom

# ============================================================================
# Claude Slash Command Automation
# ============================================================================

claude-slash-setup: ## Interactive setup for automated slash commands
	@echo "$(BLUE)Setting up automated slash command execution...$(RESET)"
	@chmod +x scripts/claude-hi/claude_slash_cron.sh
	@scripts/claude-hi/claude_slash_cron.sh setup

claude-slash-status: ## Show automated slash commands status
	@echo "$(BLUE)Checking slash command automation status...$(RESET)"
	@chmod +x scripts/claude-hi/claude_slash_cron.sh
	@scripts/claude-hi/claude_slash_cron.sh status

claude-slash-list: ## List all automated slash commands
	@echo "$(BLUE)Listing automated slash commands...$(RESET)"
	@chmod +x scripts/claude-hi/claude_slash_cron.sh
	@scripts/claude-hi/claude_slash_cron.sh list

claude-slash-remove: ## Remove specific slash command automation
	@echo "$(BLUE)Removing slash command automation...$(RESET)"
	@chmod +x scripts/claude-hi/claude_slash_cron.sh
	@echo "Available automations:"
	@scripts/claude-hi/claude_slash_cron.sh list
	@echo ""
	@scripts/claude-hi/claude_slash_cron.sh remove

# Default target
all: help
