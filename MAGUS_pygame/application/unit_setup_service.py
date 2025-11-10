"""Unit Setup Service - Handles loading and initializing unit data.

Centralizes logic for extracting equipment, skills, and inventory from
character JSON files and preparing them for scenario configuration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from logger.logger import get_logger

if TYPE_CHECKING:
    from infrastructure.repositories import CharacterRepository

logger = get_logger(__name__)


class UnitSetupService:
    """Service for loading and initializing unit data from character files.
    
    Responsibilities:
    - Load character data with proper defaults
    - Extract equipment, skills, and inventory from character JSON
    - Provide consistent data structure for scenario configuration
    """
    
    def __init__(self, character_repo: "CharacterRepository"):
        """Initialize unit setup service.
        
        Args:
            character_repo: Character repository for loading character data
        """
        self.character_repo = character_repo
    
    def load_character_with_defaults(self, char_file: str) -> dict | None:
        """Load character data with equipment, skills, and inventory.
        
        Args:
            char_file: Character filename (e.g., "Warrior.json")
            
        Returns:
            Character data dictionary or None if not found
        """
        char_data = self.character_repo.load(char_file)
        if not char_data:
            logger.warning(f"Character file not found: {char_file}")
            return None
        
        # Ensure all expected keys exist with defaults
        if "Felszerelés" not in char_data:
            char_data["Felszerelés"] = {"items": []}
        if "Képzettségek" not in char_data:
            char_data["Képzettségek"] = []
        
        return char_data
    
    def extract_equipment_from_character(self, char_data: dict) -> dict[str, str]:
        """Extract equipment mapping from character data.
        
        Equipment in character JSON is typically stored as a list of items
        with slots. This converts it to a slot->item_id mapping.
        
        Args:
            char_data: Character data dictionary
            
        Returns:
            Dictionary mapping equipment slot names to item IDs
        """
        equipment_map: dict[str, str] = {}
        
        felszereles = char_data.get("Felszerelés", {})
        if isinstance(felszereles, dict):
            items = felszereles.get("items", [])
        elif isinstance(felszereles, list):
            items = felszereles
        else:
            return equipment_map
        
        for item in items:
            if not isinstance(item, dict):
                continue
            
            item_id = item.get("id")
            slot = item.get("slot")
            
            if item_id and slot:
                equipment_map[slot] = item_id
        
        logger.debug(f"Extracted {len(equipment_map)} equipment items from character")
        return equipment_map
    
    def extract_inventory_from_character(self, char_data: dict) -> dict[str, int]:
        """Extract inventory from character data.
        
        Args:
            char_data: Character data dictionary
            
        Returns:
            Dictionary mapping item IDs to quantities
        """
        inventory_map: dict[str, int] = {}
        
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
            
            # Only include items without specific slots (general inventory)
            if item_id and not item.get("slot"):
                inventory_map[item_id] = inventory_map.get(item_id, 0) + qty
        
        logger.debug(f"Extracted {len(inventory_map)} inventory items from character")
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
            'char_data': char_data,
            'equipment': self.extract_equipment_from_character(char_data),
            'inventory': self.extract_inventory_from_character(char_data),
            'skills': self.extract_skills_from_character(char_data),
        }
