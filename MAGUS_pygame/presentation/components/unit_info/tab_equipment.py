"""
Armor tab rendering for unit info popup - shows equipped armor pieces.
"""

import pygame
from config import UI_TEXT

from .popup_style import PopupStyle


def draw_equipment(unit, screen: pygame.Surface, style: PopupStyle, x_left: int, x_right: int, y: int, context=None) -> int:
    """Draw armor tab content. Returns new y offset."""
    # Helper to get equipment mapping
    equipment = {}
    if unit.character_data and "equipment" in unit.character_data:
        equipment = unit.character_data["equipment"]
    elif hasattr(unit, "equipment"):
        equipment = getattr(unit, "equipment", {})

    def get_item_name(item_id, is_armor: bool = True):
        if not item_id:
            return "(empty)"

        # Try repository first
        if context and hasattr(context, "equipment_repo"):
            repo = context.equipment_repo
            if repo:
                try:
                    armor_data = repo.find_armor_by_id(item_id)
                    if armor_data and isinstance(armor_data, dict):
                        return armor_data.get("name", item_id)
                except Exception:
                    pass

        return str(item_id)

    # Header
    header = style.header_font.render("Armor", True, style.color_header_armor)
    screen.blit(header, (x_left, y))
    y += 30

    # Armor pieces
    armor_list = equipment.get("armor", [])
    armor_header = style.text_font.render("Armor Pieces:", True, style.color_header_armor)
    screen.blit(armor_header, (x_left + 10, y))
    y += 28

    if armor_list:
        for armor_id in armor_list:
            armor_name = get_item_name(armor_id, is_armor=True)
            armor_text = style.small_font.render(f"- {armor_name}", True, UI_TEXT)
            screen.blit(armor_text, (x_left + 30, y))
            y += 20
    else:
        no_armor = style.small_font.render("(none equipped)", True, (150, 150, 150))
        screen.blit(no_armor, (x_left + 30, y))
        y += 20

    # Placeholder for detailed armor visualization
    y += 20
    info_text = style.small_font.render("(Detailed armor visualization coming soon)", True, (150, 150, 150))
    screen.blit(info_text, (x_left + 10, y))
    y += 20

    return y
