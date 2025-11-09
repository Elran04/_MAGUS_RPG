"""
Map preview component for scenario selector.

Displays scenario background image preview and map information
for scenario selection screens.
"""


import pygame
from logger.logger import get_logger

logger = get_logger(__name__)


class MapPreview:
    """Preview panel for scenario map and background.

    Shows background image preview and scenario information in a panel
    suitable for scenario selection screens.
    """

    def __init__(self, x: int, y: int, width: int, height: int):
        """Initialize map preview panel.

        Args:
            x: Panel X position
            y: Panel Y position
            width: Panel width
            height: Panel height
        """
        self.rect = pygame.Rect(x, y, width, height)

        # Layout
        self.preview_width = width - 40
        self.preview_height = int((height - 120) * 0.8)  # 80% for image, 20% for info

        # Fonts
        self.font_title = pygame.font.Font(None, 32)
        self.font_label = pygame.font.Font(None, 24)
        self.font_value = pygame.font.Font(None, 20)

        # Colors
        self.color_bg = (0, 0, 0, 170)
        self.color_title = (255, 215, 0)
        self.color_label = (255, 255, 255)
        self.color_value = (200, 200, 200)
        self.color_missing = (220, 120, 120)
        self.color_grid = (70, 70, 90)
        self.color_grid_bg = (40, 40, 55, 140)

        # Background cache
        self._background_cache: dict[str, pygame.Surface] = {}

        logger.debug(f"MapPreview initialized at ({x}, {y}) size {width}x{height}")

    def draw(
        self,
        surface: pygame.Surface,
        scenario_name: str,
        background_surface: pygame.Surface | None = None,
        background_filename: str | None = None,
    ) -> None:
        """Draw map preview panel.

        Args:
            surface: Surface to draw on
            scenario_name: Name of the scenario/map
            background_surface: Pre-loaded background surface (or None)
            background_filename: Background filename for display (or None if not found)
        """
        # Draw panel background
        panel = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        panel.fill(self.color_bg)
        surface.blit(panel, self.rect.topleft)

        # Title
        title = self.font_title.render("Map Preview", True, self.color_title)
        surface.blit(title, (self.rect.x + 20, self.rect.y + 15))

        # Background image area
        img_x = self.rect.x + 20
        img_y = self.rect.y + 60

        if background_surface:
            # Scale and draw background
            scaled_bg = self._scale_background(
                background_surface, self.preview_width, self.preview_height
            )
            surface.blit(scaled_bg, (img_x, img_y))
        else:
            # Draw placeholder grid
            self._draw_placeholder_grid(
                surface, img_x, img_y, self.preview_width, self.preview_height
            )

            # Warning message
            warn = self.font_label.render("No background image", True, self.color_missing)
            warn_rect = warn.get_rect(
                center=(img_x + self.preview_width // 2, img_y + self.preview_height // 2)
            )
            surface.blit(warn, warn_rect)

        # Info section (below image)
        info_y = img_y + self.preview_height + 15

        # Scenario name
        scenario_surf = self.font_label.render(f"Scenario: {scenario_name}", True, self.color_label)
        surface.blit(scenario_surf, (img_x, info_y))
        info_y += 25

        # Background filename
        bg_label = background_filename if background_filename else "<none>"
        bg_surf = self.font_value.render(f"Background: {bg_label}", True, self.color_value)
        surface.blit(bg_surf, (img_x, info_y))

    def _scale_background(
        self, bg_surface: pygame.Surface, max_width: int, max_height: int
    ) -> pygame.Surface:
        """Scale background to fit within preview area while preserving aspect ratio.

        Args:
            bg_surface: Original background surface
            max_width: Maximum width
            max_height: Maximum height

        Returns:
            Scaled background surface
        """
        bg_width, bg_height = bg_surface.get_size()

        # Calculate scaling factor
        scale_x = max_width / bg_width
        scale_y = max_height / bg_height
        scale = min(scale_x, scale_y)

        new_width = int(bg_width * scale)
        new_height = int(bg_height * scale)

        return pygame.transform.smoothscale(bg_surface, (new_width, new_height))

    def _draw_placeholder_grid(
        self, surface: pygame.Surface, x: int, y: int, width: int, height: int
    ) -> None:
        """Draw a placeholder grid pattern when no background is available.

        Args:
            surface: Surface to draw on
            x: Grid X position
            y: Grid Y position
            width: Grid width
            height: Grid height
        """
        # Create placeholder surface
        placeholder = pygame.Surface((width, height), pygame.SRCALPHA)
        placeholder.fill(self.color_grid_bg)

        # Draw grid pattern
        grid_spacing = 20
        for gx in range(0, width, grid_spacing):
            pygame.draw.line(placeholder, self.color_grid, (gx, 0), (gx, height), 1)
        for gy in range(0, height, grid_spacing):
            pygame.draw.line(placeholder, self.color_grid, (0, gy), (width, gy), 1)

        surface.blit(placeholder, (x, y))
