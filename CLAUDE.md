@AGENTS.md

This file adds Claude-Code-only guidance on top of the tool-agnostic `AGENTS.md` above (Claude Code doesn't read AGENTS.md natively, so this import is the bridge). Everything else — repo overview, skill catalog, skill anatomy, evals, Makefile commands, contributing — lives in `AGENTS.md`; don't duplicate it here.

## Plugin System (Recommended for Claude Code)

Register this repository as a Claude Code Plugin marketplace:
```bash
/plugin marketplace add mgiovani/cc-arsenal
```

Then, to install a specific plugin set:
1. Select **Browse and install plugins**
2. Select **cc-arsenal-marketplace**
3. Select one of the variants (see the table below)
4. Select **Install now**

Alternatively, directly install via:
```bash
/plugin install cc-arsenal@cc-arsenal-marketplace
```

For local development, add a local marketplace instead:
```bash
/plugin marketplace add /path/to/cc-arsenal
```

**Benefits over `npx skills add`:** managed installation, automatic updates, easy enable/disable, no system-wide symlinks — plus the extras below (subagent orchestration, hooks, plugin variants) that only work inside Claude Code.

**Plugin variants** — install the whole toolkit or a focused subset:

| Plugin | Use Case |
|--------|----------|
| `cc-arsenal` | Complete toolkit — every skill |
| `cc-arsenal-dev` | Development workflows |
| `cc-arsenal-review` | Code review and quality audits |
| `cc-arsenal-docs` | Documentation generation |
| `cc-arsenal-git` | Git/GitHub workflow automation |
| `cc-arsenal-jira` | Jira standup, planning, and CLI |
| `cc-arsenal-skills` | Specialty model-invoked capabilities |
| `cc-arsenal-teams` | Team orchestration (experimental) |

Each variant's exact skill set is defined in [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json) — the single source of truth, so the list never drifts across docs. The `cc-arsenal` variant intentionally omits the `skills` field there: an unset `skills` means "auto-load every skill in the repo," so it never needs syncing with the others.

**Troubleshooting plugin updates:**

Local directory marketplaces (`"source": "directory"`) do NOT support auto-update or version detection — Claude Code caches `marketplace.json` on first install and local file changes don't invalidate that cache. After creating new skills or bumping versions:
```bash
rm -rf ~/.claude/plugins/cache/cc-arsenal-marketplace/
# Then in Claude Code: /plugin → Update now
```
Use a GitHub remote marketplace instead for automatic updates in production.

### Development Installation (Symlink Method)

**Only for developing cc-arsenal itself.** Regular users should use the plugin system above.

```bash
uv sync --extra dev
uv run python -m scripts.setup.install     # creates symlinks in ~/.claude
uv run python -m scripts.setup.configure   # interactive: choose specific skills to symlink

# equivalent Makefile targets
make dry-run
make install
make configure
```

`make configure` never modifies `~/.claude/settings.json` — it only symlinks the files you select.

### Team Configuration

For automatic marketplace + plugin installation across team members, add to `.claude/settings.json`:
```json
{
  "extraKnownMarketplaces": {
    "cc-arsenal": {
      "source": { "source": "github", "repo": "mgiovani/cc-arsenal" }
    }
  },
  "enabledPlugins": ["cc-arsenal"]
}
```
When team members trust the repository folder, Claude Code automatically installs the marketplace and plugin.

## Optional Features

```bash
# Statusline Management
make install-statusline           # Install statusline (delegates to feature Makefile)
make uninstall-statusline         # Uninstall statusline (delegates to feature Makefile)
make -C integrations/claude-code/statusline help           # Show all statusline commands
make -C integrations/claude-code/statusline status         # Show statusline configuration
make -C integrations/claude-code/statusline test           # Test statusline
make -C integrations/claude-code/statusline list-backups   # List backups

# Session Scheduler (Claude Hi)
make -C integrations/claude-code/claude-hi help      # Show all scheduler commands
make -C integrations/claude-code/claude-hi standard  # Set up 9am/2pm/7pm schedule
make -C integrations/claude-code/claude-hi status    # Check current schedule
make -C integrations/claude-code/claude-hi remove    # Remove schedule
make -C integrations/claude-code/claude-hi now       # Send 'hi' immediately
```

## Per-skill hooks

A few skills declare a `hooks` key in their SKILL.md frontmatter (e.g. `agent-browser`'s `Stop` hook that closes its browser session). This key is Claude-Code-only — other tools ignore it per the Portability convention in `AGENTS.md` — so those skills must still work correctly with the hook absent.

## Documentation Guidelines

**No README files inside `skills/`** — Claude Code detects them as actual components. Put docs in `docs/` and let each skill's `SKILL.md` be its own native doc.
