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
from typing import Optional

from domain.entities import Unit, Weapon
from domain.value_objects import DamageResult
from domain.mechanics.damage import DamageContext, calculate_final_damage
from domain.mechanics.critical import is_critical_hit, get_critical_damage_multiplier
from domain.mechanics.armor import ArmorPiece, apply_overpower_degradation
from domain.mechanics.reach import calculate_mandatory_ep_loss


class AttackOutcome(Enum):
    """Result of attack resolution before damage."""
    MISS = "miss"                    # all_TÉ <= base_VÉ
    BLOCKED = "blocked"              # base_VÉ < all_TÉ <= block_VÉ (shield)
    PARRIED = "parried"              # block_VÉ < all_TÉ <= parry_VÉ (weapon)
    DODGE_ATTEMPT = "dodge_attempt"  # parry_VÉ < all_TÉ <= dodge_VÉ (needs speed check)
    HIT = "hit"                      # all_TÉ > all_VÉ (normal hit)
    OVERPOWER = "overpower"          # all_TÉ > all_VÉ + 50 (overwhelming strike)
    CRITICAL = "critical"            # Critical hit (automatic, to FP)
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
        is_critical: Whether attack was a critical hit
        is_overpower: Whether attack was an overpower strike
        hit: Whether attack successfully hit (deals damage)
        damage_to_fp: Fatigue damage dealt
        damage_to_ep: Direct EP damage dealt
        armor_absorbed: Damage absorbed by armor
        armor_degraded: Whether armor was degraded
        mandatory_ep_loss: EP loss from reach rules
        requires_dodge_check: Whether defender needs speed check
    """
    outcome: AttackOutcome
    all_te: int
    all_ve: int
    attack_roll: int
    
    is_critical: bool = False
    is_overpower: bool = False
    hit: bool = False
    
    damage_to_fp: int = 0
    damage_to_ep: int = 0
    armor_absorbed: int = 0
    armor_degraded: bool = False
    mandatory_ep_loss: int = 0
    
    requires_dodge_check: bool = False
    dodge_success: Optional[bool] = None


def calculate_defense_values(
    defender: Unit,
    shield_ve: int = 0,
    dodge_modifier: int = 0,
    condition_modifier: int = 0
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
    # Base VÉ from character + conditions
    base_ve = defender.combat_stats.VE + condition_modifier
    
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
        base_ve=base_ve,
        block_ve=block_ve,
        parry_ve=parry_ve,
        dodge_ve=dodge_ve,
        all_ve=all_ve
    )


def calculate_attack_value(
    attacker: Unit,
    attack_roll: int,
    weapon: Optional[Weapon] = None,
    condition_modifier: int = 0
) -> int:
    """
    Calculate final attack value (all_TÉ).
    
    all_TÉ = base TÉ + weapon TÉ + d100 roll + conditions
    
    Args:
        attacker: Attacking unit
        attack_roll: d100 roll (1-100)
        weapon: Weapon used (defaults to attacker's weapon)
        condition_modifier: Conditions/status effects modifier
        
    Returns:
        Final attack value
    """
    if weapon is None:
        weapon = attacker.weapon
    
    base_te = attacker.combat_stats.TE
    weapon_te = weapon.te_modifier if weapon else 0
    
    all_te = base_te + weapon_te + attack_roll + condition_modifier
    
    return all_te


def resolve_attack(
    attacker: Unit,
    defender: Unit,
    attack_roll: int,
    base_damage_roll: int,
    weapon: Optional[Weapon] = None,
    defender_armor: Optional[list[ArmorPiece]] = None,
    weapon_skill_level: int = 0,
    shield_ve: int = 0,
    dodge_modifier: int = 0,
    attacker_conditions: int = 0,
    defender_conditions: int = 0,
    overpower_threshold: int = 50,
) -> AttackResult:
    """
    Resolve complete attack with all MAGUS rules.
    
    Args:
        attacker: Attacking unit
        defender: Defending unit
        attack_roll: d100 attack roll
        base_damage_roll: Base weapon damage roll
        weapon: Weapon used (defaults to attacker's weapon)
        defender_armor: List of defender's armor pieces
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
    
    if defender_armor is None:
        defender_armor = []
    
    # Check for critical hit first (affects everything)
    is_crit = is_critical_hit(attack_roll, weapon_skill_level)
    
    # Calculate attack and defense values
    all_te = calculate_attack_value(attacker, attack_roll, weapon, attacker_conditions)
    defense = calculate_defense_values(defender, shield_ve, dodge_modifier, defender_conditions)
    
    # Determine outcome
    outcome = AttackOutcome.MISS
    hit = False
    requires_dodge = False
    is_overpower_strike = False
    
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
    elif all_te <= defense.dodge_ve:
        # Dodge attempt required
        outcome = AttackOutcome.DODGE_ATTEMPT
        requires_dodge = True
        hit = True  # Pending dodge check
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
        from domain.mechanics.armor import calculate_total_armor_absorption
        armor_sfe = calculate_total_armor_absorption(defender_armor)
        
        # Overpower degrades armor before applying (even if critical will ignore it)
        if is_overpower_strike and armor_sfe > 0:
            apply_overpower_degradation(defender_armor)
            armor_degraded = True
            # Recalculate after degradation
            armor_sfe = calculate_total_armor_absorption(defender_armor)
        
        # Critical hits ignore armor (after degradation if overpower)
        if is_crit:
            armor_sfe = 0
        
        # Apply critical damage multiplier
        damage_multiplier = 1
        if is_crit:
            damage_multiplier = get_critical_damage_multiplier(weapon_skill_level)
        
        # Calculate damage
        damage_ctx = DamageContext(
            charge_multiplier=damage_multiplier,
            armor_absorption=armor_sfe
        )
        damage_result = calculate_final_damage(attacker, weapon, base_damage_roll, damage_ctx)
        
        # Determine where damage goes based on outcome
        if outcome in (AttackOutcome.BLOCKED, AttackOutcome.PARRIED):
            # Block/parry: damage goes to FP only
            # TODO: Apply block/parry skill modifiers to reduce FP damage
            damage_to_fp = damage_result.final_damage
            armor_absorbed = damage_result.armor_absorbed
            
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
    
    return AttackResult(
        outcome=outcome,
        all_te=all_te,
        all_ve=defense.all_ve,
        attack_roll=attack_roll,
        is_critical=is_crit,
        is_overpower=is_overpower_strike,
        hit=hit,
        damage_to_fp=damage_to_fp,
        damage_to_ep=damage_to_ep,
        armor_absorbed=armor_absorbed,
        armor_degraded=armor_degraded,
        mandatory_ep_loss=mandatory_ep,
        requires_dodge_check=requires_dodge,
    )


def apply_attack_result(result: AttackResult, defender: Unit) -> None:
    """
    Apply attack result damage to defender.
    Mutates defender's EP and FP.
    
    Args:
        result: Attack result with damage values
        defender: Unit to apply damage to
    """
    if not result.hit:
        return
    
    # Apply FP damage
    if result.damage_to_fp > 0:
        defender.spend_fatigue(result.damage_to_fp)
    
    # Apply EP damage (direct + mandatory)
    total_ep_damage = result.damage_to_ep + result.mandatory_ep_loss
    if total_ep_damage > 0:
        defender.take_damage(total_ep_damage)
