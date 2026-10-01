# Motion and springs

Read this when motion feels cheap, a value has several targets (cursor, container width, tab indicator), or a UI morph must loop.

## Why closed-form springs

A fixed easing curve reads as cheap; motion with weight speeds up, slightly overshoots and comes to rest. Use closed-form damped springs: they are a pure function of time, so `seek(t)` can jump straight to any late frame without stepping through the earlier ones. Never integrate a spring frame by frame.

A value that changes target several times must not restart its spring (the motion jumps). Sum one spring per target change, each starting at its own time. This keeps motion continuous and still seekable.

```js authored
// Unit step response of a damped spring (mass 1): 0 before `t <= 0`, settles at 1.
export function settle(t, stiffness = 170, damping = 26) {
  if (t <= 0) return 0;
  const w = Math.sqrt(stiffness);
  const zeta = damping / (2 * w);
  if (zeta < 1) { // underdamped: a little overshoot
    const wd = w * Math.sqrt(1 - zeta * zeta);
    const decay = Math.exp(-zeta * w * t);
    return 1 - decay * (Math.cos(wd * t) + (zeta / Math.sqrt(1 - zeta * zeta)) * Math.sin(wd * t));
  }
  if (zeta === 1) return 1 - Math.exp(-w * t) * (1 + w * t); // critical
  const r1 = -w * (zeta - Math.sqrt(zeta * zeta - 1)); // overdamped: two real roots
  const r2 = -w * (zeta + Math.sqrt(zeta * zeta - 1));
  return 1 - (r2 * Math.exp(r1 * t) - r1 * Math.exp(r2 * t)) / (r2 - r1);
}

// A value that is re-targeted over time. `changes` = [[atTime, newValue], ...], sorted.
// Each change adds its own spring from its own start time; nothing restarts,
// so any frame is computed directly from t.
export function retarget(t, changes, stiffness, damping) {
  return changes.reduce((v, [at, value], i) =>
    i === 0 ? value : v + (value - changes[i - 1][1]) * settle(t - at, stiffness, damping), 0);
}

// Stretchy tab indicator: the leading edge rides a stiffer spring than the trailing edge.
export function tabIndicator(t, stops, width) {
  const front = retarget(t, stops, 320, 30);
  const back = retarget(t, stops, 140, 22);
  return { x0: Math.min(front, back), x1: Math.max(front, back) + width };
}

const unit = (x) => (x < 0 ? 0 : x > 1 ? 1 : x);
// Label inside a morphing container: fade in shortly after the morph begins,
// fade out just before the next morph.
export const labelOpacity = (t, morphIn, nextMorph) =>
  Math.min(unit((t - morphIn - 0.08) / 0.12), unit((nextMorph - 0.1 - t) / 0.1));

// Seamless loops: wrap time so the last frame lands back on frame 0.
export const wrap = (t, length) => t - Math.floor(t / length) * length;
```

Starting stiffness (k, damping d): default `170, 26` (cards, containers, camera); snappy `320, 30` (buttons, toggles, leading edges); soft `140, 22` (trailing edges); titles `220, 22`; staggered grids `260, 20`. Heavy for big type, 3D objects and logo lockups (lower k); playful with visible overshoot only for mascots and stickers.

## Rules

- Swap easing curves for springs: UI elements may overshoot slightly, type should not overshoot at all. Any value with more than one target uses `retarget()`.
- Tab indicators stretch because leading and trailing edges sit on different springs, the leading edge stiffer.
- Looping film: the last frame equals the first, including cursor position and velocity. Map time with `wrap`, end the last state at the first state's pose, and check the seam by playing the file twice back to back.
- One-shape UI morph: a single container changes size, radius and fill from state to state; content swaps behind a short blur (blur the content, not the container); a cursor drives each change with real clicks and drags.
- Overshoot applies to transforms only. A counter must never fly past its value and fall back; a figure that was never true is a lie.
- Perfectly synchronized follow-through is just a bigger object: resolve shadows, trailing panels and housings a beat after the main body.
- Mix easing by direction: entrances ease out, exits ease in, on-screen moves ease in-out, impacts (a slam, a stamp) ease in.

## What makes motion read as designed

- Every movement makes a claim. Name what each one says in a sentence that ends ("the counter breathes because data is still arriving"); if you cannot finish it, cut the movement. A dead shot needs one genuinely changing thing, not more wobble.
- Nothing ever fully stops: a hold carries 1 to 2 percent breathing, a slow drift, a shimmer. A frozen final second is the cheapest tell (consecutive frames bit-identical).
- The camera is an actor: one continuous move per scene, a 4 to 8 percent push-in, orbit or parallax (near layers travel further). Never let it ease to a dead stop. For a through-line film use dwell-and-sweep: the camera rests 1.5 to 2.5 s at each hero moment while counters keep ticking.
- Overlap action: no two elements share a start or end; stagger at irregular offsets clearly shorter than the animation they offset (an offset longer than the animation becomes a queue). Delay supporting elements, never the focal one; stagger what happens, not what already exists.
- Compound properties only when they tell one story (slide plus fade yes; rise plus rotate plus scale plus blur no).
- Depth planes: far layer at about a fifth of the camera rate, content at full rate, foreground several times. Occlusion (one large blurred foreground element crossing the content) sells depth better than blur alone. Use one such element, not two.
- Pace to genre: showreel ideas run 1.5 to 4 s each and cut hard; something new on screen every 2 to 4 s.
- Avoid the slideshow: let something cross every seam (shared element, space or motion vector) and vary energy so a hero moment has quiet to land against.
- Handmade feel without `Math.random`: seed a PRNG once, step on holds quantized to the integer frame index (a two-frame hold), not to elapsed seconds, which drift.
- Motion blur only on beats that snap (slam, whip, spin, scale punch), one to three per film; never on text meant to be read at that moment (blur the approach, land sharp, hold). Canvas routes get blur from subframe blending (`render-engine.md`).
