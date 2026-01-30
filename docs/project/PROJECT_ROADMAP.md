# 🗺️ MAGUS RPG System — Development Roadmap

## 🎯 Overview
Two modules: GM Toolkit (PySide6) for data/editing and a Pygame combat demo for mechanics prototyping. Godot is the likely target for the final game, so the Pygame module is for mechanics validation.

## ✅ Recently Completed
- **Charge Special Attack**: Complete implementation with movement pathfinding, combat modifiers (+20 TÉ, -25 VÉ, 2x damage), UI dropdown, and visual feedback; minimum 5 hex distance, costs 10 AP + 20 STA
- **Opportunity Attack Reactions**: UI accept/decline popup, queued reactions, charge path ZoC checks, and detailed log output
- **Weapon Switching System**: Popup-based weapon switching (hotkey 'W' or button); swap between main_hand and quickslots; 5 AP cost; validation for wield modes and weapon compatibility
- **Menu Initialization UX**: GameContext loads on a background thread; menu stays interactive with queued selections and a loading hint for Quick Combat/New Game
- **Skills System**: Skills VO with normalized lookup; weaponskill modifiers (BASE + UNIQUE effects); weaponskill_longswords (levels 0-6 with all effects); integrated with attack resolution and critical thresholds
- **Critical Failure Mechanics**: Level-dependent failure ranges; corrected thresholds; distinct CRITICAL_FAILURE outcome; 11 tests fixed
- **Quick Combat Weapon Quickslots**: Auto-equips 3 weapons (main + 2 quickslots); displayed in unit info popup; data layer complete
- **Stamina/Fatigue System**: Complete with 5 states (Friss → Kimerült → Unconscious); progressive TÉ/VÉ penalties; action costs for attacks/block/parry/dodge
- **Injury Condition System**: 4-tier tracking (Egészséges/Könnyű/Súlyos/Kritikus) based on FP/EP thresholds; penalties to all combat stats (KÉ/TÉ/VÉ/CÉ)
- **Unconscious Mechanics**: Units at 0 stamina have zero combat values, cannot act, turns auto-skipped
- **Zone-Based Armor Integration**: Hit zone resolution for real hits; SFÉ absorption by body location; block/parry use raw damage
- **Combat UI Enhancements**: HUD shows real-time stamina; conditions tab displays fatigue/injury states; enriched combat messages with zone/SFÉ/damage details
- **Docs**: Added internal reference docs for conditions and skills
- ScenarioService refactor + focused tests; Equipment validation fixes
- Combat docs merged into `COMBAT_MECHANICS.md` with Quick Reference
- Character Creator summary/export + **Character Loader UI** (browse/view/delete)

## 🎯 Current Focus (short-term)
- **Weaponskills with Special Attacks**: Implement unique special attacks and effects for each weapon type (dagger combo, charge, shield bash, etc.) with skill-level progression
- **Crowd Control Effects System**: Implement knockdown, stun, daze, paralyzed conditions with application rules and stack behavior
- **Damage Over Time (DoT) Effects**: Bleed (ÉP loss/round), pain (FP loss/round), and other persistent damage mechanics
- **Saving/Check Throws**: Attribute and skill-based check mechanics with multiple outcomes (success, partial, critical success/fail)
- **Stance System**: Defensive, dual-wield, feint, and other stances sourced from skills with appropriate combat modifiers
- **Hitzone Specialization**: Expand hitzone system with conditional effects (specific zone + damage threshold → status effect, crowd control, DoT)
- **Combat-Related Skills**: Dodge, parry, block, and additional special attack skills implementation (one-by-one progression)
- **Stamina Recovery**: Turn-based or rest mechanics; regeneration rates; exhaustion saves

## 🔭 Backlog / Future
- **Shield Integration (Weapon Category)**: Shields remain in weapon category (no dedicated slot or models). Focus on VÉ bonus management and skill-based modifiers; stance system is separate from shields.
- **Advanced Combat**: Dual-wielding penalties/bonuses; two-handed weapon bonuses; additional special attacks; combat maneuvers
- **Ranged Combat**: Attack resolution for bows/crossbows; ammunition tracking; range penalties
- **AI and Encounter Generation**: Procedural combat scenarios; enemy behavior trees
- **Adventure-Mode Framework**: Travel, events, persistence beyond combat
- **Item Templates**: Procedural equipment generation for GM Toolkit
- **Game Balance Config**: Centralized constants/settings for tuning
- **Character Creator Polish**: Inline editing fields for saved characters; origin/birthplace integration; XP/level progression

## 🚧 Next Milestones (near-term)
- **Weaponskill Effects**: Complete unique effects for all weapon types; integrate into attack resolution
- **Condition & DoT System**: Knockdown/stun/daze/paralyzed conditions; bleed/pain DoT mechanics; condition application framework
- **Save Mechanics**: Attribute/skill check throws with outcome branches; integration with conditions and effects
- **Stance Framework**: Core stance system with combat modifier application; defensive, dual-wield, feint stances
- **Hitzone Conditional Effects**: Expand zone system to apply effects (conditions, DoT) on specific damage thresholds
- **Combat Demo UX**: Enhanced combat log with effect indicators; damage numbers; condition icons

## 📌 Status Snapshot
- **Combat Systems**: Stamina (5 fatigue states + unconscious), injury (4-tier conditions), zone-based armor, skills (weaponskill modifiers + critical failures), enriched attack resolution; charge special attack with damage multiplier and movement; opportunity attack reactions
- **Special Attacks**: Charge (move + attack with +20 TÉ, -25 VÉ, 2x damage), dagger combo (multi-hit with TÉ stacking), shield bash (1d3 damage with range/skill restrictions); framework ready for additional special attacks per weaponskill
- **Combat UI**: Real-time HUD (stamina/FP/EP bars), conditions tab (fatigue + injury), detailed combat messages (zone/SFÉ/damage), unit info popup (equipment + quickslots); special attacks dropdown (button-like when single option, full dropdown when multiple); action panel with toggle-based selection (ESC menu-only)
- **Skills System**: weaponskill modifiers (BASE + UNIQUE effects per weapon type), weaponskill_longswords fully implemented (levels 0-6), shieldskill modifiers defined (levels 0-5 with directional protection, stamina reduction, attacker damage, special actions); foundation ready for crowd control, DoT, saves, stances
- **GM Toolkit**: Editors for skills/classes/equipment/races; 5-step character wizard; character loader (read-only + delete)
- **Data Layer**: JSON + SQLite hybrid; managers operational; Pydantic models; equipment context system with MGT negation by skill
- **Tests**: 261 tests passing (skills, weaponskills, critical failures, combat mechanics, stamina, equipment validation, scenario service); pytest/mypy/ruff configured
- **Docs**: COMBAT_MECHANICS.md comprehensive; DEVELOPER_GUIDE current; EQUIPMENT_SYSTEM.md updated; DIRECTIONAL_MECHANICS.md for defense angles; SKILLS.md for weaponskill/shieldskill progression; MkDocs builds successfully

## 📝 Tracking
- CHANGELOG.md for notable changes
- Semantic versioning: pending start (v0.1-alpha, v0.2-alpha)