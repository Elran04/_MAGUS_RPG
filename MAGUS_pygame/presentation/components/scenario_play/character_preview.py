"""
Character preview component for scenario selector.

Displays character information including sprite, stats, skills, and equipment
in a three-column preview panel with scrollable sections during team composition.
"""

from typing import TYPE_CHECKING, Any

import pygame
from config.paths import DEJAVU_FONT_PATH
from logger.logger import get_logger

if TYPE_CHECKING:
    from application.game_context import GameContext

logger = get_logger(__name__)


class CharacterPreview:
    """Preview panel for character information with sprite and stats.

    Three-column layout:
    - Left: Sprite, Combat Stats, Attributes
    - Middle: Skills (scrollable)
    - Right: Equipment (scrollable)
    """

    def __init__(self, x: int, y: int, width: int, height: int, context: "GameContext"):
        """Initialize character preview panel.

        Args:
            x: Panel X position
            y: Panel Y position
            width: Panel width
            height: Panel height
            context: Game context for data access
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.context = context

        # Four-column layout sizing (custom percentages)
        self.col_padding = 15
        self._compute_columns(width)

        # Scroll positions for skills and equipment columns
        self.skills_scroll = 0
        self.equipment_scroll = 0
        self.scroll_speed = 20

        # Data lookup caches for names
        self._skill_names: dict[str, str] = {}
        self._equipment_names: dict[str, str] = {}

        # Tooltip state (stores full text when truncated)
        self._hover_tooltip: str | None = None
        self._hover_pos: tuple[int, int] | None = None

        # Fonts
        self.font_title = pygame.font.Font(DEJAVU_FONT_PATH, 24)
        self.font_section = pygame.font.Font(DEJAVU_FONT_PATH, 20)
        self.font_label = pygame.font.Font(DEJAVU_FONT_PATH, 16)
        self.font_value = pygame.font.Font(DEJAVU_FONT_PATH, 14)
        self.font_small = pygame.font.Font(DEJAVU_FONT_PATH, 12)

        # Colors
        self.color_bg = (0, 0, 0, 180)
        self.color_title = (255, 215, 0)
        self.color_section = (200, 200, 255)
        self.color_label = (255, 255, 255)
        self.color_value = (200, 200, 200)
        self.color_highlight = (180, 200, 180)
        self.color_missing = (230, 120, 120)
        self.color_divider = (80, 80, 100)
        self.color_scrollbar = (100, 100, 120)
        self.color_scrollbar_bg = (40, 40, 50)

        # Sprite cache
        self._sprite_cache: dict[str, pygame.Surface] = {}

        logger.debug(f"CharacterPreview initialized at ({x}, {y}) size {width}x{height}")

    def _compute_columns(self, total_width: int) -> None:
        """Compute custom column widths (15%, 35%, 25%, 25%) and starts."""
        w0 = int(total_width * 0.15)
        w1 = int(total_width * 0.35)
        w2 = int(total_width * 0.25)
        # Ensure exact sum by assigning the remainder to the last column
        w3 = max(0, total_width - (w0 + w1 + w2))
        self.col_widths = [w0, w1, w2, w3]
        self.col_starts = [0, w0, w0 + w1, w0 + w1 + w2]

    def handle_scroll(self, event: pygame.event.Event) -> None:
        """Handle scroll events for skills and equipment columns.

        Args:
            event: Pygame event
        """
        if event.type == pygame.MOUSEWHEEL:
            # Determine which column is being scrolled based on mouse position
            mouse_pos = pygame.mouse.get_pos()

            # Column 3 (skills)
            skills_col_x = self.rect.x + self.col_starts[2]
            if skills_col_x <= mouse_pos[0] < skills_col_x + self.col_widths[2]:
                self.skills_scroll = max(0, self.skills_scroll - event.y * self.scroll_speed)

            # Column 4 (equipment)
            equipment_col_x = self.rect.x + self.col_starts[3]
            if equipment_col_x <= mouse_pos[0] < equipment_col_x + self.col_widths[3]:
                self.equipment_scroll = max(0, self.equipment_scroll - event.y * self.scroll_speed)

    def draw(
        self,
        surface: pygame.Surface,
        character_data: dict[str, Any] | None,
        sprite_surface: pygame.Surface | None,
        character_filename: str = "",
        sprite_filename: str = "",
    ) -> None:
        """Draw character preview panel with three-column layout.

        Args:
            surface: Surface to draw on
            character_data: Character JSON data dict (or None if not loaded)
            sprite_surface: Pre-loaded sprite surface (or None)
            character_filename: Character filename for display
            sprite_filename: Sprite filename for display
        """
        # Draw panel background
        panel = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        panel.fill(self.color_bg)
        surface.blit(panel, self.rect.topleft)

        # Title
        title = self.font_title.render("Karakter előnézet", True, self.color_title)
        surface.blit(title, (self.rect.x + 20, self.rect.y + 15))

        if not character_data or not sprite_surface:
            msg = self.font_label.render("Előnézet nem elérhető", True, self.color_missing)
            surface.blit(msg, (self.rect.x + self.rect.width // 2 - 100, self.rect.y + 60))
            return

        # Draw column dividers
        divider1_x = self.rect.x + self.col_starts[1]
        divider2_x = self.rect.x + self.col_starts[2]
        divider3_x = self.rect.x + self.col_starts[3]
        pygame.draw.line(
            surface,
            self.color_divider,
            (divider1_x, self.rect.y + 50),
            (divider1_x, self.rect.bottom),
            2,
        )
        pygame.draw.line(
            surface,
            self.color_divider,
            (divider2_x, self.rect.y + 50),
            (divider2_x, self.rect.bottom),
            2,
        )
        pygame.draw.line(
            surface,
            self.color_divider,
            (divider3_x, self.rect.y + 50),
            (divider3_x, self.rect.bottom),
            2,
        )

        # COLUMN 1: Sprite
        self._draw_sprite_column(surface, character_data, sprite_surface, character_filename)

        # COLUMN 2: Combat Stats and Attributes
        self._draw_stats_column(surface, character_data)

        # COLUMN 3: Skills (scrollable)
        self._draw_skills_column(surface, character_data.get("Képzettségek", []))

        # COLUMN 4: Equipment (scrollable)
        self._draw_equipment_column(surface, character_data.get("Felszerelés"))

        # Tooltip (draw last so it's on top)
        if self._hover_tooltip and self._hover_pos:
            self._draw_tooltip(surface, self._hover_tooltip, self._hover_pos)
        # Reset tooltip for next frame
        self._hover_tooltip = None
        self._hover_pos = None

    def _draw_sprite_column(
        self,
        surface: pygame.Surface,
        character_data: dict[str, Any],
        sprite_surface: pygame.Surface,
        character_filename: str,
    ) -> None:
        """Draw first column with sprite and character name.

        Args:
            surface: Surface to draw on
            character_data: Character data
            sprite_surface: Character sprite
            character_filename: Character filename
        """
        col_x = self.rect.x + self.col_starts[0] + self.col_padding
        y = self.rect.y + 55

        # Character name
        name = character_data.get("Név", character_filename.replace(".json", ""))
        name_surf = self.font_label.render(name, True, self.color_label)
        # Center name in column
        name_x = col_x + (self.col_widths[0] - self.col_padding * 2 - name_surf.get_width()) // 2
        surface.blit(name_surf, (name_x, y))
        y += 35

        # Sprite (scaled to fit column)
        max_sprite_size = self.col_widths[0] - self.col_padding * 2 - 10
        sprite_scaled = self._scale_sprite(sprite_surface, max_sprite_size, max_sprite_size)
        sprite_rect = sprite_scaled.get_rect()
        # Center sprite in column
        sprite_x = col_x + (self.col_widths[0] - self.col_padding * 2 - sprite_rect.width) // 2
        surface.blit(sprite_scaled, (sprite_x, y))

    def _draw_stats_column(self, surface: pygame.Surface, character_data: dict[str, Any]) -> None:
        """Draw second column with combat stats and attributes using a compact table layout.

        Args:
            surface: Surface to draw on
            character_data: Character data
        """
        col_x = self.rect.x + self.col_starts[1] + self.col_padding
        y = self.rect.y + 55

        # Combat Stats Section
        combat = character_data.get("Harci értékek", {})
        section_title = self.font_section.render("Harci értékek", True, self.color_section)
        surface.blit(section_title, (col_x, y))
        y += 25

        # Draw combat stats in two columns
        combat_keys = ["KÉ", "TÉ", "VÉ", "CÉ", "FP", "ÉP"]
        combat_rows = self._build_table_rows(combat_keys, combat)
        y = self._draw_table(surface, combat_rows, col_x, y, columns=2, col_spacing=90)
        y += 10

        # Attributes Section
        attributes = character_data.get("Tulajdonságok", {})
        section_title = self.font_section.render("Tulajdonságok", True, self.color_section)
        surface.blit(section_title, (col_x, y))
        y += 25

        attr_keys = [
            "Erő",
            "Ügyesség",
            "Gyorsaság",
            "Állóképesség",
            "Egészség",
            "Intelligencia",
            "Akaraterő",
            "Asztrál",
            "Érzékelés",
            "Karizma",
        ]
        attr_rows = self._build_table_rows(attr_keys, attributes, shorten_keys=True)
        self._draw_table(surface, attr_rows, col_x, y, columns=2, col_spacing=140)

    def _scale_sprite(
        self, sprite: pygame.Surface, max_width: int, max_height: int
    ) -> pygame.Surface:
        """Scale sprite to fit within max dimensions while preserving aspect ratio.

        Args:
            sprite: Original sprite surface
            max_width: Maximum width
            max_height: Maximum height

        Returns:
            Scaled sprite surface
        """
        sprite_width, sprite_height = sprite.get_size()

        # Calculate scaling factor
        scale_x = max_width / sprite_width
        scale_y = max_height / sprite_height
        scale = min(scale_x, scale_y)

        new_width = int(sprite_width * scale)
        new_height = int(sprite_height * scale)

        return pygame.transform.smoothscale(sprite, (new_width, new_height))

    def _build_table_rows(
        self,
        keys: list[str],
        data: dict[str, Any],
        shorten_keys: bool = False,
    ) -> list[tuple[str, Any]]:
        """Prepare (key, value) rows for table drawing."""
        rows: list[tuple[str, Any]] = []
        for k in keys:
            v = data.get(k, "-")
            dk = k
            if shorten_keys and len(dk) > 9:
                dk = dk[:9] + "."
            rows.append((dk, v))
        return rows

    def _draw_table(
        self,
        surface: pygame.Surface,
        rows: list[tuple[str, Any]],
        x: int,
        y: int,
        columns: int = 2,
        col_spacing: int = 90,
        row_height: int = 22,
    ) -> int:
        """Draw rows in a multi-column table and return new y."""
        if not rows:
            return y
        import math

        per_col = math.ceil(len(rows) / columns)
        for idx, (label, value) in enumerate(rows):
            col_index = idx // per_col
            row_index = idx % per_col
            draw_x = x + col_index * col_spacing
            text = self.font_value.render(f"{label}: {value}", True, self.color_value)
            surface.blit(text, (draw_x, y + row_index * row_height))
        return y + per_col * row_height

    def _draw_skills_column(self, surface: pygame.Surface, skills: list[Any]) -> None:
        """Draw third column with scrollable skills list.

        Args:
            surface: Surface to draw on
            skills: Skills list
        """
        col_x = self.rect.x + self.col_starts[2] + self.col_padding
        col_width = self.col_widths[2] - self.col_padding * 2
        y_start = self.rect.y + 55

        # Section title
        title = self.font_section.render("Képzettségek", True, self.color_section)
        surface.blit(title, (col_x, y_start))

        # Create clipping rect for scrollable area
        content_y = y_start + 30
        content_height = self.rect.height - 90
        clip_rect = pygame.Rect(col_x, content_y, col_width, content_height)

        # Create subsurface for clipping
        subsurface = surface.subsurface(clip_rect)

        if not skills:
            empty = self.font_value.render("No skills", True, self.color_missing)
            subsurface.blit(empty, (5, 10))
            return

        # Calculate total height first
        total_height = len(skills) * 22

        # Clamp scroll position to prevent overflow
        max_scroll = max(0, total_height - content_height)
        self.skills_scroll = min(self.skills_scroll, max_scroll)
        self.skills_scroll = max(0, self.skills_scroll)

        # Draw skills with scroll offset
        y = -self.skills_scroll

        mouse_pos = pygame.mouse.get_pos()
        for skill in skills:
            if isinstance(skill, dict):
                skill_id = skill.get("id", "?")
                skill_name = self._get_skill_name(skill_id)  # Look up actual name
                skill_level = skill.get("Szint") or skill.get("%")
                if skill_level is not None:
                    skill_text = f"{skill_name} ({skill_level})"
                else:
                    skill_text = skill_name
            else:
                skill_text = str(skill)

            # Truncate if too long
            truncated = False
            if len(skill_text) > 25:
                truncated = True
                display_text = skill_text[:22] + "..."
            else:
                display_text = skill_text

            line = self.font_small.render(f"• {display_text}", True, self.color_value)
            if -30 < y < content_height:  # Only draw if visible
                subsurface.blit(line, (5, y))
                if truncated:
                    line_rect = pygame.Rect(
                        col_x + 5, content_y + y, line.get_width(), line.get_height()
                    )
                    if line_rect.collidepoint(mouse_pos):
                        self._hover_tooltip = skill_text
                        self._hover_pos = mouse_pos
            y += 22

        # Draw scrollbar if needed
        if total_height > content_height:
            self._draw_scrollbar(
                surface, clip_rect, self.skills_scroll, total_height, content_height
            )

    def _draw_equipment_column(self, surface: pygame.Surface, equipment: Any) -> None:
        """Draw fourth column with scrollable equipment list.

        Args:
            surface: Surface to draw on
            equipment: Equipment data
        """
        col_x = self.rect.x + self.col_starts[3] + self.col_padding
        col_width = self.col_widths[3] - self.col_padding * 2
        y_start = self.rect.y + 55

        # Section title
        title = self.font_section.render("Felszerelés", True, self.color_section)
        surface.blit(title, (col_x, y_start))

        # Parse equipment data
        equipment_items: list[Any] = []
        if isinstance(equipment, dict):
            equipment_items = equipment.get("items", [])
        elif isinstance(equipment, list):
            equipment_items = equipment

        # Create clipping rect for scrollable area
        content_y = y_start + 30
        content_height = self.rect.height - 90
        clip_rect = pygame.Rect(col_x, content_y, col_width, content_height)

        # Create subsurface for clipping
        subsurface = surface.subsurface(clip_rect)

        if not equipment_items:
            empty = self.font_value.render("No equipment", True, self.color_missing)
            subsurface.blit(empty, (5, 10))
            return

        # Calculate total height first
        total_height = len(equipment_items) * 22

        # Clamp scroll position to prevent overflow
        max_scroll = max(0, total_height - content_height)
        self.equipment_scroll = min(self.equipment_scroll, max_scroll)
        self.equipment_scroll = max(0, self.equipment_scroll)

        # Draw equipment with scroll offset
        y = -self.equipment_scroll

        mouse_pos = pygame.mouse.get_pos()
        for item in equipment_items:
            if isinstance(item, dict):
                item_id = item.get("id", "?")
                item_category = item.get("category", "general")
                item_name = self._get_equipment_name(item_id, item_category)  # Look up actual name
                item_qty = item.get("qty")

                if item_qty and item_qty > 1:
                    item_text = f"{item_name} x{item_qty}"
                else:
                    item_text = item_name
            else:
                item_text = str(item)

            # Truncate if too long
            truncated = False
            if len(item_text) > 25:
                truncated = True
                display_text = item_text[:22] + "..."
            else:
                display_text = item_text

            line = self.font_small.render(f"• {display_text}", True, self.color_value)
            if -30 < y < content_height:  # Only draw if visible
                subsurface.blit(line, (5, y))
                if truncated:
                    line_rect = pygame.Rect(
                        col_x + 5, content_y + y, line.get_width(), line.get_height()
                    )
                    if line_rect.collidepoint(mouse_pos):
                        self._hover_tooltip = item_text
                        self._hover_pos = mouse_pos
            y += 22

        # Draw scrollbar if needed
        if total_height > content_height:
            self._draw_scrollbar(
                surface, clip_rect, self.equipment_scroll, total_height, content_height
            )

    def _draw_scrollbar(
        self,
        surface: pygame.Surface,
        clip_rect: pygame.Rect,
        scroll_pos: int,
        content_height: int,
        visible_height: int,
    ) -> None:
        """Draw scrollbar for a column.

        Args:
            surface: Surface to draw on
            clip_rect: Clipping rectangle of the scrollable area
            scroll_pos: Current scroll position
            content_height: Total content height
            visible_height: Visible area height
        """
        scrollbar_width = 8
        scrollbar_x = clip_rect.right - scrollbar_width - 2
        scrollbar_y = clip_rect.y
        scrollbar_height = clip_rect.height

        # Draw scrollbar background
        bg_rect = pygame.Rect(scrollbar_x, scrollbar_y, scrollbar_width, scrollbar_height)
        pygame.draw.rect(surface, self.color_scrollbar_bg, bg_rect)

        # Calculate thumb size and position
        thumb_height = max(30, int((visible_height / content_height) * scrollbar_height))
        max_scroll = content_height - visible_height
        thumb_y = (
            scrollbar_y + int((scroll_pos / max_scroll) * (scrollbar_height - thumb_height))
            if max_scroll > 0
            else scrollbar_y
        )

        # Draw scrollbar thumb
        thumb_rect = pygame.Rect(scrollbar_x, thumb_y, scrollbar_width, thumb_height)
        pygame.draw.rect(surface, self.color_scrollbar, thumb_rect, border_radius=4)

    def _get_skill_name(self, skill_id: str) -> str:
        """Look up skill name from ID using the application layer facade."""
        if skill_id in self._skill_names:
            return self._skill_names[skill_id]

        readable_name = self.context.get_skill_name(skill_id)
        self._skill_names[skill_id] = readable_name
        return readable_name

    def _get_equipment_name(self, item_id: str, category: str) -> str:
        """Look up equipment name from ID and category using application layer facade."""
        cache_key = f"{category}:{item_id}"
        if cache_key in self._equipment_names:
            return self._equipment_names[cache_key]

        name = self.context.get_equipment_name(item_id, category)
        self._equipment_names[cache_key] = name
        return name

    def _draw_tooltip(self, surface: pygame.Surface, text: str, pos: tuple[int, int]) -> None:
        """Draw a simple tooltip near the mouse position."""
        padding = 6
        tooltip_surf = self.font_small.render(text, True, self.color_label)
        bg_rect = tooltip_surf.get_rect()
        bg_rect.x = pos[0] + 12
        bg_rect.y = pos[1] + 12
        bg_rect.inflate_ip(padding * 2, padding * 2)
        pygame.draw.rect(surface, (30, 30, 50, 220), bg_rect, border_radius=4)
        pygame.draw.rect(surface, self.color_divider, bg_rect, 1, border_radius=4)
        surface.blit(tooltip_surf, (bg_rect.x + padding, bg_rect.y + padding))
