# Mode: plan

An implementation plan the reader can approve step by step before anything is
built.

## The page

- **Header**: what is being built, in one sentence taken from the plan itself,
  and the step count.
- **Critical path**: one diagram, when the steps have real dependencies. The
  point it must make is which chain sets the total, so weight that chain and let
  the parallel branches recede. Skip the diagram entirely when the plan is a flat
  sequence, since an arrow between every consecutive pair carries nothing.
- **Per step**, one anchored block: what it does, which files it touches, what it
  depends on, and how it is verified. A step with no verification is shown with
  that gap visible, not hidden.
- **Open questions**: anything the plan could not settle, each anchored, each
  stating what changes depending on the answer.

Anchor per step: `step-<n>`. Label: the step's own title.

## Verdicts

`approve`, `rework` (the comment says what is wrong), `cut` (do not do this).

## Data

From `project-planner`, `implement-feature`, `orchestrate`, or a plan file being
converted. Keep the plan's own ordering and its own words for what each step
does.

Name real files. A step that says "update the relevant modules" is a step nobody
can approve, so surface that vagueness rather than inventing paths to fill the
field.

## Notes

- Dependencies come from the plan. Do not infer them from step order: adjacent
  steps are frequently independent, and a fabricated edge changes what the
  critical path diagram claims.
- When a step is cut, note which later steps depended on it. That consequence is
  the reader's next decision and they should not have to trace it themselves.
