.PHONY: help install uninstall configure status test test-units list-backups force-install

# Colors for output
BLUE := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

STATUSLINE_DIR := $(shell pwd)

help: ## Show statusline commands
	@echo "$(BLUE)Statusline Management Commands$(RESET)"
	@echo
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo
	@echo "$(YELLOW)Quick Start:$(RESET)"
	@echo "  make install       # Install statusline with interactive prompts"
	@echo "  make status        # Show current configuration"
	@echo "  make uninstall     # Remove statusline"

install: ## Install statusline to ~/.claude (with prompts)
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
	@ln -sf "$(STATUSLINE_DIR)" ~/.claude/scripts/claude/statusline
	@echo "$(GREEN)🔧 Configuring Claude Code settings...$(RESET)"
	@$(STATUSLINE_DIR)/lib/claude_config.sh install force
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

force-install: ## Force install without prompts (creates automatic backup)
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
	@ln -sf "$(STATUSLINE_DIR)" ~/.claude/scripts/claude/statusline
	@echo "$(GREEN)🔧 Configuring Claude Code settings...$(RESET)"
	@$(STATUSLINE_DIR)/lib/claude_config.sh install force
	@echo "$(GREEN)✅ Statusline force-installed and configured!$(RESET)"
	@echo "$(BLUE)🎉 Automatically configured - just restart Claude Code!$(RESET)"

uninstall: ## Remove statusline from ~/.claude
	@echo "$(BLUE)Uninstalling statusline...$(RESET)"
	@if [ -L ~/.claude/scripts/claude/statusline ] || [ -d ~/.claude/scripts/claude/statusline ]; then \
		echo "$(YELLOW)Found existing statusline installation$(RESET)"; \
		read -p "Are you sure you want to uninstall? (y/N): " confirm; \
		if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
			echo "$(BLUE)Removing Claude Code settings...$(RESET)"; \
			$(STATUSLINE_DIR)/lib/claude_config.sh uninstall; \
			echo "$(BLUE)Removing statusline files...$(RESET)"; \
			rm -rf ~/.claude/scripts/claude/statusline; \
			echo "$(GREEN)Statusline completely uninstalled$(RESET)"; \
		else \
			echo "$(YELLOW)Uninstall cancelled$(RESET)"; \
		fi; \
	else \
		echo "$(YELLOW)Statusline not found$(RESET)"; \
	fi

configure: ## Configure statusline interactively
	@echo "$(BLUE)Configuring Claude Code Statusline...$(RESET)"
	@if [ ! -f $(STATUSLINE_DIR)/configure_statusline.py ]; then \
		echo "$(RED)Configuration script not found$(RESET)"; \
		exit 1; \
	fi
	@python3 $(STATUSLINE_DIR)/configure_statusline.py

status: ## Show current statusline configuration status
	@echo "$(BLUE)Claude Code Statusline Status$(RESET)"
	@$(STATUSLINE_DIR)/lib/claude_config.sh show

list-backups: ## List available statusline backups
	@echo "$(BLUE)Available statusline backups:$(RESET)"
	@if [ -d ~/.claude/backups/statusline ] && ls ~/.claude/backups/statusline/backup-* 2>/dev/null | head -10; then \
		echo; \
		echo "$(YELLOW)To restore a backup:$(RESET)"; \
		echo "  1. Run 'make uninstall'"; \
		echo "  2. Copy backup: cp -r ~/.claude/backups/statusline/backup-TIMESTAMP ~/.claude/scripts/claude/statusline"; \
		echo "  3. Or run 'make install' to install fresh version"; \
	else \
		echo "$(YELLOW)No statusline backups found$(RESET)"; \
	fi

test: ## Test statusline with official Claude Code JSON structure
	@echo "$(BLUE)Testing statusline...$(RESET)"
	@echo "{\"hook_event_name\":\"Status\",\"session_id\":\"test123\",\"transcript_path\":\"/path/to/transcript.json\",\"cwd\":\"$$(pwd)\",\"model\":{\"id\":\"claude-opus-4-1\",\"display_name\":\"Opus\"},\"workspace\":{\"current_dir\":\"$$(pwd)\",\"project_dir\":\"$$(pwd)\"},\"version\":\"1.0.80\",\"output_style\":{\"name\":\"default\"},\"cost\":{\"total_cost_usd\":0.01234,\"total_duration_ms\":45000,\"total_api_duration_ms\":2300,\"total_lines_added\":156,\"total_lines_removed\":23},\"context_window\":{\"total_input_tokens\":15234,\"total_output_tokens\":4521,\"context_window_size\":200000}}" | $(STATUSLINE_DIR)/statusline.sh

test-units: ## Run comprehensive unit tests for statusline modules
	@echo "$(BLUE)Running statusline unit tests...$(RESET)"
	@$(STATUSLINE_DIR)/tests/run_tests.sh

.DEFAULT_GOAL := help
