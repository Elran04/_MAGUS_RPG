# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
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

### Changed
- Renamed `ScenarioService` methods for clarity: `can_advance_from_team_a` → `has_team_a_units`, `can_finish` → `has_team_b_units`
- Merged `COMBAT_MECHANICS_SUMMARY.md` into `COMBAT_MECHANICS.md` with Quick Reference section
- Fixed critical hit routing: clarified FP vs EP damage paths in combat mechanics
- Moved legacy docs to `docs/archive/` (QUICKSTART, IMPLEMENTATION_SUMMARY, MIGRATION, etc.)
- Updated all documentation paths to reflect new structure
- Standardized naming: `Project_Roadmap.md` → `PROJECT_ROADMAP.md`
- Restructured test suite from package-level folders to centralized root `tests/` folder with subdirectories
- Test execution now uses root conftest.py with dynamic sys.path management instead of package-level conftest files

### Fixed
- Equipment validation: restored missing return statements for valid cases
- Test coverage: added tests to catch missing returns and slot mismatches
- Documentation: removed outdated map editor references
- Links: updated all cross-references to archived and renamed docs

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
