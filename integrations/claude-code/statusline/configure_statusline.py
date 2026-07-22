#!/usr/bin/env python3
# ruff: noqa: T201 -- prints are the UI of this interactive tool
"""Interactive configuration for the Claude Code statusline.

Offers exactly the options the statusline honors:
    - display.display_mode               emoji | text | ascii
    - components.enabled.lines_changed   show lines added/removed on line 1

Environment variables (STATUSLINE_DISPLAY_MODE, CLAUDE_STATUSLINE_ACCOUNT_LABEL,
...) override the config file at render time; see STATUSLINE.md.
"""

import json
import sys
from pathlib import Path

CONFIG_PATH = Path.home() / '.claude' / 'cc-arsenal' / 'statusline_config.json'

DISPLAY_MODES = {
    '1': ('emoji', 'Icons for every segment (default)'),
    '2': ('text', 'Short text labels instead of icons'),
    '3': ('ascii', 'Pure ASCII, no icons or unicode'),
}


def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            print(f'Warning: could not parse {CONFIG_PATH}, starting fresh')
    return {}


def save_config(config: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2) + '\n')
    print(f'Saved {CONFIG_PATH}')


def current(config: dict) -> tuple[str, bool]:
    mode = config.get('display', {}).get('display_mode', 'emoji')
    lines = config.get('components', {}).get('enabled', {}).get('lines_changed', False)
    return mode, bool(lines)


def main() -> int:
    config = load_config()
    mode, lines = current(config)

    print('Statusline configuration')
    print(f'  config file:   {CONFIG_PATH}')
    print(f'  display mode:  {mode}')
    print(f'  lines changed: {"on" if lines else "off"}')
    print()

    print('Display mode:')
    for key, (name, desc) in DISPLAY_MODES.items():
        marker = '*' if name == mode else ' '
        print(f'  {key}) [{marker}] {name:<6} {desc}')
    choice = input(f'Choose 1-3 [keep {mode}]: ').strip()
    if choice in DISPLAY_MODES:
        mode = DISPLAY_MODES[choice][0]

    prompt = f'Show lines added/removed? y/n [{"y" if lines else "n"}]: '
    answer = input(prompt).strip().lower()
    if answer in ('y', 'n'):
        lines = answer == 'y'

    config.setdefault('display', {})['display_mode'] = mode
    config.setdefault('components', {}).setdefault('enabled', {})['lines_changed'] = lines
    save_config(config)
    print('Restart Claude Code (or wait for the next refresh) to see the change.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (KeyboardInterrupt, EOFError):
        print('\nAborted, nothing saved.')
        sys.exit(1)
