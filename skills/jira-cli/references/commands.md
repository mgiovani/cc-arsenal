# Jira CLI - Comprehensive Command Reference

This file contains detailed command syntax, options, and examples for all jira-cli operations.

## Issue Management

### Listing Issues

Use powerful filters to find exactly what you need:

```bash
# Basic listing
jira issue list                          # Recent issues
jira issue list "Feature Request"        # Search by specific text
jira issue list --created -7d            # Last 7 days
jira issue list -s"To Do"                # Specific status
jira issue list -yHigh                   # High priority

# Personal queries
jira issue list -a$(jira me)             # Assigned to me
jira issue list -r$(jira me)             # Reported by me
jira issue list -w                       # Issues I'm watching

# Filtering by fields
jira issue list -lbackend                # With label
jira issue list -CBackend                # With component
jira issue list -tBug                    # Bug type
jira issue list -R"Won't do"             # With resolution

# Combined filters (high priority, In Progress, created this month, with labels)
jira issue list -yHigh -s"In Progress" --created month -lbackend -l"high-prio"

# Time-based queries
jira issue list --created -1h            # Created in last hour
jira issue list --updated -30m           # Updated in last 30 minutes
jira issue list --created week           # Created this week
jira issue list --created month          # Created this month
jira issue list --created-before -24w    # Created before 24 weeks ago

# Advanced queries
jira issue list -a"User A" -r"User B"    # Assigned to A, reported by B
jira issue list -ax                      # Unassigned issues
jira issue list -a~x                     # Assigned to anyone
jira issue list -s~Done                  # Status NOT done (~ is NOT)
jira issue list -s~Done --created-before -24w -a~x  # Complex NOT query

# Special queries
jira issue list --history                # Recently viewed by you
jira issue list -r$(jira me) --reverse  # First issue you ever reported
jira issue list -a$(jira me) -tBug -sDone -rFixed --reverse  # First bug you fixed

# Project-specific
jira issue list -pXYZ                    # In project XYZ
jira issue list -w -pXYZ                 # Watching in project XYZ

# Sorting and ordering
jira issue list --order-by rank --reverse     # By rank (same as UI)
jira issue list --order-by created           # By creation date
jira issue list --order-by updated           # By update date

# Output formats
jira issue list --plain                  # Plain text
jira issue list --csv                    # CSV format
jira issue list --raw                    # Raw JSON
jira issue list --columns key,summary,status,assignee  # Custom columns
jira issue list --plain --no-headers     # No headers (for parsing)

# Raw JQL
jira issue list -q "summary ~ cli"       # Execute JQL in project context
```

### Creating Issues

```bash
# Interactive mode
jira issue create

# Non-interactive with all parameters
jira issue create -tBug -s"Bug title" -yHigh -lbug -lurgent -b"Description" --no-input

# Create with specific fields
jira issue create -tStory -s"Story title" -yMedium -lfeature
jira issue create -tTask -s"Task" -a"John Doe"  -CBackend
jira issue create -tBug -s"Critical bug" -yHighest --fix-version v2.0

# Attach to epic during creation
jira issue create -tStory -s"Story title" -PEPIC-42

# Using templates for description
jira issue create --template /path/to/template.md
jira issue create --template -                    # From stdin

# Pipe description from stdin
echo "Description from pipeline" | jira issue create -s"Summary" -tTask

# With custom fields
jira issue create --custom field1=value1 --custom field2=value2
```

### Editing Issues

```bash
# Interactive edit
jira issue edit ISSUE-1

# Update specific fields
jira issue edit ISSUE-1 -s"New summary"
jira issue edit ISSUE-1 -yHigh
jira issue edit ISSUE-1 -b"New description"

# Update multiple fields at once
jira issue edit ISSUE-1 -s"New summary" -yHigh -lurgent --no-input

# Add and remove labels/components
jira issue edit ISSUE-1 --label new-label
jira issue edit ISSUE-1 --label -old-label --label new-label
jira issue edit ISSUE-1 --component -FE --component BE

# Update fix version
jira issue edit ISSUE-1 --fix-version v2.0
jira issue edit ISSUE-1 --fix-version -v1.0 --fix-version v2.0
```

