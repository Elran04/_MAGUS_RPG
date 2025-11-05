import contextlib
from collections.abc import Callable

from PySide6 import QtCore, QtWidgets

from ui.character_creation.widgets.common import AttributesReadOnlyWidget
from engine.currency_manager import CurrencyManager
from ui.character_creation.services import SkillDatabaseHelper, EquipmentLoader


class SummaryStepWidget(QtWidgets.QWidget):
    """
    Summary step widget to display the aggregated character data.

    Contract:
    - constructor accepts get_data: Callable[[], dict]
    - refresh(): recompute and display summary from current data
    - get_result(): return the same data (future hook for finalized payload)
    """

    def __init__(self, get_data: Callable[[], dict], parent=None):
        super().__init__(parent)
        self._get_data = get_data
        self._currency_manager = CurrencyManager()
        # Helpers: skill name resolver and equipment catalog
        self._skill_db = SkillDatabaseHelper("")
        self._equip_loader = EquipmentLoader()
        equip_data = self._equip_loader.load_all_equipment()
        # Build quick-lookup map: {category: {id: item_dict}}
        self._equip_map: dict[str, dict[str, dict]] = {
            "armor": {i.get("id"): i for i in equip_data.get("armor", [])},
            "weapons_and_shields": {i.get("id"): i for i in equip_data.get("weapons_and_shields", [])},
            "general": {i.get("id"): i for i in equip_data.get("general", [])},
        }
        self._build_ui()
        
    def _build_ui(self):
        """Build the structured summary UI."""
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(12)
        
        # Title
        title = QtWidgets.QLabel("Karakter összegzés")
        title.setStyleSheet("font-weight: bold; font-size: 16px; padding: 4px;")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)
        
        # Main content: 3-column layout
        content_layout = QtWidgets.QHBoxLayout()
        content_layout.setSpacing(12)
        
        # Left column: Basic info + Attributes
        left_column = self._build_left_column()
        content_layout.addWidget(left_column, stretch=1)
        
        # Middle column: Skills/Equipment tabs
        middle_column = self._build_middle_column()
        content_layout.addWidget(middle_column, stretch=2)
        
        # Right column: Combat stats
        right_column = self._build_right_column()
        content_layout.addWidget(right_column, stretch=1)
        
        main_layout.addLayout(content_layout, stretch=1)
        
    def _build_left_column(self) -> QtWidgets.QWidget:
        """Build the left column: Basic info + Attributes."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Basic info groupbox
        self.basic_info_group = QtWidgets.QGroupBox("Alap információk")
        self.basic_info_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
            }
        """)
        basic_layout = QtWidgets.QFormLayout()
        basic_layout.setSpacing(8)
        basic_layout.setContentsMargins(8, 12, 8, 8)
        
        self.name_label = QtWidgets.QLabel("-")
        self.race_label = QtWidgets.QLabel("-")
        self.class_label = QtWidgets.QLabel("-")
        self.spec_label = QtWidgets.QLabel("-")
        self.age_label = QtWidgets.QLabel("-")
        self.gender_label = QtWidgets.QLabel("-")
        
        for label in [self.name_label, self.race_label, self.class_label, 
                      self.spec_label, self.age_label, self.gender_label]:
            label.setStyleSheet("font-weight: normal; color: #ddd;")
        
        basic_layout.addRow("Név:", self.name_label)
        basic_layout.addRow("Faj:", self.race_label)
        basic_layout.addRow("Kaszt:", self.class_label)
        basic_layout.addRow("Specializáció:", self.spec_label)
        basic_layout.addRow("Kor:", self.age_label)
        basic_layout.addRow("Nem:", self.gender_label)
        
        self.basic_info_group.setLayout(basic_layout)
        layout.addWidget(self.basic_info_group)
        
        # Attributes (read-only)
        self.attributes_widget = AttributesReadOnlyWidget(self._get_data)
        layout.addWidget(self.attributes_widget, stretch=1)
        
        return widget
        
    def _build_middle_column(self) -> QtWidgets.QWidget:
        """Build the middle column: Skills and Equipment tabs."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.tabs = QtWidgets.QTabWidget()
        
        # Skills tab
        self.skills_widget = QtWidgets.QWidget()
        skills_layout = QtWidgets.QVBoxLayout(self.skills_widget)
        skills_layout.setContentsMargins(8, 8, 8, 8)
        
        self.skills_tree = QtWidgets.QTreeWidget()
        self.skills_tree.setHeaderLabels(["Képzettség", "Szint/%"])
        self.skills_tree.setAlternatingRowColors(True)
        # Enable category grouping (expandable root items)
        self.skills_tree.setRootIsDecorated(True)
        skills_layout.addWidget(self.skills_tree)
        
        self.tabs.addTab(self.skills_widget, "Képzettségek")
        
        # Equipment tab
        self.equipment_widget = QtWidgets.QWidget()
        equipment_layout = QtWidgets.QVBoxLayout(self.equipment_widget)
        equipment_layout.setContentsMargins(8, 8, 8, 8)
        
        # Currency display
        self.currency_label = QtWidgets.QLabel()
        self.currency_label.setStyleSheet("font-weight: bold; padding: 4px; background-color: #2a2a2a; border-radius: 3px;")
        equipment_layout.addWidget(self.currency_label)
        
        # Equipment tree
        self.equipment_tree = QtWidgets.QTreeWidget()
        self.equipment_tree.setHeaderLabels(["Tárgy", "Mennyiség"])
        self.equipment_tree.setAlternatingRowColors(True)
        # Enable category grouping (expandable root items)
        self.equipment_tree.setRootIsDecorated(True)
        equipment_layout.addWidget(self.equipment_tree)
        
        self.tabs.addTab(self.equipment_widget, "Felszerelés")
        
        layout.addWidget(self.tabs)
        return widget
        
    def _build_right_column(self) -> QtWidgets.QWidget:
        """Build the right column: Combat stats."""
        self.combat_group = QtWidgets.QGroupBox("Harci értékek")
        self.combat_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
            }
        """)
        
        layout = QtWidgets.QFormLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(8, 12, 8, 8)
        
        # Combat stat labels
        self.fp_label = QtWidgets.QLabel("-")
        self.ep_label = QtWidgets.QLabel("-")
        self.kp_label = QtWidgets.QLabel("-")
        self.ke_label = QtWidgets.QLabel("-")
        self.te_label = QtWidgets.QLabel("-")
        self.ve_label = QtWidgets.QLabel("-")
        self.ce_label = QtWidgets.QLabel("-")
        
        for label in [self.fp_label, self.ep_label, self.kp_label, self.ke_label,
                      self.te_label, self.ve_label, self.ce_label]:
            label.setStyleSheet(
                "font-weight: bold; padding: 4px 8px; background-color: #2a2a2a; "
                "border-radius: 3px; min-width: 40px;"
            )
            label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        
        layout.addRow("FP:", self.fp_label)
        layout.addRow("ÉP:", self.ep_label)
        layout.addRow("KP:", self.kp_label)
        layout.addRow("KÉ:", self.ke_label)
        layout.addRow("TÉ:", self.te_label)
        layout.addRow("VÉ:", self.ve_label)
        layout.addRow("CÉ:", self.ce_label)
        
        self.combat_group.setLayout(layout)
        return self.combat_group
        
    def refresh(self):
        """Update all display widgets from current character data."""
        data = self._get_data() or {}
        
        # Update basic info
        self.name_label.setText(data.get("Név", "-"))
        self.race_label.setText(data.get("Faj", "-"))
        self.class_label.setText(data.get("Kaszt", "-"))
        self.spec_label.setText(data.get("Specializáció", "-") or "Nincs")
        self.age_label.setText(str(data.get("Kor", "-")))
        self.gender_label.setText(data.get("Nem", "-"))
        
        # Update attributes
        self.attributes_widget.refresh()
        
        # Update skills tree grouped by main category
        self.skills_tree.clear()
        skills = data.get("Képzettségek", [])
        grouped_skills: dict[str, list[QtWidgets.QTreeWidgetItem]] = {}
        for skill in skills:
            skill_id = skill.get("id", "???")
            # Prefer explicit display/name if present
            skill_name = skill.get("Képzettség") or skill.get("name")
            if not skill_name and skill_id and skill_id != "???":
                info = self._skill_db.get_skill_info(skill_id)
                if info:
                    n, p, _ = info
                    skill_name = f"{n} ({p})" if p else n
            if not skill_name:
                skill_name = skill_id

            # Determine category
            cat = "Egyéb"
            with contextlib.suppress(Exception):
                cats = self._skill_db.get_skill_categories(skill_id)
                if cats and (cats[0] or cats[1]):
                    cat = cats[0] or cats[1] or "Egyéb"

            # Determine level/percentage display
            level = skill.get("Szint", 0)
            percent = skill.get("%", 0)
            if level and int(level) > 0:
                level_str = f"{level}. fok"
            elif percent and int(percent) > 0:
                level_str = f"{percent}%"
            else:
                level_str = "Alap"

            child = QtWidgets.QTreeWidgetItem([skill_name, level_str])
            grouped_skills.setdefault(cat, []).append(child)

        # Create group nodes
        for cat, items in sorted(grouped_skills.items(), key=lambda kv: kv[0]):
            root = QtWidgets.QTreeWidgetItem([cat, ""])
            for child in items:
                root.addChild(child)
            self.skills_tree.addTopLevelItem(root)
            self.skills_tree.expandItem(root)

        self.skills_tree.resizeColumnToContents(0)
        
        # Update equipment
        equipment = data.get("Felszerelés", {})
        currency = equipment.get("currency", 0)
        items = equipment.get("items", [])
        
        # Update currency display
        self.currency_label.setText(f"Vagyon: {self._currency_manager.format(currency)}")
        
        # Update equipment tree grouped by category
        self.equipment_tree.clear()
        group_labels = {
            "armor": "Páncélzat",
            "weapons_and_shields": "Fegyverek és pajzsok",
            "general": "Általános",
        }
        grouped_items: dict[str, list[QtWidgets.QTreeWidgetItem]] = {}
        for item in items:
            # Minimal format: { category, id, qty? }
            cat = item.get("category") or "general"
            iid = item.get("id")
            qty = int(item.get("qty", 1))
            item_name = None
            if cat and iid:
                item_dict = self._equip_map.get(cat, {}).get(iid)
                if item_dict:
                    item_name = item_dict.get("name")
            # Fallbacks for older shape
            if not item_name:
                item_name = item.get("name") or iid or "???"
            child = QtWidgets.QTreeWidgetItem([item_name, str(qty)])
            grouped_items.setdefault(cat, []).append(child)

        # Create group nodes
        for cat_key in ("armor", "weapons_and_shields", "general"):
            items_in_cat = grouped_items.get(cat_key, [])
            if not items_in_cat:
                continue
            root = QtWidgets.QTreeWidgetItem([group_labels.get(cat_key, cat_key), ""])
            for child in items_in_cat:
                root.addChild(child)
            self.equipment_tree.addTopLevelItem(root)
            self.equipment_tree.expandItem(root)
        
        self.equipment_tree.resizeColumnToContents(0)
        
        # Update combat stats
        combat = data.get("Harci értékek", {})
        self.fp_label.setText(str(combat.get("FP", "-")))
        self.ep_label.setText(str(combat.get("ÉP", "-")))
        
        # KP display (remaining from character creation)
        kp_val = data.get("Képzettségpontok", 0)
        if isinstance(kp_val, dict):
            kp_val = kp_val.get("Remaining", 0)
        self.kp_label.setText(str(kp_val))
        
        self.ke_label.setText(str(combat.get("KÉ", "-")))
        self.te_label.setText(str(combat.get("TÉ", "-")))
        self.ve_label.setText(str(combat.get("VÉ", "-")))
        self.ce_label.setText(str(combat.get("CÉ", "-")))
        # MGT is evaluated in-game depending on armor; not shown in summary
        
    def get_result(self) -> dict:
        """Return filtered data for downstream save/finish operations."""
        return self._filtered_data()

    def _filtered_data(self) -> dict:
        """Return only the fields we want to present and save.
    Includes: base info (Név, Nem, Kor, Faj, Kaszt, Specializáció),
    Tulajdonságok, Képzettségek, Felszerelés, Képzettségpontok (int).
    Excludes: any keys starting with '_', descriptions, etc. (Harci értékek kept, but
    HM/szint removed)
        """
        src = dict(self._get_data() or {})
        allowed_keys = {
            "Név",
            "Nem",
            "Kor",
            "Faj",
            "Kaszt",
            "Specializáció",
            "Tulajdonságok",
            "Képzettségek",
            "Felszerelés",
            "Képzettségpontok",
            "Harci értékek",
        }
        out = {}
        for k, v in src.items():
            if k.startswith("_"):
                continue
            if k == "Spec_leírás":
                continue
            if k in ("Fejleszthető",):
                continue
            if k in allowed_keys:
                out[k] = v
        # Ensure required collections exist
        out.setdefault("Képzettségek", [])
        out.setdefault("Felszerelés", {"currency": 0, "items": []})

        # Transform skills to minimal schema: only id + (Szint or %)
        minimal_skills: list[dict] = []
        for s in out.get("Képzettségek", []) or []:
            sid = s.get("id")
            if not sid:
                continue
            if int(s.get("Szint", 0) or 0) > 0:
                minimal_skills.append({"id": sid, "Szint": int(s.get("Szint", 0) or 0)})
            elif int(s.get("%", 0) or 0) > 0:
                minimal_skills.append({"id": sid, "%": int(s.get("%", 0) or 0)})
            else:
                # If neither present, still keep id to indicate possession at base
                minimal_skills.append({"id": sid})
        out["Képzettségek"] = minimal_skills

        # Coerce KP to int (remaining). If dict leaked in, squash to 0 or best-effort.
        kp_val = out.get("Képzettségpontok", 0)
        if isinstance(kp_val, dict):
            # Prefer a 'Remaining' field if present, else 0
            kp_val = int(kp_val.get("Remaining", 0) or 0)
        with contextlib.suppress(Exception):
            kp_val = int(kp_val)
        out["Képzettségpontok"] = kp_val

        # Remove HM/szint from Harci értékek (these are DB-derived per-level rules)
        combat = out.get("Harci értékek")
        if isinstance(combat, dict) and "HM/szint" in combat:
            combat = dict(combat)
            combat.pop("HM/szint", None)
            out["Harci értékek"] = combat
        return out

