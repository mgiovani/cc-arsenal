# Makefile for git diff pane hook
# Development and testing commands only
# Installation is handled via Claude Code plugin system

.DEFAULT_GOAL := help
.PHONY: help test status check-delta clean

# Colors
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m

# Paths
SCRIPT_DIR := $(shell pwd)
PANE_ID_FILE := /tmp/claude-diff-pane-id

help: ## Show this help message
	@echo "$(BLUE)Git Diff Pane Hook - Development Commands$(NC)"
	@echo ""
	@echo "$(YELLOW)Installation:$(NC)"
	@echo "  This hook is installed via Claude Code plugin system:"
	@echo "  /plugin install cc-arsenal@cc-arsenal-marketplace"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(BLUE)Configuration Environment Variables:$(NC)"
	@echo "  CLAUDE_DIFF_PANE_WIDTH       - Pane width percentage (default: 40)"
	@echo "  CLAUDE_DIFF_PANE_POSITION    - Pane position: left or right (default: right)"
	@echo "  CLAUDE_DIFF_STAGED_ONLY      - Show only staged changes (default: false)"
	@echo "  CLAUDE_DIFF_TOOL             - Diff tool: delta, diff-so-fancy, or git (default: auto)"

test: ## Test the hook manually (requires tmux and git repo)
	@echo "$(BLUE)🧪 Testing git diff pane hook...$(NC)"
	@if [ -z "$$TMUX" ]; then \
		echo "$(RED)❌ Error: Not in a tmux session$(NC)"; \
		echo "$(YELLOW)Please run this command inside tmux$(NC)"; \
		exit 1; \
	fi
	@if ! git rev-parse --git-dir > /dev/null 2>&1; then \
		echo "$(RED)❌ Error: Not in a git repository$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✓ Inside tmux session$(NC)"
	@echo "$(GREEN)✓ Inside git repository$(NC)"
	@echo "$(BLUE)Running hook script...$(NC)"
	@bash $(SCRIPT_DIR)/scripts/diff-pane.sh
	@echo "$(GREEN)✅ Hook executed successfully!$(NC)"
	@echo "$(YELLOW)Check your tmux panes for the diff output$(NC)"

status: ## Show current hook configuration and status
	@echo "$(BLUE)📊 Git Diff Pane Hook Status$(NC)"
	@echo ""
	@echo "$(BLUE)Installation:$(NC)"
	@echo "  This hook is installed via Claude Code plugin system"
	@echo "  Check: /plugin list (should show cc-arsenal)"
	@echo ""
	@echo "$(BLUE)Environment:$(NC)"
	@if [ -n "$$TMUX" ]; then \
		echo "  $(GREEN)✓ Inside tmux session$(NC)"; \
	else \
		echo "  $(YELLOW)⚠ Not in tmux (hook won't trigger)$(NC)"; \
	fi
	@if git rev-parse --git-dir > /dev/null 2>&1; then \
		echo "  $(GREEN)✓ Inside git repository$(NC)"; \
	else \
		echo "  $(YELLOW)⚠ Not in git repo (hook won't trigger)$(NC)"; \
	fi
	@echo ""
	@echo "$(BLUE)Diff Tools:$(NC)"
	@if command -v delta > /dev/null 2>&1; then \
		echo "  $(GREEN)✓ delta installed$(NC)"; \
	else \
		echo "  $(YELLOW)⚠ delta not found (will use git diff)$(NC)"; \
	fi
	@if command -v diff-so-fancy > /dev/null 2>&1; then \
		echo "  $(GREEN)✓ diff-so-fancy installed$(NC)"; \
	else \
		echo "  $(YELLOW)⚠ diff-so-fancy not found$(NC)"; \
	fi
	@echo ""
	@echo "$(BLUE)Current Pane:$(NC)"
	@if [ -f "$(PANE_ID_FILE)" ]; then \
		PANE_ID=$$(cat $(PANE_ID_FILE)); \
		echo "  Pane ID: $$PANE_ID"; \
		if [ -n "$$TMUX" ] && tmux list-panes -F '#{pane_id}' 2>/dev/null | grep -q "^$$PANE_ID$$"; then \
			echo "  $(GREEN)✓ Pane is active$(NC)"; \
		else \
			echo "  $(YELLOW)⚠ Pane not found (will be recreated)$(NC)"; \
		fi \
	else \
		echo "  $(YELLOW)⚠ No active pane$(NC)"; \
	fi
	@echo ""
	@echo "$(BLUE)Configuration:$(NC)"
	@echo "  CLAUDE_DIFF_PANE_WIDTH:    $${CLAUDE_DIFF_PANE_WIDTH:-40 (default)}"
	@echo "  CLAUDE_DIFF_PANE_POSITION: $${CLAUDE_DIFF_PANE_POSITION:-right (default)}"
	@echo "  CLAUDE_DIFF_STAGED_ONLY:   $${CLAUDE_DIFF_STAGED_ONLY:-false (default)}"
	@echo "  CLAUDE_DIFF_TOOL:          $${CLAUDE_DIFF_TOOL:-auto (default)}"

check-delta: ## Check if delta is installed and suggest installation
	@echo "$(BLUE)🔍 Checking for delta...$(NC)"
	@if command -v delta > /dev/null 2>&1; then \
		echo "$(GREEN)✓ delta is installed$(NC)"; \
		delta --version; \
	else \
		echo "$(YELLOW)⚠ delta not found$(NC)"; \
		echo ""; \
		echo "$(BLUE)Installation options:$(NC)"; \
		echo "  cargo install git-delta"; \
		echo "  brew install git-delta"; \
		echo "  apt install git-delta"; \
		echo "  pacman -S git-delta"; \
		echo ""; \
		echo "$(BLUE)More info:$(NC) https://github.com/dandavison/delta"; \
	fi

clean: ## Clean up temporary files
	@echo "$(BLUE)🧹 Cleaning up...$(NC)"
	@if [ -f "$(PANE_ID_FILE)" ]; then \
		echo "  Removing pane ID file..."; \
		rm -f "$(PANE_ID_FILE)"; \
	fi
	@echo "$(GREEN)✅ Cleanup complete$(NC)"