### Assigning Issues

```bash
# Interactive assign
jira issue assign

# Assign to specific user
jira issue assign ISSUE-1 "Jon Doe"

# Assign to self
jira issue assign ISSUE-1 $(jira me)

# Assign based on keyword (prompts if multiple matches)
jira issue assign ISSUE-1 john

# Assign to default assignee
jira issue assign ISSUE-1 default

# Unassign
jira issue assign ISSUE-1 x
```

### Moving/Transitioning Issues

```bash
# Interactive transition
jira issue move

# Move to specific status
jira issue move ISSUE-1 "In Progress"
jira issue move ISSUE-1 Done

# Move with comment
jira issue move ISSUE-1 "In Progress" --comment "Started working on it"

# Set resolution and assignee while moving
jira issue move ISSUE-1 Done -RFixed
jira issue move ISSUE-1 Done -RFixed -a$(jira me)
```

### Viewing Issues

```bash
# View issue in terminal
jira issue view ISSUE-1

# View with recent comments
jira issue view ISSUE-1 --comments 5
jira issue view ISSUE-1 --comments 10
```

### Linking Issues

```bash
# Interactive linking
jira issue link

# Link with relationship type
jira issue link ISSUE-1 ISSUE-2 Blocks
jira issue link ISSUE-1 ISSUE-2 "is blocked by"
jira issue link ISSUE-1 ISSUE-2 Duplicates
jira issue link ISSUE-1 ISSUE-2 Relates

# Add remote web link
jira issue link remote ISSUE-1 https://example.com "Example text"
jira issue link remote ISSUE-1 https://github.com/org/repo/pull/123 "PR #123"

# Unlink issues
jira issue unlink ISSUE-1 ISSUE-2
```

### Cloning Issues

```bash
# Clone an issue
jira issue clone ISSUE-1

# Clone with modifications
jira issue clone ISSUE-1 -s"Modified summary"
jira issue clone ISSUE-1 -s"New title" -yHigh -a$(jira me)

# Clone and replace text in summary/description
jira issue clone ISSUE-1 -H"old text:new text"
jira issue clone ISSUE-1 -H"2024:2025"
```

### Deleting Issues

```bash
# Interactive delete
jira issue delete

# Delete specific issue
jira issue delete ISSUE-1

# Delete with all subtasks
jira issue delete ISSUE-1 --cascade
```

### Comments

```bash
# Add comment interactively
jira issue comment add

# Add comment with text
jira issue comment add ISSUE-1 "My comment text"

# Add internal comment (visible only to team)
jira issue comment add ISSUE-1 "Internal note" --internal

# Add comment from template
jira issue comment add ISSUE-1 --template /path/to/comment.md
jira issue comment add ISSUE-1 --template -

# Pipe comment from stdin
echo "Comment from pipeline" | jira issue comment add ISSUE-1
```

### Worklog (Time Tracking)

```bash
# Add worklog interactively
jira issue worklog add

# Add worklog with time
jira issue worklog add ISSUE-1 "2h 30m" --no-input
jira issue worklog add ISSUE-1 "1d" --no-input
jira issue worklog add ISSUE-1 "30m" --no-input

# Add worklog with comment
jira issue worklog add ISSUE-1 "2h" --comment "Implementation work" --no-input
jira issue worklog add ISSUE-1 "1h 15m" --comment "Code review" --no-input
```

## Epic Management

### Listing Epics

```bash
# List all epics (explorer view)
jira epic list

# List epics (table view)
jira epic list --table

# List epics with filters (same filters as issue list)
jira epic list -r$(jira me)              # Reported by me
jira epic list -sOpen                     # Open epics
jira epic list -yHigh                     # High priority
jira epic list -r$(jira me) -sOpen -yHigh  # Combined filters

# List issues in an epic
jira epic list EPIC-1

# List epic issues with filters
jira epic list EPIC-1 -ax                # Unassigned issues in epic
jira epic list EPIC-1 -yHigh             # High priority issues in epic
jira epic list EPIC-1 -a$(jira me)      # My issues in epic

# Order epic issues by rank
jira epic list EPIC-1 --order-by rank --reverse
```

