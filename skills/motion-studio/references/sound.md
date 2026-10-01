# Sound: score and SFX on the picture's timeline

Read this for any film with audio: a supplied track to sync to, or music and effects to synthesize.

## Two paths

- Track supplied: measure it with librosa into `beats.json` (bpm, beats, downbeats, hits) before animating. Never eyeball tempo.
- No track: synthesize the score and SFX in code on the same timeline as the picture (nothing to license). Code-synthesized music has carried a 2-minute film; sound is what makes it feel like a film rather than generated video. Sound is part of the first render, not post.

## Measure a track

Write `beats.json` with `bpm`, `beats`, `downbeats` (every 4th beat) and onset `hits`; the animation reads it.

```python authored
"""Measure a supplied track: uv run --with librosa beats.py track.wav > beats.json"""
import json
import sys

import librosa

audio, rate = librosa.load(sys.argv[1], sr=None, mono=True)
tempo, beat_times = librosa.beat.beat_track(y=audio, sr=rate, units="time")
hit_times = librosa.onset.onset_detect(y=audio, sr=rate, units="time", backtrack=False)

beat_list = [round(float(b), 3) for b in beat_times]
grid = {
    "bpm": round(float(tempo if not hasattr(tempo, "__len__") else tempo[0]), 2),
    "beats": beat_list,          # UI state changes
    "downbeats": beat_list[::4], # big moments (assumes 4/4)
    "hits": [round(float(h), 3) for h in hit_times],  # SFX
}
json.dump(grid, sys.stdout, indent=1)
```

Placement rules:

- State changes land on beats, big moments (chapter changes, hero reveals) on downbeats, SFX on onset hits.
- Start the film on a downbeat; if the first downbeat is not at 0, keep an offset and apply it everywhere.
- Cut on bar lines for big changes; give each musical phrase its own visual.
- Render one frame per beat as a contact sheet before the full render and check that the change lands on the grid.
- Even with no music, put hits on a shared pulse (a `bpm` constant), so every idle, bounce and cut shares one beat. 120 BPM with something happening on every beat is the standard morph-film grid.
- Lyrics are timed to the audio, not to a stopwatch; for narration, lock beats to the start of the word that names the thing, and use offline TTS (Kokoro) per beat when the voice must be generated, taking durations from the generated files.

## Synthesize SFX and music

- Build SFX from a few seeded voices written to a 48 kHz 16-bit mono WAV: click (short high sine, fast decay), pop (rising sine, 0.15 s), thump (falling sine, ~0.5 s), whoosh (seeded noise with a sine-shaped envelope), plus tick, crack, riser, sparkle, drip, chime, boing, buzz as needed. Seed the noise (LCG), never `Math.random`.
- Cue time = the contact frame minus about 0.03 s. Late reads as broken; slightly early reads as synced. Derive cues from the picture's own event timeline (generate `cues.json` from the beat sheet), not from guesses.
- Vary repeats: per-cue `pitch` multiplier 0.9 to 1.3 for typing and pops so repeats do not sound pasted; `pan` -1..1 for position; footsteps about one per 0.1 s of walking sell a small character.
- Keep each SFX at 0.3 to 0.6 gain; soft-clip (tanh) the mix so a dense first draft cannot clip against the bed.
- No continuous "pencil drawing" scratch bed: tested and rejected, it fights everything. Draw-on is silent; contacts make sound.
- Music bed: with no narration, bed about 0.5 and SFX 0.3 to 0.6; under narration the bed sits about 22 dB below. Starting the bed late (a hook on clicks and typing alone, bed landing with the first cut) hits harder than music from frame 0.
- Looping films: audio in bars that divide the loop length so the sound loops too.
- Game-feel films: choreograph in game time and convert cue times after hit-stop so sound lands on the freeze, and compute music section times after hit-stop or the boss theme starts early.

## Loudness

Normalize the final mix to -14 LUFS with a two-pass `loudnorm` (keep true peak at or below -1.5 dBTP). Verify: `ffmpeg -i final.mp4 -af loudnorm=print_format=summary -f null -` and read integrated loudness and true peak. In zsh, brace every shell variable (`${e}`) or `$var:l` gets eaten as a modifier; doing the loudnorm in Node avoids it.

## API keys

Voice or sound APIs (ElevenLabs and similar): keys live in `.env`; tell the agent the variable name ("the key is ELEVENLABS_API_KEY in .env"). Never paste a real key into a prompt you will screenshot.

## Audio-driven visuals

Sample audio data on every frame (one call per frame at `f / fps`), never one tween for the whole duration, or the visual will not react. Do not add equalizer bars, spectrum analyzers, waveform displays, music-note clip art, rainbow cycling, strobing white on beats or pulsing orbs. Details for HyperFrames audio (voiceover carve, data-fx chains) are in `hyperframes.md`.
