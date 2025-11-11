"""Equipment phase - equip characters with weapons and armor.

TODO: Implement equipment selection for each unit in roster.
"""

from __future__ import annotations

import pygame
from application.game_context import GameContext
from config import DEJAVU_FONT_PATH
from domain.value_objects.scenario_config import UnitSetup
from logger.logger import get_logger
from presentation.components.equipment.equipment_panel_coordinator import EquipmentPanelCoordinator
from presentation.components.equipment.roster_list import RosterList

from .phase_base import SelectionPhaseBase

logger = get_logger(__name__)


class EquipmentPhase(SelectionPhaseBase):
    """Equipment phase (placeholder).

    Future functionality:
    - Select weapons for each character
    - Choose armor/protection
    - Manage inventory items
    - Preview equipment stats
    - Validate equipment restrictions (class/race requirements)
    """

    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        context: GameContext,
        team_a_size: int,
        team_b_size: int,
    ):
        """Initialize equipment phase.

        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
            context: Game context for data access
            team_a_size: Number of units in team A
            team_b_size: Number of units in team B
        """
        super().__init__(screen_width, screen_height, context)

        self.team_a_size = team_a_size
        self.team_b_size = team_b_size

        # Team colors (could be centralized later)
        self.team_a_color = (80, 160, 255)
        self.team_b_color = (255, 120, 120)

        # Combined roster (list of tuples (display_name, is_team_a, index_in_team))
        team_a = context.scenario_service.get_team(True)
        team_b = context.scenario_service.get_team(False)
        self.combined_roster: list[tuple[str, bool, int]] = []
        for idx, unit in enumerate(team_a):
            name = unit.character_file.rsplit(".", 1)[0]
            self.combined_roster.append((name, True, idx))
        for idx, unit in enumerate(team_b):
            name = unit.character_file.rsplit(".", 1)[0]
            self.combined_roster.append((name, False, idx))

        # Fonts
        self.font_title = pygame.font.Font(DEJAVU_FONT_PATH, 40)
        self.font_normal = pygame.font.Font(DEJAVU_FONT_PATH, 24)
        self.font_small = pygame.font.Font(DEJAVU_FONT_PATH, 16)

        # Colors
        self.color_bg = (20, 20, 30)
        self.color_text = (255, 255, 255)
        self.color_highlight = (255, 215, 0)
        self.color_instructions = (180, 180, 180)

        # UI layout calculations (after fonts defined)
        left_panel_w = max(220, screen_width // 5)
        right_panel_w = max(260, screen_width // 4)
        middle_w = screen_width - left_panel_w - right_panel_w - 40  # 40 = margins
        top_y = 110
        panel_h = screen_height - top_y - 80

        # Roster list (left)
        self.roster_list = RosterList(
            x=20,
            y=top_y,
            width=left_panel_w,
            height=panel_h,
            font=self.font_normal,
            team_a_color=self.team_a_color,
            team_b_color=self.team_b_color,
        )
        self.roster_list.set_items(self.combined_roster)

        # Equipment coordinator (middle + right)
        coord_width = screen_width - left_panel_w - 40
        self.equipment_coordinator = EquipmentPanelCoordinator(
            context=context,
            font=self.font_small,
            title_font=self.font_normal,
            screen_width=coord_width,
            screen_height=panel_h,
        )
        # Adjust position
        self.equipment_coordinator.equipment_panel.rect.x = 20 + left_panel_w + 10
        self.equipment_coordinator.equipment_panel.rect.y = top_y
        self.equipment_coordinator.inventory_panel.rect.x = (
            20 + left_panel_w + 10 + (coord_width - 40) // 2 + 20
        )
        self.equipment_coordinator.inventory_panel.rect.y = top_y

        # Recalculate layouts after position adjustment
        self.equipment_coordinator.equipment_panel._layout_slots()
        self.equipment_coordinator.inventory_panel._layout()

        # Current inventory items (tracked here)
        self.current_inventory: list[dict] = []

        # Load initial selected unit equipment if any
        self._load_selected_unit_equipment()

        logger.info(
            f"Equipment phase initialized: Team A={team_a_size} units, Team B={team_b_size} units"
        )

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle input events.

        Args:
            event: Pygame event
        """
        # Delegate to roster list first
        selection_changed = self.roster_list.handle_event(event)
        if selection_changed:
            self._load_selected_unit_equipment()

        # Equipment coordinator (handles both panels)
        if self.equipment_coordinator.handle_event(event):
            # Persist equipment changes back to underlying unit
            self._persist_equipment_changes()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.cancelled = True
                logger.info("Equipment phase cancelled (going back)")
            elif event.key == pygame.K_RETURN:
                # Proceed to deployment (future: validation of equipment)
                self.completed = True
                logger.info("Equipment phase completed")

    def draw(self, surface: pygame.Surface) -> None:
        """Draw equipment screen (placeholder).

        Args:
            surface: Surface to draw on
        """
        # Background
        surface.fill(self.color_bg)

        # Title
        title = self.font_title.render("Equipment Selection", True, self.color_text)
        title_rect = title.get_rect(center=(self.screen_width // 2, 50))
        surface.blit(title, title_rect)

        # Phase title already drawn; draw sub-panels
        self.roster_list.draw(surface)
        self.equipment_coordinator.draw(surface)

        # Instructions
        self._draw_instructions(surface)

    def _draw_instructions(self, surface: pygame.Surface) -> None:
        """Draw control instructions."""
        y = self.screen_height - 40
        instructions = "Select slot → Click item to equip | Right-click slot to remove | Enter: Continue | ESC: Back"
        inst_surf = self.font_small.render(instructions, True, self.color_instructions)
        inst_rect = inst_surf.get_rect(center=(self.screen_width // 2, y))
        surface.blit(inst_surf, inst_rect)

    def can_proceed(self) -> bool:
        """Check if can proceed to next phase.

        Returns:
            True (equipment currently optional)
        """
        return True

    # --- Internal helpers -------------------------------------------------
    def _load_selected_unit_equipment(self) -> None:
        """Load equipment and inventory for the selected unit."""
        sel = self.roster_list.get_selected()
        if not sel:
            return
        name, is_team_a, idx = sel
        unit = self.context.scenario_service.get_team(is_team_a)[idx]

        # Load fresh data for this unit (creates new instance each time)
        self.equipment_coordinator.set_data(unit.equipment, unit.inventory)

    def _persist_equipment_changes(self) -> None:
        """Persist equipment and inventory changes back to the unit."""
        sel = self.roster_list.get_selected()
        if not sel:
            return
        _, is_team_a, idx = sel
        unit = self.context.scenario_service.get_team(is_team_a)[idx]

        # Get updated equipment and inventory from coordinator
        updated_equipment = self.equipment_coordinator.get_equipment()
        updated_inventory = self.equipment_coordinator.get_current_inventory()

        # Rebuild UnitSetup with updated equipment and inventory
        updated = UnitSetup(
            character_file=unit.character_file,
            sprite_file=unit.sprite_file,
            start_q=unit.start_q,
            start_r=unit.start_r,
            facing=unit.facing,
            equipment=updated_equipment,
            inventory=updated_inventory,  # Updated inventory
        )
        self.context.scenario_service.update_unit(is_team_a, idx, updated)
