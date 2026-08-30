# Mode: map

The shape of a codebase or a system. No verdicts, comments everywhere.

## The page

- **Entry points**, first. Where execution actually starts: the binaries, the
  routes, the scheduled jobs, the message handlers. A reader orienting in an
  unfamiliar repo needs these before anything else.
- **The module graph**, as one diagram. Nodes are things that exist on disk;
  edges are imports or calls that were verified, never inferred from similar
  names.
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
