# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- **Weaponskill AP Costs**: Attack AP cost now properly scales with weaponskill level (unskilled doubles cost, level 1 adds +2, level 2+ uses base cost)
- **Atomic Attack Transactions**: Attack effects (damage, stamina) are only applied after AP is successfully spent, preventing partial execution and state corruption
- **Charge Special Attack**: Complete implementation of charge mechanics (move up to 5 hexes + melee attack)
  - Domain action: ChargeAction with movement pathfinding, facing adjustment, and attack resolution
  - Combat modifiers: +20 TÉ for attack, -25 VÉ penalty, 2x damage multiplier
  - Cost: 10 AP, 20 Stamina; minimum distance 5 hexes, maximum range 5 hexes + weapon reach
  - UI: ActionPanel dropdown for special attacks with visual highlighting when active
  - Validation: charge-specific attackable zone visualization (movement + reach combined)
  - Execution pipeline: integrated with BattleService, ActionHandler, and BattleActionExecutor
- **Presentation Layer Message Formatting**: Attack result messages now formatted in presentation layer (battle_action_executor.py) instead of domain layer for proper separation of concerns
- **Color-Coded ÉP Damage Display**: Visual feedback for ÉP damage sources using color tags:
  - Purple: Mandatory EP loss from weapon size rule (e.g., dagger 6 FP = 1 ÉP)
  - White: FP overflow when FP exhausted
  - Red: Overpower strike direct ÉP damage
- **Enhanced Combat Messages**: 
  - Multi-line format (up to 3 lines) with proper spacing
  - Shows attack roll value in TÉ: `TÉ 68 (50)` where 50 is d100 roll
  - Pre-armor damage display for transparency
  - Breakdown of damage types (FP/ÉP) with source indication
- **Battle Screen Refactoring**: Split 786-line BattleScreen into lightweight coordinator pattern with three specialized classes:
  - **BattleInputHandler** (64 lines): Mouse/keyboard translation, hex hover tracking
  - **BattleActionExecutor** (249 lines): Combat action execution, message display with color parsing
  - **BattleRenderCoordinator** (202 lines): Rendering coordination, HUD, overlays, controls display
  - Result: 47% line reduction (786 → 430 lines), improved maintainability and testability
  - All game functions verified working: movement, attack, rotation, inspection, turn ending
- **Skills System**: Skills VO for normalized skill lookup; weaponskill modifiers (BASE universal + weapon-specific UNIQUE effects); integrated with attack resolution
- **Weaponskill_Longswords**: Full implementation (levels 0-6) with stat penalties/bonuses, stamina reduction, critical thresholds, overpower shifts, opportunity attacks (1x at level 3, 3x at level 6)
- **Critical Failure Mechanics**: Level-dependent failure ranges (0: 1-10, 1: 1-5, 2: 1 only, 3+: none); distinct CRITICAL_FAILURE outcome in attack resolution
- **Quick Combat Weapon Quickslots**: Auto-equips up to 3 weapons (main_hand, weapon_quick_1, weapon_quick_2); displayed in unit info popup
- **Stamina/Fatigue System**: Physical endurance tied to Állóképesség; progressive combat penalties across 5 states; stamina costs for attacks and defensive actions
- **Injury Condition System**: 4-tier condition tracking (Egészséges/Könnyű/Súlyos/Kritikus) based on FP/EP thresholds; penalties to all combat stats
- **Unconscious Mechanics**: Units at 0 stamina have zero combat values, cannot act, and their turns are automatically skipped
- **Zone-Based Armor Integration**: Hit zone resolution for real hits; SFÉ absorption by body location; block/parry use raw damage for stamina calculation
- **Enriched Combat Messages**: Attack results display hit zone, SFÉ absorption, and rolled damage for successful hits; stamina costs shown for defensive actions
- **Unit Tests**: 261 tests passing (expanded from 115); coverage for skills, weaponskills, critical failures, injury system, unconscious mechanics
- MkDocs Material documentation site with dark/light theme toggle
- Comprehensive unit tests for `ScenarioService` (team limits, duplicates, validation)
- `docs/DEVELOPER_GUIDE.md` - consolidated developer onboarding guide
- `docs/PROJECT_STATUS.md` - current capabilities and recent changes snapshot
- `docs/archive/` - organized historical documentation
- **CharacterLoaderQt**: UI for browsing, viewing, and deleting saved character files; integrates existing SummaryStepWidget for read-only display
- **CI/CD Pipeline**: GitHub Actions workflow for automated testing, linting, type checking, and documentation builds on push/PR (Windows + Ubuntu)
- **Pre-commit Hooks**: Automatic code quality checks (black, ruff, mypy, trailing whitespace, JSON validation) before commits
- **pytest.ini**: Centralized test configuration with markers (smoke, integration, unit, slow) and coverage support
- **docs/CI_CD_SETUP.md**: Complete guide for CI/CD workflows and pre-commit hook usage
- **Centralized Test Structure**: Root `tests/` folder with `pygame/` (198 tests) and `gamemaster_tools/` (6 tests) subdirectories
- **Root conftest.py**: Unified sys.path management for multi-package test execution with dynamic package priority
- **docs/architecture/TESTING.md**: Complete guide to test structure, execution patterns, and namespace management
- **Menu Loading UX**: Menu stays interactive while `GameContext` initializes on a background thread; actions are queued and auto-run once ready with a loading hint

