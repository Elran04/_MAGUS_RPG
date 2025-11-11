"""Scenario Editor - Create and edit battle scenarios.

Simple workflow:
1. Choose: New scenario or load existing
2. Edit deployment zones and obstacles on hex grid
3. Save changes

Architecture:
- Uses ScenarioRepository for file I/O (clean architecture)
- Presentation layer only handles UI/input
- No direct file system access
- Component-based design for maintainability
"""

from __future__ import annotations

from enum import Enum

import pygame
from application.game_context import GameContext
from infrastructure.events.editor_events import (
    EV_CLOSE,
    EV_LOAD,
    EV_NEW,
    EV_SAVE,
    EV_SET_BACKGROUND,
    EV_SET_DESCRIPTION,
    EV_SET_NAME,
    EV_TOOL_SELECT,
)
from infrastructure.events.event_bus import EditorEventBus
from infrastructure.rendering.hex_grid import get_grid_bounds, pixel_to_hex
from logger.logger import get_logger
from presentation.components.scenario_editor.hex_grid_editor import HexGridEditor
from presentation.components.scenario_editor.scenario_list_dialog import ScenarioListDialog

logger = get_logger(__name__)


class EditorMode(Enum):
    """Editor state machine (simplified)."""

    LOAD_DIALOG = "load_dialog"  # Scenario selection dialog
    EDITING = "editing"  # Main editing mode


class EditTool(Enum):
    """Available editing tools (mirrors external widget options)."""

    TEAM_A_SPAWN = "team_a"
    TEAM_B_SPAWN = "team_b"
    OBSTACLE = "obstacle"
    ERASE = "erase"


