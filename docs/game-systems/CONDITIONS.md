# Conditions System

This document captures the intended and current behavior of **conditions** in the Pygame combat prototype.

## Overview
Conditions modify combat performance based on **stamina (fatigue)** and **injury**. They are applied automatically as stamina/FP/EP values change and feed into combat stats (KÉ/TÉ/VÉ/CÉ) through modifiers.

**Current condition families:**
- **Fatigue / Stamina State** (Friss → Kimerült → Unconscious)
- **Injury State** (Egészséges → Könnyű → Súlyos → Kritikus)

## Fatigue (Stamina States)
Stamina is tracked independently from FP/EP and represents short‑term endurance. Current stamina ratio determines the fatigue tier and applies combat penalties.

### States and effects
- **Friss**: No penalties
- **Felpezsdült**: Small penalties
- **Kifulladt**: Moderate penalties
- **Kifáradt**: Heavy penalties
- **Kimerült**: Severe penalties
- **Unconscious**: Current stamina = 0; unit cannot act, combat values are zeroed

> The exact penalty values are defined in the stamina system and applied through combat modifiers. HUD shows current stamina and state.

### Sources of stamina cost
- Attacks (attacker stamina)
- Block / Parry / Dodge (defender stamina)
- Charge (fixed stamina cost)
- Opportunity attacks (use normal attack stamina cost logic)

## Injury States
Injury is driven by FP/EP thresholds and represents longer‑term harm. It applies penalties to combat stats independent of stamina.

### Tiers
- **Egészséges**: No penalties
- **Könnyű**: Light penalties
- **Súlyos**: Significant penalties
- **Kritikus**: Severe penalties

## Unconscious
A unit at **0 stamina** becomes unconscious:
- Cannot act
- Turn is auto‑skipped
- Combat values are treated as 0

## Interaction Rules
- Fatigue and injury penalties **stack**.
- Stamina costs are applied via action and reaction resolution; damage (FP/EP) is applied separately.
- Defensive stamina cost is calculated from **raw incoming damage** on block/parry.

## UI / Feedback
- HUD shows stamina/FP/EP bars.
- Unit Info popup displays fatigue and injury states.
- Battle log displays stamina costs for defensive actions.

## Planned / TODO
- Stamina recovery (turn‑based / rest) and exhaustion saves
- Dodge resolution (speed check) with partial damage
- Condition icons / visual feedback in combat
- Expanded condition categories (status effects, debuffs)
