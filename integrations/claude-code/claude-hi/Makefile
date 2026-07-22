.PHONY: help setup status remove now standard extended custom slash-setup slash-status slash-list slash-remove

# Colors for output
BLUE := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

CLAUDE_HI_DIR := $(shell pwd)

help: ## Show claude-hi session scheduler commands
	@echo "$(BLUE)Claude 'Hi' Session Scheduler Commands$(RESET)"
	@echo
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo
	@echo "$(YELLOW)Quick Start:$(RESET)"
	@echo "  make standard      # Set up 9am/2pm/7pm schedule"
	@echo "  make status        # Check current schedule"
	@echo "  make remove        # Remove schedule"
	@echo
	@echo "$(YELLOW)Background:$(RESET)"
	@echo "  Claude Code resets context every 5 hours. This scheduler"
	@echo "  automatically sends 'hi' to keep sessions warm."

# ============================================================================
# Claude Hi - Session Keep-Alive Scheduler
# ============================================================================

setup: ## Interactive setup for Claude 'hi' cron scheduler
	@echo "$(BLUE)Setting up Claude 'Hi' Cron Scheduler...$(RESET)"
	@chmod +x $(CLAUDE_HI_DIR)/claude_hi_cron.sh
	@$(CLAUDE_HI_DIR)/claude_hi_cron.sh setup

status: ## Show Claude 'hi' cron status
	@echo "$(BLUE)Claude 'Hi' Cron Status:$(RESET)"
	@chmod +x $(CLAUDE_HI_DIR)/claude_hi_cron.sh
	@$(CLAUDE_HI_DIR)/claude_hi_cron.sh status

remove: ## Remove Claude 'hi' cron schedule
	@echo "$(YELLOW)Removing Claude 'Hi' Cron Schedule...$(RESET)"
	@chmod +x $(CLAUDE_HI_DIR)/claude_hi_cron.sh
	@$(CLAUDE_HI_DIR)/claude_hi_cron.sh remove
	@echo "$(GREEN)Claude 'hi' schedule removed$(RESET)"

now: ## Send 'hi' to Claude right now
	@echo "$(BLUE)Sending 'hi' to Claude...$(RESET)"
	@chmod +x $(CLAUDE_HI_DIR)/claude_hi_cron.sh
	@$(CLAUDE_HI_DIR)/claude_hi_cron.sh now

standard: ## Quick setup work hours (9,14,19) - triggers 5h before resets
	@echo "$(BLUE)Setting up work hours schedule...$(RESET)"
	@chmod +x $(CLAUDE_HI_DIR)/claude_hi_cron.sh
	@$(CLAUDE_HI_DIR)/claude_hi_cron.sh setup "9,14,19"
	@echo "$(GREEN)Work schedule: 9am/2pm/7pm triggers → 2pm/7pm/12am resets$(RESET)"

extended: ## Quick setup extended day (4,9,14,19) - full coverage
	@echo "$(BLUE)Setting up extended day schedule...$(RESET)"
	@chmod +x $(CLAUDE_HI_DIR)/claude_hi_cron.sh
	@$(CLAUDE_HI_DIR)/claude_hi_cron.sh setup "4,9,14,19"
	@echo "$(GREEN)Extended schedule: 4am/9am/2pm/7pm triggers → 9am/2pm/7pm/12am resets$(RESET)"

custom: ## Custom schedule helper for different work patterns
	@echo "$(BLUE)Custom Schedule Helper...$(RESET)"
	@chmod +x $(CLAUDE_HI_DIR)/claude_hi_cron.sh
	@$(CLAUDE_HI_DIR)/claude_hi_cron.sh custom

# ============================================================================
# Claude Slash Command Automation
# ============================================================================

slash-setup: ## Interactive setup for automated slash commands
	@echo "$(BLUE)Setting up automated slash command execution...$(RESET)"
	@chmod +x $(CLAUDE_HI_DIR)/claude_slash_cron.sh
	@$(CLAUDE_HI_DIR)/claude_slash_cron.sh setup

slash-status: ## Show automated slash commands status
	@echo "$(BLUE)Checking slash command automation status...$(RESET)"
	@chmod +x $(CLAUDE_HI_DIR)/claude_slash_cron.sh
	@$(CLAUDE_HI_DIR)/claude_slash_cron.sh status

slash-list: ## List all automated slash commands
	@echo "$(BLUE)Listing automated slash commands...$(RESET)"
	@chmod +x $(CLAUDE_HI_DIR)/claude_slash_cron.sh
	@$(CLAUDE_HI_DIR)/claude_slash_cron.sh list

slash-remove: ## Remove specific slash command automation
	@echo "$(BLUE)Removing slash command automation...$(RESET)"
	@chmod +x $(CLAUDE_HI_DIR)/claude_slash_cron.sh
	@echo "Available automations:"
	@$(CLAUDE_HI_DIR)/claude_slash_cron.sh list
	@echo ""
	@$(CLAUDE_HI_DIR)/claude_slash_cron.sh remove

.DEFAULT_GOAL := help
