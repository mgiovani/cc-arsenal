# Fix Bug - Examples & Reference

## Argument Parsing

Parse optional arguments from the command invocation:

**Optional Flags**:
- `--branch name` or `-b name`: Create fix on a specific branch (default: current branch)
- `--interactive` or `-i`: Prompt for confirmation at each phase
- `--test-only`: Only reproduce and analyze the bug, do not implement fix

## Usage Examples

### Example 1: Simple Bug Fix (inline, default)

```bash
/fix-bug User profile page throws 404 on refresh
```

Single file, single root cause — no task chain needed:
1. **Phase 0**: Discover project uses `npm test` and `npm run lint`
2. **Phase 1**: Find failing test or create one, locate routing bug
3. **Phase 2**: Plan fix (add route configuration)
4. **Phase 3**: Implement fix
5. **Phase 4**: Verify all tests pass
6. **Phase 5**: Commit `fix(routing): add profile route configuration`

### Example 2: Bug with Issue Number (task chain, multi-file)

```bash
/fix-bug #789 --branch fix/payment-webhook
```

Webhook signature validation touches the handler, the signing util, and two
call sites — spans multiple files, so create the six-task chain first:
1. **Create task chain** for all 6 phases with strict sequential dependencies
2. **Phase 0**: Fetch issue `gh issue view 789`, discover `make test` and `make lint`
3. **Phase 1**: Reproduce failing webhook, root cause: missing signature validation
4. **Phase 2**: Plan fix: add HMAC signature verification
5. **Phase 3**: Implement signature validation
6. **Phase 4**: Verify with integration tests
7. **Phase 5**: Commit: `fix(webhooks): validate payment signatures\n\nCloses #789`
8. **Track progress**: `TaskList` after each phase shows which task unblocked

### Example 3: Interactive Bug Fix

```bash
/fix-bug "Auth tokens expire too quickly" --interactive
```

**Process**:
1. Prompt user after Phase 0 (confirm discovered commands)
2. Prompt user after Phase 1 (confirm root cause analysis)
3. Prompt user after Phase 2 (approve fix plan)
4. Implement fix
5. Prompt user before commit (review changes)

### Example 4: Analysis Only

```bash
/fix-bug Database query timeout in reports --test-only
```

**Process**:
1. Run Phases 0-2 only
2. Report root cause analysis
3. Suggest fix approaches
4. Do not implement or commit
5. Let user decide next steps

## Browser Testing Integration (Optional)

If the bug affects a web UI and the agent-browser skill is available:

**After Phase 3 (Implementation), before Phase 4**:

1. **Start Development Server** using discovered dev command from Phase 0

2. **Browser Testing** (if agent-browser skill is available):
```
Use agent-browser skill to:
1. Navigate to the affected page/component
2. Reproduce the original bug scenario
3. Verify the bug is now fixed
4. Test edge cases
5. Take screenshots as evidence
```

3. **Report Browser Test Results** - Include in final summary with screenshot evidence.

**When to Skip Browser Testing**:
- Backend-only bugs (API, database, services)
- CLI tool bugs
- Unit test failures (not integration/E2E)
- No development server available
- User explicitly requested to skip

## Error Handling

### Test Failures After Fix

1. Re-run the specific test with verbose output
2. Analyze the new failure mode
3. Check if the fix introduced a regression
4. Adjust the fix or revert if necessary
5. Never commit code with failing tests

### Ambiguous Bug Description

1. Use `AskUserQuestion` to clarify:
   - Expected vs actual behavior
   - Steps to reproduce
   - Error messages or symptoms
2. Do not proceed with guesses

### Cannot Reproduce Bug

1. Verify the correct test command is being used
2. Check if the bug was already fixed
3. Ask user for more details on reproduction
4. Document findings and report inability to reproduce

### Multiple Root Causes

1. Identify all contributing factors
2. Ask user which to fix first
3. Consider if they should be fixed together or separately
4. Plan accordingly

## Quality Checklist

See "Phase 4: Quality Verification" in [SKILL.md](../SKILL.md) — that's the
authoritative checklist, not duplicated here.

## Commit Message Guidelines

- Type: `fix:` (for bug fixes)
- Scope: `(module)` if applicable
- Subject: Describe WHAT was fixed (not how)
- Body: Explain WHY this fixes the bug
- Footer: Reference issue numbers

**Example**:
```
fix(auth): prevent token expiration on page reload

The authentication middleware was not refreshing tokens when
the user reloaded the page, causing premature logouts.

This fix adds token refresh logic to the middleware that
runs on every page load, checking token expiration and
refreshing when needed.

Closes #123
```
