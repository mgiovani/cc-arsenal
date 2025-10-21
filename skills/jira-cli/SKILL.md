---
name: jira-cli
description: Interactive command-line tool for Atlassian Jira. This skill should be used when users want to interact with Jira issues, epics, sprints, or when they mention Jira workflows, issue management, or need help with jira-cli commands and workflows.
---

# Jira CLI

Interactive command-line tool for Atlassian Jira that minimizes reliance on the web interface while maintaining essential functionality for daily Jira operations.

## Overview

JiraCLI (`jira-cli`) is a command line tool for managing Jira issues, epics, and sprints. Supports both Jira Cloud and on-premise installations with multiple authentication methods.

**For AI use, always add `--plain` flag to get plain text output suitable for parsing.**

## When to Use This Skill

Use this skill when:
- Managing Jira issues from the command line
- Creating, editing, or viewing Jira tickets
- Working with epics and sprints
- Automating Jira workflows
- Users mention "jira", "ticket", "issue", "epic", or "sprint"
- Writing scripts for Jira automation

## Essential Commands

```bash
# List recent issues (always use --plain for AI)
jira issue list --plain

# View issue details
jira issue view ISSUE-1 --plain

# Create an issue
jira issue create -tBug -s"Bug title" -yHigh -b"Description"

# Assign issue to yourself
jira issue assign ISSUE-1 $(jira me)

# Move issue to "In Progress"
jira issue move ISSUE-1 "In Progress"

# Add comment
jira issue comment add ISSUE-1 --comment "My comment"

# Add worklog
jira issue worklog add ISSUE-1 "2h" --comment "Implementation work"
```

## How to Use This Skill

**For detailed command reference and examples, load the appropriate reference file:**

### 1. Comprehensive Commands Reference

**Load:** [references/commands.md](./references/commands.md)

Use this file when you need:
- Detailed command syntax and options
- All available flags and parameters
- Issue management operations (list, create, edit, assign, move, view, link, clone, delete)
- Epic management (list, create, add/remove issues)
- Sprint management (list, add issues)
- Release management
- Output format options
- Non-interactive command patterns

### 2. Common Workflow Examples

**Load:** [references/workflows.md](./references/workflows.md)

Use this file when you need:
- Daily standup preparation workflows
- Sprint planning commands
- Code review workflow integration
- Bug triage procedures
- Team collaboration patterns
- Best practices for different scenarios

### 3. Scripting and Automation

**Load:** [references/scripting.md](./references/scripting.md)

Use this file when you need:
- Bash automation scripts
- Data extraction and reporting
- Integration with CI/CD pipelines
- Metrics and analytics examples
- Bulk operations

## Quick Reference

### Powerful List Filters

```bash
# Combine flags for precise queries (always add --plain)
jira issue list --plain -a$(jira me) -yHigh -s"To Do" --created -7d -lbackend

# Use tilde (~) as NOT operator
jira issue list --plain -s~Done --created-before -24w

# Filter by multiple criteria
jira issue list --plain -yHigh,Critical -s"In Progress" -lbug
```

## Resources

- **GitHub**: https://github.com/ankitpokhrel/jira-cli
- **Installation Guide**: https://github.com/ankitpokhrel/jira-cli/wiki/Installation
- **FAQs**: https://github.com/ankitpokhrel/jira-cli/discussions/categories/faqs
