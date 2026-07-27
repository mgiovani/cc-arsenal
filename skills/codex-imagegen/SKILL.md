---
name: codex-imagegen
description: Generates images and polished raster art (logos, mascots, hero images, icons, characters, sprite sheets, illustrations, product mockups) by driving Codex CLI's $imagegen skill. This is the default image generator, use it for any request to generate or create an image or visual asset, including "generate an image", "create a hero image", "make a mascot", "design a logo", "draw an icon", "generate a sprite sheet", or "make an illustration". Requires the `codex` CLI installed and authenticated (ChatGPT or API-key auth). Not for architecture, flow, or sequence diagrams (use docs-diagram).
metadata:
  author: mgiovani
  version: 1.0.0
allowed-tools:
  - Bash
  - Read
  - Glob
  - Grep
---

# Codex Imagegen: Illustrated Asset Generation via Codex CLI

Generate polished, professionally-illustrated raster art (mascots, hero images, logos, sprite sheets, product mockups) by driving Codex CLI's `$imagegen` skill. Use this instead of hand-drawing shapes in SVG/CSS/SwiftUI when the asset needs to look designed, not programmatically constructed.

## Scope check (do this first)

This skill wraps a multi-minute, credit-billed Codex run and is the default handler for image-generation requests:

- **Architecture/flow/sequence diagram** → tell the user to use `docs-diagram` instead and stop here.
- Otherwise, continue: the cost gate in Phase 2 decides whether to confirm before running.

## Ground rules

- **Single-quote the whole prompt.** `$imagegen` must reach `codex` literally, not be shell-expanded: a double-quoted or unquoted prompt containing `$imagegen` breaks.
- **Never fabricate a model ID.** `gpt-5.6-sol` is this recipe's known-good default at time of writing; if `codex` rejects it, check `codex --version`/`codex exec --help` for a current one rather than guessing a replacement.
- **Never claim chroma removal or file output succeeded without viewing the pixels.** `sips hasAlpha: yes` proves nothing; open the PNG.
- **Stop before an expensive run and confirm** when the brief is a batch (multiple assets), a consistency-critical asset (recurring character/mascot), or explicitly says "final"/"official": this is real spend and multi-minute wall-clock time, not a free retry.

## Phase 1: Environment check

```bash
codex --version
```

- Not found → tell the user to install Codex CLI and stop.
- Version older than 0.144 → `gpt-5.6-sol` will 400 with "requires a newer version"; tell the user to upgrade before continuing. See [references/troubleshooting.md](references/troubleshooting.md) for the auth/version gotcha table.
- Run from the target repo's root so codex's relative move-file paths land in the right workspace.

## Phase 2: Gather the brief and budget effort

Mine the request for: subject, purpose (README hero, app mascot, icon set, sprite sheet), style, exact save path(s), and whether transparency is required.

Pick `model_reasoning_effort`:

| Ask | Effort |
|---|---|
| Official mascot, multi-image character consistency, intricate composition | `xhigh` |
| Basic placeholder art, single simple asset, low-stakes draft | `high` or lower |

`xhigh` burns significant tokens/credits: don't default to it. If unclear which bucket the request falls in, ask.

**Confirm before running** when this is a batch, a consistency-critical/official asset, or the user said "final": state the design brief, model, effort, exact output paths, and estimated run length (minutes) and get a go-ahead before invoking. For a single obvious low-stakes placeholder, proceed straight to Phase 3.

## Phase 3: Invoke

Run from the workspace root, prompt single-quoted, non-interactive:

```bash
codex exec --full-auto -m gpt-5.6-sol -c model_reasoning_effort="<xhigh|high>" \
  'Use the $imagegen skill to create <asset>. <detailed design brief — subject,
   style, composition, palette, "transparent background" if needed>.
   Move the final PNGs into the workspace at these exact paths: <path1>, <path2>.'
```

If transparency is required, say so explicitly in the brief ("transparent background"): the skill's built-in flow handles chroma-key removal on its own; don't ask for it as a separate step.

For a consistent character across multiple images, put the *full* shared design brief in every asset's prompt, and generate pose/mood variants as edits of the first approved image rather than independent generations: one built-in `image_gen` call per asset is the skill's own rule, so batches are sequential, not parallel.

## Phase 4: Run it in the background, don't pipe the output

