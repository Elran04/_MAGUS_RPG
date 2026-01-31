"""
Attack resolution system for MAGUS combat.

Handles complete attack flow:
1. TÉ vs VÉ comparison (with d100 roll)
2. Hit/miss/block/parry/dodge determination
3. Critical hit detection
4. Overpower strike detection
5. Damage calculation with all modifiers
6. Armor degradation
7. Mandatory EP loss from reach rules
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.entities import Unit, Weapon

from domain.mechanics.armor import HitzoneResolver
from domain.mechanics.attack_angle import (
    AttackAngle,
    get_attack_angle,
    is_attack_from_back,
    is_attack_from_back_left,
    is_attack_from_back_right,
    is_attack_from_front,
    is_attack_from_front_left,
    is_attack_from_front_right,
)
from domain.mechanics.conditions.stamina import Stamina
from domain.mechanics.critical import (
    CriticalContext,
    get_critical_damage_multiplier,
    is_critical_failure,
    is_critical_hit,
)
from domain.mechanics.damage import DamageContext, calculate_final_damage
from domain.mechanics.reach import calculate_mandatory_ep_loss
from domain.mechanics.skills import get_overpower_threshold_for_skill

# --- Helper Functions ---

def _get_stamina_modifier(unit: Unit, modifier_type: str = "te_mod") -> int:
    """Get stamina modifier (TE or VE) for a unit."""
    if not hasattr(unit, "stamina") or not unit.stamina:
        return 0
    modifiers = unit.stamina.get_combat_modifiers()
    return getattr(modifiers, modifier_type, 0)


def _get_injury_modifier(unit: Unit, modifier_type: str = "te_mod") -> int:
    """Get injury condition modifier (TE or VE) for a unit."""
    if not hasattr(unit, "fp") or not hasattr(unit, "ep"):
        return 0
    from .conditions.injury import calculate_injury_condition, get_injury_modifiers
    injury_cond = calculate_injury_condition(
        unit.fp.current, unit.fp.maximum, unit.ep.current, unit.ep.maximum
    )
    modifiers = get_injury_modifiers(injury_cond)
    return getattr(modifiers, modifier_type, 0)


def _is_unit_conscious(unit: Unit) -> bool:
    """Check if unit is conscious (not unconscious from stamina)."""
    if not hasattr(unit, "stamina") or not unit.stamina:
        return True
    return not unit.stamina.is_unconscious()


def _create_stamina_snapshot(unit: Unit) -> Stamina:
    """Create a temporary stamina pool snapshot for cost calculation."""
    if hasattr(unit, "stamina") and unit.stamina:
        return Stamina(
            max_stamina=unit.stamina.max_stamina,
            current_stamina=unit.stamina.current_stamina,
            attribute_ref=unit.stamina.attribute_ref,
        )
    else:
        endurance = getattr(unit.attributes, "endurance", 10) if hasattr(unit, "attributes") else 10
        return Stamina.from_attribute(endurance, start_full=False)


class AttackOutcome(Enum):
    """Result of attack resolution before damage."""

    CRITICAL_FAILURE = (
        "critical_failure"  # Critical fumble (1-10 at level 0, 1-5 at level 1, 1 at level 2)
    )
    MISS = "miss"  # all_TÉ <= base_VÉ
    BLOCKED = "blocked"  # base_VÉ < all_TÉ <= block_VÉ (shield)
    PARRIED = "parried"  # block_VÉ < all_TÉ <= parry_VÉ (weapon)
    DODGE_ATTEMPT = "dodge_attempt"  # parry_VÉ < all_TÉ <= dodge_VÉ (needs speed check)
    HIT = "hit"  # all_TÉ > all_VÉ (normal hit)
    OVERPOWER = "overpower"  # all_TÉ > all_VÉ + 50 (overwhelming strike)
    CRITICAL = "critical"  # Critical hit (automatic, to FP)
    CRITICAL_OVERPOWER = "critical_overpower"  # Both critical AND overpower (devastating)


@dataclass(frozen=True)
class DefenseValues:
    """
    Calculated defense values for a unit.

    base_VÉ: Character's base VÉ ± conditions
    block_VÉ: base_VÉ + shield VÉ (if equipped)
    parry_VÉ: base_VÉ + weapon VÉ (+ shield if dual wielding)
    dodge_VÉ: parry_VÉ + dodge modifier (from skill)
    all_VÉ: Final effective VÉ (currently dodge_VÉ, or parry_VÉ if no dodge skill)
    """

    base_ve: int
    block_ve: int
    parry_ve: int
    dodge_ve: int
    all_ve: int  # Effective VÉ used for comparison


@dataclass
class AttackResult:
    """
    Complete result of an attack resolution.

    Attributes:
        outcome: Type of attack outcome
        all_te: Final attack value (base TÉ + roll + modifiers)
        all_ve: Final defense value used
        attack_roll: Raw d100 roll
        rolled_damage: Raw weapon damage roll before modifiers/armor
        is_critical: Whether attack was a critical hit
        is_overpower: Whether attack was an overpower strike
        hit: Whether attack successfully hit (deals damage)
        damage_to_fp: Fatigue damage dealt
        damage_to_ep: Direct EP damage dealt
        armor_absorbed: Damage absorbed by armor
        armor_degraded: Whether armor was degraded
        mandatory_ep_loss: EP loss from reach rules
        requires_dodge_check: Whether defender needs speed check
        hit_zone: Resolved hit zone string (if any)
        zone_sfe: SFÉ value (armor absorption) for that hit zone
    """

    outcome: AttackOutcome
    all_te: int
    all_ve: int
    attack_roll: int
    rolled_damage: int = 0

    is_critical: bool = False
    is_overpower: bool = False
    hit: bool = False

    damage_to_fp: int = 0
    damage_to_ep: int = 0
    armor_absorbed: int = 0
    armor_degraded: bool = False
    mandatory_ep_loss: int = 0

    requires_dodge_check: bool = False
    dodge_success: bool | None = None
    # Stamina integration (independent from FP damage)
    stamina_spent_attacker: int = 0  # Stamina cost for attacker (e.g., attack AP cost)
    stamina_spent_defender: int = 0  # Stamina cost for defender (block, parry, dodge)
    # New armor integration
    hit_zone: str | None = None
    zone_sfe: int = 0


def calculate_defense_values(
    defender: Unit,
    shield_ve: int = 0,
    dodge_modifier: int = 0,
    condition_modifier: int = 0,
    attack_angle: AttackAngle | None = None,
) -> DefenseValues:
    """
    Calculate all defense threshold values for a unit.

    Args:
        defender: Defending unit
        shield_ve: VÉ bonus from equipped shield (if any)
        dodge_modifier: Dodge skill modifier
        condition_modifier: Conditions/status effects modifier
        attack_angle: Angle of incoming attack for directional VÉ restrictions

    Returns:
        DefenseValues with all thresholds
    """
    # Unconscious defenders have zero defense values
    if not _is_unit_conscious(defender):
        return DefenseValues(base_ve=0, block_ve=0, parry_ve=0, dodge_ve=0, all_ve=0)

    # Base VÉ from character + conditions + stamina penalties + injury penalties
    stamina_mod = _get_stamina_modifier(defender, "ve_mod")
    injury_mod = _get_injury_modifier(defender, "ve_mod")
    base_ve = defender.combat_stats.VE + condition_modifier + stamina_mod + injury_mod

    # === Apply directional VÉ restrictions with shield skill ===
    # Shield VÉ now depends on shield skill level and attack angle
    effective_shield_ve = 0
    if shield_ve > 0 and attack_angle is not None:
        # Check if defender has shield skill and if shield protects from this angle
        from domain.mechanics.skills import shield_protects_from_angle

        shield_skill_level = defender.skills.get_rank("shieldskill", 0) if defender.skills else 0
        if shield_protects_from_angle(shield_skill_level, attack_angle):
            effective_shield_ve = shield_ve
        # Otherwise shield_ve is 0 for non-protected angles
    elif shield_ve > 0:
        # If no attack_angle provided, assume shield applies (backward compatibility)
        effective_shield_ve = shield_ve

    # Block VÉ: base + shield (if equipped and angle protected)
    block_ve = base_ve + effective_shield_ve

    # Parry VÉ: base + weapon VÉ (only applies to FRONT, FRONT_RIGHT, FRONT_LEFT)
    # Weapon VÉ only applies to attacks from FRONT (0), FRONT_RIGHT (1), FRONT_LEFT (5)
    weapon_ve = 0
    if defender.weapon and attack_angle is not None:
        if attack_angle in (AttackAngle.FRONT, AttackAngle.FRONT_RIGHT, AttackAngle.FRONT_LEFT):
            weapon_ve = defender.weapon.ve_modifier
        # Otherwise weapon_ve is 0 for side/back attacks
    elif defender.weapon:
        # If no attack_angle provided, assume weapon applies (backward compatibility)
        weapon_ve = defender.weapon.ve_modifier

    parry_ve = base_ve + weapon_ve + effective_shield_ve

    # Dodge VÉ: parry + dodge skill modifier
    dodge_ve = parry_ve + dodge_modifier

    # all_VÉ is dodge_VÉ if dodge skill exists, else parry_VÉ
    all_ve = dodge_ve if dodge_modifier > 0 else parry_ve

    return DefenseValues(
        base_ve=base_ve, block_ve=block_ve, parry_ve=parry_ve, dodge_ve=dodge_ve, all_ve=all_ve
    )


def calculate_attack_value(
    attacker: Unit,
    attack_roll: int,
    weapon: Weapon | None = None,
    condition_modifier: int = 0,
    skill_mod: int = 0,
) -> int:
    """
    Calculate final attack value (all_TÉ).

    all_TÉ = base TÉ + weapon TÉ + d100 roll + conditions + stamina + injury + skill

    Args:
        attacker: Attacking unit
        attack_roll: d100 roll (1-100)
        weapon: Weapon used (defaults to attacker's weapon)
        condition_modifier: Conditions/status effects modifier
        skill_mod: Weapon skill TÉ modifier

    Returns:
        Final attack value
    """
    if weapon is None:
        weapon = attacker.weapon

    # Unconscious attackers cannot attack; force attack value to 0
    if not _is_unit_conscious(attacker):
        return 0

    base_te = attacker.combat_stats.TE
    stamina_mod = _get_stamina_modifier(attacker, "te_mod")
    injury_mod = _get_injury_modifier(attacker, "te_mod")
    weapon_te = weapon.te_modifier if weapon else 0

    all_te = (
        base_te
        + weapon_te
        + stamina_mod
        + injury_mod
        + attack_roll
        + condition_modifier
        + skill_mod
    )

    return all_te


def resolve_attack(
    attacker: Unit,
    defender: Unit,
    attack_roll: int,
    base_damage_roll: int,
    weapon: Weapon | None = None,
    weapon_skill_level: int = 2,
    shield_ve: int = 0,
    dodge_modifier: int = 0,
    attacker_conditions: int = 0,
    defender_conditions: int = 0,
    overpower_threshold: int = 50,
    # Stamina modifiers (optional): dicts passed to Stamina.apply_cost
    stamina_block: dict | None = None,
    stamina_parry: dict | None = None,
    stamina_dodge: dict | None = None,
) -> AttackResult:
    """
    Resolve complete attack with all MAGUS rules.

    Args:
        attacker: Attacking unit
        defender: Defending unit
        attack_roll: d100 attack roll
        base_damage_roll: Base weapon damage roll
        weapon: Weapon used (defaults to attacker's weapon)
        weapon_skill_level: Attacker's skill with weapon
        shield_ve: Defender's shield VÉ bonus
        dodge_modifier: Defender's dodge skill modifier
        attacker_conditions: TÉ modifier from conditions
        defender_conditions: VÉ modifier from conditions
        overpower_threshold: Threshold for overpower (default 50, modified by skills)

    Returns:
        Complete attack result with damage and effects
    """
    if weapon is None:
        weapon = attacker.weapon

    # Armor is sourced from defender.armor_system (if present)

    # === Apply weapon skill modifiers ===
    skill_stamina_cost_modifier = 0
    skill_critical_override = None
    skill_critical_failure_max = None
    _skill_attack_ap_multiplier = 1

    # For now, all weapon skills use longswords modifiers; later: registry lookup
    from domain.mechanics.skills import apply_weaponskill_modifiers

    skill_id = (
        weapon.skill_id
        if weapon is not None and hasattr(weapon, "skill_id") and weapon.skill_id
        else "weaponskill_longswords"
    )

    (
        skill_stamina_cost_modifier,
        skill_critical_override,
        skill_critical_failure_max,
        _skill_attack_ap_multiplier,
    ) = apply_weaponskill_modifiers(attacker, attack_roll, weapon_skill_level, skill_id)

    # Apply skill overpower threshold shift
    overpower_threshold = get_overpower_threshold_for_skill(
        weapon_skill_level, overpower_threshold, skill_id
    )

    # === Calculate attack angle for directional modifiers (needed early for defense) ===
    attack_angle = get_attack_angle(attacker, defender)

    # === Check for critical failure (levels 0-2) ===
    is_fail = is_critical_failure(attack_roll, weapon_skill_level, skill_critical_failure_max)
    if is_fail:
        # Critical failure: attack is immediately CRITICAL_FAILURE outcome, no damage, no hit
        # Still show actual TÉ and VÉ values for player feedback
        all_te = calculate_attack_value(
            attacker, attack_roll, weapon, attacker_conditions, weapon_skill_level
        )
        defense = calculate_defense_values(
            defender, shield_ve, dodge_modifier, defender_conditions, attack_angle
        )

        return AttackResult(
            outcome=AttackOutcome.CRITICAL_FAILURE,
            all_te=all_te,
            all_ve=defense.all_ve,
            attack_roll=attack_roll,
            rolled_damage=0,
            is_critical=False,
            is_overpower=False,
            hit=False,
            damage_to_fp=0,
            damage_to_ep=0,
            armor_absorbed=0,
            armor_degraded=False,
            mandatory_ep_loss=0,
            stamina_spent_attacker=0,
            stamina_spent_defender=0,
        )

    # === Build critical context ===
    # Create context once and use consistently for all critical checks
    critical_ctx = CriticalContext(
        attack_roll=attack_roll,
        weapon_skill_level=weapon_skill_level,
        critical_threshold=skill_critical_override,
    )

    # Check for critical hit first (affects everything)
    is_crit = is_critical_hit(
        critical_ctx.attack_roll,
        critical_ctx.weapon_skill_level,
        critical_ctx.critical_threshold,
    )

    # Unconscious attackers cannot land critical hits
    if not _is_unit_conscious(attacker):
        is_crit = False

    # Calculate attack and defense values
    all_te = calculate_attack_value(
        attacker, attack_roll, weapon, attacker_conditions, 0
    )

    # === Apply directional attack bonuses (only if conscious) ===
    # Back attack: +10 TÉ
    # Side/diagonal attacks (back-left, back-right, front-left, front-right): +5 TÉ
    directional_te_bonus = 0
    if _is_unit_conscious(attacker):  # Only apply bonuses if attacker is conscious
        if is_attack_from_back(attacker, defender):
            directional_te_bonus = 10
        elif is_attack_from_back_left(attacker, defender) or is_attack_from_back_right(
            attacker, defender
        ) or is_attack_from_front_left(attacker, defender) or is_attack_from_front_right(
            attacker, defender
        ):
            directional_te_bonus = 5

    all_te += directional_te_bonus
    defense = calculate_defense_values(
        defender, shield_ve, dodge_modifier, defender_conditions, attack_angle
    )

    # Determine outcome
    outcome = AttackOutcome.MISS
    hit = False
    requires_dodge = False
    is_overpower_strike = False
    stamina_spent_defender = 0

    # Check for overpower first (independent of hit/miss)
    if all_te > defense.all_ve + overpower_threshold:
        is_overpower_strike = True

    if is_crit:
        # Critical hit: automatic hit, ignores VÉ
        if is_overpower_strike:
            # BOTH critical AND overpower: devastating combo
            outcome = AttackOutcome.CRITICAL_OVERPOWER
        else:
            # Just critical: amplified damage to FP, ignores armor
            outcome = AttackOutcome.CRITICAL
        hit = True
    elif all_te <= defense.base_ve:
        # Complete miss
        outcome = AttackOutcome.MISS
        hit = False
    elif all_te <= defense.block_ve:
        # Blocked by shield
        outcome = AttackOutcome.BLOCKED
        hit = True  # Hit but reduced to FP damage
    elif all_te <= defense.parry_ve:
        # Parried by weapon
        outcome = AttackOutcome.PARRIED
        hit = True  # Hit but reduced to FP damage
    elif dodge_modifier > 0 and all_te <= defense.dodge_ve:
        # Dodge attempt required (only if defender has dodge skill)
        outcome = AttackOutcome.DODGE_ATTEMPT
        requires_dodge = True
        hit = True  # Pending dodge check
        # Dodge always costs stamina even if it would fail; apply immediately as an action cost
        # Placeholder base cost aligned with "action points" concept
        DODGE_STAMINA_BASE_COST = 6
        # Compute stamina cost using defender's stamina pool snapshot
        temp_sta = _create_stamina_snapshot(defender)
        stamina_spent_defender = temp_sta.apply_cost(
            DODGE_STAMINA_BASE_COST, stamina_dodge or {"min_cost": 1}
        )
    else:
        # Normal hit
        hit = True
        # Set outcome based on overpower flag (already calculated above)
        if is_overpower_strike:
            outcome = AttackOutcome.OVERPOWER
        else:
            outcome = AttackOutcome.HIT

    # Calculate damage if hit
    damage_to_fp = 0
    damage_to_ep = 0
    armor_absorbed = 0
    armor_degraded = False
    mandatory_ep = 0

    if hit and not requires_dodge:  # Don't calculate damage until dodge resolved
        # Determine armor absorption
        # Resolve hit zone only for real hits (not block/parry)
        resolved_zone: str | None = None
        if outcome in (
            AttackOutcome.HIT,
            AttackOutcome.CRITICAL,
            AttackOutcome.OVERPOWER,
            AttackOutcome.CRITICAL_OVERPOWER,
        ):
            resolved_zone = HitzoneResolver.resolve()

        armor_sfe = 0
        # Prefer defender's ArmorSystem if available
        if hasattr(defender, "armor_system") and defender.armor_system is not None:
            # Overpower degrades the outermost layer at that zone before applying armor
            if is_overpower_strike and resolved_zone is not None:
                defender.armor_system.reduce_sfe(resolved_zone, 1)
                armor_degraded = True
            # Critical ignores armor; otherwise use zone-specific SFE
            if not is_crit and resolved_zone is not None:
                armor_sfe = defender.armor_system.get_sfe_for_hit(resolved_zone)
        # No legacy fallback; if no armor system, armor_sfe remains 0

        # Apply critical damage multiplier
        damage_multiplier = 1
        if is_crit:
            damage_multiplier = get_critical_damage_multiplier(weapon_skill_level)

        # Calculate damage
        damage_ctx = DamageContext(charge_multiplier=damage_multiplier, armor_absorption=armor_sfe)
        damage_result = calculate_final_damage(attacker, weapon, base_damage_roll, damage_ctx)

        # Determine where damage goes based on outcome
        if outcome in (AttackOutcome.BLOCKED, AttackOutcome.PARRIED):
            # Block/parry: stamina cost based on RAW incoming damage (no armor absorption)
            # Calculate damage WITHOUT armor to get true weapon impact
            damage_ctx_no_armor = DamageContext(
                charge_multiplier=damage_multiplier,
                armor_absorption=0,  # No armor absorption during active defense
            )
            damage_no_armor = calculate_final_damage(
                attacker, weapon, base_damage_roll, damage_ctx_no_armor
            )
            base_fp_cost = damage_no_armor.final_damage

            # Compute stamina cost using defender's stamina pool snapshot
            temp_sta = _create_stamina_snapshot(defender)

            if outcome == AttackOutcome.BLOCKED:
                # Apply shield skill stamina modifiers
                from domain.mechanics.skills import calculate_block_stamina_cost

                shield_skill_level = (
                    defender.skills.get_rank("shieldskill", 0) if defender.skills else 0
                )
                # Shield skill modifies stamina cost
                modified_cost = calculate_block_stamina_cost(
                    base_fp_cost, shield_skill_level, is_unskilled=False
                )
                spent = temp_sta.apply_cost(modified_cost, stamina_block or {})
            else:
                # Parry uses standard stamina cost
                spent = temp_sta.apply_cost(base_fp_cost, stamina_parry or {})

            stamina_spent_defender = spent  # Stamina cost, not FP damage
            armor_absorbed = 0  # No armor absorption during block/parry

        elif outcome == AttackOutcome.CRITICAL_OVERPOWER:
            # BOTH critical AND overpower: devastating combination
            # - Critical: damage multiplied, armor ignored
            # - Overpower: damage goes to EP (bypasses FP), armor degraded
            damage_to_ep = damage_result.final_damage
            armor_absorbed = damage_result.armor_absorbed

        elif outcome == AttackOutcome.OVERPOWER:
            # Pure overpower: damage to EP, armor degraded
            damage_to_ep = damage_result.final_damage
            armor_absorbed = damage_result.armor_absorbed

        elif outcome == AttackOutcome.CRITICAL:
            # Pure critical: amplified damage to FP, armor ignored
            # Critical does NOT bypass FP - only overpower does that!
            damage_to_fp = damage_result.final_damage
            armor_absorbed = damage_result.armor_absorbed
            # Mandatory EP loss still applies for critical hits to FP
            mandatory_ep = calculate_mandatory_ep_loss(weapon, damage_to_fp)

        else:
            # Normal hit: damage to FP, with mandatory EP loss
            damage_to_fp = damage_result.final_damage
            armor_absorbed = damage_result.armor_absorbed

            # Calculate mandatory EP loss from reach rules
            mandatory_ep = calculate_mandatory_ep_loss(weapon, damage_to_fp)

    # Calculate attacker stamina cost (mirrors AP cost) using skill modifier
    base_attack_time = weapon.attack_time if weapon else 5
    if skill_stamina_cost_modifier >= 1:
        modified_cost = base_attack_time * skill_stamina_cost_modifier
    else:
        modified_cost = base_attack_time + skill_stamina_cost_modifier
    stamina_spent_attacker = max(1, int(math.ceil(modified_cost)))

    return AttackResult(
        outcome=outcome,
        all_te=all_te,
        all_ve=defense.all_ve,
        attack_roll=attack_roll,
        rolled_damage=base_damage_roll,
        is_critical=is_crit,
        is_overpower=is_overpower_strike,
        hit=hit,
        damage_to_fp=damage_to_fp,
        damage_to_ep=damage_to_ep,
        armor_absorbed=armor_absorbed,
        armor_degraded=armor_degraded,
        mandatory_ep_loss=mandatory_ep,
        requires_dodge_check=requires_dodge,
        stamina_spent_attacker=stamina_spent_attacker,
        stamina_spent_defender=stamina_spent_defender,
        hit_zone=(
            resolved_zone
            if (
                outcome
                in (
                    AttackOutcome.HIT,
                    AttackOutcome.CRITICAL,
                    AttackOutcome.OVERPOWER,
                    AttackOutcome.CRITICAL_OVERPOWER,
                )
            )
            else None
        ),
        zone_sfe=(
            armor_sfe
            if (
                outcome
                in (
                    AttackOutcome.HIT,
                    AttackOutcome.CRITICAL,
                    AttackOutcome.OVERPOWER,
                    AttackOutcome.CRITICAL_OVERPOWER,
                )
            )
            else 0
        ),
    )


def apply_attack_result(result: AttackResult, defender: Unit) -> None:
    """
    Apply attack result damage to defender.
    Mutates defender's EP and FP only (not stamina).

    Stamina costs are handled separately by the application layer.

    FP exhaustion rule: When FP is 0, any FP damage goes to EP instead.

    Args:
        result: Attack result with damage values
        defender: Unit to apply damage to
    """
    if not result.hit:
        return

    # Apply FP damage only
    # spend_fatigue returns overflow that went to EP
    fp_overflow = 0
    if result.damage_to_fp > 0:
        fp_overflow += defender.spend_fatigue(result.damage_to_fp)

    # Apply EP damage (direct + mandatory)
    # Note: FP overflow is already applied by spend_fatigue
    total_ep_damage = result.damage_to_ep + result.mandatory_ep_loss
    if total_ep_damage > 0:
        defender.take_damage(total_ep_damage)
