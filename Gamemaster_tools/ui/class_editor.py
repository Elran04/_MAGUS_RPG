from PySide6 import QtWidgets, QtCore
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.class_db_manager import ClassDBManager

class ClassEditorQt(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kaszt szerkesztő")
        self.resize(700, 600)
        # Standard ablakvezérlők (min/max/close)
        self.setWindowFlags(QtCore.Qt.WindowType.Window | QtCore.Qt.WindowType.WindowMinimizeButtonHint | QtCore.Qt.WindowType.WindowMaximizeButtonHint | QtCore.Qt.WindowType.WindowCloseButtonHint)
        self.class_db = ClassDBManager()
        self.init_ui()
        self.load_classes()
        # Ha van kaszt, automatikusan megjelenítjük az első kaszt részleteit
        if self.class_items:
            self.display_class_details(self.class_list.currentItem(), None)

    def init_ui(self):
        self.layout = QtWidgets.QVBoxLayout(self)
        self.class_list = QtWidgets.QListWidget()
        self.layout.addWidget(QtWidgets.QLabel("Kasztok:"))
        self.layout.addWidget(self.class_list)
        self.details_group = QtWidgets.QGroupBox("Kaszt adatok")
        self.details_layout = QtWidgets.QFormLayout(self.details_group)
        self.layout.addWidget(self.details_group)
        self.save_btn = QtWidgets.QPushButton("Mentés")
        self.layout.addWidget(self.save_btn)
        self.class_list.currentItemChanged.connect(self.display_class_details)
        self.save_btn.clicked.connect(self.save_class)

    def load_classes(self):
        self.class_list.clear()
        # Sort by ID (not alphabetically)
        self.class_items = sorted(self.class_db.list_classes(), key=lambda x: x[0])
        for cid, name in self.class_items:
            self.class_list.addItem(f"{name} (ID: {cid})")
        if self.class_items:
            self.class_list.setCurrentRow(0)

    def display_class_details(self, current, previous):

        if not current:
            return
        idx = self.class_list.currentRow()
        class_id, name = self.class_items[idx]
        details = self.class_db.get_class_details(class_id)
        # Clear previous widgets
        while self.details_layout.count():
            item = self.details_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        # Editable name
        self.name_edit = QtWidgets.QLineEdit(details["name"])
        self.details_layout.addRow("Név:", self.name_edit)
        # Stats with double_chance
        stats_table = QtWidgets.QTableWidget(len(details["stats"]), 4)
        stats_table.setHorizontalHeaderLabels(["Tulajdonság", "Min", "Max", "Duplázási esély"])
        for i, stat_row in enumerate(details["stats"]):
            stat = stat_row[0]
            minv = stat_row[1]
            maxv = stat_row[2]
            # double_chance lehet None vagy nem 0/1, ilyenkor legyen 0
            double_chance = stat_row[3]
            if double_chance not in (0, 1):
                double_chance = 0
            stats_table.setItem(i, 0, QtWidgets.QTableWidgetItem(stat))
            stats_table.setItem(i, 1, QtWidgets.QTableWidgetItem(str(minv)))
            stats_table.setItem(i, 2, QtWidgets.QTableWidgetItem(str(maxv)))
            # Checkbox for double_chance
            chk = QtWidgets.QTableWidgetItem()
            chk.setFlags(QtCore.Qt.ItemFlag.ItemIsUserCheckable | QtCore.Qt.ItemFlag.ItemIsEnabled)
            chk.setCheckState(QtCore.Qt.CheckState.Checked if double_chance == 1 else QtCore.Qt.CheckState.Unchecked)
            stats_table.setItem(i, 3, chk)
        self.details_layout.addRow("Tulajdonságok:", stats_table)
        # Starting currency
        min_gold, max_gold = details["starting_currency"] if details["starting_currency"] else (0, 0)
        self.min_gold_edit = QtWidgets.QSpinBox()
        self.min_gold_edit.setMaximum(9999)
        self.min_gold_edit.setValue(min_gold)
        self.max_gold_edit = QtWidgets.QSpinBox()
        self.max_gold_edit.setMaximum(9999)
        self.max_gold_edit.setValue(max_gold)
        currency_layout = QtWidgets.QHBoxLayout()
        currency_layout.addWidget(QtWidgets.QLabel("Min:"))
        currency_layout.addWidget(self.min_gold_edit)
        currency_layout.addWidget(QtWidgets.QLabel("Max:"))
        currency_layout.addWidget(self.max_gold_edit)
        currency_widget = QtWidgets.QWidget()
        currency_widget.setLayout(currency_layout)
        self.details_layout.addRow("Kezdő tőke:", currency_widget)
        # Extra XP
        extra_xp = details["extra_xp"] if details["extra_xp"] else 0
        self.extra_xp_edit = QtWidgets.QSpinBox()
        self.extra_xp_edit.setMaximum(999999)
        self.extra_xp_edit.setValue(extra_xp)
        self.details_layout.addRow("Extra XP:", self.extra_xp_edit)
        # Store current class id
        self.current_class_id = class_id

    def save_class(self):
        # Save name
        new_name = self.name_edit.text()
        self.class_db.update_class_name(self.current_class_id, new_name)
        # Save starting currency
        min_gold = self.min_gold_edit.value()
        max_gold = self.max_gold_edit.value()
        with self.class_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE starting_currency SET min_gold = ?, max_gold = ? WHERE class_id = ?", (min_gold, max_gold, self.current_class_id))
            conn.commit()
        # Save extra XP
        extra_xp = self.extra_xp_edit.value()
        with self.class_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE further_level_requirements SET extra_xp = ? WHERE class_id = ?", (extra_xp, self.current_class_id))
            conn.commit()
        # Save double_chance for stats
        stats_table = None
        for i in range(self.details_layout.count()):
            item = self.details_layout.itemAt(i)
            widget = item.widget()
            if isinstance(widget, QtWidgets.QTableWidget):
                stats_table = widget
                break
        if stats_table:
            with self.class_db.get_connection() as conn:
                cursor = conn.cursor()
                for row in range(stats_table.rowCount()):
                    stat_name = stats_table.item(row, 0).text()
                    min_value = int(stats_table.item(row, 1).text())
                    max_value = int(stats_table.item(row, 2).text())
                    double_chance = 1 if stats_table.item(row, 3).checkState() == QtCore.Qt.CheckState.Checked else 0
                    cursor.execute(
                        "UPDATE stats SET min_value = ?, max_value = ?, double_chance = ? WHERE class_id = ? AND stat_name = ?",
                        (min_value, max_value, double_chance, self.current_class_id, stat_name)
                    )
                conn.commit()
        QtWidgets.QMessageBox.information(self, "Mentés", "Kaszt adatok mentve!")
        # Frissítsük a kaszt listát és a részleteket is
        self.load_classes()
        # Válasszuk ki újra az aktuális kasztot, hogy a részletek is frissüljenek
        for idx, (cid, _) in enumerate(self.class_items):
            if cid == self.current_class_id:
                self.class_list.setCurrentRow(idx)
                # A részletek frissítését explicit meghívjuk, hogy a tickboxok is biztosan frissüljenek
                self.display_class_details(self.class_list.currentItem(), None)
                break

if __name__ == "__main__":
    from utils.dark_mode import apply_dark_mode
    
    app = QtWidgets.QApplication(sys.argv)
    apply_dark_mode(app)
    
    editor = ClassEditorQt()
    editor.exec()
