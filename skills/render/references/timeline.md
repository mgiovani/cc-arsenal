# Mode: timeline

What happened, in order, and what it cost. Comments only: the reader is not
voting on the past, they are checking the record and adding what it missed.

## The page

- **At a glance**: the one-line answer (what happened and its impact), then
  four facts (window, duration, detection, impact), then the root cause and
  the resulting change as two callouts. A reader who stops here still knows
  what broke and what changed.
- **Timeline**: every dated event on a vertical rule, each one who acted, what
  they did, and where that is confirmed (a log, a transcript, a file). Order is
  the record; do not reorder for narrative effect.
- **Action items**: the follow-up work the incident produced, each one owned
  and marked open or done. A closed incident with no open actions says so
  plainly rather than omitting the section.

Anchor per event: `event-<date>-<slug>`. The date prefix, not an ordinal,
because two runs of the same investigation add events in between existing
ones, and a numbered anchor would reattach an old comment to whatever now
sits in that position. Anchor per action item: `action-<slug-of-its-title>`.
Label: the event's or item's own title.

## Verdicts

None. A timeline is a record, not a set of items the reader accepts or
rejects one by one; a wrong entry gets corrected by editing DATA, not by a
drop verdict. Comments carry every reaction: a question about an event, a
correction, a missing follow-up.

## Data

From a `fix-bug` investigation's own trail, from `git log` on a subsystem, or
from an incident retold after the fact. Keep the source's own timestamps and
its own wording for what happened; a paraphrased event is a different event
if the reader was there for the original.

Every event needs a who and a where-confirmed, not just a what. "Something
crashed" with no evidence is not a timeline entry, it is a guess with a
timestamp attached.

## Blocks

`tldr`, `facts`, `callout` (risk, decision), `timeline`, and an anchored
`row` for each action item. Not `checklist`: the shipped `.checklist > li`
row grid and `.anchored`'s own gutter grid both claim the same two columns.
Nesting an anchored mark inside a checklist row fights that layout. `row`
gets the same open or done tag and hairline-shared list, without the
conflict. See [assets/templates/timeline.html](../assets/templates/timeline.html)
for the full composition.

## Notes

- Group nothing. A timeline's whole point is that order carries the meaning;
  grouping events by actor or by type is a different page.
- Mark the events that only add color, a retry that changed nothing, a
  routine check, with `data-state="minor"` so the rule dims them without
  removing them. The reader should be able to skim the bold events alone and
  still get the story.
- A timeline that ends at detection and skips the fix is half a record. If
  the decision callout has nothing to say yet, the incident is not closed.