### Creating Epics

```bash
# Interactive
jira epic create

# With parameters
jira epic create -n"Epic name" -s"Epic summary"
jira epic create -n"Q1 Features" -s"Q1 Feature Development" -yHigh -lfeature -b"Epic description"
```

### Managing Epic Issues

```bash
# Add issues to epic (interactive)
jira epic add

# Add issues to epic (up to 50 at once)
jira epic add EPIC-1 ISSUE-1 ISSUE-2 ISSUE-3

# Remove issues from epic (interactive)
jira epic remove

# Remove issues from epic (up to 50 at once)
jira epic remove ISSUE-1 ISSUE-2 ISSUE-3
```

## Sprint Management

### Listing Sprints

```bash
# List all sprints (explorer view)
jira sprint list

# List sprints (table view)
jira sprint list --table

# Current active sprint
jira sprint list --current

# Current sprint with filters
jira sprint list --current -a$(jira me)
jira sprint list --current -yHigh
jira sprint list --current -a$(jira me) -yHigh -s"In Progress"

# Previous sprint
jira sprint list --prev

# Next planned sprint
jira sprint list --next

# Filter by sprint state
jira sprint list --state active
jira sprint list --state future
jira sprint list --state future,active
jira sprint list --state closed

# Specific sprint (use ID from sprint list)
jira sprint list SPRINT_ID
jira sprint list SPRINT_ID -yHigh
jira sprint list SPRINT_ID -a$(jira me)
jira sprint list SPRINT_ID -yHigh -a$(jira me) -s"In Progress"

# Order sprint issues by rank
jira sprint list SPRINT_ID --order-by rank --reverse
```

### Adding Issues to Sprint

```bash
# Add issues interactively
jira sprint add

# Add multiple issues (up to 50 at once)
jira sprint add SPRINT_ID ISSUE-1 ISSUE-2 ISSUE-3
```

## Release Management

Interact with releases (project versions). Ensure the [feature is enabled](https://support.atlassian.com/jira-software-cloud/docs/enable-releases-and-versions/) on your instance.

```bash
# List releases for default project
jira release list

# List releases for specific project by ID
jira release list --project 1000

# List releases for specific project by key
jira release list --project MYPROJ
```

## Other Commands

### Project and Board Navigation

```bash
# Open project in browser
jira open

# Open specific issue in browser
jira open ISSUE-1

# List all projects you have access to
jira project list

# List all boards in a project
jira board list
```

### User Information

```bash
# Get your own username (useful in scripts)
jira me
```

## Navigation and Interaction

When in interactive UI:

**Movement:**
- **Arrow keys** or **j,k,h,l** - Navigate through list
- **g** - Jump to top
- **G** - Jump to bottom
- **CTRL+f** - Scroll page down
- **CTRL+b** - Scroll page up

**Actions:**
- **v** - View selected issue details
- **m** - Transition the selected issue
- **CTRL+r** or **F5** - Refresh the list
- **ENTER** - Open selected issue in browser
- **c** - Copy issue URL to clipboard (requires xclip/xsel on Linux)
- **CTRL+k** - Copy issue key to clipboard
- **w** or **TAB** - Toggle focus between sidebar and content
- **q** / **ESC** / **CTRL+c** - Quit
- **?** - Show help window

## Output Formats and Options

### Format Options

```bash
# Interactive table (default)
jira issue list

# Plain text output (for scripts)
jira issue list --plain

# CSV format (for spreadsheets)
jira issue list --csv

# Raw JSON (for programmatic parsing)
jira issue list --raw
```

### Column Selection

```bash
# Default columns
jira issue list

# Custom columns
jira issue list --columns key,summary,status
jira issue list --columns key,summary,status,assignee,priority
jira issue list --columns created,updated,reporter

# Without headers (for parsing)
jira issue list --plain --no-headers
jira issue list --csv --no-headers
```

### Pagination

jira-cli handles pagination automatically. For very large result sets, the tool will fetch additional pages as needed.
