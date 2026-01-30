"""
Conditions tab rendering for unit info popup - shows status effects and modifiers.
"""

import pygame

from .popup_style import PopupStyle


def draw_conditions(unit, screen: pygame.Surface, style: PopupStyle, x: int, y: int) -> int:
    """Draw conditions tab content. Returns new y offset."""
    # Header
    header = style.header_font.render("Conditions", True, style.color_header_conditions)
    screen.blit(header, (x, y))
    y += 30

    state_label, stamina_te, stamina_ve = _get_stamina_condition(unit)
    injury_label, injury_ke, injury_te, injury_ve, injury_ce = _get_injury_condition(unit)

    # Fatigue status line
    fatigue_text = style.text_font.render(f"Fatigue: {state_label}", True, (200, 200, 200))
    screen.blit(fatigue_text, (x + 10, y))
    y += 22

    # Injury status line
    injury_text = style.text_font.render(f"Injury: {injury_label}", True, (200, 200, 200))
    screen.blit(injury_text, (x + 10, y))
    y += 22

    # Combined modifiers summary
    mod_parts = []
    total_ke = injury_ke
    total_te = stamina_te + injury_te
    total_ve = stamina_ve + injury_ve
    total_ce = injury_ce

    if total_ke != 0:
        mod_parts.append(f"KÉ {total_ke}")
    if total_te != 0:
        mod_parts.append(f"TÉ {total_te}")
    if total_ve != 0:
        mod_parts.append(f"VÉ {total_ve}")
    if total_ce != 0:
        mod_parts.append(f"CÉ {total_ce}")

    mods_str = ", ".join(mod_parts) if mod_parts else "No penalties"
    mods_color = (220, 80, 80) if mod_parts else (150, 150, 150)
    mods_text = style.small_font.render(mods_str, True, mods_color)
    screen.blit(mods_text, (x + 30, y))
    y += 20

    return y


def _get_stamina_condition(unit) -> tuple[str, int, int]:
    """Return (state_label, te_mod, ve_mod) from unit stamina, or defaults."""
    if hasattr(unit, "stamina") and unit.stamina:
        # Show explicit Unconscious state when stamina is 0
        if unit.stamina.is_unconscious():
            return ("Unconscious", 0, 0)
        _, state = unit.stamina.get_state()
        mods = unit.stamina.get_combat_modifiers()
        return state.value, mods.te_mod, mods.ve_mod
    return ("None", 0, 0)


def _get_injury_condition(unit) -> tuple[str, int, int, int, int]:
    """Return (injury_label, ke_mod, te_mod, ve_mod, ce_mod) or defaults."""
    if hasattr(unit, "fp") and hasattr(unit, "ep"):
        from domain.mechanics.conditions.injury import (
            calculate_injury_condition,
            get_injury_modifiers,
        )

        injury = calculate_injury_condition(
            unit.fp.current,
            unit.fp.maximum,
            unit.ep.current,
            unit.ep.maximum,
        )
        mods = get_injury_modifiers(injury)
        return injury.value, mods.ke_mod, mods.te_mod, mods.ve_mod, mods.ce_mod
    return ("None", 0, 0, 0, 0)
