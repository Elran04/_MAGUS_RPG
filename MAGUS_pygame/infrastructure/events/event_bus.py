"""Event bus for inter-process communication using dependency injection.

Provides a clean, testable event bus for communication between
pygame game loop and PySide6 UI processes.
"""

from __future__ import annotations

import multiprocessing
from queue import Empty

from .editor_events import EditorEvent


class EditorEventBus:
    """Event bus for bidirectional communication between game and UI.

    Uses dependency injection for queue instances, making it testable
    and avoiding global state.

    Directions:
        UI -> Game: publish() / drain_events()
        Game -> UI: publish_to_ui() / drain_ui_events()
    """

    def __init__(
        self, ui_to_game_queue: multiprocessing.Queue, game_to_ui_queue: multiprocessing.Queue
    ):
        """Initialize event bus with injected queues.

        Args:
            ui_to_game_queue: Queue for events from UI to game
            game_to_ui_queue: Queue for events from game to UI
        """
        self._ui_to_game = ui_to_game_queue
        self._game_to_ui = game_to_ui_queue

    def publish(self, evt: EditorEvent) -> None:
        """Publish event from UI to game.

        Args:
            evt: Event to publish
        """
        self._ui_to_game.put(evt)

    def drain_events(self, max_batch: int = 128) -> list[EditorEvent]:
        """Collect all pending UI->game events (non-blocking).

        Args:
            max_batch: Maximum number of events to drain

        Returns:
            List of events (may be empty)
        """
        events: list[EditorEvent] = []
        for _ in range(max_batch):
            try:
                events.append(self._ui_to_game.get_nowait())
            except Empty:
                break
        return events

    def publish_to_ui(self, evt: EditorEvent) -> None:
        """Publish event from game to UI.

        Args:
            evt: Event to publish
        """
        self._game_to_ui.put(evt)

    def drain_ui_events(self, max_batch: int = 128) -> list[EditorEvent]:
        """Collect all pending game->UI events (non-blocking).

        Args:
            max_batch: Maximum number of events to drain

        Returns:
            List of events (may be empty)
        """
        events: list[EditorEvent] = []
        for _ in range(max_batch):
            try:
                events.append(self._game_to_ui.get_nowait())
            except Empty:
                break
        return events
