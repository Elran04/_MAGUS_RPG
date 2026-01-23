# 🗺️ MAGUS RPG System — Development Roadmap

## 🎯 Overview
Two modules: GM Toolkit (PySide6) for data/editing and a Pygame combat demo for mechanics prototyping. Godot is the likely target for the final game, so the Pygame module is for mechanics validation.

## ✅ Recently Completed
- **Menu Initialization UX**: GameContext loads on a background thread; menu stays interactive with queued selections and a loading hint for Quick Combat/New Game
- **Skills System**: Skills VO with normalized lookup; weaponskill modifiers (BASE + UNIQUE effects); weaponskill_longswords (levels 0-6 with all effects); integrated with attack resolution and critical thresholds
- **Critical Failure Mechanics**: Level-dependent failure ranges; corrected thresholds; distinct CRITICAL_FAILURE outcome; 11 tests fixed
- **Quick Combat Weapon Quickslots**: Auto-equips 3 weapons (main + 2 quickslots); displayed in unit info popup; data layer complete
- **Stamina/Fatigue System**: Complete with 5 states (Friss → Kimerült → Unconscious); progressive TÉ/VÉ penalties; action costs for attacks/block/parry/dodge
- **Injury Condition System**: 4-tier tracking (Egészséges/Könnyű/Súlyos/Kritikus) based on FP/EP thresholds; penalties to all combat stats (KÉ/TÉ/VÉ/CÉ)
- **Unconscious Mechanics**: Units at 0 stamina have zero combat values, cannot act, turns auto-skipped
- **Zone-Based Armor Integration**: Hit zone resolution for real hits; SFÉ absorption by body location; block/parry use raw damage
- **Combat UI Enhancements**: HUD shows real-time stamina; conditions tab displays fatigue/injury states; enriched combat messages with zone/SFÉ/damage details
- ScenarioService refactor + focused tests; Equipment validation fixes
- Combat docs merged into `COMBAT_MECHANICS.md` with Quick Reference
- Character Creator summary/export + **Character Loader UI** (browse/view/delete)

## 🎯 Current Focus (short-term)
- **In-Battle Weapon Switching**: Hotkeys (1/2) to switch between main_hand and quickslots; AP cost; visual feedback
- **Dodge Resolution**: Speed checks (Gyorsaság próba); partial damage on failed dodge; skill-based cost reduction
- **Stamina Recovery**: Turn-based or rest mechanics; regeneration rates; exhaustion saves
- Character Creator: inline editing fields for saved characters
- Combat UX: visual feedback improvements (icons, damage numbers, condition indicators)

## 🔭 Backlog / Future
- **Shield as Separate Equipment**: Distinct from weapons; active block mechanics; VE bonus management
- **Advanced Combat**: Dual-wielding penalties/bonuses; two-handed weapon bonuses; charge mechanics; combat maneuvers
- **Ranged Combat**: Attack resolution for bows/crossbows; ammunition tracking; range penalties
- **AI and Encounter Generation**: Procedural combat scenarios; enemy behavior trees
- **Adventure-Mode Framework**: Travel, events, persistence beyond combat
- **Item Templates**: Procedural equipment generation for GM Toolkit
- **Game Balance Config**: Centralized constants/settings for tuning

## 🚧 Next Milestones (near-term)
- **Combat Mechanics Polish**: Unit tests at 90%+ coverage; dodge resolution; stamina recovery; skill system hooks
- **Shield System**: Separate equipment entity; block cost reduction; VE calculation overhaul
- **Combat Demo UX**: Camera integration (pan/zoom); damage numbers; condition icons; combat log enhancements
- **Character System**: Load/edit UI completion; origin/birthplace integration; XP/level progression
- **Scenario Generator**: Random encounter creation; balanced team composition

## 📌 Status Snapshot
- **Combat Systems**: Stamina (5 fatigue states + unconscious), injury (4-tier conditions), zone-based armor, skills (weaponskill modifiers + critical failures), enriched attack resolution
- **Combat UI**: Real-time HUD (stamina/FP/EP bars), conditions tab (fatigue + injury), detailed combat messages (zone/SFÉ/damage), unit info popup (equipment + quickslots)
- **GM Toolkit**: Editors for skills/classes/equipment/races; 5-step character wizard; character loader (read-only + delete)
- **Data Layer**: JSON + SQLite hybrid; managers operational; Pydantic models
- **Tests**: 261 tests passing (skills, weaponskills, critical failures, combat mechanics); pytest/mypy/ruff configured
- **Docs**: COMBAT_MECHANICS.md comprehensive; DEVELOPER_GUIDE current; EQUIPMENT_SYSTEM.md updated; MkDocs builds successfully

## 📝 Tracking
- CHANGELOG.md for notable changes
- Semantic versioning: pending start (v0.1-alpha, v0.2-alpha)