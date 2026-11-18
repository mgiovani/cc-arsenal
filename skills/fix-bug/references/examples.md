# Fix Bug - Examples & Reference

## Contents

- [Argument Parsing](#argument-parsing)
- [Usage Examples](#usage-examples)
- [Browser Testing Integration (Optional)](#browser-testing-integration-optional)
- [Error Handling](#error-handling)

## Argument Parsing

Parse optional arguments from the user's request:

Optional flags:

| Flag | Effect |
|------|--------|
| `--branch name` or `-b name` | Create fix on a specific branch (default: current branch) |
| `--interactive` or `-i` | Prompt for confirmation at each phase |
| `--test-only` | Only reproduce and analyze the bug, do not implement fix |

## Usage Examples

### Example 1: Simple Bug Fix (inline, default)

Invoke the skill (Claude Code: `/fix-bug User profile page throws 404 on refresh`):

Single file, single root cause, no task chain needed:
1. Phase 0: discover project uses `npm test` and `npm run lint`
2. Phase 1: find failing test or create one, locate routing bug
3. Phase 2: plan fix (add route configuration)
4. Phase 3: implement fix
5. Phase 4: verify all tests pass
6. Phase 5: commit `fix(routing): add profile route configuration`

### Example 2: Bug with Issue Number (task chain, multi-file)

Invoke the skill (Claude Code: `/fix-bug #789 --branch fix/payment-webhook`):

Webhook signature validation touches the handler, the signing util, and two
call sites, spans multiple files, so create the six-task chain first:
1. Create the task chain for all 6 phases with strict sequential dependencies
2. Phase 0: fetch issue `gh issue view 789`, discover `make test` and `make lint`
3. Phase 1: reproduce failing webhook, root cause: missing signature validation
4. Phase 2: plan fix: add HMAC signature verification
5. Phase 3: implement signature validation
6. Phase 4: verify with integration tests
7. Phase 5: commit: `fix(webhooks): validate payment signatures\n\nCloses #789`
8. Track progress: the task/todo tool (`TaskList` in Claude Code) after each phase shows which task unblocked; otherwise keep the checklist in the reply

### Example 3: Interactive Bug Fix

Invoke the skill (Claude Code: `/fix-bug "Auth tokens expire too quickly" --interactive`). The run pauses for the user four times: after Phase 0 to confirm the discovered commands, after Phase 1 to confirm the root cause, after Phase 2 to approve the fix plan, and before the commit to review the diff.

### Example 4: Analysis Only

Invoke the skill (Claude Code: `/fix-bug Database query timeout in reports --test-only`). Only Phases 0-2 run. The report gives the root cause with its evidence and the fix approaches worth considering; nothing is implemented or committed.

## Browser Testing Integration (Optional)

If the bug affects a web UI and the agent-browser skill is available:

After Phase 3 (Implementation), before Phase 4:

1. Start the development server using the discovered dev command from Phase 0

2. Browser testing (if the agent-browser skill is available):
```
Use agent-browser skill to:
1. Navigate to the affected page/component
2. Reproduce the original bug scenario
3. Verify the bug is now fixed
4. Test edge cases
5. Take screenshots as evidence
```

3. Report browser test results: include them in the final summary with screenshot evidence.

When to skip browser testing:
- Backend-only bugs (API, database, services)
- CLI tool bugs
- Unit test failures (not integration/E2E)
- No development server available
- User explicitly requested to skip

## Error Handling

- **Tests fail after the fix.** Re-run the failing test verbosely and work out whether the fix caused a regression; adjust or revert it, because a commit with a failing test hides which change broke what.
- **The bug description is ambiguous.** Ask the user with the structured question tool where one exists (`AskUserQuestion`, `question`, `ask_user`); otherwise ask in chat and wait for the answer. Get expected versus actual behavior, the steps to reproduce, and any error text. A guess here means fixing a different bug.
- **The bug will not reproduce.** Check the test command is the right one and whether the bug is already fixed on this branch, then ask for more reproduction detail. If it still does not reproduce, report what you tried and stop.
- **There are several root causes.** List every contributing factor and ask the user which to fix first, and whether they belong in one change or separate ones.
