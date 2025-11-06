"""
Event handling for user input and UI interactions.
"""

from actions.action_attack import compute_attackable, handle_attack_click
from actions.action_charge import compute_charge_targets, execute_charge_attack
from actions.action_handling import process_action_ui_click
from actions.action_movement import apply_move_if_valid, compute_reachable
from actions.action_wield import toggle_wield_mode
from config import AP_COST_FACING, ActionMode
from core.game_state import GameState, next_turn
from systems.hex_grid import pixel_to_hex


def handle_ui_click(state: GameState, ui_result: dict) -> None:
    """
    Process UI click results from dropdown and facing buttons.
    Updates action mode and recalculates overlays.
    """
    if ui_result["type"] == "select_action":
        action = ui_result["action"]
        if action == "move":
            state.action_mode = ActionMode.MOVE
            compute_reachable(state)
            state.attackable_for_active = set()
            state.charge_targets = set()
        elif action == "attack":
            state.action_mode = ActionMode.ATTACK
            state.reachable_for_active = set()
            compute_attackable(state)
            state.charge_targets = set()
        elif action == "charge":
            state.action_mode = ActionMode.CHARGE
            state.reachable_for_active = set()
            state.attackable_for_active = set()
            compute_charge_targets(state)
        elif action == "change_facing":
            state.action_mode = ActionMode.CHANGE_FACING
            state.reachable_for_active = set()
            state.attackable_for_active = set()
            state.charge_targets = set()
        elif action == "change_wield":
            state.action_mode = ActionMode.CHANGE_WIELD
            state.reachable_for_active = set()
            state.attackable_for_active = set()
            state.charge_targets = set()
    elif ui_result["type"] == "select_facing":
        handle_facing_change(state, ui_result["facing"])
    elif ui_result["type"] == "toggle_wield":
        handle_wield_change(state)
    # toggle_dropdown is handled automatically by action_handling


def handle_wield_change(state: GameState) -> None:
    """
    Toggle the active unit's weapon wield mode.
    """
    if toggle_wield_mode(state):
        # Refresh popup wield info if visible
        if state.unit_info_popup and state.unit_info_popup.visible:
            state.unit_info_popup.refresh_cached_wield_info()


def handle_facing_change(state: GameState, new_facing: int) -> None:
    """
    Change active unit's facing direction.
    Deducts AP_COST_FACING action points.
    Auto-ends turn if AP depleted.
    """
    if state.active_unit.current_action_points >= AP_COST_FACING:
        state.active_unit.facing = new_facing
        state.active_unit.current_action_points -= AP_COST_FACING
        print(
            f"{state.active_unit.name} changed facing to {new_facing}. AP remaining: {state.active_unit.current_action_points}/{state.active_unit.max_action_points}"
        )
        # Check if AP depleted
        if state.active_unit.current_action_points <= 0:
            next_turn(state)
            state.action_mode = ActionMode.MOVE
            compute_reachable(state)
        else:
            # If we remain in ATTACK mode, update attackable tiles based on new facing
            if state.action_mode == ActionMode.ATTACK:
                compute_attackable(state)
    else:
        print(
            f"{state.active_unit.name} doesn't have enough AP to change facing! (Need {AP_COST_FACING}, have {state.active_unit.current_action_points})"
        )


def handle_grid_click(
    state: GameState, q: int, r: int, grid_bounds: tuple[int, int, int, int]
) -> None:
    """
    Process grid click based on action mode.
    Routes to movement, attack, charge, or wield handlers.

    Args:
        state: Current game state
        q, r: Hex coordinates of clicked position
        grid_bounds: (MIN_Q, MAX_Q, MIN_R, MAX_R) boundaries
    """
    MIN_Q, MAX_Q, MIN_R, MAX_R = grid_bounds

    # Only act if the clicked hex is on the grid
    if MIN_Q <= q < MAX_Q and MIN_R <= r < MAX_R:
        if state.action_mode == ActionMode.MOVE:
            _ = apply_move_if_valid(state, q, r)
        elif state.action_mode == ActionMode.ATTACK:
            _ = handle_attack_click(state, q, r)
        elif state.action_mode == ActionMode.CHARGE:
            # Check if clicked hex is a valid charge target
            if (q, r) in state.charge_targets:
                execute_charge_attack(state, q, r)
        elif state.action_mode == ActionMode.CHANGE_WIELD:
            # Any click in change wield mode toggles the wield mode
            handle_wield_change(state)


def handle_right_click(state: GameState, mx: int, my: int) -> None:
    """
    Handle right-click: show unit info popup if clicking on unit, close popup if clicking outside.

    Args:
        state: Current game state
        mx, my: Mouse pixel coordinates
    """
    # Check if popup is visible and we're clicking outside it
    if state.unit_info_popup and state.unit_info_popup.visible:
        if state.unit_info_popup.is_click_outside(mx, my):
            state.unit_info_popup.hide()
        return

    # Check if right-clicking on a unit to show info
    q, r = pixel_to_hex(mx, my)
    warrior_pos = state.warrior.get_position()
    goblin_pos = state.goblin.get_position()

    if (q, r) == warrior_pos:
        state.unit_info_popup.show(state.warrior)
    elif (q, r) == goblin_pos:
        state.unit_info_popup.show(state.goblin)


def process_mouse_click(
    state: GameState, mx: int, my: int, button: int, grid_bounds: tuple[int, int, int, int]
) -> None:
    """
    Main mouse click processor.

    Args:
        state: Current game state
        mx, my: Mouse pixel coordinates
        button: Mouse button (1=left, 3=right)
        grid_bounds: (MIN_Q, MAX_Q, MIN_R, MAX_R) boundaries
    """
    if button == 1:  # Left click
        # If popup is visible, check if clicking inside for tab switching or outside to close
        if state.unit_info_popup and state.unit_info_popup.visible:
            # Try tab click first
            if state.unit_info_popup.handle_click(mx, my):
                return  # Tab was clicked, handled
            # Otherwise check if clicking outside to close
            if state.unit_info_popup.is_click_outside(mx, my):
                state.unit_info_popup.hide()
            return

        # Try UI click first
        ui_result = process_action_ui_click(mx, my, state.ui_state, state.active_unit)
        if ui_result:
            handle_ui_click(state, ui_result)
        else:
            # Try grid click
            q, r = pixel_to_hex(mx, my)
            handle_grid_click(state, q, r, grid_bounds)
    elif button == 3:  # Right click
        handle_right_click(state, mx, my)
