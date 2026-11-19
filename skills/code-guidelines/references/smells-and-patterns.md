# Smells and patterns

## Contents

- [How to use this catalog](#how-to-use-this-catalog)
- [Gate for a design pattern](#gate-for-a-design-pattern)
- [Bloaters](#bloaters)
- [Conditionals](#conditionals)
- [Couplers and change preventers](#couplers-and-change-preventers)
- [Dispensables](#dispensables)
- [Patterns that fix visible pain](#patterns-that-fix-visible-pain)
- [Smells in agent-written code](#smells-in-agent-written-code)

## How to use this catalog

Name the smell by its catalog name, find the smallest refactoring that removes it, and apply a pattern only when the pain is visible in the code. The names and the refactorings follow the refactoring.guru catalog.

Run the existing tests before and after each refactoring step. A refactoring changes structure and never behaviour. To carry one out end to end, say "Using refactor to carry out the change" and use the `refactor` skill (via the Skill tool where available, otherwise apply its rules inline).

Thresholds below are prompts to look, not gates. The project's lint caps win over them.

## Gate for a design pattern

A pattern is the last resort, not decoration. Drop a suggested pattern when any of these is true:

- The smallest refactoring already removes the pain.
- Reuse, the standard library or the platform already covers it.
- There are fewer than three variants or call sites, unless the diff shows the next variant arriving.
- The fix adds more files, types or indirection than the pain it removes.
- The only argument is that you may need it later.

A trivial two-branch conditional never earns a pattern. If the pain is not in the tables below, name the smell and stop. Do not invent a pattern for it.

## Bloaters

| Smell | How to spot it | Smallest refactoring |
|---|---|---|
| Long function | It does several jobs, or has sections that need comments | Extract Method, split by job |
| Long parameter list | More than about five parameters | Introduce Parameter Object |
| Data clumps | The same few values travel together | Extract Class or a small value type |
| Primitive obsession | Strings or ints stand for domain concepts | Replace Primitive with Object, or an enum |
| Large class or god module | One file mixes responsibilities and changes for unrelated reasons | Extract Class |
| Magic numbers and repeated literals | The same literal appears in several places | Named constant |

## Conditionals

| Smell | How to spot it | Smallest refactoring |
|---|---|---|
| Nested conditions | Indentation deeper than about three levels | Guard clauses, early return |
| Else branch | A branch exists only to handle the other case | Return early, delete the `else` |
| Type-code switch or if ladder | A new case means editing the ladder | Map from key to handler, then polymorphism if behaviour differs |
| Flag arguments | A boolean parameter flips what the function does | Two functions with clear names |
| Repeated null checks | The same absence test sits in many callers | Null Object, or return a default once |
| Interacting booleans | `loading`, `failed` and `done` can disagree | One state value and one transition function |

## Couplers and change preventers

| Smell | How to spot it | Smallest refactoring |
|---|---|---|
| Feature envy | A method uses another object's data more than its own | Move Method |
| Message chains | `a.b().c().d()` reaches through objects | Hide Delegate |
| Middle man | A class only forwards calls | Remove Middle Man, inline it |
| Inappropriate intimacy | One module reaches into another's internals | Move Method, narrow the interface |
| Shotgun surgery | One logical change edits many files | Move the scattered parts together |
| Divergent change | One module changes for unrelated reasons | Extract Class |
| Parallel tables | Two maps or enums keyed the same way must change together | Fold into one table |
| Leaking SDK types | A vendor type shows up in domain or UI code | Adapter behind a small port |

## Dispensables

| Smell | How to spot it | Smallest refactoring |
|---|---|---|
| Duplicate code | Near-identical blocks of more than about five lines | Extract Method, but only if they must change together |
| Dead code | No live caller, after a whole-tree grep | Delete it |
| Speculative generality | A hook, flag or abstract class nobody varies | Inline or remove |
| One-implementation interface | One implementer, no test double, no boundary | Inline it |
| Lazy class | A class too small to justify itself | Inline Class |
| Comment as deodorant | A comment excuses unclear code | Rename or extract |
| Pass-through wrapper | The body forwards its own parameters unchanged | Delete it |
| Stub | The body is `pass`, `...` or a bare not-implemented throw | Implement it or remove the caller |

## Patterns that fix visible pain

| Visible pain | Pattern | Keep it small |
|---|---|---|
| A growing ladder by outcome, type or mode | Strategy or Command | One map entry per case |
| Status flags with impossible combinations | State, or a tagged union | One transition function |
| Vendor calls spread through the code | Adapter or Facade, with dependency inversion | The domain owns the port, one module wraps the SDK |
| Guards copied into each handler (auth, rate limit, validation) | Chain of Responsibility as ordered middleware | Each check passes or stops |
| Many callers walk several subsystems for one operation | Facade | One entry function |
| Many optional constructor arguments, order-dependent setup | Builder, or a parameter object with named fields | Validate in one place |
| Creation picked by scattered conditionals | Factory Method | Only with enough variants to earn it |
| One event hand-fanned to several consumers | Observer | Use the emitter the code already has |
| Logging, caching or retry copied at each call site | Decorator | Apply at composition |
| Repeated absence checks for a collaborator | Null Object | A no-op chosen once at construction |

When branches grow, the answer is one of these, not another `elif`. When a pattern is not needed yet, leave a guard clause and a dispatch map.

## Smells in agent-written code

Review agent output for these first, because they are the common failure modes:

- Reimplementing a helper the project already has (a hand-rolled slug, a hand-formatted currency).
- Hand-rolled standard-library work: a JSON round trip to deep-copy, `range(len(xs))` loops, a manual counting dict, a hand-built query-string parser.
- A guard added to the path the bug report names, while a sibling caller stays broken.
- Rebuilt native controls and wrappers that add a file and a hop with no behaviour.
- Type escapes (`Any`, `as any`, `cast` to quiet an error). Fix the type instead.
- Swallowed exceptions, and stub bodies left behind.
- Chat residue in source: a pasted preamble, a markdown fence line, "rest unchanged", unfilled placeholders.
- A closing summary that repeats the code.
