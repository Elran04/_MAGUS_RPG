"""Weapon type and slot constants, and utility functions for weapon type checks."""
from enum import Enum, auto
from typing import Any

def _normalize(val: str | None) -> str:
    return (val or "").strip().lower()

class Slot(str, Enum):
    MAIN_HAND = "main_hand"
    OFF_HAND = "off_hand"
    ARMOR = "armor"
    WEAPON_QUICK_1 = "weapon_quick_1"
    WEAPON_QUICK_2 = "weapon_quick_2"
    QUICK_ACCESS_1 = "quick_access_1"
    QUICK_ACCESS_2 = "quick_access_2"

class WeaponType(str, Enum):
    ONE_HANDED = "one-handed"
    TWO_HANDED = "two-handed"
    VARIABLE = "variable"
    RANGED = "ranged"
    SHIELD = "shield"

# Weapon type check utilities

def is_one_handed_weapon(weapon: dict[str, Any], off_hand_present: bool = False) -> bool:
    mode = _normalize(weapon.get("wield_mode"))
    if mode in ["egykezes", "one-handed", "1h"]:
        return True
    if mode in ["változó", "variable"] and off_hand_present:
        return True
    return False

def is_two_handed_weapon(weapon: dict[str, Any], off_hand_present: bool = False) -> bool:
    mode = _normalize(weapon.get("wield_mode"))
    if mode in ["kétkezes", "two-handed", "2h"]:
        return True
    if mode in ["változó", "variable"] and not off_hand_present:
        return True
    return False

def is_ranged_weapon(weapon: dict[str, Any]) -> bool:
    wtype = _normalize(weapon.get("type"))
    return wtype in ["távolsági", "ranged", "íjászfegyver"]

def is_shield(weapon: dict[str, Any]) -> bool:
    wtype = _normalize(weapon.get("type"))
    return wtype in ["pajzs", "shield"]
