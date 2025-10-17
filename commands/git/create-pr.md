---
description: "Create a PR with conventional commit format and pre-filled template"
argument-hint: "[--base branch] [--reviewers user1,user2] [--labels label1,label2] [--assignees user1,user2]"
allowed-tools: ["Bash", "Read", "Write"]
---

# Create Pull Request Command

Create a GitHub Pull Request following conventional commits specification, pre-filled with the PR template, and opened in the browser for final review.

## Your Task

1. **Validate Preconditions**:
   - Check working tree is clean: `git status --porcelain`
   - Get current branch: `git branch --show-current`
   - Verify branch is not main/master
   - Check commits exist: `git log origin/<base>..HEAD --oneline`
   - Extract ticket ID from branch name (e.g., `ABC-123` from `feature/ABC-123-description`)
   - Display compact validation summary (max 60 chars per line)

2. **Ask for Confirmation** (after validation):
   - Show compact summary with ticket, commits count, authors
   - Ask: `Create PR? (y/n/e to edit):`
   - Accept: `y`, `yes`, `n`, `no`, `e`, `edit`
   - On `e`: ask for custom title/body modifications

3. **Determine Base Branch**:
   - Use `--base` argument if provided
   - Otherwise use: `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`
   - Fall back to `main` if detection fails

4. **Analyze Changes**:
   - Run `git log origin/<base>..HEAD --format="%h %s"` to get commits
   - Run `git diff origin/<base>...HEAD --stat` for file changes
   - Identify primary change type for PR title

5. **Generate PR Title** (Conventional Commit Format):
   - Format: `type(scope): [TICKET-123] description` (max 72 chars)
   - Or: `type(scope): description` (if no ticket)
   - Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`
   - Examples:
     - `feat(auth): [ABC-123] add OAuth2 login support`
     - `fix(api): resolve null pointer in user endpoint`

6. **Fill PR Template**:
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

7. **Push and Create PR**:
   - **CRITICAL Step 1**: Push branch FIRST: `git push -u origin <branch>`
   - **Step 2**: Write body to temp file: `/tmp/pr-body-$(date +%s).md`
   - **Step 3**: Open PR in browser with --web (for user to finish):
     ```bash
     # Push first (MUST DO THIS)
     git push -u origin $(git branch --show-current)

     # Create temp body file
     cat > /tmp/pr-body-$(date +%s).md << 'EOF'
     ## Summary
     [Your generated content here]
     EOF

     # Open in browser with pre-filled data
     gh pr create \
       --title "type(scope): [TICKET] description" \
       --body-file /tmp/pr-body-<timestamp>.md \
       --base main \
       --web
     ```
   - **CRITICAL**: DO NOT use --reviewer, --assignee, or --label with --web (they conflict!)
   - User will add reviewers/labels in the web UI
   - Display: "Opening PR in browser for final review..."

## Argument Parsing

Parse optional arguments from the command invocation:
- `--base branch` or `-b branch` (target branch, defaults to repo default)
- `--draft` or `-d` (create as draft PR)

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
