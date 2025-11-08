"""
Character Repository - Handles loading and caching character data.
"""

import json
from typing import Optional
from pathlib import Path

from config import get_character_json_path
from logger.logger import get_logger

logger = get_logger(__name__)


class CharacterRepository:
    """Repository for character data access."""
    
    def __init__(self):
        self._cache: dict[str, dict] = {}
    
    def load(self, filename: str) -> Optional[dict]:
        """
        Load character JSON by filename.
        
        Args:
            filename: Character file name (e.g., "Warri.json")
            
        Returns:
            Character data dictionary or None if not found
        """
        # Check cache first
        if filename in self._cache:
            logger.debug(f"Character cache hit: {filename}")
            return self._cache[filename]
        
        # Load from disk
        try:
            path = get_character_json_path(filename)
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
                self._cache[filename] = data
                logger.info(f"Loaded character: {filename}")
                return data
        except FileNotFoundError:
            logger.error(f"Character file not found: {filename}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {filename}: {e}")
            return None
        except Exception:
            logger.exception(f"Failed to load character: {filename}")
            return None
    
    def exists(self, filename: str) -> bool:
        """Check if a character file exists."""
        if filename in self._cache:
            return True
        
        path = get_character_json_path(filename)
        return path.exists()
    
    def list_all(self) -> list[str]:
        """List all available character files."""
        from config import CHARACTERS_DIR
        try:
            files = [f for f in CHARACTERS_DIR.iterdir() if f.suffix == '.json']
            return [f.name for f in sorted(files)]
        except Exception:
            logger.exception("Failed to list character files")
            return []
    
    def clear_cache(self) -> None:
        """Clear the character cache."""
        self._cache.clear()
        logger.debug("Character cache cleared")
