"""
Központi logging konfiguráció a MAGUS pygame projekthez.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class PygameLogger:
    """Központi logger osztály a MAGUS pygame projekthez."""

    _instance: Optional["PygameLogger"] = None
    _initialized: bool = False

    def __new__(cls):
        """Singleton pattern - csak egy logger instance létezik."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Logger inicializálása."""
        if not self._initialized:
            self._setup_logging()
            PygameLogger._initialized = True

    def _setup_logging(self):
        """Logging rendszer beállítása."""
        # Logs mappa létrehozása
        log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)

        # Log fájl neve dátummal
        log_file = log_dir / f"pygame_{datetime.now().strftime('%Y%m%d')}.log"

        # Root logger konfigurálása
        root_logger = logging.getLogger("magus_pygame")
        root_logger.setLevel(logging.DEBUG)

        # Egyedi formátum
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Fájl handler - minden log a fájlba
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        # Console handler - csak INFO és felette
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        # Handlerek hozzáadása (csak ha még nincsenek)
        if not root_logger.handlers:
            root_logger.addHandler(file_handler)
            root_logger.addHandler(console_handler)

    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """
        Logger instance visszaadása a megadott névvel.

        Args:
            name: A logger neve (általában __name__)

        Returns:
            Konfigurált logger instance
        """
        # Biztosítjuk, hogy a singleton létrejött
        PygameLogger()
        return logging.getLogger(f"magus_pygame.{name}")


def get_logger(name: str) -> logging.Logger:
    """
    Kényelmi függvény logger instance megszerzéséhez.

    Args:
        name: A logger neve (általában __name__)

    Returns:
        Konfigurált logger instance

    Example:
        >>> from logger.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Játék elindult")
    """
    return PygameLogger.get_logger(name)
