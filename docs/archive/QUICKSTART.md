# Archived: Quick Start Guide

This guide has been archived in favor of `docs/DEVELOPER_GUIDE.md`, which consolidates setup, running, structure, and troubleshooting.

Original content follows for historical reference:

---

# Quick Start Guide

## 1. Prerequisites

Ensure you have:
- Python 3.13+ installed
- Pygame 2.6.1+ installed
- Character JSON files in `d:\_Projekt\_MAGUS_RPG\characters/`
- Sprite images in assets folders

## 2. Test the Architecture

```powershell
cd d:\_Projekt\_MAGUS_RPG\MAGUS_pygame
python main.py
```

You should see:
- A test screen with architecture test title
- A unit displayed on a hex
- Unit stats panel on the left
- Controls at the bottom

**Controls:**
- Arrow keys: Move unit
- R: Rotate unit
- ESC: Exit

## 3. Verify Everything Works

### Test 1: Imports
```powershell
python -c "from application.game_context import GameContext; print('✓ Imports OK')"
```

### Test 2: Character Loading
```powershell
python -c "from application.game_context import GameContext; c=GameContext(); chars=c.character_repo.list_all(); print(f'Found {len(chars)} characters'); print(chars)"
```

### Test 3: Sprite Loading
```powershell
python -c "from application.game_context import GameContext; c=GameContext(); sprites=c.sprite_repo.list_character_sprites(); print(f'Found {len(sprites)} sprites'); print(sprites)"
```

## 4. Explore the Code

Start with these files to understand the architecture:

```
1. domain/value_objects/__init__.py    # See immutable value types
2. domain/entities/__init__.py         # See Unit and Weapon entities
3. domain/services.py                  # See UnitFactory
4. infrastructure/repositories/        # See data access pattern
5. application/game_context.py         # See dependency injection
6. presentation/test_screen.py         # See UI layer example
```

## 5. Common Tasks

### Create a Unit
```python
from application.game_context import GameContext
from domain.value_objects import Position, Facing

context = GameContext()

unit = context.unit_factory.create_unit(
    character_filename="Warri.json",
    position=Position(q=0, r=0),
    facing=Facing(0)
)

print(unit)  # See unit details
```

### Load and Cache Character Data
```python
context = GameContext()
char_data = context.character_repo.load("Warri.json")
print(f"Name: {char_data['Név']}")
print(f"Stats: {char_data['Harci értékek']}")
```

### Work with Hex Positions
```python
from domain.value_objects import Position
from infrastructure.rendering.hex_grid import (
    hex_to_pixel,
    get_hex_neighbors,
    get_hex_range
)

pos = Position(q=0, r=0)
x, y = hex_to_pixel(pos)
neighbors = get_hex_neighbors(pos)
nearby = get_hex_range(pos, radius=2)

print(f"Pixel coords: ({x}, {y})")
print(f"Neighbors: {neighbors}")
print(f"Within 2 hexes: {len(nearby)} hexes")
```

## 6. Read Documentation

1. **ARCHITECTURE.md** - Understand the design
2. **MIGRATION.md** - Learn how to port old features
3. **IMPLEMENTATION_SUMMARY.md** - See what was built

## 7. Troubleshooting

### "Character file not found"
Check that character JSONs exist in:
```
d:\_Projekt\_MAGUS_RPG\characters\
```

### "Sprite not found"
Check that sprite files exist in:
```
d:\_Projekt\_MAGUS_RPG\MAGUS_pygame\assets\sprites\characters\
```

Or copy from old system:
```powershell
# Copy sprites from old system (if needed)
Copy-Item -Path ".\old_system\assets\sprites\characters\*" -Destination ".\assets\sprites\characters\" -Recurse
```

### "Equipment data not found"
Ensure equipment JSON exists:
```
d:\_Projekt\_MAGUS_RPG\Gamemaster_tools\data\equipment\weapons_and_shields.json
```

### Import errors
Make sure you're running from the MAGUS_pygame directory:
```powershell
cd d:\_Projekt\_MAGUS_RPG\MAGUS_pygame
```

## 8. Next Steps

### Learn by Example
1. Read `presentation/test_screen.py` to see how UI works
2. Read `domain/services.py` to see UnitFactory pattern
3. Read `infrastructure/repositories/` to see data access

### Start Porting Features
1. Choose a simple feature from old_system
2. Follow patterns in MIGRATION.md
3. Create domain logic first
4. Add infrastructure if needed
5. Wire through GameContext
6. Create UI components last

### Common First Ports
- **Damage calculation**: `old_system/systems/damage_calculator.py` → `domain/mechanics/damage.py`
- **Movement validation**: Use existing hex_grid + create movement rules
- **Simple menu**: `old_system/ui/menu.py` → `presentation/screens/menu_screen.py`

## 9. Getting Help

- Check logs: `logger/logs/pygame_YYYYMMDD.log`
- Enable debug logging: Check logger/logger.py
- Reference old implementation: `old_system/`
- Read ARCHITECTURE.md for design principles

## 10. Development Workflow

```powershell
# 1. Make changes
# Edit files in domain/, infrastructure/, application/, or presentation/

# 2. Test imports
python -c "from application.game_context import GameContext; print('OK')"

# 3. Run test program
python main.py

# 4. Check logs
cat logger/logs/pygame_*.log | Select-String "ERROR"

# 5. Iterate
```

## Quick Reference

### Key Classes
- `Unit`: Combat unit entity
- `Position`: Hex coordinate value object
- `UnitFactory`: Creates units from data
- `GameContext`: Dependency container
- `CharacterRepository`: Loads character data

### Key Functions
- `hex_to_pixel()`: Convert hex coords to screen
- `get_hex_neighbors()`: Get adjacent hexes
- `unit.move_to()`: Move unit
- `unit.take_damage()`: Apply damage
- `unit.spend_fatigue()`: Use FP

### File Organization
- `domain/` - Business logic (no external dependencies)
- `infrastructure/` - I/O, rendering, external concerns
- `application/` - Orchestration, services
- `presentation/` - UI screens and components
- `config/` - Paths and configuration
- `logger/` - Logging infrastructure

---

**You're now ready to develop with the clean architecture!**

