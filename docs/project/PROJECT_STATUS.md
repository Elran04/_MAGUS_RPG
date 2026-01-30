# Project Status — MAGUS RPG (as of 2026-01-23)

## Overview

Two actively developed modules:

- **GM Toolkit (PySide6)**: Full-featured editors for skills, classes, equipment, races, and a complete 5-step Character Creator with working export.
- **Game Demo (Pygame)**: Hex-based tactical combat with functional melee, stamina system, initiative queue, and scenario loading.

## Current Capabilities

### GM Toolkit
- **Editors**: Skills, classes (with specializations), equipment (weapons/armor/general), races (11 races with attributes/skills)
- **Character Creator**: Complete 5-step wizard
  - Basic info + class/specialization selection
  - Skills assignment with placeholder resolution
  - Skill learning with KP spending
  - Equipment/inventory with currency management
  - Summary with JSON export to `characters/*.json`
- **Character Loader**: Browse saved characters, view summary, delete, refresh (read-only display; full editing planned)
- **UI/UX**: Dark mode, responsive layouts, currency widgets, validation feedback

### Game Demo
- **Combat Mechanics**: 
  - Attack resolution: melee, critical hits, overpower strikes, zone-based armor absorption
  - Special attacks: Charge (move up to 5 hexes + attack with +20 TÉ, -25 VÉ, 2x damage; 10 AP, 20 STA)
  - Skills system: weaponskill modifiers (BASE + UNIQUE effects per weapon type); weaponskill_longswords (levels 0-6); critical thresholds and failure ranges
  - Stamina system: 5 fatigue states with progressive penalties; unconscious handling (zero combat values, turn skipped)
  - Injury conditions: 4 tiers with KÉ/TÉ/VÉ/CÉ penalties based on FP/EP damage
  - Defensive actions: block/parry/dodge with stamina costs; reactions (opportunity attacks)
- **Combat UI**:
  - HUD: Real-time stamina/FP/EP bars, action points, round counter
  - Unit Info Popup: Stats, equipment, conditions tab (fatigue + injury states)
  - Combat messages: Enriched with hit zone, SFÉ absorption, rolled damage
- **Quick Combat**: Test mode bypassing menus (Goblin vs Warrior)
- **Initiative**: Turn queue with charge mechanics; KÉ-based ordering
- **Hex Grid**: Coordinate system, reach patterns, movement/attack highlighting
- **Scenario Loading**: JSON-based with spawn zones, team size enforcement, obstacles
- **Camera**: Infrastructure present but not yet wired to controls

### Data Layer
- **Hybrid Storage**: JSON (races, equipment, characters) + SQLite (skills, classes, combat stats)
- **Managers**: RaceManager, ClassDBManager, SkillManager, EquipmentLoader all operational
- **Models**: Pydantic models for races, dataclasses for combat entities

### Quality & Testing
- **Tests**: 261 tests passing (skills, weaponskills, critical failures, combat mechanics, stamina, equipment validation, scenario service)
- **Type Safety**: mypy configured; strict checking in progress
- **Linting**: ruff + black for code quality
- **Documentation**: MkDocs Material site (builds successfully), consolidated guides, archived legacy docs

## Recent Changes (December 2025)

## Recent Changes (January 2026)
- **Charge Special Attack**: Fully implemented charge mechanics with movement pathfinding, combat modifiers (+20 TÉ, -25 VÉ, 2x damage), UI dropdown, and charge-specific attackable zone highlighting; minimum 5 hex distance, costs 10 AP + 20 STA
- **Opportunity Attack Reactions**: Accept/decline popup, queued reactions, charge path ZoC checks, and battle log integration
- **Menu Initialization UX**: GameContext now builds on a background thread; menu stays clickable with a loading hint, and selections queue until initialization finishes (faster Quick Combat entry)
- **Weapon Switch Popup Polish**: Variable 1h/2h display fixed, validation passes selected wield mode, and guards block ranged/two-handed pairings with occupied off-hand; unit info popup now shows item names via shared context
- **Battle Screen Refactoring**: Split 786-line BattleScreen into three lightweight coordinators (47% reduction to 418 lines):
  - **BattleInputHandler**: Mouse/keyboard translation, hex hover tracking (64 lines)
  - **BattleActionExecutor**: Combat action execution, message display (208 lines)
  - **BattleRenderCoordinator**: Rendering coordination, UI overlays (202 lines)
  - Result: Improved code maintainability, better separation of concerns, easier to test and extend
  - All game functions verified: movement, attack, rotation, inspection, turn ending
