#!/usr/bin/env python3
"""
Interactive Claude Code Statusline Configuration Tool
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

class StatuslineConfigurator:
    def __init__(self):
        self.config_path = Path.home() / ".claude" / "claude_dump" / "statusline_config.json"
        self.config = self.load_config()
        
        # Component descriptions
        self.component_info = {
            "model": "🤖 Model name/version (e.g., Opus, Claude-3.5-Sonnet)",
            "directory": "📁 Current working directory",
            "git": "🌿 Git branch and status (clean/dirty/ahead/behind)",
            "context": "📊 Context window usage percentage remaining",
            "session_cost": "💰 Current session cost in USD",
            "daily_cost": "📅 Daily usage cost total",
            "reset_countdown": "🔄 Time until 5-hour window resets",
            "duration_info": "⏱️ Request processing time (total/API)",
            "lines_changed": "📝 Lines added/removed in session"
        }
        
        self.separator_options = {
            "1": " │ ",
            "2": " | ",
            "3": " • ",
            "4": " ▶ ",
            "5": "   ",
            "6": " → "
        }

    def load_config(self) -> Dict[str, Any]:
        """Load existing configuration or create default"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️  Error loading config: {e}")
                print("Using default configuration...")
        
        # Default configuration
        return {
            "components": {
                "order": [
                    "model",
                    "directory", 
                    "git",
                    "context",
                    "session_cost",
                    "daily_cost",
                    "lines_changed",
                    "duration_info",
                    "reset_countdown"
                ],
                "enabled": {
                    "model": True,
                    "directory": True,
                    "git": True,
                    "context": True,
                    "session_cost": True,
                    "daily_cost": True,
                    "reset_countdown": True,
                    "duration_info": False,
                    "lines_changed": False
                }
            },
            "display": {
                "separator": " │ ",
                "compact_separator": "│",
                "max_width": 120,
                "compact_threshold": 80
            },
            "formatting": {
                "directory_max_length": 25,
                "directory_display_mode": "short",
                "git_branch_max_length": 15,
                "cost_decimal_places": 3,
                "daily_cost_decimal_places": 2
            }
        }

    def save_config(self):
        """Save configuration to file"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            print(f"✅ Configuration saved to {self.config_path}")
        except IOError as e:
            print(f"❌ Error saving config: {e}")
            return False
        return True

    def show_current_config(self):
        """Display current configuration"""
        print("\n🔧 Current Statusline Configuration")
        print("=" * 50)
        
        print("\n📋 Enabled Components (in order):")
        enabled_components = []
        for component in self.config["components"]["order"]:
            if self.config["components"]["enabled"].get(component, False):
                desc = self.component_info.get(component, component)
                print(f"  ✅ {component}: {desc}")
                enabled_components.append(component)
            else:
                desc = self.component_info.get(component, component)
                print(f"  ❌ {component}: {desc}")
        
        print(f"\n🎨 Display Settings:")
        print(f"  Separator: '{self.config['display']['separator']}'")
        print(f"  Compact separator: '{self.config['display']['compact_separator']}'")
        print(f"  Max width: {self.config['display']['max_width']}")
        print(f"  Compact threshold: {self.config['display']['compact_threshold']}")
        
        print(f"\n📐 Formatting:")
        for key, value in self.config['formatting'].items():
            if key == "directory_display_mode":
                mode_desc = "shortened path" if value == "short" else "full path"
                print(f"  Directory Display: {value} ({mode_desc})")
            else:
                print(f"  {key.replace('_', ' ').title()}: {value}")

    def configure_components(self):
        """Interactive component configuration"""
        print("\n🔧 Configure Components")
        print("=" * 30)
        
        while True:
            print("\nChoose an action:")
            print("1. Enable/disable components")
            print("2. Reorder components")
            print("3. Back to main menu")
            
            choice = input("\nEnter choice (1-3): ").strip()
            
            if choice == "1":
                self.toggle_components()
            elif choice == "2":
                self.reorder_components()
            elif choice == "3":
                break
            else:
                print("❌ Invalid choice")

    def toggle_components(self):
        """Enable/disable individual components"""
        print("\n✅❌ Enable/Disable Components")
        print("-" * 35)
        
        while True:
            print("\nCurrent status:")
            for i, component in enumerate(self.component_info.keys(), 1):
                enabled = self.config["components"]["enabled"].get(component, False)
                status = "✅" if enabled else "❌"
                desc = self.component_info[component]
                print(f"{i}. {status} {component}: {desc}")
            
            print(f"{len(self.component_info) + 1}. Back")
            
            try:
                choice = int(input(f"\nToggle component (1-{len(self.component_info) + 1}): ").strip())
                if choice == len(self.component_info) + 1:
                    break
                elif 1 <= choice <= len(self.component_info):
                    component = list(self.component_info.keys())[choice - 1]
                    current_status = self.config["components"]["enabled"].get(component, False)
                    self.config["components"]["enabled"][component] = not current_status
                    new_status = "enabled" if not current_status else "disabled"
                    print(f"✅ {component} {new_status}")
                else:
                    print("❌ Invalid choice")
            except ValueError:
                print("❌ Please enter a number")

    def reorder_components(self):
        """Reorder components interactively"""
        print("\n🔄 Reorder Components")
        print("-" * 25)
        
        current_order = self.config["components"]["order"].copy()
        
        print("Current order:")
        for i, component in enumerate(current_order, 1):
            desc = self.component_info.get(component, component)
            print(f"{i}. {component}: {desc}")
        
        print("\nEnter new order by typing component numbers separated by spaces")
        print("Example: 2 1 3 4 5 6 (to move directory before model)")
        
        try:
            order_input = input("New order: ").strip()
            if not order_input:
                return
                
            indices = [int(x) - 1 for x in order_input.split()]
            
            if len(set(indices)) != len(indices):
                print("❌ Duplicate indices not allowed")
                return
                
            if not all(0 <= i < len(current_order) for i in indices):
                print(f"❌ Invalid indices. Use numbers 1-{len(current_order)}")
                return
            
            # Reorder
            new_order = [current_order[i] for i in indices]
            
            # Add any missing components at the end
            for component in current_order:
                if component not in new_order:
                    new_order.append(component)
            
            self.config["components"]["order"] = new_order
            
            print("\n✅ New order:")
            for i, component in enumerate(new_order, 1):
                print(f"{i}. {component}")
                
        except ValueError:
            print("❌ Invalid input. Please enter numbers separated by spaces")

    def configure_display(self):
        """Configure display settings"""
        print("\n🎨 Display Settings")
        print("=" * 20)
        
        while True:
            print("\nChoose setting to modify:")
            print("1. Change separator")
            print("2. Change compact separator") 
            print("3. Change max width")
            print("4. Change compact threshold")
            print("5. Change directory display mode")
            print("6. Back to main menu")
            
            choice = input("\nEnter choice (1-6): ").strip()
            
            if choice == "1":
                self.change_separator()
            elif choice == "2":
                self.change_compact_separator()
            elif choice == "3":
                self.change_max_width()
            elif choice == "4":
                self.change_compact_threshold()
            elif choice == "5":
                self.change_directory_display_mode()
            elif choice == "6":
                break
            else:
                print("❌ Invalid choice")

    def change_separator(self):
        """Change main separator"""
        print("\n🎨 Choose separator style:")
        for key, value in self.separator_options.items():
            current = " (current)" if value == self.config["display"]["separator"] else ""
            print(f"{key}. '{value}'{current}")
        print("7. Custom separator")
        
        choice = input("\nEnter choice (1-7): ").strip()
        
        if choice in self.separator_options:
            self.config["display"]["separator"] = self.separator_options[choice]
            print(f"✅ Separator set to '{self.separator_options[choice]}'")
        elif choice == "7":
            custom = input("Enter custom separator: ")
            self.config["display"]["separator"] = custom
            print(f"✅ Custom separator set to '{custom}'")
        else:
            print("❌ Invalid choice")

    def change_compact_separator(self):
        """Change compact separator"""
        current = self.config["display"]["compact_separator"]
        print(f"\nCurrent compact separator: '{current}'")
        new_sep = input("Enter new compact separator (or press Enter to keep current): ")
        if new_sep:
            self.config["display"]["compact_separator"] = new_sep
            print(f"✅ Compact separator set to '{new_sep}'")

    def change_max_width(self):
        """Change max width"""
        current = self.config["display"]["max_width"]
        print(f"\nCurrent max width: {current}")
        try:
            new_width = int(input("Enter new max width: "))
            if new_width > 0:
                self.config["display"]["max_width"] = new_width
                print(f"✅ Max width set to {new_width}")
            else:
                print("❌ Width must be positive")
        except ValueError:
            print("❌ Please enter a valid number")

    def change_compact_threshold(self):
        """Change compact threshold"""
        current = self.config["display"]["compact_threshold"]
        print(f"\nCurrent compact threshold: {current}")
        try:
            new_threshold = int(input("Enter new compact threshold: "))
            if new_threshold > 0:
                self.config["display"]["compact_threshold"] = new_threshold
                print(f"✅ Compact threshold set to {new_threshold}")
            else:
                print("❌ Threshold must be positive")
        except ValueError:
            print("❌ Please enter a valid number")

    def change_directory_display_mode(self):
        """Change directory display mode"""
        current = self.config["formatting"].get("directory_display_mode", "short")
        print(f"\nCurrent directory display mode: {current}")
        print("\nDirectory display options:")
        
        mode_current = " (current)" if current == "short" else ""
        full_current = " (current)" if current == "full" else ""
        print(f"1. short - Show shortened path (~/projects/myproject){mode_current}")
        print(f"2. full - Show full absolute path (/Users/username/projects/myproject){full_current}")
        
        choice = input("\nEnter choice (1-2): ").strip()
        
        if choice == "1":
            self.config["formatting"]["directory_display_mode"] = "short"
            print("✅ Directory display set to short path")
        elif choice == "2":
            self.config["formatting"]["directory_display_mode"] = "full"
            print("✅ Directory display set to full path")
        else:
            print("❌ Invalid choice")

    def preview_statusline(self):
        """Show preview of current configuration"""
        print("\n👀 Statusline Preview")
        print("=" * 20)
        
        print("📊 Mock Preview (with current unsaved settings):")
        self._show_mock_statusline_preview()
    
    def _show_mock_statusline_preview(self):
        """Show a realistic mock preview of the statusline"""
        components = []
        
        for component in self.config["components"]["order"]:
            if not self.config["components"]["enabled"].get(component, False):
                continue
                
            if component == "model":
                components.append("🤖 Opus")
            elif component == "directory":
                if self.config["formatting"].get("directory_display_mode", "short") == "full":
                    components.append("📁 /Users/user/projects/my-project")
                else:
                    components.append("📁 ~/projects/my-project")
            elif component == "git":
                components.append("🌿 main ●")
            elif component == "context":
                components.append("📊 73%")
            elif component == "session_cost":
                components.append("💰 $0.023")
            elif component == "daily_cost":
                components.append("📅 $1.47")
            elif component == "lines_changed":
                components.append("📝 +42/-8")
            elif component == "duration_info":
                components.append("⏱️ 2s (1s)")
            elif component == "reset_countdown":
                components.append("🔄 3h45m")
        
        if not components:
            print("(No components enabled)")
            return
            
        separator = self.config["display"]["separator"]
        terminal_width = 120  # Mock terminal width
        compact_threshold = self.config["display"]["compact_threshold"]
        
        # Show full version
        full_preview = separator.join(components)
        print(f"{full_preview}")
        
        # Show compact version if it would trigger
        if len(full_preview) > compact_threshold:
            print("\n📱 Compact version (narrow terminal):")
            compact_separator = self.config["display"]["compact_separator"]
            
            # Create compact components (simplified)
            compact_components = []
            for component in self.config["components"]["order"]:
                if not self.config["components"]["enabled"].get(component, False):
                    continue
                    
                if component == "model":
                    compact_components.append("🤖Opus")
                elif component == "directory":
                    compact_components.append("📁my-project")
                elif component == "git":
                    compact_components.append("🌿main●")
                elif component == "context":
                    compact_components.append("📊73%")
                elif component == "session_cost":
                    compact_components.append("💰$0.023")
                elif component == "daily_cost":
                    compact_components.append("📅$1.47")
                elif component == "lines_changed":
                    compact_components.append("📝+42-8")
                elif component == "duration_info":
                    compact_components.append("⏱️2s")
                elif component == "reset_countdown":
                    compact_components.append("🔄3h45m")
            
            compact_preview = compact_separator.join(compact_components)
            print(f"{compact_preview}")
            
        print(f"\n⚙️  Settings: {len(components)} components, separator: '{separator}'")

    def main_menu(self):
        """Main configuration menu"""
        print("\n🎯 Claude Code Statusline Configurator")
        print("=" * 40)
        
        while True:
            print("\nMain Menu:")
            print("1. Show current configuration")
            print("2. Configure components")
            print("3. Configure display settings")
            print("4. Preview statusline")
            print("5. Save and exit")
            print("6. Exit without saving")
            
            choice = input("\nEnter choice (1-6): ").strip()
            
            if choice == "1":
                self.show_current_config()
            elif choice == "2":
                self.configure_components()
            elif choice == "3":
                self.configure_display()
            elif choice == "4":
                self.preview_statusline()
            elif choice == "5":
                if self.save_config():
                    print("\n✅ Configuration saved successfully!")
                    print("Restart Claude Code to see changes.")
                break
            elif choice == "6":
                print("\n👋 Exiting without saving changes.")
                break
            else:
                print("❌ Invalid choice")

def main():
    """Main entry point"""
    configurator = StatuslineConfigurator()
    try:
        configurator.main_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Configuration cancelled.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()