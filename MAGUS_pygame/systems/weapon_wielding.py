"""
Weapon wielding system for handling variable wield mode weapons.

"Változó" (Variable) wield mode allows weapons to be wielded in either 1-handed or 2-handed mode
depending on the wielder's attributes (Erő and Ügyesség).

Rules:
- If unit has Erő >= variable_strength_req AND Ügyesség >= variable_dex_req:
  - Can choose 1-handed or 2-handed wielding
  - If choosing 2-handed: gains bonus KÉ, TÉ, VÉ from weapon
- If unit doesn't meet both requirements:
  - Must wield 2-handed
  - No bonus stats
"""
from __future__ import annotations
from typing import Dict, Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.unit_manager import Unit


def get_attribute_value(unit: "Unit", attribute_name: str) -> int:
    """
    Get the value of a specific attribute from the unit's character data.
    Handles case-insensitive attribute name matching.
    
    Args:
        unit: The unit whose attribute to retrieve
        attribute_name: Name of the attribute (e.g., "Erő", "Ügyesség")
    
    Returns:
        Attribute value, or 0 if not found
    """
    if not hasattr(unit, 'character_data') or not unit.character_data:
        return 0
    
    properties = unit.character_data.get('Tulajdonságok', {})
    
    # Try exact match first
    if attribute_name in properties:
        attr_data = properties[attribute_name]
        if isinstance(attr_data, dict):
            return attr_data.get('value', 0)
        return attr_data
    
    # Try case-insensitive match
    for key, value in properties.items():
        if key.lower() == attribute_name.lower():
            if isinstance(value, dict):
                return value.get('value', 0)
            return value
    
    return 0


def can_wield_one_handed(unit: "Unit", weapon: Dict) -> bool:
    """
    Check if unit meets attribute requirements to wield a variable weapon 1-handed.
    
    Args:
        unit: The unit attempting to wield the weapon
        weapon: Weapon data dictionary
    
    Returns:
        True if unit can wield 1-handed, False if must use 2-handed
    """
    if weapon.get('wield_mode') != 'Változó':
        return False
    
    str_req = weapon.get('variable_strength_req', 0)
    dex_req = weapon.get('variable_dex_req', 0)
    
    unit_strength = get_attribute_value(unit, 'Erő')
    unit_dexterity = get_attribute_value(unit, 'Ügyesség')
    
    can_wield = unit_strength >= str_req and unit_dexterity >= dex_req
    
    return can_wield


def has_variable_weapon(unit: "Unit") -> bool:
    """Return True if the unit currently wields a weapon with 'Változó' wield mode."""
    return bool(getattr(unit, "weapon", None)) and unit.weapon.get("wield_mode") == "Változó"


def get_wielding_mode(unit: "Unit", weapon: Dict) -> str:
    """
    Determine the wielding mode for a weapon based on unit's attributes and preference.
    
    For variable weapons:
    - If meets requirements: uses player's preference (defaults to 1-handed)
    - If doesn't meet requirements: forced 2-handed
    
    Args:
        unit: The unit wielding the weapon
        weapon: Weapon data dictionary
    
    Returns:
        "1-handed" or "2-handed"
    """
    wield_mode = weapon.get('wield_mode', '1-handed')
    
    if wield_mode == 'Változó':
        if can_wield_one_handed(unit, weapon):
            # Player can choose - check preference, default to 1-handed
            if hasattr(unit, 'wielding_mode_preference') and unit.wielding_mode_preference:
                return unit.wielding_mode_preference
            return "1-handed"
        else:
            # Forced 2-handed
            return "2-handed"
    
    # For non-variable weapons, use the wield_mode directly
    return wield_mode


def apply_two_handed_bonuses(unit: "Unit", weapon: Dict, wielding_two_handed: bool) -> Dict[str, int]:
    """
    Calculate combat stat bonuses when wielding a variable weapon 2-handed.
    
    Only applies if:
    1. Weapon is variable mode
    2. Unit meets attribute requirements (can wield 1-handed)
    3. Unit chooses to wield 2-handed anyway
    
    Args:
        unit: The unit wielding the weapon
        weapon: Weapon data dictionary
        wielding_two_handed: Whether unit is wielding 2-handed
    
    Returns:
        Dictionary with bonus values: {'KE': X, 'TE': Y, 'VE': Z}
    """
    bonuses = {'KE': 0, 'TE': 0, 'VE': 0}
    
    if weapon.get('wield_mode') != 'Változó':
        return bonuses
    
    # Only grant bonuses if unit CAN wield 1-handed but CHOOSES 2-handed
    if not can_wield_one_handed(unit, weapon):
        return bonuses
    
    if not wielding_two_handed:
        return bonuses
    
    # Apply bonuses
    bonuses['KE'] = weapon.get('variable_bonus_KE', 0)
    bonuses['TE'] = weapon.get('variable_bonus_TE', 0)
    bonuses['VE'] = weapon.get('variable_bonus_VE', 0)
    
    return bonuses


def get_wielding_info(unit: "Unit", weapon: Optional[Dict] = None) -> Dict:
    """
    Get complete wielding information for a unit's weapon.
    
    Args:
        unit: The unit to check
        weapon: Optional weapon dict, uses unit.weapon if not provided
    
    Returns:
        Dictionary with:
        - 'mode': "1-handed" or "2-handed"
        - 'can_choose': bool (can player choose wielding mode)
        - 'bonuses': dict with KE/TE/VE bonuses if wielding 2-handed
        - 'forced_two_handed': bool (must use 2-handed)
    """
    if weapon is None:
        weapon = unit.weapon
    
    if not weapon:
        return {
            'mode': '1-handed',
            'can_choose': False,
            'bonuses': {'KE': 0, 'TE': 0, 'VE': 0},
            'forced_two_handed': False
        }
    
    wield_mode = weapon.get('wield_mode', '1-handed')
    
    if wield_mode != 'Változó':
        # Non-variable weapon
        return {
            'mode': wield_mode,
            'can_choose': False,
            'bonuses': {'KE': 0, 'TE': 0, 'VE': 0},
            'forced_two_handed': wield_mode == '2-handed'
        }
    
    # Variable weapon
    can_choose = can_wield_one_handed(unit, weapon)
    
    # Get current wielding mode from unit preference or default
    current_mode = get_wielding_mode(unit, weapon)
    
    bonuses = {'KE': 0, 'TE': 0, 'VE': 0}
    if current_mode == "2-handed" and can_choose:
        bonuses = apply_two_handed_bonuses(unit, weapon, True)
    
    return {
        'mode': current_mode,
        'can_choose': can_choose,
        'bonuses': bonuses,
        'forced_two_handed': not can_choose
    }


def set_wielding_mode(unit: "Unit", mode: str) -> bool:
    """
    Set the wielding mode preference for a unit's variable weapon.
    
    Args:
        unit: The unit to update
        mode: "1-handed" or "2-handed"
    
    Returns:
        True if mode was set successfully, False if not allowed
    """
    if not unit.weapon or unit.weapon.get('wield_mode') != 'Változó':
        return False
    
    if mode == "1-handed" and not can_wield_one_handed(unit, unit.weapon):
        return False
    
    unit.wielding_mode_preference = mode
    
    # Recalculate combat stats with new wielding mode
    # This would trigger a recalculation of bonuses
    return True
