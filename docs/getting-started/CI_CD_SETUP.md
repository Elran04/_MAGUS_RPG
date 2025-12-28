# CI/CD and Code Quality Setup

This document describes the automated quality checks configured for the project.

## Overview

The project uses:
- **GitHub Actions** for CI/CD (automated testing on push/PR)
- **Pre-commit hooks** for local quality checks before commits
- **pytest.ini** for centralized test configuration

## GitHub Actions CI

### Workflow File
`.github/workflows/ci.yml`

### What It Does
Automatically runs on every push and pull request to `main` or `develop`:

1. **Run tests** (`pytest`)
2. **Type check** (`mypy`)
3. **Lint** (`ruff check`)
4. **Format check** (`black --check`)
5. **Build docs** (`mkdocs build --strict`)

### Platforms
- **Windows** (primary)
- **Ubuntu** (cross-platform validation)

### Viewing Results
- Check the **Actions** tab on GitHub
- Failed builds will block PRs
- Logs show exactly which checks failed

---

## Pre-commit Hooks

### What Are They?
Local checks that run automatically **before** each commit, catching issues before CI.

### Installation

```powershell
# Install dependencies (includes pre-commit)
poetry install --with dev

# Activate hooks
poetry run pre-commit install
```

### What Hooks Run?

1. **black** - Code formatting (auto-fixes)
2. **ruff** - Linting (auto-fixes simple issues)
3. **mypy** - Type checking (reports errors)
4. **trailing-whitespace** - Removes trailing spaces
5. **end-of-file-fixer** - Ensures single blank line at EOF
6. **check-yaml** - Validates YAML syntax
7. **check-json** - Validates JSON syntax (for character files, etc.)
8. **check-added-large-files** - Prevents committing large files (>500KB)
9. **check-merge-conflict** - Detects merge conflict markers
10. **debug-statements** - Finds leftover debugger calls
11. **isort** - Sorts imports alphabetically

### Manual Run

```powershell
# Run all hooks on all files (e.g., after setup)
poetry run pre-commit run --all-files

# Run specific hook
poetry run pre-commit run black --all-files
poetry run pre-commit run mypy --all-files
```

### Skipping Hooks (Emergency Only)

```powershell
# Skip hooks for urgent commit (not recommended)
git commit -m "Urgent fix" --no-verify
```

---

## Test Configuration (pytest.ini)

### Location
`pytest.ini` (project root)

### Features

**Test Markers** - Categorize tests:
```powershell
poetry run pytest -m smoke       # Quick smoke tests
poetry run pytest -m integration # Full integration tests
poetry run pytest -m unit        # Isolated unit tests
poetry run pytest -m slow        # Long-running tests
```

**Default Options**:
- Verbose output (`-v`)
- Short traceback (`--tb=short`)
- Strict markers (prevents typos)

### Test Discovery
- Files: `test_*.py`
- Classes: `Test*`
- Functions: `test_*`
- Directory: `MAGUS_pygame/tests/`

---

## Common Workflows

### First-Time Setup
```powershell
poetry install --with dev
poetry run pre-commit install
poetry run pre-commit run --all-files  # Initial cleanup
```

### Daily Development
```powershell
# Make changes
poetry run pytest -k test_something  # Test specific feature

# Pre-commit runs automatically on:
git add .
git commit -m "Feature: XYZ"

# If hooks fail, fix issues and commit again
```

### Before PR
```powershell
# Run full test suite
poetry run pytest -v

# Run all quality checks
poetry run pre-commit run --all-files

# Build docs
poetry run mkdocs build --strict
```

### CI Failure Debugging
If CI fails but local works:
1. Check CI logs for specific error
2. Ensure Poetry lock file is committed
3. Verify Python version match (3.13)
4. Test on Ubuntu if Windows-specific issue suspected

---

## Troubleshooting

### Pre-commit is slow on first run
**Cause**: Hooks download dependencies (mypy, ruff, etc.) on first use  
**Solution**: Wait ~2 minutes; subsequent runs are fast

### Mypy fails with missing imports
**Cause**: Type stubs not available for some packages  
**Solution**: Already configured with `--ignore-missing-imports`

### YAML check fails on mkdocs.yml
**Cause**: Custom YAML tags not recognized by checker  
**Solution**: Expected; CI uses mkdocs build to validate instead

### Ruff auto-fixes broke my code
**Cause**: Rare; ruff is conservative  
**Solution**: Review changes with `git diff`, revert if needed

### Black reformatted my code
**Cause**: Black enforces consistent style  
**Solution**: Accept changes (improves consistency) or configure `.blackignore`

---

## Configuration Files

| File | Purpose |
|------|---------|
| `.github/workflows/ci.yml` | GitHub Actions CI workflow |
| `.pre-commit-config.yaml` | Pre-commit hooks configuration |
| `pytest.ini` | Test runner configuration |
| `pyproject.toml` | Tool settings (black, ruff, mypy) |
| `.gitignore` | Excludes cache files, build artifacts |

---

## Future Enhancements

**Planned additions** (from infrastructure recommendations):
- Test coverage reporting (`pytest-cov`)
- Dependency security scanning (`safety`)
- Semantic versioning automation (`commitizen`)
- PyInstaller executable builds
- Data backup system for character files

---

## Quick Reference

```powershell
# Run tests
poetry run pytest

# Format code
poetry run black .

# Lint code
poetry run ruff check --fix .

# Type check
poetry run mypy MAGUS_pygame/ Gamemaster_tools/

# Run all pre-commit hooks
poetry run pre-commit run --all-files

# Build docs
poetry run mkdocs build --strict
poetry run mkdocs serve  # Live preview
```
