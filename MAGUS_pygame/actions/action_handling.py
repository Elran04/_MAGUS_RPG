"""
Action handling UI utilities: dropdown menu for actions and initiative rolling.
"""
import random
import pygame
from typing import Optional, Dict, List
from config import HEIGHT, WIDTH, UI_BORDER, UI_TEXT, UI_ACTIVE, UI_INACTIVE
from core.game_state import GameState


def roll_initiative(state: GameState) -> None:
    """
    Roll initiative for both units (d100 + KÉ).
    Determine turn order for the round and set first active unit.
    In case of tie, higher base KÉ wins. If still tied, reroll.
    """
    warrior_ke = state.warrior.KE
    goblin_ke = state.goblin.KE
    
    while True:
        warrior_d100 = random.randint(1, 100)
        goblin_d100 = random.randint(1, 100)
        
        warrior_init = warrior_d100 + warrior_ke
        goblin_init = goblin_d100 + goblin_ke
        
        # Store the rolls for display
        state.initiative_rolls = {
            state.warrior.name: warrior_init,
            state.goblin.name: goblin_init,
        }
        
        if warrior_init > goblin_init:
            state.turn_order = [state.warrior, state.goblin]
            break
        elif goblin_init > warrior_init:
            state.turn_order = [state.goblin, state.warrior]
            break
        else:
            # Tied - use base KÉ as tiebreaker
            if warrior_ke > goblin_ke:
                state.turn_order = [state.warrior, state.goblin]
                break
            elif goblin_ke > warrior_ke:
                state.turn_order = [state.goblin, state.warrior]
                break
            # Both init and base KÉ are equal - reroll (loop continues)
    
    # Set first active unit and clear acted tracking
    state.active_unit = state.turn_order[0]
    state.units_acted_this_round = set()
    state.turn = 0 if state.active_unit == state.warrior else 1
    
    # Reset action points for both units at start of new round
    state.warrior.current_action_points = state.warrior.max_action_points
    state.goblin.current_action_points = state.goblin.max_action_points


def setup_action_ui() -> Dict[str, object]:
    """Create dropdown and facing selection UI elements.

    Returns:
        dict with keys: dropdown_rect, dropdown_open, ui_font, action_options, facing_buttons
    """
    DROPDOWN_W, DROPDOWN_H = 200, 36
    dropdown_rect = pygame.Rect(10, HEIGHT - DROPDOWN_H - 10, DROPDOWN_W, DROPDOWN_H)
    ui_font = pygame.font.SysFont(None, 28)
    
    action_options = ["Move", "Attack", "Change Facing"]
    
    # Facing direction buttons (shown when Change Facing is selected)
    # Arrange in hex pattern around a center point
    facing_center_x = 10 + DROPDOWN_W + 40
    facing_center_y = HEIGHT - 60
    facing_buttons = []
    # Use simple ASCII arrows or characters
    # Facing: 0=N, 1=NE, 2=SE, 3=S, 4=SW, 5=NW
    facing_labels = ["^", ">", "v", "<", "v", "^"]  # Will draw rotated triangles instead
    button_size = 30
    
    for i in range(6):
        # Arrange buttons in hex pattern, offset by 30° to match side-facing
        angle = math.radians(-90 + 30 + i * 60)  # Start at top-right, go clockwise
        x = facing_center_x + 50 * math.cos(angle) - button_size // 2
        y = facing_center_y + 50 * math.sin(angle) - button_size // 2
        facing_buttons.append({
            "rect": pygame.Rect(int(x), int(y), button_size, button_size),
            "facing": i,
            "angle": -60 + i * 60  # Angle for drawing the arrow triangle
        })
    
    return {
        "dropdown_rect": dropdown_rect,
        "dropdown_open": False,
        "ui_font": ui_font,
        "action_options": action_options,
        "selected_action": "Move",
        "facing_buttons": facing_buttons,
    }


import math


