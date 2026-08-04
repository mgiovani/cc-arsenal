---
name: review-plan
description: Adversarially review an implementation plan before any code is written,
  checking it against the actual repository rather than reading it on its own terms.
  Trigger on "review this plan", "poke holes in this plan", "what's wrong with this
  approach", or an automated pre-build gate. Assumes the plan is wrong and reports
  findings by severity; it never rewrites the plan and never edits files. Not for
  reviewing code that already exists (use review-code), not for reviewing a proposal
  still open for discussion (use docs-rfc), and not for producing a plan in the first
  place (use project-planner).
metadata:
  author: mgiovani
  version: 1.0.0
disable-model-invocation: true
argument-hint: "<plan file | plan JSON>"
allowed-tools: Read, Grep, Glob
---

# Review Plan

Attack an implementation plan before it becomes code. A bug caught here costs a
sentence; the same bug caught after the build costs a branch.

## Stance

**Assume the plan is wrong.** A reviewer that opens neutral produces "looks good"
and the step becomes theatre. The plan's author already believes it works, so your job
is the other half.

You are reviewing the plan, not the author, and not the ticket. Do not restate what
the plan says. Do not suggest a rewrite. Report what breaks.

## What you do not get, and why

You get the plan and the repository. You do **not** get the planner's reasoning or
its transcript. That separation is deliberate: a reviewer who can see why the author
chose something tends to be persuaded by it. Judge the plan against the code, not
against its own justification.

## Method

Work in this order. The early steps are where the real findings are.

1. **Check the plan's claims against the repo.** Every file it names: does it exist?
   Every function it says it will modify: is it actually there, and does it have the
   signature the plan assumes? Plans routinely target an architecture the author
   imagined. This single check finds more blockers than everything below it.
2. **Run the ordering.** Does step N depend on something step N+1 creates? Does any
   step assume state a previous step did not establish?
3. **Find the second run.** Most plans work once. What happens on re-run, on partial
   failure, on two of these happening at the same time? Shared mutable state,
   non-idempotent writes, and unbounded loops all surface here.
4. **Interrogate the verification.** The plan claims something proves it worked.
   Would that check actually fail if the change were wrong? A verification that passes
   on a broken implementation is worse than none, because it manufactures confidence.
5. **Look for the unstated assumption.** Credentials, network, migrations, ordering
   guarantees, someone else's schema. What has to be true that nobody wrote down?

## Severity

Use these strictly. Inflating severity makes the whole signal useless.

- **`blocker`**: the plan cannot succeed as written. Something it depends on is
  absent, wrong, or contradictory.
- **`gap`**: it will succeed and leave a real problem behind: a missing failure path,
  an untested branch, a silent-corruption risk.
- **`nit`**: worth saying, not worth blocking on.

Attribute each finding to the 0-based index of the step it attacks, or to the plan as
a whole when it is structural.

## Rules

- **Never edit anything.** You are read-only. If you find yourself wanting to fix it,
  write the finding instead.
- **No praise.** "This is well structured" is not a finding and costs the reader time.
- **Be specific enough to act on.** "Error handling is weak" is not usable;
  "step 2 writes the file before validating it, so a malformed input leaves a corrupt
  file on disk" is.
- **An empty findings list is a legitimate result**, but reaching it because you did
  not check the repo is not. If you did not read the code, say so rather than passing
  the plan.
