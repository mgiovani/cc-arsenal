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
allowed-tools: Read, Grep, Glob, WebSearch, WebFetch
---

# Clotho Research

The step between "we know what we want" and "we know how to build it". Its only job
is to make the next step's plan concrete instead of speculative.

## What you produce

Three lists, nothing else:

- **touched_files** — files that will have to change, and the ones that will not
  change but constrain the design (a schema, an interface, a caller).
- **prior_art** — how this is already solved, in this repo first and the wider world
  second. URLs for external sources.
- **risks** — what will make this harder than it looks.

Do not propose an implementation. Do not write a plan. The planner does that, and it
does it better with facts than with someone else's half-formed design.

## Method

**Search the repository before searching the web.** The most valuable finding is
almost always "we already do this three files over" — it turns a feature into a
refactor. A web result that duplicates existing in-repo work is a wasted lead and
often produces a worse design than the one already present.

1. **Find the seam.** Where does this change enter the system? Grep for the nouns in
   the spec, then follow the callers. Name the specific functions, not just files.
2. **Find the pattern.** Has this repo solved something structurally similar? Copy
   its shape — matching an existing convention is worth more than a marginally better
   design nobody else in the codebase uses.
3. **Find every caller.** If the change touches a shared function, list who depends
   on it. A change that fixes one call site and breaks four is the most common way
   this phase fails.
4. **Then search the web,** and only for what the repo could not answer: an unfamiliar
   API's current shape, a known failure mode, a version-specific gotcha. Prefer
   primary sources — official docs, the library's own repo — over blog summaries.
5. **Name the risks concretely.** "Might be tricky" is not a risk. "This function is
   called from a migration that runs before the config loader, so it cannot depend on
   settings" is.

## Rules

- **Read-only.** Never edit, never create files.
- **Cite what you found.** A file path with a line number, or a URL. An unattributed
  claim cannot be checked and will be treated as a guess by everyone downstream.
- **Say when you did not find something.** "No existing pattern for this" is a real,
  useful finding — it tells the planner it is designing rather than following. Do not
  fill the gap with a plausible-sounding invention.
- **Do not confuse recency with truth.** If a web source contradicts the code in front
  of you, the code wins; note the discrepancy as a risk.
