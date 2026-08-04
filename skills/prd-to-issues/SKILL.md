---
name: prd-to-issues
description: Turn an approved PRD into tracked issues, one per requirement, with the
  dependencies between them recorded. Trigger on "file issues for this PRD", "turn this
  spec into tickets", "break this PRD into work", or an automated hand-off after a PRD
  is approved. Creates issues in beads or GitHub and reports what it created; it never
  writes the PRD, never estimates, and never closes or merges anything. Not for writing
  the PRD itself (use product-prd), not for sequencing work inside one ticket (use
  project-planner), and not for filing a single ad-hoc issue you could type yourself.
metadata:
  author: mgiovani
  version: 1.0.0
disable-model-invocation: true
argument-hint: "<path to PRD.md>"
allowed-tools: Read, Grep, Bash
---

# PRD to Issues

The seam between a written spec and a tracked backlog. A PRD is one document; work is
many issues with an order. This is the translation, and it is mechanical on purpose:
the thinking already happened in the PRD.

## What you produce

- **One issue per requirement ID.** `PRD-FR-001` becomes exactly one issue, and the ID
  goes in the title. That ID is the only link back to the spec, and it is what makes a
  re-run recognise its own earlier output.
- **Dependencies between them**, taken from the PRD's own ordering and its stated
  prerequisites, not invented.
- **A report** of what was created, what was skipped, and what blocked.

## Method

1. **Read the whole PRD first.** Requirement IDs, non-goals, and every
   `[NEEDS CLARIFICATION: ...]` tag.
2. **Stop on unresolved clarifications.** If a requirement carries one, do not file it.
   List those separately and say the PRD is not ready for that requirement. A ticket
   filed on a guess costs more than the one that was never filed.
3. **Check what already exists** before creating anything, by searching for the
   requirement ID:
   ```bash
   bd list --json | grep -o 'PRD-[A-Z]*-[0-9]*'      # or:
   gh issue list --search "PRD-FR-001" --state all --json number,title
   ```
   An ID that already has an issue is skipped and reported as skipped, never
   duplicated and never silently updated.
4. **Create one issue per remaining requirement.** Prefer `bd`, which records
   dependencies as a graph; fall back to `gh` when `bd` is unavailable:
   ```bash
   bd create "PRD-FR-001: <requirement title>" -d "$(cat body.md)" -p 2
   bd dep add <child-id> <parent-id>                  # child needs parent first
   ```
   ```bash
   gh issue create --title "PRD-FR-001: <requirement title>" --body-file body.md
   ```
   The body carries the requirement text verbatim, its Given/When/Then acceptance
   criteria, and a line naming the PRD file. Copy the acceptance criteria unchanged:
   rewording them is how a spec and its tickets drift apart.
5. **Record dependencies last**, once every issue exists and has an id. A dependency
   pointing at an issue that was skipped in step 3 is reported, not guessed around.
6. **Report.** Created, skipped-because-existing, and blocked-on-clarification, each
   with its requirement ID.

## Rules

- **The PRD is the only source.** Every issue traces to a requirement ID in it. If work
  seems obviously missing, say so in the report, but do not file it.
- **Never estimate, never prioritise beyond what the PRD states.** Priority comes from
  the PRD's own prioritisation if it has one, and is left at the tracker default if not.
- **Never close, reopen, merge, or edit an existing issue.** This skill only creates.
- **Idempotent by requirement ID.** Running it twice on the same PRD must create nothing
  the second time. This is the property that makes it safe to re-run after the PRD is
  revised, and it rests entirely on the ID being in the title.
- **Non-goals are not issues.** They are the boundary that stops the backlog growing
  past the spec.
- **Say what you did not file.** A silent skip is indistinguishable from work nobody
  noticed was missing.

## Boundaries

Stops at created issues. Sequencing the work inside one ticket is `project-planner`;
writing or revising the PRD is `product-prd`. Where a tracker syncs to GitHub itself
(`bd github sync`), let it, and do not create the same issue twice through two paths.
