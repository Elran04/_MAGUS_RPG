## Font Management Automation

### Problem Solved
The application was hardcoded to use `C:\Windows\Fonts\DejaVuSans.ttf`, which doesn't exist on systems where the DejaVu font isn't installed. This caused `FileNotFoundError` crashes.

### Solution Implemented

A new **FontManager** utility automatically handles font loading with the following strategy:

#### Priority Order:
1. **Windows System Fonts**: Check if `C:\Windows\Fonts\DejaVuSans.ttf` exists
2. **Project Cache**: Look for cached font in `assets/fonts/DejaVuSans.ttf`
3. **Auto-Download**: Attempt to download font from GitHub mirror
4. **Graceful Fallback**: Use pygame's default system font

#### Key Features:
- **Automatic Download**: Caches fonts in the project to avoid repeated downloads
- **Multiple URLs**: Tries several download sources for reliability
- **Safe Loading**: `load_font()` function handles None gracefully
- **Logging**: Tracks all font loading attempts and fallbacks

### Usage

Instead of:
```python
import pygame
from config import DEJAVU_FONT_PATH
font = pygame.font.Font(DEJAVU_FONT_PATH, 24)  # Crashes if None
```

Use:
```python
from config import DEJAVU_FONT_PATH, load_font
font = load_font(DEJAVU_FONT_PATH, 24)  # Always works
```

### Files Modified

- **New**: `MAGUS_pygame/utils/font_manager.py` - Font management utility
- **Updated**: All font loading across the codebase to use `load_font()`
  - `presentation/screens/scenario_setup/scenario_screen.py`
  - `presentation/screens/scenario_setup/scenario_phases/*.py`
  - `presentation/components/scenario_play/*.py`
  - `config/__init__.py` and `config/paths.py`

### Implementation Details

```python
def load_font(font_path: Path | None, size: int) -> pygame.font.Font:
    """Safely load a font with fallback to pygame default.
    
    - Returns custom font if path is valid
    - Falls back to pygame default if path is None
    - Handles file not found errors gracefully
    """
```

### Testing

The font manager has been tested and will:
- Detect missing fonts automatically
- Download them from reliable sources when available
- Fall back to pygame's default font without crashing
- Log all operations for debugging

#### Current Behavior:
- System check: Looks for Windows system fonts ✓
- Project cache: Saves downloaded fonts for reuse ✓
- Download: Attempts GitHub mirrors (may require network) ✓
- Fallback: Uses pygame default font when all else fails ✓
