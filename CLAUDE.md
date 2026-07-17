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
3. Select one of:
   - **cc-arsenal** - Complete toolkit (all 41 skills)
   - **cc-arsenal-dev** - Development skills only (implement-feature, fix-bug, test-suite, refactor, ci-generate, ci-local, inject-docs, project-planner, nanobanana, db-migrate, docker-init, env-setup, vrt-check, i18n-check, ship)
   - **cc-arsenal-review** - Code review and quality skills only (review-code, review-security, review-deps, review-perf, review-design)
   - **cc-arsenal-docs** - Documentation skills only (ADR, RFC, diagrams, init, check, update)
   - **cc-arsenal-git** - Git/GitHub workflow skills only (git-commit, git-create-pr, git-release, gitflow, gh-daily, git-sync)
   - **cc-arsenal-jira** - Jira skills only (jira-cli, jira-daily, jira-todo)
   - **cc-arsenal-skills** - Specialty skills only (agent-browser, find-skills, create-skill, create-rule)
   - **cc-arsenal-teams** - Team orchestration (team-implement, team-review)
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

**Plugin Variants (8 total):**

| Plugin | Skills Loaded | Use Case |
|--------|--------------|----------|
| `cc-arsenal` | All 41 skills | Full toolkit for complete workflow automation |
| `cc-arsenal-dev` | implement-feature, fix-bug, test-suite, refactor, ci-generate, ci-local, inject-docs, project-planner, nanobanana, db-migrate, docker-init, env-setup, vrt-check, i18n-check, ship | Development workflows with subagents |
| `cc-arsenal-review` | review-code, review-security, review-deps, review-perf, review-design | Code review and quality audits |
| `cc-arsenal-docs` | docs-adr, docs-check, docs-diagram, docs-init, docs-rfc, docs-update | Documentation generation only |
| `cc-arsenal-git` | git-commit, git-create-pr, git-release, gitflow, gh-daily, git-sync | Git/GitHub workflow automation |
| `cc-arsenal-jira` | jira-cli, jira-daily, jira-todo | Jira standup, planning, and CLI |
| `cc-arsenal-skills` | agent-browser, find-skills, create-skill, create-rule | Specialty model-invoked capabilities |
| `cc-arsenal-teams` | team-implement, team-review | Team orchestration (experimental) |

The `cc-arsenal` plugin intentionally omits the `skills` field in `marketplace.json` — an unset `skills` field means "auto-load every skill in the repo," so it doesn't need to be kept in sync with the other variants.

**How it works:**
- Single repository, all skills in `skills/`
- `.claude-plugin/marketplace.json` defines the marketplace and each plugin variant's `skills` list
- Users install only what they need without duplicating code

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
make -C scripts/claude/statusline help           # Show all statusline commands
make -C scripts/claude/statusline status         # Show statusline configuration
make -C scripts/claude/statusline test           # Test statusline
make -C scripts/claude/statusline list-backups   # List backups

# Session Scheduler (Claude Hi)
make -C scripts/claude-hi help      # Show all scheduler commands
make -C scripts/claude-hi standard  # Set up 9am/2pm/7pm schedule
make -C scripts/claude-hi status    # Check current schedule
make -C scripts/claude-hi remove    # Remove schedule
make -C scripts/claude-hi now       # Send 'hi' immediately
```

## Per-skill hooks

A few skills declare a `hooks` key in their SKILL.md frontmatter (e.g. `agent-browser`'s `Stop` hook that closes its browser session). This key is Claude-Code-only — other tools ignore it per the Portability convention in `AGENTS.md` — so those skills must still work correctly with the hook absent; the hook is a convenience, not a dependency.

## Documentation Guidelines

**No README files inside `skills/`** — Claude Code detects them as actual components. Put docs in `docs/`, use `AGENTS.md` for cross-tool guidance and this file for Claude-Code specifics, and let each skill's `SKILL.md` be its own native doc.