### Changed
- **Message Architecture**: Moved attack result message formatting from domain layer (attack_action.py) to presentation layer (battle_action_executor.py) for proper separation of concerns
- **Critical Failure Display**: Now shows actual TÉ and VÉ values instead of 0 vs 0 for better player feedback
- **Combat Log Layout**: Fixed separator line positioning with static spacing (90px) to accommodate 3-line messages
- **Attack Execution Flow**: battle_screen.py now delegates to battle_action_executor.execute_attack() instead of calling battle_service directly
- **Critical Thresholds**: Corrected to level-dependent values (0-1: 101 impossible, 2: 100 nat only, 3: 100, 4: 96, 5+: 91); aligned with MAGUS rulebook
- **Weaponskill Architecture**: Refactored to BASE_WEAPONSKILL_MODIFIERS (universal levels 0-6) + WEAPONSKILL_UNIQUE_EFFECTS (weapon-specific levels 3 & 6 only)
- **Weapon Metadata**: Added category (e.g., "Hosszú kardok") and skill_id (e.g., "weaponskill_longswords") fields to Weapon entity
- **Damage Calculations**: Floor rounding for multiplied damage (no fractional HP loss); stamina and FP now fully independent systems
- **Stamina Penalties**: Updated to realistic values (Friss 0/0, Felpezsdült -2/-1, Kifulladt -4/-3, Kifáradt -7/-5, Kimerült -10/-8)
- **Combat Message Position**: Moved to bottom center above tooltip for better visibility
- **Defensive Actions**: Block/parry/dodge stamina costs now use defender's stamina snapshot; mirror deduction in opportunity attacks
- Renamed `ScenarioService` methods for clarity: `can_advance_from_team_a` → `has_team_a_units`, `can_finish` → `has_team_b_units`
- Merged `COMBAT_MECHANICS_SUMMARY.md` into `COMBAT_MECHANICS.md` with Quick Reference section
- Fixed critical hit routing: clarified FP vs EP damage paths in combat mechanics
- Moved legacy docs to `docs/archive/` (QUICKSTART, IMPLEMENTATION_SUMMARY, MIGRATION, etc.)
- Updated all documentation paths to reflect new structure
- Standardized naming: `Project_Roadmap.md` → `PROJECT_ROADMAP.md`
- Restructured test suite from package-level folders to centralized root `tests/` folder with subdirectories
- Test execution now uses root conftest.py with dynamic sys.path management instead of package-level conftest files
- Menu input now remains responsive during startup; loading overlay is informational instead of blocking

### Fixed
- **AP Validation Bug**: Added AP check to validate_attack_target() to prevent attacks without sufficient AP
- **Weapon Skill Mapping on Switch**: Fixed BattleService._build_weapon_entity() to use correct Hungarian category mapping ("Hosszú kardok" → "weaponskill_longswords") instead of hardcoded English keys, ensuring proper skill_id assignment
- **Float AP Cost Extraction**: Fixed _extract_ap_cost() to handle float values (from weaponskill multiplier calculations) instead of returning 0
- **Weapon Category Mappings**: Added missing mappings for "Tőrök" (daggers) → weaponskill_daggers and "Rövid kardok" (short swords) → weaponskill_shortswords
- **Unconscious Unit Turn Skipping**: Fixed end_turn() loop logic that incorrectly triggered battle_active=False when encountering unconscious units, causing false draw conditions
- **Battle Service Method Naming**: Fixed battle_action_executor calling non-existent attack_unit() instead of attack_current_unit()
- **Mandatory EP Loss Calculation**: Verified rule correctly applies to post-armor damage (damage_to_fp) not pre-armor damage
- **Color Tag Parsing**: Added support for <white>, <purple>, <red> tags in action_panel combat message rendering
- **Critical Failure Tests**: Fixed 11 failing tests across 4 files after CRITICAL_FAILURE implementation (updated weapon_skill_level parameters, adjusted rolls to avoid failure ranges)
- **Circular Import**: Resolved Stamina import issue in Unit entity using TYPE_CHECKING
- **HUD Stamina Display**: Fixed to read unit.stamina instead of re-initializing every frame
- **Zone Resolution**: Limited to real hits only; no zone calculation for blocked/parried/dodged attacks
- **Conditions UI**: Removed duplicate variable block causing NameError in UnitInfoPopup
- Equipment validation: restored missing return statements for valid cases
- Test coverage: added tests to catch missing returns and slot mismatches
- Documentation: removed outdated map editor references
- Links: updated all cross-references to archived and renamed docs
- Weapon switch popup: variable wield modes display correctly, validation enforces ranged/two-handed off-hand restriction, and unit popup shows item names reliably

### Removed
- Duplicate method definitions in `UnitSetupService`
- Debug logging from key application files
- Outdated scenario editor command from README
- Old package-level test directories (`MAGUS_pygame/tests/`, `Gamemaster_tools/tests/`)
- Package-level conftest.py files (replaced by single root conftest.py)
- Coverage cache files (.coverage, coverage.json, htmlcov/)
- 217 __pycache__/ directories (~1280 .pyc files) to improve repository cleanliness

## [2025-12] - December 2025

### Added
- ScenarioService with spawn-zone-based team size limits
- Equipment validation service with comprehensive tests
- Reaction handler with type-safe dataclasses

### Changed
- Application layer services refactored and cleaned
- Test suite expanded with focused scenario service tests

---

## How to Update

When making notable changes:

1. Add entries under `[Unreleased]` in appropriate categories (Added/Changed/Fixed/Removed)
2. Use present tense ("Add feature" not "Added feature")
3. Reference issue/PR numbers when applicable
4. When releasing, move `[Unreleased]` items to a dated version section
