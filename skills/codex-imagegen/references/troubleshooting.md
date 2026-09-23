# Troubleshooting: version, auth, and manual chroma-key fixes

Load this file when Phase 1's environment check fails, or when Phase 5 QC finds a bad chroma removal that needs a manual re-run.

## Version / auth gotchas

| Symptom | Cause | Fix |
|---|---|---|
| `codex exec` 400s with "requires a newer version" | `codex --version` is older than 0.156 | Upgrade Codex CLI before retrying `-m gpt-6-sol` |
| `error: unexpected argument '--full-auto' found` | Codex 0.156 removed `--full-auto` | Use `--approve-for-me` (workspace-write sandbox plus automatic approval review) |
| `-m gpt-6-sol` rejected with an auth/model-access error (not a version error) | ChatGPT-account auth rejects API-only models | Fall back to the config default model (`~/.codex/config.toml` → `model`, `model_reasoning_effort`) instead of forcing `gpt-6-sol` |
| `codex` on `PATH` behaves like an old/standalone build | `~/.local/bin/codex` resolves to a stale `~/.codex/packages/standalone` binary | Check `codex --version`; the current npm-installed binary is typically at `/opt/homebrew/bin/codex`: use that path explicitly if the two disagree |

## Manual chroma-key recovery

Use when Phase 5 QC finds visible spill/key-color fringe that the built-in flow didn't fully clean.

1. Raw generations persist in `$CODEX_HOME/generated_images/<session>/exec-*.png`: recover the original from there rather than re-running the whole generation.
2. Run the chroma-removal helper directly:
   ```bash
   uv run --with pillow python3 \
     $CODEX_HOME/skills/.system/imagegen/scripts/remove_chroma_key.py \
     --input raw.png --out clean.png --auto-key corners --soft-matte --force
   ```
3. **Do not** pass `--despill` or `--spill-cleanup` when the subject art is in the pink/magenta family: despill desaturates those hues toward gray (it has visibly killed pink blush/highlight tones in past runs).
4. Open `clean.png` and re-check edges before treating it as fixed: the helper can also silently under-correct.
