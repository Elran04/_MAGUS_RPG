# Directional Attack and Defense Modifiers Implementation

## Overview

Implemented directional attack angle-based modifiers for the MAGUS combat system. The system now applies different TÉ bonuses to attackers and VÉ restrictions to defenders based on the relative direction of the attack.

## Attack Angle System

The attack angle system has 6 discrete directions (0-5) relative to the defender's facing:

- **0: FRONT** - Directly ahead (0°)
- **1: FRONT_RIGHT** - Front-right diagonal (60° right)
- **2: BACK_RIGHT** - Back-right diagonal (120° right)
- **3: BACK** - Directly behind (180°)
- **4: BACK_LEFT** - Back-left diagonal (120° left)
- **5: FRONT_LEFT** - Front-left diagonal (60° left)

See `MAGUS_pygame/domain/mechanics/attack_angle.py` for implementation.

## Attacker Directional TÉ Bonuses

Attackers receive position-based TÉ bonuses:

### Back Attack (+10 TÉ)
- Attack from direction 3 (directly behind defender)
- Represents a fully exposed back position

### Diagonal Attacks (+5 TÉ)
- Attacks from directions: 1 (front-right), 2 (back-right), 4 (back-left), 5 (front-left)
- These flanking positions provide tactical advantage

### Front Attack (+0 TÉ)
- Attack from direction 0 (directly in front)
- No bonus; baseline attack

**Example:**
```
Base TÉ: 50 + weapon(10) + roll(50) = 110

Back Attack:   110 + 10 = 120 TÉ
Diagonal Attack: 110 + 5 = 115 TÉ
Front Attack:   110 + 0 = 110 TÉ
```

## Defender Directional VÉ Restrictions

Defender equipment provides directional VÉ bonuses:

### Shield VÉ Protection
- **Applies to:** Front attacks only (angle 0)
- **Does NOT apply to:** All other angles (1-5)
- Default shield facing matches character facing
- Shield skill can expand protection area later

### Weapon VÉ Bonus
- **Applies to:** Front (0), Front-Right (1), Front-Left (5)
- **Does NOT apply to:** Back-Right (2), Back (3), Back-Left (4)
- Represents the weapon's ability to block/parry from forward positions

**Example:**
```
Defender: base_VE=50, weapon_VE=8, shield_VE=15

Front Attack (angle 0):
  block_VE = 50 + 15 = 65
  parry_VE = 50 + 8 + 15 = 73

Back Attack (angle 3):
  block_VE = 50 + 0 = 50  (no shield)
  parry_VE = 50 + 0 + 0 = 50  (no weapon, no shield)

Back-Right Attack (angle 2):
  block_VE = 50 + 0 = 50  (no shield)
  parry_VE = 50 + 0 + 0 = 50  (no weapon VE for back angles)
```

## Integration Points

### attack_resolution.py
1. **Imports attack angle system**
   - `get_attack_angle()` - Calculate relative direction
   - Direction check helpers - `is_attack_from_back()`, etc.

2. **Early angle calculation**
   - Computed before critical failure check
   - Used throughout attack resolution

3. **TÉ modifier application**
   - Applied after base attack value calculation
   - Includes directional bonuses before VÉ comparison

4. **VÉ restriction enforcement**
   - `calculate_defense_values()` now accepts `attack_angle` parameter
   - Shield and weapon VÉ are conditionally applied

## Test Coverage

### test_directional_modifiers.py (8 tests)
- **Attacker bonuses (6 tests):**
  - Back attack +10 TÉ
  - Back-left attack +5 TÉ
  - Back-right attack +5 TÉ
  - Front-left attack +5 TÉ
  - Front-right attack +5 TÉ
  - Front attack +0 TÉ (no bonus)

- **Defender restrictions (2 tests):**
  - Shield VÉ only applies to front attacks
  - Weapon VÉ only applies to front angles (0, 1, 5)

### test_attack_angle.py (9 tests)
- 6-direction angle detection
- Defender facing independence
- Helper function validation

### test_attack_resolution.py (24 tests)
- All existing tests pass
- Backward compatible with optional `attack_angle` parameter

### test_weaponskill_longswords.py
- Updated to account for directional bonuses in position-based tests

## Mechanical Design Rationale

1. **Attack Bonuses:**
   - Back attacks are most dangerous (+10 TÉ) - highest danger unaware
   - Diagonal/flank attacks are moderately dangerous (+5 TÉ)
   - Front attacks are standard (no bonus) - frontal engagement

2. **Defense Restrictions:**
   - Shield can only protect forward arc initially
   - Weapon parry limited to forward-facing directions
   - Back attacks bypass most active defenses
   - Encourages tactical positioning and facing awareness

3. **Skill System Integration:**
   - Shield skill can expand protection area (for future implementation)
   - Flanking and retreat-attacking rewards positioning tactics
   - Base system allows specialization in defensive angles

## Future Enhancements

1. **Shield Skills:** Expand shield coverage to other angles
2. **Flanking Bonuses:** Coordinated multi-attacker bonuses
3. **Facing Changes:** Movement and facing adjustment mechanics
4. **Special Attacks:** Leverage directional system for retreat attacks, shield bashes
5. **Armor:** Directional armor effectiveness (back armor weaker, etc.)

## Files Modified

- `MAGUS_pygame/domain/mechanics/attack_resolution.py` - Integrated directional modifiers
- `tests/pygame/test_weaponskill_longswords.py` - Updated TÉ expectations for directional bonus
- `tests/pygame/test_directional_modifiers.py` - New test file (8 tests)

## Backward Compatibility

All changes are backward compatible:
- `calculate_defense_values()` has optional `attack_angle` parameter (defaults to None)
- When `attack_angle=None`, all VÉ bonuses apply (legacy behavior)
- All existing tests pass with proper updates
