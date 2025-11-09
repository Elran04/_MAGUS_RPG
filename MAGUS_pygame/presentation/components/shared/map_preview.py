"""
Map preview component for scenario selector.

Displays scenario background image preview and map information
for scenario selection screens.
"""


import pygame
import math
from infrastructure.rendering.hex_grid import hex_to_pixel, get_grid_bounds
from config import HEX_SIZE
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
        self.preview_height = int((height - 100) * 0.85)  # 85% for image, 15% for info

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
        scenario_data: dict | None = None,
    ) -> None:
        """Draw map preview panel with hex grid rendering.

        Args:
            surface: Surface to draw on
            scenario_name: Name of the scenario/map
            background_surface: Pre-loaded background surface (or None)
            background_filename: Background filename for display (or None if not found)
            scenario_data: Scenario data dict with spawn_zones and obstacles (or None)
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

        # Create a subsurface/render target for the preview area
        preview_rect = pygame.Rect(img_x, img_y, self.preview_width, self.preview_height)
        
        if scenario_data:
            # Render the scenario like the editor does, then scale down
            self._draw_scenario_preview(surface, preview_rect, background_surface, scenario_data)
        elif background_surface:
            # Just show background if no scenario data
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

    def _draw_scenario_preview(
        self,
        surface: pygame.Surface,
        preview_rect: pygame.Rect,
        background_surface: pygame.Surface | None,
        scenario_data: dict,
    ) -> None:
        """Render scenario with hex grid like the editor, then scale to preview size.

        Args:
            surface: Surface to draw on
            preview_rect: Rectangle defining preview area
            background_surface: Background image (or None)
            scenario_data: Scenario data with spawn_zones and obstacles
        """
        # Get screen size from surface (this is what the editor uses)
        screen_width, screen_height = surface.get_size()
        
        # Create a full-resolution render surface (like in editor)
        full_render = pygame.Surface((screen_width, screen_height))
        full_render.fill((20, 20, 30))  # Dark background
        
        # Draw background at full resolution
        if background_surface:
            scaled_bg = pygame.transform.scale(background_surface, (screen_width, screen_height))
            full_render.blit(scaled_bg, (0, 0))
        
        # Draw hex grid with zones/obstacles using editor's approach
        self._draw_hex_grid_on_surface(full_render, scenario_data)
        
        # Scale down the full render to fit preview area
        scaled_preview = pygame.transform.smoothscale(
            full_render, (preview_rect.width, preview_rect.height)
        )
        surface.blit(scaled_preview, preview_rect.topleft)

    def _draw_hex_grid_on_surface(self, surface: pygame.Surface, scenario_data: dict) -> None:
        """Draw hex grid with zones and obstacles (replicates editor rendering).

        Args:
            surface: Surface to draw on
            scenario_data: Scenario data with spawn_zones and obstacles
        """
        # Colors matching editor
        color_team_a = (100, 150, 255, 140)  # Blue
        color_team_b = (255, 100, 100, 140)  # Red
        color_obstacle = (80, 80, 80, 180)   # Gray
        color_hex_border = (100, 100, 120)
        
        # Get grid bounds from infrastructure (same as editor)
        min_q, max_q, min_r, max_r = get_grid_bounds()
        
        # Extract zone data
        team_a_zones = set(
            (z['q'], z['r']) 
            for z in scenario_data.get('spawn_zones', {}).get('team_a', [])
        )
        team_b_zones = set(
            (z['q'], z['r']) 
            for z in scenario_data.get('spawn_zones', {}).get('team_b', [])
        )
        obstacles = set(
            (o['q'], o['r']) 
            for o in scenario_data.get('obstacles', [])
        )
        
        # Create overlay for transparent zones
        screen_w, screen_h = surface.get_size()
        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        
        # Draw hexes
        hex_size = HEX_SIZE
        margin = hex_size * 2
        
        for q in range(min_q, max_q + 1):
            for r in range(min_r, max_r + 1):
                cx, cy = hex_to_pixel(q, r)
                
                # Skip if off-screen
                if not (-margin < cx < screen_w + margin and -margin < cy < screen_h + margin):
                    continue
                
                # Draw hex border
                corners = self._get_hex_corners(cx, cy, hex_size)
                pygame.draw.polygon(surface, color_hex_border, corners, 2)
                
                # Draw zone overlays
                if (q, r) in team_a_zones:
                    pygame.draw.polygon(overlay, color_team_a, corners, 0)
                
                if (q, r) in team_b_zones:
                    pygame.draw.polygon(overlay, color_team_b, corners, 0)
                
                if (q, r) in obstacles:
                    pygame.draw.polygon(overlay, color_obstacle, corners, 0)
        
        # Blit overlay
        surface.blit(overlay, (0, 0))
        
        # Draw obstacle markers
        for q, r in obstacles:
            cx, cy = hex_to_pixel(q, r)
            if -margin < cx < screen_w + margin and -margin < cy < screen_h + margin:
                # Draw X for obstacle
                mark_size = hex_size // 3
                pygame.draw.line(surface, (200, 200, 200), 
                               (cx - mark_size, cy - mark_size), 
                               (cx + mark_size, cy + mark_size), 3)
                pygame.draw.line(surface, (200, 200, 200), 
                               (cx - mark_size, cy + mark_size), 
                               (cx + mark_size, cy - mark_size), 3)

    def _get_hex_corners(self, cx: int, cy: int, hex_size: int) -> list[tuple[int, int]]:
        """Get hex corner points for pointy-top hex.

        Args:
            cx: Center X
            cy: Center Y
            hex_size: Hex size

        Returns:
            List of corner points
        """
        corners = []
        for i in range(6):
            angle = math.pi / 180 * (60 * i - 30)  # Pointy-top orientation
            x = cx + hex_size * math.cos(angle)
            y = cy + hex_size * math.sin(angle)
            corners.append((int(x), int(y)))
        return corners

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
        """Draw a placeholder hex grid pattern when no background is available.

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

        # Draw hex grid pattern
        hex_size = 25
        hex_height = hex_size * 2
        hex_width = int(hex_size * 1.732)  # sqrt(3)
        
        # Offset rows for hex pattern
        rows = int(height / (hex_height * 0.75)) + 2
        cols = int(width / hex_width) + 2
        
        for row in range(rows):
            for col in range(cols):
                # Offset every other row
                offset_x = (hex_width // 2) if row % 2 == 1 else 0
                center_x = col * hex_width + offset_x
                center_y = int(row * hex_height * 0.75)
                
                # Draw hex outline
                if 0 <= center_x < width and 0 <= center_y < height:
                    self._draw_hex_outline(placeholder, center_x, center_y, hex_size, self.color_grid)

        surface.blit(placeholder, (x, y))
    
    def _draw_hex_outline(
        self, surface: pygame.Surface, cx: int, cy: int, size: int, color: tuple[int, int, int]
    ) -> None:
        """Draw a single hexagon outline.

        Args:
            surface: Surface to draw on
            cx: Center X
            cy: Center Y
            size: Hex size
            color: Line color
        """
        import math
        
        points = []
        for i in range(6):
            angle = math.pi / 3 * i - math.pi / 6  # Start from flat top
            px = cx + size * math.cos(angle)
            py = cy + size * math.sin(angle)
            points.append((px, py))
        
        # Draw hex outline
        for i in range(6):
            start = points[i]
            end = points[(i + 1) % 6]
            pygame.draw.line(surface, color, start, end, 1)
