"""
Equipment data loader for MAGUS_pygame.
Loads weapon and equipment data from the Gamemaster_tools data folder.
"""
import json
import os
from typing import Any, Dict, Optional


def repo_root() -> str:
    """Get the repository root directory."""
    # __file__ is in systems/ folder -> parent is MAGUS_pygame -> parent is repo root
    magus_pygame_dir = os.path.dirname(os.path.dirname(__file__))
    return os.path.dirname(magus_pygame_dir)


_WEAPONS_CACHE: Optional[list[Dict[str, Any]]] = None


def load_weapons_data() -> list[Dict[str, Any]]:
    """Load weapons and shields data from JSON.

    Returns:
        List of weapon dictionaries.
    Raises:
        FileNotFoundError if the file doesn't exist.
        json.JSONDecodeError if invalid JSON.
    """
    global _WEAPONS_CACHE
    if _WEAPONS_CACHE is not None:
        return _WEAPONS_CACHE

    path = os.path.join(
        repo_root(), 
        "Gamemaster_tools", 
        "data", 
        "equipment", 
        "weapons_and_shields.json"
    )
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        _WEAPONS_CACHE = data
        return data


def find_weapon_by_id(weapon_id: str) -> Optional[Dict[str, Any]]:
    """Find a weapon by its ID.

    Args:
        weapon_id: The weapon's ID (e.g., 'longsword', 'dagger')
    Returns:
        Weapon data dictionary or None if not found.
    """
    weapons = load_weapons_data()
    for weapon in weapons:
        if weapon.get("id") == weapon_id:
            return weapon
    return None


def get_weapon_combat_stats(weapon_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract combat-relevant stats from weapon data.

    Args:
        weapon_data: Full weapon dictionary
    Returns:
        Dictionary with combat stats (KE, TE, VE, attack_time, damage, etc.)
    """
    return {
        "attack_time": weapon_data.get("attack_time", 5),
        "damage_min": weapon_data.get("damage_min", 1),
        "damage_max": weapon_data.get("damage_max", 6),
        "stp": weapon_data.get("stp", 10),
        "armor_penetration": weapon_data.get("armor_penetration", 0),
        "can_disarm": weapon_data.get("can_disarm", False),
        "can_break_weapon": weapon_data.get("can_break_weapon", False),
        "damage_types": weapon_data.get("damage_types", []),
        "damage_bonus_attributes": weapon_data.get("damage_bonus_attributes", []),
        "KE": weapon_data.get("KE", 0),
        "TE": weapon_data.get("TE", 0),
        "VE": weapon_data.get("VE", 0),
        "CE": weapon_data.get("CE", 0),  # For ranged weapons
        "size_category": weapon_data.get("size_category", 1),
        "wield_mode": weapon_data.get("wield_mode", "Egykezes"),
    }
