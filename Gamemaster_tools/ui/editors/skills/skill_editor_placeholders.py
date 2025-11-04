"""
Placeholder Skill Editor Tab
Manages placeholder skill resolutions through a visual interface
"""

import os

# Import placeholder manager
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from utils.placeholder_manager import PlaceholderManager


class PlaceholderEditorTab:
    """
    Manages the placeholder resolutions tab in the skill editor.
    Allows viewing and editing which skills can replace placeholders.
    """

    def __init__(self, tab_widget, parent_editor):
        """
        Initialize the placeholder editor tab

        Args:
            tab_widget: QTabWidget to add the tab to
            parent_editor: Reference to parent SkillEditorQt instance
        """
        self.tab_widget = tab_widget
        self.parent = parent_editor
        self.placeholder_mgr = PlaceholderManager()

        # Widget references
        self.placeholder_list = None
        self.resolution_list = None
        self.available_skills_combo = None
        self.category_edit = None
        self.notes_edit = None
        self.current_placeholder = None

        # Create the tab
        self.create_tab()

    def create_tab(self):
        """Create the placeholder management tab"""
        tab = QWidget()
        main_layout = QVBoxLayout()
        tab.setLayout(main_layout)

        # Header
        header = QLabel("Helyfoglaló képzettségek kezelése")
        header_font = QFont()
        header_font.setPointSize(11)
        header_font.setBold(True)
        header.setFont(header_font)
        main_layout.addWidget(header)

        # Info text
        info = QLabel(
            "A helyfoglaló képzettségek (pl. 'Fegyverhasználat (Választható)') olyan speciális képzettségek, "
            "amelyek karakteralkotáskor konkrét képzettségekre cserélhetők. Itt állíthatod be, hogy melyik "
            "helyfoglaló milyen képzettségekre váltható."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #888; margin: 10px 0;")
        main_layout.addWidget(info)

        # Horizontal splitter: left = placeholder list, right = resolutions
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel: Placeholder list
        left_panel = self.create_placeholder_list_panel()
        splitter.addWidget(left_panel)

        # Right panel: Resolution editor
        right_panel = self.create_resolution_editor_panel()
        splitter.addWidget(right_panel)

        splitter.setSizes([400, 800])
        main_layout.addWidget(splitter, stretch=1)

        # Add to tab widget
        self.tab_widget.addTab(tab, "Helyfoglalók")

        # Load initial data
        self.load_placeholders()
        # Ensure available skills are populated so search/select works even before picking a placeholder
        self.populate_available_skills()

    def create_placeholder_list_panel(self):
        """Create the left panel with placeholder list"""
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)

        # Label
        label = QLabel("Helyfoglaló képzettségek:")
        label_font = QFont()
        label_font.setBold(True)
        label.setFont(label_font)
        layout.addWidget(label)

        # List of placeholders
        self.placeholder_list = QListWidget()
        self.placeholder_list.currentItemChanged.connect(self.on_placeholder_selected)
        layout.addWidget(self.placeholder_list)

        # Refresh button
        btn_refresh = QPushButton("🔄 Frissítés")
        btn_refresh.clicked.connect(self.load_placeholders)
        layout.addWidget(btn_refresh)

        return panel

    def create_resolution_editor_panel(self):
        """Create the right panel with resolution editor"""
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)

        # Current placeholder info
        self.placeholder_info_label = QLabel("Válassz egy helyfoglalót a bal oldalról")
        self.placeholder_info_label.setStyleSheet(
            "font-weight: bold; font-size: 11pt; margin-bottom: 10px;"
        )
        layout.addWidget(self.placeholder_info_label)

        # Resolutions list
        res_label = QLabel("Elérhető feloldások:")
        layout.addWidget(res_label)

        self.resolution_list = QListWidget()
        layout.addWidget(self.resolution_list, stretch=1)

        # Add resolution form
        add_form = QWidget()
        add_layout = QFormLayout()
        add_form.setLayout(add_layout)

        # Skill selector
        self.available_skills_combo = QComboBox()
        self.available_skills_combo.setEditable(True)
        add_layout.addRow("Képzettség:", self.available_skills_combo)

        # Category
        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText("pl. light_medium, heavy, ranged")
        add_layout.addRow("Kategória:", self.category_edit)

        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Opcionális megjegyzések...")
        self.notes_edit.setMaximumHeight(60)
        add_layout.addRow("Megjegyzés:", self.notes_edit)

        layout.addWidget(add_form)

        # Buttons
        btn_layout = QHBoxLayout()

        btn_add = QPushButton("➕ Feloldás hozzáadása")
        btn_add.clicked.connect(self.add_resolution)
        btn_layout.addWidget(btn_add)

        btn_remove = QPushButton("➖ Feloldás törlése")
        btn_remove.clicked.connect(self.remove_resolution)
        btn_layout.addWidget(btn_remove)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return panel

    def load_placeholders(self):
        """Load all placeholder skills into the list"""
        if self.placeholder_list is None:
            return
        self.placeholder_list.clear()
        placeholders = self.placeholder_mgr.get_all_placeholders()

        for ph in placeholders:
            display = f"{ph['name']}"
            if ph["parameter"]:
                display += f" ({ph['parameter']})"

            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, ph["id"])
            self.placeholder_list.addItem(item)

        if not placeholders:
            item = QListWidgetItem("Nincs helyfoglaló képzettség az adatbázisban")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.placeholder_list.addItem(item)

    def on_placeholder_selected(self, current, previous):
        """Handle placeholder selection"""
        if not current:
            return

        placeholder_id = current.data(Qt.ItemDataRole.UserRole)
        if not placeholder_id:
            return

        self.current_placeholder = placeholder_id

        # Update info label
        self.placeholder_info_label.setText(f"Feloldások ehhez: {current.text()}")

        # Load resolutions
        self.load_resolutions(placeholder_id)

        # Populate available skills
        self.populate_available_skills()

    def load_resolutions(self, placeholder_id):
        """Load resolutions for the selected placeholder"""
        if self.resolution_list is None:
            return
        self.resolution_list.clear()
        resolutions = self.placeholder_mgr.get_resolutions(placeholder_id)

        for res in resolutions:
            display = f"{res['skill_name']}"
            if res["parameter"]:
                display += f" ({res['parameter']})"
            if res["resolution_category"]:
                display += f" [{res['resolution_category']}]"
            if res["notes"]:
                display += f" - {res['notes']}"

            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, res["target_skill_id"])
            item.setData(int(Qt.ItemDataRole.UserRole) + 1, res["resolution_category"])
            item.setData(int(Qt.ItemDataRole.UserRole) + 2, res["notes"])
            self.resolution_list.addItem(item)

        if not resolutions:
            item = QListWidgetItem("Nincs feloldás megadva - add hozzá alább!")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.resolution_list.addItem(item)

    def populate_available_skills(self):
        """Populate combo with all non-placeholder skills"""
        if self.available_skills_combo is None:
            return
        self.available_skills_combo.clear()

        # Get all skills from parent editor
        if hasattr(self.parent, "all_skills"):
            for skill in self.parent.all_skills:
                # Skip placeholders
                if skill.get("placeholder", 0) == 1:
                    continue

                display = skill["name"]
                if skill.get("parameter"):
                    display += f" ({skill['parameter']})"

                self.available_skills_combo.addItem(display, skill["id"])

    def suggest_skill_selection(self, skill_id: str | None, display_text: str | None = None):
        """Suggest/select a skill in the available skills combo based on a left-tree selection.

        If the skill_id exists in the combo's data, selects it. Otherwise, if display_text is provided,
        sets the editable text so the user sees it in the search bar.
        """
        if self.available_skills_combo is None:
            return
        # Populate if empty to maximize chance of a match
        if self.available_skills_combo.count() == 0:
            self.populate_available_skills()

        if skill_id:
            idx = self.available_skills_combo.findData(skill_id)
            if idx != -1:
                self.available_skills_combo.setCurrentIndex(idx)
                return
        # Fallback: set search text for visibility
        if display_text:
            # Only works when combo is editable (it is)
            self.available_skills_combo.setEditText(display_text)

    def add_resolution(self):
        """Add a new resolution for the current placeholder"""
        if not self.current_placeholder:
            QMessageBox.warning(
                self.tab_widget, "Nincs kiválasztva", "Válassz ki egy helyfoglalót!"
            )
            return

        if (
            self.available_skills_combo is None
            or self.category_edit is None
            or self.notes_edit is None
        ):
            return

        # Get selected skill
        idx = self.available_skills_combo.currentIndex()
        if idx < 0:
            QMessageBox.warning(self.tab_widget, "Nincs képzettség", "Válassz ki egy képzettséget!")
            return

        target_skill_id = self.available_skills_combo.currentData()
        category_text = self.category_edit.text().strip()
        category = category_text if category_text else None
        notes_text = self.notes_edit.toPlainText().strip()
        notes = notes_text if notes_text else None

        try:
            self.placeholder_mgr.add_resolution(
                self.current_placeholder, target_skill_id, category, notes
            )

            # Reload resolutions
            self.load_resolutions(self.current_placeholder)

            # Clear form
            if self.category_edit is not None:
                self.category_edit.clear()
            if self.notes_edit is not None:
                self.notes_edit.clear()

            QMessageBox.information(self.tab_widget, "Siker", "Feloldás hozzáadva!")

        except (ValueError, KeyError, TypeError) as e:
            QMessageBox.critical(
                self.tab_widget, "Hiba", f"Nem sikerült hozzáadni a feloldást:\n{e}"
            )

    def remove_resolution(self):
        """Remove the selected resolution"""
        if not self.current_placeholder:
            QMessageBox.warning(
                self.tab_widget, "Nincs kiválasztva", "Válassz ki egy helyfoglalót!"
            )
            return

        if self.resolution_list is None:
            return

        current_item = self.resolution_list.currentItem()
        if not current_item:
            QMessageBox.warning(
                self.tab_widget,
                "Nincs feloldás kiválasztva",
                "Válassz ki egy feloldást a törléshez!",
            )
            return

        target_skill_id = current_item.data(Qt.ItemDataRole.UserRole)
        if not target_skill_id:
            return

        # Confirm deletion
        reply = QMessageBox.question(
            self.tab_widget,
            "Törlés megerősítése",
            f"Biztosan törölni szeretnéd ezt a feloldást?\n\n{current_item.text()}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.placeholder_mgr.remove_resolution(self.current_placeholder, target_skill_id)
                self.load_resolutions(self.current_placeholder)
                QMessageBox.information(self.tab_widget, "Siker", "Feloldás törölve!")
            except (ValueError, KeyError) as e:
                QMessageBox.critical(
                    self.tab_widget, "Hiba", f"Nem sikerült törölni a feloldást:\n{e}"
                )
