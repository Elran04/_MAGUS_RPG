"""Scenario List Dialog - Modal dialog for selecting scenarios to load."""

from __future__ import annotations

import pygame
from logger.logger import get_logger

logger = get_logger(__name__)


class ScenarioListDialog:
    """Modal dialog for scenario selection with scrollable list."""
    
    def __init__(self, screen_width: int, screen_height: int, scenarios: list[str]):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.scenarios = scenarios
        
        self.selected_index = 0
        self.scroll_offset = 0
        self.result: str | None = None  # Selected scenario name
        self.cancelled = False
        
        # Fonts
        self.font_large = pygame.font.Font(None, 48)
        self.font_normal = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        
        # Colors
        self.color_overlay = (0, 0, 0, 180)
        self.color_panel = (40, 40, 50)
        self.color_text = (240, 240, 255)
        self.color_highlight = (255, 215, 0)
        self.color_button = (60, 70, 90)
        self.color_button_hover = (80, 90, 120)
        
        # Layout
        dialog_w, dialog_h = 600, 500
        self.dialog_rect = pygame.Rect(
            (screen_width - dialog_w) // 2,
            (screen_height - dialog_h) // 2,
            dialog_w, dialog_h
        )
        
        self.list_rect = pygame.Rect(
            self.dialog_rect.x + 20,
            self.dialog_rect.y + 80,
            self.dialog_rect.width - 40,
            self.dialog_rect.height - 160
        )
        
        self.btn_load = pygame.Rect(
            self.dialog_rect.centerx - 160,
            self.dialog_rect.bottom - 60,
            140, 45
        )
        
        self.btn_cancel = pygame.Rect(
            self.dialog_rect.centerx + 20,
            self.dialog_rect.bottom - 60,
            140, 45
        )
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle input events.
        
        Returns:
            True if dialog is still active, False if closed
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.cancelled = True
                return False
            elif event.key == pygame.K_UP:
                self.selected_index = max(0, self.selected_index - 1)
            elif event.key == pygame.K_DOWN:
                self.selected_index = min(len(self.scenarios) - 1, self.selected_index + 1)
            elif event.key == pygame.K_RETURN:
                if self.scenarios:
                    self.result = self.scenarios[self.selected_index]
                    return False
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                pos = event.pos
                
                # List clicks
                if self.list_rect.collidepoint(pos):
                    relative_y = pos[1] - self.list_rect.y
                    clicked_index = (relative_y // 40) + self.scroll_offset
                    if 0 <= clicked_index < len(self.scenarios):
                        self.selected_index = clicked_index
                
                # Button clicks
                elif self.btn_load.collidepoint(pos):
                    if self.scenarios:
                        self.result = self.scenarios[self.selected_index]
                        return False
                
                elif self.btn_cancel.collidepoint(pos):
                    self.cancelled = True
                    return False
            
            # Scroll wheel
            elif event.button == 4:  # Scroll up
                self.scroll_offset = max(0, self.scroll_offset - 1)
            elif event.button == 5:  # Scroll down
                max_scroll = max(0, len(self.scenarios) - 8)
                self.scroll_offset = min(max_scroll, self.scroll_offset + 1)
        
        return True
    
    def draw(self, surface: pygame.Surface) -> None:
        """Draw the dialog."""
        # Semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill(self.color_overlay)
        surface.blit(overlay, (0, 0))
        
        # Dialog box
        pygame.draw.rect(surface, self.color_panel, self.dialog_rect, border_radius=10)
        pygame.draw.rect(surface, self.color_highlight, self.dialog_rect, width=3, border_radius=10)
        
        # Title
        title = self.font_large.render("Load Scenario", True, self.color_highlight)
        surface.blit(title, title.get_rect(center=(self.dialog_rect.centerx, self.dialog_rect.y + 40)))
        
        # Scenario list
        if not self.scenarios:
            no_text = self.font_normal.render("No scenarios found", True, (150, 150, 150))
            surface.blit(no_text, no_text.get_rect(center=self.list_rect.center))
        else:
            self._draw_scenario_list(surface)
        
        # Buttons
        self._draw_buttons(surface)
        
        # Instructions
        inst = self.font_small.render(
            "↑↓ or Click to select | Enter or Load button | ESC to cancel",
            True, (200, 200, 220)
        )
        surface.blit(inst, inst.get_rect(center=(self.dialog_rect.centerx, self.dialog_rect.bottom + 35)))
    
    def _draw_scenario_list(self, surface: pygame.Surface) -> None:
        """Draw scrollable scenario list."""
        visible_count = min(8, len(self.scenarios))
        
        for i in range(visible_count):
            scenario_idx = i + self.scroll_offset
            if scenario_idx >= len(self.scenarios):
                break
            
            scenario_name = self.scenarios[scenario_idx]
            y = self.list_rect.y + i * 40
            
            # Highlight selected
            if scenario_idx == self.selected_index:
                highlight_rect = pygame.Rect(
                    self.list_rect.x,
                    y,
                    self.list_rect.width,
                    38
                )
                pygame.draw.rect(surface, self.color_button_hover, highlight_rect, border_radius=5)
            
            # Scenario name
            color = self.color_highlight if scenario_idx == self.selected_index else self.color_text
            text = self.font_normal.render(scenario_name, True, color)
            surface.blit(text, (self.list_rect.x + 10, y + 8))
        
        # Scroll indicator
        if len(self.scenarios) > 8:
            scroll_text = self.font_small.render(
                f"{self.scroll_offset + 1}-{min(self.scroll_offset + 8, len(self.scenarios))} of {len(self.scenarios)}",
                True, (180, 180, 200)
            )
            surface.blit(scroll_text, (self.list_rect.x, self.list_rect.bottom + 5))
    
    def _draw_buttons(self, surface: pygame.Surface) -> None:
        """Draw Load and Cancel buttons."""
        mouse_pos = pygame.mouse.get_pos()
        
        # Load button
        load_color = self.color_button_hover if self.btn_load.collidepoint(mouse_pos) else self.color_button
        pygame.draw.rect(surface, load_color, self.btn_load, border_radius=5)
        load_text = self.font_normal.render("Load", True, self.color_text)
        surface.blit(load_text, load_text.get_rect(center=self.btn_load.center))
        
        # Cancel button
        cancel_color = self.color_button_hover if self.btn_cancel.collidepoint(mouse_pos) else self.color_button
        pygame.draw.rect(surface, cancel_color, self.btn_cancel, border_radius=5)
        cancel_text = self.font_normal.render("Cancel", True, self.color_text)
        surface.blit(cancel_text, cancel_text.get_rect(center=self.btn_cancel.center))
    
    def is_done(self) -> bool:
        """Check if dialog is finished."""
        return self.result is not None or self.cancelled
    
    def get_result(self) -> str | None:
        """Get selected scenario name, or None if cancelled."""
        return self.result
