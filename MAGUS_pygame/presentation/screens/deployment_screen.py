"""
Deployment screen for placing units on the hex grid before combat.

Allows players to position units from both teams on the hex battlefield
before the combat phase begins. Supports click-to-place, position validation,
and auto-advance to next undeployed unit.
"""


import pygame
from application.game_context import GameContext
from config import GRASS_BACKGROUND, HEIGHT, WIDTH, get_character_sprite_path
from domain.value_objects import ScenarioConfig, UnitSetup
from infrastructure.rendering.hex_grid import get_grid_bounds, hex_to_pixel, pixel_to_hex
from infrastructure.rendering.sprite_utils import load_and_mask_sprite
from logger.logger import get_logger

logger = get_logger(__name__)


class DeploymentScreen:
    """Deployment screen for positioning units on hex grid.

    Manages unit placement before combat begins. Validates positions,
    prevents overlapping placements, and tracks deployment progress.

    Emits action strings for application layer:
    - "deployment_confirmed": All units deployed and confirmed
    - "deployment_cancelled": User cancelled deployment
    """

    def __init__(
        self, screen_width: int, screen_height: int, config: ScenarioConfig, context: GameContext
    ):
        """Initialize deployment screen.

        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
            config: Scenario configuration with teams to deploy
            context: Game context for data access
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.context = context

        # Make config mutable during deployment (convert back to immutable when confirmed)
        self.config = config
        self.all_units = list(config.get_all_units())  # Mutable list for deployment

        # State
        self.action: str | None = None
        self.current_unit_index = 0

        # Grid bounds
        self.min_q, self.max_q, self.min_r, self.max_r = get_grid_bounds()

        # Hovered hex
        self.hovered_hex: tuple[int, int] | None = None

        # Load sprites
        self.unit_sprites: dict[int, pygame.Surface | None] = {}
        self._load_unit_sprites()

        # Load background
        self.background = self._load_background()

        # Fonts
        self.font_title = pygame.font.Font(None, 36)
        self.font_normal = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 22)

        # Colors
        self.color_text = (255, 255, 255)
        self.color_team_a = (100, 150, 255)
        self.color_team_b = (255, 100, 100)
        self.color_current = (255, 255, 0)
        self.color_panel_bg = (0, 0, 0, 200)
        self.color_button_enabled = (60, 120, 60)
        self.color_button_disabled = (60, 60, 60)
        self.color_button_reset = (80, 60, 60)

        # Buttons
        self.button_confirm = pygame.Rect(screen_width - 250, screen_height - 80, 200, 50)
        self.button_reset = pygame.Rect(screen_width - 250, screen_height - 150, 200, 50)

        logger.info(f"DeploymentScreen initialized: {len(self.all_units)} units to deploy")

    def _load_unit_sprites(self) -> None:
        """Load sprites for all units using sprite repository."""
        for i, unit in enumerate(self.all_units):
            try:
                sprite_path = get_character_sprite_path(unit.sprite_file)
                sprite = load_and_mask_sprite(str(sprite_path))
                self.unit_sprites[i] = sprite
                logger.debug(f"Loaded sprite for unit {i}: {unit.sprite_file}")
            except Exception as e:
                logger.warning(f"Failed to load sprite for unit {i} ({unit.sprite_file}): {e}")
                self.unit_sprites[i] = None

    def _load_background(self) -> pygame.Surface | None:
        """Load and scale background image.

        Returns:
            Background surface or None if loading fails
        """
        try:
            bg_img = pygame.image.load(str(GRASS_BACKGROUND)).convert()
            scaled_bg = pygame.transform.smoothscale(bg_img, (WIDTH, HEIGHT))
            logger.debug(f"Loaded background: {GRASS_BACKGROUND}")
            return scaled_bg
        except Exception as e:
            logger.warning(f"Failed to load background: {e}")
            return None

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle input events.

        Args:
            event: Pygame event
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.action = "deployment_cancelled"
                logger.info("Deployment cancelled by user")
            elif event.key == pygame.K_RETURN:
                if self._all_units_deployed():
                    self._confirm_deployment()
            elif event.key == pygame.K_TAB:
                self._cycle_to_next_unit()
            elif event.key == pygame.K_r:
                self._reset_positions()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                self._handle_click(event.pos)

        elif event.type == pygame.MOUSEMOTION:
            # Update hovered hex
            q, r = pixel_to_hex(*event.pos)
            if self.min_q <= q < self.max_q and self.min_r <= r < self.max_r:
                self.hovered_hex = (q, r)
            else:
                self.hovered_hex = None

    def _cycle_to_next_unit(self) -> None:
        """Cycle to the next undeployed unit, or wrap around if all deployed."""
        start_idx = self.current_unit_index

        # Try to find next undeployed unit
        for i in range(1, len(self.all_units) + 1):
            next_idx = (start_idx + i) % len(self.all_units)
            unit = self.all_units[next_idx]
            if not unit.is_deployed():
                self.current_unit_index = next_idx
                logger.debug(f"Cycled to unit {next_idx}: {unit.character_file}")
                return

        # If all deployed, just cycle normally
        self.current_unit_index = (start_idx + 1) % len(self.all_units)
        logger.debug(f"All units deployed, cycled to unit {self.current_unit_index}")

    def _reset_positions(self) -> None:
        """Reset all unit positions to undeployed state."""
        # Create new UnitSetup instances without deployment
        for i, unit in enumerate(self.all_units):
            self.all_units[i] = UnitSetup(
                character_file=unit.character_file,
                sprite_file=unit.sprite_file,
                start_q=None,
                start_r=None,
                facing=0,
            )

        self.current_unit_index = 0
        logger.info("All unit positions reset")

    def _handle_click(self, pos: tuple[int, int]) -> None:
        """Handle mouse click.

        Args:
            pos: Mouse position (x, y)
        """
        # Check button clicks
        if self.button_confirm.collidepoint(pos):
            if self._all_units_deployed():
                self._confirm_deployment()
            return

        if self.button_reset.collidepoint(pos):
            self._reset_positions()
            return

        # Check hex click for deployment
        q, r = pixel_to_hex(*pos)
        if self.min_q <= q < self.max_q and self.min_r <= r < self.max_r:
            self._deploy_unit_at(q, r)

    def _deploy_unit_at(self, q: int, r: int) -> None:
        """Deploy current unit at hex position.

        Args:
            q: Hex Q coordinate
            r: Hex R coordinate
        """
        # Check if position is already occupied
        if self._is_position_occupied(q, r):
            logger.debug(f"Position ({q}, {r}) already occupied")
            return

        # Deploy current unit
        current_unit = self.all_units[self.current_unit_index]
        self.all_units[self.current_unit_index] = current_unit.with_deployment(q, r, facing=0)
        logger.info(
            f"Deployed unit {self.current_unit_index} ({current_unit.character_file}) at ({q}, {r})"
        )

        # Auto-advance to next undeployed unit
        self._cycle_to_next_unit()

    def _is_position_occupied(self, q: int, r: int) -> bool:
        """Check if hex position is occupied.

        Args:
            q: Hex Q coordinate
            r: Hex R coordinate

        Returns:
            True if position is occupied
        """
        for unit in self.all_units:
            if unit.start_q == q and unit.start_r == r:
                return True
        return False

    def _all_units_deployed(self) -> bool:
        """Check if all units have been deployed.

        Returns:
            True if all units have positions
        """
        return all(unit.is_deployed() for unit in self.all_units)

    def _confirm_deployment(self) -> None:
        """Confirm deployment and build final immutable config."""
        # Split units back into teams
        team_a_size = len(self.config.team_a)
        team_a_units = self.all_units[:team_a_size]
        team_b_units = self.all_units[team_a_size:]

        # Build final immutable config
        self.config = self.config.with_team_a(team_a_units).with_team_b(team_b_units)

        self.action = "deployment_confirmed"
        logger.info(f"Deployment confirmed: Team A={len(team_a_units)}, Team B={len(team_b_units)}")

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the deployment screen.

        Args:
            surface: Surface to draw on
        """
        # Background
        if self.background:
            surface.blit(self.background, (0, 0))
        else:
            surface.fill((20, 30, 20))

        # Draw grid with placed units
        self._draw_grid_with_units(surface)

        # Draw UI overlay
        self._draw_ui_overlay(surface)

        # Draw buttons
        self._draw_buttons(surface)

    def _draw_grid_with_units(self, surface: pygame.Surface) -> None:
        """Draw hex grid with placed units and highlighting.

        Args:
            surface: Surface to draw on
        """
        from infrastructure.rendering.hex_grid import HEX_COLOR_OUTLINE, draw_hex_outline

        # Draw all hexes
        for q in range(self.min_q, self.max_q):
            for r in range(self.min_r, self.max_r):
                x, y = hex_to_pixel(q, r)

                # Highlight hovered hex
                if self.hovered_hex == (q, r):
                    if self._is_position_occupied(q, r):
                        highlight_color = (200, 80, 80)  # Red for occupied
                    else:
                        highlight_color = (80, 200, 80)  # Green for available
                    draw_hex_outline(surface, x, y, highlight_color, width=3)
                else:
                    draw_hex_outline(surface, x, y, HEX_COLOR_OUTLINE)

        # Draw placed units
        for i, unit in enumerate(self.all_units):
            if unit.is_deployed():
                x, y = hex_to_pixel(unit.start_q, unit.start_r)
                sprite = self.unit_sprites.get(i)

                if sprite:
                    # Center sprite on hex
                    sprite_rect = sprite.get_rect(center=(x, y))
                    surface.blit(sprite, sprite_rect)

                    # Draw unit number
                    font_tiny = pygame.font.Font(None, 18)
                    num_text = font_tiny.render(str(i + 1), True, (255, 255, 255))
                    num_bg = pygame.Surface((20, 20), pygame.SRCALPHA)
                    num_bg.fill((0, 0, 0, 180))
                    surface.blit(num_bg, (x - 10, y - 40))
                    surface.blit(num_text, (x - 7, y - 38))

    def _draw_ui_overlay(self, surface: pygame.Surface) -> None:
        """Draw UI overlay with current unit info and instructions.

        Args:
            surface: Surface to draw on
        """
        # Semi-transparent panel at top
        panel_height = 120
        panel = pygame.Surface((self.screen_width, panel_height), pygame.SRCALPHA)
        panel.fill(self.color_panel_bg)
        surface.blit(panel, (0, 0))

        # Current unit info
        current_unit = self.all_units[self.current_unit_index]
        team_a_size = len(self.config.team_a)
        team_letter = "A" if self.current_unit_index < team_a_size else "B"
        team_color = self.color_team_a if team_letter == "A" else self.color_team_b

        title = f"Deploying: Team {team_letter} - {current_unit.character_file}"
        title_surf = self.font_title.render(title, True, self.color_current)
        surface.blit(title_surf, (20, 15))

        # Deployment progress
        deployed_count = sum(1 for u in self.all_units if u.is_deployed())
        status = f"Deployed: {deployed_count}/{len(self.all_units)}"
        status_surf = self.font_normal.render(status, True, self.color_text)
        surface.blit(status_surf, (20, 55))

        # Instructions
        if not self._all_units_deployed():
            inst = "Click hex to place unit  |  TAB: Next unit  |  R: Reset all  |  ESC: Cancel"
        else:
            inst = "All units deployed! Press ENTER or click Confirm to start"
        inst_surf = self.font_small.render(inst, True, self.color_text)
        surface.blit(inst_surf, (20, 90))

    def _draw_buttons(self, surface: pygame.Surface) -> None:
        """Draw action buttons.

        Args:
            surface: Surface to draw on
        """
        # Reset button
        pygame.draw.rect(surface, self.color_button_reset, self.button_reset)
        reset_text = self.font_normal.render("Reset", True, self.color_text)
        reset_rect = reset_text.get_rect(center=self.button_reset.center)
        surface.blit(reset_text, reset_rect)

        # Confirm button (enabled only when all units deployed)
        can_confirm = self._all_units_deployed()
        confirm_color = self.color_button_enabled if can_confirm else self.color_button_disabled
        text_color = self.color_text if can_confirm else (120, 120, 120)

        pygame.draw.rect(surface, confirm_color, self.button_confirm)
        confirm_text = self.font_normal.render("Confirm", True, text_color)
        confirm_rect = confirm_text.get_rect(center=self.button_confirm.center)
        surface.blit(confirm_text, confirm_rect)

    def get_action(self) -> str | None:
        """Get emitted action (if any).

        Returns:
            Action string or None
        """
        return self.action

    def get_config(self) -> ScenarioConfig:
        """Get the deployment configuration with unit positions.

        Returns:
            ScenarioConfig with deployed positions
        """
        return self.config

    def is_complete(self) -> bool:
        """Check if deployment is complete (confirmed or cancelled).

        Returns:
            True if deployment finished
        """
        return self.action is not None
