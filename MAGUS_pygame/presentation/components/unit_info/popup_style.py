"""
Popup styling and layout constants for unit info popup.
"""

import pygame


class PopupStyle:
    """Small struct to keep popup sizes, paddings, fonts, and colors consistent."""

    def __init__(self):
        # Dimensions
        self.width = 600
        self.height = 700
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
        self.color_header_skills = (100, 200, 255)
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
