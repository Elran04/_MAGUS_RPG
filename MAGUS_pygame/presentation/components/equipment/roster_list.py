from __future__ import annotations

import pygame


class RosterList:
    """Scrollable roster list for equipment phase.

    Displays combined Team A and Team B units with color-coded text and
    supports selection via mouse and keyboard.
    """

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        font: pygame.font.Font,
        team_a_color=(80, 160, 255),
        team_b_color=(255, 120, 120),
        text_color=(230, 230, 240),
        bg_color=(25, 25, 35),
        border_color=(70, 70, 90),
    ) -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.team_a_color = team_a_color
        self.team_b_color = team_b_color
        self.text_color = text_color
        self.bg_color = bg_color
        self.border_color = border_color

        # Data: list of tuples (display_name, is_team_a, index_in_team)
        self.items: list[tuple[str, bool, int]] = []
        self.selected: int = 0
        self.scroll_offset: int = 0
        self.item_height: int = max(28, font.get_height() + 8)

    def set_items(self, items: list[tuple[str, bool, int]]) -> None:
        self.items = items
        self.selected = 0 if items else -1
        self.scroll_offset = 0

    def get_selected(self) -> tuple[str, bool, int] | None:
        if 0 <= self.selected < len(self.items):
            return self.items[self.selected]
        return None

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle events. Returns True if selection changed."""
        if event.type == pygame.MOUSEWHEEL:
            # Scroll list
            self.scroll_offset = max(0, self.scroll_offset - event.y * self.item_height)
            max_offset = max(0, len(self.items) * self.item_height - self.rect.height)
            self.scroll_offset = min(self.scroll_offset, max_offset)
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                rel_y = event.pos[1] - self.rect.y + self.scroll_offset
                idx = rel_y // self.item_height
                if 0 <= idx < len(self.items):
                    if idx != self.selected:
                        self.selected = idx
                        return True
            return False

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                if self.selected > 0:
                    self.selected -= 1
                    self._ensure_visible()
                    return True
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                if self.selected < len(self.items) - 1:
                    self.selected += 1
                    self._ensure_visible()
                    return True
        return False

    def _ensure_visible(self) -> None:
        top = self.selected * self.item_height
        bottom = top + self.item_height
        if top < self.scroll_offset:
            self.scroll_offset = top
        elif bottom > self.scroll_offset + self.rect.height:
            self.scroll_offset = bottom - self.rect.height

    def draw(self, surface: pygame.Surface) -> None:
        # Background
        pygame.draw.rect(surface, self.bg_color, self.rect)
        pygame.draw.rect(surface, self.border_color, self.rect, 1)

        # Clip
        clip_prev = surface.get_clip()
        surface.set_clip(self.rect)

        # Draw items
        y = self.rect.y - self.scroll_offset
        for i, (name, is_team_a, _) in enumerate(self.items):
            item_rect = pygame.Rect(self.rect.x, y, self.rect.width, self.item_height)
            # Selection highlight
            if i == self.selected:
                pygame.draw.rect(surface, (50, 60, 90), item_rect)
            # Text color by team
            color = self.team_a_color if is_team_a else self.team_b_color
            label = self.font.render(name, True, color)
            surface.blit(
                label, (self.rect.x + 10, y + (self.item_height - label.get_height()) // 2)
            )
            y += self.item_height

        # Restore clip
        surface.set_clip(clip_prev)
