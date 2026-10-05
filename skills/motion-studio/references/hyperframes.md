# HyperFrames: HTML plus GSAP, authored by agents

Read this when the user wants a framework instead of the zero-dependency canvas route, thinks in web pages, needs captions, voiceover, templates or Studio editing, or says "HyperFrames" or "/hyperframes". Opus skips frameworks unless told, so say so explicitly. For the Remotion comparison and port see `remotion.md`.

## Contents

- [Install the agent skills (ask the user first)](#install-the-agent-skills-ask-the-user-first)
- [Router (input to workflow)](#router-input-to-workflow)
- [Minimal composition](#minimal-composition)
- [Determinism rules](#determinism-rules)
- [Prompting HyperFrames](#prompting-hyperframes)
- [Verify and render](#verify-and-render)

HyperFrames (Apache 2.0, no React, no build step) renders video from HTML. A composition is an HTML file whose DOM declares timing with `data-*` attributes, whose animation runtime is seekable (GSAP by default; CSS, Anime.js, Lottie, Three.js and Web Animations are also seeked), and whose media playback the framework owns. The renderer asks the project for each exact frame, so a slow machine drops nothing.

## Install the agent skills (ask the user first)

Requires Node.js (`fnm install --lts` or `brew install node`).

```bash
npx skills add heygen-com/hyperframes
```

Pick **Core Skills**; the `/hyperframes` router installs a specialized workflow when a request needs one. Start a fresh agent chat after installing, then ask it to use `/hyperframes`. Non-interactive or CI refresh:

```bash
npx hyperframes skills update
```

`npx hyperframes skills check` reports stale or missing skills without changing anything; `npx hyperframes skills update <workflow-name>` installs one workflow; `npx skills add heygen-com/hyperframes --all` installs everything. If the agent cannot see a skill: new session, confirm the skill directory belongs to that agent, run `check`, then `update`. A first request that works:

```text
Using /hyperframes, make a 10-second product intro for https://example.com.
```

Without the slash command the agent guesses at HTML video conventions instead of loading the rules.

## Router (input to workflow)

Product site or brief: product-launch-video. Topic, notes or script with no site: faceless-explainer. GitHub PR: pr-to-video. Music track whose beat grid drives the piece: music-to-video (music used only as a bed does not select it). Short unnarrated design-led unit, typically under 10 s: motion-graphics. Existing talking-head footage: embedded-captions (plain captions) or talking-head-recut (designed cards). Presentation: slideshow (present it with `npx hyperframes present <dir>`; never `render` a deck). Figma file: figma import; Remotion port: remotion-to-hyperframes; anything else: general-video. Narrative workflows are strongest at 30 to 90 s and support about 3 minutes. Do not override a workflow's designed style; use a freeform build for full style control.

Project layout: `BRIEF.md`, `STORYBOARD.md`, `SCRIPT.md`, `frame.md` (visual direction), `index.html`, `hyperframes.json`, `compositions/`, `assets/`, `renders/`.

## Minimal composition

```html
<style>
  #stage { position: relative; width: 1280px; height: 720px; overflow: hidden; background: #0a0a0a; }
  .clip  { position: absolute; inset: 0; display: grid; place-items: center; }
  #title { font-size: 160px; font-weight: 800; color: #fff; opacity: 0; }
</style>

<div id="stage" data-composition-id="title-card" data-start="0"
     data-width="1280" data-height="720" data-duration="3" data-fps="30">
  <div id="card" class="clip" data-start="0" data-duration="3" data-track-index="0">
    <div id="title">HELLO</div>
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<script>
  // same fade, written in seconds instead of frames
  const tl = gsap.timeline({ paused: true });
  tl.to("#title", { opacity: 1, duration: 0.5, ease: "none" }, 0);
  tl.to("#title", { opacity: 1, duration: 2.0, ease: "none" }, 0.5);
  tl.to("#title", { opacity: 0, duration: 0.5, ease: "none" }, 2.5);

  window.__timelines = window.__timelines || {};
  window.__timelines["title-card"] = tl;
</script>
```

Three rules make it render: every visible slot is `class="clip"` with an id, `data-start`, `data-duration` and `data-track-index`; the timeline is created paused; it is registered on `window.__timelines` under the root's `data-composition-id` (miss that and you get a still frame). Tracks are not layers; use CSS `z-index` for paint order. `data-start` can reference another clip (`intro - 0.5`). Nested compositions use `data-composition-src`; per-instance values use `data-variable-values`.

## Determinism rules

- Register every timeline; build it synchronously. If built in an async callback (`document.fonts.ready`), assign `window.__timelines[id] = tl` at the end, after the tweens exist, never before.
- No `Date.now()`, `performance.now()`, unseeded `Math.random()` (use a seeded PRNG such as mulberry32; quantize stop-motion holds on the integer frame index), render-time fetches, hover/scroll/focus state, `repeat: -1` (use `Math.max(0, Math.floor(duration / cycleDuration) - 1)`, floor not ceil), `tl.play()`, empty tweens used only to set duration (use `data-duration`).
- `<video>` must be `muted`; audio goes in separate `<audio>` elements. Do not tween `display`, `visibility` or `autoAlpha` on a clip element; fade a child. Do not animate `width/height/top/left` directly on a `<video>`. Iframes do not seek; they render frozen or blank.
- Cold-seek safety (a parallel render worker seeks non-linearly): state the visible end state of anything that starts hidden (`opacity: 1` in the destination vars). Also: hide initial state with CSS or a bare `gsap.set` outside the timeline, remember `fromTo` shows its from-state before it starts (use `to()` plus `keyframes` or a zero-duration `tl.set()` when absent before its cue). Also avoid: relative `+=` tweens on a property another tween writes, DOM measuring (`getBoundingClientRect`) inside timeline callbacks, function-valued vars that call methods on the first argument.
- Layout: fixed-pixel root (do not hardcode 1920/1080 on `#root` when using sizing from the framework), build the end state in static HTML/CSS first and animate from/to it, use flex/grid not hardcoded offsets, no `<br>` in body text, transformed elements must be block-level and sized, leave clearance for overshoot at peak size. Do not centre with `transform: translate(-50%, -50%)` on something GSAP moves (use `xPercent`/`yPercent`).
- Two properties animated on one element by different tweens fight; combine into one tween. Every image gets a motion treatment; add entrance animations to every scene and transitions between scenes.

## Prompting HyperFrames

Skeleton, one line per decision:

```text
[route]      /motion-graphics
[spec]       8-second 1920x1080 video.
[beats]      Beat 1 (0-4s): ...  Beat 2 (4-5s): ...  Beat 3 (5-8s): ...
[copy]       the exact on-screen text, quoted
[technique]  Adapt the `code-typing` and `vfx-shatter` registry blocks.
[negatives]  No narration, no image or media files.
```

Default spec is 1920x1080 at 30 fps; do not over-spec (4K or 60 fps slows renders). Copy is quoted exactly. Name registry blocks exactly as in the catalog; they are adapted starting points, so naming one pins the technique. "No narration" is not "silent"; say "no audio" for none. Pin 3D with "Three.js via the adapter" (CSS perspective reads flat on lighting-critical scenes). Describe a storyboard as a plan (arc, per-frame beats, pacing rule), not scene by scene. Mood words get a designer's interpretation; hexes, timestamps and named techniques get yours. Point at a spec (`frame.md`, a site, a Figma frame) instead of "on-brand". Use paths (`assets/logo.svg`), not "my logo". Tell it about transitions by mood ("warm", "dramatic zoom", "cold, clinical"). If a scene keeps misfiring, strip it to the simplest version, confirm, then add one layer at a time; use absolute targets ("dots 6 px") not "2x finer".

## Verify and render

```bash
npx hyperframes lint
npx hyperframes check
npx hyperframes snapshot . --at <times>
```

```bash
npx hyperframes render --quality draft --output review.mp4
npx hyperframes render --quality high --output master.mp4
npx hyperframes render --fps 60 --output final-60fps.mp4
npx hyperframes render --resolution 4k --output final-4k.mp4
npx hyperframes render --docker --output output.mp4
```

Other formats: `--format webm` (transparent overlay), `--format mov` (ProRes master), `--format gif --fps 15`, `--format png-sequence`, `--format hls`. Use `--docker` to rule the machine out as a variable; parallel workers are not bit-identical to each other (a few plus-or-minus 1 pixel level differences). HDR output only when the composition references HDR media. Reuse a design with `hyperframes render --variables '{"ground":"#0d1420","ink":"#c8ff3d"}' --strict-variables`.

Motion blur: mark snapping elements with `data-hf-motion-blur` (optionally `'{"shutterAngle": 360}'`, default 720); blur one to three beats, never text to be read, never slow drifts or fades; the engine's `motionBlur` render option blurs the whole frame at render time only.

More workflows: captions (`npx hyperframes transcribe interview.mp4 --engine whisper --model medium.en`), background removal (`npx hyperframes remove-background subject.mp4 -o subject.webm`), media effects and colour grading (`npx hyperframes media-treatment`), design-tool handoff (rebuild moving states in HTML, keep pictures as pictures). Music sync: `/music-to-video` uses `beat_cut` (one clip per anchor) or `phrase_flow` (slow push or crossfade) pacing on a measured beat grid (`sound.md`).
