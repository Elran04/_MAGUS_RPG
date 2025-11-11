"""Base class for scenario selection phases.

Provides common interface for phase-specific screens.
"""

from abc import ABC, abstractmethod

import pygame
from application.game_context import GameContext


class SelectionPhaseBase(ABC):
    """Abstract base for selection phase screens.

    Each phase (map, team A, team B, equipment) implements this interface
    to provide consistent behavior and easy extension.
    """

    def __init__(self, screen_width: int, screen_height: int, context: GameContext):
        """Initialize phase screen.

        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
            context: Game context for data access
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.context = context

        # Phase state
        self.completed = False
        self.cancelled = False

    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle input events.

        Args:
            event: Pygame event
        """
        pass

    @abstractmethod
    def draw(self, surface: pygame.Surface) -> None:
        """Draw the phase screen.

        Args:
            surface: Surface to draw on
        """
        pass

    @abstractmethod
    def can_proceed(self) -> bool:
        """Check if phase allows proceeding to next.

        Returns:
            True if phase is complete and can advance
        """
        pass

    def is_completed(self) -> bool:
        """Check if phase is completed.

        Returns:
            True if user confirmed and moved forward
        """
        return self.completed

    def is_cancelled(self) -> bool:
        """Check if phase was cancelled.

        Returns:
            True if user cancelled the phase
        """
        return self.cancelled

    def reset(self) -> None:
        """Reset phase state (when going back)."""
        self.completed = False
        self.cancelled = False
