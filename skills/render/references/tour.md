# Mode: tour

A guided walkthrough of one code path, told as a sequence of stops. No
verdicts, comments everywhere.

## The page

- **The answer in one line, first**: what the tour covers and where it ends,
  as `tldr`. A reader who stops here still knows the shape of the path.
- **The route**, as one `flow` overview: every stop in order, labelled with the
  function or file it lands on. The reader sees the whole trip before taking
  any step of it.
- **One section per stop**: a real code excerpt with numbered notes (`annot`),
  one line saying why that stop matters, and a link to the next stop. A stop
  with no code to show is not a stop; fold it into its neighbour.
- **The files visited**, as a `tree`, at the end. It is the tour's own table of
  contents in reverse: what got read, in the order it was read.

Anchor per stop: `stop-<path-slug>-<symbol>`, taken from the file and the
function or class the stop lands on, never from its position in the sequence.
A tour gets stops inserted or reordered on a second pass same as any other
page. Label: the stop's title.

## Verdicts

None. The reader is following a path, not deciding on it. Comments are
usually questions about one stop or a correction to what a stop claims.

## Blocks

`tldr`, `flow`, `annot`, `tree`. Template: `assets/templates/tour.html`.

## Data

From reading the actual source: `clotho-research`'s trace of a code path, an
`explain`-style question about how something works, or direct exploration.
Every code excerpt is copied from the file at the line numbers it cites,
never reconstructed from memory. Verify the call at each stop actually leads
to the next one; a tour that skips a step in the real call chain is worse
than a shorter, honest one.

## Notes

- Keep stops to the path that matters. A tour that visits every function a
  call passes through, including the ones that only forward an argument,
  buries the two or three stops that actually explain the behavior.
- The "why it matters" line is the payload. Code with a caption restating
  what it does teaches nothing; code with a caption saying what breaks
  without it does.
- End the last stop by saying so, not by trailing into the file tree. The
  reader should never wonder if they missed a stop.
