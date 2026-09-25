# Mode: plan

An implementation plan the reader can approve step by step before anything is
built.

## The page

- **Header**: what is being built, in one sentence taken from the plan itself,
  and the step count.
- **Critical path**: one diagram, when the steps have real dependencies. Drawn
  with `Render.diagram.dependency` from `steps[].deps`, left to right, with
  `critical: true` marking the chain that sets the plan's total; write that
  conclusion as `DATA.critical`, one sentence, and it becomes the diagram's
  title. Skip the diagram entirely when no step names a dependency, since a
  diagram of disconnected boxes carries nothing.
- **Per step**, one anchored block: what it does, which files it touches, what it
  depends on, and how it is verified. A step with no verification is shown with
  that gap visible, not hidden.
- **Open questions**: anything the plan could not settle, each anchored, each
  stating what changes depending on the answer.

Anchor per step: `step-<slug-of-its-title>`, never `step-<n>`. Steps get
inserted and reordered between revisions, and a numbered anchor silently
reattaches an old comment to whatever now sits in that position. Label: the
step's own title.

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

## Blocks

Template: `assets/templates/plan.html`. Composition, in reading order:

- `tldr` and `facts` (page-head plus At a glance): the plan's goal in one
  sentence and a handful of labelled values about the plan itself.
- `callout` (`data-kind="risk"`): the one risk the plan cannot absorb quietly.
- `diagram`, anchored: `Render.diagram.dependency`, one node per step and one
  edge per `deps` entry, `dir: 'LR'`, `critical: true`; an `.empty` state
  explains why the diagram is skipped when no step names a dependency, and a
  plan over the type's budget shows the builder's own refusal instead of a
  cramped graph.
- `steps`, each `<li class="anchored">` holding what the step does, the files
  it touches (`tree`, or a note when a step touches none), what it depends on,
  a verdict control, and either its verification or a visible `tag` saying the
  plan names none.
- `row` (Open questions), anchored: each question, what it is missing, and
  what changes once it is answered.
