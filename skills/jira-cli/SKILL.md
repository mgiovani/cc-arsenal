---
name: jira-cli
description: Interactive command-line tool for Atlassian Jira. This skill should be used when users want to interact with Jira issues, epics, sprints, or when they mention Jira workflows, issue management, or need help with jira-cli commands and workflows.
---

# Jira CLI

Interactive command-line tool for Atlassian Jira that minimizes reliance on the web interface while maintaining essential functionality for daily Jira operations.

## Overview

JiraCLI (`jira-cli`) is a feature-rich interactive command line tool for managing Jira issues, epics, and sprints. Supports both Jira Cloud and on-premise installations with multiple authentication methods.

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
# List recent issues
jira issue list

# View issue details
jira issue view ISSUE-1

# Create an issue interactively
jira issue create

# Assign issue to yourself
jira issue assign ISSUE-1 $(jira me)

# Move issue to "In Progress"
jira issue move ISSUE-1 "In Progress"

# Add comment
jira issue comment add ISSUE-1 "My comment"
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
- Navigation and keyboard shortcuts
- Output format options

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
# Combine flags for precise queries
jira issue list -a$(jira me) -yHigh -s"To Do" --created -7d -lbackend

# Use tilde (~) as NOT operator
jira issue list -s~Done --created-before -24w

# Output formats
jira issue list --plain              # For scripts
jira issue list --csv                # Spreadsheet-friendly
jira issue list --columns key,status # Custom columns
```

### Interactive UI Navigation

- **Arrow keys** or `j,k,h,l` - Navigate
- **v** - View issue details
- **m** - Transition issue
- **ENTER** - Open in browser
- **c** - Copy URL, **CTRL+k** - Copy key
- **?** - Show help

## Resources

- **GitHub**: https://github.com/ankitpokhrel/jira-cli
- **Installation Guide**: https://github.com/ankitpokhrel/jira-cli/wiki/Installation
- **FAQs**: https://github.com/ankitpokhrel/jira-cli/discussions/categories/faqs
