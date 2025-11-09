"""
Domain mechanics - Reactions (Phase 2)

Exports reaction protocols and implementations.
"""
from .base import ReactionCategory, ReactionResult, Reaction
from .opportunity_attack import OpportunityAttackReaction

__all__ = [
    "ReactionCategory",
    "ReactionResult",
    "Reaction",
    "OpportunityAttackReaction",
]
