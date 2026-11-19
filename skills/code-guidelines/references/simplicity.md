# Simplicity

## Contents

- [The ladder](#the-ladder)
- [Scope first, then shrink](#scope-first-then-shrink)
- [Functions and responsibilities](#functions-and-responsibilities)
- [Planning a feature](#planning-a-feature)
- [Things to leave out](#things-to-leave-out)
- [Limits and complexity caps](#limits-and-complexity-caps)

## The ladder

Walk these rungs in order and stop at the first one that fully works:

1. Check that the thing needs to exist at all.
2. Look for it in this codebase and use it the way the surrounding code does.
3. Look for it in the standard library or the platform.
4. Look for it in an installed dependency.
5. Write one line a reader grasps at a glance.
6. Write the minimum custom code.

Each rung blocks a kind of over-build that agents produce by default. A house component beats a native widget when one exists. Where none exists, take the native control: a modal is a `<dialog>`, a date field is `<input type="date">`.

## Scope first, then shrink

The smallest diff wins only after you know everything it must touch. Before editing, list the callers, tests, fixtures, config and exports that depend on what you change. Grep for every caller of a function before you modify it.

Cutting a caller, test or fixture to shrink the diff is a false win. A rename that misses one fixture is a scope bug.

For a vague request ("build me X"), ship the smallest version that does the core job. Do not offer a menu of variants. End with one line naming what you skipped and any risk the reader must know.

## Functions and responsibilities

One function, one responsibility. When a function validates, decides and persists, turn each step into a private function with its own name.

Split by job, never by line count. A helper that exists only to shorten its parent hides the structure. Merge near-copies only when they must change together. Code that merely looks alike stays separate.

Extract a shared helper after the same intent appears three times, not before. A premature abstraction costs more than the duplication it removes.

## Planning a feature

Draw the architecture before the code: the layers, the dependency direction and the pattern the problem calls for. Name each pattern and what it prevents.

Dependency inversion means the consumer declares a small port (a protocol or interface). An adapter implements it and is wired once at the composition root. The rule never instantiates the adapter itself.

A new variant of behaviour enters as a new implementation. Do not edit the code that consumes the abstraction.

## Things to leave out

- An interface with one implementation, a factory with one product, a wrapper that only forwards calls. The exception is a seam with a real second implementation, which can be a test double, or a boundary you must isolate.
- A config knob nothing sets. A documented constant is cheaper than a field with one caller.
- A module nobody uses yet. Extend an existing file first, and let each integration arrive with its first real use.
- Options, type conversions and wrappers nobody asked for. Keep values in the form the platform gives you.
- Defensive branches kept just in case. Remove dead code only after you grep the whole tree, tests, fixtures, config and dynamic references included, and put that proof in the commit message.
- Decorative extras in UI work, such as gradients, hover lift and shadows nobody requested.

## Limits and complexity caps

Where the project's lint sets caps on complexity, branches, statements or arguments, obey them and fix the code rather than the cap. Where it sets none, set none yourself.

Some projects switch these caps off on purpose, because collapsing a guard chain into fewer returns, or splitting a function to fit a statement budget, buries the structure the rule counts. Follow the project either way.

A function that takes more than about five parameters is a smell worth a parameter object. Treat that as a prompt to look, not a gate.
