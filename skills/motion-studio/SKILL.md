---
name: motion-studio
description: "Make motion design videos rendered from code with Claude Code: showreels, product launch reels, UI morph films, music videos, explainers, Claude-mascot (Clawd) cartoons, hand-drawn storybook shorts. Covers the deterministic seek(t) canvas renderer with Playwright and ffmpeg, closed-form springs, beat grids and synthesized sound, the contact-sheet critique loop, director prompt patterns (one-liner, brand reel, reference, XML state spec, overnight brief), a catalog of proven styles, and the HyperFrames and Remotion routes. Use when the user asks for a launch video, showreel, product reel, animated explainer, motion ad, music video, Claude mascot / Clawd animation, or a HyperFrames or Remotion video made in code. Not for editing live-action footage in a video editor, generating clips with a text-to-video model alone, or static images."
metadata:
  summary: "Motion videos rendered from code: seek(t) engine, springs, beat-synced sound, critique loop, styles, HyperFrames and Remotion"
  author: mgiovani
  version: 1.0.0
---

# Motion studio

Every video here is a program. Claude writes code that paints a frame for any moment in time, a headless browser (or Node canvas) captures the frames, ffmpeg encodes them. The model cannot emit an MP4; only an agent with a shell can render, listen to and look at its own frames. The prompt is 10 percent of the video; the harness (renderer, sound, critique loop) is the other 90.

## When to use

- Launch videos, product reels, showreels, motion ads, UI morph loops, music videos, explainers, short films made in code.
- Turning a product URL, a reference clip or a song into a rendered MP4.
- Building or fixing the pipeline itself: `seek(t)`, springs, beat grid, SFX, critique loop.

## Pick a route first

| Route | When | Read |
|---|---|---|
| A. Canvas `seek(t)` + Playwright + ffmpeg (default) | Any one-off film; zero dependencies, full control | `references/render-engine.md` |
| A1. Clawd / p5.brush cartoon | Animations starring the Claude mascot, painted storybook cartoons | `references/clawd-mascot.md` |
| A2. Hand-drawn Node canvas (no browser) | Storybook, brush-ink and watercolour, low-poly loops, game-feel shorts | `references/hand-drawn-canvas.md` |
| B. HyperFrames (HTML + GSAP, agent skills) | Web-page thinking, captions, voiceover, templates, Studio editing | `references/hyperframes.md` |
| C. Remotion (React) | Teams already in React, series, data-driven templates | `references/remotion.md` |

Opus defaults to route A (one `index.html`, Playwright, ffmpeg, zero dependencies) and skips Remotion and HyperFrames even when installed. If the user wants a framework, say so explicitly in the brief.

HyperFrames setup (ask the user first): run `npx skills add heygen-com/hyperframes` and choose Core Skills; for CI or non-interactive refresh run `npx hyperframes skills update`. Start a fresh chat afterwards and ask it to use `/hyperframes`. HyperFrames needs no React or build step and is Apache 2.0; Remotion fits teams already writing React (components, design system, typed inputs).

## Core workflow

1. Collect inputs: product and URL, duration, formats (9:16, 1:1, 16:9), brand colours and fonts, a reference (frame, video, image folder), music (file or "synthesize"). Ask for anything missing.
2. Gather real assets: screenshot the real product with Playwright into `./assets` and list them. Never redraw UI from imagination.
3. Reference to style: name a look and feed a frame; write `docs/style_guide.md` from it, then `docs/shotlist.md`. Without a reference, output falls back to centered text on a gradient with everything fading in. See `references/prompting-and-briefs.md`, `references/style-catalog.md`.
4. Beat grid: measure the supplied track with librosa into `beats.json`, or synthesize music and SFX on the same timeline as the picture. See `references/sound.md`.
5. Show the shot list on the beat grid and wait for OK before scene code (overnight runs: continue after a stated timeout).
6. Build `index.html` with `window.seek(t)`, closed-form springs, seeded noise only. See `references/render-engine.md`, `references/motion-and-springs.md`.
7. Critique loop: contact sheet, strip, phone test; score 1 to 10; fix the 3 worst; repeat until every score is 8 or higher; re-render only the affected seconds. See `references/critique-loop.md`.
8. Render all formats from one timeline, mix audio to -14 LUFS, deliver `final.mp4`, `contact.png`, `poster.png` (and a loop check for loops), and say what you would improve next.

## Rules that apply everywhere

- A film is a function of time only: `window.seek(t)` draws the frame at `t`. During render there are no CSS transitions, timers or `requestAnimationFrame`, and nothing persists from one frame to the next. `await document.fonts.ready` before capturing canvas text.
- Randomness is seeded (mulberry32), never `Math.random`.
- Encode H.264 (`libx264`), `yuv420p`, CRF 16. Motion blur by rendering 4 subframes per frame and blending with ffmpeg `tmix`.
- Motion: closed-form springs; a value with several targets sums one spring per change instead of restarting (`retarget()`); tab indicators stretch with the leading edge stiffer than the trailing edge; a loop's last frame equals its first, cursor velocity included.
- Ban the AI-video defaults: a title centered on a gradient, fade-in on everything, labels in the corners or borders around the frame, glowing UI chrome, stock particle bursts. One display face, one UI face, one accent. Something new on screen every 2 to 4 seconds.
- Sound: synthesize the score and SFX on the same timeline unless a track is supplied; state changes on beats, big moments on downbeats, SFX on hits; mix at -14 LUFS.
- Effort (Opus 5.5 defaults to medium): keep medium for tweaks and re-renders, raise to xhigh for a new film, and use max for launch pieces whose opening seconds must hook.
- Put house rules in the project `CLAUDE.md` so every film inherits them. Keep one session per brand. API keys live in `.env`, never in a prompt.
- Reframe type and UI per format; do not crop a 16:9 render to vertical.
- Long films are iteration, not one shot. For long or multi-chapter films, write `docs/ANIMATION_GUIDE.md` first and have subagents code each chapter in its own file behind it.

## Routing

| User says | Load |
|---|---|
| "build the renderer", "render the video", "motion blur", "ffmpeg encode", "loop", "formats" | `references/render-engine.md` |
| "motion feels cheap", "springs", "cursor and container jump", "tab indicator", "UI morph", "camera" | `references/motion-and-springs.md` |
| "music", "beats", "sync", "SFX", "loudness", "no audio track" | `references/sound.md` |
| "looks mid", "review the render", "contact sheet", "before I post it" | `references/critique-loop.md` |
| "write the prompt", "brand reel", "reference video", "state list", "overnight", "director brief", "effort" | `references/prompting-and-briefs.md` |
| "what style", "riso", "pixel", "watercolour", "product tour", "documentary" | `references/style-catalog.md` |
| "Clawd", "Claude mascot", "p5.brush", "painted cartoon" | `references/clawd-mascot.md` |
| "hand-drawn", "storybook", "ant", "low-poly loop", "game short in JS" | `references/hand-drawn-canvas.md` |
| "HyperFrames", "/hyperframes", "captions", "GSAP", "video from a URL or PR" | `references/hyperframes.md` |
| "Remotion", "React video", "HyperFrames vs Remotion", "port to HyperFrames" | `references/remotion.md` |

Credits and source licenses: `references/credits.md`.
