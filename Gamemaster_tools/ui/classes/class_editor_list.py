"""
Class Editor List Panel
Handles the class/specialization tree panel on the left side
"""

from PySide6 import QtCore, QtWidgets
from PySide6.QtGui import QFont


class ClassListPanel:
    """Manages the class/specialization tree panel"""

    def __init__(self, parent, on_selection_changed):
        """
        Initialize the class list panel

        Args:
            parent: Parent widget (splitter)
            on_selection_changed: Callback when selection changes (receives class_id, spec_id)
        """
        self.on_selection_changed = on_selection_changed
        self.class_db = None  # Will be set from parent

        self.list_widget = QtWidgets.QWidget()
        self.create_ui(parent)

    def create_ui(self, parent):
        """Create the class/spec tree panel UI"""
        left_layout = QtWidgets.QVBoxLayout(self.list_widget)

        # Header
        header_label = QtWidgets.QLabel("Kasztok és specializációk:")
        header_font = QFont()
        header_font.setPointSize(11)
        header_font.setBold(True)
        header_label.setFont(header_font)
        left_layout.addWidget(header_label)

        # Tree widget
        self.class_tree = QtWidgets.QTreeWidget()
        self.class_tree.setHeaderLabels(["Név"])
        self.class_tree.header().setStretchLastSection(True)
        self.class_tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.class_tree.currentItemChanged.connect(self.on_tree_selection_changed)
        left_layout.addWidget(self.class_tree)

        parent.addWidget(self.list_widget)

    def populate(self, class_db):
        """
        Populate the tree with classes and specializations

        Args:
            class_db: ClassDBManager instance
        """
        self.class_db = class_db
        self.class_tree.clear()

        # Sort by ID (not alphabetically)
        classes = sorted(self.class_db.list_classes(), key=lambda x: x[0])

        for cid, name in classes:
            class_item = QtWidgets.QTreeWidgetItem([name])
            class_item.setData(0, QtCore.Qt.ItemDataRole.UserRole, (cid, None))

            # Load specializations
            try:
                specs = self.class_db.list_specialisations(cid)
            except Exception:
                specs = []

            for spec in specs:
                s_item = QtWidgets.QTreeWidgetItem([spec["specialisation_name"]])
                s_item.setData(0, QtCore.Qt.ItemDataRole.UserRole, (cid, spec["specialisation_id"]))
                class_item.addChild(s_item)

            class_item.setExpanded(True)
            self.class_tree.addTopLevelItem(class_item)

        # Select first if available
        if self.class_tree.topLevelItemCount() > 0:
            self.class_tree.setCurrentItem(self.class_tree.topLevelItem(0))

    def on_tree_selection_changed(self, current: QtWidgets.QTreeWidgetItem, previous):
        """Handle tree item selection"""
        if not current:
            return

        data = current.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if not data:
            return

        class_id, spec_id = data
        self.on_selection_changed(class_id, spec_id)

    def reselect_current(self, class_id, spec_id):
        """Reselect the specified class/spec in tree after refresh"""
        root_count = self.class_tree.topLevelItemCount()
        for i in range(root_count):
            item = self.class_tree.topLevelItem(i)
            cid, _ = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            if cid == class_id:
                if spec_id is None:
                    self.class_tree.setCurrentItem(item)
                    return
                # Find child spec
                for j in range(item.childCount()):
                    child = item.child(j)
                    cid2, sid = child.data(0, QtCore.Qt.ItemDataRole.UserRole)
                    if sid == spec_id:
                        self.class_tree.setCurrentItem(child)
                        return