- **Skills System**: Skills VO integrated; weaponskill modifiers (BASE universal + weapon-specific UNIQUE effects); weaponskill_longswords fully implemented (levels 0-6)
- **Critical Mechanics**: Corrected thresholds (level-dependent); failure ranges (0: 1-10, 1: 1-5, 2: 1 only, 3+: none); CRITICAL_FAILURE outcome; 11 tests fixed
- **Weapon Quickslots**: Auto-equips 3 weapons in quick combat (main_hand + 2 quickslots); displayed in unit info popup; switching UI pending
- **Stamina System**: 5 fatigue states (Friss → Kimerült) with progressive TÉ/VÉ penalties; unconscious at 0 stamina (zero combat values, turn skipped)
- **Injury Conditions**: 4-tier system (Egészséges/Könnyű/Súlyos/Kritikus) based on FP/EP thresholds; penalties to KÉ/TÉ/VÉ/CÉ
- **Zone-Based Armor**: Hit location resolution; SFÉ absorption by body part; block/parry stamina costs use raw damage
- **Combat UI**: HUD shows real-time stamina; conditions tab displays fatigue/injury; combat messages enriched with zone/SFÉ/damage details
- **Docs**: Added internal reference docs for conditions and skills
- **Quick Combat**: Rapid test mode for mechanics validation
- **Equipment Integration**: Auto-equip system; shield VE extraction

## Outstanding Work

### High Priority
- **In-Battle Weapon Switching**: Hotkeys (1/2) to switch between main_hand and quickslots; AP cost; visual feedback for active weapon
- **Dodge Resolution**: Gyorsaság (speed) checks; partial damage on failed dodge; skill-based stamina cost reduction
- **Stamina Recovery**: Turn-based regeneration; rest mechanics; exhaustion save implementation
- **Additional Weaponskills**: Implement unique effects for shortswords, bows, longhandled weapons (BASE modifiers already universal)
- **Camera Integration**: Wire existing camera module to game controls (pan/zoom)
- **Combat Feedback**: Visual polish (damage numbers, condition icons, status effects)

### Medium Priority
- **Scenario Generator**: No random encounter/combat setup tool
- **Origin/Birthplace System**: Data models exist (`Origin` in `race_model.py`) but not in Character Creator UI
- **XP/Leveling**: CombatStats support XP tracking but no progression UI
- **Item Templates**: No template system for procedural equipment generation

### Documentation
- Scenario docs should clarify spawn-zone-based team limits and non-strict asset checks
- Architecture doc could reflect recent application layer refactors (ScenarioService, UnitSetupService)

## Known Limitations

- **Pygame Demo**: Mechanics prototype only; final game likely targets Godot
- **Stamina UX**: System works but lacks polish (no icons, minimal feedback)
- **Armor Layering**: Schema present in JSON but conflict validation is warning-only
- **Dual-Wielding**: Basic support but no bonuses/penalties wired
- **Adventure Mode**: No travel/exploration; combat-only prototype

## Next Steps

1. **Character Load/Edit Flow**: Implement UI to select and modify saved characters
2. **Combat Polish**: Add visual feedback for stamina, conditions, damage; integrate camera controls
3. **Ranged Support**: Wire ranged attack resolution and ammunition system
4. **Versioning**: Start semantic tags (v0.1-alpha, etc.) and maintain CHANGELOG
5. **Documentation Cadence**: Keep MkDocs site updated as features land

---

This snapshot reflects the state as of December 28, 2025. See [PROJECT_ROADMAP.md](PROJECT_ROADMAP.md) for detailed plans and [CHANGELOG.md](CHANGELOG.md) for tracked changes.
