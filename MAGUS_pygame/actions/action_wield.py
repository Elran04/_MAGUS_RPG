"""
Action handling for changing weapon wield mode.
Allows toggling between 1-handed and 2-handed for variable weapons.
"""

from core.game_state import GameState
from systems.weapon_wielding import get_wielding_info, set_wielding_mode

# AP cost for changing wield mode - FREE (no cost)
AP_COST_CHANGE_WIELD = 0  # Free action to adjust grip


def can_change_wield_mode(state: GameState) -> bool:
    """
    Check if the active unit can change their weapon wield mode.

    Returns:
        True if unit has a variable weapon and can choose wielding mode
    """
    unit = state.active_unit

    if not unit.weapon:
        return False

    wield_info = get_wielding_info(unit)
    return wield_info["can_choose"]


def toggle_wield_mode(state: GameState) -> bool:
    """
    Toggle the active unit's weapon wield mode between 1-handed and 2-handed.

    Args:
        state: Current game state

    Returns:
        True if wield mode was changed successfully
    """
    unit = state.active_unit

    # Get current wield info
    wield_info = get_wielding_info(unit)

    if not wield_info["can_choose"]:
        forced_msg = " (forced 2-handed)" if wield_info["forced_two_handed"] else ""
        print(f"[WIELD] {unit.name} cannot change wield mode{forced_msg}")
        state.combat_message = f"Cannot change wield mode{forced_msg}"
        state.message_timer = 180
        return False

    # Toggle between modes
    current_mode = wield_info["mode"]
    new_mode = "2-handed" if current_mode == "1-handed" else "1-handed"

    # Set new mode
    if set_wielding_mode(unit, new_mode):
        # Get updated bonuses
        new_wield_info = get_wielding_info(unit)
        bonuses = new_wield_info["bonuses"]

        # Create message
        bonus_text = ""
        if new_mode == "2-handed" and any(bonuses.values()):
            bonus_parts = []
            if bonuses["KE"] > 0:
                bonus_parts.append(f"+{bonuses['KE']} KÉ")
            if bonuses["TE"] > 0:
                bonus_parts.append(f"+{bonuses['TE']} TÉ")
            if bonuses["VE"] > 0:
                bonus_parts.append(f"+{bonuses['VE']} VÉ")
            if bonus_parts:
                bonus_text = f" ({', '.join(bonus_parts)})"

        message = f"{unit.name} changed to {new_mode} wielding{bonus_text}"
        print(f"[WIELD] {message}")
        state.combat_message = message
        state.message_timer = 180

        return True

    return False


def get_wield_mode_display(state: GameState) -> str:
    """
    Get display string for current wield mode.

    Args:
        state: Current game state

    Returns:
        String describing current wield mode and options
    """
    unit = state.active_unit

    if not unit.weapon:
        return "No weapon equipped"

    wield_info = get_wielding_info(unit)

    if not wield_info["can_choose"]:
        if wield_info["forced_two_handed"]:
            return "2-handed (forced - need more Erő/Ügyesség)"
        else:
            weapon_mode = unit.weapon.get("wield_mode", "1-handed")
            return f"{weapon_mode} (fixed)"

    # Can choose
    current = wield_info["mode"]
    other = "2-handed" if current == "1-handed" else "1-handed"

    bonuses = wield_info["bonuses"]
    bonus_text = ""
    if current == "2-handed" and any(bonuses.values()):
        bonus_parts = []
        if bonuses["KE"] > 0:
            bonus_parts.append(f"+{bonuses['KE']} KÉ")
        if bonuses["TE"] > 0:
            bonus_parts.append(f"+{bonuses['TE']} TÉ")
        if bonuses["VE"] > 0:
            bonus_parts.append(f"+{bonuses['VE']} VÉ")
        if bonus_parts:
            bonus_text = f" ({', '.join(bonus_parts)})"

    return f"Current: {current}{bonus_text} | Click to change to {other}"