def draw_action_ui(screen: pygame.Surface, ui_state: Dict[str, object], action_mode: str):
    """Draw action dropdown and facing selection UI.

    Args:
        screen: pygame screen surface
        ui_state: dict from setup_action_ui
        action_mode: current action mode string
    """
    ui_font = ui_state["ui_font"]
    dropdown_rect = ui_state["dropdown_rect"]
    dropdown_open = ui_state["dropdown_open"]
    action_options = ui_state["action_options"]
    selected_action = ui_state.get("selected_action", "Move")
    
    # Draw main dropdown button
    pygame.draw.rect(screen, UI_ACTIVE, dropdown_rect, border_radius=6)
    pygame.draw.rect(screen, UI_BORDER, dropdown_rect, width=2, border_radius=6)
    
    # Show current selection with text
    text = f"{selected_action}"
    text_surf = ui_font.render(text, True, UI_TEXT)
    text_rect = text_surf.get_rect(midleft=(dropdown_rect.left + 10, dropdown_rect.centery))
    screen.blit(text_surf, text_rect)
    
    # Draw small triangle arrow indicator
    arrow_x = dropdown_rect.right - 20
    arrow_y = dropdown_rect.centery
    arrow_size = 6
    
    if dropdown_open:
        # Up arrow (triangle pointing up)
        points = [
            (arrow_x, arrow_y - arrow_size // 2),  # Top point
            (arrow_x - arrow_size, arrow_y + arrow_size // 2),  # Bottom left
            (arrow_x + arrow_size, arrow_y + arrow_size // 2)   # Bottom right
        ]
    else:
        # Down arrow (triangle pointing down)
        points = [
            (arrow_x, arrow_y + arrow_size // 2),  # Bottom point
            (arrow_x - arrow_size, arrow_y - arrow_size // 2),  # Top left
            (arrow_x + arrow_size, arrow_y - arrow_size // 2)   # Top right
        ]
    pygame.draw.polygon(screen, UI_TEXT, points)
    
    # Draw dropdown options if open (expand upward)
    if dropdown_open:
        option_height = 36
        for i, option in enumerate(action_options):
            # Draw options above the dropdown button (reversed order, expanding up)
            option_rect = pygame.Rect(
                dropdown_rect.left,
                dropdown_rect.top - (len(action_options) - i) * option_height,
                dropdown_rect.width,
                option_height
            )
            color = UI_ACTIVE if option == action_mode.title() else UI_INACTIVE
            pygame.draw.rect(screen, color, option_rect, border_radius=6)
            pygame.draw.rect(screen, UI_BORDER, option_rect, width=2, border_radius=6)
            
            opt_text = ui_font.render(option, True, UI_TEXT)
            opt_text_rect = opt_text.get_rect(midleft=(option_rect.left + 10, option_rect.centery))
            screen.blit(opt_text, opt_text_rect)
    
    # Draw facing direction buttons if "Change Facing" is selected
    if selected_action == "Change Facing":
        facing_buttons = ui_state["facing_buttons"]
        for btn in facing_buttons:
            pygame.draw.rect(screen, UI_INACTIVE, btn["rect"], border_radius=4)
            pygame.draw.rect(screen, UI_BORDER, btn["rect"], width=2, border_radius=4)
            
            # Draw a small triangle pointing in the facing direction
            center_x = btn["rect"].centerx
            center_y = btn["rect"].centery
            angle_rad = math.radians(btn["angle"])
            
            # Triangle dimensions
            size = 10
            tip_x = center_x + size * math.cos(angle_rad)
            tip_y = center_y + size * math.sin(angle_rad)
            
            perp_angle = angle_rad + math.pi / 2
            base1_x = center_x + (size * 0.4) * math.cos(perp_angle)
            base1_y = center_y + (size * 0.4) * math.sin(perp_angle)
            base2_x = center_x - (size * 0.4) * math.cos(perp_angle)
            base2_y = center_y - (size * 0.4) * math.sin(perp_angle)
            
            points = [(tip_x, tip_y), (base1_x, base1_y), (base2_x, base2_y)]
            pygame.draw.polygon(screen, UI_TEXT, points)


def process_action_ui_click(mx: int, my: int, ui_state: Dict[str, object]) -> Optional[Dict[str, any]]:
    """
    Process click on action UI (dropdown or facing buttons).
    
    Returns:
        dict with 'type' and relevant data, or None:
        - {'type': 'toggle_dropdown'}
        - {'type': 'select_action', 'action': 'move'/'attack'/'change_facing'}
        - {'type': 'select_facing', 'facing': 0-5}
    """
    dropdown_rect = ui_state["dropdown_rect"]
    dropdown_open = ui_state["dropdown_open"]
    action_options = ui_state["action_options"]
    
    # Check dropdown button click
    if dropdown_rect.collidepoint(mx, my):
        ui_state["dropdown_open"] = not dropdown_open
        return {"type": "toggle_dropdown"}
    
    # Check dropdown options if open (options are above the button)
    if dropdown_open:
        option_height = 36
        for i, option in enumerate(action_options):
            option_rect = pygame.Rect(
                dropdown_rect.left,
                dropdown_rect.top - (len(action_options) - i) * option_height,
                dropdown_rect.width,
                option_height
            )
            if option_rect.collidepoint(mx, my):
                ui_state["dropdown_open"] = False
                ui_state["selected_action"] = option
                action_mode = option.lower().replace(" ", "_")
                return {"type": "select_action", "action": action_mode}
    
    # Check facing buttons if Change Facing is selected
    if ui_state.get("selected_action") == "Change Facing":
        facing_buttons = ui_state["facing_buttons"]
        for btn in facing_buttons:
            if btn["rect"].collidepoint(mx, my):
                return {"type": "select_facing", "facing": btn["facing"]}
    
    return None
