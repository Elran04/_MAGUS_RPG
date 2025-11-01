"""
Class Editor - PySide6 version with dark mode support
Modern tabbed interface for M.A.G.U.S. class management
Refactored into modular components for better maintainability
"""

import os
import sys

from PySide6 import QtCore, QtWidgets

# Add grandparent directory to path (Gamemaster_tools)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from ui.classes.class_editor_actions import ClassEditorActions
from ui.classes.class_editor_list import ClassListPanel
from ui.classes.class_editor_tabs import ClassEditorTabs
from utils.class_db_manager import ClassDBManager


class ClassEditorQt(QtWidgets.QDialog):
    """Modern class editor with tabbed interface"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kaszt szerkesztő")
        self.resize(1500, 700)

        # Standard window controls (min/max/close)
        self.setWindowFlags(
            QtCore.Qt.WindowType.Window
            | QtCore.Qt.WindowType.WindowMinimizeButtonHint
            | QtCore.Qt.WindowType.WindowMaximizeButtonHint
            | QtCore.Qt.WindowType.WindowCloseButtonHint
        )

        # Initialize class database manager
        self.class_db = ClassDBManager()

        # Initialize actions handler early (non-optional for type checkers)
        self.editor_actions = ClassEditorActions(self)

        # Ensure required tables exist (safe no-ops if already exist)
        try:
            self.class_db.ensure_specialisations_table()
        except Exception:
            pass
        try:
            self.class_db.ensure_starting_equipment_table()
        except Exception:
            pass
        try:
            self.class_db.ensure_classes_description_column()
        except Exception:
            pass

        # Current selection state
        self.current_class_id = None
        self.current_spec_id = None

        # Initialize component handlers
        self.class_list_panel = None
        self.tabs = None

        # Initialize UI
        self.init_ui()

        # Load tree
        assert self.class_list_panel is not None
        self.class_list_panel.populate(self.class_db)

    def init_ui(self):
        """Initialize the user interface"""
        root = QtWidgets.QVBoxLayout(self)

        # Splitter with tree (left) and editor (right)
        splitter = QtWidgets.QSplitter()
        splitter.setOrientation(QtCore.Qt.Orientation.Horizontal)
        root.addWidget(splitter, stretch=1)

        # Actions handler already initialized in __init__

        # Left panel - Class/spec tree
        self.class_list_panel = ClassListPanel(
            splitter, on_selection_changed=self.on_selection_changed
        )

        # Right panel - Tabbed editor
        self.create_editor_panel(splitter)

        # Set initial splitter sizes: 30% tree, 70% tabs
        splitter.setSizes([200, 800])

        # Bottom action bar
        actions_layout = QtWidgets.QHBoxLayout()
        self.btn_add_spec = QtWidgets.QPushButton("Specializáció hozzáadása")
        self.btn_del_spec = QtWidgets.QPushButton("Specializáció törlése")
        self.btn_save_all = QtWidgets.QPushButton("Mentés")
        actions_layout.addWidget(self.btn_add_spec)
        actions_layout.addWidget(self.btn_del_spec)
        actions_layout.addStretch()
        actions_layout.addWidget(self.btn_save_all)
        root.addLayout(actions_layout)

        # Connect action bar signals
        self.btn_save_all.clicked.connect(self.editor_actions.save_current)
        self.btn_add_spec.clicked.connect(self.editor_actions.add_specialisation)
        self.btn_del_spec.clicked.connect(self.editor_actions.delete_specialisation)

    def create_editor_panel(self, parent):
        """Create the editor panel on the right"""
        right = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right)

        # Create tab widget
        tab_widget = QtWidgets.QTabWidget()
        right_layout.addWidget(tab_widget)

        # Initialize tabs
        self.tabs = ClassEditorTabs(tab_widget, self)

        parent.addWidget(right)

    def on_selection_changed(self, class_id, spec_id):
        """Handle class/spec selection from tree"""
        self.current_class_id = class_id
        self.current_spec_id = spec_id
        self.editor_actions.load_details()

    # Delegate equipment actions to actions module
    def add_currency_row(self):
        """Add currency row - delegates to actions"""
        self.editor_actions.add_currency_row()

    def add_item_row(self):
        """Add item row - delegates to actions"""
        self.editor_actions.add_item_row()

    def delete_equipment_row(self):
        """Delete equipment row - delegates to actions"""
        self.editor_actions.delete_equipment_row()

    def save_description_file(self):
        """Save description file - delegates to actions"""
        self.editor_actions.save_description_file()

    def open_description_file(self):
        """Open description file - delegates to actions"""
        self.editor_actions.open_description_file()


if __name__ == "__main__":
    from utils.dark_mode import apply_dark_mode

    app = QtWidgets.QApplication(sys.argv)
    apply_dark_mode(app)

    editor = ClassEditorQt()
    editor.exec()
