# Posting a review to GitHub

Run this flow only when the user explicitly asks to post the review (for example "post it on the PR" or `--comment`). Without that request the report stays in chat and no `gh` write command runs.

The scratch dir `<scratch>` is the `mktemp -d` directory used for the whole review. It is never inside the repo.

## 1. Findings contract

Each agent writes `<scratch>/findings/<lane>.json` (core agents write `core-<prefix>.json`) in the shape defined by the shared preamble in [agent-prompts.md](agent-prompts.md#shared-preamble).

`severity` is Critical, Major, Minor or Nit. `verdict` is CONFIRMED, PLAUSIBLE, REJECTED or null (not verified). Save the diff the review used to `<scratch>/pr.diff` (`gh pr diff <n> > <scratch>/pr.diff`, or the `git diff origin/<base>...HEAD` fallback).

## 2. Merge and anchor

```bash
uv run <skill-dir>/scripts/merge_findings.py --findings <scratch>/findings --diff <scratch>/pr.diff --out <scratch>
```

It drops REJECTED findings, merges duplicates (duplicate versions go in a `<details>` block), and writes:

- `merged.json`: all surviving findings.
- `review-payload.json`: the `gh api` payload (`event`, `body`, `comments`).

A finding becomes an inline comment only when its `line` is on the RIGHT side and inside a hunk of `base...HEAD`. Everything else goes in the review body: severity table, dependency summary, praise, pre-existing items, verdict summary. If the script is unavailable, apply the same rules by hand.

## 3. Preview

Show the user, before any write:

- Count of inline comments vs body-only items.
- The body text and each inline comment.

Post only after the user confirms.

## 4. Post one review

```bash
gh api repos/{owner}/{repo}/pulls/<n>/reviews --method POST --input <scratch>/review-payload.json
```

Post exactly one review with `"event": "COMMENT"`. Never use `REQUEST_CHANGES` or `APPROVE`: you cannot request changes on your own PR, and approval is the human's call. Do not post comments one by one.

## 5. Handle 422

HTTP 422 means an inline anchor was rejected. List existing reviews first (the command in section 6), then move the rejected comments into the review body and retry once.

## 6. Handle 504

`gh api` can return 504 and still create the review. Before any retry:

```bash
gh api repos/{owner}/{repo}/pulls/<n>/reviews --jq '.[] | {id, state, submitted_at, body: .body[0:80]}'
```

If a review with your body already exists, stop and report its id. Retry only when none exists. Never double-post.

## 7. Comment style

- 1 to 3 plain sentences per comment: the problem, then the fix.
- Add a code suggestion only when it is short.
- No praise padding ("Great job", "Nice work"), no emoji, no restating the code, no stacked hedges.
- Name the concrete symptom, not the category.
- Run `stopslop <file>` on drafted bodies when it is installed, and fix what it flags. If it is not installed, reread each comment against the rules above.
