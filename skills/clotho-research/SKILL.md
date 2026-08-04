---
name: clotho-research
description: Find what a change will actually touch before planning it — the existing
  code that must change, the prior art worth copying, and the risks that will bite.
  Trigger on "what would this change touch", "research this before we plan it", or an
  automated pre-planning step. Reports files, sources, and risks; it never proposes an
  implementation and never edits anything. Not for auditing dependencies (use
  review-deps), not for writing the plan itself (use project-planner), and not for
  reviewing code that already exists (use review-code).
metadata:
  author: mgiovani
  version: 1.0.0
disable-model-invocation: true
argument-hint: "<spec file | spec JSON>"
allowed-tools: Read, Grep, Find, Ls
---

# Clotho Research

The step between "we know what we want" and "we know how to build it". Its only job
is to make the next step's plan concrete instead of speculative.

## What you produce

Three lists, nothing else:

- **touched_files** — files that will have to change, and the ones that will not
  change but constrain the design (a schema, an interface, a caller).
- **prior_art** — how this is already solved, in this repo first and the wider world
  second. In-repo findings are cited `path:line` from a Read or Grep you actually ran.
  External sources come from memory, not retrieval, so each one is suffixed
  `(unverified — recalled, not fetched)`.
- **risks** — what will make this harder than it looks.

Do not propose an implementation. Do not write a plan. The planner does that, and it
does it better with facts than with someone else's half-formed design.

## Method

**The repository is the only thing you can actually check.** The most valuable finding
is almost always "we already do this three files over" — it turns a feature into a
refactor. It is also the one kind of finding you can prove, by reading the file and
quoting the line.

1. **Find the seam.** Where does this change enter the system? Grep for the nouns in
   the spec, then follow the callers. Name the specific functions, not just files.
2. **Find the pattern.** Has this repo solved something structurally similar? Copy
   its shape — matching an existing convention is worth more than a marginally better
   design nobody else in the codebase uses.
3. **Find every caller.** If the change touches a shared function, list who depends
   on it. A change that fixes one call site and breaks four is the most common way
   this phase fails.
4. **Then fall back to memory, and label it.** This session has no retrieval tool of
   any kind — only Read, Grep, Find, Ls, all repo-local. For what the repo could not
   answer (an unfamiliar API's shape, a known failure mode, a version-specific
   gotcha) you are recalling, not looking up, and your recall has a training cutoff
   and no way to notice a breaking change since. Report it anyway — a labelled lead
   beats silence — but suffix every one `(unverified — recalled, not fetched)` so the
   planner knows to confirm it before betting a step on it.
5. **Name the risks concretely.** "Might be tricky" is not a risk. "This function is
   called from a migration that runs before the config loader, so it cannot depend on
   settings" is.

## Rules

- **Read-only.** Never edit, never create files.
- **Cite what you found, and say how you know it.** In-repo: a file path with a line
  number you actually read. Anything else: the reference plus
  `(unverified — recalled, not fetched)`. An unattributed claim cannot be checked and
  will be treated as a guess by everyone downstream; an unlabelled recalled one is
  worse, because it will be treated as checked.
- **Say when you did not find something.** "No existing pattern for this" is a real,
  useful finding — it tells the planner it is designing rather than following. Do not
  fill the gap with a plausible-sounding invention.
- **Do not confuse recall with truth.** If something you remember contradicts the code
  in front of you, the code wins — you can read the code and you cannot re-read your
  memory. Note the discrepancy as a risk.
