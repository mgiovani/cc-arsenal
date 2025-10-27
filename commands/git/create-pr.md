---
description: "Create a PR with conventional commit format and pre-filled template"
argument-hint: "[--base branch] [--draft]"
allowed-tools: ["Bash(git *)", "Bash(gh *)", "Read", "Write"]
---

# Create Pull Request Command

Create a GitHub Pull Request following conventional commits specification, pre-filled with the PR template, and opened in the browser for final review.

## Your Task

1. **Validate Preconditions**:
  - Check working tree is clean: `git status --porcelain`
  - Get current branch: `git branch --show-current`
  - Verify branch is not main/master
  - Check commits exist: `git log origin/<base>..HEAD --oneline`
  - Extract ticket ID from branch name (e.g., `ABC-123` from `feature/ABC-123_description`)
  - Display compact validation summary (max 60 chars per line)

2. **Determine Base Branch**:
  - Use `--base` argument if provided
  - Otherwise use: `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`
  - Fall back to `main` if detection fails

3. **Analyze Changes**:
  - Run `git log origin/<base>..HEAD --format="%h %s"` to get commits
  - Run `git diff origin/<base>...HEAD --stat` for file changes
  - Identify primary change type for PR title

4. **Generate PR Title** (Conventional Commit Format):
  - Format: `type(scope): [TICKET-123] description` (max 72 chars)
  - Or: `type(scope): description` (if no ticket)
  - Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`
  - Examples:
    - `feat(auth): [ABC-123] add OAuth2 login support`
    - `fix(api): resolve null pointer in user endpoint`

5. **Fill PR Template**:
  - Look for `.github/pull_request_template.md`
  - Fill based on commits and changes
  - Save to `/tmp/pr-body-$(date +%s).md`
  - If no template, use:
    ```markdown
    ## Summary
    [Brief description]

    ## Changes
    - [Bullet points from commits]

    ## Testing
    - [ ] Tests added/updated
    - [ ] Manual testing completed
    ```

6. **Ask for Confirmation**:
  - Show compact summary with ticket, commits count, authors
  - Display preview of generated PR title
  - Display preview of generated PR body
  - Ask: `Create PR? (y/n/e to edit):`
  - Accept: `y`, `yes`, `n`, `no`, `e`, `edit`
  - On `e`: ask for custom title/body modifications

7. **Push and Create PR** (after user confirms):
  - **CRITICAL Step 1**: Push branch FIRST: `git push -u origin <branch>`
  - **Step 2**: Create temp body file with timestamp variable
  - **Step 3**: Open PR in browser with --web (for user to finish):
    ```bash
    # Push first (MUST DO THIS)
    git push -u origin $(git branch --show-current)

    # Create temp body file (capture timestamp in variable)
    BODY_FILE="/tmp/pr-body-$(date +%s).md"
    cat > "$BODY_FILE" << 'EOF'
    ## Summary
    [Your generated content here]
    EOF

    # Open in browser with pre-filled data (use determined base branch)
    # Add --draft if user specified --draft or -d flag
    gh pr create \
      --title "type(scope): [TICKET] description" \
      --body-file "$BODY_FILE" \
      --base <determined-base-branch> \
      --web
    ```
  - **CRITICAL**: DO NOT use --reviewer, --assignee, or --label with --web (they conflict!)
  - User will add reviewers/labels in the web UI
  - Display: "Opening PR in browser for final review..."

## Argument Parsing

Parse optional arguments from the command invocation:
- `--base branch` or `-b branch` (target branch, defaults to repo default)
- `--draft` or `-d` (if present, add `--draft` flag to gh pr create command)

**Note**: Reviewers, labels, and assignees must be added in the web UI due to gh CLI limitations with --web flag.

## Important Notes

- **Template Preservation**: Fill the existing PR template WITHOUT changing its structure
- **Conventional Commits**: PR title MUST follow conventional commit format
- **Ticket Integration**: Extract ticket number from branch name (patterns: `ABC-123`, `PROJ-456`, etc.) and place after type/scope
- **Browser Review**: Always use `--web` to let user finalize the PR
- **Multiple Commits**: Summarize all commits in the PR, focus on the overall change
- **Breaking Changes**: Clearly indicate if the PR contains breaking changes

## Output Format

**Validation Summary** (keep lines under 60 chars):
```
✅ Branch: feature/ABC-123-add-authentication
✅ Ticket: ABC-123 (In Progress)
✅ Commits: 8 commits ready
⚠️ Authors: Multiple authors detected

Create PR? (y/n/e to edit):
```

## Examples

```bash
# Simple PR (uses repo default base branch)
/create-pr

# Target specific base branch
/create-pr --base develop

# Create as draft PR
/create-pr --draft

# Specify base branch and draft
/create-pr -b develop -d
```

After pushing the branch, the PR will open in your browser pre-filled with title and body. Add reviewers/labels in the web UI before creating.
