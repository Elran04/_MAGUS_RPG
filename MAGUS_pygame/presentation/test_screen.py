"""
Test Screen - Minimal screen for testing the new architecture.
"""

import pygame
from typing import Optional

from domain.entities import Unit
from domain.value_objects import Position, Facing
from infrastructure.rendering.hex_grid import hex_to_pixel
from logger.logger import get_logger

logger = get_logger(__name__)


class TestScreen:
    """
    Simple test screen to verify architecture works.
    
    Displays:
    - A test unit on the hex grid
    - Unit info overlay
    - Basic controls
    """
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.running = True
        
        # Test unit
        self.test_unit: Optional[Unit] = None
        
        # UI fonts
        self.font_large = pygame.font.Font(None, 48)
        self.font_normal = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        
        logger.info("TestScreen initialized")
    
    def set_test_unit(self, unit: Unit) -> None:
        """Set the unit to display."""
        self.test_unit = unit
        logger.info(f"Test unit set: {unit.name}")
    
    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle input events."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False
                logger.info("ESC pressed - exiting test screen")
            
            # Test unit movement
            if self.test_unit and event.key == pygame.K_UP:
                new_pos = Position(self.test_unit.position.q, self.test_unit.position.r - 1)
                self.test_unit.move_to(new_pos)
                logger.debug(f"Unit moved to {new_pos}")
            
            elif self.test_unit and event.key == pygame.K_DOWN:
                new_pos = Position(self.test_unit.position.q, self.test_unit.position.r + 1)
                self.test_unit.move_to(new_pos)
                logger.debug(f"Unit moved to {new_pos}")
            
            elif self.test_unit and event.key == pygame.K_LEFT:
                new_pos = Position(self.test_unit.position.q - 1, self.test_unit.position.r)
                self.test_unit.move_to(new_pos)
                logger.debug(f"Unit moved to {new_pos}")
            
            elif self.test_unit and event.key == pygame.K_RIGHT:
                new_pos = Position(self.test_unit.position.q + 1, self.test_unit.position.r)
                self.test_unit.move_to(new_pos)
                logger.debug(f"Unit moved to {new_pos}")
            
            elif self.test_unit and event.key == pygame.K_r:
                self.test_unit.rotate_to(self.test_unit.facing.rotate_clockwise())
                logger.debug(f"Unit rotated to facing {self.test_unit.facing.direction}")
    
    def draw(self, surface: pygame.Surface) -> None:
        """Render the screen."""
        # Background
        surface.fill((20, 25, 35))
        
        # Title
        title = self.font_large.render("Architecture Test", True, (255, 255, 255))
        surface.blit(title, (self.width // 2 - title.get_width() // 2, 20))
        
        # Draw test unit if present
        if self.test_unit:
            self._draw_unit(surface, self.test_unit)
            self._draw_unit_info(surface, self.test_unit)
        else:
            msg = self.font_normal.render("No unit loaded", True, (150, 150, 150))
            surface.blit(msg, (self.width // 2 - msg.get_width() // 2, self.height // 2))
        
        # Instructions
        self._draw_instructions(surface)
    
    def _draw_unit(self, surface: pygame.Surface, unit: Unit) -> None:
        """Draw unit sprite and hex."""
        px, py = hex_to_pixel(unit.position)
        
        # Draw hex outline
        import math
        HEX_SIZE = 40
        points = []
        for i in range(6):
            angle = math.pi / 180 * (60 * i - 30)
            x = px + HEX_SIZE * math.cos(angle)
            y = py + HEX_SIZE * math.sin(angle)
            points.append((x, y))
        
        pygame.draw.polygon(surface, (100, 120, 140), points, width=2)
        
        # Draw unit sprite if available
        if unit.sprite:
            sprite_rect = unit.sprite.get_rect(center=(px, py))
            surface.blit(unit.sprite, sprite_rect)
        else:
            # Draw placeholder circle
            pygame.draw.circle(surface, (200, 100, 100), (px, py), 25)
        
        # Draw name
        name_surf = self.font_small.render(unit.name, True, (255, 255, 255))
        name_rect = name_surf.get_rect(center=(px, py - 60))
        surface.blit(name_surf, name_rect)
        
        # Draw facing indicator
        facing_angle = -90 + unit.facing.direction * 60
        angle_rad = math.radians(facing_angle)
        tip_x = px + 35 * math.cos(angle_rad)
        tip_y = py + 35 * math.sin(angle_rad)
        pygame.draw.line(surface, (255, 215, 0), (px, py), (tip_x, tip_y), 3)
    
    def _draw_unit_info(self, surface: pygame.Surface, unit: Unit) -> None:
        """Draw unit information panel."""
        panel_x = 20
        panel_y = 100
        line_height = 25
        
        info_lines = [
            f"Name: {unit.name}",
            f"Position: {unit.position}",
            f"Facing: {unit.facing.direction}",
            f"EP: {unit.ep}",
            f"FP: {unit.fp}",
            f"KÉ: {unit.combat_stats.KE}",
            f"TÉ: {unit.combat_stats.TE}",
            f"VÉ: {unit.combat_stats.VE}",
            f"Strength: {unit.attributes.strength}",
            f"Dexterity: {unit.attributes.dexterity}",
        ]
        
        for i, line in enumerate(info_lines):
            text = self.font_small.render(line, True, (200, 200, 200))
            surface.blit(text, (panel_x, panel_y + i * line_height))
    
    def _draw_instructions(self, surface: pygame.Surface) -> None:
        """Draw control instructions."""
        y = self.height - 100
        instructions = [
            "Arrow Keys: Move unit",
            "R: Rotate clockwise",
            "ESC: Exit"
        ]
        
        for i, text in enumerate(instructions):
            surf = self.font_small.render(text, True, (150, 150, 150))
            surface.blit(surf, (self.width // 2 - surf.get_width() // 2, y + i * 25))
    
    def is_running(self) -> bool:
        """Check if screen is still active."""
        return self.running
