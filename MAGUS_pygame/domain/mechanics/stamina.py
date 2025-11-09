"""
Stamina subsystem for MAGUS combat engine.

Models stamina as physical/mental endurance tied to Állóképesség.
- Base stamina = Állóképesség * 10 (plus optional skill modifiers)
- Manages stamina costs, recovery, thresholds, and derived combat effects

Design goals:
- Pure domain logic (no I/O, no pygame)
- Deterministic, testable functions with clear contracts
- Hooks for future extensions (regen, conditions, UI)
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple, Dict, Iterable


class StaminaState(str, Enum):
    """Threshold tiers for stamina percentage.

    Ranges (inclusive of lower bound, exclusive of upper bound except 100% edge):
    - FRISS:       80% <= ratio <= 100%
    - FELPEZSDULT: 60% <= ratio < 80%
    - KIFULLADT:   40% <= ratio < 60%
    - KIFARADT:    20% <= ratio < 40%
    - KIMERULT:     0% <= ratio < 20%
    """

    FRISS = "Friss"
    FELPEZSDULT = "Felpezsdült"
    KIFULLADT = "Kifulladt"
    KIFARADT = "Kifáradt"
    KIMERULT = "Kimerült"


# Percentage thresholds as boundaries (ratio in 0..1)
# Ordered from highest to lowest
THRESHOLDS: Tuple[Tuple[float, StaminaState], ...] = (
    (0.80, StaminaState.FRISS),
    (0.60, StaminaState.FELPEZSDULT),
    (0.40, StaminaState.KIFULLADT),
    (0.20, StaminaState.KIFARADT),
    (0.00, StaminaState.KIMERULT),
)


@dataclass(frozen=True)
class CombatModifiers:
    """Derived effective combat stat modifiers from stamina tier.

    Negative values reduce stats (e.g., TE/VE).
    """

    te_mod: int = 0
    ve_mod: int = 0


# Default mapping for derived combat penalties per stamina state (placeholder values)
DEFAULT_COMBAT_MODIFIERS: Dict[StaminaState, CombatModifiers] = {
    StaminaState.FRISS: CombatModifiers(0, 0),
    StaminaState.FELPEZSDULT: CombatModifiers(-1, -1),
    StaminaState.KIFULLADT: CombatModifiers(-2, -2),
    StaminaState.KIFARADT: CombatModifiers(-4, -4),
    StaminaState.KIMERULT: CombatModifiers(-6, -6),
}


@dataclass
class Stamina:
    """Stamina resource tied to Állóképesség.

    Attributes:
        max_stamina: Maximum stamina (typically Állóképesség * 10 + skill bonuses)
        current_stamina: Current stamina points (0..max_stamina)
        attribute_ref: The Állóképesség value used to derive base (for reference)
        skill_bonus_max: Flat bonus added to max (e.g., Teherbírás)
        combat_modifiers_map: Mapping from StaminaState to CombatModifiers

    Notes:
        - Use apply_cost() for spending stamina with modifiers
        - Use recover() to regain stamina (capped to max)
        - Use get_state() to query percentage and tier
        - Penalties for low tiers are returned by get_combat_modifiers()
    """

    max_stamina: int
    current_stamina: int
    attribute_ref: int
    skill_bonus_max: int = 0
    combat_modifiers_map: Dict[StaminaState, CombatModifiers] = None

    def __post_init__(self) -> None:
        if self.combat_modifiers_map is None:
            self.combat_modifiers_map = DEFAULT_COMBAT_MODIFIERS
        # Clamp current within bounds
        self.current_stamina = max(0, min(self.current_stamina, self.max_stamina))

    # ---------- Constructors ----------
    @classmethod
    def from_attribute(
        cls,
        allokepesseg: int,
        skill_bonus_max: int = 0,
        start_full: bool = True,
        combat_modifiers_map: Optional[Dict[StaminaState, CombatModifiers]] = None,
    ) -> "Stamina":
        """Create Stamina from Állóképesség value.

        Base: max = Állóképesség * 10 + skill_bonus_max
        """
        max_sta = max(0, int(allokepesseg) * 10 + int(skill_bonus_max))
        curr = max_sta if start_full else max(0, max_sta // 2)
        return cls(
            max_stamina=max_sta,
            current_stamina=curr,
            attribute_ref=int(allokepesseg),
            skill_bonus_max=int(skill_bonus_max),
            combat_modifiers_map=combat_modifiers_map or DEFAULT_COMBAT_MODIFIERS,
        )

    # ---------- Core ops ----------
    def apply_cost(self, base_cost: int, modifiers: Optional[Dict] = None) -> int:
        """Spend stamina according to base cost and optional modifiers.

        Contract:
        - base_cost: non-negative integer (interpreted as "action points" for now)
        - modifiers (optional) keys (all optional, placeholders allowed):
            - "skill_level": int  -> absorbs 1 stamina per level (min 0)
            - "absorption": int   -> flat absorption before reductions (>=0)
            - "flat_reduction": int -> flat reduction after absorption (>=0)
            - "multiplier": float -> multiplicative penalty (e.g., heavy armor)
            - "multipliers": Iterable[float] -> composed multiplicative penalties
            - "min_cost": int    -> floor for minimum stamina spent
        - Result is clamped >= 0, current_stamina won't go below 0

        Returns:
            actual_spent: int (how much stamina was deducted)
        """
        cost = max(0, int(base_cost))
        if cost == 0:
            return 0

        m = modifiers or {}

        # Absorption by skills/technique (mirrors armor absorption idea)
        absorption = 0
        if "skill_level" in m and m["skill_level"] is not None:
            # Placeholder: 1 stamina absorbed per skill level
            absorption += max(0, int(m["skill_level"]))
        if "absorption" in m and m["absorption"] is not None:
            absorption += max(0, int(m["absorption"]))
        cost = max(0, cost - absorption)

        # Flat reduction from specific perks/stances
        if "flat_reduction" in m and m["flat_reduction"] is not None:
            cost = max(0, cost - max(0, int(m["flat_reduction"])) )

        # Multiplicative penalties (heavy armor, conditions, etc.)
        mult = float(m.get("multiplier", 1.0))
        if "multipliers" in m and m["multipliers"] is not None:
            for val in m["multipliers"]:  # type: ignore[assignment]
                try:
                    mult *= float(val)
                except (TypeError, ValueError):
                    continue
        # Round to nearest int; keep at least 0
        cost = int(round(cost * max(0.0, mult)))

        # Enforce minimum cost if specified (e.g., dodge always costs some stamina)
        if "min_cost" in m and m["min_cost"] is not None:
            cost = max(cost, max(0, int(m["min_cost"])) )

        # Apply to pool, clamped at 0
        actual_spent = min(cost, self.current_stamina)
        self.current_stamina -= actual_spent
        return actual_spent

    def recover(self, amount: int) -> int:
        """Recover stamina, capped at max.

        Returns:
            actual_recovered: int
        """
        gain = max(0, int(amount))
        if gain == 0:
            return 0
        before = self.current_stamina
        self.current_stamina = min(self.max_stamina, self.current_stamina + gain)
        return self.current_stamina - before

    # ---------- Queries ----------
    def ratio(self) -> float:
        """Return current stamina ratio in range [0.0, 1.0]."""
        if self.max_stamina <= 0:
            return 0.0
        return max(0.0, min(1.0, self.current_stamina / float(self.max_stamina)))

    def get_state(self) -> Tuple[float, StaminaState]:
        """Return (ratio, stamina_state)."""
        r = self.ratio()
        # Special-case exact full to be FRISS
        if r >= 0.999999:
            return r, StaminaState.FRISS
        for bound, state in THRESHOLDS:
            if r >= bound:
                return r, state
        # Fallback (shouldn't happen)
        return r, StaminaState.KIMERULT

    def get_combat_modifiers(self) -> CombatModifiers:
        """Return derived combat modifiers based on current stamina state.

        Default mapping can be overridden via constructor.
        """
        _, state = self.get_state()
        return self.combat_modifiers_map.get(state, CombatModifiers())

    def is_exhausted(self) -> bool:
        """True when in Kimerült tier (< 20%)."""
        _, state = self.get_state()
        return state == StaminaState.KIMERULT

    def is_unconscious(self) -> bool:
        """True when stamina is 0 (collapse)."""
        return self.current_stamina <= 0

    # ---------- Hooks for future extensions ----------
    def requires_exhaustion_save(self) -> bool:
        """At Kimerült tier, an Állóképesség save is required each turn.

        The actual saving throw resolution is handled elsewhere.
        """
        return self.is_exhausted() and not self.is_unconscious()

    # Convenience to spend action cost (AP) as stamina for now
    def spend_action_points(self, ap_cost: int, **modifiers) -> int:
        """Alias to apply_cost using AP as stamina cost (temporary rule).

        Example:
            stamina.spend_action_points(5, multiplier=1.5)  # heavy armor penalty
        """
        return self.apply_cost(ap_cost, modifiers or None)

    # ---------- Regeneration helper ----------
    def regenerate_tick(self, *, resting: bool = False, intense: bool = False) -> int:
        """Regenerate stamina over time.

        Policy (placeholder, adjustable):
        - intense=True (in combat/strenuous): 0 recovery
        - resting=True (out of combat, resting): max(1, floor(0.05 * max))
        - default (light activity): max(1, floor(0.02 * max))

        Returns recovered amount actually applied.
        """
        if intense:
            return 0
        if resting:
            amount = max(1, int(self.max_stamina * 0.05))
        else:
            amount = max(1, int(self.max_stamina * 0.02))
        return self.recover(amount)


# ---------- Fatigue condition placeholder hook ----------
from dataclasses import dataclass


@dataclass(frozen=True)
class FatigueCondition:
    """Placeholder fatigue condition to be integrated with conditions system later.

    severity: maps to StaminaState for now; consumers can translate to effects.
    """

    severity: StaminaState
    note: str = ""


def create_fatigue_condition(state: StaminaState, note: str = "") -> FatigueCondition:
    """Create a fatigue condition placeholder based on current stamina state."""
    return FatigueCondition(severity=state, note=note)
