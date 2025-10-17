# Jira CLI - Scripting and Automation

This file contains examples for automating Jira operations with scripts and integrating with CI/CD pipelines.

## Bash Scripting Examples

### Tickets Created Per Day This Month

```bash
#!/usr/bin/env bash
# Generate report of tickets created per day in current month

tickets=$(jira issue list --created month --plain --columns created --no-headers | \
  awk '{print $2}' | awk -F'-' '{print $3}' | sort -n | uniq -c)

echo "${tickets}" | while IFS=$'\t' read -r line; do
  day=$(echo "${line}" | awk '{print $2}')
  count=$(echo "${line}" | awk '{print $1}')
  printf "Day #%s: %s tickets\n" "${day}" "${count}"
done
```

### Number of Tickets Per Sprint

```bash
#!/usr/bin/env bash
# Count tickets in each sprint

sprints=$(jira sprint list --table --plain --columns id,name --no-headers)

echo "${sprints}" | while IFS=$'\t' read -r id name; do
  count=$(jira sprint list "${id}" --plain --no-headers 2>/dev/null | wc -l)
  printf "%10s: %3d tickets\n" "${name}" $((count))
done
```

### Number of Unique Assignees Per Sprint

```bash
#!/usr/bin/env bash
# Count unique assignees in each sprint

sprints=$(jira sprint list --table --plain --columns id,name --no-headers)

echo "${sprints}" | while IFS=$'\t' read -r id name; do
  count=$(jira sprint list "${id}" --plain --columns assignee --no-headers 2>/dev/null | \
    awk '{print $2}' | awk NF | sort -n | uniq | wc -l)
  printf "%10s: %3d people\n" "${name}" $((count))
done
```

### Daily Standup Report

```bash
#!/usr/bin/env bash
# Generate daily standup report

echo "=== Daily Standup Report ==="
echo ""

echo "Yesterday's work (updated in last 24h):"
jira issue list -a$(jira me) --updated -1d --plain --columns key,summary

echo ""
echo "Currently working on:"
jira issue list -a$(jira me) -s"In Progress" --plain --columns key,summary

echo ""
echo "Closed this week:"
jira issue list -a$(jira me) -sDone --updated week --plain --columns key,summary
```

### Sprint Report Generator

```bash
#!/usr/bin/env bash
# Generate sprint summary report

SPRINT_ID=$1

if [ -z "$SPRINT_ID" ]; then
  echo "Usage: $0 <sprint-id>"
  exit 1
fi

echo "=== Sprint Report for Sprint $SPRINT_ID ==="
echo ""

total=$(jira sprint list "$SPRINT_ID" --plain --no-headers | wc -l)
done_count=$(jira sprint list "$SPRINT_ID" -sDone --plain --no-headers | wc -l)
in_progress=$(jira sprint list "$SPRINT_ID" -s"In Progress" --plain --no-headers | wc -l)
todo=$(jira sprint list "$SPRINT_ID" -s"To Do" --plain --no-headers | wc -l)

echo "Total tickets: $total"
echo "Done: $done_count"
echo "In Progress: $in_progress"
echo "To Do: $todo"
echo ""

completion_rate=$(echo "scale=2; ($done_count / $total) * 100" | bc)
echo "Completion rate: ${completion_rate}%"
```

### Bulk Issue Assignment

```bash
#!/usr/bin/env bash
# Assign unassigned high priority tickets to team members

# Get list of unassigned high priority tickets
issues=$(jira issue list -ax -yHigh -s"To Do" --plain --columns key --no-headers)

# Team members
team=("Alice" "Bob" "Charlie")
team_size=${#team[@]}
index=0

# Assign in round-robin fashion
for issue in $issues; do
  assignee="${team[$index]}"
  echo "Assigning $issue to $assignee"
  jira issue assign "$issue" "$assignee"
  index=$(( (index + 1) % team_size ))
done
```

### Auto-Label Based on Summary

