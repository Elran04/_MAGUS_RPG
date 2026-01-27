"""
Skills tab rendering for unit info popup - shows learned skills.
"""

import pygame

from .popup_style import PopupStyle


def draw_skills(unit, screen: pygame.Surface, style: PopupStyle, x_left: int, x_right: int, y: int) -> int:
    """Draw skills tab content. Returns new y offset."""
    # Header
    header = style.header_font.render("Skills", True, (100, 200, 255))
    screen.blit(header, (x_left, y))
    y += 30

    # Get skills from unit
    skills = unit.skills if unit.skills else None
    if not skills or not skills._ranks:
        no_skills = style.text_font.render("No skills learned", True, (150, 150, 150))
        screen.blit(no_skills, (x_left + 10, y))
        return y + 30

    # Display skills in 2 columns
    skill_items = sorted(skills._ranks.items())
    displayed = 0
    for skill_name, skill_level in skill_items:
        col = displayed % 2
        row = displayed // 2
        skill_x = x_left + 10 + (col * 180)
        skill_y = y + (row * 22)

        # Format skill name (convert underscores to spaces, capitalize)
        display_name = skill_name.replace("_", " ").title()
        skill_text = style.small_font.render(f"{display_name}: {skill_level}", True, (100, 200, 255))
        screen.blit(skill_text, (skill_x, skill_y))
        displayed += 1

    rows = (displayed + 1) // 2
    y += rows * 22 + style.line_gap
    return y
