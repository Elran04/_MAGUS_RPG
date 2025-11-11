"""Presentation layer screens.

Organized into logical subdirectories:
- menu/: Main menu and menu-related screens
- scenario_setup/: Scenario configuration screens (map, teams, equipment phases)
- game/: In-game screens (battle, deployment, equipment)
- editor/: Scenario editor and related tools
"""

# Menu screens
# Editor screens
from .editor.scenario_editor_screen import ScenarioEditorScreen

# Game screens
from .game.battle_screen import BattleScreen
from .game.deployment_screen import DeploymentScreen
from .game.equipment_screen import EquipmentScreen
from .menu.menu_screen import Menu, MenuItem, MenuState

# Scenario setup screens
from .scenario_setup.scenario_screen import ScenarioScreen

__all__ = [
    # Menu
    "Menu",
    "MenuState",
    "MenuItem",
    # Scenario setup
    "ScenarioScreen",
    # Game
    "BattleScreen",
    "DeploymentScreen",
    "EquipmentScreen",
    # Editor
    "ScenarioEditorScreen",
]
