"""Scenario loader for MAGUS Pygame.
Loads scenario JSON defining units, positions, facing, and background.
"""

from __future__ import annotations

import json
from typing import Any, Tuple
import pygame

from config import (
    get_scenario_json_path,
    get_character_json_path,
    get_character_sprite_path,
    CHARACTER_SPRITES_DIR,
    GRASS_BACKGROUND,
    WIDTH,
    HEIGHT,
)
from systems.character_loader import load_character_json
from systems.equipment_loader import find_weapon_by_id, get_weapon_combat_stats
from rendering.sprite_manager import load_and_mask_sprite
from core.unit_manager import Unit


def load_scenario(name: str) -> Tuple[list[Unit], pygame.Surface | None, dict[str, Any]]:
    """Load a scenario by name.

    Args:
        name: Scenario file name without extension (e.g. 'default')

    Returns:
        (units, background_surface, scenario_dict)
    """
    path = get_scenario_json_path(f"{name}.json")
    data: dict[str, Any] = {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        # Fallback: return empty units and default background
        return [], _load_background(str(GRASS_BACKGROUND)), {}

    units_config = data.get("units", [])
    units: list[Unit] = []

    for uconf in units_config:
        sprite_file = uconf.get("sprite", "warrior.png")
        sprite_path = get_character_sprite_path(sprite_file)
        sprite = load_and_mask_sprite(str(sprite_path))
        q = int(uconf.get("start_q", 0))
        r = int(uconf.get("start_r", 0))
        unit = Unit(q, r, sprite)
        unit.facing = int(uconf.get("facing", 0))

        # Load character sheet if present
        char_file = uconf.get("character_file")
        if char_file:
            try:
                char_data = load_character_json(char_file)
                unit.name = char_data.get("Név", unit.name or "Unit")
                unit.character_data = char_data
                unit.set_combat(char_data.get("Harci értékek", {}))
                unit.set_attributes(char_data.get("Tulajdonságok", {}))

                # Load first weapon id if present
                equipment = char_data.get("Felszerelés", [])
                if equipment:
                    weapon_id = equipment[0]
                    weapon_data = find_weapon_by_id(weapon_id)
                    if weapon_data:
                        unit.set_weapon(get_weapon_combat_stats(weapon_data))
            except Exception:
                pass

        units.append(unit)

    # Load background image (scenario overrides default)
    bg_file = data.get("background")
    background_surface = _load_background(bg_file) if bg_file else _load_background(str(GRASS_BACKGROUND))

    return units, background_surface, data


def _load_background(path_str: str) -> pygame.Surface | None:
    try:
        bg_img = pygame.image.load(path_str).convert()
        return pygame.transform.smoothscale(bg_img, (WIDTH, HEIGHT))
    except Exception:
        return None


__all__ = ["load_scenario"]
