# Project Status — MAGUS RPG (as of 2025-12-28)

## Overview
Two actively developed modules:
- GM Toolkit (PySide6): Editors for skills, classes, equipment, races, and a multi-step Character Creator.
- Game Demo (Pygame): Turn-based tactical combat on a hex grid with melee combat playable.

## Current Capabilities
- Data: Hybrid JSON + SQLite, managers for races, classes, skills, equipment; currency handling.
- Character Creation: 5-step wizard with KP tracking, prerequisite checks, inventory/shop, dark-mode UI.
- Combat: Initiative, basic melee, hex grid, scenario loading from JSON.
- Scenario: ScenarioService builds configs, enforces team size from spawn zones or generic limits; duplicate control optional.
- Testing/Quality: Extensive tests for combat and equipment; new tests cover scenario service edge cases; mypy/ruff/black configured.

## Recent Changes
- ScenarioService: Renamed methods `can_advance_from_team_a` → `has_team_a_units` and `can_finish` → `has_team_b_units`; updated usages.
- ScenarioService: Added focused unit tests (team size limits, duplicates, missing files, update/remove, build_config validation).
- UnitSetupService: Removed duplicate method definitions; kept documented+logged versions; behavior unchanged.
- Equipment Validation: Earlier fixes + tests to catch missing returns and slot mismatches.
- Type Checking: `reaction_handler.py` passes mypy strict; ongoing cleanup across application.

## Known Documentation Gaps
- README: Mentions `MAGUS_pygame/tools/map_editor.py` which is not present; command likely outdated.
- Scenario Docs: Should mention team size derives from spawn zones (with generic fallback) and non-strict asset existence checks.
- Architecture: Application layer services/handlers clarified (ScenarioService, UnitSetupService, Reaction/Action handlers) — reflect recent refactors.
- Roadmap: Several items can be marked complete (validation, scenario setup flow, tests); Next focus might shift to stamina/ranged.

## Proposed Documentation Updates
1) Fix README run commands and requirements; remove/replace map editor instruction.
2) Update QUICKSTART and SCENARIO docs to reflect scenario flow and team size rules.
3) Refresh ARCHITECTURE/IMPLEMENTATION_SUMMARY with current service boundaries and testing approach.
4) Update Project_Roadmap with completed items and near-term priorities.
5) Add CHANGELOG.md to capture refactors and test additions going forward.

---
This file is a living snapshot intended to guide doc cleanup and roadmap updates.
