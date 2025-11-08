"""
Sprite Repository - Handles loading and caching sprite images.
"""

import pygame
from typing import Optional
from pathlib import Path

from config import get_character_sprite_path, BACKGROUND_SPRITES_DIR
from logger.logger import get_logger

logger = get_logger(__name__)


class SpriteRepository:
    """Repository for sprite image access."""
    
    def __init__(self):
        self._sprite_cache: dict[str, pygame.Surface] = {}
        self._background_cache: dict[str, pygame.Surface] = {}
    
    def load_character_sprite(self, filename: str) -> Optional[pygame.Surface]:
        """
        Load a character sprite image.
        
        Args:
            filename: Sprite filename (e.g., "warrior.png")
            
        Returns:
            Pygame Surface or None if not found
        """
        cache_key = f"char_{filename}"
        
        if cache_key in self._sprite_cache:
            return self._sprite_cache[cache_key]
        
        try:
            path = get_character_sprite_path(filename)
            surface = pygame.image.load(str(path)).convert_alpha()
            self._sprite_cache[cache_key] = surface
            logger.debug(f"Loaded character sprite: {filename}")
            return surface
        except pygame.error:
            logger.error(f"Failed to load sprite: {filename}")
            return None
        except Exception:
            logger.exception(f"Error loading sprite: {filename}")
            return None
    
    def load_background(self, filename: str) -> Optional[pygame.Surface]:
        """
        Load a background image.
        
        Args:
            filename: Background filename (e.g., "grass_bg.jpg")
            
        Returns:
            Pygame Surface or None if not found
        """
        if filename in self._background_cache:
            return self._background_cache[filename]
        
        try:
            path = BACKGROUND_SPRITES_DIR / filename
            surface = pygame.image.load(str(path)).convert()
            self._background_cache[filename] = surface
            logger.debug(f"Loaded background: {filename}")
            return surface
        except pygame.error:
            logger.error(f"Failed to load background: {filename}")
            return None
        except Exception:
            logger.exception(f"Error loading background: {filename}")
            return None
    
    def character_sprite_exists(self, filename: str) -> bool:
        """Check if a character sprite file exists."""
        path = get_character_sprite_path(filename)
        return path.exists()
    
    def background_exists(self, filename: str) -> bool:
        """Check if a background file exists."""
        path = BACKGROUND_SPRITES_DIR / filename
        return path.exists()
    
    def list_character_sprites(self) -> list[str]:
        """List all available character sprite files."""
        from config import CHARACTER_SPRITES_DIR
        try:
            files = [
                f.name for f in CHARACTER_SPRITES_DIR.iterdir()
                if f.suffix in ['.png', '.jpg', '.jpeg']
                and 'bg' not in f.name.lower()
                and 'silhouette' not in f.name.lower()
            ]
            return sorted(files)
        except Exception:
            logger.exception("Failed to list character sprites")
            return []
    
    def list_backgrounds(self) -> list[str]:
        """List all available background files."""
        try:
            files = [
                f.name for f in BACKGROUND_SPRITES_DIR.iterdir()
                if f.suffix in ['.png', '.jpg', '.jpeg']
            ]
            return sorted(files)
        except Exception:
            logger.exception("Failed to list backgrounds")
            return []
    
    def clear_cache(self) -> None:
        """Clear sprite cache."""
        self._sprite_cache.clear()
        self._background_cache.clear()
        logger.debug("Sprite cache cleared")
