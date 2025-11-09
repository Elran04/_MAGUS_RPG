# MAGUS Combat Mechanics Summary

## Attack Outcomes

### 1. MISS
- **Condition**: TÉ ≤ base_VÉ
- **Effect**: No damage
- **Example**: TÉ 65 ≤ VÉ 100 → MISS

### 2. HIT (Normal)
- **Condition**: base_VÉ < TÉ ≤ dodge_VÉ (and not critical)
- **Damage**: Goes to **FP** (Fájdalom Pont - Pain Points)
- **Special**: Mandatory EP loss based on weapon reach
  - Reach 1: 6 FP → 1 EP
  - Reach 2-3: 8 FP → 1 EP
  - Reach 4+: 10 FP → 1 EP
- **Example**: TÉ 105 > VÉ 60, 10 FP + 1 EP (mandatory)

### 3. BLOCKED / PARRIED
- **Condition**: TÉ falls in block/parry threshold ranges
  - BLOCKED: base_VÉ < TÉ ≤ block_VÉ (shield defense)
  - PARRIED: block_VÉ < TÉ ≤ parry_VÉ (weapon defense)
- **Damage**: Converted to **Stamina cost** (FP drain)
- **Stamina Cost**: Based on RAW incoming weapon damage (NO armor absorption)
  - Higher damage weapons (e.g., warhammer) cost more stamina to block/parry
  - Lower damage weapons (e.g., knife) cost less stamina to block/parry
  - Modified by defender's blocking/parrying skill level
  - **Armor does NOT reduce stamina cost** - active defense negates armor benefit
- **Example**: Blocking a 2d8+3 warhammer (damage 8) costs significantly more stamina than blocking a 1d4 knife (damage 2), regardless of armor worn

### 4. CRITICAL (Pure)
- **Condition**: Attack roll ≥ critical threshold (based on weapon skill)
- **Damage**: Amplified damage to **FP** (with mandatory EP loss)
- **Effects**:
  - Auto-hit (ignores VÉ)
  - Damage multiplied (1.5x to 2.5x based on skill)
  - Armor ignored (SFÉ not applied)
  - Still applies mandatory EP loss
- **Example**: Roll 97, skill 2 → TÉ 157 vs VÉ 110
  - Outcome: CRITICAL
  - Damage: 15.75 FP + 1 EP (mandatory)
  - **Critical does NOT bypass FP** - only amplifies FP damage!

### 5. OVERPOWER (Pure)
- **Condition**: TÉ > VÉ + 50 (threshold modifiable by skills)
- **Damage**: Direct damage to **EP** (Életerő Pont - Life Force)
- **Effects**:
  - Bypasses FP entirely
  - Degrades ALL armor pieces by 1 SFÉ permanently
  - No mandatory EP loss (already direct EP damage)
- **Example**: TÉ 148 > VÉ 60 + 50
  - Outcome: OVERPOWER
  - Damage: 12 EP (direct)

### 6. CRITICAL_OVERPOWER (Devastating Combo)
- **Condition**: Both critical AND overpower conditions met
- **Damage**: Amplified damage to **EP**
- **Effects**:
  - Critical: damage multiplied, armor ignored
  - Overpower: damage goes to EP, armor degraded
  - **This is the "one-shot" scenario** - a devastating strike!
- **Example**: Roll 96, TÉ 156 > VÉ 60 + 50
  - Outcome: CRITICAL_OVERPOWER
  - Damage: 15.75 EP (multiplied, direct)
  - Both is_critical and is_overpower flags are True

### 7. DODGE_ATTEMPT
- **Condition**: parry_VÉ < TÉ ≤ dodge_VÉ
- **Effect**: Requires Gyorsaság (speed) check
- **Stamina Cost**: Fixed base cost (6 points) modified by dodge skill
  - Unlike block/parry, dodge cost is independent of incoming damage
  - Represents physical exertion of evasive movement
  - Stamina spent immediately, even if dodge check fails
- **Notes**: Dodge success resolution TODO

## Key Mechanics

