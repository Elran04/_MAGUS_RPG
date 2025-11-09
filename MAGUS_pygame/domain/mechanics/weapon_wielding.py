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

from dataclasses import dataclass
from enum import Enum

from ..entities import Unit, Weapon


class WieldMode(str, Enum):
    """Weapon wielding modes."""

    ONE_HANDED = "1-handed"
    TWO_HANDED = "2-handed"
    VARIABLE = "Változó"  # Hungarian: Variable/Changeable


@dataclass(frozen=True)
class WieldingBonuses:
    """Combat stat bonuses from 2-handed wielding of variable weapons."""

    ke_bonus: int = 0
    te_bonus: int = 0
    ve_bonus: int = 0

    def is_active(self) -> bool:
        """Check if any bonuses are active."""
        return self.ke_bonus != 0 or self.te_bonus != 0 or self.ve_bonus != 0


@dataclass(frozen=True)
class WieldingInfo:
    """Complete information about how a weapon is being wielded."""

    mode: WieldMode
    can_choose: bool  # Can player choose wielding mode?
    bonuses: WieldingBonuses
    forced_two_handed: bool  # Must use 2-handed?
    meets_requirements: bool  # Meets attribute requirements?


def can_wield_one_handed(unit: Unit, weapon: Weapon, strength_req: int, dex_req: int) -> bool:
    """
    Check if unit meets attribute requirements to wield a variable weapon 1-handed.

    Args:
        unit: The unit attempting to wield the weapon
        weapon: The weapon entity
        strength_req: Erő (strength) requirement for 1-handed wielding
        dex_req: Ügyesség (dexterity) requirement for 1-handed wielding

    Returns:
        True if unit can wield 1-handed, False if must use 2-handed
    """
    if not unit.attributes:
        return False

    return unit.attributes.strength >= strength_req and unit.attributes.dexterity >= dex_req


def calculate_wielding_bonuses(
    can_wield_one_handed: bool,
    wielding_two_handed: bool,
    ke_bonus: int = 0,
    te_bonus: int = 0,
    ve_bonus: int = 0,
) -> WieldingBonuses:
    """
    Calculate combat stat bonuses when wielding a variable weapon 2-handed.

    Bonuses only apply if:
    1. Unit meets attribute requirements (can wield 1-handed)
    2. Unit chooses to wield 2-handed anyway

    Args:
        can_wield_one_handed: Whether unit meets requirements
        wielding_two_handed: Whether unit is wielding 2-handed
        ke_bonus: Initiative bonus for 2-handed wielding
        te_bonus: Attack bonus for 2-handed wielding
        ve_bonus: Defense bonus for 2-handed wielding

    Returns:
        WieldingBonuses with appropriate values
    """
    if can_wield_one_handed and wielding_two_handed:
        return WieldingBonuses(ke_bonus=ke_bonus, te_bonus=te_bonus, ve_bonus=ve_bonus)
    return WieldingBonuses()


def get_wielding_mode(
    unit: Unit,
    weapon: Weapon,
    wield_mode: str,
    strength_req: int,
    dex_req: int,
    preference: WieldMode | None = None,
) -> WieldMode:
    """
    Determine the wielding mode for a weapon based on unit's attributes and preference.

    For variable weapons:
    - If meets requirements: uses player's preference (defaults to 1-handed)
    - If doesn't meet requirements: forced 2-handed

    Args:
        unit: The unit wielding the weapon
        weapon: The weapon entity
        wield_mode: Weapon's base wield mode
        strength_req: Strength requirement for 1-handed
        dex_req: Dexterity requirement for 1-handed
        preference: Player's wielding preference (optional)

    Returns:
        WieldMode enum value
    """
    # Handle variable weapons
    if wield_mode == WieldMode.VARIABLE:
        if can_wield_one_handed(unit, weapon, strength_req, dex_req):
            # Player can choose - use preference or default to 1-handed
            return preference if preference else WieldMode.ONE_HANDED
        else:
            # Forced 2-handed
            return WieldMode.TWO_HANDED

    # Non-variable weapons
    try:
        return WieldMode(wield_mode)
    except ValueError:
        # Default to 1-handed if unknown mode
        return WieldMode.ONE_HANDED