`codex exec` has no background flag, background it yourself and never pipe through `tail`/`head` (the pipe buffers everything until exit, so nothing streams while it runs):

```bash
codex exec --full-auto -m gpt-5.6-sol -c model_reasoning_effort="high" \
  -o /tmp/codex-imagegen-final.md \
  '...' > /tmp/codex-imagegen-run.log 2>&1 &
```

- `-o final.md` captures just the final summary.
- Poll `/tmp/codex-imagegen-run.log` for progress; a multi-asset brief can run for many minutes (sequential generation + edit chains + chroma removal + reasoning between steps).
- **File presence in the target paths is not "done."** Assets can appear incrementally before the run finishes (chroma removal/verification still pending): wait for the process to exit before treating the run as complete.
- After exit, `cat` the `-o` output file for the summary and verify the promised paths actually exist (`ls`).

## Phase 5: QC every asset

Open each PNG before wiring it into anything:

- Transparent background actually transparent (not just alpha-flagged): check by viewing the image, not by trusting a metadata field.
- Edges clean, no chroma-key spill (a pink/magenta or green fringe around the subject).
- Consistent character/style across a batch.

Codex can claim chroma removal succeeded while the key color is still visibly there: never report success on the CLI's word alone.

## Notes

- Chroma-key flow: the built-in `image_gen` tool has no native alpha, so the skill generates on a flat chroma-key background then strips it locally. **Never** pass `--despill`/`--spill-cleanup` on pink/magenta-family subject art: despill desaturates those colors toward gray.
- True native alpha (no chroma-key step) needs the CLI fallback (`gpt-image-1.5 --background transparent`) plus `OPENAI_API_KEY`: codex will ask before downgrading to it; don't force it.
- ChatGPT-account auth rejects API-only models; if `-m gpt-5.6-sol` fails on an auth error rather than a version error, see [references/troubleshooting.md](references/troubleshooting.md).
- Regenerating with the same output filenames is cheap; re-integrating a bad asset into the app isn't: favor a re-run over shipping a QC failure.
- If a chroma removal comes out visibly wrong, don't just report failure: the raw generation and the fix procedure are in [references/troubleshooting.md](references/troubleshooting.md) (load it when you actually hit this).

## Worked examples

**1. Single placeholder icon (low stakes, no confirmation gate)**
```
$ codex --version → codex-cli 0.146.0
Effort: high (basic placeholder, single asset) — proceeding without a confirm gate.

$ codex exec --full-auto -m gpt-5.6-sol -c model_reasoning_effort="high" \
    -o /tmp/codex-imagegen-final.md \
    'Use the $imagegen skill to create a minimalist gear icon, flat vector style,
     single accent color on transparent background. Move the final PNG to
     assets/icons/gear.png.' > /tmp/codex-imagegen-run.log 2>&1 &

[poll log until process exits]
$ ls assets/icons/gear.png → found
[open assets/icons/gear.png — background transparent, edges clean]
Done: assets/icons/gear.png
```

**2. Official mascot, transparency-critical (confirmation gate + chroma QC)**
```
Brief: official product mascot, xhigh effort (consistency-critical), transparent
background, 3 pose variants, saves to assets/mascot/{idle,wave,jump}.png.
Estimated run: several minutes across 3 sequential generations. Proceed? (yes/no)

[user: yes]
$ codex exec --full-auto -m gpt-5.6-sol -c model_reasoning_effort="xhigh" \
    -o /tmp/codex-imagegen-final.md \
    'Use the $imagegen skill to create <full shared mascot design brief>, idle pose,
     transparent background. Move the final PNG to assets/mascot/idle.png.' \
    > /tmp/codex-imagegen-run.log 2>&1 &
[wait for exit, then generate wave/jump as edits of the approved idle.png]

[open each PNG] idle.png: clean alpha, no spill. wave.png: faint magenta fringe
on the left arm — chroma removal didn't fully clear. Re-running wave.png only
before shipping.
```

**3. Scope-check redirect (not this skill's job)**
```
User: "draw an architecture diagram of our microservices"

This is a diagram, not an illustrated raster asset — use the docs-diagram
skill instead. Stopping here.
```

## Reference Files

- `references/troubleshooting.md`: version/auth gotcha table, manual chroma-key recovery procedure. Load when a version/auth error blocks Phase 1, or a chroma removal needs a manual fix after Phase 5.
