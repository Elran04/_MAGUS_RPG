"""
M.A.G.U.S. Race Editor - Faj szerkesztő UI
Modern modular interface for M.A.G.U.S. race management
Refactored into modular components for better maintainability
"""

import os
import sys
from pathlib import Path

from PySide6 import QtCore, QtWidgets

# Add Gamemaster_tools to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from engine.race_manager import RaceManager
from config.paths import DATA_DIR
from ui.editors.races.race_editor_actions import RaceEditorActions
from ui.editors.races.race_editor_list import RaceListPanel
from ui.editors.races.race_editor_tabs import RaceEditorTabs
from utils.log.logger import get_logger

logger = get_logger(__name__)


class RaceEditorQt(QtWidgets.QMainWindow):
    """M.A.G.U.S. Faj szerkesztő - Modern modular interface"""

    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info("Race Editor inicializálása")

        self.setWindowTitle("M.A.G.U.S. - Faj Szerkesztő")
        self.setMinimumSize(1200, 800)

        # Standard window controls (min/max/close)
        self.setWindowFlags(
            QtCore.Qt.WindowType.Window
            | QtCore.Qt.WindowType.WindowMinimizeButtonHint
            | QtCore.Qt.WindowType.WindowMaximizeButtonHint
            | QtCore.Qt.WindowType.WindowCloseButtonHint
        )

        # Data manager (use centralized data directory)
        self.race_manager = RaceManager(DATA_DIR)
        self.race_manager.load_all()

        # Initialize component handlers
        self.race_list_panel: RaceListPanel | None = None
        self.tabs: RaceEditorTabs | None = None
        self.editor_actions: RaceEditorActions | None = None

        # Initialize UI
        self.init_ui()

        # Load race list
        assert self.race_list_panel is not None
        self.race_list_panel.populate(self.race_manager)

    def init_ui(self):
        """UI inicializálás"""
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)

        root = QtWidgets.QVBoxLayout(central)

        # Splitter with race list (left) and editor (right)
        splitter = QtWidgets.QSplitter()
        splitter.setOrientation(QtCore.Qt.Orientation.Horizontal)
        root.addWidget(splitter, stretch=1)

        # Initialize actions handler
        self.editor_actions = RaceEditorActions(self)

        # Left panel - Race list
        self.race_list_panel = RaceListPanel(splitter, on_selection_changed=self.on_race_selected)

        # Right panel - Tabbed editor
        self.create_editor_panel(splitter)

        # Set initial splitter sizes: 20% list, 80% tabs
        splitter.setSizes([200, 1000])

        # Bottom action bar
        actions_layout = QtWidgets.QHBoxLayout()
        self.btn_save = QtWidgets.QPushButton("💾 Mentés")
        self.btn_save.setMinimumHeight(40)
        actions_layout.addStretch()
        actions_layout.addWidget(self.btn_save)
        root.addLayout(actions_layout)

        # Connect buttons
        self.race_list_panel.btn_new.clicked.connect(self.editor_actions.create_new_race)
        self.race_list_panel.btn_delete.clicked.connect(self.editor_actions.delete_race)
        self.btn_save.clicked.connect(self.editor_actions.save_race)

    def create_editor_panel(self, parent):
        """Create the tabbed editor panel"""
        editor_widget = QtWidgets.QWidget()
        editor_layout = QtWidgets.QVBoxLayout(editor_widget)

        # Név és ID
        form = QtWidgets.QFormLayout()
        self.tabs = RaceEditorTabs(self.race_manager)
        self.tabs.txt_id.setReadOnly(True)  # ID nem szerkeszthető
        form.addRow("ID:", self.tabs.txt_id)
        form.addRow("Név:", self.tabs.txt_name)
        editor_layout.addLayout(form)

        # Tab widget
        editor_layout.addWidget(self.tabs.tab_widget)

        parent.addWidget(editor_widget)

        # Connect skill actions
        self.tabs.btn_add_skill.clicked.connect(self.editor_actions.add_racial_skill)
        self.tabs.btn_edit_skill.clicked.connect(self.editor_actions.edit_racial_skill)
        self.tabs.btn_delete_skill.clicked.connect(self.editor_actions.delete_racial_skill)
        self.tabs.btn_add_forbidden.clicked.connect(self.editor_actions.add_forbidden_skill)
        self.tabs.btn_remove_forbidden.clicked.connect(self.editor_actions.remove_forbidden_skill)

        # Connect special ability actions
        self.tabs.list_available_abilities.itemClicked.connect(self.tabs.show_ability_details)
        self.tabs.list_race_abilities.itemClicked.connect(self.tabs.show_ability_details)

        # Connect ability buttons
        btn_add_ability = QtWidgets.QPushButton("→ Hozzáad")
        btn_add_ability.clicked.connect(self.editor_actions.add_special_ability)
        btn_remove_ability = QtWidgets.QPushButton("← Eltávolít")
        btn_remove_ability.clicked.connect(self.editor_actions.remove_special_ability)

        # Add these buttons to the special abilities tab
        # Find the tab and add buttons
        abilities_tab = self.tabs.tab_widget.widget(2)  # Index 2 = Special abilities tab
        if abilities_tab:
            # Find the splitter in the tab
            for child in abilities_tab.findChildren(QtWidgets.QSplitter):
                # Add buttons to left and right widgets
                left_widget = child.widget(0)
                right_widget = child.widget(1)
                if left_widget:
                    left_widget.layout().addWidget(btn_add_ability)
                if right_widget:
                    right_widget.layout().addWidget(btn_remove_ability)
                break

    def on_race_selected(self, race_id: str):
        """Faj kiválasztva -> betöltés"""
        race = self.race_manager.get_race(race_id)
        if race and self.tabs:
            self.tabs.load_race(race)
            logger.info(f"Faj betöltve: {race.name}")


def main():
    """Main entry point"""
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Apply dark mode if available
    try:
        from utils.ui.dark_mode import apply_dark_mode

        apply_dark_mode(app)
    except ImportError:
        pass

    window = RaceEditorQt()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