def get_wielding_info(
    unit: Unit,
    weapon: Weapon,
    wield_mode: str,
    strength_req: int = 0,
    dex_req: int = 0,
    ke_bonus: int = 0,
    te_bonus: int = 0,
    ve_bonus: int = 0,
    preference: WieldMode | None = None,
) -> WieldingInfo:
    """
    Get complete wielding information for a unit's weapon.

    Args:
        unit: The unit wielding the weapon
        weapon: The weapon entity
        wield_mode: Base wield mode from weapon data
        strength_req: Erő requirement for 1-handed (for variable weapons)
        dex_req: Ügyesség requirement for 1-handed (for variable weapons)
        ke_bonus: KÉ bonus for 2-handed wielding (for variable weapons)
        te_bonus: TÉ bonus for 2-handed wielding (for variable weapons)
        ve_bonus: VÉ bonus for 2-handed wielding (for variable weapons)
        preference: Player's wielding preference

    Returns:
        WieldingInfo with complete wielding details

    Example:
        >>> info = get_wielding_info(
        ...     unit=warrior,
        ...     weapon=longsword,
        ...     wield_mode="Változó",
        ...     strength_req=16,
        ...     dex_req=13,
        ...     te_bonus=5,
        ...     ve_bonus=3
        ... )
        >>> if info.bonuses.is_active():
        ...     print(f"Bonus TÉ: +{info.bonuses.te_bonus}")
    """
    # Non-variable weapons
    if wield_mode != WieldMode.VARIABLE:
        mode = (
            WieldMode(wield_mode)
            if wield_mode in [m.value for m in WieldMode]
            else WieldMode.ONE_HANDED
        )
        return WieldingInfo(
            mode=mode,
            can_choose=False,
            bonuses=WieldingBonuses(),
            forced_two_handed=(mode == WieldMode.TWO_HANDED),
            meets_requirements=True,
        )

    # Variable weapon
    meets_reqs = can_wield_one_handed(unit, weapon, strength_req, dex_req)
    current_mode = get_wielding_mode(unit, weapon, wield_mode, strength_req, dex_req, preference)

    # Calculate bonuses
    bonuses = calculate_wielding_bonuses(
        can_wield_one_handed=meets_reqs,
        wielding_two_handed=(current_mode == WieldMode.TWO_HANDED),
        ke_bonus=ke_bonus,
        te_bonus=te_bonus,
        ve_bonus=ve_bonus,
    )

    return WieldingInfo(
        mode=current_mode,
        can_choose=meets_reqs,
        bonuses=bonuses,
        forced_two_handed=not meets_reqs,
        meets_requirements=meets_reqs,
    )


def validate_wielding_mode_change(
    unit: Unit,
    weapon: Weapon,
    wield_mode: str,
    new_mode: WieldMode,
    strength_req: int,
    dex_req: int,
) -> bool:
    """
    Validate if a wielding mode change is allowed.

    Args:
        unit: The unit wielding the weapon
        weapon: The weapon entity
        wield_mode: Weapon's base wield mode
        new_mode: Desired wielding mode
        strength_req: Strength requirement for 1-handed
        dex_req: Dexterity requirement for 1-handed

    Returns:
        True if mode change is valid, False otherwise
    """
    # Can't change non-variable weapons
    if wield_mode != WieldMode.VARIABLE:
        return False

    # Can't wield 1-handed if don't meet requirements
    if new_mode == WieldMode.ONE_HANDED:
        return can_wield_one_handed(unit, weapon, strength_req, dex_req)

    # Can always wield 2-handed
    return True
