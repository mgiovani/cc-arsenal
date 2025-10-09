---
description: "Create a PR with conventional commit format and pre-filled template"
argument-hint: "[--base branch] [--reviewers user1,user2] [--labels label1,label2] [--assignees user1,user2]"
allowed-tools: ["Bash", "Read", "Write"]
---

# Create Pull Request Command

Create a GitHub Pull Request following conventional commits specification, pre-filled with the PR template, and opened in the browser for final review.

## Your Task

1. **Extract Jira Ticket** (if present):
   - Get current branch name using `git branch --show-current`
   - Extract Jira ticket pattern (e.g., `ABC-123`, `PROJ-456`) from branch name
   - Format: `[TICKET-123]` for PR title prefix

2. **Determine Base Branch**:
   - Use `--base` argument if provided
   - Otherwise, detect repository default branch using `gh repo view --json defaultBranchRef --jq .defaultBranchRef.name`
   - Fall back to `main` if detection fails

3. **Analyze Changes**:
   - Run `git log origin/<base-branch>..HEAD` to get all commits in the branch
   - Run `git diff origin/<base-branch>...HEAD` to understand the full scope of changes
   - Identify the primary change type for the PR title

4. **Generate PR Title** (Conventional Commit Format):
   - Format: `[JIRA-123] type(scope): description` (if Jira ticket found)
   - Or: `type(scope): description` (if no Jira ticket)
   - Type: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`
   - Scope: Component/module affected (optional but recommended)
   - Description: Concise summary in imperative mood (max 50 chars after prefix)
   - Examples:
     - `[ABC-123] feat(auth): add OAuth2 login support`
     - `[PROJ-456] fix(api): resolve null pointer in user endpoint`
     - `refactor(parser): extract validation logic`

5. **Fill PR Template**:
   - Look for `.github/pull_request_template.md` or `.github/PULL_REQUEST_TEMPLATE.md`
   - If template exists: Fill it based on the changes, preserving the template structure
   - If no template: Create a standard body with:
     ```markdown
     ## Summary
     [Brief description of changes]

     ## Changes
     - Change 1
     - Change 2

     ## Testing
     - [ ] Tests added/updated
     - [ ] Manual testing completed

     ## Breaking Changes
     [If applicable, describe breaking changes]
     ```
   - Analyze commits and changes to fill each section appropriately
   - Keep the original template structure intact - DO NOT deviate from it

6. **Create PR with gh CLI**:
   - **ALWAYS use `--web` flag**: This opens the browser for user to finish PR creation
   - **Pre-populate with `--title` and `--body-file`**: These work WITH `--web` to pre-fill the web form
   - **YOU MUST generate the title and body** based on the analysis of changes and conventional commit rules
   - Steps:
     1. Analyze changes and generate conventional commit title following the format rules
     2. Fill PR template based on changes and save to `/tmp/pr-body-{timestamp}.md`
     3. Display the generated content to user
     4. Open browser with pre-filled title and body using `--title` and `--body-file` flags
   - Support optional arguments that work with `--web`:
     - `--base branch` → `--base branch` (specify target branch)
     - `--title string` → Pre-fills the PR title in web form
     - `--body-file file` → Pre-fills the PR body from file in web form
     - `--reviewer handle` → `--reviewer user1 --reviewer user2` (one flag per reviewer)
     - `--label name` → `--label label1 --label label2` (one flag per label)
     - `--assignee handle` → `--assignee user1 --assignee user2` (one flag per assignee)
     - `--draft` → `--draft` (create as draft PR)
   - Example:
     ```bash
     # Generate and save body
     cat > /tmp/pr-body-20250108.md << 'EOF'
     ## Summary
     Added OAuth2 authentication support...
     EOF

     # Display to user
     echo "Title: [ABC-123] feat(auth): add OAuth2 support"
     echo "Body saved to: /tmp/pr-body-20250108.md"

     # Open in browser with pre-filled data
     gh pr create \
       --title "[ABC-123] feat(auth): add OAuth2 support" \
       --body-file /tmp/pr-body-20250108.md \
       --base develop \
       --reviewer john --reviewer jane \
       --label enhancement --label security \
       --web
     ```
   - Note: User can still edit title and body in browser before creating

## Argument Parsing

Parse optional arguments from the command invocation:
- `--base branch` or `-b branch` (target branch, defaults to repo default)
- `--reviewers user1,user2` or `-r user1,user2` (comma-separated list)
- `--labels label1,label2` or `-l label1,label2` (comma-separated list)
- `--assignees user1,user2` or `-a user1,user2` (comma-separated list)
- `--draft` or `-d` (create as draft PR)

## Important Notes

- **Template Preservation**: Fill the existing PR template WITHOUT changing its structure
- **Conventional Commits**: PR title MUST follow conventional commit format
- **Jira Integration**: Extract ticket number from branch name (patterns: `PROJ-123`, `ABC-456`, etc.)
- **Browser Review**: Always use `--web` to let user finalize the PR
- **Multiple Commits**: Summarize all commits in the PR, focus on the overall change
- **Breaking Changes**: Clearly indicate if the PR contains breaking changes

## Examples

```bash
# Simple PR (uses repo default base branch)
/create-pr

# Target specific base branch
/create-pr --base develop

# With reviewers and labels
/create-pr --reviewers john,jane --labels bug,urgent

# Full options
/create-pr -b develop -r alice,bob -l enhancement,security -a alice
```

Create the PR with pre-filled information and open in browser for final review and submission.
