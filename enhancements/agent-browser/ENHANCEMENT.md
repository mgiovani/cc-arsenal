---
# Enhancement for: agent-browser
hooks:
  Stop:
  - hooks:
    - type: command
      command: agent-browser close 2>/dev/null || true
      once: true
      timeout: 10
---

## Claude Code Enhanced Features

This skill integrates with Claude Code's tool ecosystem for enhanced automation.
