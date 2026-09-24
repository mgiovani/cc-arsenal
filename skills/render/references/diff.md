# Mode: diff

A hunk-by-hunk review of a change: what moved, in which files, shown as real
diffs instead of a description of them.

## The page

- **Header**: what changed and why, in one sentence taken from the change
  itself, plus the base it is diffed against.
- **At a glance** opens with the tldr, then the file and line counts and the
  added-versus-removed balance, before any code.
- **Touched files**: one tree, add, modify and delete marked, so the reader
  sees the shape of the change before its content.
- **Per file**, one section holding its hunks: each hunk is a diff block,
  unified by default, switched to the split variant for a config or prose
  change where the reader needs the whole before and the whole after side by
  side rather than interleaved plus and minus lines. A file with no hunk shown
  still gets its section, with an empty state naming it.

Anchor per hunk: `hunk-<path-slug>-<hunk-label-slug>`. The label comes from
the hunk's own content, for instance the function or table it touches, never
from its position in the file: two hunks in the same file need two different
labels or they will share a verdict and every comment. Label: `<path>: <hunk
label>`.

## Blocks

- `tldr`: the change and why, first, before any diff.
- `facts`: base, files changed, total lines, the largest file.
- `tally`: added versus removed lines, as one bar.
- `tree`: every touched file, add, modify and delete marked.
- `diff`: one per hunk, unified by default; split for a hunk whose point is
  prose or config shape rather than line-by-line code.

## Verdicts

`accept`, `revise` (the comment says what to change), `reject` (drop this
hunk).

## Data

From `refactor`, `db-migrate`, or any pull request diff. A bare `render diff`
on an unstaged or committed change runs `git diff`, or the migration tool's
own diff, first, and renders what it produced.

Keep the hunk's real line numbers and real text. Trim a large file to the
hunks that carry the point rather than showing the whole file; a file that
changed but earns no excerpt still gets a section, with an empty state saying
so.

## Notes

- A file with no hunk is not a smaller version of the block; it is the
  block's empty state, because the reader still needs to see that the file
  was touched.
- Group by file, not by hunk type. A reader accepting a whole file's worth of
  change should not have to hunt across the page for its second hunk.
- Do not invent a before or after for a hunk the source diff did not show. If
  a file's own diff is too large to excerpt meaningfully, say so in the
  section instead of truncating it silently.
