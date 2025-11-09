"""Thread-safe event bus bridging PySide6 tool window and Pygame scenario editor.

Directions:
    UI -> Game: publish() / drain_events()
    Game -> UI: publish_to_ui() / drain_ui_events()

This keeps responsibilities clear and avoids the widget consuming its own outbound events.
"""
from __future__ import annotations

import multiprocessing
from queue import Empty
from typing import List, Optional
from .editor_events import EditorEvent

# Use multiprocessing.Queue for inter-process communication
# These will be set by init_queues() from the main process
_EVENT_QUEUE: Optional[multiprocessing.Queue] = None        # UI -> Game
_EVENT_QUEUE_UI: Optional[multiprocessing.Queue] = None     # Game -> UI


def init_queues(ui_to_game: multiprocessing.Queue, game_to_ui: multiprocessing.Queue) -> None:
    """Initialize the queues (must be called from each process).
    
    Args:
        ui_to_game: Queue for events from UI to Game
        game_to_ui: Queue for events from Game to UI
    """
    global _EVENT_QUEUE, _EVENT_QUEUE_UI
    _EVENT_QUEUE = ui_to_game
    _EVENT_QUEUE_UI = game_to_ui


def publish(evt: EditorEvent) -> None:
    """Publish an event from any thread."""
    if _EVENT_QUEUE is not None:
        _EVENT_QUEUE.put(evt)


def drain_events(max_batch: int = 128) -> List[EditorEvent]:
    """Collect all pending events (non-blocking)."""
    if _EVENT_QUEUE is None:
        return []
    out: List[EditorEvent] = []
    for _ in range(max_batch):
        try:
            out.append(_EVENT_QUEUE.get_nowait())
        except Empty:
            break
    return out


def publish_to_ui(evt: EditorEvent) -> None:
    """Publish event from game thread to the tool window."""
    if _EVENT_QUEUE_UI is not None:
        _EVENT_QUEUE_UI.put(evt)


def drain_ui_events(max_batch: int = 128) -> List[EditorEvent]:
    """Drain events destined for the tool window (game -> UI)."""
    if _EVENT_QUEUE_UI is None:
        return []
    out: List[EditorEvent] = []
    for _ in range(max_batch):
        try:
            out.append(_EVENT_QUEUE_UI.get_nowait())
        except Empty:
            break
    return out
