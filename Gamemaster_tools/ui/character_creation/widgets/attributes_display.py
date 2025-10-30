from PySide6 import QtWidgets, QtCore, QtGui
from typing import Callable, Dict, Optional
import sys
import os

# Ensure engine path is available
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from engine.attribute_manager import AttributeManager


class AttributesDisplayWidget(QtWidgets.QWidget):
    """
    Interactive attribute display and management widget.
    Supports:
    - Dice rolling (with double-roll for certain stats)
    - Point-buy allocation
    - Modifier breakdown tooltips
    - Mode switching between roll and point-buy
    """
    
    # Signal emitted when attributes change
    attributes_changed = QtCore.Signal(dict)
    
    def __init__(self, 
                 get_character_data: Callable[[], Dict], 
                 set_character_data: Callable[[str, any], None],
                 get_class_db: Callable,
                 parent=None):
        super().__init__(parent)
        self._get_character_data = get_character_data
        self._set_character_data = set_character_data
        self._get_class_db = get_class_db
        self.attribute_manager: Optional[AttributeManager] = None
        self.mode = "roll"  # "roll" or "pointbuy"
        self.attribute_spinboxes: Dict[str, QtWidgets.QSpinBox] = {}
        self._build_ui()
        
    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Title and mode selector
        header = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("Tulajdonságok")
        title.setStyleSheet("font-weight: bold; font-size: 14px; padding: 4px;")
        header.addWidget(title)
        header.addStretch()
        
        # Mode toggle
        self.mode_combo = QtWidgets.QComboBox()
        self.mode_combo.addItems(["Dobás", "Pontelosztás"])
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        self.mode_combo.setToolTip("Válassz módot: kockadobás vagy pontelosztás")
        header.addWidget(QtWidgets.QLabel("Mód:"))
        header.addWidget(self.mode_combo)
        
        layout.addLayout(header)
        
        # Roll button (visible in roll mode)
        self.roll_button = QtWidgets.QPushButton("🎲 Dobás")
        self.roll_button.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.roll_button.clicked.connect(self._roll_attributes)
        layout.addWidget(self.roll_button)
        
        # Point pool display (visible in point-buy mode)
        self.points_widget = QtWidgets.QWidget()
        points_layout = QtWidgets.QHBoxLayout(self.points_widget)
        points_layout.setContentsMargins(0, 0, 0, 0)
        self.points_label = QtWidgets.QLabel("Elérhető pontok: 0 / 0")
        self.points_label.setStyleSheet("font-weight: bold; font-size: 12px; padding: 4px;")
        points_layout.addWidget(self.points_label)
        points_layout.addStretch()
        
        reset_btn = QtWidgets.QPushButton("Nullázás")
        reset_btn.clicked.connect(self._reset_to_minimums)
        reset_btn.setToolTip("Minden tulajdonság visszaállítása minimumra")
        points_layout.addWidget(reset_btn)
        
        layout.addWidget(self.points_widget)
        self.points_widget.setVisible(False)
        
        # Attributes grid
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(8)
        grid.setContentsMargins(4, 4, 4, 4)
        
        # Attribute order (MAGUS attributes - M.A.G.U.S. 5 version)
        self.attribute_labels = {}
        attributes = [
            ("Erő", "Erő"),
            ("Gyorsaság", "Gyorsaság"),
            ("Ügyesség", "Ügyesség"),
            ("Állóképesség", "Állóképesség"),
            ("Egészség", "Egészség"),
            ("Karizma", "Karizma"),
            ("Intelligencia", "Intelligencia"),
            ("Akaraterő", "Akaraterő"),
            ("Asztrál", "Asztrál"),
            ("Érzékelés", "Érzékelés"),
        ]
        
        for idx, (key, display_name) in enumerate(attributes):
            # Label
            name_label = QtWidgets.QLabel(f"{display_name}:")
            name_label.setStyleSheet("font-weight: bold; color: #aaa;")
            name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
            grid.addWidget(name_label, idx, 0)
            
            # Value display (for roll mode)
            value_label = QtWidgets.QLabel("--")
            value_label.setStyleSheet("""
                background-color: rgba(80, 80, 100, 0.3);
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 13px;
                font-weight: bold;
                color: #fff;
                min-width: 30px;
            """)
            value_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(value_label, idx, 1)
            self.attribute_labels[key] = value_label
            
            # Spinbox (for point-buy mode)
            spinbox = QtWidgets.QSpinBox()
            spinbox.setMinimum(1)
            spinbox.setMaximum(20)
            spinbox.setValue(10)
            spinbox.setProperty("attribute", key)
            spinbox.valueChanged.connect(self._on_spinbox_changed)
            spinbox.setVisible(False)
            grid.addWidget(spinbox, idx, 2)
            self.attribute_spinboxes[key] = spinbox
        
        layout.addLayout(grid)
        layout.addStretch(1)
        
        # Info footer
        self.info_label = QtWidgets.QLabel(
            "<i>Az értékek az első lépésben megadott faj, kor és kaszt alapján kerültek kiszámításra.</i>"
        )
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: #888; font-size: 9pt; padding: 4px;")
        layout.addWidget(self.info_label)
    
    def initialize(self, class_name: str, race: str, age: int):
        """Initialize the attribute manager for given class/race/age."""
        class_db = self._get_class_db()
        self.attribute_manager = AttributeManager(class_db)
        self.attribute_manager.initialize_for_class(class_name, race, age)
        
        # Update spinbox ranges based on class
        for attr, spinbox in self.attribute_spinboxes.items():
            min_val, max_val = self.attribute_manager.stat_ranges.get(attr, (8, 18))
            spinbox.setMinimum(min_val)
            spinbox.setMaximum(max_val)
            spinbox.setValue(min_val)
        
        # Update points display
        if self.mode == "pointbuy":
            self._update_points_display()
        
        # Check if we have saved class values
        data = self._get_character_data() or {}
        saved_class_values = data.get("_AttributeClassValues")
        saved_mode = data.get("_AttributeMode", "roll")
        
        if saved_class_values:
            # Restore saved values
            self.attribute_manager.set_class_values(saved_class_values, race, age)
            self.mode = saved_mode
            self.mode_combo.setCurrentText("Pontelosztás" if saved_mode == "pointbuy" else "Dobás")
        else:
            # Initial roll
            if self.mode == "roll":
                self._roll_attributes()
            else:
                self.attribute_manager.reset_to_minimums(race, age)
        
        self.refresh()
    
    def _on_mode_changed(self, index):
        """Handle mode switch between roll and point-buy."""
        new_mode = "pointbuy" if index == 1 else "roll"
        
        if new_mode == self.mode:
            return
        
        self.mode = new_mode
        
        # Update UI visibility
        self.roll_button.setVisible(self.mode == "roll")
        self.points_widget.setVisible(self.mode == "pointbuy")
        
        for label in self.attribute_labels.values():
            label.setVisible(self.mode == "roll")
        for spinbox in self.attribute_spinboxes.values():
            spinbox.setVisible(self.mode == "pointbuy")
        
        if self.mode == "pointbuy":
            self._update_points_display()
            self.info_label.setText(
                "<i>Ossz el pontokat a tulajdonságok között. "
                "Magasabb értékek több pontba kerülnek.</i>"
            )
        else:
            self.info_label.setText(
                "<i>Kattints a 'Dobás' gombra új értékek generálásához.</i>"
            )
        
        # Save mode preference
        self._set_character_data("_AttributeMode", self.mode)
        
        self.refresh()
    
    def _roll_attributes(self):
        """Roll new attribute values."""
        if not self.attribute_manager:
            QtWidgets.QMessageBox.warning(
                self, 
                "Hiba", 
                "Először válassz fajt, kasztot és életkort!"
            )
            return
        
        data = self._get_character_data() or {}
        race = data.get("Faj", "Ember")
        age = int(data.get("Kor", 20))
        
        self.attribute_manager.roll_attributes(race, age)
        self._save_and_emit()
        self.refresh()
    
    def _reset_to_minimums(self):
        """Reset all attributes to minimum values."""
        if not self.attribute_manager:
            return
        
        data = self._get_character_data() or {}
        race = data.get("Faj", "Ember")
        age = int(data.get("Kor", 20))
        
        self.attribute_manager.reset_to_minimums(race, age)
        
        # Update spinboxes
        for attr, spinbox in self.attribute_spinboxes.items():
            min_val = self.attribute_manager.stat_ranges[attr][0]
            spinbox.blockSignals(True)
            spinbox.setValue(min_val)
            spinbox.blockSignals(False)
        
        self._save_and_emit()
        self.refresh()
    
    def _on_spinbox_changed(self, value):
        """Handle spinbox value change in point-buy mode."""
        if not self.attribute_manager or self.mode != "pointbuy":
            return
        
        spinbox = self.sender()
        attr = spinbox.property("attribute")
        
        data = self._get_character_data() or {}
        race = data.get("Faj", "Ember")
        age = int(data.get("Kor", 20))
        
        # Try to set the value
        if not self.attribute_manager.set_point_buy_value(attr, value, race, age):
            # Revert to previous value
            old_value = self.attribute_manager.class_values.get(attr, 
                self.attribute_manager.stat_ranges[attr][0])
            spinbox.blockSignals(True)
            spinbox.setValue(old_value)
            spinbox.blockSignals(False)
            
            QtWidgets.QMessageBox.warning(
                self,
                "Nincs elég pont",
                f"Nincs elég pontod ehhez az értékhez!\n"
                f"Elérhető: {self.attribute_manager.available_points}\n"
                f"Elköltött: {self.attribute_manager.get_spent_points()}"
            )
        else:
            self._save_and_emit()
            self._update_points_display()
    
    def _update_points_display(self):
        """Update the point pool display."""
        if not self.attribute_manager:
            return
        
        available = self.attribute_manager.available_points
        spent = self.attribute_manager.get_spent_points()
        remaining = available - spent
        
        self.points_label.setText(
            f"Pontok: <b>{remaining}</b> / {available} "
            f"<span style='color: #888;'>(elköltött: {spent})</span>"
        )
        
        if remaining < 0:
            self.points_label.setStyleSheet(
                "font-weight: bold; font-size: 12px; padding: 4px; color: #f44336;"
            )
        elif remaining == 0:
            self.points_label.setStyleSheet(
                "font-weight: bold; font-size: 12px; padding: 4px; color: #4caf50;"
            )
        else:
            self.points_label.setStyleSheet(
                "font-weight: bold; font-size: 12px; padding: 4px;"
            )
    
    def _save_and_emit(self):
        """Save current state to character data and emit change signal."""
        if not self.attribute_manager:
            return
        
        # Save class values (before race/age modifiers)
        self._set_character_data("_AttributeClassValues", 
            self.attribute_manager.class_values.copy())
        
        # Save final values
        final = self.attribute_manager.get_all_final_values()
        self._set_character_data("Tulajdonságok", final)
        
        # Emit signal
        self.attributes_changed.emit(final)
        
    def refresh(self):
        """Update the displayed attribute values from current character data."""
        if not self.attribute_manager:
            return
        
        data = self._get_character_data() or {}
        race = data.get("Faj", "Ember")
        
        if self.mode == "roll":
            # Update labels with color coding and tooltips
            for attr, label in self.attribute_labels.items():
                breakdown = self.attribute_manager.get_attribute_breakdown(attr)
                final_value = breakdown["final"]
                
                label.setText(str(final_value))
                
                # Color coding
                base_style = """
                    background-color: rgba(80, 80, 100, 0.3);
                    padding: 4px 8px;
                    border-radius: 3px;
                    font-size: 13px;
                    font-weight: bold;
                    min-width: 30px;
                """
                
                if final_value >= 16:
                    color = "#4caf50"
                elif final_value >= 13:
                    color = "#8bc34a"
                elif final_value >= 10:
                    color = "#ffc107"
                elif final_value >= 7:
                    color = "#ff9800"
                else:
                    color = "#f44336"
                
                label.setStyleSheet(base_style + f"color: {color};")
                
                # Tooltip with breakdown
                tooltip = self._build_tooltip(attr, breakdown)
                label.setToolTip(tooltip)
        
        else:  # point-buy mode
            # Update spinboxes
            for attr, spinbox in self.attribute_spinboxes.items():
                class_value = self.attribute_manager.class_values.get(
                    attr, 
                    self.attribute_manager.stat_ranges[attr][0]
                )
                spinbox.blockSignals(True)
                spinbox.setValue(class_value)
                spinbox.blockSignals(False)
                
                # Tooltip shows final value with modifiers
                breakdown = self.attribute_manager.get_attribute_breakdown(attr)
                tooltip = self._build_tooltip(attr, breakdown)
                spinbox.setToolTip(tooltip)
            
            self._update_points_display()
    
    def _build_tooltip(self, attr: str, breakdown: Dict) -> str:
        """Build a detailed tooltip showing attribute breakdown."""
        lines = [f"<b>{attr}</b>"]
        lines.append("<hr>")
        
        class_val = breakdown["class_value"]
        race_mod = breakdown["race_modifier"]
        age_mod = breakdown["age_modifier"]
        final = breakdown["final"]
        min_val = breakdown["min"]
        max_val = breakdown["max"]
        double_roll = breakdown["double_roll"]
        
        lines.append(f"Kaszt érték: <b>{class_val}</b>")
        if double_roll:
            lines.append("  <i>(dupla dobás, magasabb)</i>")
        lines.append(f"  Tartomány: {min_val}-{max_val}")
        
        if race_mod != 0:
            sign = "+" if race_mod > 0 else ""
            lines.append(f"Faj módosító: <b>{sign}{race_mod}</b>")
        
        if age_mod != 0:
            sign = "+" if age_mod > 0 else ""
            lines.append(f"Kor módosító: <b>{sign}{age_mod}</b>")
        
        lines.append("<hr>")
        lines.append(f"<b>Végső érték: {final}</b>")
        
        return "<br>".join(lines)
                
    def get_attributes(self) -> Dict[str, int]:
        """Return the current attribute values as a dict."""
        if self.attribute_manager:
            return self.attribute_manager.get_all_final_values()
        
        data = self._get_character_data() or {}
        return data.get("Tulajdonságok", {})
