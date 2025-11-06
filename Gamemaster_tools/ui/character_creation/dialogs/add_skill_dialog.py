from typing import Callable, Any
from PySide6 import QtCore, QtGui, QtWidgets

from utils.log.logger import get_logger
from utils.placeholder_manager import PlaceholderManager

logger = get_logger(__name__)


class AddSkillDialog(QtWidgets.QDialog):
    """
    Dialog to select and add a new skill for learning.
    Highlights unmet prerequisites in red and disables adding when unmet.

    Dependencies are injected to avoid tight coupling with the step widget.
    """

    def __init__(
        self,
        parent: QtWidgets.QWidget,
        db_path_getter: Callable[[str], str],
        prereq_checker,
        get_current_map: Callable[[], dict[str, dict[str, int]]],
        get_attributes: Callable[[], dict[str, Any]],
        get_current_skill_ids: Callable[[], set[str]],
        kp_cost_getter: Callable[[str, int, int], Any],
        placeholder_mgr: PlaceholderManager | None = None,
        skill_db_helper=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Új képzettség tanulása")
        self.setMinimumSize(900, 600)

        self._get_db_path = db_path_getter
        self._prereq_checker = prereq_checker
        self._get_current_map = get_current_map
        self._get_attributes = get_attributes
        self._get_current_skill_ids = get_current_skill_ids
        self._kp_cost_getter = kp_cost_getter
        self._placeholder_mgr = placeholder_mgr
        self._skill_db = skill_db_helper

        self._selected: tuple[str, int] | None = None

        self._build_ui()
        self._load_categories()
        self._load_table()
        self._update_ok_button()

    # ---- Public API ----

    def get_selected(self) -> tuple[str, int] | None:
        return self._selected

    # ---- UI construction ----

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)

        # Filters
        filter_layout = QtWidgets.QHBoxLayout()
        filter_layout.addWidget(QtWidgets.QLabel("Kategória:"))
        self.category_combo = QtWidgets.QComboBox()
        self.category_combo.addItem("Minden kategória", None)
        filter_layout.addWidget(self.category_combo, stretch=1)

        filter_layout.addWidget(QtWidgets.QLabel("Keresés:"))
        self.search_box = QtWidgets.QLineEdit()
        self.search_box.setPlaceholderText("Képzettség neve...")
        filter_layout.addWidget(self.search_box, stretch=1)
        layout.addLayout(filter_layout)

        # Table
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Képzettség", "Kategória", "Típus", "Min. KP", "Előfeltételek",
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        self.table.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection
        )
        layout.addWidget(self.table)

        # Buttons
        self.button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        ok_button = self.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        ok_button.setText("Hozzáadás")

        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        # Events
        self.category_combo.currentIndexChanged.connect(self._load_table)
        self.search_box.textChanged.connect(self._load_table)
        self.table.selectionModel().selectionChanged.connect(self._update_ok_button)

    def _load_categories(self) -> None:
        if not self._skill_db:
            return
        categories = self._skill_db.get_all_skill_categories()
        for category in categories:
            self.category_combo.addItem(category, category)

    # ---- Data loading ----

    def _load_table(self) -> None:
        if not self._skill_db:
            return
            
        self.table.setRowCount(0)
        category_filter = self.category_combo.currentData()
        search_filter = (self.search_box.text() or "").lower()
        current_skill_ids = self._get_current_skill_ids()
        current_map = self._get_current_map()
        attributes = self._get_attributes()

        try:
            skills = self._skill_db.get_learnable_skills(category_filter)
            
            for skill_id, name, parameter, category, skill_type in skills:
                if skill_id in current_skill_ids:
                    continue

                display_name = f"{name} ({parameter})" if parameter else name
                if search_filter and search_filter not in display_name.lower():
                    continue

                check_level = 1 if skill_type == 1 else 0
                check_percent = 3 if skill_type == 2 else 0

                prereq_ok, _ = self._prereq_checker.check_prerequisites(
                    skill_id, check_level, check_percent, current_map, attributes
                )

                prereq_text = "-"
                # Always show prerequisites (both met and unmet)
                parts = []
                
                # Get attribute prerequisites
                attr_rows = self._skill_db.get_skill_attribute_prerequisites(skill_id)
                
                for attr, min_val, lvl in attr_rows:
                    if lvl and int(lvl) > check_level:
                        continue
                    current_val = attributes.get(attr)
                    user_has_attr = current_val is not None and int(current_val) >= int(min_val)
                    
                    attr_str = f"{attr} {min_val}+"
                    if user_has_attr:
                        attr_str = f'<span style="color: #51cf66;">{attr_str}</span>'
                    else:
                        attr_str = f'<span style="color: #ff6b6b;">{attr_str}</span>'
                    parts.append(attr_str)
                
                # Get skill prerequisites
                prereq_rows = self._skill_db.get_skill_skill_prerequisites(skill_id)
                
                for req_skill_id, min_level, for_level in prereq_rows:
                    if for_level and int(for_level) > check_level:
                        continue
                    
                    # Check if this is a placeholder (OR logic)
                    if self._placeholder_mgr and self._placeholder_mgr.is_placeholder(req_skill_id):
                        # Get all valid alternatives for this placeholder
                        alternatives = self._placeholder_mgr.get_resolutions(req_skill_id)
                        
                        for idx, alt in enumerate(alternatives):
                            alt_id = alt['target_skill_id']
                            alt_name = alt['skill_name']
                            alt_param = alt['parameter']
                            
                            # Get skill type for proper formatting
                            alt_type = self._skill_db.get_skill_type(alt_id) or 1
                            
                            # Check if user has this alternative at required level
                            user_has = False
                            if alt_id in current_map:
                                if alt_type == 2:  # Percent-based
                                    user_has = current_map[alt_id].get("%", 0) >= int(min_level)
                                else:  # Level-based
                                    user_has = current_map[alt_id].get("level", 0) >= int(min_level)
                            
                            # Format display
                            disp = f"{alt_name} ({alt_param})" if alt_param else alt_name
                            
                            # Add "VAGY" only if not the last element
                            is_last = (idx == len(alternatives) - 1)
                            if alt_type == 2:
                                req_str = f"{disp} - {int(min_level)}%"
                            else:
                                req_str = f"{disp} - {int(min_level)}. szint"
                            
                            if not is_last:
                                req_str += " VAGY"
                            
                            # Color code: green if met, red if not
                            if user_has:
                                req_str = f'<span style="color: #51cf66;">{req_str}</span>'
                            else:
                                req_str = f'<span style="color: #ff6b6b;">{req_str}</span>'
                            
                            parts.append(req_str)
                    else:
                        # Regular (non-placeholder) prerequisite
                        skill_info = self._skill_db.get_skill_info(req_skill_id)
                        if skill_info:
                            req_name, req_param, req_type = skill_info
                            req_type_int = int(req_type or 1)
                            disp = f"{req_name} ({req_param})" if req_param else req_name
                            
                            # Check if user has this skill at required level
                            user_has_skill = False
                            if req_skill_id in current_map:
                                if req_type_int == 2:  # Percent-based
                                    user_has_skill = current_map[req_skill_id].get("%", 0) >= int(min_level)
                                else:  # Level-based
                                    user_has_skill = current_map[req_skill_id].get("level", 0) >= int(min_level)
                            
                            # Show proper suffix based on skill type
                            if req_type_int == 2:
                                req_str = f"{disp} - {int(min_level)}%"
                            else:
                                req_str = f"{disp} - {int(min_level)}. szint"
                            
                            # Color code: green if met, red if not
                            if user_has_skill:
                                req_str = f'<span style="color: #51cf66;">{req_str}</span>'
                            else:
                                req_str = f'<span style="color: #ff6b6b;">{req_str}</span>'
                            
                            parts.append(req_str)
                
                prereq_text = "<br>".join(parts) if parts else "-"

                row = self.table.rowCount()
                self.table.insertRow(row)

                name_item = QtWidgets.QTableWidgetItem(display_name)
                name_item.setData(QtCore.Qt.ItemDataRole.UserRole, (skill_id, skill_type, prereq_ok))
                if not prereq_ok:
                    name_item.setForeground(QtGui.QBrush(QtGui.QColor("#ff6b6b")))
                self.table.setItem(row, 0, name_item)

                cat_item = QtWidgets.QTableWidgetItem(category or "")
                if not prereq_ok:
                    cat_item.setForeground(QtGui.QBrush(QtGui.QColor("#ff6b6b")))
                self.table.setItem(row, 1, cat_item)

                type_text = "Szint" if skill_type == 1 else ("%" if skill_type == 2 else "Mindkettő")
                type_item = QtWidgets.QTableWidgetItem(type_text)
                if not prereq_ok:
                    type_item.setForeground(QtGui.QBrush(QtGui.QColor("#ff6b6b")))
                self.table.setItem(row, 2, type_item)

                kp_cost = self._calc_int_cost(skill_id, check_level, check_percent)
                kp_item = QtWidgets.QTableWidgetItem(str(kp_cost if kp_cost is not None else "?"))
                if not prereq_ok:
                    kp_item.setForeground(QtGui.QBrush(QtGui.QColor("#ff6b6b")))
                self.table.setItem(row, 3, kp_item)

                # Use a QLabel for prerequisites to support HTML formatting
                prereq_label = QtWidgets.QLabel(prereq_text)
                prereq_label.setTextFormat(QtCore.Qt.TextFormat.RichText)
                prereq_label.setWordWrap(True)
                prereq_label.setMargin(4)
                # Don't override colors - the HTML spans handle coloring
                self.table.setCellWidget(row, 4, prereq_label)

        except Exception as e:
            logger.error(f"Error loading skills in dialog: {e}", exc_info=True)

    # ---- Events ----

    def _update_ok_button(self) -> None:
        ok_button = self.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        selected_rows = self.table.selectionModel().selectedRows() if self.table.selectionModel() else []
        if not selected_rows:
            ok_button.setEnabled(False)
            ok_button.setToolTip("Válassz ki egy képzettséget!")
            return
        row = selected_rows[0].row()
        name_item = self.table.item(row, 0)
        _, _, prereq_ok = name_item.data(QtCore.Qt.ItemDataRole.UserRole)
        ok_button.setEnabled(bool(prereq_ok))
        ok_button.setToolTip("" if prereq_ok else "Előfeltételek nem teljesülnek")

    def _on_accept(self) -> None:
        selected_rows = self.table.selectionModel().selectedRows() if self.table.selectionModel() else []
        if not selected_rows:
            self.reject()
            return
        row = selected_rows[0].row()
        name_item = self.table.item(row, 0)
        skill_id, skill_type, prereq_ok = name_item.data(QtCore.Qt.ItemDataRole.UserRole)
        if not prereq_ok:
            self.reject()
            return
        self._selected = (skill_id, skill_type)
        self.accept()

    # ---- Helpers ----

    def _calc_int_cost(self, skill_id: str, level: int, percent: int) -> int | None:
        try:
            raw = self._kp_cost_getter(skill_id, level, percent)
            if raw is None:
                return None
            return int(raw)
        except Exception:
            return None
