"""
Stats tab rendering for unit info popup - shows health, combat stats, and weapon info.
"""

import pygame
from config import UI_BORDER, UI_TEXT

from .popup_style import PopupStyle


def draw_health_section(unit, screen: pygame.Surface, style: PopupStyle, x: int, y: int) -> int:
    """Draw FP/ÉP section. Returns new y offset."""
    # Header
    header = style.header_font.render("Health", True, style.color_header_health)
    screen.blit(header, (x, y))
    y += 30

    # FP (Fatigue Points)
    fp_current = unit.fp.current
    fp_max = unit.fp.maximum
    fp_text = style.text_font.render(f"FP: {fp_current} / {fp_max}", True, UI_TEXT)
    screen.blit(fp_text, (x + 10, y))

    # FP bar
    bar_width = style.health_bar_width
    bar_height = style.health_bar_height
    bar_x = x + style.health_bar_x_offset
    bar_y = y + style.health_bar_y_adjust

    # Background bar
    pygame.draw.rect(
        screen, style.bar_bg, (bar_x, bar_y, bar_width, bar_height), border_radius=5
    )

    # Fill bar (blue for FP)
    if fp_max > 0:
        fill_width = int((fp_current / fp_max) * bar_width)
        pygame.draw.rect(
            screen, style.fp_fill, (bar_x, bar_y, fill_width, bar_height), border_radius=5
        )

    pygame.draw.rect(
        screen, UI_BORDER, (bar_x, bar_y, bar_width, bar_height), width=2, border_radius=5
    )
    y += 30

    # ÉP (Health Points)
    ep_current = unit.ep.current
    ep_max = unit.ep.maximum
    ep_text = style.text_font.render(f"ÉP: {ep_current} / {ep_max}", True, UI_TEXT)
    screen.blit(ep_text, (x + 10, y))

    # ÉP bar
    pygame.draw.rect(
        screen,
        style.bar_bg,
        (bar_x, bar_y + style.health_ep_bar_delta_y, bar_width, bar_height),
        border_radius=5,
    )

    # Fill bar (red for ÉP)
    if ep_max > 0:
        fill_width = int((ep_current / ep_max) * bar_width)
        pygame.draw.rect(
            screen,
            style.ep_fill,
            (bar_x, bar_y + style.health_ep_bar_delta_y, fill_width, bar_height),
            border_radius=5,
        )

    pygame.draw.rect(
        screen,
        UI_BORDER,
        (bar_x, bar_y + style.health_ep_bar_delta_y, bar_width, bar_height),
        width=2,
        border_radius=5,
    )
    y += 35

    return y


def draw_combat_stats(unit, screen: pygame.Surface, style: PopupStyle, x: int, y: int, context=None) -> int:
    """Draw combat statistics with breakdown. Returns new y offset."""
    # Header
    header = style.header_font.render("Combat Stats", True, style.color_header_combat)
    screen.blit(header, (x, y))
    y += 30

    # Get base stats from unit
    base_ke = unit.combat_stats.KE
    base_te = unit.combat_stats.TE
    base_ve = unit.combat_stats.VE
    base_ce = unit.combat_stats.CE

    # Get weapon modifiers if weapon equipped
    weapon_ke = 0
    weapon_te = 0
    weapon_ve = 0

    if unit.weapon:
        weapon_ke = unit.weapon.ke_modifier
        weapon_te = unit.weapon.te_modifier
        weapon_ve = unit.weapon.ve_modifier

    # Get shield modifiers if shield equipped
    shield_ke = 0
    shield_te = 0
    shield_ve = 0

    if context and hasattr(context, "equipment_repo"):
        equipment = {}
        if unit.character_data and "equipment" in unit.character_data:
            equipment = unit.character_data["equipment"]

        off_hand = equipment.get("off_hand", "")
        if off_hand:
            shield_data = context.equipment_repo.find_weapon_by_id(off_hand)
            if shield_data:
                shield_ke = shield_data.get("KE", 0)
                shield_te = shield_data.get("TE", 0)
                shield_ve = shield_data.get("VE", 0)

    # Condition modifiers (stamina + injury penalties)
    _, stamina_te, stamina_ve = _get_stamina_condition(unit)
    _, injury_ke, injury_te, injury_ve, injury_ce = _get_injury_condition(unit)

    cond_ke = injury_ke
    cond_te = stamina_te + injury_te
    cond_ve = stamina_ve + injury_ve
    cond_ce = injury_ce

    # Calculate final values
    final_ke = base_ke + weapon_ke + shield_ke + cond_ke
    final_te = base_te + weapon_te + shield_te + cond_te
    final_ve = base_ve + weapon_ve + shield_ve + cond_ve
    final_ce = base_ce + cond_ce

    # Define stats with breakdown
    stats = [
        ("KÉ", base_ke, weapon_ke, shield_ke, cond_ke, final_ke),
        ("TÉ", base_te, weapon_te, shield_te, cond_te, final_te),
        ("VÉ", base_ve, weapon_ve, shield_ve, cond_ve, final_ve),
        ("CÉ", base_ce, 0, 0, cond_ce, final_ce),
    ]

    # Draw each stat with breakdown
    for i, (stat_name, base_val, weapon_val, shield_val, cond_val, final_val) in enumerate(stats):
        stat_y = y + (i * style.stat_row_height)

        # Build prefix parts
        prefix_parts = [f"{stat_name}: {base_val}"]
        if weapon_val != 0:
            prefix_parts.append(f"+ {weapon_val}")
        if shield_val != 0:
            prefix_parts.append(f"+ {shield_val}")
        prefix = " ".join(prefix_parts)

        base_color = (200, 220, 255) if (weapon_val or shield_val) else (200, 200, 200)
        prefix_surface = style.text_font.render(prefix, True, base_color)
        screen.blit(prefix_surface, (x + 10, stat_y))
        offset_x = x + 10 + prefix_surface.get_width()

        # Condition modifier in red (if any)
        if cond_val != 0:
            cond_surface = style.text_font.render(f" - {abs(cond_val)}", True, (220, 80, 80))
            screen.blit(cond_surface, (offset_x + 4, stat_y))
            offset_x += cond_surface.get_width() + 4

        # Final value
        final_surface = style.text_font.render(f" = {final_val}", True, (220, 220, 220))
        screen.blit(final_surface, (offset_x + 8, stat_y))

    y += style.stat_row_height * len(stats) + style.line_gap
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
        from domain.mechanics.injury import calculate_injury_condition, get_injury_modifiers

        injury = calculate_injury_condition(
            unit.fp.current,
            unit.fp.maximum,
            unit.ep.current,
            unit.ep.maximum,
        )
        mods = get_injury_modifiers(injury)
        return injury.value, mods.ke_mod, mods.te_mod, mods.ve_mod, mods.ce_mod
    return ("None", 0, 0, 0, 0)
