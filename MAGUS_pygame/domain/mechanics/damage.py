"""
Domain damage calculation mechanics.
Ported and refactored from old_system/systems/damage_calculator.py
Pure domain logic: no pygame, no global state, no printing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from domain.value_objects import DamageResult

if TYPE_CHECKING:
    from domain.entities import Unit, Weapon


# --- Data Structures ---


@dataclass(frozen=True)
class DamageContext:
    """Optional situational modifiers for damage resolution."""

    charge_multiplier: int = 1  # Multiplier applied after bonuses
    armor_absorption: int = 0  # Flat absorption (e.g., from armor piece)


# --- Helpers ---


def _get_attribute_value(unit: Unit, attr_hu: str) -> int:
    """Fetch attribute value from unit.attributes using Hungarian key mapping.
    Supported keys: Erő, Ügyesség, Gyorsaság, Állóképesség, Egészség, Karizma,
    Intelligencia, Akaraterő, Asztrál, Érzékelés.
    Unknown returns 0.
    """
    return unit.attributes.get_attribute(attr_hu, 0)


def _calculate_attribute_bonus(unit: Unit, weapon: Weapon | None) -> int:
    """Legacy-compatible rule:
    For each attribute listed in weapon.damage_bonus_attributes (if present):
      if value > 15 => bonus += (value - 15)
    Else 0.
    Missing weapon => 0.
    """
    if weapon is None:
        return 0

    # Use dedicated bonus attribute list when available
    bonus_attrs = getattr(weapon, "damage_bonus_attributes", []) or []
    total = 0
    for attr_name in bonus_attrs:
        val = _get_attribute_value(unit, attr_name)
        if val > 15:
            total += val - 15
    return total


def calculate_final_damage(
    attacker: Unit,
    weapon: Weapon | None,
    base_damage: int,
    ctx: DamageContext | None = None,
) -> DamageResult:
    """Compute final damage from base + attribute bonus + situational context.

    Args:
        attacker: Attacking unit
        weapon: Weapon used (can be None)
        base_damage: Raw rolled damage (already within weapon dice range)
        ctx: Optional damage context (multipliers, absorption)

    Returns:
        DamageResult with breakdown.
    """
    if base_damage < 0:
        base_damage = 0
    ctx = ctx or DamageContext()

    attr_bonus = _calculate_attribute_bonus(attacker, weapon)
    modified = base_damage + attr_bonus

    # Apply multiplier (e.g., charge)
    charge_mult = max(1, ctx.charge_multiplier)
    multiplied = modified * charge_mult

    # Armor absorption (flat)
    absorbed = min(multiplied, max(0, ctx.armor_absorption))
    final = multiplied - absorbed

    # Penetrated means damage exceeded armor capacity (armor couldn't stop it all)
    penetrated = multiplied > ctx.armor_absorption if ctx.armor_absorption > 0 else False

    return DamageResult(
        base_damage=base_damage,
        final_damage=final,
        armor_absorbed=absorbed,
        penetrated=penetrated,
        is_critical=False,
        overkill=0,
    )


class DamageService:
    """Service around damage calculation for application layer.

    Responsibilities:
    - Provide high-level API for attack resolution
    - Future: integrate critical rolls, weapon dice parsing, status effects
    """

    def resolve_attack(
        self,
        attacker: Unit,
        defender: Unit,
        weapon: Weapon | None,
        rolled_damage: int,
        ctx: DamageContext | None = None,
    ) -> DamageResult:
        result = calculate_final_damage(attacker, weapon, rolled_damage, ctx)
        # Apply damage to defender as a side-effect
        defender.take_damage(result.final_damage)
        return result
