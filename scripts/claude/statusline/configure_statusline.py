#!/usr/bin/env python3
"""Interactive Claude Code Statusline Configuration Tool"""

import json
import sys
from pathlib import Path
from typing import Any


class StatuslineConfigurator:
    def __init__(self) -> None:
        self.config_path = (
            Path.home() / '.claude' / 'cc-arsenal' / 'statusline_config.json'
        )
        self.config = self.load_config()

        # Component descriptions
        self.component_info = {
            'model': '🤖 Model name/version (e.g., Opus, Claude-3.5-Sonnet)',
            'directory': '📁 Current working directory',
            'git': '🌿 Git branch and status (clean/dirty/ahead/behind)',
            'context': '📊 Context window usage percentage remaining',
            'session_cost': '💰 Current session cost in USD',
            'reset_countdown': '🔄 Time until 5-hour window resets',
            'duration_info': '⏱️ Request processing time (total/API)',
            'lines_changed': '📝 Lines added/removed in session',
            'schedule': '📅 Next scheduled task or current Claude window',
        }

        self.separator_options = {
            '1': ' │ ',
            '2': ' | ',
            '3': ' • ',
            '4': ' ▶ ',
            '5': '   ',
            '6': ' → ',
        }

    def load_config(self) -> dict[str, Any]:
        """Load existing configuration or create default"""
        if self.config_path.exists():
            try:
                with self.config_path.open() as f:
                    return json.load(f)  # type: ignore[no-any-return]
            except (OSError, json.JSONDecodeError):
                pass

        # Default configuration
        return {
            'components': {
                'order': [
                    'model',
                    'directory',
                    'git',
                    'context',
                    'session_cost',
                    'lines_changed',
                    'duration_info',
                    'reset_countdown',
                ],
                'enabled': {
                    'model': True,
                    'directory': True,
                    'git': True,
                    'context': True,
                    'session_cost': True,
                    'reset_countdown': True,
                    'duration_info': False,
                    'lines_changed': False,
                },
            },
            'display': {
                'separator': ' │ ',
                'compact_separator': '│',
                'max_width': 120,
                'compact_threshold': 80,
            },
            'formatting': {
                'directory_max_length': 25,
                'directory_display_mode': 'short',
                'git_branch_max_length': 15,
                'cost_decimal_places': 3,
            },
        }

    def save_config(self) -> bool:
        """Save configuration to file"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self.config_path.open('w') as f:
                json.dump(self.config, f, indent=2)
        except OSError:
            return False
        return True

    def show_current_config(self) -> None:
        """Display current configuration"""

        enabled_components = []
        for component in self.config['components']['order']:
            if self.config['components']['enabled'].get(component, False):
                self.component_info.get(component, component)
                enabled_components.append(component)
            else:
                self.component_info.get(component, component)

        for key, _value in self.config['formatting'].items():
            if key == 'directory_display_mode':
                pass
            else:
                pass

    def configure_components(self) -> None:
        """Interactive component configuration"""

        while True:
            choice = input('\nEnter choice (1-3): ').strip()

            if choice == '1':
                self.toggle_components()
            elif choice == '2':
                self.reorder_components()
            elif choice == '3':
                break
            else:
                pass

    def toggle_components(self) -> None:
        """Enable/disable individual components"""

        while True:
            for _i, component in enumerate(self.component_info.keys(), 1):
                self.config['components']['enabled'].get(component, False)
                self.component_info[component]

            try:
                choice = int(
                    input(
                        f'\nToggle component (1-{len(self.component_info) + 1}): '
                    ).strip()
                )
                if choice == len(self.component_info) + 1:
                    break
                if 1 <= choice <= len(self.component_info):
                    component = list(self.component_info.keys())[choice - 1]
                    current_status = self.config['components']['enabled'].get(
                        component, False
                    )
                    self.config['components']['enabled'][component] = not current_status
                else:
                    pass
            except ValueError:
                pass

    def reorder_components(self) -> None:
        """Reorder components interactively"""

        current_order = self.config['components']['order'].copy()

        for _i, component in enumerate(current_order, 1):
            self.component_info.get(component, component)

        try:
            order_input = input('New order: ').strip()
            if not order_input:
                return

            indices = [int(x) - 1 for x in order_input.split()]

            if len(set(indices)) != len(indices):
                return

            if not all(0 <= i < len(current_order) for i in indices):
                return

            # Reorder
            new_order = [current_order[i] for i in indices]

            # Add any missing components at the end
            for component in current_order:
                if component not in new_order:
                    new_order.append(component)

            self.config['components']['order'] = new_order

            for _i, _component in enumerate(new_order, 1):
                pass

        except ValueError:
            pass

    def configure_display(self) -> None:
        """Configure display settings"""

        while True:
            choice = input('\nEnter choice (1-6): ').strip()

            if choice == '1':
                self.change_separator()
            elif choice == '2':
                self.change_compact_separator()
            elif choice == '3':
                self.change_max_width()
            elif choice == '4':
                self.change_compact_threshold()
            elif choice == '5':
                self.change_directory_display_mode()
            elif choice == '6':
                break
            else:
                pass

    def change_separator(self) -> None:
        """Change main separator"""
        for _key, value in self.separator_options.items():
            ' (current)' if value == self.config['display']['separator'] else ''

        choice = input('\nEnter choice (1-7): ').strip()

        if choice in self.separator_options:
            self.config['display']['separator'] = self.separator_options[choice]
        elif choice == '7':
            custom = input('Enter custom separator: ')
            self.config['display']['separator'] = custom
        else:
            pass

    def change_compact_separator(self) -> None:
        """Change compact separator"""
        self.config['display']['compact_separator']
        new_sep = input('Enter new compact separator (or press Enter to keep current): ')
        if new_sep:
            self.config['display']['compact_separator'] = new_sep

    def change_max_width(self) -> None:
        """Change max width"""
        self.config['display']['max_width']
        try:
            new_width = int(input('Enter new max width: '))
            if new_width > 0:
                self.config['display']['max_width'] = new_width
            else:
                pass
        except ValueError:
            pass

    def change_compact_threshold(self) -> None:
        """Change compact threshold"""
        self.config['display']['compact_threshold']
        try:
            new_threshold = int(input('Enter new compact threshold: '))
            if new_threshold > 0:
                self.config['display']['compact_threshold'] = new_threshold
            else:
                pass
        except ValueError:
            pass

    def change_directory_display_mode(self) -> None:
        """Change directory display mode"""
        self.config['formatting'].get('directory_display_mode', 'short')

        choice = input('\nEnter choice (1-2): ').strip()

        if choice == '1':
            self.config['formatting']['directory_display_mode'] = 'short'
        elif choice == '2':
            self.config['formatting']['directory_display_mode'] = 'full'
        else:
            pass

    def preview_statusline(self) -> None:
        """Show preview of current configuration"""

        self._show_mock_statusline_preview()

    def _show_mock_statusline_preview(self) -> None:
        """Show a realistic mock preview of the statusline"""
        components = []

        for component in self.config['components']['order']:
            if not self.config['components']['enabled'].get(component, False):
                continue

            if component == 'model':
                components.append('🤖 Opus')
            elif component == 'directory':
                if (
                    self.config['formatting'].get('directory_display_mode', 'short')
                    == 'full'
                ):
                    components.append('📁 /Users/user/projects/my-project')
                else:
                    components.append('📁 ~/projects/my-project')
            elif component == 'git':
                components.append('🌿 main ●')
            elif component == 'context':
                components.append('📊 73%')
            elif component == 'session_cost':
                components.append('💰 $0.023')
            elif component == 'lines_changed':
                components.append('📝 +42/-8')
            elif component == 'duration_info':
                components.append('⏱️ 2s (1s)')
            elif component == 'reset_countdown':
                components.append('🔄 3h45m')

        if not components:
            return

        separator = self.config['display']['separator']
        compact_threshold = self.config['display']['compact_threshold']

        # Show full version
        full_preview = separator.join(components)

        # Show compact version if it would trigger
        if len(full_preview) > compact_threshold:
            compact_separator = self.config['display']['compact_separator']

            # Create compact components (simplified)
            compact_components = []
            for component in self.config['components']['order']:
                if not self.config['components']['enabled'].get(component, False):
                    continue

                if component == 'model':
                    compact_components.append('🤖Opus')
                elif component == 'directory':
                    compact_components.append('📁my-project')
                elif component == 'git':
                    compact_components.append('🌿main●')
                elif component == 'context':
                    compact_components.append('📊73%')
                elif component == 'session_cost':
                    compact_components.append('💰$0.023')
                elif component == 'lines_changed':
                    compact_components.append('📝+42-8')
                elif component == 'duration_info':
                    compact_components.append('⏱️2s')
                elif component == 'reset_countdown':
                    compact_components.append('🔄3h45m')

            compact_separator.join(compact_components)

    def main_menu(self) -> None:
        """Main configuration menu"""

        while True:
            choice = input('\nEnter choice (1-6): ').strip()

            if choice == '1':
                self.show_current_config()
            elif choice == '2':
                self.configure_components()
            elif choice == '3':
                self.configure_display()
            elif choice == '4':
                self.preview_statusline()
            elif choice == '5':
                if self.save_config():
                    pass
                break
            elif choice == '6':
                break
            else:
                pass


def main() -> None:
    """Main entry point"""
    configurator = StatuslineConfigurator()
    try:
        configurator.main_menu()
    except KeyboardInterrupt:
        pass
    except (OSError, RuntimeError):
        sys.exit(1)


if __name__ == '__main__':
    main()
