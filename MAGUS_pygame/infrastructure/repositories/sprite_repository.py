"""
Sprite Repository - Handles loading and caching sprite images.
"""


import pygame
from config import BACKGROUND_SPRITES_DIR, get_character_sprite_path
from logger.logger import get_logger

logger = get_logger(__name__)


class SpriteRepository:
    """Repository for sprite image access."""

    def __init__(self):
        self._sprite_cache: dict[str, pygame.Surface] = {}
        self._background_cache: dict[str, pygame.Surface] = {}

    def load_character_sprite(self, filename: str, max_size: int = 80) -> pygame.Surface | None:
        """
        Load a character sprite image and scale it to fit within hex.

        Args:
            filename: Sprite filename (e.g., "warrior.png")
            max_size: Maximum width/height in pixels (default 80 to fit in hex)

        Returns:
            Pygame Surface or None if not found
        """
        cache_key = f"char_{filename}_{max_size}"

        if cache_key in self._sprite_cache:
            return self._sprite_cache[cache_key]

        try:
            path = get_character_sprite_path(filename)
            surface = pygame.image.load(str(path)).convert_alpha()

            # Scale down to fit within hex
            original_width = surface.get_width()
            original_height = surface.get_height()

            if original_width > max_size or original_height > max_size:
                # Calculate scale factor to fit within max_size
                scale_factor = min(max_size / original_width, max_size / original_height)
                new_width = int(original_width * scale_factor)
                new_height = int(original_height * scale_factor)
                surface = pygame.transform.smoothscale(surface, (new_width, new_height))
                logger.debug(
                    f"Scaled sprite {filename} from {original_width}x{original_height} to {new_width}x{new_height}"
                )

            self._sprite_cache[cache_key] = surface
            logger.debug(f"Loaded character sprite: {filename}")
            return surface
        except pygame.error:
            logger.error(f"Failed to load sprite: {filename}")
            return None
        except Exception:
            logger.exception(f"Error loading sprite: {filename}")
            return None

    def load_background(self, filename: str) -> pygame.Surface | None:
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
                f.name
                for f in CHARACTER_SPRITES_DIR.iterdir()
                if f.suffix in [".png", ".jpg", ".jpeg"]
                and "bg" not in f.name.lower()
                and "silhouette" not in f.name.lower()
            ]
            return sorted(files)
        except Exception:
            logger.exception("Failed to list character sprites")
            return []

    def list_backgrounds(self) -> list[str]:
        """List all available background files."""
        try:
            files = [
                f.name
                for f in BACKGROUND_SPRITES_DIR.iterdir()
                if f.suffix in [".png", ".jpg", ".jpeg"]
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
