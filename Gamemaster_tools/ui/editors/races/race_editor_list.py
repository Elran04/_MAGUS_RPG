"""
Race Editor List Panel
Handles the race list panel on the left side
"""

from engine.race_manager import RaceManager
from PySide6 import QtCore, QtWidgets
from PySide6.QtGui import QFont


class RaceListPanel:
    """Manages the race list panel"""

    def __init__(self, parent, on_selection_changed):
        """
        Initialize the race list panel

        Args:
            parent: Parent widget (splitter)
            on_selection_changed: Callback when selection changes (receives race_id)
        """
        self.on_selection_changed = on_selection_changed
        self.race_manager: RaceManager | None = None

        self.list_widget = QtWidgets.QWidget()
        self.race_list = QtWidgets.QListWidget()
        self.btn_new = QtWidgets.QPushButton("Új faj")
        self.btn_delete = QtWidgets.QPushButton("Törlés")

        self.create_ui(parent)

    def create_ui(self, parent):
        """Create the race list panel UI"""
        layout = QtWidgets.QVBoxLayout(self.list_widget)
        self.list_widget.setMaximumWidth(250)

        # Header
        header_label = QtWidgets.QLabel("<b>Fajok listája</b>")
        header_font = QFont()
        header_font.setPointSize(11)
        header_font.setBold(True)
        header_label.setFont(header_font)
        layout.addWidget(header_label)

        # List widget
        self.race_list.itemClicked.connect(self.on_race_selected)
        layout.addWidget(self.race_list)

        # Buttons
        layout.addWidget(self.btn_new)
        layout.addWidget(self.btn_delete)

        parent.addWidget(self.list_widget)

    def populate(self, race_manager: RaceManager):
        """
        Populate the list with races

        Args:
            race_manager: RaceManager instance
        """
        self.race_manager = race_manager
        self.race_list.clear()

        for race in race_manager.get_all_races():
            item = QtWidgets.QListWidgetItem(race.name)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, race.id)
            self.race_list.addItem(item)

        # Auto-select first race if available
        if self.race_list.count() > 0:
            self.race_list.setCurrentRow(0)
            first_item = self.race_list.item(0)
            if first_item:
                self.on_race_selected(first_item)

    def on_race_selected(self, item: QtWidgets.QListWidgetItem):
        """Handle race selection"""
        race_id = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if self.on_selection_changed:
            self.on_selection_changed(race_id)

    def refresh(self):
        """Refresh the race list"""
        if self.race_manager:
            self.populate(self.race_manager)
