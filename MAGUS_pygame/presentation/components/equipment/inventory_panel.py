from __future__ import annotations

import pygame
from typing import Dict

class InventoryPanel:
    """Displays current equipment/inventory for selected unit.

    For now shows equipment mapping and placeholder inventory list.
    """

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        font: pygame.font.Font,
        title_font: pygame.font.Font | None = None,
        bg_color=(25, 25, 35),
        border_color=(70, 70, 90),
        text_color=(230, 230, 240),
    ) -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.title_font = title_font or font
        self.bg_color = bg_color
        self.border_color = border_color
        self.text_color = text_color
        self.equipment: Dict[str, str] = {}
        self.inventory: Dict[str, int] = {}

    def set_data(self, equipment: Dict[str, str], inventory: Dict[str, int]) -> None:
        self.equipment = equipment
        self.inventory = inventory

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, self.bg_color, self.rect)
        pygame.draw.rect(surface, self.border_color, self.rect, 1)

        y = self.rect.y + 10
        title = self.title_font.render("Equipment", True, self.text_color)
        surface.blit(title, (self.rect.x + 10, y))
        y += title.get_height() + 6

        # Equipment list
        for slot, value in sorted(self.equipment.items()):
            line = f"{slot.replace('_',' ').title()}: {value}" if value else f"{slot}: <none>"
            label = self.font.render(line, True, self.text_color)
            surface.blit(label, (self.rect.x + 12, y))
            y += label.get_height() + 2

        y += 8
        inv_title = self.title_font.render("Inventory", True, self.text_color)
        surface.blit(inv_title, (self.rect.x + 10, y))
        y += inv_title.get_height() + 6

        if not self.inventory:
            empty = self.font.render("(empty)", True, (150, 150, 160))
            surface.blit(empty, (self.rect.x + 12, y))
            return

        for item_id, qty in self.inventory.items():
            line = f"{item_id} x{qty}" if qty > 1 else item_id
            label = self.font.render(line, True, self.text_color)
            surface.blit(label, (self.rect.x + 12, y))
            y += label.get_height() + 2
