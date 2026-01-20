# Deprecated / Experimental Hooks

This folder contains hooks that are **not enabled by default** and are kept for reference, study, or experimental purposes.

## Why This Folder Exists

- **Not production-ready**: These hooks may have issues or incomplete implementations
- **Experimental features**: Testing concepts that may or may not be integrated later
- **Reference implementations**: Examples for learning or building custom hooks
- **Study cases**: Analyzing different approaches to hook design

## Contents

### diff-pane

A tmux-based git diff viewer that automatically opens a side pane showing changes when files are edited.

**Status**: Experimental - Works but has edge cases
**Reason for deprecation**: Added complexity, tmux-specific, not universally useful

**Manual Installation** (if you want to test it):
```bash
# Symlink the hooks.json to enable it
ln -s "$(pwd)/hooks/_deprecated/diff-pane/hooks.json" ~/.claude/hooks/diff-pane.json
```

## Important Notes

- These hooks are **NOT loaded automatically** by the plugin system
- The underscore prefix (`_deprecated`) prevents auto-discovery
- Use at your own risk - no support or guarantees
- May contain bugs or incomplete implementations