### Damage Routing Decision Tree
```
Is it OVERPOWER (TÉ > VÉ + 50)?
├─ YES → Degrade armor first
│        Is it also CRITICAL?
│        ├─ YES → CRITICAL_OVERPOWER → Damage to EP (multiplied, ignores armor)
│        └─ NO  → OVERPOWER → Damage to EP
│
└─ NO → Is it CRITICAL?
        ├─ YES → CRITICAL → Damage to FP (multiplied, ignores armor, + mandatory EP)
        └─ NO  → Is it HIT/BLOCK/PARRY?
                 ├─ YES → Damage to FP (with armor, + mandatory EP)
                 └─ NO  → MISS → No damage
```

### Critical Hit Thresholds (Placeholder)
| Weapon Skill Level | Critical Threshold |
|--------------------|-------------------|
| 0-1                | 99                |
| 2-3                | 95                |
| 4-5                | 90                |

### Critical Damage Multipliers (Placeholder)
| Weapon Skill Level | Damage Multiplier |
|--------------------|-------------------|
| 0-1                | 1.5x              |
| 2-3                | 1.75x             |
| 4-5                | 2.0x              |
| 6+                 | 2.5x              |

### Armor Mechanics
- **SFÉ** (Sebzés Felfogó Érték): Armor absorption value
- **Current SFÉ**: Can be degraded by overpower strikes
- **Degradation**: Each overpower reduces current_sfe by 1 permanently
- **Repair**: Can restore current_sfe up to base sfe value
- **Broken**: current_sfe = 0 means armor is broken (no protection)
- **Critical Ignores Armor**: Critical hits ignore armor entirely (damage calculated as if armor_absorption = 0)

### Mandatory EP Loss
Even normal hits to FP cause some EP loss based on weapon reach:
- **Reach 1** (unarmed, dagger): Every 6 FP → 1 EP
- **Reach 2-3** (sword, mace): Every 8 FP → 1 EP
- **Reach 4+** (two-handed, polearm): Every 10 FP → 1 EP

This represents the physical trauma of being struck, even when armor/toughness absorbs most damage.

## Common Misconceptions

### ❌ WRONG: "Critical hits bypass FP and deal EP damage"
- **Critical ALONE**: Deals amplified damage to **FP** (not EP)
- Only when **BOTH critical AND overpower** occur does damage go to EP

### ❌ WRONG: "Critical and overpower can't happen together"
- They absolutely can! That's the CRITICAL_OVERPOWER outcome
- Both flags (is_critical, is_overpower) can be True simultaneously

### ❌ WRONG: "Overpower degrades armor after critical ignores it"
- Armor degradation happens **BEFORE** critical ignores it
- This ensures overpower still has its armor-breaking effect

### ✅ CORRECT: Attack Flow Order
1. Check overpower (TÉ > VÉ + 50)
2. **If overpower**: Degrade armor first
3. Check critical (roll ≥ threshold)
4. Determine outcome (CRITICAL_OVERPOWER if both)
5. Calculate damage (multiply if critical, ignore armor if critical)
6. Route damage:
   - CRITICAL_OVERPOWER or OVERPOWER → EP
   - CRITICAL, HIT, BLOCKED, PARRIED → FP
   - MISS → No damage

## Test Coverage

**115 tests passing** covering:
- ✅ Armor creation, degradation, repair (29 tests)
- ✅ Attack resolution all outcomes (25 tests)
- ✅ Damage calculation with bonuses, multipliers, armor (28 tests)
- ✅ Reach system and mandatory EP loss (28 tests)
- ✅ Smoke tests for all scenarios (5 tests)

## Implementation Files

- `domain/mechanics/attack_resolution.py` - Main attack flow
- `domain/mechanics/damage.py` - Damage calculation
- `domain/mechanics/armor.py` - Armor entities and degradation
- `domain/mechanics/critical.py` - Critical hit detection
- `domain/mechanics/reach.py` - Weapon reach and mandatory EP
- `tests/test_attack_resolution.py` - Comprehensive attack tests
- `tests/test_combat_smoke.py` - End-to-end scenario tests

---

*Last updated: 2025-01-XX*
*Status: Core mechanics complete, 115 tests passing*
