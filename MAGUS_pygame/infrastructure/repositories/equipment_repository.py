"""
Equipment Repository - Handles loading weapon and equipment data.
"""

import json

from config import get_equipment_json_path
from logger.logger import get_logger

logger = get_logger(__name__)


class EquipmentRepository:
    """Repository for equipment data access."""

    def __init__(self):
        self._weapons_cache: list[dict] | None = None
        self._armor_cache: list[dict] | None = None

    def load_weapons(self) -> list[dict]:
        """Load all weapon data."""
        if self._weapons_cache is not None:
            return self._weapons_cache

        try:
            path = get_equipment_json_path("weapons_and_shields.json")
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
                self._weapons_cache = data
                logger.info(f"Loaded {len(data)} weapons")
                return data
        except Exception:
            logger.exception("Failed to load weapons data")
            return []

    def find_weapon_by_id(self, weapon_id: str) -> dict | None:
        """
        Find a weapon by its ID.

        Args:
            weapon_id: Weapon identifier

        Returns:
            Weapon data dict or None
        """
        weapons = self.load_weapons()
        for weapon in weapons:
            if weapon.get("id") == weapon_id:
                return weapon

        logger.warning(f"Weapon not found: {weapon_id}")
        return None

    def load_armor(self) -> list[dict]:
        """Load all armor data."""
        if self._armor_cache is not None:
            return self._armor_cache

        try:
            path = get_equipment_json_path("armor.json")
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
                self._armor_cache = data
                logger.info(f"Loaded {len(data)} armor pieces")
                return data
        except Exception:
            logger.exception("Failed to load armor data")
            return []

    def find_armor_by_id(self, armor_id: str) -> dict | None:
        """Find an armor piece by ID."""
        armor_list = self.load_armor()
        for armor in armor_list:
            if armor.get("id") == armor_id:
                return armor

        logger.warning(f"Armor not found: {armor_id}")
        return None

    def clear_cache(self) -> None:
        """Clear equipment cache."""
        self._weapons_cache = None
        self._armor_cache = None
        logger.debug("Equipment cache cleared")
