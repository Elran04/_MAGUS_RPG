"""Action system package.

Core player-initiated actions (movement, attack, equipment, special) and
later reaction mechanics (opportunity, counterattack, etc.).

Phase 1 provides minimal base abstractions and two core actions:
- AttackAction: basic weapon attack using resolve_attack()
- MovementAction: basic movement with pathfinding (no reactions yet)
"""

from __future__ import annotations

from .attack_action import AttackAction
from .base import Action, ActionCategory, ActionCost, ActionResult
from .movement_action import MovementAction

__all__ = [
    "ActionCategory",
    "ActionCost",
    "ActionResult",
    "Action",
    "AttackAction",
    "MovementAction",
]