```bash
#!/usr/bin/env bash
# Auto-label issues based on keywords in summary

# Get issues without labels
issues=$(jira issue list --plain --columns key,summary --no-headers)

echo "$issues" | while IFS=$'\t' read -r key summary; do
  # Check for keywords and add labels
  if echo "$summary" | grep -qi "bug\|error\|crash"; then
    echo "Adding 'bug' label to $key"
    jira issue edit "$key" --label bug
  fi

  if echo "$summary" | grep -qi "feature\|enhancement"; then
    echo "Adding 'enhancement' label to $key"
    jira issue edit "$key" --label enhancement
  fi

  if echo "$summary" | grep -qi "urgent\|critical\|blocker"; then
    echo "Adding 'urgent' label to $key"
    jira issue edit "$key" --label urgent
  fi
done
```

### Export Issues to CSV

```bash
#!/usr/bin/env bash
# Export filtered issues to CSV file

OUTPUT_FILE="issues_$(date +%Y%m%d).csv"

# Export with custom columns
jira issue list \
  --created month \
  --csv \
  --columns key,type,status,priority,assignee,summary,created \
  > "$OUTPUT_FILE"

echo "Exported to $OUTPUT_FILE"
```

### Monitor High Priority Issues

```bash
#!/usr/bin/env bash
# Monitor and alert on high priority unassigned issues

THRESHOLD=5

count=$(jira issue list -ax -yHigh -s~Done --plain --no-headers | wc -l)

if [ "$count" -gt "$THRESHOLD" ]; then
  echo "⚠️  Alert: $count high priority unassigned issues (threshold: $THRESHOLD)"
  jira issue list -ax -yHigh -s~Done --plain --columns key,summary

  # Could send to Slack, email, etc.
  # slack-cli send "#team-alerts" "High priority issues need attention: $count tickets"
else
  echo "✅ OK: $count high priority unassigned issues"
fi
```

## CI/CD Integration

### GitHub Actions - Create Jira Issue on PR

```yaml
name: Create Jira Issue
on:
  pull_request:
    types: [opened]

jobs:
  create-jira:
    runs-on: ubuntu-latest
    steps:
      - name: Install jira-cli
        run: |
          wget https://github.com/ankitpokhrel/jira-cli/releases/latest/download/jira_linux_amd64.tar.gz
          tar -xf jira_linux_amd64.tar.gz
          sudo mv jira /usr/local/bin/

      - name: Create Jira Issue
        env:
          JIRA_API_TOKEN: ${{ secrets.JIRA_API_TOKEN }}
          JIRA_SERVER: ${{ secrets.JIRA_SERVER }}
          JIRA_PROJECT: ${{ secrets.JIRA_PROJECT }}
        run: |
          jira issue create \
            -tTask \
            -s"Review PR #${{ github.event.pull_request.number }}: ${{ github.event.pull_request.title }}" \
            -b"${{ github.event.pull_request.html_url }}" \
            --no-input
```

### GitLab CI - Update Jira on Deploy

```yaml
update_jira:
  stage: deploy
  script:
    - |
      # Extract Jira keys from commit messages
      JIRA_KEYS=$(git log --format=%B -n 10 | grep -oE '[A-Z]+-[0-9]+' | sort -u)

      for KEY in $JIRA_KEYS; do
        echo "Updating $KEY to Done"
        jira issue move "$KEY" Done -RDeployed --comment "Deployed to production"
      done
  only:
    - main
```

### Jenkins Pipeline - Sprint Metrics

```groovy
pipeline {
    agent any
    triggers {
        cron('0 9 * * 1')  // Every Monday at 9 AM
    }
    stages {
        stage('Generate Sprint Report') {
            steps {
                script {
                    sh '''
                        # Get current sprint
                        SPRINT_ID=$(jira sprint list --current --table --plain --columns id --no-headers)

                        # Generate metrics
                        echo "Sprint Metrics Report" > sprint_report.txt
                        echo "===================" >> sprint_report.txt

                        total=$(jira sprint list $SPRINT_ID --plain --no-headers | wc -l)
                        done=$(jira sprint list $SPRINT_ID -sDone --plain --no-headers | wc -l)

                        echo "Total: $total" >> sprint_report.txt
                        echo "Done: $done" >> sprint_report.txt

                        # Send to team
                        cat sprint_report.txt
                    '''
                }
            }
        }
    }
}
```

## Data Analysis

### Export Data for Analysis

