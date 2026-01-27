"""
Weapons tab rendering for unit info popup - shows equipped weapons and quick slots with stats.
"""

import pygame
from config import UI_TEXT

from .popup_style import PopupStyle


def draw_weapons(unit, screen: pygame.Surface, style: PopupStyle, x_left: int, x_right: int, y: int, context=None) -> int:
    """Draw weapons tab content with equipped weapons and quick slots. Returns new y offset."""
    # Helper to get equipment mapping
    equipment = {}
    if unit.character_data and "equipment" in unit.character_data:
        equipment = unit.character_data["equipment"]
    elif hasattr(unit, "equipment"):
        equipment = getattr(unit, "equipment", {})

    def get_item_name(item_id, is_armor: bool = False):
        if not item_id:
            return "(empty)"

        # Try repository first
        if context and hasattr(context, "equipment_repo"):
            repo = context.equipment_repo
            if repo:
                try:
                    weapon_data = repo.find_weapon_by_id(item_id)
                    if weapon_data and isinstance(weapon_data, dict):
                        return weapon_data.get("name", item_id)
                except Exception:
                    pass

        # Fallback: check if it's the main hand weapon object
        if unit.weapon and getattr(unit.weapon, "id", None) == item_id:
            return getattr(unit.weapon, "name", item_id)

        return str(item_id)

    def get_weapon_stats(item_id):
        """Get weapon damage stats if available."""
        if not item_id or not context or not hasattr(context, "equipment_repo"):
            return None

        try:
            weapon_data = context.equipment_repo.find_weapon_by_id(item_id)
            if weapon_data and isinstance(weapon_data, dict):
                damage_min = weapon_data.get("damage_min", 1)
                damage_max = weapon_data.get("damage_max", 6)
                return (damage_min, damage_max)
        except Exception:
            pass
        return None

    # Header
    header = style.header_font.render("Weapons", True, style.color_header_equipment)
    screen.blit(header, (x_left, y))
    y += 30

    # Main hand
    main_hand = equipment.get("main_hand", "")
    main_hand_name = get_item_name(main_hand)
    main_hand_text = style.text_font.render(f"Main Hand: {main_hand_name}", True, UI_TEXT)
    screen.blit(main_hand_text, (x_left + 10, y))
    y += 24

    # Main hand stats
    main_stats = get_weapon_stats(main_hand)
    if main_stats:
        stats_text = style.small_font.render(
            f"  Damage: {main_stats[0]}-{main_stats[1]}", True, (200, 200, 150)
        )
        screen.blit(stats_text, (x_left + 30, y))
        y += 20

    # Off hand
    off_hand = equipment.get("off_hand", "")
    off_hand_name = get_item_name(off_hand)
    off_hand_text = style.text_font.render(f"Off Hand: {off_hand_name}", True, UI_TEXT)
    screen.blit(off_hand_text, (x_left + 10, y))
    y += 24

    # Off hand stats
    off_stats = get_weapon_stats(off_hand)
    if off_stats:
        stats_text = style.small_font.render(
            f"  Damage: {off_stats[0]}-{off_stats[1]}", True, (200, 200, 150)
        )
        screen.blit(stats_text, (x_left + 30, y))
        y += 20

    # Quick weapons section
    y += 10
    quick_header = style.text_font.render("Quick Slots", True, style.color_header_equipment)
    screen.blit(quick_header, (x_left + 10, y))
    y += 24

    quick_slots = [
        ("weapon_quick_1", "Quick Weapon 1"),
        ("weapon_quick_2", "Quick Weapon 2"),
        ("weapon_quick_3", "Quick Weapon 3"),
        ("weapon_quick_4", "Quick Weapon 4"),
    ]

    for slot_key, slot_label in quick_slots:
        quick_weapon = equipment.get(slot_key, "")
        quick_name = get_item_name(quick_weapon)
        quick_text = style.small_font.render(f"{slot_label}: {quick_name}", True, UI_TEXT)
        screen.blit(quick_text, (x_left + 20, y))
        y += 20

        # Quick weapon stats
        quick_stats = get_weapon_stats(quick_weapon)
        if quick_stats:
            stats_text = style.small_font.render(
                f"  Damage: {quick_stats[0]}-{quick_stats[1]}", True, (200, 200, 150)
            )
            screen.blit(stats_text, (x_left + 40, y))
            y += 18

    # Quick access items
    y += 10
    qa_header = style.text_font.render("Quick Items", True, style.color_header_equipment)
    screen.blit(qa_header, (x_left + 10, y))
    y += 24

    qa1 = equipment.get("quick_access_1", "")
    qa1_name = get_item_name(qa1)
    qa1_text = style.small_font.render(f"Quick Item 1: {qa1_name}", True, UI_TEXT)
    screen.blit(qa1_text, (x_left + 20, y))
    y += 20

    qa2 = equipment.get("quick_access_2", "")
    qa2_name = get_item_name(qa2)
    qa2_text = style.small_font.render(f"Quick Item 2: {qa2_name}", True, UI_TEXT)
    screen.blit(qa2_text, (x_left + 20, y))
    y += 20

    return y
