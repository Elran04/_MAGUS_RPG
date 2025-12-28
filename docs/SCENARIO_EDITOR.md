# Scenario Editor Guide

## Overview

The Scenario Editor is a full-featured visual tool for creating and editing battle scenarios in MAGUS RPG. Access it from the main menu via **"Scenario Editor"** (below Load Game).

## Features

### Scenario Management
- **Dropdown Selection**: Choose from existing scenarios in the `data/scenarios/` directory
- **New**: Create a new scenario with default settings
- **Save**: Write changes to JSON file (button highlights when modified)
- **Delete**: Remove scenario with confirmation dialog
- **Modified Indicator**: Asterisk (*) appears in title when unsaved changes exist

### Hex Grid Editor

Interactive hex grid displays the battle map with color-coded zones:
- **Blue hexes**: Team A deployment zone
- **Red hexes**: Team B deployment zone  
- **Gray hexes**: Obstacles (with type letter overlay)

#### Edit Modes

Click the mode buttons on the left to switch editing modes:

1. **Team A Zone** (Blue): Click hexes to add/remove Team A spawn positions
2. **Team B Zone** (Red): Click hexes to add/remove Team B spawn positions
3. **Obstacle**: Click hexes to place/replace obstacles (currently "tree" type)
4. **Erase**: Click hexes to remove all zone/obstacle data

#### Grid Coordinates

The editor uses hex cube coordinates (q, r) where:
- **q**: Horizontal axis (left-right)
- **r**: Vertical axis (diagonal)
- Grid bounds defined in scenario JSON `grid_size` field

### Map Configuration

- **Background Dropdown**: Select background image from available sprites
  - Located at bottom-left of screen
  - Changes immediately reflected (requires save to persist)
  - Backgrounds read from `assets/sprites/` directory

### Information Panel

Left panel displays:
- Current scenario name from JSON
- Grid size bounds (Q and R ranges)
- Zone hex counts (Team A/B)
- Obstacle count
- Current edit mode

## Workflow Examples

### Creating a New Scenario

1. Click **"New"** button
2. A new scenario file `new_scenario_N.json` is created and loaded
3. Edit deployment zones by clicking hexes in Team A/Team B modes
4. Add obstacles in Obstacle mode
5. Select background from dropdown
6. Click **"Save"** to persist changes
7. Optionally rename the JSON file in filesystem

### Editing Existing Scenario

1. Select scenario from dropdown at top
2. Switch edit mode (Team A, Team B, Obstacle, Erase)
3. Click hex tiles to modify
4. Change background if desired
5. Click **"Save"** when done
6. Or press ESC to exit with confirmation if modified

### Deleting a Scenario

1. Select scenario to delete
2. Click **"Delete"** button
3. Confirm in dialog (Y key or click Yes)
4. Editor switches to next available scenario

## Keyboard Shortcuts

- **ESC**: Exit editor (confirms if unsaved changes)
- **Y**: Confirm dialog "Yes"
- **N**: Confirm dialog "No"

## Scenario JSON Format

The editor reads/writes JSON files in this structure:

```json
{
  "name": "Display Name",
  "description": "Optional description",
  "grid_size": {
    "min_q": -6,
    "max_q": 7,
    "min_r": -6,
    "max_r": 7
  },
  "spawn_zones": {
    "team_a": [
      {"q": -5, "r": 0},
      {"q": -5, "r": 1}
    ],
    "team_b": [
      {"q": 5, "r": 0},
      {"q": 5, "r": 1}
    ]
  },
  "background": "grass_bg.jpg",
  "obstacles": [
    {"q": 0, "r": 0, "type": "tree"},
    {"q": 2, "r": 1, "type": "tree"}
  ]
}
```

### Fields

- `name`: Scenario display name (shown in scenario selection)
- `description`: Optional flavor text
- `grid_size`: Hex grid boundaries (cube coordinates)
- `spawn_zones`: Deployment hexes for each team
- `background`: Background image filename (from `assets/sprites/`)
- `obstacles`: Impassable/blocking hexes with type metadata

## Technical Details

### Architecture Integration

- **Repository Layer**: Uses `ScenarioRepository` to list scenarios, `SpriteRepository` for backgrounds
- **File I/O**: Direct JSON read/write via `config.get_scenario_json_path()`
- **UI Components**: Leverages `Dropdown` component for selection
- **Coordinate System**: Flat-top hex with cube coordinates (q, r, s where s = -q - r)

### Hex Rendering

- Flat-top orientation (pointy sides, flat top/bottom)
- Size: 25 pixels per hex
- Grid offset: (250, 120) screen pixels
- Coordinate conversion: `_pixel_to_hex()` and `_hex_to_pixel()`
- Hex rounding: Proper cube coordinate rounding to nearest integer hex

### Confirmation Dialogs

Modal overlay dialog for destructive actions:
- Semi-transparent background blocks interaction
- Yes/No buttons with keyboard shortcuts
- Used for: Delete scenario, Discard unsaved changes

## Future Enhancements

Potential additions:
- **Obstacle Type Selector**: Dropdown or cycle through types (tree, rock, water, etc.)
- **Grid Size Editor**: Adjust min/max Q/R bounds visually
- **Unit Placement**: Preview starting unit positions from scenario config
- **Description Editor**: Multi-line text input for scenario description
- **Undo/Redo**: Change history stack
- **Copy/Paste Zones**: Duplicate zone patterns
- **Symmetry Tools**: Mirror zones across axes
- **Terrain Types**: Multiple hex tile types beyond obstacles

## Troubleshooting

**"No scenario loaded" message**:
- Check that `data/scenarios/` contains valid JSON files
- Verify JSON syntax (use validator if needed)

**Hex clicks not registering**:
- Ensure clicking within grid bounds (check grid_size in JSON)
- Offset centered at (250, 120) - adjust if screen size differs

**Background not displaying in game**:
- Verify image exists in `assets/sprites/`
- Check filename matches exactly (case-sensitive)
- Supported formats: PNG, JPG, JPEG

**Save button disabled**:
- Button only activates when modifications made
- Try toggling a hex to enable

## File Locations

- **Scenario JSONs**: `MAGUS_pygame/data/scenarios/*.json`
- **Background Images**: `MAGUS_pygame/assets/sprites/*.{png,jpg,jpeg}`
- **Editor Code**: `MAGUS_pygame/presentation/screens/scenario_editor_screen.py`
- **Config Helpers**: `MAGUS_pygame/config/paths.py` (get_scenario_json_path)

---

*For game architecture: [ARCHITECTURE.md](./ARCHITECTURE.md)*  
*For setup and running: [DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md)*
