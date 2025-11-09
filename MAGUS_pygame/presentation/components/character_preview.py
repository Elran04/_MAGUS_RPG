"""
Character preview component for scenario selector.

Displays character information including sprite, stats, skills, and equipment
in a preview panel during team composition.
"""

import pygame
from pathlib import Path
from typing import Optional, Any

from logger.logger import get_logger

logger = get_logger(__name__)


class CharacterPreview:
    """Preview panel for character information with sprite and stats.
    
    Shows character sprite, combat stats, attributes, equipment, and skills
    in a formatted panel suitable for scenario selection screens.
    """
    
    def __init__(self, x: int, y: int, width: int, height: int):
        """Initialize character preview panel.
        
        Args:
            x: Panel X position
            y: Panel Y position
            width: Panel width
            height: Panel height
        """
        self.rect = pygame.Rect(x, y, width, height)
        
        # Fonts
        self.font_title = pygame.font.Font(None, 32)
        self.font_label = pygame.font.Font(None, 24)
        self.font_value = pygame.font.Font(None, 20)
        
        # Colors
        self.color_bg = (0, 0, 0, 180)
        self.color_title = (255, 215, 0)
        self.color_label = (255, 255, 255)
        self.color_value = (200, 200, 200)
        self.color_highlight = (180, 200, 180)
        self.color_missing = (230, 120, 120)
        
        # Sprite cache
        self._sprite_cache: dict[str, pygame.Surface] = {}
        
        logger.debug(f"CharacterPreview initialized at ({x}, {y}) size {width}x{height}")
    
    def draw(
        self,
        surface: pygame.Surface,
        character_data: Optional[dict[str, Any]],
        sprite_surface: Optional[pygame.Surface],
        character_filename: str = "",
        sprite_filename: str = ""
    ) -> None:
        """Draw character preview panel.
        
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
        title = self.font_title.render("Preview", True, self.color_title)
        surface.blit(title, (self.rect.x + 20, self.rect.y + 15))
        
        if not character_data or not sprite_surface:
            msg = self.font_label.render("No preview available", True, self.color_missing)
            surface.blit(msg, (self.rect.x + 20, self.rect.y + 60))
            return
        
        # Draw sprite (left side)
        sprite_x = self.rect.x + 20
        sprite_y = self.rect.y + 60
        
        # Scale sprite to fit (max 96x96)
        sprite_scaled = self._scale_sprite(sprite_surface, 96, 96)
        surface.blit(sprite_scaled, (sprite_x, sprite_y))
        
        # Draw character info (right side)
        info_x = self.rect.x + 140
        info_y = self.rect.y + 60
        
        # Character name
        name = character_data.get("Név", character_filename.replace('.json', ''))
        name_surf = self.font_label.render(f"Name: {name}", True, self.color_label)
        surface.blit(name_surf, (info_x, info_y))
        info_y += 25
        
        # Combat stats
        combat = character_data.get("Harci értékek", {})
        info_y = self._draw_combat_stats(surface, combat, info_x, info_y)
        info_y += 5
        
        # Attributes (subset)
        attributes = character_data.get("Tulajdonságok", {})
        info_y = self._draw_attributes(surface, attributes, info_x, info_y)
        info_y += 5
        
        # Equipment preview
        equipment = character_data.get("Felszerelés")
        info_y = self._draw_equipment(surface, equipment, info_x, info_y)
        info_y += 5
        
        # Skills preview
        skills = character_data.get("Képzettségek", [])
        self._draw_skills(surface, skills, info_x, info_y)
    
    def _scale_sprite(self, sprite: pygame.Surface, max_width: int, max_height: int) -> pygame.Surface:
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
    
    def _draw_combat_stats(self, surface: pygame.Surface, combat: dict[str, Any], x: int, y: int) -> int:
        """Draw combat statistics.
        
        Args:
            surface: Surface to draw on
            combat: Combat stats dict
            x: X position
            y: Y position
            
        Returns:
            Updated Y position after drawing
        """
        stat_keys = ["TÉ", "VÉ", "KÉ", "FP", "ÉP"]
        
        for key in stat_keys:
            value = combat.get(key, '-')
            line = self.font_value.render(f"{key}: {value}", True, self.color_label)
            surface.blit(line, (x, y))
            y += 18
        
        return y
    
    def _draw_attributes(self, surface: pygame.Surface, attributes: dict[str, Any], x: int, y: int) -> int:
        """Draw character attributes (subset).
        
        Args:
            surface: Surface to draw on
            attributes: Attributes dict
            x: X position
            y: Y position
            
        Returns:
            Updated Y position after drawing
        """
        attr_keys = ["Erő", "Ügyesség", "Gyorsaság", "Állóképesség"]
        
        for key in attr_keys:
            value = attributes.get(key, '-')
            # Truncate key for display
            display_key = key[:6] if len(key) > 6 else key
            line = self.font_value.render(f"{display_key}: {value}", True, self.color_value)
            surface.blit(line, (x, y))
            y += 18
        
        return y
    
    def _draw_equipment(self, surface: pygame.Surface, equipment: Any, x: int, y: int) -> int:
        """Draw equipment list preview (first 3 items).
        
        Args:
            surface: Surface to draw on
            equipment: Equipment data (dict with items list or list)
            x: X position
            y: Y position
            
        Returns:
            Updated Y position after drawing
        """
        # Handle both old (list) and new (dict with items) formats
        equipment_items: list[Any] = []
        if isinstance(equipment, dict):
            equipment_items = equipment.get("items", [])
        elif isinstance(equipment, list):
            equipment_items = equipment
        
        # Title
        eq_title = self.font_label.render("Equipment:", True, self.color_title)
        surface.blit(eq_title, (x, y))
        y += 20
        
        if not equipment_items:
            empty = self.font_value.render("No equipment", True, self.color_missing)
            surface.blit(empty, (x, y))
            return y + 18
        
        # Show first 3 items
        for item in equipment_items[:3]:
            if isinstance(item, dict):
                item_id = item.get("id", "?")
            else:
                item_id = str(item)
            
            line = self.font_value.render(f"- {item_id}", True, self.color_highlight)
            surface.blit(line, (x + 20, y))
            y += 16
        
        # Show "..." if more items exist
        if len(equipment_items) > 3:
            more = self.font_value.render(f"... +{len(equipment_items) - 3} more", True, self.color_value)
            surface.blit(more, (x + 20, y))
            y += 16
        
        return y
    
    def _draw_skills(self, surface: pygame.Surface, skills: list[Any], x: int, y: int) -> int:
        """Draw skills list preview (first 4 skills).
        
        Args:
            surface: Surface to draw on
            skills: Skills list
            x: X position
            y: Y position
            
        Returns:
            Updated Y position after drawing
        """
        # Title
        sk_title = self.font_label.render("Skills:", True, self.color_title)
        surface.blit(sk_title, (x, y))
        y += 20
        
        if not skills:
            empty = self.font_value.render("No skills", True, self.color_missing)
            surface.blit(empty, (x, y))
            return y + 18
        
        # Show first 4 skills
        for skill in skills[:4]:
            if isinstance(skill, dict):
                skill_id = skill.get("id", "?")
                skill_level = skill.get("Szint") or skill.get("%")
                if skill_level is not None:
                    skill_text = f"{skill_id} ({skill_level})"
                else:
                    skill_text = skill_id
            else:
                skill_text = str(skill)
            
            line = self.font_value.render(f"- {skill_text}", True, self.color_highlight)
            surface.blit(line, (x + 20, y))
            y += 16
        
        # Show "..." if more skills exist
        if len(skills) > 4:
            more = self.font_value.render(f"... +{len(skills) - 4} more", True, self.color_value)
            surface.blit(more, (x + 20, y))
            y += 16
        
        return y
