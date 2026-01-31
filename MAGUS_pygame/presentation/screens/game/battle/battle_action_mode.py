"""Action mode management for battle screen."""

from enum import Enum

from logger.logger import get_logger

logger = get_logger(__name__)


class ActionMode(Enum):
    """Current action mode for player input."""

    IDLE = "idle"
    MOVE = "move"
    ATTACK = "attack"
    INSPECT = "inspect"
