---
name: jira-cli
description: Run raw ankitpokhrel/jira-cli commands directly against Jira Cloud or on-prem, issue/epic/sprint CRUD, JQL-style filtering, and scripting/CI automation (bulk assign, auto-label, sprint add). Invoke explicitly via /jira-cli, or when the user wants literal `jira` CLI syntax, a filter the curated skills don't expose, or a bash/CI script that drives jira-cli. Manual-invocation skill, does not auto-fire on general mentions of "jira" or "ticket". Not for a ready-made standup summary correlated with git commits (use jira-daily). Not for a prioritized "what should I work on" plan (use jira-todo).
disable-model-invocation: true
---

# Jira CLI

Command reference and scripting patterns for `jira-cli`, the command-line tool for managing Jira issues, epics, and sprints without the web UI.

## Prerequisites

These references assume `jira` on `PATH` is [ankitpokhrel/jira-cli](https://github.com/ankitpokhrel/jira-cli): a different tool can claim the same binary name. Before trusting any command below, run `jira version` once per session and confirm the output looks like this project (e.g. `jira version 1.x.x` with a `Homepage: https://github.com/ankitpokhrel/jira-cli` line). If it doesn't, stop and check `which jira` instead of guessing at flags.

For AI use, always add `--plain` (and usually `--no-headers`) to get parseable text output instead of the interactive table.

## When to Use This Skill

Manual slash-command skill (`/jira-cli`): it does not auto-trigger on mentions of "jira" or "ticket". Invoke it directly for raw `jira` CLI commands (issues, epics, sprints) or scripting/automation. On tools that don't read Claude-Code frontmatter, `disable-model-invocation` is ignored: the `/jira-cli` phrasing itself is the manual-invocation signal there too.

## Essential Commands

Curated top-7 for the most common operations. For anything else (filters, epic/sprint management, releases, output formats), load [references/commands.md](./references/commands.md); don't try to recall the rest from memory.

```bash
# List recent issues (always use --plain for AI)
jira issue list --plain

# View issue details
jira issue view ISSUE-1 --plain

# Create an issue
jira issue create -tBug -s"Bug title" -yHigh -b"Description" --no-input

# Assign issue to yourself
jira issue assign ISSUE-1 $(jira me)

# Move issue to "In Progress"
jira issue move ISSUE-1 "In Progress"

# Add comment
jira issue comment add ISSUE-1 --comment "My comment"

# Add worklog
jira issue worklog add ISSUE-1 "2h" --comment "Implementation work"
```

## Worked Examples

**Confirm the CLI flavor before anything else:**
```
$ jira version
jira version 1.5.1
Homepage: https://github.com/ankitpokhrel/jira-cli
```
A different `jira version` output (or a "command not found") means stop and resolve `which jira` before running any command from this skill.

**Parse `--plain` output for scripting**: columns are tab-separated, headers are on unless suppressed:
```
$ jira issue list -a$(jira me) -s"In Progress" --plain --no-headers --columns key,summary
PROJ-123	Fix login redirect loop
PROJ-124	Add rate limiting to API
```
```bash
jira issue list -a$(jira me) -s"In Progress" --plain --no-headers --columns key,summary | \
  while IFS=$'\t' read -r key summary; do echo "Working: $key - $summary"; done
```

**Create non-interactively and capture the new key from the URL jira-cli prints:**
```
$ jira issue create -tBug -s"Login redirect loop" -yHigh --no-input
Issue created
https://your-domain.atlassian.net/browse/PROJ-125
```
```bash
key=$(jira issue create -tBug -s"Login redirect loop" -yHigh --no-input | grep -oE '[A-Z]+-[0-9]+$')
```

**Bulk sprint add sourced from a live filter, not a hardcoded list:**
```bash
jira sprint add SPRINT_ID $(jira issue list -s"Ready for Dev" --plain --columns key --no-headers | tr '\n' ' ')
```

## How to Use This Skill

Load reference files on demand, don't pull all three into context for a single command.

### 1. Comprehensive Commands Reference

**Load:** [references/commands.md](./references/commands.md)

Detailed syntax for issue management (list, create, edit, assign, move, view, link, clone, delete, comments, worklog), epic management, sprint management, releases, and output-format options.

### 2. Common Workflow Examples

**Load:** [references/workflows.md](./references/workflows.md)

Multi-command patterns: sprint planning, code review handoff, bug triage, epic tracking, incident response, backlog grooming, cross-team coordination.

### 3. Scripting and Automation

**Load:** [references/scripting.md](./references/scripting.md)

Raw bash automation that isn't already a curated skill: bulk assignment, auto-labeling, CSV export, velocity/metrics calculation, CI/CD hooks (GitHub Actions, GitLab CI, Jenkins), error handling and rate-limiting patterns. For a formatted standup report or sprint status readout, use `jira-daily` instead of hand-rolling one here: those scripts were removed from this file for that reason.

## Resources

- **GitHub**: https://github.com/ankitpokhrel/jira-cli
- **Installation Guide**: https://github.com/ankitpokhrel/jira-cli/wiki/Installation
- **FAQs**: https://github.com/ankitpokhrel/jira-cli/discussions/categories/faqs
