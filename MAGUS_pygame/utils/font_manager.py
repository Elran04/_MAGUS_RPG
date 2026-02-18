"""
Font management utility for handling system and embedded fonts.
Automatically downloads and caches fonts if they're not found.
"""

import logging
import shutil
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError

import pygame

logger = logging.getLogger(__name__)


class FontManager:
    """Manages font loading with fallback and auto-download capabilities."""

    # Font sources - DejaVu fonts from official and mirror repositories
    DEJAVU_DOWNLOAD_URLS = [
        # Official SourceForge CDN
        "https://sourceforge.net/projects/dejavu/files/dejavu/2.37/DejaVuSans.ttf/download",
        # GitHub mirror (raw content)
        "https://raw.githubusercontent.com/dejavu-fonts/dejavu-fonts/2.37/ttf/DejaVuSans.ttf",
        # Alternative: fonts.google.com mirror (if available)
        "https://github.com/JetBrains/JetBrainsMono/raw/master/fonts/ttf/JetBrainsMono-Regular.ttf",  # Fallback to JetBrains Mono if DejaVu fails
    ]

    # Windows system fonts directory
    WINDOWS_FONTS_DIR = Path("C:\\Windows\\Fonts")

    def __init__(self, project_fonts_dir: Path | None = None):
        """Initialize font manager.

        Args:
            project_fonts_dir: Directory to cache downloaded fonts in the project.
                              If None, uses assets/fonts in the project.
        """
        self.project_fonts_dir = project_fonts_dir or Path(__file__).parent.parent / "assets" / "fonts"
        self.project_fonts_dir.mkdir(parents=True, exist_ok=True)

    def get_dejavu_font_path(self) -> Path:
        """Get path to DejaVuSans.ttf, downloading if necessary.

        Returns:
            Path object pointing to the font file

        Priority:
            1. Windows System Fonts (C:\\Windows\\Fonts\\DejaVuSans.ttf)
            2. Project fonts cache
            3. Auto-download to project fonts cache
            4. Default pygame font (None)
        """
        # Check Windows system fonts first
        windows_font = self.WINDOWS_FONTS_DIR / "DejaVuSans.ttf"
        if windows_font.exists():
            logger.info(f"Found system font at {windows_font}")
            return windows_font

        # Check project fonts cache
        project_font = self.project_fonts_dir / "DejaVuSans.ttf"
        if project_font.exists():
            logger.info(f"Found cached project font at {project_font}")
            return project_font

        # Try to download and cache the font
        logger.info("DejaVu font not found locally, attempting to download...")
        if self._download_font(project_font):
            return project_font

        # Fallback: log warning and return None for pygame default font
        logger.warning(
            "Could not find or download DejaVuSans.ttf. "
            "Will use pygame default font."
        )
        return None

    def _download_font(self, target_path: Path) -> bool:
        """Download DejaVuSans.ttf from online source.

        Args:
            target_path: Where to save the downloaded font

        Returns:
            True if download successful, False otherwise
        """
        for url in self.DEJAVU_DOWNLOAD_URLS:
            try:
                logger.info(f"Downloading font from {url}")
                with urlopen(url, timeout=10) as response:
                    with open(target_path, "wb") as f:
                        f.write(response.read())
                logger.info(f"Successfully downloaded font to {target_path}")
                return True
            except URLError as e:
                logger.warning(f"Failed to download from {url}: {e}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error downloading font: {e}")
                continue

        return False

    def copy_system_font_to_cache(self) -> bool:
        """Copy DejaVuSans.ttf from Windows Fonts to project cache.

        Useful for ensuring the font is available even if system fonts are moved.

        Returns:
            True if copy successful, False otherwise
        """
        windows_font = self.WINDOWS_FONTS_DIR / "DejaVuSans.ttf"
        project_font = self.project_fonts_dir / "DejaVuSans.ttf"

        if not windows_font.exists():
            logger.warning(f"System font not found at {windows_font}")
            return False

        if project_font.exists():
            logger.info("Font already cached in project")
            return True

        try:
            shutil.copy2(windows_font, project_font)
            logger.info(f"Copied font from {windows_font} to {project_font}")
            return True
        except Exception as e:
            logger.error(f"Failed to copy font: {e}")
            return False


# Global instance
_font_manager = FontManager()


def get_dejavu_font_path() -> Path | None:
    """Convenience function to get DejaVuSans.ttf path.

    Returns:
        Path object or None if font unavailable (will use pygame default)
    """
    return _font_manager.get_dejavu_font_path()


def load_font(font_path: Path | None, size: int) -> pygame.font.Font:
    """Safely load a font with fallback to pygame default.

    Args:
        font_path: Path to custom font file, or None for pygame default
        size: Font size in pixels

    Returns:
        pygame.font.Font object (custom font or system default)

    Example:
        >>> font = load_font(DEJAVU_FONT_PATH, 24)
        >>> # Safe to use even if DEJAVU_FONT_PATH is None
    """
    if font_path and isinstance(font_path, Path) and font_path.exists():
        try:
            return pygame.font.Font(str(font_path), size)
        except pygame.error as e:
            logger.warning(f"Failed to load font from {font_path}: {e}. Using default.")
            return pygame.font.Font(None, size)
    else:
        logger.debug("Using pygame default font")
        return pygame.font.Font(None, size)
