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
    
    Supports two modes (one-time choice, locked after selection):
    - Roll (hybrid): Initial dice roll with ±2 adjustments funded by lowering other stats
    - Point-buy: Full control with point pool allocation
    
    Features:
    - Race and age modifiers
    - Modifier breakdown tooltips
    - Persistent state across wizard steps
    """
    
    # Signal emitted when attributes change
    attributes_changed = QtCore.Signal(dict)
    
    # Attribute names in display order
    ATTRIBUTE_ORDER = [
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
        self.mode: str = "roll"  # "roll" or "pointbuy"
        self.attribute_spinboxes: Dict[str, QtWidgets.QSpinBox] = {}
        self.final_value_labels: Dict[str, QtWidgets.QLabel] = {}
        # External context record (class/race/age from first page)
        self._last_ctx = None
        self._build_ui()
    
    def _get_race_age(self) -> tuple[str, int]:
        """Helper to get current race and age from character data."""
        data = self._get_character_data() or {}
        return data.get("Faj", "Ember"), int(data.get("Kor", 20))
        
    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Title
        header = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("Tulajdonságok")
        title.setStyleSheet("font-weight: bold; font-size: 14px; padding: 4px;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # One-time mode selection panel
        self.selection_widget = QtWidgets.QWidget()
        sel_layout = QtWidgets.QVBoxLayout(self.selection_widget)
        sel_layout.setContentsMargins(0, 8, 0, 8)
        prompt = QtWidgets.QLabel("Válassz módot a tulajdonságok meghatározásához:")
        prompt.setStyleSheet("font-weight: bold; padding: 4px;")
        sel_layout.addWidget(prompt)
        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addStretch()
        # Add dice emoji to Dobás and set button colors
        self.choose_roll_btn = QtWidgets.QPushButton("🎲 Dobás")
        self.choose_pointbuy_btn = QtWidgets.QPushButton("Pontelosztás")
        # Square-ish styling and color
        self.choose_roll_btn.setMinimumSize(100, 100)
        self.choose_roll_btn.setStyleSheet(
            "QPushButton { font-size: 14px; font-weight: bold; padding: 8px; border-radius: 6px; background-color: #4caf50; color: white; }"
            "QPushButton:hover { background-color: #388e3c; }"
        )
        self.choose_pointbuy_btn.setMinimumSize(100, 100)
        self.choose_pointbuy_btn.setStyleSheet(
            "QPushButton { font-size: 14px; font-weight: bold; padding: 8px; border-radius: 6px; background-color: #ffe082; color: #333; }"
            "QPushButton:hover { background-color: #ffd54f; }"
        )
        btn_row.addWidget(self.choose_roll_btn)
        btn_row.addSpacing(20)
        btn_row.addWidget(self.choose_pointbuy_btn)
        btn_row.addStretch()
        sel_layout.addLayout(btn_row)
        layout.addWidget(self.selection_widget)
        self.choose_roll_btn.clicked.connect(lambda: self._choose_mode("roll"))
        self.choose_pointbuy_btn.clicked.connect(lambda: self._choose_mode("pointbuy"))

        # Container for the actual controls shown after selection
        self.body_widget = QtWidgets.QWidget()
        body_layout = QtWidgets.QVBoxLayout(self.body_widget)
        body_layout.setContentsMargins(0, 0, 0, 0)
        
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
        body_layout.addWidget(self.roll_button)
        
        # Point pool display (visible in both modes; in roll mode shows hybrid remaining)
        self.points_widget = QtWidgets.QWidget()
        points_layout = QtWidgets.QHBoxLayout(self.points_widget)
        points_layout.setContentsMargins(0, 0, 0, 0)
        self.points_label = QtWidgets.QLabel("Elérhető pontok: 0 / 0")
        self.points_label.setStyleSheet("font-weight: bold; font-size: 12px; padding: 4px;")
        points_layout.addWidget(self.points_label)
        points_layout.addStretch()
        
        self.reset_btn = QtWidgets.QPushButton("Nullázás")
        self.reset_btn.clicked.connect(self._reset_to_minimums)
        self.reset_btn.setToolTip("Minden tulajdonság visszaállítása minimumra")
        points_layout.addWidget(self.reset_btn)
        
        body_layout.addWidget(self.points_widget)
        self.points_widget.setVisible(True)
        # Disable and hide reset-to-minimums in roll mode to respect ±2 hybrid limits
        self.reset_btn.setEnabled(self.mode == "pointbuy")
        self.reset_btn.setVisible(self.mode == "pointbuy")
        
        # Attributes grid
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(8)
        grid.setContentsMargins(4, 4, 4, 4)
        # Keep spinboxes compact and left-aligned; use a right-side spacer column
        grid.setColumnStretch(0, 0)  # attribute labels
        grid.setColumnStretch(1, 0)  # spinboxes
        grid.setColumnStretch(2, 1)  # spacer expands to separate columns
        grid.setColumnStretch(3, 0)  # final label caption
        grid.setColumnStretch(4, 0)  # final value
        
        for idx, (key, display_name) in enumerate(self.ATTRIBUTE_ORDER):
            # Label
            name_label = QtWidgets.QLabel(f"{display_name}:")
            name_label.setStyleSheet("font-weight: bold; color: #aaa;")
            name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
            grid.addWidget(name_label, idx, 0)
            
            # Spinbox (used in both modes; roll-mode constrained to ±2 around rolled base, point-buy uses min/max)
            spinbox = QtWidgets.QSpinBox()
            spinbox.setMinimum(1)
            spinbox.setMaximum(25)
            spinbox.setValue(10)
            spinbox.setProperty("attribute", key)
            spinbox.valueChanged.connect(self._on_spinbox_changed)
            spinbox.setMaximumWidth(80)
            grid.addWidget(spinbox, idx, 1, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
            # right-side spacer keeps the spinbox left within the cell
            grid.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum), idx, 2)
            self.attribute_spinboxes[key] = spinbox
            
            # Final value caption and value label on the right
            final_caption = QtWidgets.QLabel("Végül:")
            final_caption.setStyleSheet("font-weight: bold; color: #aaa;")
            final_caption.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
            grid.addWidget(final_caption, idx, 3)
            
            final_value_lbl = QtWidgets.QLabel("-")
            final_value_lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)
            final_value_lbl.setStyleSheet("font-size: 12px; padding-left: 6px;")
            grid.addWidget(final_value_lbl, idx, 4)
            self.final_value_labels[key] = final_value_lbl
        
        body_layout.addLayout(grid)
        body_layout.addStretch(1)
        
        # Info footer
        self.info_label = QtWidgets.QLabel(
            "<i>Dobás: magasabb átlag, kevesebb kontroll (±2 állítható minden értéken).\n"
            "Pontelosztás: teljes kontroll, alacsonyabb átlag.</i>"
        )
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: #888; font-size: 9pt; padding: 4px;")
        body_layout.addWidget(self.info_label)

        layout.addWidget(self.body_widget)
        # Initially, show selection until a mode is chosen
        self.body_widget.setVisible(False)
    
    def initialize(self, class_name: str, race: str, age: int):
        """Initialize the attribute manager for given class/race/age."""
        class_db = self._get_class_db()
        self.attribute_manager = AttributeManager(class_db)
        self.attribute_manager.initialize_for_class(class_name, race, age)
        # Record initial context (no timer watching; updates happen on wizard navigation)
        try:
            self._last_ctx = (class_name, race, int(age))
        except Exception:
            self._last_ctx = None
        
        # Set initial spinbox ranges
        for attr, spinbox in self.attribute_spinboxes.items():
            min_val, max_val = self.attribute_manager.stat_ranges.get(attr, (8, 18))
            spinbox.setRange(min_val, max_val)
            spinbox.setValue(min_val)
        
        # Restore saved state if exists
        data = self._get_character_data() or {}
        if data.get("_AttributeClassValues"):
            self._restore_saved_state(race, age, data)
        
        self.refresh()

    # Timer-based external change watcher removed; updates are handled on wizard navigation.

    def _clamp_values_to_ranges(self, values: Dict[str, int]) -> Dict[str, int]:
        """Clamp provided class values to current stat ranges."""
        clamped = {}
        for attr, _ in self.ATTRIBUTE_ORDER:
            min_val, max_val = self.attribute_manager.stat_ranges.get(attr, (8, 18))
            v = int(values.get(attr, min_val))
            clamped[attr] = max(min_val, min(max_val, v))
        return clamped

    def refresh_from_basic_selection(self, class_name: str, race: str, age: int):
        """Explicitly refresh attributes when the first page (basic/spec) changes and Next is pressed."""
        if not self.attribute_manager:
            self.initialize(class_name, race, age)
            return
        old_class = self._last_ctx[0] if self._last_ctx else None
        if class_name and class_name != old_class:
            # Reinitialize for new class, clamp current values to new ranges
            self.attribute_manager.initialize_for_class(class_name, race, age)
            current_vals = {attr: sb.value() for attr, sb in self.attribute_spinboxes.items()}
            clamped = self._clamp_values_to_ranges(current_vals)
            self.attribute_manager.set_class_values(clamped, race, age)
            self._configure_spinboxes(race, age)
        else:
            # Only race/age changed: re-apply modifiers
            try:
                self.attribute_manager.set_class_values(self.attribute_manager.class_values.copy(), race, age)
            except Exception:
                pass
        self._last_ctx = (class_name, race, int(age))
        self._update_final_labels()
        self._update_points_display()
        self._save_and_emit()
    
    def _restore_saved_state(self, race: str, age: int, data: Dict):
        """Restore previously saved attribute state."""
        self.attribute_manager.set_class_values(data["_AttributeClassValues"], race, age)
        
        if data.get("_AttributeRolledBase"):
            self.attribute_manager.set_original_class_values(data["_AttributeRolledBase"])
        
        if data.get("_AttributeMode") in ("roll", "pointbuy"):
            self.mode = data["_AttributeMode"]
            self.selection_widget.setVisible(False)
            self.body_widget.setVisible(True)
            self._apply_mode_ui()
    
    def _choose_mode(self, mode: str):
        """One-time mode selection: set mode, lock it, and prepare UI/state."""
        if mode not in ("roll", "pointbuy") or self._get_character_data().get("_AttributeModeLocked"):
            return
        
        # Lock the selection
        self.mode = mode
        self._set_character_data("_AttributeMode", mode)
        self._set_character_data("_AttributeModeLocked", True)
        
        # Show main body, hide selection
        self.selection_widget.setVisible(False)
        self.body_widget.setVisible(True)
        
        # Initialize state for chosen mode
        race, age = self._get_race_age()
        if mode == "roll":
            self._roll_attributes()
            self._set_character_data("_InitialRollDone", True)
            self.roll_button.setVisible(False)
        else:
            self.attribute_manager.reset_to_minimums(race, age)
            self._save_and_emit()
            self._update_points_display()
        
        self._apply_mode_ui()

    def _apply_mode_ui(self):
        """Apply visibility, ranges, handlers, and info text for the current mode."""
        race, age = self._get_race_age()
        
        # Update UI visibility
        initial_roll_done = self._get_character_data().get("_InitialRollDone", False)
        self.roll_button.setVisible(self.mode == "roll" and not initial_roll_done)
        self.reset_btn.setEnabled(self.mode == "pointbuy")
        self.reset_btn.setVisible(self.mode == "pointbuy")
        
        # Configure spinboxes and update display
        self._configure_spinboxes(race, age)
        self._update_info_text()
        self._update_points_display()
        self.refresh()
    
    def _configure_spinboxes(self, race: str, age: int):
        """Configure spinbox ranges and handlers based on current mode."""
        handler = self._on_spinbox_changed if self.mode == "pointbuy" else self._on_roll_spinbox_changed
        
        for attr, spinbox in self.attribute_spinboxes.items():
            spinbox.blockSignals(True)
            try:
                if self.mode == "pointbuy":
                    min_val, max_val = self.attribute_manager.stat_ranges.get(attr, (8, 18))
                    cur = self.attribute_manager.class_values.get(attr, min_val)
                else:
                    min_val, max_val = self.attribute_manager.get_roll_limits(attr)
                    cur = self.attribute_manager.class_values.get(attr, min_val)
                
                spinbox.setMinimum(min_val)
                spinbox.setMaximum(max_val)
                spinbox.setValue(cur)
                
                # Reconnect to appropriate handler
                try:
                    spinbox.valueChanged.disconnect()
                except Exception:
                    pass
                spinbox.valueChanged.connect(handler)
            finally:
                spinbox.blockSignals(False)
    
    def _update_info_text(self):
        """Update the info label text based on current mode."""
        if self.mode == "pointbuy":
            self.info_label.setText(
                "<i>Ossz el pontokat a tulajdonságok között. "
                "Magasabb értékek több pontba kerülnek.</i>"
            )
        else:
            self.info_label.setText(
                "<i>Dobás (hibrid): kezdő értékek a dobások. "
                "Csökkentéssel pontot nyersz, amiből más értékeket növelhetsz (±2 határon belül). "
                "A pontköltség megegyezik a pontelosztás szabályaival.</i>"
            )
    
    def _roll_attributes(self):
        """Roll new attribute values (only used for initial roll in hybrid mode)."""
        if not self.attribute_manager:
            QtWidgets.QMessageBox.warning(self, "Hiba", "Először válassz fajt, kasztot és életkort!")
            return
        
        race, age = self._get_race_age()
        self.attribute_manager.roll_attributes(race, age)
        
        # Persist rolled baseline
        self._set_character_data("_AttributeRolledBase", 
                                 self.attribute_manager.original_class_values.copy())
        self._save_and_emit()
        
        if self.mode == "roll":
            self._configure_spinboxes(race, age)
        
        self._update_points_display()
        self.refresh()
    
    def _reset_to_minimums(self):
        """Reset all attributes to minimum values (point-buy mode only)."""
        if not self.attribute_manager:
            return
        
        race, age = self._get_race_age()
        self.attribute_manager.reset_to_minimums(race, age)
        
        # Update all spinboxes to minimum
        self._update_spinbox_values()
        
        self._save_and_emit()
        self._update_points_display()
    
    def _update_spinbox_values(self):
        """Update all spinbox values from attribute manager."""
        for attr, spinbox in self.attribute_spinboxes.items():
            value = self.attribute_manager.class_values.get(
                attr, self.attribute_manager.stat_ranges[attr][0]
            )
            spinbox.blockSignals(True)
            spinbox.setValue(int(value))
            spinbox.blockSignals(False)
    
    def _revert_spinbox(self, spinbox: QtWidgets.QSpinBox, attr: str):
        """Revert spinbox to valid value when change is rejected."""
        if self.mode == "pointbuy":
            value = self.attribute_manager.class_values.get(
                attr, self.attribute_manager.stat_ranges[attr][0]
            )
        else:
            lo, hi = self.attribute_manager.get_roll_limits(attr)
            value = min(max(self.attribute_manager.class_values.get(attr, lo), lo), hi)
        
        spinbox.blockSignals(True)
        spinbox.setValue(value)
        spinbox.blockSignals(False)
    
    def _on_spinbox_changed(self, value):
        """Handle spinbox value change in point-buy mode."""
        if not self.attribute_manager or self.mode != "pointbuy":
            return
        
        spinbox = self.sender()
        attr = spinbox.property("attribute")
        race, age = self._get_race_age()
        
        if not self.attribute_manager.set_point_buy_value(attr, value, race, age):
            self._revert_spinbox(spinbox, attr)
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
            self._update_final_labels()

    def _on_roll_spinbox_changed(self, value):
        """Handle spinbox value change in roll (hybrid) mode with ±2 bounds and point constraints."""
        if not self.attribute_manager or self.mode != "roll":
            return
        
        spinbox = self.sender()
        attr = spinbox.property("attribute")
        race, age = self._get_race_age()
        
        if not self.attribute_manager.set_roll_value(attr, int(value), race, age):
            self._revert_spinbox(spinbox, attr)
        else:
            # Persist updated baseline
            self._set_character_data("_AttributeRolledBase", 
                                     self.attribute_manager.original_class_values.copy())
        
        self._save_and_emit()
        self._update_points_display()
        self._update_final_labels()
    
    def _update_points_display(self):
        """Update the point pool display for current mode."""
        if not self.attribute_manager:
            return
        
        if self.mode == "pointbuy":
            available = self.attribute_manager.available_points
            spent = self.attribute_manager.get_spent_points()
            remaining = available - spent
            text = f"Pontok: <b>{remaining}</b> / {available} <span style='color: #888;'>(elköltött: {spent})</span>"
        else:
            remaining = self.attribute_manager.get_hybrid_remaining_points()
            spent, generated = self.attribute_manager.get_hybrid_spent_and_generated()
            text = f"Hibrid szabad pontok: <b>{remaining}</b> <span style='color: #888;'>(költött: {spent}, nyert: {generated})</span>"
        
        self.points_label.setText(text)
        
        # Style based on remaining points
        color = "#f44336" if remaining < 0 else ("#4caf50" if remaining == 0 else "")
        self.points_label.setStyleSheet(
            f"font-weight: bold; font-size: 12px; padding: 4px;{f' color: {color};' if color else ''}"
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
        """Update the displayed attribute values and tooltips from current character data."""
        if not self.attribute_manager:
            return
        
        # Update spinbox values and tooltips
        self._update_spinbox_values()
        for attr, spinbox in self.attribute_spinboxes.items():
            breakdown = self.attribute_manager.get_attribute_breakdown(attr)
            spinbox.setToolTip(self._build_tooltip(attr, breakdown))
        # Update final value labels
        self._update_final_labels()
        
        self._update_points_display()

    def _update_final_labels(self):
        """Refresh the right-side final value labels from the attribute manager."""
        if not self.attribute_manager:
            return
        for attr, label in self.final_value_labels.items():
            final_val = self.attribute_manager.final_values.get(attr, 0)
            label.setText(str(final_val))
            # Optional subtle style: highlight if modifiers changed it
            class_val = self.attribute_manager.class_values.get(attr, 0)
            if final_val > class_val:
                label.setStyleSheet("font-size: 12px; padding-left: 6px; color: #2e7d32;")
            elif final_val < class_val:
                label.setStyleSheet("font-size: 12px; padding-left: 6px; color: #c62828;")
            else:
                label.setStyleSheet("font-size: 12px; padding-left: 6px;")
    
    def _build_tooltip(self, attr: str, breakdown: Dict) -> str:
        """Build a detailed tooltip showing attribute breakdown."""
        lines = [
            f"<b>{attr}</b>",
            "<hr>",
            f"Kaszt érték: <b>{breakdown['class_value']}</b>"
        ]
        
        if breakdown["double_roll"]:
            lines.append("  <i>(dupla dobás, magasabb)</i>")
        
        lines.append(f"  Tartomány: {breakdown['min']}-{breakdown['max']}")
        
        for mod_type, mod_key in [("Faj", "race_modifier"), ("Kor", "age_modifier")]:
            mod_val = breakdown[mod_key]
            if mod_val != 0:
                sign = "+" if mod_val > 0 else ""
                lines.append(f"{mod_type} módosító: <b>{sign}{mod_val}</b>")
        
        lines.extend(["<hr>", f"<b>Végső érték: {breakdown['final']}</b>"])
        
        return "<br>".join(lines)
                
    def get_attributes(self) -> Dict[str, int]:
        """Return the current attribute values as a dict."""
        if self.attribute_manager:
            return self.attribute_manager.get_all_final_values()
        
        data = self._get_character_data() or {}
        return data.get("Tulajdonságok", {})
