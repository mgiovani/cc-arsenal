# Remotion route and HyperFrames comparison

Read this to choose between Remotion, HyperFrames and the plain canvas route, to start a Remotion project, or to port Remotion to HyperFrames.

## Choose

| Situation | Route |
|---|---|
| One-off film, full control, no dependencies | Canvas `seek(t)` (`render-engine.md`); this is Opus's default |
| Team already writes React: components, design system, charting libraries, typed validated inputs, series and data-driven templates, mature Lambda rendering | Remotion |
| Web page, HTML prototype, exported design or existing browser animation (GSAP, Lottie) is the source; agent authors it; human edits in Studio; no build step | HyperFrames (`hyperframes.md`) |

Both open a real browser, draw each frame and encode. What differs is what you write and how time works.

- Remotion: React and TypeScript. The component reads the frame number and returns that frame's values, in frames. One pure function of the frame number, no timeline to register, no contract to get subtly wrong; simpler to hold in your head, older, more templates and tutorials, far more production history.
- HyperFrames: HTML, CSS and JavaScript. The renderer pauses animation and seeks to an exact moment before each capture, in seconds. Needs no React, no build step, no component rewrite. Apache 2.0, so no seat count or licence review (Remotion is free for individuals and companies up to three people, paid above; check the current terms). Its rules (paused timeline, no wall clocks, no unseeded randomness) break quietly if ignored; its agent skills encode them.
- Both ship a visual editor that saves back to source; both render on AWS Lambda; HyperFrames also renders locally, on a hosted cloud and on Google Cloud Run.
- Opus does not reach for either unless told. Say "use Remotion" or "using /hyperframes" explicitly.

## Starting Remotion

`npx create-video@latest --yes --blank --no-tailwind my-video`, `npm i`, then run your coding agent in the folder. Install the agent skills with `npx skills add remotion-dev/skills` (gives `/remotion-create`, `/remotion-render` and others), e.g. `/remotion-create a 20s 9:16 launch film for PRODUCT, springs only, one accent color`. Preview with `npx remotion studio`; render with `npx remotion render <CompositionId> out/launch.mp4`.

Rules that matter:

- Animate only from `useCurrentFrame()`; never CSS transitions or timers. Frame 0 is the first, `durationInFrames - 1` the last.
- `interpolate(frame, [in range], [out range], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })` (clamp is usually what you want; default is extend); `spring()` or `Easing.spring({damping: 200})` for settles.
- Register with `<Composition id component durationInFrames fps width height defaultProps>`; keep the component and its registration in one file so dimensions and defaults sit next to the code.
- Prefer separate CSS transform properties (`scale`, `translate`, `rotate`) over a combined `transform` string so Studio can edit keyframes inline.
- Scenes: `TransitionSeries` from `@remotion/transitions` with presentations such as `fade()` and timings such as `linearTiming({ durationInFrames: 15 })`; set `premountFor={fps}` on every timed sequence. `<Series>` when no transitions are needed.
- Media: `<Video>` and `<Audio>` from `@remotion/media` (`trimBefore`, `volume` via `interpolate`); fonts via `@remotion/google-fonts` or `@remotion/fonts` (`loadFont`). Audio-reactive: `useWindowedAudioData` plus `visualizeAudio`, `numberOfSamples` a power of two. Motion blur for animated HTML: `<HtmlInCanvasMotionBlur>` from `@remotion/motion-blur` (no nesting HTML-in-canvas).
- Do not discard the user's manual Studio edits when revising a project.

## Port Remotion to HyperFrames

```bash
npx skills add heygen-com/hyperframes --skill remotion-to-hyperframes
```

Then ask the agent to port the composition. About 80 percent translates mechanically: `useCurrentFrame` and `interpolate` become timeline tweens, `Sequence` becomes clips, frames become seconds, `spring` becomes a `back.out`-style ease. The rest is refused and flagged rather than mistranslated: React state machines (`useState`/`useEffect`), async metadata, third-party React UI libraries. The skill renders both versions, compares them frame by frame and records what it dropped. Port only because the source material or team fits HyperFrames better, not because it looks newer.
