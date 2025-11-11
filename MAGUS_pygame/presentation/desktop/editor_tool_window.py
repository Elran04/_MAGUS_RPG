from __future__ import annotations

import sys

from config import BACKGROUND_SPRITES_DIR
from infrastructure.events.editor_events import (
    EV_CLOSE,
    EV_LOAD,
    EV_NEW,
    EV_SAVE,
    EV_SET_BACKGROUND,
    EV_SET_DESCRIPTION,
    EV_SET_NAME,
    EV_STATE_UPDATE,
    EV_TOOL_SELECT,
    EditorEvent,
)
from infrastructure.events.event_bus import EditorEventBus
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# Shutdown signaling from game loop
_QUIT_EVENT = None  # Will be set per-process
# Event bus instance (injected)
_EVENT_BUS: EditorEventBus | None = None


class ToolWindow(QWidget):
    def __init__(self, event_bus: EditorEventBus) -> None:
        super().__init__()
        self.event_bus = event_bus
        self.setWindowTitle("Scenario Editor Tools")
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.setMinimumWidth(240)

        self.status_label = QLabel("Ready")
        self.scenario_label = QLabel("<no scenario>")
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Scenario Name")
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("Description")

        # Tool buttons
        self.btn_team_a = QPushButton("Team A Spawn")
        self.btn_team_b = QPushButton("Team B Spawn")
        self.btn_obstacle = QPushButton("Obstacle")
        self.btn_erase = QPushButton("Erase")

        # Actions
        self.btn_new = QPushButton("New")
        self.btn_save = QPushButton("Save")
        self.btn_load = QPushButton("Load")
        self.btn_close = QPushButton("Close")

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Scenario:"))
        layout.addWidget(self.scenario_label)
        layout.addWidget(QLabel("Name:"))
        layout.addWidget(self.name_edit)
        layout.addWidget(QLabel("Description:"))
        layout.addWidget(self.desc_edit)
        layout.addSpacing(10)
        layout.addWidget(QLabel("Tool:"))
        layout.addWidget(self.btn_team_a)
        layout.addWidget(self.btn_team_b)
        layout.addWidget(self.btn_obstacle)
        layout.addWidget(self.btn_erase)
        layout.addSpacing(10)

        row1 = QHBoxLayout()
        row1.addWidget(self.btn_new)
        row1.addWidget(self.btn_load)
        layout.addLayout(row1)
        layout.addSpacing(10)

        # Background list
        layout.addWidget(QLabel("Backgrounds:"))
        self.bg_list = QListWidget()
        layout.addWidget(self.bg_list)
        self.btn_refresh_bg = QPushButton("Refresh Backgrounds")
        self.btn_clear_bg = QPushButton("Clear Background")
        bg_row = QHBoxLayout()
        bg_row.addWidget(self.btn_refresh_bg)
        bg_row.addWidget(self.btn_clear_bg)
        layout.addLayout(bg_row)
        row2 = QHBoxLayout()
        row2.addWidget(self.btn_save)
        row2.addWidget(self.btn_close)
        layout.addLayout(row2)
        layout.addSpacing(10)
        layout.addWidget(self.status_label)
        self.setLayout(layout)

        # Wire clicks -> publish events
        self.btn_team_a.clicked.connect(
            lambda: self.event_bus.publish(EditorEvent(EV_TOOL_SELECT, {"tool": "team_a"}))
        )
        self.btn_team_b.clicked.connect(
            lambda: self.event_bus.publish(EditorEvent(EV_TOOL_SELECT, {"tool": "team_b"}))
        )
        self.btn_obstacle.clicked.connect(
            lambda: self.event_bus.publish(EditorEvent(EV_TOOL_SELECT, {"tool": "obstacle"}))
        )
        self.btn_erase.clicked.connect(
            lambda: self.event_bus.publish(EditorEvent(EV_TOOL_SELECT, {"tool": "erase"}))
        )
        self.btn_new.clicked.connect(lambda: self.event_bus.publish(EditorEvent(EV_NEW)))
        self.btn_save.clicked.connect(lambda: self.event_bus.publish(EditorEvent(EV_SAVE)))
        self.btn_load.clicked.connect(lambda: self.event_bus.publish(EditorEvent(EV_LOAD)))
        self.btn_close.clicked.connect(lambda: self.event_bus.publish(EditorEvent(EV_CLOSE)))
        self.name_edit.editingFinished.connect(self._emit_name_change)
        self.desc_edit.editingFinished.connect(self._emit_description_change)
        self.btn_refresh_bg.clicked.connect(self._load_background_list)
        self.btn_clear_bg.clicked.connect(
            lambda: self.event_bus.publish(EditorEvent(EV_SET_BACKGROUND, {"background": None}))
        )
        self.bg_list.itemClicked.connect(self._background_selected)

        # Initial population
        self._load_background_list()

        # Poll for state updates from game (consume game->UI events)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._poll_updates)
        self.timer.start(100)

    def _poll_updates(self) -> None:
        global _QUIT_EVENT
        if _QUIT_EVENT and _QUIT_EVENT.is_set():
            app = QApplication.instance()
            if app is not None:
                app.quit()
            return
        # Drain game->UI events
        for evt in self.event_bus.drain_ui_events():
            if evt.type == EV_STATE_UPDATE:
                payload = evt.payload or {}
                scen_name = payload.get("scenario_name")
                if scen_name:
                    self.scenario_label.setText(scen_name)
                    if not self.name_edit.hasFocus():
                        self.name_edit.setText(scen_name)
                desc = payload.get("description")
                if desc is not None and not self.desc_edit.hasFocus():
                    self.desc_edit.setText(desc)
                bg = payload.get("background")
                if bg is not None:
                    # Highlight selected background
                    self._highlight_background(bg)
        # no return value needed

    def set_status(self, text: str) -> None:
        self.status_label.setText(text)

    def set_scenario(self, name: str) -> None:
        self.scenario_label.setText(name)
        if name:
            self.name_edit.setText(name)

    def _emit_name_change(self) -> None:
        text = self.name_edit.text().strip()
        if text:
            self.event_bus.publish(EditorEvent(EV_SET_NAME, {"name": text}))

    def _emit_description_change(self) -> None:
        text = self.desc_edit.text().strip()
        if text:
            self.event_bus.publish(EditorEvent(EV_SET_DESCRIPTION, {"description": text}))

    def _load_background_list(self) -> None:
        from pathlib import Path

        self.bg_list.clear()
        none_item = QListWidgetItem("<None>")
        none_item.setData(Qt.UserRole, None)
        self.bg_list.addItem(none_item)
        try:
            bg_dir = Path(BACKGROUND_SPRITES_DIR)
            for p in sorted(bg_dir.glob("*")):
                if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp"}:
                    item = QListWidgetItem(p.name)
                    item.setData(Qt.UserRole, p.name)
                    self.bg_list.addItem(item)
        except Exception as e:
            self.set_status(f"BG load error: {e}")

    def _background_selected(self, item: QListWidgetItem) -> None:
        bg = item.data(Qt.UserRole)
        self.event_bus.publish(EditorEvent(EV_SET_BACKGROUND, {"background": bg}))

    def _highlight_background(self, filename: str | None) -> None:
        # Select matching item in list
        for i in range(self.bg_list.count()):
            it = self.bg_list.item(i)
            if it.data(Qt.UserRole) == filename:
                self.bg_list.setCurrentItem(it)
                break
        if filename is None:
            # Select <None>
            self.bg_list.setCurrentRow(0)


def run_tool_window(quit_event, ui_to_game_queue, game_to_ui_queue) -> None:
    """Run the tool window in a separate process.

    Args:
        quit_event: multiprocessing.Event to signal shutdown
        ui_to_game_queue: multiprocessing.Queue for sending events to game
        game_to_ui_queue: multiprocessing.Queue for receiving events from game
    """
    global _QUIT_EVENT
    _QUIT_EVENT = quit_event

    # Create event bus instance for UI process
    event_bus = EditorEventBus(ui_to_game_queue, game_to_ui_queue)

    app = QApplication.instance() or QApplication(sys.argv)
    w = ToolWindow(event_bus)
    w.move(50, 50)  # initial position; user can drag it anywhere
    w.show()
    app.exec()
