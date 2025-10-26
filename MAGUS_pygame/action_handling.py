"""
Action handling UI utilities: buttons setup, rendering, and clicks processing.
"""
import pygame
from typing import Optional, Dict
from config import HEIGHT, UI_BORDER, UI_TEXT, UI_ACTIVE, UI_INACTIVE


def setup_action_ui() -> Dict[str, object]:
    """Create button rects and font for action UI.

    Returns:
        dict with keys: move_button_rect, attack_button_rect, ui_font
    """
    BUTTON_W, BUTTON_H = 120, 36
    move_button_rect = pygame.Rect(10, HEIGHT - BUTTON_H - 10, BUTTON_W, BUTTON_H)
    attack_button_rect = pygame.Rect(20 + BUTTON_W, HEIGHT - BUTTON_H - 10, BUTTON_W, BUTTON_H)
    ui_font = pygame.font.SysFont(None, 28)
    return {
        "move_button_rect": move_button_rect,
        "attack_button_rect": attack_button_rect,
        "ui_font": ui_font,
    }


def _draw_button(screen: pygame.Surface, rect: pygame.Rect, label: str, active: bool, ui_font: pygame.font.Font):
    pygame.draw.rect(screen, UI_ACTIVE if active else UI_INACTIVE, rect, border_radius=6)
    pygame.draw.rect(screen, UI_BORDER, rect, width=2, border_radius=6)
    text_surf = ui_font.render(label, True, UI_TEXT)
    text_rect = text_surf.get_rect(center=rect.center)
    screen.blit(text_surf, text_rect)


def draw_action_ui(screen: pygame.Surface, ui_state: Dict[str, object], action_mode: str):
    """Draw Move and Attack buttons.

    Args:
        screen: pygame screen surface
        ui_state: dict from setup_action_ui
        action_mode: 'move' or 'attack'
    """
    ui_font = ui_state["ui_font"]
    move_button_rect = ui_state["move_button_rect"]
    attack_button_rect = ui_state["attack_button_rect"]
    _draw_button(screen, move_button_rect, "Move", action_mode == "move", ui_font)
    _draw_button(screen, attack_button_rect, "Attack", action_mode == "attack", ui_font)


def process_action_button_click(mx: int, my: int, ui_state: Dict[str, object]) -> Optional[str]:
    """Return 'move' or 'attack' if a button was clicked, else None."""
    move_button_rect = ui_state["move_button_rect"]
    attack_button_rect = ui_state["attack_button_rect"]
    if move_button_rect.collidepoint(mx, my):
        return "move"
    if attack_button_rect.collidepoint(mx, my):
        return "attack"
    return None