class ScenarioEditorScreen:
    """Scenario editor with hex grid visualization."""

    def __init__(self, screen_width: int, screen_height: int, context: GameContext):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.context = context

        # State
        # Start directly in editing; scenario may be None until created/loaded via tool window
        self.mode = EditorMode.EDITING
        self.action: str | None = None  # "back" to exit

        # Scenario data
        self.scenario_name = ""
        self.scenario_data: dict | None = None
        self.modified = False
        self.available_scenarios: list[str] = []
        self.background_cache: pygame.Surface | None = None

        # Components
        self.load_dialog: ScenarioListDialog | None = None
        self.hex_grid = HexGridEditor()  # Uses HEX_SIZE from config

        # Event bus (injected after creation)
        self.event_bus: EditorEventBus | None = None

        # Fonts
        self.font_large = pygame.font.Font(None, 48)
        self.font_normal = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)

        # Colors
        self.color_bg = (20, 20, 30)
        self.color_panel = (40, 40, 50)
        self.color_text = (240, 240, 255)
        self.color_highlight = (255, 215, 0)
        self.color_button = (60, 70, 90)
        self.color_button_hover = (80, 90, 120)

        # Current tool (controlled by external widget)
        self.current_tool: EditTool = EditTool.TEAM_A_SPAWN

        logger.info("Scenario Editor initialized")

    def set_event_bus(self, event_bus: EditorEventBus) -> None:
        """Inject event bus for communication with external tool window.

        Args:
            event_bus: Event bus instance for bidirectional communication
        """
        self.event_bus = event_bus
        logger.info("Event bus injected into scenario editor")

    def _setup_ui(self) -> None:
        """Legacy in-editor UI removed; external widget handles controls."""
        return

    def _load_scenario(self, scenario_stem: str) -> None:
        """Load scenario JSON via repository."""
        data = self.context.scenario_repo.load_scenario(scenario_stem)
        if data:
            self.scenario_data = data
            self.scenario_name = scenario_stem
            self.modified = False
            self.mode = EditorMode.EDITING
            self._load_background()  # Load background when scenario loads
            # Notify UI of state update
            if self.event_bus:
                try:
                    from infrastructure.events.editor_events import EV_STATE_UPDATE, EditorEvent

                    self.event_bus.publish_to_ui(
                        EditorEvent(
                            EV_STATE_UPDATE,
                            {
                                "scenario_name": self.scenario_data.get("name", self.scenario_name),
                                "description": self.scenario_data.get("description", ""),
                                "file": self.scenario_name,
                                "tool": self.current_tool.value,
                                "background": self.scenario_data.get("background"),
                                "counts": {
                                    "team_a": len(
                                        self.scenario_data.get("spawn_zones", {}).get("team_a", [])
                                    ),
                                    "team_b": len(
                                        self.scenario_data.get("spawn_zones", {}).get("team_b", [])
                                    ),
                                    "obstacles": len(self.scenario_data.get("obstacles", [])),
                                },
                            },
                        )
                    )
                except Exception:
                    pass
        else:
            logger.error(f"Failed to load scenario: {scenario_stem}")
            self.scenario_data = None

    def _create_new_scenario(self) -> None:
        """Create a new blank scenario."""
        # Find unique name
        self.available_scenarios = self.context.scenario_repo.list_scenarios()
        counter = 1
        while f"new_scenario_{counter}" in self.available_scenarios:
            counter += 1

        new_name = f"new_scenario_{counter}"
        self.scenario_name = new_name
        self.scenario_data = {
            "name": f"New Scenario {counter}",
            "description": "A new battle scenario",
            "spawn_zones": {"team_a": [], "team_b": []},
            "background": None,  # Default to no background
            "obstacles": [],
        }
        self.modified = True
        self.mode = EditorMode.EDITING
        self._load_background()  # Load background for new scenario
        logger.info(f"Created new scenario: {new_name}")
        # Notify UI of state update
        if self.event_bus:
            try:
                from infrastructure.events.editor_events import EV_STATE_UPDATE, EditorEvent

                self.event_bus.publish_to_ui(
                    EditorEvent(
                        EV_STATE_UPDATE,
                        {
                            "scenario_name": self.scenario_data.get("name", self.scenario_name),
                            "description": self.scenario_data.get("description", ""),
                            "file": self.scenario_name,
                            "tool": self.current_tool.value,
                            "background": self.scenario_data.get("background"),
                            "counts": {"team_a": 0, "team_b": 0, "obstacles": 0},
                        },
                    )
                )
            except Exception:
                pass

    def _load_background(self) -> None:
        """Load and cache the background image."""
        if not self.scenario_data:
            return

        background_name = self.scenario_data.get("background")
        if not background_name:
            self.background_cache = None
            return

        try:
            from config import BACKGROUND_SPRITES_DIR

            # Use background_name directly as filename (it's already a filename from the widget)
            bg_path = BACKGROUND_SPRITES_DIR / background_name
            if bg_path.exists():
                bg_surface = pygame.image.load(str(bg_path)).convert()
                # Scale to screen size
                self.background_cache = pygame.transform.scale(
                    bg_surface, (self.screen_width, self.screen_height)
                )
                logger.debug(f"Loaded background: {background_name}")
            else:
                logger.warning(f"Background file not found: {bg_path}")
                self.background_cache = None
        except Exception as e:
            logger.warning(f"Could not load background {background_name}: {e}")
            self.background_cache = None

    def _save_scenario(self) -> None:
        """Save current scenario via repository."""
        if not self.scenario_data or not self.scenario_name:
            return

        # Generate filename from scenario name: "Forest Clearing" -> "forest_clearing"
        scenario_display_name = self.scenario_data.get("name", self.scenario_name)
        filename = scenario_display_name.lower().replace(" ", "_")
        # Remove special characters, keep only alphanumeric and underscores
        filename = "".join(c for c in filename if c.isalnum() or c == "_")

        # Update internal scenario_name to match
        self.scenario_name = filename

        if self.context.scenario_repo.save_scenario(filename, self.scenario_data):
            self.modified = False
            logger.info(f"Saved scenario as: {filename}.json (name: {scenario_display_name})")
        else:
            logger.error(f"Failed to save scenario: {filename}")

    def _toggle_hex(self, q: int, r: int, tool: EditTool) -> None:
        """Toggle hex tile based on current tool."""
        if not self.scenario_data:
            return

        coord = {"q": q, "r": r}
        self.modified = True

        if tool == EditTool.TEAM_A_SPAWN:
            zones = self.scenario_data.setdefault("spawn_zones", {}).setdefault("team_a", [])
            if coord in zones:
                zones.remove(coord)
            else:
                zones.append(coord)

        elif tool == EditTool.TEAM_B_SPAWN:
            zones = self.scenario_data.setdefault("spawn_zones", {}).setdefault("team_b", [])
            if coord in zones:
                zones.remove(coord)
            else:
                zones.append(coord)

        elif tool == EditTool.OBSTACLE:
            obstacles = self.scenario_data.setdefault("obstacles", [])
            existing = next((o for o in obstacles if o["q"] == q and o["r"] == r), None)
            if existing:
                obstacles.remove(existing)
            else:
                obstacles.append({"q": q, "r": r, "type": "blocked"})

        elif tool == EditTool.ERASE:
            # Remove from all zones
            for zone_key in ["team_a", "team_b"]:
                zones = self.scenario_data.get("spawn_zones", {}).get(zone_key, [])
                if coord in zones:
                    zones.remove(coord)

            # Remove obstacles
            obstacles = self.scenario_data.get("obstacles", [])
            self.scenario_data["obstacles"] = [
                o for o in obstacles if not (o["q"] == q and o["r"] == r)
            ]

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle input events."""
        # Also process any external UI events each frame when events come in
        # Note: This is safe to call frequently; it drains a small queue
        self.process_external_events()

        # Load dialog takes precedence
        if self.mode == EditorMode.LOAD_DIALOG and self.load_dialog:
            self.load_dialog.handle_event(event)

            # Check if dialog completed
            if self.load_dialog.cancelled:
                self.mode = EditorMode.EDITING
                self.load_dialog = None
            elif self.load_dialog.get_result():
                self._load_scenario(self.load_dialog.get_result())
                self.load_dialog = None
            return

        # Global keyboard shortcuts
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # ESC: exit editor
                self.action = "back"

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                self._handle_click(event.pos)

    def _handle_click(self, pos: tuple[int, int]) -> None:
        """Handle mouse click."""
        if self.mode == EditorMode.EDITING:
            # Hex grid click anywhere (no in-editor panel)
            q, r = pixel_to_hex(pos[0], pos[1])
            if self.scenario_data:
                min_q, max_q, min_r, max_r = get_grid_bounds()
                if min_q <= q <= max_q and min_r <= r <= max_r:
                    self._toggle_hex(q, r, self.current_tool)

    def process_external_events(self) -> None:
        """Consume events from external tool window and apply them."""
        if not self.event_bus:
            return

        for evt in self.event_bus.drain_events():
            try:
                if evt.type == EV_TOOL_SELECT:
                    payload = evt.payload or {}
                    tool_key = str(payload.get("tool", "")).lower()
                    mapping = {
                        "team_a": EditTool.TEAM_A_SPAWN,
                        "team_b": EditTool.TEAM_B_SPAWN,
                        "obstacle": EditTool.OBSTACLE,
                        "erase": EditTool.ERASE,
                    }
                    new_tool = mapping.get(tool_key)
                    if new_tool is not None:
                        self.current_tool = new_tool
                elif evt.type == EV_SAVE:
                    self._save_scenario()
                elif evt.type == EV_LOAD:
                    # Open load dialog over current view
                    scenarios = self.context.scenario_repo.list_scenarios()
                    self.load_dialog = ScenarioListDialog(
                        self.screen_width, self.screen_height, scenarios
                    )
                    self.mode = EditorMode.LOAD_DIALOG
                elif evt.type == EV_CLOSE:
                    self.action = "back"
                elif evt.type == EV_NEW:
                    self._create_new_scenario()
                elif evt.type == EV_SET_NAME:
                    payload = evt.payload or {}
                    new_name = str(payload.get("name", "")).strip()
                    if new_name and self.scenario_data:
                        self.scenario_data["name"] = new_name
                        self.modified = True
                        # Push update
                        if self.event_bus:
                            try:
                                from infrastructure.events.editor_events import (
                                    EV_STATE_UPDATE,
                                    EditorEvent,
                                )

                                self.event_bus.publish_to_ui(
                                    EditorEvent(EV_STATE_UPDATE, {"scenario_name": new_name})
                                )
                            except Exception:
                                pass
                elif evt.type == EV_SET_DESCRIPTION:
                    payload = evt.payload or {}
                    new_desc = str(payload.get("description", "")).strip()
                    if self.scenario_data:
                        self.scenario_data["description"] = new_desc
                        self.modified = True
                        # Push update
                        if self.event_bus:
                            try:
                                from infrastructure.events.editor_events import (
                                    EV_STATE_UPDATE,
                                    EditorEvent,
                                )

                                self.event_bus.publish_to_ui(
                                    EditorEvent(EV_STATE_UPDATE, {"description": new_desc})
                                )
                            except Exception:
                                pass
                elif evt.type == EV_SET_BACKGROUND:
                    payload = evt.payload or {}
                    bg = payload.get("background")
                    if self.scenario_data is not None:
                        if bg:
                            self.scenario_data["background"] = bg
                        else:
                            self.scenario_data["background"] = None
                        self.modified = True
                        self._load_background()
                        # Push update
                        if self.event_bus:
                            try:
                                from infrastructure.events.editor_events import (
                                    EV_STATE_UPDATE,
                                    EditorEvent,
                                )

                                self.event_bus.publish_to_ui(
                                    EditorEvent(
                                        EV_STATE_UPDATE,
                                        {"background": self.scenario_data.get("background")},
                                    )
                                )
                            except Exception:
                                pass
            except Exception as e:
                logger.warning(f"Failed to process external editor event {evt}: {e}")

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the editor screen."""
        surface.fill(self.color_bg)

        if self.mode == EditorMode.LOAD_DIALOG:
            # Dim screen and draw dialog
            if self.load_dialog:
                dim = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
                dim.fill((0, 0, 0, 140))
                surface.blit(dim, (0, 0))
                self.load_dialog.draw(surface)
        elif self.mode == EditorMode.EDITING:
            self._draw_editor(surface)

    def _draw_editor(self, surface: pygame.Surface) -> None:
        """Draw main editor interface."""
        if not self.scenario_data:
            # Empty state: guide to use external tool
            title = self.font_large.render("Scenario Editor", True, self.color_highlight)
            surface.blit(title, title.get_rect(center=(self.screen_width // 2, 100)))
            prompt = self.font_normal.render(
                "Use external tool: New or Load", True, self.color_text
            )
            surface.blit(prompt, prompt.get_rect(center=(self.screen_width // 2, 180)))
            inst = self.font_small.render("ESC: Exit", True, (180, 180, 200))
            surface.blit(
                inst, inst.get_rect(center=(self.screen_width // 2, self.screen_height - 40))
            )
            return

        # Draw cached background
        if self.background_cache:
            surface.blit(self.background_cache, (0, 0))

        # Minimal HUD
        title_text = self.scenario_data.get("name", "Scenario")
        if self.modified:
            title_text += " *"
        title = self.font_normal.render(title_text, True, self.color_highlight)
        surface.blit(title, (20, 20))

        tool_text = self.font_small.render(
            f"Tool: {self.current_tool.value}", True, self.color_text
        )
        surface.blit(tool_text, (20, 60))

        stats_lines = [
            f"Team A: {len(self.scenario_data.get('spawn_zones', {}).get('team_a', []))}",
            f"Team B: {len(self.scenario_data.get('spawn_zones', {}).get('team_b', []))}",
            f"Obstacles: {len(self.scenario_data.get('obstacles', []))}",
        ]
        y = 90
        for s in stats_lines:
            txt = self.font_small.render(s, True, self.color_text)
            surface.blit(txt, (20, y))
            y += 24

        inst = self.font_small.render(
            "Click hexes to edit | Use external panel for actions | ESC to exit",
            True,
            (180, 180, 200),
        )
        surface.blit(inst, inst.get_rect(center=(self.screen_width // 2, self.screen_height - 20)))

        # Hex grid component
        self.hex_grid.draw(surface, self.scenario_data)

    # Legacy button drawing removed

    def is_done(self) -> bool:
        """Check if editor should exit."""
        return self.action == "back"

    def get_action(self) -> str | None:
        """Get action for application layer."""
        return self.action
