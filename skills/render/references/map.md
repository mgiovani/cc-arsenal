# Mode: map

The shape of a codebase or a system. No verdicts, comments everywhere.

## The page

- **Entry points**, first. Where execution actually starts: the binaries, the
  routes, the scheduled jobs, the message handlers. A reader orienting in an
  unfamiliar repo needs these before anything else.
- **The module graph**, as one diagram. Nodes are things that exist on disk;
  edges are imports or calls that were verified, never inferred from similar
  names. Drawn with `Render.diagram.dependency`, or `Render.diagram.architecture`
  when the nodes group into zones (layers, services, trust boundaries); pass
  `nodes`/`edges` with ids and labels only, never coordinates, and let the
  diagram engine lay it out.
- **A data path**, traced end to end for the system's most important operation.
  One concrete trace teaches more than a complete graph, because it shows the
  order things happen in.
- **Per module**, one anchored block: what it owns, what it depends on, and its
  path in the repo.
- **Boundaries**: where a trust, process or network boundary is crossed, marked
  on the diagram. These are where the bugs and the security questions live.

Anchor per module: `module-<path-slug>`. Per diagram: `diagram-<slug>`.

## Verdicts

None. Comments only, usually corrections from someone who knows the system.

## Data

From `docs-diagram`, `clotho-research`, or direct exploration.

Verify before drawing. Read the file that defines a component before it becomes a
node. Confirm each edge by finding the import or call. Get counts by running a
command and use that number. Drop anything that cannot be confirmed: an empty
directory and an unused stub are not components, and a plausible edge that does
not exist is the most damaging thing this page can contain.

## Notes

- Split rather than cram. Four readable views beat one diagram with fifty nodes.
- Say what is out of scope. A map of the API layer that silently omits the worker
  tier reads as complete and is not.
- Note the commit the map was built from. It goes stale, and the reader needs to
  know how stale.

## Blocks

`wrap-wide` plus `toc`, no toolbar filterbar (map has no verdicts and no facet
filters). Composition, in page order:

| Block | Holds |
|---|---|
| `tree` | Entry points and key files: the binaries, CLI commands and modules a reader needs before anything else, grouped by directory |
| `diagram` | The module graph: `Render.diagram.dependency` (flat) or `.architecture` (zoned), nodes that exist on disk, edges confirmed by reading the import or call, never inferred from similar names. Over the type's node/edge budget, split into more than one diagram rather than fight the refusal |
| `flow` | The data path: one operation traced end to end, one pipeline stage per function, in the order it actually runs |
| `table` | One row per module: what it owns, what it depends on, and the command or route that enters it. The module cell is anchored (`module-<path-slug>`) |
| `layers` | The architecture as stacked levels, top level first |

A `callout` (kind `note`) states what the map leaves out and whether it crosses
a trust, process or network boundary. Every diagram is anchored
(`diagram-<slug>`); entry points and layers are not, per blocks.md's anchored
block contract. Template: `assets/templates/map.html`.
