"""
Domain mechanics - Reactions (Phase 2)

Exports reaction protocols and implementations.
"""

from .base import Reaction, ReactionCategory, ReactionResult
from .counterattack import CounterattackReaction
from .opportunity_attack import OpportunityAttackReaction
from .reaction_shieldbash import ReactionShieldBash

__all__ = [
    "ReactionCategory",
    "ReactionResult",
    "Reaction",
    "OpportunityAttackReaction",
    "CounterattackReaction",
    "ReactionShieldBash",
]
