"""
Unit information popup display.
Shows detailed unit stats when right-clicking on a unit.
"""

import os

import pygame
from config import HEIGHT, UI_ACTIVE, UI_BORDER, UI_INACTIVE, UI_TEXT, WIDTH
from systems.combat_stats import compute_effective_combat_stats
from systems.weapon_wielding import get_wielding_info


class PopupStyle:
    """Small struct to keep popup sizes, paddings, fonts, and colors consistent."""

    def __init__(self):
        # Dimensions
        self.width = 400
        self.height = 550
        self.border_radius = 10

        # Layout/padding
        self.padding = 20
        self.section_gap = 10
        self.line_gap = 10
        self.tab_height = 35
        self.tab_gap = 5
        self.tab_margin_bottom = 15
        self.stat_row_height = 28
        self.attribute_row_height = 22

        # Overlay/background
        self.overlay_alpha = 150
        self.bg_color = (40, 40, 50)

        # Header colors
        self.color_header_health = (100, 200, 255)
        self.color_header_combat = (255, 100, 100)
        self.color_header_attributes = (100, 255, 100)
        self.color_header_equipment = (255, 200, 100)
        self.color_header_armor = (200, 200, 100)
        self.color_header_conditions = (200, 100, 255)

        # Bars/colors
        self.bar_bg = (60, 60, 60)
        self.fp_fill = (70, 130, 220)
        self.ep_fill = (220, 70, 70)

        # Health section layout
        self.health_bar_width = 200
        self.health_bar_height = 20
        self.health_bar_x_offset = 150
        self.health_bar_y_adjust = 2
        self.health_ep_bar_delta_y = 28

        # Silhouette sizing in Armor tab
        self.silhouette_max_width = 300
        self.silhouette_max_height = 380

        # Close text
        self.close_text_bottom_margin = 10

        # Fonts
        self.title_font = pygame.font.SysFont(None, 32, bold=True)
        self.header_font = pygame.font.SysFont(None, 28, bold=True)
        self.text_font = pygame.font.SysFont(None, 24)
        self.small_font = pygame.font.SysFont(None, 20)


