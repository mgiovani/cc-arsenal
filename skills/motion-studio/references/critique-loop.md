# Critique loop: make the agent watch its own frames

Read this before showing any render to a human, whenever a film "looks a bit mid", and after every fix. The model reads images, so it can look at what it rendered; that single habit separates clips that land from clips posted with "it's a bit mid". Reading code never shows motion. Iteration is the method: a polished 45 s short took 163 model calls and nearly seven hours, not one shot.

## Render the review images

```bash authored
# contact sheet: 2 frames per second, 6 across, 5 down
ffmpeg -i out/final.mp4 -vf "fps=2,scale=270:-1,tile=6x5" -frames:v 1 out/contact.png
# strip: 12 consecutive frames starting at a fast action (4.1 s) to catch pops and overlaps
ffmpeg -ss 4.1 -i out/final.mp4 -vf "scale=320:-1,tile=12x1" -frames:v 1 out/strip.png
# phone test: how it reads at 360 px wide
ffmpeg -i out/final.mp4 -vf "fps=1,scale=360:-1,tile=5x3" -frames:v 1 out/phone.png
# loop check: play twice back to back and watch the seam
ffmpeg -stream_loop 1 -i out/final.mp4 -c copy out/loop_check.mp4
```

Write each image to a new filename (or check mtime): a preview read back from cache shows the old version and a fix looks like it failed. If ffmpeg lacks `drawtext` (common in homebrew builds), draw labels with canvas into a PNG and `overlay` it. Long films: tile one sheet per chapter instead of one huge sheet.

## Review pass (prompt the agent exactly like this)

1. Open the contact sheet, strip and phone test and look at them properly. Be a harsh motion director, not a proud author.
2. Score each 1 to 10 on: hook in the first 2 s, readability at phone size, motion quality (springs, no dead frames), variety (a new thing every 2 to 4 s), composition, brand accuracy, sound sync.
3. List the 3 biggest problems with timestamps and log scores and problems (a `docs/review_log.md` works).
4. Fix the 3 worst problems, re-render only the affected seconds, show the new contact sheet and new scores.
5. Repeat until every score is 8 or higher. Minimum three rounds per shot on long films.

## Hunt list (named failures to look for)

- text overlapping during swaps
- anything sliding instead of easing
- corner labels and frame borders
- centered title on a gradient, everything fading in
- blurry scaled text (a `will-change` or bitmap upscaling problem)
- a dead beat with nothing happening
- a stutter at the loop seam
- glow on UI chrome, generic particle bursts
- frame 0 empty because everything pops in
- UI redrawn from imagination instead of a real screenshot
- sound landing late or off the beat grid

## Gates

- Determinism: the same span rendered twice hashes the same.
- One frame per beat as a contact sheet before the full render; first 5 s as a sample for long films.
- Crop at full resolution for faces, hands, contacts and glows; follow a world point through a moving camera for feet and props.
- Check the encoded master, not only the sheets, and check duration and loudness. A render that exits 0 proves nothing.
- Deliver `final.mp4`, `loop_check.mp4` (loops), `poster.png`, `contact.png`, and say what you would improve next.

For timing, read the sheet like a first-time viewer: render a shot at a fixed step (every 0.1 to 0.15 s), ask at each frame where the eye is and whether it understands yet, and count frames per read (24 frames = 1 s at 24 fps). A read that flashes past in a few frames or shares frames with another read will be missed.
