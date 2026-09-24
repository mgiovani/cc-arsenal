# Mode: brainstorm

Ideas laid out so they can be compared, combined and cut.

## The page

- **The tension**, stated at the top: what problem or constraint the ideas are
  answering. Ideas float free without it, and every one looks equally good.
- **Idea cards**, grouped by theme, each anchored. A card carries the idea in one
  line, what it would take, and specifically what tension it resolves. A card
  that resolves nothing is a card to cut.
- **Combinations**: a place to pair two ideas, since the useful output of a
  brainstorm is often a hybrid rather than a winner.
- **Impact vs. effort**, optional. Score an idea's `impact` and `effortScore`
  (1 to 5 each) and, once at least two ideas carry both, a `Render.diagram.quadrant`
  plots them; below that it stays an `.empty` state rather than a plot with one dot.
- **What was ruled out**, with the reason, kept visible. It stops the same idea
  returning next session, and it is the part most often thrown away.

Anchor per idea: `idea-<slug>`. Label: the idea's one-liner.

## Verdicts

`shortlist`, `park`, `drop`.

## Data

From a discussion, a research pass, or an existing notes file. Ideas keep the
wording they were proposed in.

Do not filter before rendering. A brainstorm page's value is showing the reader
the range, including the ideas that will obviously lose, because the losing ones
are what make the shortlist look deliberate.

## Notes

- Group by theme, not by quality. Ranking is what the reader is there to do.
- Six to fifteen ideas. Below six the page is a list; above fifteen nobody
  reads to the bottom, so split by theme into sections instead of pruning.
- Where two ideas are the same idea, merge them and note it. Duplicate cards make
  a theme look better supported than it is.

## Blocks

Template: [assets/templates/brainstorm.html](../assets/templates/brainstorm.html).

- `tldr`: the tension, the one question every idea below answers.
- `idea`, grouped into one `.ideas` grid per theme section: the idea in one
  line, the tension it resolves, its theme, and cost and effort as tags, with
  the `shortlist` / `park` / `drop` verdict control.
- `diagram`, anchored, optional: a `quadrant` plotting every scored idea by
  impact and effort, once two or more carry a score.
- `tally`: idea counts by verdict, shortlist through drop through undecided.
- `callout` (`data-kind="note"`): the hard constraint every idea has to fit,
  such as an existing gate or convention the repo already runs.
