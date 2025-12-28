# 🗺️ MAGUS RPG System — Development Roadmap

## 🎯 Overview
Two modules: GM Toolkit (PySide6) for data/editing and a Pygame combat demo for mechanics prototyping. Godot is the likely target for the final game, so the Pygame module is for mechanics validation.

## ✅ Recently Completed
- ScenarioService refactor (clear naming: has_team_a_units / has_team_b_units) + focused tests (team limits, duplicates, update/remove, build_config)
- UnitSetupService cleanup (removed duplicate methods)
- Equipment validation fixes + tests (returns, slot mismatches)
- Combat docs merged into a single `COMBAT_MECHANICS.md` with Quick Reference; legacy docs archived
- Documentation consolidation: DEVELOPER_GUIDE, PROJECT_STATUS, nav cleanup, CHANGELOG.md
- Character Creator summary/export (SummaryStepWidget + JSON save in `character_storage.save_character`) in daily use
- Stamina system fully wired (domain `Stamina`, combat hooks, `tests/test_stamina*.py`)

## 🎯 Current Focus (short-term)
## 🎯 Current Focus (short-term)
- Character Creator: add load/edit flow (UI to open `characters/*.json`, edit, re-save)
- Combat UX: stamina/condition tuning + better feedback (icons/log text); ranged/thrown support remains
- Docs platform: wire CHANGELOG into MkDocs nav and keep publishing cadence now that build succeeds again
- Versioning: start semantic version tags; keep CHANGELOG up to date alongside doc site updates

## 📌 Status Snapshot
- GM Toolkit: editors for skills/classes/equipment/races; dark-mode UI; currency/shop/inventory; 5-step character wizard with working summary/export
- Data layer: JSON + SQLite hybrid; managers for races/classes/skills/equipment; Pydantic models in place
- Combat demo: melee functional; initiative/turn queue; armor layering; stamina hooks active; tests for damage/attack resolution (~115+)
- Services: ScenarioService and UnitSetupService clean; equipment validation verified by tests
- Docs: DEVELOPER_GUIDE + COMBAT_MECHANICS up to date; MkDocs build succeeds (warning: CHANGELOG missing from nav)
- Tests/Quality: pytest, mypy, ruff/black configured; ScenarioService tests cover team limits/duplicates/validation
- AI and encounter generation
- Adventure-mode framework (travel, events, persistence)
- Skill-driven combat depth (parry/dodge mastery, block cost tuning, hit localization, conditions)
- Dual-wielding and two-handed bonuses; item templates for GM Toolkit
- Game balance config (constants/game_balance.py), settings.json for runtime prefs

- GM Toolkit: editors for skills/classes/equipment/races; dark-mode UI; currency/shop/inventory; 5-step character wizard with working summary/export
- Data layer: JSON + SQLite hybrid; managers for races/classes/skills/equipment; Pydantic models in place
- Combat demo: melee functional; initiative/turn queue; armor layering; stamina hooks active; tests for damage/attack resolution (~115+)
- Services: ScenarioService and UnitSetupService clean; equipment validation verified by tests
- Docs: DEVELOPER_GUIDE + COMBAT_MECHANICS up to date; MkDocs build currently failing (needs fix) before site redeploy
- Tests/Quality: pytest, mypy, ruff/black configured; ScenarioService tests cover team limits/duplicates/validation

## 📝 Tracking
- CHANGELOG.md for notable changes
- Semantic versioning: pending start (v0.1-alpha, v0.2-alpha)