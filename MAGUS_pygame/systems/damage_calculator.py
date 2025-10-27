"""
Damage calculation system for MAGUS combat.
Handles attribute-based damage bonuses and damage roll calculations.
"""
from __future__ import annotations
from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from core.unit_manager import Unit
    from core.game_state import GameState


def get_attribute_value(unit: "Unit", attribute_name: str) -> int:
    """
    Get the value of a specific attribute from the unit's character data.
    Handles case-insensitive attribute name matching.
    
    Args:
        unit: The unit whose attribute to retrieve
        attribute_name: Name of the attribute (e.g., "erő", "ügyesség")
    
    Returns:
        Attribute value, or 0 if not found
    """
    if not hasattr(unit, 'character_data') or not unit.character_data:
        return 0
    
    properties = unit.character_data.get('Tulajdonságok', {})
    
    # Try exact match first
    if attribute_name in properties:
        attr_data = properties[attribute_name]
        # If it's a dict with 'value' or 'aktuális', use that
        if isinstance(attr_data, dict):
            return attr_data.get('aktuális', attr_data.get('value', 0))
        # Otherwise it's a direct value
        return attr_data
    
    # Try case-insensitive match
    lower_attr_name = attribute_name.lower()
    for key, value in properties.items():
        if key.lower() == lower_attr_name:
            if isinstance(value, dict):
                return value.get('aktuális', value.get('value', 0))
            return value
    
    print(f"[DAMAGE CALC] Warning: Attribute '{attribute_name}' not found for {unit.name}")
    return 0


def calculate_attribute_damage_bonus(unit: "Unit") -> int:
    """
    Calculate total damage bonus from attributes based on equipped weapon.
    
    For each attribute listed in weapon's damage_bonus_attributes:
    - If attribute value > 15: bonus = (value - 15)
    - If attribute value <= 15: no bonus
    
    Args:
        unit: The unit whose damage bonus to calculate
    
    Returns:
        Total damage bonus from all relevant attributes
    """
    if not unit.weapon:
        return 0
    
    damage_bonus_attrs = unit.weapon.get('damage_bonus_attributes', [])
    if not damage_bonus_attrs:
        return 0
    
    total_bonus = 0
    bonus_breakdown = []
    
    for attr_name in damage_bonus_attrs:
        attr_value = get_attribute_value(unit, attr_name)
        
        if attr_value > 15:
            bonus = attr_value - 15
            total_bonus += bonus
            bonus_breakdown.append(f"{attr_name}={attr_value} (+{bonus})")
        else:
            bonus_breakdown.append(f"{attr_name}={attr_value} (+0)")
    
    print(f"[DAMAGE CALC] {unit.name} attribute bonuses: {', '.join(bonus_breakdown)} = Total +{total_bonus}")
    
    return total_bonus


def calculate_damage(unit: 'Unit', base_damage: int, state: 'GameState' = None) -> Dict[str, any]:
    """
    Calculate final damage including attribute bonuses and charge multiplier.
    
    Args:
        unit: The attacking unit
        base_damage: Base damage rolled (from weapon's damage_min to damage_max)
        state: Optional game state for charge multiplier
    
    Returns:
        Dict with:
        - 'final_damage': int - Total damage after bonuses and multipliers
        - 'base_damage': int - Original rolled damage
        - 'attribute_bonus': int - Bonus from attributes
        - 'charge_multiplier': int - Damage multiplier from charge (if applicable)
    """
    attribute_bonus = calculate_attribute_damage_bonus(unit)
    damage_with_bonus = base_damage + attribute_bonus
    
    # Apply charge damage multiplier if active
    charge_multiplier = 1
    if state and hasattr(state, 'charge_damage_multiplier'):
        charge_multiplier = state.charge_damage_multiplier
    
    final_damage = damage_with_bonus * charge_multiplier
    
    print(f"[DAMAGE CALC] {unit.name}: Base={base_damage}, Attr Bonus={attribute_bonus}, Multiplier=x{charge_multiplier}, Final={final_damage}")
    
    return {
        'final_damage': final_damage,
        'base_damage': base_damage,
        'attribute_bonus': attribute_bonus,
        'charge_multiplier': charge_multiplier
    }
