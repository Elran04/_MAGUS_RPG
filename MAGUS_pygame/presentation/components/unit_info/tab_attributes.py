"""
Attributes tab rendering for unit info popup - shows character properties with MGT impact.
"""

import pygame
from config import UI_TEXT
from domain.mechanics.equipment import build_equipment_context, get_effective_attributes

from .popup_style import PopupStyle


def draw_attributes(unit, screen: pygame.Surface, style: PopupStyle, x: int, y: int) -> int:
    """Draw character attributes (Tulajdonságok) with MGT and effective values. Returns new y offset."""
    # Header
    header = style.header_font.render("Attributes", True, style.color_header_attributes)
    screen.blit(header, (x, y))
    y += 30

    # Get base and effective attributes
    attrs = unit.attributes
    effective_attrs = get_effective_attributes(unit)

    # Get MGT context
    mgt_context = build_equipment_context(unit)
    total_mgt = mgt_context.get_total_mgt()

    # Always show MGT value (red if burden, green if none)
    mgt_text_color = (255, 100, 100) if total_mgt > 0 else (100, 255, 100)
    mgt_text = style.text_font.render(f"MGT: {total_mgt}", True, mgt_text_color)
    screen.blit(mgt_text, (x + 10, y))
    y += 28

    attr_data = [
        ("Erő", attrs.strength, None),  # Strength unchanged
        ("Ügy", attrs.dexterity, effective_attrs.dexterity),  # Dexterity affected by MGT
        ("Gyo", attrs.speed, effective_attrs.speed),  # Speed affected by MGT
        ("Áll", attrs.endurance, None),  # Endurance unchanged
        ("Egé", attrs.health, None),  # Health unchanged
        ("Kar", attrs.charisma, None),  # Charisma unchanged
        ("Int", attrs.intelligence, None),  # Intelligence unchanged
        ("Aka", attrs.willpower, None),  # Willpower unchanged
        ("Asz", attrs.astral, None),  # Astral unchanged
    ]

    displayed = 0
    for attr_name, base_value, effective_value in attr_data:
        # Draw in 3 columns
        col = displayed % 3
        row = displayed // 3
        attr_x = x + 10 + (col * 120)
        attr_y = y + (row * 22)

        # If there's an effective value different from base, show both
        if effective_value is not None and effective_value != base_value:
            # Show base value in gray
            base_text = style.small_font.render(f"{attr_name}: {base_value}", True, (150, 150, 150))
            screen.blit(base_text, (attr_x, attr_y))

            # Show effective value in red (reduced by MGT)
            eff_text = style.small_font.render(f"→{effective_value}", True, (255, 100, 100))
            screen.blit(eff_text, (attr_x + 85, attr_y))
        else:
            # Normal display for unchanged attributes
            attr_text = style.small_font.render(f"{attr_name}: {base_value}", True, UI_TEXT)
            screen.blit(attr_text, (attr_x, attr_y))

        displayed += 1

    rows = (displayed + 2) // 3
    y += rows * style.attribute_row_height + style.line_gap

    return y
