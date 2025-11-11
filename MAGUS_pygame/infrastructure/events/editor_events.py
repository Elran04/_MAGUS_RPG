"""Shared event types for Pygame <-> PySide6 editor tool window."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# Keep event payload as plain dicts for simple cross-process pickling
@dataclass(frozen=True)
class EditorEvent:
    type: str
    payload: dict[str, Any] | None = None


# Outgoing events from UI to game
EV_TOOL_SELECT = "tool_select"  # payload: {"tool": "team_a|team_b|obstacle|erase"}
EV_SAVE = "save"  # payload: None
EV_LOAD = "load"  # payload: None
EV_CLOSE = "close"  # payload: None
EV_NEW = "new"  # payload: None
EV_SET_NAME = "set_name"  # payload: {"name": str}
EV_SET_DESCRIPTION = "set_description"  # payload: {"description": str}
EV_SET_BACKGROUND = "set_background"  # payload: {"background": str | None}

# Outgoing events from game to UI (state updates)
EV_STATE_UPDATE = "state_update"  # payload: {"scenario_name": str, "tool": str, "counts": {...}}
EV_HINT = "hint"  # payload: {"text": str}
