# Mode: explain

Understanding, built in layers. No verdicts, comments everywhere.

## The page

- **The answer in one line**, first, before any context. A reader who stops here
  should still have what they asked for.
- **The mechanism**, usually one diagram, showing how the thing actually works.
  This is the layer that justifies a page over a paragraph, so if there is no
  shape worth drawing, say so and write prose instead of building a page.
- **The detail**, in sections the reader opens as needed. Each section answers
  one question and says which question in its heading.
- **What this does not cover**, at the end. The boundary of an explanation is
  part of it, and leaving it off is how a reader over-applies what they learned.

Anchor per section: `section-<slug>`. Anchor the diagram and any worked example
separately, since those attract the most questions.

## Verdicts

None. The reader is learning, not deciding. Comments are the whole feedback
surface, and they are usually questions rather than corrections, so the composer
placeholder says so.

## Data

From research done for the occasion, from `clotho-research`, or from the
codebase. Every claim about how something works must be verified against the
thing itself, not recalled. Cite the file, the doc or the source for anything
load-bearing.

Where the answer is genuinely uncertain, the page says so at that point in the
explanation. Confident prose over a shaky fact is the failure mode this mode is
most prone to.

## Notes

- Layer by depth, not by chronology. A history of how something came to work
  this way is a different page and rarely the one that was asked for.
- One worked example beats three abstractions. Use a real one from the project
  where the subject is the project's own code.
