# React Performance

## Contents

- [Measure first](#measure-first)
- [Memoization](#memoization)
- [Render rules](#render-rules)
- [Waterfalls and bundles](#waterfalls-and-bundles)
- [Lists, images and fonts](#lists-images-and-fonts)
- [Effects, listeners and timers](#effects-listeners-and-timers)

## Measure first

Start from the real bottleneck (LCP, INP, CLS, long tasks, bundle size), change one thing, and measure again. Targets: LCP under 2.5s, INP under 200ms, CLS under 0.1. Test on a throttled connection and a mid-range phone as well as a fast laptop.

Tailwind and plain CSS carry no runtime cost. The one trap is a dynamically built class name that never reaches the build.

## Memoization

Check the build config for the React Compiler before you touch `useMemo`, `useCallback` or `memo`.

- With the compiler on, add none of them for speed. A manual memo needs a stated reason, such as an external consumer that relies on identity. Review treats an unjustified one as a blocking comment.
- Opt a component out with `"use no memo"` only with a comment linking the upstream incompatibility.
- Without the compiler, memoize only after a profile shows the win. Do not wrap a short boolean or number expression in `useMemo`, since the comparison can cost more than the work.
- Hoisting static JSX and regex literals to module scope is cheap and stays worth doing in either case.

## Render rules

- Compute anything derivable from props or state during render. State copied from props and synced by an effect costs an extra render and can drift.
- Run work caused by a user action in the event handler, not in an effect watching state that the handler set.
- Use `setX(curr => ...)` when the next value depends on the previous one.
- Pass a function to `useState` when the initial value is costly. Keep the initial value of a primitive plain.
- Depend on primitives in effect dependency lists (`user.id`, not `user`). Subscribe to a derived boolean (past a threshold) instead of a value that changes every frame.
- Read live state used only in a handler on demand, so the component stops re-rendering on every change.
- Keep per-frame values such as pointer position in a ref and write the DOM node directly. A `setState` per mousemove re-renders on every event.
- Use stable ids as keys, never the array index for a list that can reorder.
- Render conditions with a ternary. `count && badge` prints a visible `0`.
- Copy before sorting with `toSorted`. `sort()` mutates props or state.
- Use `startTransition` or `useDeferredValue` for non-urgent updates such as filtering, and debounce search input at about 300ms.
- Keep an expensive, often-toggled subtree alive with `Activity` instead of unmounting it.

## Waterfalls and bundles

- Start independent async work together with `Promise.all`, or start early and await late. Move an `await` into the branch that needs its result.
- Wrap only the component that waits on data in `Suspense` with a skeleton of its final shape, so the shell paints at once. Skip it when layout depends on the data.
- Split by route and lazy-load heavy components that are not needed for first paint, such as an editor or a graph library. Preload the chunk on hover or focus of its trigger.
- Import from the file that defines a symbol. A barrel file of a large library (icons, UI kits, date utilities) loads thousands of modules.
- Load analytics and other third-party scripts after the app is interactive, and put `defer` or `async` on script tags.

## Lists, images and fonts

- Use `content-visibility: auto` with a `contain-intrinsic-size` placeholder for long lists, and virtualize when the list grows past what that handles. Paginate or filter large sets instead of loading thousands of rows.
- Give every image width and height or an `aspect-ratio`. Lazy-load below-the-fold images only, never the hero, and serve about twice the displayed width.
- Use `font-display: swap` or `optional`, preload only the critical face, load only the weights in use, and set a metric-matched fallback.
- Animate only `transform` and `opacity`, and set `will-change` only on an element while it animates. See the motion reference.

## Effects, listeners and timers

- Return a cleanup from every effect that adds a listener, timer, observer or subscription. An unmounted component must stop working.
- Observe a sentinel with `IntersectionObserver` instead of a scroll listener.
- Mark listeners that only observe `touchstart` or `wheel` as `{ passive: true }`.
- Hold one global listener for app-wide shortcuts instead of one per hook instance.
- Batch layout reads before writes. Interleaving them forces a reflow each time.
- Defer non-urgent work such as analytics with `requestIdleCallback`, and never defer anything the user is waiting on.
- Abort in-flight requests on unmount or navigation, so a slow response cannot overwrite a newer one.
