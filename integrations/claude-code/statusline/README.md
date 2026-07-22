# Claude Code Enhanced Statusline

A bash+jq statusline for Claude Code showing model, git status, cost, context usage, and 5-hour/7-day usage windows — with optional multi-account support.

## Example

```
🤖 Opus │ 📁 cc-arsenal │ 🌿 main ● │ 📊 22% │ 💰 $0.043 │ ⏱️ 21m
🔄 5h: 16% → 21:00 │ 📅 7d: 39% → Dec 31 21:00
```

## Install

```bash
make install-statusline   # from the cc-arsenal project root
```

👉 **[Complete guide →](STATUSLINE.md)** — installation, configuration, every `STATUSLINE_*`/`CLAUDE_*` env var, multi-account setup, and troubleshooting.
