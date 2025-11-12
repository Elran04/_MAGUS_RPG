"""Unit Setup Service - Loads inventory and skills for scenario setup."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from infrastructure.repositories import CharacterRepository

from logger.logger import get_logger

logger = get_logger(__name__)


class UnitSetupService:
    def __init__(self, character_repo: "CharacterRepository"):
        self.character_repo = character_repo

    def load_character_with_defaults(self, char_file: str) -> dict | None:
        char_data = self.character_repo.load(char_file)
        if not char_data:
            return None
        if "Felszerelés" not in char_data:
            char_data["Felszerelés"] = {"items": []}
        if "Képzettségek" not in char_data:
            char_data["Képzettségek"] = []
        return char_data

    def extract_inventory_from_character(self, char_data: dict) -> dict[str, int]:
        inventory_map: dict[str, int] = {}
        equipped_ids = set()
        equipment = char_data.get("equipment", {})
        if isinstance(equipment, dict):
            for value in equipment.values():
                if isinstance(value, list):
                    equipped_ids.update(value)
                elif isinstance(value, str):
                    equipped_ids.add(value)
        felszereles = char_data.get("Felszerelés", {})
        if isinstance(felszereles, dict):
            items = felszereles.get("items", [])
        elif isinstance(felszereles, list):
            items = felszereles
        else:
            return inventory_map
        for item in items:
            if not isinstance(item, dict):
                continue
            item_id = item.get("id")
            qty = item.get("qty", 1)
            if item_id and not item.get("slot") and item_id not in equipped_ids:
                inventory_map[item_id] = inventory_map.get(item_id, 0) + qty
        return inventory_map

    def extract_skills_from_character(self, char_data: dict) -> dict[str, int]:
        skills_map: dict[str, int] = {}
        kepzettsegek = char_data.get("Képzettségek", [])
        if not isinstance(kepzettsegek, list):
            return skills_map
        for skill in kepzettsegek:
            if not isinstance(skill, dict):
                continue
            skill_id = skill.get("id")
            if not skill_id:
                continue
            level = skill.get("Szint") or skill.get("%")
            if level is not None:
                try:
                    skills_map[skill_id] = int(level)
                except (ValueError, TypeError):
                    pass
        return skills_map

    def prepare_unit_data(self, char_file: str) -> dict | None:
        char_data = self.load_character_with_defaults(char_file)
        if not char_data:
            return None
        return {
            "char_data": char_data,
            "inventory": self.extract_inventory_from_character(char_data),
            "skills": self.extract_skills_from_character(char_data),
        }

    def extract_inventory_from_character(self, char_data: dict) -> dict[str, int]:
        """Extract inventory from character data, excluding equipped items."""
        inventory_map: dict[str, int] = {}

        # Get equipped item ids from equipment mapping (if present)
        equipped_ids = set()
        equipment = char_data.get("equipment", {})
        if isinstance(equipment, dict):
            for slot, value in equipment.items():
                if isinstance(value, list):
                    equipped_ids.update(value)
                elif isinstance(value, str):
                    equipped_ids.add(value)

        felszereles = char_data.get("Felszerelés", {})
        if isinstance(felszereles, dict):
            items = felszereles.get("items", [])
        elif isinstance(felszereles, list):
            items = felszereles
        else:
            return inventory_map

        for item in items:
            if not isinstance(item, dict):
                continue

            item_id = item.get("id")
            qty = item.get("qty", 1)

            # Only include items not equipped and without specific slots (general inventory)
            if item_id and not item.get("slot") and item_id not in equipped_ids:
                inventory_map[item_id] = inventory_map.get(item_id, 0) + qty

        logger.debug(
            f"Extracted {len(inventory_map)} inventory items from character (excluding equipped)"
        )
        return inventory_map

    def extract_skills_from_character(self, char_data: dict) -> dict[str, int]:
        """Extract skills from character data.

        Args:
            char_data: Character data dictionary

        Returns:
            Dictionary mapping skill IDs to skill levels/percentages
        """
        skills_map: dict[str, int] = {}

        kepzettsegek = char_data.get("Képzettségek", [])
        if not isinstance(kepzettsegek, list):
            return skills_map

        for skill in kepzettsegek:
            if not isinstance(skill, dict):
                continue

            skill_id = skill.get("id")
            if not skill_id:
                continue

            # Try to get level (Szint) first, then percentage (%)
            level = skill.get("Szint") or skill.get("%")
            if level is not None:
                try:
                    skills_map[skill_id] = int(level)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid skill level for {skill_id}: {level}")

        logger.debug(f"Extracted {len(skills_map)} skills from character")
        return skills_map

    def prepare_unit_data(self, char_file: str) -> dict | None:
        """Load character and extract all relevant data for unit setup.

        This is a convenience method that loads the character and extracts
        equipment, inventory, and skills in one call.

        Args:
            char_file: Character filename

        Returns:
            Dictionary with keys: 'char_data', 'equipment', 'inventory', 'skills'
            Returns None if character not found
        """
        char_data = self.load_character_with_defaults(char_file)
        if not char_data:
            return None

        return {
            "char_data": char_data,
            "equipment": {},
            "inventory": self.extract_inventory_from_character(char_data),
            "skills": self.extract_skills_from_character(char_data),
        }
