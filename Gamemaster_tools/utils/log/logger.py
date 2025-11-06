"""
Központi logging konfiguráció a MAGUS RPG projekthez.
Egységes log formátumot és kezelést biztosít az alkalmazás minden részéhez.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class MagusLogger:
    """Központi logger osztály a MAGUS RPG projekthez."""

    _instance: Optional["MagusLogger"] = None
    _initialized: bool = False

    def __new__(cls) -> "MagusLogger":
        """Singleton pattern - csak egy logger instance létezik."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Logger inicializálása."""
        if not self._initialized:
            self._setup_logging()
            MagusLogger._initialized = True

    def _setup_logging(self) -> None:
        """Logging rendszer beállítása."""
        # Logs mappa létrehozása
        log_dir = Path(__file__).parent.parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)

        # Log fájl neve dátummal
        log_file = log_dir / f"magus_{datetime.now().strftime('%Y%m%d')}.log"

        # Root logger konfigurálása
        root_logger = logging.getLogger()
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
        MagusLogger()
        return logging.getLogger(name)


def get_logger(name: str) -> logging.Logger:
    """
    Kényelmi függvény logger instance megszerzéséhez.

    Args:
        name: A logger neve (általában __name__)

    Returns:
        Konfigurált logger instance

    Example:
        >>> from utils.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Alkalmazás elindult")
    """
    return MagusLogger.get_logger(name)
