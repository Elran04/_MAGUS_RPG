"""
Game initialization and setup utilities.
"""

import pygame
from config import HEIGHT, WIDTH, WARRIOR_SPRITE, GOBLIN_SPRITE, GRASS_BACKGROUND
from rendering.sprite_manager import load_and_mask_sprite
from systems.character_loader import load_character_json
from systems.equipment_loader import find_weapon_by_id, get_weapon_combat_stats
from systems.scenario_loader import load_scenario

from core.unit_manager import Unit


def setup_game() -> tuple[Unit, Unit, pygame.Surface | None]:
    """
    Initialize game resources: load sprites, create units, load character data.

    Returns:
        Tuple of (warrior, goblin, background_image)
    """

    # Load sprites using centralized paths
    warrior_sprite = load_and_mask_sprite(str(WARRIOR_SPRITE))
    goblin_sprite = load_and_mask_sprite(str(GOBLIN_SPRITE))

    # Create units with default positions
    warrior = Unit(3, 3, warrior_sprite)
    goblin = Unit(6, 3, goblin_sprite)

    # Try to attach demo combat stats from repo characters/*.json
    try:
        warrior_json = load_character_json("Teszt.json")
        warrior.name = warrior_json.get("Név", "Warrior")
        warrior.character_data = warrior_json  # Store full character data
        warrior.set_combat(warrior_json.get("Harci értékek", {}))
        warrior.set_attributes(warrior_json.get("Tulajdonságok", {}))

        # Load equipped weapon
        equipment = warrior_json.get("Felszerelés", [])
        if equipment and len(equipment) > 0:
            weapon_id = equipment[0]  # Use first item as main weapon
            weapon_data = find_weapon_by_id(weapon_id)
            if weapon_data:
                weapon_stats = get_weapon_combat_stats(weapon_data)
                warrior.set_weapon(weapon_stats)
            else:
                pass
    except Exception:
        pass

    try:
        goblin_json = load_character_json("Teszt_Goblin.json")
        goblin.name = goblin_json.get("Név", "Goblin")
        goblin.character_data = goblin_json  # Store full character data
        goblin.set_combat(goblin_json.get("Harci értékek", {}))
        goblin.set_attributes(goblin_json.get("Tulajdonságok", {}))

        # Load equipped weapon
        equipment = goblin_json.get("Felszerelés", [])
        if equipment and len(equipment) > 0:
            weapon_id = equipment[0]  # Use first item as main weapon
            weapon_data = find_weapon_by_id(weapon_id)
            if weapon_data:
                weapon_stats = get_weapon_combat_stats(weapon_data)
                goblin.set_weapon(weapon_stats)
            else:
                pass
    except Exception:
        pass

    # Load background image and scale to window size
    background = None
    try:
        bg_img = pygame.image.load(str(GRASS_BACKGROUND)).convert()
        background = pygame.transform.smoothscale(bg_img, (WIDTH, HEIGHT))
    except Exception:
        pass

    return warrior, goblin, background


def setup_game_from_scenario(name: str) -> tuple[Unit, Unit, pygame.Surface | None]:
    """Initialize game from a scenario name.

    Loads units and background from scenario JSON. Falls back to default setup
    if scenario can't be loaded or is missing required units.
    
    Args:
        name: Scenario file base name (without .json)
    Returns:
        Tuple of (warrior, goblin, background_image)
    """
    units, background, data = load_scenario(name)
    if len(units) >= 2:
        # For now assume first two are warrior/goblin archetypes
        return units[0], units[1], background
    # Fallback to classic setup
    return setup_game()
