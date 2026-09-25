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
  summary: "Turn an approved PRD into tracked issues, one per requirement ID, with dependencies recorded"
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

| Output | Description |
|--------|--------------|
| One issue per requirement ID | `PRD-FR-001` becomes exactly one issue, with the ID in the title. That ID is the only link back to the spec, and it's what lets a re-run recognize its own earlier output. |
| Dependencies between issues | Taken from the PRD's own ordering and its stated prerequisites, never invented. |
| A report | What was created, what was skipped, and what blocked. |

## Method

1. Read the whole PRD first, noting requirement IDs, non-goals, and every
   `[NEEDS CLARIFICATION: ...]` tag.
2. An unresolved clarification on a requirement means it doesn't get filed. List those
   separately and say the PRD isn't ready for that requirement yet; a ticket filed on a
   guess costs more than the one that was never filed.
3. Before creating anything, check what already exists by searching for the
   requirement ID:
   ```bash
   bd list --json | grep -o 'PRD-[A-Z]*-[0-9]*'      # or:
   gh issue list --search "PRD-FR-001" --state all --json number,title
   ```
   Skip an ID that already has an issue and report it as skipped. Never duplicate it,
   never update it silently.
4. Create one issue per remaining requirement. Prefer `bd`, which records dependencies
   as a graph, and fall back to `gh` when `bd` isn't available:
   ```bash
   bd create "PRD-FR-001: <requirement title>" -d "$(cat body.md)" -p 2
   bd dep add <child-id> <parent-id>                  # child needs parent first
   ```
   ```bash
   gh issue create --title "PRD-FR-001: <requirement title>" --body-file body.md
   ```
   Carry the requirement text verbatim in the body, along with its Given/When/Then
   acceptance criteria and a line naming the PRD file. Copying the acceptance criteria
   unchanged matters, since rewording them is how a spec and its tickets drift apart.
5. Once every issue exists and has an id, record dependencies. If one points at an
   issue that was skipped in step 3, report that rather than guessing around it.
6. Close with a report, tagging each requirement ID as created, skipped because it
   already existed, or blocked on a clarification.

## Rules

| Rule | Why |
|------|-----|
| The PRD is the only source | Every issue traces to a requirement ID in it. If work looks obviously missing, say so in the report, but don't file it. |
| Never estimate or prioritize beyond the PRD | Priority follows the PRD's own prioritization when it has one, and falls back to the tracker default otherwise. |
| Never close, reopen, merge, or edit an existing issue | This skill only creates. |
| Idempotent by requirement ID | Running it twice on the same PRD must create nothing the second time. That's what makes a re-run safe after the PRD is revised, and it rests entirely on the ID being in the title. |
| Non-goals are not issues | They're the boundary that keeps the backlog from growing past the spec. |
| Say what you did not file | A silent skip is indistinguishable from work nobody noticed was missing. |

## Boundaries

Stops at created issues. Sequencing the work inside one ticket is `project-planner`;
writing or revising the PRD is `product-prd`. Where a tracker syncs to GitHub itself
(`bd github sync`), let it, and do not create the same issue twice through two paths.
