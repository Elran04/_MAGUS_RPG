from __future__ import annotations

import pygame
from typing import Dict, List

SLOT_ORDER = [
    "primary_weapon",
    "offhand",
    "ranged_weapon",
    "armor_head",
    "armor_torso",
    "armor_legs",
]

class EquipmentSlotsPanel:
    """Panel displaying equipment slots for a single unit.

    Each slot is a rectangle; clicking cycles placeholder items.
    Integration with real equipment repository can replace cycle logic later.
    """

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        font: pygame.font.Font,
        bg_color=(25, 25, 35),
        border_color=(70, 70, 90),
        slot_color=(55, 65, 95),
        slot_hover=(75, 85, 115),
        text_color=(230, 230, 240),
    ) -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.bg_color = bg_color
        self.border_color = border_color
        self.slot_color = slot_color
        self.slot_hover = slot_hover
        self.text_color = text_color

        self.slot_rects: Dict[str, pygame.Rect] = {}
        self.slot_values: Dict[str, str] = {slot: "<none>" for slot in SLOT_ORDER}
        self.slot_cycle_items: Dict[str, List[str]] = {
            "primary_weapon": ["sword", "axe", "mace", "<none>"],
            "offhand": ["shield", "dagger", "torch", "<none>"],
            "ranged_weapon": ["bow", "crossbow", "sling", "<none>"],
            "armor_head": ["cap", "helm", "hood", "<none>"],
            "armor_torso": ["leather", "chain", "plate", "<none>"],
            "armor_legs": ["greaves", "leggings", "pants", "<none>"],
        }
        self._layout_slots()

    def _layout_slots(self) -> None:
        padding = 12
        slot_h = 60
        gap = 10
        x = self.rect.x + padding
        y = self.rect.y + padding
        slot_w = self.rect.width - 2 * padding
        for slot in SLOT_ORDER:
            self.slot_rects[slot] = pygame.Rect(x, y, slot_w, slot_h)
            y += slot_h + gap

    def set_initial(self, equipment: Dict[str, str]) -> None:
        for k, v in equipment.items():
            if k in self.slot_values:
                self.slot_values[k] = v

    def get_equipment(self) -> Dict[str, str]:
        return dict(self.slot_values)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle events. Returns True if any slot changed."""
        changed = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for slot, rect in self.slot_rects.items():
                if rect.collidepoint(event.pos):
                    cycle = self.slot_cycle_items.get(slot, [])
                    if cycle:
                        current = self.slot_values.get(slot, "<none>")
                        try:
                            idx = cycle.index(current)
                        except ValueError:
                            idx = -1
                        new_val = cycle[(idx + 1) % len(cycle)] if cycle else current
                        self.slot_values[slot] = new_val
                        changed = True
        return changed

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, self.bg_color, self.rect)
        pygame.draw.rect(surface, self.border_color, self.rect, 1)

        mouse_pos = pygame.mouse.get_pos()
        for slot, rect in self.slot_rects.items():
            hover = rect.collidepoint(mouse_pos)
            pygame.draw.rect(surface, self.slot_hover if hover else self.slot_color, rect, border_radius=6)
            label = self.font.render(slot.replace("_", " ").title(), True, self.text_color)
            surface.blit(label, (rect.x + 12, rect.y + 10))
            value = self.slot_values.get(slot, "<none>")
            val_label = self.font.render(value, True, (200, 200, 220))
            surface.blit(val_label, (rect.x + 12, rect.y + 32))
