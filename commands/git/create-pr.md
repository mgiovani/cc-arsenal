---
description: "Create a PR with conventional commit format and pre-filled template"
argument-hint: "[--base branch] [--draft]"
allowed-tools: ["Bash(git *)", "Bash(gh *)", "Read", "Write", "Task", "TodoWrite"]
---

# Create Pull Request Command

Create a GitHub Pull Request following conventional commits specification, pre-filled with the PR template, and opened in the browser for final review.

## Quality Guidelines

**CRITICAL**: PR descriptions must accurately reflect ACTUAL changes:
1. **Verify every claim** - Each bullet point must correspond to real code changes
2. **Check commit messages** - Use actual commit messages, don't paraphrase incorrectly
3. **Accurate scope** - Only mention files/modules that actually changed
4. **No hallucinated features** - Don't describe functionality that wasn't implemented

## Your Task

### Phase 1: Deep Change Analysis (Use SubAgents for Comprehensive PRs)

For PRs with multiple commits or complex changes, spawn parallel agents:

```
If branch has >3 commits or >10 files changed:

Agent 1 - Feature Analysis:
- prompt: "Analyze all commits in this branch. What user-facing features or fixes were implemented? Focus on WHAT changed for users, not HOW the code changed."
- subagent_type: "general-purpose"

Agent 2 - Technical Analysis:
- prompt: "Analyze the code changes. What architectural or technical changes were made? Look for: new dependencies, API changes, database migrations, config changes."
- subagent_type: "general-purpose"

Agent 3 - Risk Assessment:
- prompt: "Identify risks in these changes: breaking changes, security implications, performance impacts, areas needing extra review. Check for removed tests or skipped validations."
- subagent_type: "general-purpose"

Agent 4 - Test Coverage:
- prompt: "Check if changes include tests. For each modified file, is there a corresponding test change? List untested changes that should have tests."
- subagent_type: "Explore"

Merge results → Generate accurate, comprehensive PR description
```

### Track Progress with TodoWrite

Use TodoWrite to track PR creation steps:

```
TodoWrite:
- [ ] Validate preconditions (clean tree, correct branch)
- [ ] Analyze commits and changes
- [ ] Generate PR title (conventional format)
- [ ] Fill PR template with accurate description
- [ ] Get user confirmation
- [ ] Push branch and create PR

Mark each as in_progress → completed as you proceed.
```

### Phase 2: Validate Preconditions

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

6. **Verify PR Description Accuracy**:
  Before showing to user, verify each claim:
  ```
  For each bullet point in PR description:
  1. Find the corresponding commit or code change
  2. If no evidence found, remove the claim
  3. Verify file paths mentioned actually exist
  4. Check that feature descriptions match actual code behavior
  ```

7. **Ask for Confirmation**:
  - Show compact summary with ticket, commits count, authors
  - Display preview of generated PR title
  - Display preview of generated PR body
  - Ask: `Create PR? (y/n/e to edit):`
  - Accept: `y`, `yes`, `n`, `no`, `e`, `edit`
  - On `e`: ask for custom title/body modifications

8. **Push and Create PR** (after user confirms):
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
