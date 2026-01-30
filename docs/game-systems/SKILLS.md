# Skills System

This document captures the intended and current behavior of **skills** in the Pygame combat prototype.

## Overview
The skills system provides standardized lookup and modifiers for combat resolution. It currently focuses on **weapon skills** that affect attack AP cost, stamina cost, critical thresholds, and special effects.

## Core Concepts
- **Skill IDs**: Weapons reference a `skill_id` (e.g., `weaponskill_longswords`).
- **Skill Lookup**: Skills are resolved via a normalized lookup so missing or unknown skill IDs safely default to rank 0.
- **Base vs Unique Effects**:
  - **BASE modifiers** apply to *all* weapon skills by rank (0–6).
  - **UNIQUE effects** apply to specific weapon categories at ranks 3 and 6.

## Weaponskill Modifiers (Current)
### BASE modifiers (all weapons)
- Rank‑based AP scaling
- Stamina cost modifiers
- Critical failure thresholds
- Critical hit thresholds (higher ranks reduce fail chance)

### UNIQUE effects (weapon‑specific)
- Example: **Longswords** at rank 3 and 6
  - Additional opportunity attack triggers
  - Overpower/critical shifts
  - Stat adjustments specific to the weapon family

## Integration Points
- **Attack Resolution**: Uses skill rank to modify stamina cost and critical thresholds.
- **AP Costs**: Attack AP cost scales with skill rank (unskilled doubles cost; rank 1 adds +2; rank 2+ uses base cost).
- **Opportunity Attacks**: Skill level is passed to OA resolution to ensure correct stamina cost and effects.

## Shieldskill Modifiers (Current)
Shieldskill progresses from level 0 (untrained) to level 5 (master), affecting defensive capabilities, stamina costs, and protection zones.

### Level 0: Untrained
- **Stat Penalties**: -10 KÉ, -25 TÉ, -20 VÉ, -30 CÉ (unskilled condition applied)
- **Stamina Cost**: 2× normal block stamina cost
- **Protection Zone**: FRONT only (angle 0)
- **MGT**: Full shield MGT applies
- **Special Actions**: None

### Level 1: Basic
- **Stat Penalties**: None (unskilled condition removed)
- **Stamina Cost**: 2× normal block stamina cost
- **Protection Zone**: FRONT only (angle 0)
- **MGT**: Full shield MGT applies
- **Special Actions**: None

### Level 2: Normal
- **Stat Penalties**: None
- **Stamina Cost**: 1× normal (no penalty)
- **Protection Zone**: FRONT + FRONT_LEFT + FRONT_RIGHT (angles 0, 1, 5)
- **MGT**: Full shield MGT applies
- **Special Actions**: None

### Level 3: Control
- **Stat Penalties**: None
- **Stamina Cost**: 1× normal with -3 stamina reduction on successful blocks (min 1)
- **Attacker Stamina Cost**: 1d3 stamina damage to attacker on block
- **Protection Zone**: FRONT + FRONT_LEFT + FRONT_RIGHT (angles 0, 1, 5)
- **MGT**: Full shield MGT applies
- **Special Actions**: Shield bash action unlocked

### Level 4: Mastery
- **Stat Penalties**: None
- **Stamina Cost**: 1× normal with -5 stamina reduction on successful blocks
- **Attacker Stamina Cost**: 1d6 stamina damage to attacker on block
- **Protection Zone**: FRONT + FRONT_LEFT + FRONT_RIGHT (angles 0, 1, 5)
- **MGT**: Shield MGT negated (no encumbrance penalty from shield)
- **Special Actions**: Shield bash + Reaction shield bash (1/round after successful block)

### Level 5: Master
- **Stat Penalties**: None
- **Stamina Cost**: 1× normal with -10 stamina reduction on successful blocks (min 1)
- **Attacker Stamina Cost**: 1d10 stamina damage to attacker on block
- **Protection Zone**: All directions except BACK (angles 0, 1, 2, 4, 5)
- **MGT**: Shield MGT negated
- **Special Actions**: Shield bash + Reaction shield bash (1/round after successful block)

### Directional Protection
Shield VÉ only applies when attacks come from angles within the protection zone. Attack angles are relative to defender facing:
- **FRONT** (0): Directly ahead
- **FRONT_RIGHT** (1): 60° right
- **FRONT_LEFT** (5): 60° left  
- **BACK_RIGHT** (2): 120° right
- **BACK_LEFT** (4): 120° left
- **BACK** (3): Directly behind

## Data Sources
- Weapon definitions include category and `skill_id`
- Skills data lives in the data layer and is loaded via managers
- Shield skill modifiers defined in `domain/mechanics/skills/shieldskill_modifiers.py`
- Protection zones enforce directional VÉ in attack resolution

## Planned / TODO
- Additional weapon families (shortswords, bows, polearms, etc.)
- Shield bash action implementation (unlocked at level 3+)
- Reaction shield bash mechanic (unlocked at level 4+)
- Attacker stamina damage on blocks (level 3+)
- Non‑combat skills (travel, crafting, social)
- UI for skill effects and rank descriptions
