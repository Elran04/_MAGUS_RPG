"""
Unit Factory - Creates Unit entities from character data.
"""

from typing import Optional
import uuid

from domain.entities import Unit
from domain.value_objects import Position, CombatStats, ResourcePool, Attributes, Facing
from infrastructure.repositories import CharacterRepository, EquipmentRepository
from logger.logger import get_logger

logger = get_logger(__name__)


class UnitFactory:
    """
    Factory for creating Unit entities from character data.
    
    Handles:
    - Loading character JSON
    - Extracting combat stats and attributes
    - Loading weapon modifiers
    - Creating properly initialized Unit instances
    """
    
    def __init__(
        self,
        character_repo: CharacterRepository,
        equipment_repo: EquipmentRepository
    ):
        self.character_repo = character_repo
        self.equipment_repo = equipment_repo
    
    def create_unit(
        self,
        character_filename: str,
        position: Position,
        facing: Facing = Facing(0)
    ) -> Optional[Unit]:
        """
        Create a unit from a character file.
        
        Args:
            character_filename: Character JSON filename
            position: Starting position on the hex grid
            facing: Starting facing direction
            
        Returns:
            Unit instance or None if creation fails
        """
        # Load character data
        char_data = self.character_repo.load(character_filename)
        if char_data is None:
            logger.error(f"Cannot create unit: character file not found: {character_filename}")
            return None
        
        try:
            # Extract basic info
            name = char_data.get("Név", character_filename.replace('.json', ''))
            unit_id = str(uuid.uuid4())[:8]  # Short unique ID
            
            # Extract attributes
            attributes_data = char_data.get("Tulajdonságok", {})
            attributes = Attributes.from_dict(attributes_data)
            
            # Extract combat stats
            combat_data = char_data.get("Harci értékek", {})
            combat_stats = CombatStats(
                KE=combat_data.get("KÉ", 0),
                TE=combat_data.get("TÉ", 0),
                VE=combat_data.get("VÉ", 0),
                CE=combat_data.get("CÉ", 0),
            )
            
            # Create resource pools
            fp_max = combat_data.get("FP", 20)
            ep_max = combat_data.get("ÉP", 10)
            fp = ResourcePool(current=fp_max, maximum=fp_max)
            ep = ResourcePool(current=ep_max, maximum=ep_max)
            
            # Create unit
            unit = Unit(
                id=unit_id,
                name=name,
                position=position,
                facing=facing,
                fp=fp,
                ep=ep,
                combat_stats=combat_stats,
                attributes=attributes,
                character_data=char_data
            )
            
            # Load weapon if equipped
            self._equip_primary_weapon(unit, char_data)
            
            logger.info(f"Created unit: {name} at {position}")
            return unit
            
        except Exception:
            logger.exception(f"Failed to create unit from {character_filename}")
            return None
    
    def _equip_primary_weapon(self, unit: Unit, char_data: dict) -> None:
        """Extract and equip the primary weapon from equipment list."""
        equipment_data = char_data.get("Felszerelés")
        
        # Handle different equipment formats
        items = []
        if isinstance(equipment_data, dict):
            items = equipment_data.get("items", [])
        elif isinstance(equipment_data, list):
            items = equipment_data
        
        # Find first weapon
        for item in items:
            if isinstance(item, dict):
                category = item.get("category", "")
                item_id = item.get("id", "")
                
                if category == "weapons_and_shields":
                    # Load weapon data
                    weapon_data = self.equipment_repo.find_weapon_by_id(item_id)
                    if weapon_data:
                        unit.weapon_stats = self._extract_weapon_stats(weapon_data)
                        logger.debug(f"Equipped {item_id} to {unit.name}")
                        return
        
        logger.debug(f"No weapon found in equipment for {unit.name}")
    
    def _extract_weapon_stats(self, weapon_data: dict) -> dict:
        """Extract relevant weapon stats for combat."""
        return {
            "id": weapon_data.get("id", ""),
            "name": weapon_data.get("name", "Unknown"),
            "KE": weapon_data.get("KE", 0),
            "TE": weapon_data.get("TE", 0),
            "VE": weapon_data.get("VE", 0),
            "attack_time": weapon_data.get("attack_time", 5),
            "damage": weapon_data.get("damage", "1d6"),
            "damage_min": weapon_data.get("damage_min", 1),
            "damage_max": weapon_data.get("damage_max", 6),
            "armor_penetration": weapon_data.get("armor_penetration", 0),
            "size_category": weapon_data.get("size_category", 1),
        }
