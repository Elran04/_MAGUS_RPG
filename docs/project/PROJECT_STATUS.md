# Project Status — MAGUS RPG (as of 2025-12-28)

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
- **Combat**: Melee attacks, damage calculation, armor absorption, critical hits, overpower strikes
  - Shield bonuses properly applied to defender VE
  - FP exhaustion handling (overflow converts to EP)
  - Defensive action costs shown as "Stamina" vs "FP" damage
- **Quick Combat**: Test mode bypassing menus (Goblin vs Warrior, forest clearing)
- **Stamina System**: Fully integrated (`domain/mechanics/Stamina`), affects block/parry/dodge costs, combat modifiers based on fatigue states
- **Initiative**: Turn queue with charge mechanics
- **Hex Grid**: Coordinate system, reach patterns, distance calculation
- **Scenario Loading**: JSON-based scenarios with spawn zones, team size enforcement, obstacle support
- **Camera**: Infrastructure present (`infrastructure/rendering/camera.py`) but not yet fully integrated into gameplay

### Data Layer
- **Hybrid Storage**: JSON (races, equipment, characters) + SQLite (skills, classes, combat stats)
- **Managers**: RaceManager, ClassDBManager, SkillManager, EquipmentLoader all operational
- **Models**: Pydantic models for races, dataclasses for combat entities

### Quality & Testing
- **Tests**: 115+ tests covering combat mechanics, stamina, equipment validation, scenario service
- **Type Safety**: mypy configured; strict checking in progress
- **Linting**: ruff + black for code quality
- **Documentation**: MkDocs Material site (builds successfully), consolidated guides, archived legacy docs

## Recent Changes (December 2025)

## Recent Changes (December 2025 - January 2026)
- **Quick Combat**: Added rapid test mode (`quick_combat_service.py`) with hardcoded Goblin vs Warrior battle
- **Combat Fixes**: Shield VE now correctly applied in attack resolution; FP exhaustion converts overflow to EP; defensive actions show "Stamina" cost vs "FP" damage
- **Equipment Integration**: Auto-equip system for quick combat; shield extraction from equipment for VE calculation

## Outstanding Work

### High Priority
- **Character Load/Edit UI**: No UI exists to open/edit saved `characters/*.json` files (only export works)
- **Camera Integration**: Camera module exists but not wired into game controls (panning/zoom)
- **Ranged Combat**: Detection logic present, but no ranged attack resolution or ammunition tracking
- **Combat Feedback**: Minimal visual feedback for stamina drain, conditions, damage numbers

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
