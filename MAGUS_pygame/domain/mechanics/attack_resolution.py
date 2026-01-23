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

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.entities import Unit, Weapon
from domain.mechanics.armor import HitzoneResolver
from domain.mechanics.critical import (
    get_critical_damage_multiplier,
    is_critical_failure,
    is_critical_hit,
)
from domain.mechanics.damage import DamageContext, calculate_final_damage
from domain.mechanics.reach import calculate_mandatory_ep_loss
from domain.mechanics.skills import get_overpower_threshold_for_skill
from domain.mechanics.stamina import Stamina


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
    defender: Unit, shield_ve: int = 0, dodge_modifier: int = 0, condition_modifier: int = 0
) -> DefenseValues:
    """
    Calculate all defense threshold values for a unit.

    Args:
        defender: Defending unit
        shield_ve: VÉ bonus from equipped shield (if any)
        dodge_modifier: Dodge skill modifier
        condition_modifier: Conditions/status effects modifier

    Returns:
        DefenseValues with all thresholds
    """
    # Unconscious defenders have zero defense values
    if hasattr(defender, "stamina") and defender.stamina and defender.stamina.is_unconscious():
        return DefenseValues(base_ve=0, block_ve=0, parry_ve=0, dodge_ve=0, all_ve=0)
    # Base VÉ from character + conditions + stamina penalties + injury penalties
    stamina_mod = 0
    if hasattr(defender, "stamina") and defender.stamina:
        stamina_mod = defender.stamina.get_combat_modifiers().ve_mod

    injury_mod = 0
    if hasattr(defender, "fp") and hasattr(defender, "ep"):
        from .injury import calculate_injury_condition, get_injury_modifiers

        injury_cond = calculate_injury_condition(
            defender.fp.current, defender.fp.maximum, defender.ep.current, defender.ep.maximum
        )
        injury_mod = get_injury_modifiers(injury_cond).ve_mod

    base_ve = defender.combat_stats.VE + condition_modifier + stamina_mod + injury_mod

    # Block VÉ: base + shield (if equipped)
    block_ve = base_ve + shield_ve

    # Parry VÉ: base + weapon VÉ (+ shield if applicable)
    weapon_ve = 0
    if defender.weapon:
        weapon_ve = defender.weapon.ve_modifier
    parry_ve = base_ve + weapon_ve + shield_ve

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
    if hasattr(attacker, "stamina") and attacker.stamina and attacker.stamina.is_unconscious():
        return 0

    base_te = attacker.combat_stats.TE
    stamina_mod = 0
    if hasattr(attacker, "stamina") and attacker.stamina:
        stamina_mod = attacker.stamina.get_combat_modifiers().te_mod

    injury_mod = 0
    if hasattr(attacker, "fp") and hasattr(attacker, "ep"):
        from .injury import calculate_injury_condition, get_injury_modifiers

        injury_cond = calculate_injury_condition(
            attacker.fp.current, attacker.fp.maximum, attacker.ep.current, attacker.ep.maximum
        )
        injury_mod = get_injury_modifiers(injury_cond).te_mod

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
    weapon_skill_level: int = 0,
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
    skill_ke_mod = 0
    skill_te_mod = 0
    skill_ve_mod = 0
    skill_ce_mod = 0
    skill_stamina_reduction = 0
    skill_critical_override = None

    if weapon_skill_level > 0 and hasattr(weapon, "skill_id") and weapon.skill_id:
        # For now, all weapon skills use longswords modifiers; later: registry lookup
        from domain.mechanics.skills import apply_weaponskill_modifiers

        (
            skill_ke_mod,
            skill_te_mod,
            skill_ve_mod,
            skill_ce_mod,
            skill_stamina_reduction,
            skill_critical_override,
        ) = apply_weaponskill_modifiers(attacker, attack_roll, weapon_skill_level)

        # Apply skill overpower threshold shift
        overpower_threshold = get_overpower_threshold_for_skill(
            weapon_skill_level, overpower_threshold
        )

    # === Check for critical failure (levels 0-2) ===
    is_fail = is_critical_failure(attack_roll, weapon_skill_level)
    if is_fail:
        # Critical failure: attack is immediately CRITICAL_FAILURE outcome, no damage, no hit
        # Still show actual TÉ and VÉ values for player feedback
        all_te = calculate_attack_value(
            attacker, attack_roll, weapon, attacker_conditions, weapon_skill_level
        )
        defense = calculate_defense_values(defender, shield_ve, dodge_modifier, defender_conditions)

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

    # Check for critical hit first (affects everything)
    is_crit = is_critical_hit(attack_roll, weapon_skill_level, skill_critical_override)

    # Unconscious attackers cannot land critical hits
    if hasattr(attacker, "stamina") and attacker.stamina and attacker.stamina.is_unconscious():
        is_crit = False

    # Calculate attack and defense values
    all_te = calculate_attack_value(
        attacker, attack_roll, weapon, attacker_conditions, skill_te_mod
    )
    defense = calculate_defense_values(defender, shield_ve, dodge_modifier, defender_conditions)

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
        if hasattr(defender, "stamina") and defender.stamina:
            temp_sta = Stamina(
                max_stamina=defender.stamina.max_stamina,
                current_stamina=defender.stamina.current_stamina,
                attribute_ref=defender.stamina.attribute_ref,
            )
        else:
            # Fallback: derive temporary stamina from endurance
            temp_sta = Stamina.from_attribute(
                getattr(defender.attributes, "endurance", 10), start_full=False
            )
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
            if hasattr(defender, "stamina") and defender.stamina:
                temp_sta = Stamina(
                    max_stamina=defender.stamina.max_stamina,
                    current_stamina=defender.stamina.current_stamina,
                    attribute_ref=defender.stamina.attribute_ref,
                )
            else:
                temp_sta = Stamina.from_attribute(
                    getattr(defender.attributes, "endurance", 10), start_full=False
                )
            if outcome == AttackOutcome.BLOCKED:
                spent = temp_sta.apply_cost(base_fp_cost, stamina_block or {})
            else:
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

    # Calculate attacker stamina cost (equal to AP cost of attack)
    # This will be spent by action_handler after the attack resolves
    # Apply skill-based stamina cost reduction
    stamina_spent_attacker = 0
    if attacker.weapon:
        stamina_spent_attacker = max(1, attacker.weapon.attack_time - skill_stamina_reduction)
    else:
        stamina_spent_attacker = max(1, 5 - skill_stamina_reduction)  # Default unarmed attack cost

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
