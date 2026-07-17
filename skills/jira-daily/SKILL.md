---
name: jira-daily
description: Generate a standup report from recent Jira activity and git history —
  completed tickets, in-progress work, blockers, and commit correlation. Use when
  the user wants to prepare for a daily standup, asks "what did I do yesterday",
  or wants a Jira/git activity summary in brief, slack, or manager format. Use
  jira-todo instead for forward-looking "what should I work on" planning.
metadata:
  author: mgiovani
  version: 1.0.0
disable-model-invocation: true
argument-hint: '[--project <KEY>] [--since <date>] [--format <format>]'
allowed-tools: Bash(jira *), Bash(git *), Bash(cat *), Bash(date *), Read, TodoWrite
context: fork
agent: general-purpose
---

# Jira Daily - Standup Meeting Preparation

Generates a structured standup update from real Jira and git activity. Complements
**jira-cli** (general Jira command reference) and **jira-todo** (forward-looking
planning — this skill looks backward at what was actually done).

## Anti-Hallucination Guidelines

Standup reports must reflect actual work done:
1. Only list tickets that came from jira CLI output
2. Only mark a ticket "Completed" if its status is Done/Closed/Released
3. Use real git log commit counts, never estimate
4. Only mention blockers explicitly labeled or discussed in Jira
5. Pull story points and progress from actual sprint data

## Workflow

### Phase 1: Determine Project Key

Priority order:
1. Command argument: `--project ABC` or `-p ABC`
2. Jira CLI config: read from `~/.config/.jira/.config.yml`

```bash
PROJECT_KEY=$(cat ~/.config/.jira/.config.yml 2>/dev/null | grep -A1 "^project:" | grep "key:" | awk '{print $2}')
echo "Detected project: $PROJECT_KEY"
```

If no project key is found, ask the user to specify `--project <KEY>`.

### Phase 2: Calculate Date Range

```bash
# Report since yesterday, or since Friday if today is Monday
if [[ $(date +%u) == 1 ]]; then
  SINCE_DATE=$(date -v-3d +%Y-%m-%d 2>/dev/null || date -d "3 days ago" +%Y-%m-%d)
else
  SINCE_DATE=$(date -v-1d +%Y-%m-%d 2>/dev/null || date -d "yesterday" +%Y-%m-%d)
fi
echo "Reporting since: $SINCE_DATE"
```

### Phase 3: Gather Activity Data

```bash
# Tickets updated recently
jira issue list --updated -1d --plain --columns key,summary,status,priority,type

# Tickets moved to done/completed
jira issue list --jql "status changed to (Done, Released, Closed) after -1d AND assignee was currentUser()" --plain

# Tickets currently in progress
jira issue list --assignee $(jira me) --status "In Progress" "Code Review" "In Review" --plain

# Blockers
jira issue list --assignee $(jira me) --jql "labels = 'blocked' OR description ~ 'blocked'" --plain

# Git activity
git log --author="$(git config user.email)" --since="$SINCE_DATE" --oneline --all --no-merges
git rev-list --count --since="$SINCE_DATE" --author="$(git config user.email)" --all 2>/dev/null || echo "0"
```

### Phase 4: Classify and Correlate

Do this inline — a standup's ticket count is small enough that spinning up
subagents just adds latency for no benefit:
1. Bucket each ticket into Completed / In Progress / Blocked / Started, based only
   on its actual status field.
2. Match git commit messages to ticket IDs to show which tickets have code changes.
3. For completed tickets, note business/technical impact from the ticket
   description — keep it factual, not speculative.

### Phase 5: Generate Report

Track sections completed with TodoWrite, then render using the requested format.

## Output Formats

For detailed templates (default, brief, slack, manager), see
[references/output-formats.md](references/output-formats.md).

- **Default (Detailed)**: completed work, in-progress items, blockers, sprint progress, technical highlights, metrics, schedule
- **Brief** (`--format brief`): one line per section, for quick standups
- **Slack** (`--format slack`): markdown formatted for Slack/Teams posting
- **Manager** (`--format manager`): executive summary of delivery highlights and risks

## Command Options

- `--project <KEY>` / `-p <KEY>` — Jira project key
- `--since <date>` — override the automatic date calculation, e.g. `jira-daily --since 2025-01-20`
- `--format <format>` — `brief` | `detailed` (default) | `slack` | `manager`
- `--include-planned` — include tickets planned for today, not just completed/in-progress

## Usage Examples

```bash
jira-daily                                          # auto-detect project, yesterday's activity
jira-daily --project ABC
jira-daily --format brief                            # quick standup
jira-daily --format slack                            # for Slack posting
jira-daily --format manager                          # for a manager 1:1
jira-daily --since 2025-01-15
jira-daily --since $(date -v-7d +%Y-%m-%d) --format manager   # weekly summary
```

## Integration Points

- **jira-todo**: compare yesterday's planned work against actual completion
- **jira-cli**: use for detailed command syntax and sprint/epic workflows

## Requirements

- `jira-cli` installed: https://github.com/ankitpokhrel/jira-cli
- Config at `~/.config/.jira/.config.yml`
- A local git repository for commit correlation
