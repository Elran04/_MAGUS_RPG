# MAGUS RPG — Developer Guide

This guide consolidates the essentials for working on the project.

## Setup

**Requirements:**

- Python 3.13+
- Poetry

```powershell
# From repo root
poetry install
poetry run python MAGUS_pygame/main.py   # Run game demo
poetry run python Gamemaster_tools/main.py   # Run GM Toolkit
```

## Project Structure (high level)

- `Gamemaster_tools/`: PySide6 editors (skills, classes, equipment, races) + Character Creator
- `MAGUS_pygame/`: Pygame demo (hex combat, initiative, scenario loading)
  - `application/`: Orchestration services/handlers (e.g., `scenario_service.py`, `unit_setup_service.py`)
  - `domain/`: Entities, value objects, mechanics
  - `infrastructure/`: Repositories, rendering, events
  - `presentation/`: UI/screens
  - `docs/`: Architecture, mechanics, scenarios, project status

## Running

```powershell
# Game Demo
poetry run python MAGUS_pygame/main.py

# GM Toolkit
poetry run python Gamemaster_tools/main.py
  # Character Creator: "Karaktergenerálás" button
  # Character Loader: "Karakter betöltése" button (browse, view, delete saved characters)
```

## Quick Tasks

```powershell
# Run tests (quiet)
poetry run pytest -q

# Type check
poetry run mypy MAGUS_pygame/

# Lint & format check
poetry run ruff check .
poetry run black --check .

# Build docs
poetry run mkdocs build

# Serve docs locally
poetry run mkdocs serve
```

## Scenarios (Current Behavior)

- Scenario selection is handled by `ScenarioService`.
- Team size limits derive from scenario spawn zones (if present), otherwise fall back to a generic limit.
- Duplicate units can be disabled via `allow_duplicates=False`.
- Character/sprite existence is checked best-effort; missing assets log warnings but do not block adding.
- `ScenarioConfig` is immutable; built only after a valid map and both teams are present.

## Character Setup

- `UnitSetupService` loads character data, ensures defaults, and extracts:
  - Inventory (excluding equipped items or slotted items)
  - Skills (prefers `Szint`, falls back to `%`)
- Data sources: JSON (races, equipment, characters) + SQLite (skills/classes/combat stats)

## Testing & Quality

```powershell
# Run tests
poetry run pytest -q

# Type checking
poetry run mypy MAGUS_pygame/

# Lint/format
poetry run ruff check .
poetry run black --check .
```

New tests exist for `ScenarioService` validating team limits, duplicates, update/remove, and config building.

## Troubleshooting

- Logs: `MAGUS_pygame/logger/logs/pygame_YYYYMMDD.log`
- Common checks:
  - Run from repo root with Poetry
  - Ensure characters JSON in `characters/`
  - Ensure sprites in `MAGUS_pygame/assets/sprites/`

## Documentation Map

- `docs/ARCHITECTURE.md`: Design and layering
- `docs/COMBAT_MECHANICS.md`: Combat rules (includes quick reference at top)
- `docs/EQUIPMENT_SYSTEM.md`: Equipment model and validation
- `docs/SCENARIO_EDITOR.md`: Editor concepts
- `docs/PROJECT_STATUS.md`: Current status snapshot

## Roadmap & Changelog

- Roadmap: `docs/PROJECT_ROADMAP.md`
- Recommended: add and maintain `CHANGELOG.md` for noteworthy updates

## Glossary (quick)

- **FP / ÉP**: Pain tolerance/ Health points; FP absorbs most weapon damage, EP loss occurs on big hits or by reach rules.
- **KP**: Skill points spent during character creation/learning.
- **SFÉ**: Armor absorption value; reduced by overpower hits and used to mitigate FP damage.
- **Reach**: Weapon reach category; dictates mandatory EP loss per FP damage bucket.
- **Stamina / Stamina State**: Fatigue resource; state modifies TE/VE and gates actions (block/parry/dodge costs).
- **TE / VE / CE**: Attack / Defense / Ranged values on characters.
- **MGT**: Armor movement penalty.
- **ScenarioConfig**: Immutable config built by ScenarioService before starting combat.
- **UnitSetup**: Input bundle for units (character file, sprite, equipment/skills) used by ScenarioService/UnitSetupService.

