"""
Battle log entry data structures for detailed event tracking.

Stores comprehensive information about combat events including round numbers,
participants, attack breakdowns, and all relevant combat parameters.
"""

from dataclasses import dataclass, field
from typing import Any

from domain.entities import Unit
from domain.mechanics.attack_resolution import AttackOutcome
from domain.value_objects import Position


@dataclass
class DetailedAttackData:
    """Detailed breakdown of an attack for logging purposes."""

    attacker_name: str
    defender_name: str
    round_number: int

    # Attack rolls and stats
    attack_roll: int
    all_te: int
    all_ve: int
    outcome: AttackOutcome

    # Positional modifiers
    is_flank_attack: bool
    is_rear_attack: bool
    facing_ignored_ve: bool  # VÉ from shield/weapon ignored due to facing

    # Damage details
    hit_zone: str | None = None
    zone_sfe: int = 0
    damage_to_fp: int = 0
    damage_to_ep: int = 0
    mandatory_ep_loss: int = 0
    armor_absorbed: int = 0
    stamina_spent_defender: int = 0

    # Combat modifiers on attacker
    attacker_penalties: dict[str, int] = field(default_factory=dict)  # {"stamina": -10, "injury": -5}
    attacker_buffs: dict[str, int] = field(default_factory=dict)  # {"charge": +5}

    # Combat modifiers on defender
    defender_penalties: dict[str, int] = field(default_factory=dict)
    defender_buffs: dict[str, int] = field(default_factory=dict)

    # Additional context
    is_overpower: bool = False
    is_critical: bool = False
    is_opportunity_attack: bool = False
    weapon_name: str = ""
    weapon_damage_range: tuple[int, int] = (1, 6)


@dataclass
class DetailedMoveData:
    """Detailed breakdown of a movement for logging."""

    unit_name: str
    round_number: int
    from_pos: Position
    to_pos: Position
    ap_spent: int
    distance: int
    reactions_triggered: list[str] = field(default_factory=list)  # Names of units that reacted


@dataclass
class DetailedActionData:
    """Generic detailed action data for special moves, weapon switches, etc."""

    unit_name: str
    round_number: int
    action_type: str  # "weapon_switch", "charge", "rotate", etc.
    ap_spent: int
    description: str  # Human-readable description
    extra_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class InitiativeData:
    """Initiative roll data for battle start."""

    unit_name: str
    total_initiative: int
    base_ke: int
    roll: int
    order_position: int  # 1st, 2nd, 3rd, etc.


@dataclass
class BattleLogEntry:
    """A single entry in the battle log."""

    entry_type: str  # "attack", "move", "action", "round_start", "turn_start", "initiative"
    round_number: int
    timestamp: float  # For ordering
    message: str  # Short message shown in simple log

    # Detailed data (one of these will be populated based on entry_type)
    attack_data: DetailedAttackData | None = None
    move_data: DetailedMoveData | None = None
    action_data: DetailedActionData | None = None
    initiative_data: InitiativeData | None = None

    # Unit reference for turn starts
    unit_name: str | None = None