```bash
#!/usr/bin/env bash
# Export comprehensive data for analysis

# Create timestamped directory
DIR="jira_export_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$DIR"

# Export different views
echo "Exporting all open issues..."
jira issue list -s~Done --csv > "$DIR/open_issues.csv"

echo "Exporting completed this month..."
jira issue list -sDone --updated month --csv > "$DIR/completed_month.csv"

echo "Exporting by assignee..."
for user in $(jira issue list --plain --columns assignee --no-headers | sort -u); do
  jira issue list -a"$user" --csv > "$DIR/assignee_${user// /_}.csv"
done

echo "Export complete in $DIR/"
```

### Calculate Team Velocity

```bash
#!/usr/bin/env bash
# Calculate team velocity over last N sprints

SPRINT_COUNT=5

echo "=== Team Velocity (last $SPRINT_COUNT sprints) ==="
echo ""

sprints=$(jira sprint list --state closed --table --plain --columns id,name --no-headers | head -$SPRINT_COUNT)

total_points=0
sprint_count=0

echo "$sprints" | while IFS=$'\t' read -r id name; do
  # Assuming story points in summary or custom field
  completed=$(jira sprint list "$id" -sDone --plain --no-headers | wc -l)
  echo "$name: $completed stories"

  total_points=$((total_points + completed))
  sprint_count=$((sprint_count + 1))
done

# Calculate average
if [ $sprint_count -gt 0 ]; then
  avg=$(echo "scale=2; $total_points / $sprint_count" | bc)
  echo ""
  echo "Average velocity: $avg stories per sprint"
fi
```

## Automation Helpers

### Auto-Transition Based on PR Status

```bash
#!/usr/bin/env bash
# Auto-transition Jira issues based on PR status

# Get list of open PRs from GitHub
# (requires gh CLI)
prs=$(gh pr list --json number,title --jq '.[] | "\(.number)|\(.title)"')

echo "$prs" | while IFS='|' read -r number title; do
  # Extract Jira key from PR title
  jira_key=$(echo "$title" | grep -oE '[A-Z]+-[0-9]+' | head -1)

  if [ -n "$jira_key" ]; then
    # Check current status
    status=$(jira issue view "$jira_key" --plain | grep "Status:" | awk '{print $2}')

    # Move to In Review if not already
    if [ "$status" != "Review" ]; then
      echo "Moving $jira_key to In Review (PR #$number)"
      jira issue move "$jira_key" "In Review"
      jira issue link remote "$jira_key" "https://github.com/org/repo/pull/$number" "PR #$number"
    fi
  fi
done
```

### Stale Issue Cleanup

```bash
#!/usr/bin/env bash
# Find and handle stale issues

# Find issues not updated in 3 months
stale=$(jira issue list --updated-before -12w -s"To Do" --plain --columns key,summary --no-headers)

echo "$stale" | while IFS=$'\t' read -r key summary; do
  echo "Stale issue found: $key - $summary"

  # Add comment asking for update
  jira issue comment add "$key" "This issue hasn't been updated in 3 months. Is it still relevant?"

  # Add stale label
  jira issue edit "$key" --label stale

  # Optionally: move to backlog or close
  # jira issue move "$key" "Backlog"
done
```

## Best Practices for Scripts

### Error Handling

```bash
#!/usr/bin/env bash
set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Check if jira-cli is available
if ! command -v jira &> /dev/null; then
  echo "Error: jira-cli not found. Please install it first."
  exit 1
fi

# Check for required environment variables
if [ -z "${JIRA_API_TOKEN:-}" ]; then
  echo "Error: JIRA_API_TOKEN not set"
  exit 1
fi

# Wrap jira commands with error handling
if ! jira issue list -a$(jira me) 2>&1; then
  echo "Error: Failed to fetch issues"
  exit 1
fi
```

### Logging and Debugging

```bash
#!/usr/bin/env bash

# Enable debug mode
DEBUG=${DEBUG:-false}

debug() {
  if [ "$DEBUG" = "true" ]; then
    echo "[DEBUG] $*" >&2
  fi
}

debug "Starting script..."
debug "Fetching issues for user: $(jira me)"

issues=$(jira issue list -a$(jira me) --plain --columns key --no-headers)
debug "Found $(echo "$issues" | wc -l) issues"
```

### Rate Limiting

```bash
#!/usr/bin/env bash

# Process issues with rate limiting
issues=$(jira issue list --plain --columns key --no-headers)

for issue in $issues; do
  echo "Processing $issue"
  jira issue view "$issue" > /dev/null

  # Rate limit: 1 request per second
  sleep 1
done
```