class UnitInfoPopup:
    """Popup window for displaying detailed unit information with tabs."""

    def __init__(self):
        self.visible = False
        self.unit = None
        self.popup_rect = None
        self.cached_wield_info = None  # Cache to avoid recalculating every frame
        self.current_tab = "stats"  # "stats", "equipment", "armor", "conditions"
        self.tab_buttons = []  # Will store tab button rects
        self.style = PopupStyle()

        # Load humanoid silhouette image for armor display
        self.silhouette_image = None
        try:
            magus_pygame_dir = os.path.dirname(os.path.dirname(__file__))
            sprites_dir = os.path.join(magus_pygame_dir, "assets", "sprites", "characters")
            silhouette_path = os.path.join(sprites_dir, "humanoid_silhouette.png")
            self.silhouette_image = pygame.image.load(silhouette_path).convert_alpha()
        except Exception as e:
            print(f"[POPUP] Could not load humanoid_silhouette.png: {e}")

    def show(self, unit) -> None:
        """Show popup for the given unit."""
        self.visible = True
        self.unit = unit
        self.current_tab = "stats"  # Reset to first tab
        self.refresh_cached_wield_info()

    def hide(self) -> None:
        """Hide the popup."""
        self.visible = False
        self.unit = None
        self.cached_wield_info = None

    def toggle(self, unit) -> None:
        """Toggle popup visibility for the given unit."""
        if self.visible and self.unit == unit:
            self.hide()
        else:
            self.show(unit)

    def refresh_cached_wield_info(self) -> None:
        """Refresh cached wielding info based on current unit and weapon."""
        if not self.unit or not getattr(self.unit, "weapon", None):
            self.cached_wield_info = None
            return
        weapon = self.unit.weapon
        if weapon.get("wield_mode") == "Változó":
            self.cached_wield_info = get_wielding_info(self.unit, weapon)
        else:
            self.cached_wield_info = None

    def handle_click(self, mx: int, my: int) -> bool:
        """
        Handle click within popup (e.g., tab switching).
        Returns True if click was handled.
        """
        if not self.visible:
            return False

        # Check tab button clicks
        for tab_name, tab_rect in self.tab_buttons:
            if tab_rect.collidepoint(mx, my):
                self.current_tab = tab_name
                return True

        return False

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the popup on screen."""
        if not self.visible or not self.unit:
            return

        # Popup dimensions
        popup_width = self.style.width
        popup_height = self.style.height
        popup_x = (WIDTH - popup_width) // 2
        popup_y = (HEIGHT - popup_height) // 2

        self.popup_rect = pygame.Rect(popup_x, popup_y, popup_width, popup_height)

        # Semi-transparent background overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, self.style.overlay_alpha))
        screen.blit(overlay, (0, 0))

        # Popup background
        pygame.draw.rect(
            screen, self.style.bg_color, self.popup_rect, border_radius=self.style.border_radius
        )
        pygame.draw.rect(
            screen, UI_BORDER, self.popup_rect, width=3, border_radius=self.style.border_radius
        )

        # Draw content
        y_offset = popup_y + 15
        x_left = popup_x + self.style.padding
        x_right = popup_x + popup_width - self.style.padding

        # Title - Unit Name
        title_text = self.style.title_font.render(self.unit.name, True, (255, 215, 0))
        screen.blit(title_text, (x_left, y_offset))
        y_offset += 40

        # Draw tabs
        y_offset = self._draw_tabs(screen, x_left, x_right, y_offset)
        y_offset += self.style.tab_margin_bottom

        # Draw content based on selected tab
        if self.current_tab == "stats":
            y_offset = self._draw_stats_tab(screen, x_left, x_right, y_offset)
        elif self.current_tab == "equipment":
            y_offset = self._draw_equipment_tab(screen, x_left, x_right, y_offset)
        elif self.current_tab == "armor":
            y_offset = self._draw_armor_tab(screen, x_left, x_right, y_offset, popup_x, popup_width)
        elif self.current_tab == "conditions":
            y_offset = self._draw_conditions_tab(screen, x_left, x_right, y_offset)

        # Close instruction
        close_surface = self.style.small_font.render(
            "(Click outside window to close)", True, (150, 150, 150)
        )
        close_rect = close_surface.get_rect()
        close_rect.bottom = popup_y + popup_height - self.style.close_text_bottom_margin
        close_rect.right = popup_x + popup_width - self.style.padding
        screen.blit(close_surface, close_rect)

    def _draw_tabs(self, screen: pygame.Surface, x_left: int, x_right: int, y: int) -> int:
        """Draw tab buttons. Returns new y offset."""
        tabs = [
            ("stats", "Stats"),
            ("equipment", "Equipment"),
            ("armor", "Armor"),
            ("conditions", "Conditions"),
        ]

        tab_width = (x_right - x_left) // len(tabs)
        self.tab_buttons = []

        for i, (tab_id, tab_label) in enumerate(tabs):
            tab_x = x_left + (i * tab_width)
            tab_rect = pygame.Rect(tab_x, y, tab_width - self.style.tab_gap, self.style.tab_height)
            self.tab_buttons.append((tab_id, tab_rect))

            # Tab background
            is_active = self.current_tab == tab_id
            tab_color = UI_ACTIVE if is_active else UI_INACTIVE
            pygame.draw.rect(screen, tab_color, tab_rect, border_radius=5)
            pygame.draw.rect(screen, UI_BORDER, tab_rect, width=2, border_radius=5)

            # Tab label
            label_text = self.style.small_font.render(tab_label, True, UI_TEXT)
            label_rect = label_text.get_rect(center=tab_rect.center)
            screen.blit(label_text, label_rect)

        return y + self.style.tab_height + self.style.line_gap

    def _draw_stats_tab(self, screen: pygame.Surface, x_left: int, x_right: int, y: int) -> int:
        """Draw stats tab content. Returns new y offset."""
        # Health/Fatigue Points
        y = self._draw_health_section(screen, x_left, y)
        y += self.style.section_gap

        # Combat Stats
        y = self._draw_combat_stats(screen, x_left, y)
        y += self.style.section_gap

        # Attributes (Tulajdonságok)
        y = self._draw_attributes(screen, x_left, y)

        return y

    def _draw_equipment_tab(self, screen: pygame.Surface, x_left: int, x_right: int, y: int) -> int:
        """Draw equipment tab content. Returns new y offset."""
        # Equipped Weapon
        y = self._draw_weapon_info(screen, x_left, x_right, y)
        y += 10

        # TODO: Add armor, items, etc.

        return y

    def _draw_armor_tab(
        self,
        screen: pygame.Surface,
        x_left: int,
        x_right: int,
        y: int,
        popup_x: int,
        popup_width: int,
    ) -> int:
        """Draw armor tab content with humanoid silhouette. Returns new y offset."""
        # Header
        header = self.style.header_font.render(
            "Armor Coverage", True, self.style.color_header_armor
        )
        screen.blit(header, (x_left, y))
        y += 35

        if not self.silhouette_image:
            # Fallback if image not loaded
            no_image = self.style.text_font.render(
                "Silhouette image not available", True, (150, 150, 150)
            )
            screen.blit(no_image, (x_left + 10, y))
            return y + 30

        # Calculate centered position for silhouette
        img_width = self.silhouette_image.get_width()
        img_height = self.silhouette_image.get_height()

        # Scale if needed to fit in popup
        max_width = self.style.silhouette_max_width
        max_height = self.style.silhouette_max_height
        scale = min(max_width / img_width, max_height / img_height, 1.0)

        if scale < 1.0:
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            scaled_image = pygame.transform.smoothscale(
                self.silhouette_image, (new_width, new_height)
            )
        else:
            scaled_image = self.silhouette_image
            new_width = img_width
            new_height = img_height

        # Center the image in the popup
        img_x = popup_x + (popup_width - new_width) // 2
        img_y = y

        # Draw the silhouette
        screen.blit(scaled_image, (img_x, img_y))

        # Future: Draw colored overlays on body parts using unit.armor

        y += new_height + 10

        # Placeholder text for armor pieces
        armor_text = self.style.small_font.render(
            "(Armor data not yet implemented)", True, (150, 150, 150)
        )
        armor_rect = armor_text.get_rect(center=(popup_x + popup_width // 2, y))
        screen.blit(armor_text, armor_rect)

        return y + 30

    def _draw_conditions_tab(
        self, screen: pygame.Surface, x_left: int, x_right: int, y: int
    ) -> int:
        """Draw conditions tab content. Returns new y offset."""
        y = self._draw_conditions(screen, x_left, y)
        return y

    def _draw_health_section(self, screen: pygame.Surface, x: int, y: int) -> int:
        """Draw FP/ÉP section. Returns new y offset."""
        # Header
        header = self.style.header_font.render("Health", True, self.style.color_header_health)
        screen.blit(header, (x, y))
        y += 30

        # FP (Fatigue Points)
        fp_current = self.unit.current_fp
        fp_max = self.unit.FP
        fp_text = self.style.text_font.render(f"FP: {fp_current} / {fp_max}", True, UI_TEXT)
        screen.blit(fp_text, (x + 10, y))

        # FP bar
        bar_width = self.style.health_bar_width
        bar_height = self.style.health_bar_height
        bar_x = x + self.style.health_bar_x_offset
        bar_y = y + self.style.health_bar_y_adjust

        # Background bar
        pygame.draw.rect(
            screen, self.style.bar_bg, (bar_x, bar_y, bar_width, bar_height), border_radius=5
        )

        # Fill bar (blue for FP)
        if fp_max > 0:
            fill_width = int((fp_current / fp_max) * bar_width)
            pygame.draw.rect(
                screen, self.style.fp_fill, (bar_x, bar_y, fill_width, bar_height), border_radius=5
            )

        pygame.draw.rect(
            screen, UI_BORDER, (bar_x, bar_y, bar_width, bar_height), width=2, border_radius=5
        )
        y += 30

        # ÉP (Health Points)
        ep_current = self.unit.current_ep
        ep_max = self.unit.EP
        ep_text = self.style.text_font.render(f"ÉP: {ep_current} / {ep_max}", True, UI_TEXT)
        screen.blit(ep_text, (x + 10, y))

        # ÉP bar
        pygame.draw.rect(
            screen,
            self.style.bar_bg,
            (bar_x, bar_y + self.style.health_ep_bar_delta_y, bar_width, bar_height),
            border_radius=5,
        )

        # Fill bar (red for ÉP)
        if ep_max > 0:
            fill_width = int((ep_current / ep_max) * bar_width)
            pygame.draw.rect(
                screen,
                self.style.ep_fill,
                (bar_x, bar_y + self.style.health_ep_bar_delta_y, fill_width, bar_height),
                border_radius=5,
            )

        pygame.draw.rect(
            screen,
            UI_BORDER,
            (bar_x, bar_y + self.style.health_ep_bar_delta_y, bar_width, bar_height),
            width=2,
            border_radius=5,
        )
        y += 35

        return y

    def _draw_combat_stats(self, screen: pygame.Surface, x: int, y: int) -> int:
        """Draw combat statistics with breakdown. Returns new y offset."""
        # Header
        header = self.style.header_font.render("Combat Stats", True, self.style.color_header_combat)
        screen.blit(header, (x, y))
        y += 30

        # Use centralized combat stat computation for breakdown
        breakdown = compute_effective_combat_stats(self.unit)
        base = breakdown["base"]
        weapon = breakdown["weapon"]
        wielding = breakdown["wielding"]

        stats = [
            ("KÉ", base.get("KE", 0), weapon.get("KE", 0), wielding.get("KE", 0)),
            ("TÉ", base.get("TE", 0), weapon.get("TE", 0), wielding.get("TE", 0)),
            ("VÉ", base.get("VE", 0), weapon.get("VE", 0), wielding.get("VE", 0)),
            ("CÉ", base.get("CE", 0), weapon.get("CE", 0), 0),
        ]

        # Draw each stat with breakdown
        for i, (stat_name, base_val, weapon_bonus, wield_bonus) in enumerate(stats):
            stat_y = y + (i * self.style.stat_row_height)

            # Calculate total
            total = base_val + weapon_bonus + wield_bonus

            # Draw stat name and total
            stat_text = self.style.text_font.render(f"{stat_name}: {total}", True, (200, 200, 200))
            screen.blit(stat_text, (x + 10, stat_y))

            # Draw breakdown on the right side
            breakdown_x = x + 130
            parts = []

            # Base (white)
            if base_val != 0:
                parts.append((f"{base_val}", (200, 200, 200)))

            # Weapon bonus (green)
            if weapon_bonus != 0:
                parts.append((f"+{weapon_bonus}", (100, 255, 100)))

            # Wielding bonus (cyan/light blue)
            if wield_bonus != 0:
                parts.append((f"+{wield_bonus}", (100, 200, 255)))

            # Draw breakdown
            offset_x = 0
            for part_text, color in parts:
                part_surface = self.style.small_font.render(part_text, True, color)
                screen.blit(part_surface, (breakdown_x + offset_x, stat_y + 2))
                offset_x += part_surface.get_width() + 5

        y += self.style.stat_row_height * len(stats) + self.style.line_gap
        return y

    def _draw_attributes(self, screen: pygame.Surface, x: int, y: int) -> int:
        """Draw character attributes (Tulajdonságok). Returns new y offset."""
        # Header
        header = self.style.header_font.render(
            "Attributes", True, self.style.color_header_attributes
        )
        screen.blit(header, (x, y))
        y += 30

        if not self.unit.character_data:
            no_data = self.style.text_font.render("No data available", True, (150, 150, 150))
            screen.blit(no_data, (x + 10, y))
            return y + 30

        # Get attributes
        tulajdonsagok = self.unit.character_data.get("Tulajdonságok", {})

        # Common attributes to display
        attr_names = [
            "Erő",
            "Ügyesség",
            "Gyorsaság",
            "Állóképesség",
            "Egészség",
            "Szépség",
            "Intelligencia",
            "Akaraterő",
            "Asztrál",
        ]

        displayed = 0
        for attr_name in attr_names:
            if attr_name in tulajdonsagok:
                attr_data = tulajdonsagok[attr_name]
                if isinstance(attr_data, dict):
                    value = attr_data.get("value", 0)
                else:
                    value = attr_data

                # Draw in 3 columns
                col = displayed % 3
                row = displayed // 3
                attr_x = x + 10 + (col * 120)
                attr_y = y + (row * 22)

                # Abbreviate long names
                display_name = attr_name[:3] + "." if len(attr_name) > 6 else attr_name
                attr_text = self.style.small_font.render(f"{display_name}: {value}", True, UI_TEXT)
                screen.blit(attr_text, (attr_x, attr_y))

                displayed += 1

        if displayed == 0:
            no_attrs = self.style.text_font.render("No attributes", True, (150, 150, 150))
            screen.blit(no_attrs, (x + 10, y))
            y += 30
        else:
            rows = (displayed + 2) // 3
            y += rows * self.style.attribute_row_height + self.style.line_gap

        return y

    def _draw_weapon_info(self, screen: pygame.Surface, x_left: int, x_right: int, y: int) -> int:
        """Draw equipped weapon information. Returns new y offset."""
        # Header
        header = self.style.header_font.render(
            "Equipped Weapon", True, self.style.color_header_equipment
        )
        screen.blit(header, (x_left, y))
        y += 30

        if not self.unit.weapon:
            no_weapon = self.style.text_font.render("No weapon equipped", True, (150, 150, 150))
            screen.blit(no_weapon, (x_left + 10, y))
            return y + 30

        weapon = self.unit.weapon

        # Weapon name
        weapon_name = weapon.get("name", "Unknown Weapon")
        name_text = self.style.text_font.render(weapon_name, True, (255, 215, 0))
        screen.blit(name_text, (x_left + 10, y))
        y += 25

        # Damage range
        damage_min = weapon.get("damage_min", 1)
        damage_max = weapon.get("damage_max", 6)
        damage_text = self.style.small_font.render(
            f"Damage: {damage_min}-{damage_max}", True, UI_TEXT
        )
        screen.blit(damage_text, (x_left + 20, y))
        y += 22

        # Size category
        size_cat = weapon.get("size_category", 1)
        size_text = self.style.small_font.render(f"Size Category: {size_cat}", True, UI_TEXT)
        screen.blit(size_text, (x_left + 20, y))
        y += 22

        # Wield mode
        wield_mode = weapon.get("wield_mode", "1-handed")

        if wield_mode == "Változó":
            # Variable weapon - use cached info
            wield_info = self.cached_wield_info
            if wield_info:
                current_mode = wield_info["mode"]
                can_choose = wield_info["can_choose"]
                bonuses = wield_info["bonuses"]

                mode_color = (100, 255, 100) if can_choose else (255, 150, 100)
                mode_text = self.style.small_font.render(
                    f"Wielding: {current_mode}", True, mode_color
                )
                screen.blit(mode_text, (x_left + 20, y))
                y += 22

                if can_choose:
                    choice_text = self.style.small_font.render(
                        "(Can switch modes)", True, (150, 200, 150)
                    )
                    screen.blit(choice_text, (x_left + 30, y))
                    y += 20
                else:
                    forced_text = self.style.small_font.render(
                        "(Forced - need more stats)", True, (200, 150, 100)
                    )
                    screen.blit(forced_text, (x_left + 30, y))
                    y += 20

                # Show bonuses if wielding 2-handed with choice
                if current_mode == "2-handed" and can_choose and any(bonuses.values()):
                    bonus_parts = []
                    if bonuses["KE"] > 0:
                        bonus_parts.append(f"+{bonuses['KE']} KÉ")
                    if bonuses["TE"] > 0:
                        bonus_parts.append(f"+{bonuses['TE']} TÉ")
                    if bonuses["VE"] > 0:
                        bonus_parts.append(f"+{bonuses['VE']} VÉ")

                    bonus_str = ", ".join(bonus_parts)
                    bonus_text = self.style.small_font.render(
                        f"Bonuses: {bonus_str}", True, (100, 255, 255)
                    )
                    screen.blit(bonus_text, (x_left + 30, y))
                    y += 22
        else:
            # Fixed wield mode
            wield_text = self.style.small_font.render(f"Wield Mode: {wield_mode}", True, UI_TEXT)
            screen.blit(wield_text, (x_left + 20, y))
            y += 22

        return y + 5

    def _draw_conditions(self, screen: pygame.Surface, x: int, y: int) -> int:
        """Draw status conditions (placeholder). Returns new y offset."""
        # Header
        header = self.style.header_font.render(
            "Conditions", True, self.style.color_header_conditions
        )
        screen.blit(header, (x, y))
        y += 30

        # Placeholder for future conditions
        # TODO: Add condition system (stunned, bleeding, poisoned, etc.)
        no_conditions = self.style.text_font.render("None", True, (150, 150, 150))
        screen.blit(no_conditions, (x + 10, y))
        y += 25

        return y

    def is_click_outside(self, mx: int, my: int) -> bool:
        """Check if mouse click is outside the popup area."""
        if not self.visible or not self.popup_rect:
            return False
        return not self.popup_rect.collidepoint(mx, my)
