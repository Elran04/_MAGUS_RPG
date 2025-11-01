from PySide6 import QtCore, QtWidgets


class PlaceholderResolutionDialog(QtWidgets.QDialog):
    """Dialog for choosing which skill to use for a placeholder.
    Kept as a fallback; main flow uses inline dropdowns.
    """
    def __init__(self, parent, placeholder_id, resolutions):
        super().__init__(parent)
        self.placeholder_id = placeholder_id
        self.resolutions = resolutions
        self.chosen_skill_id = None
        
        self.setWindowTitle("Helyfoglaló képzettség feloldása")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QtWidgets.QVBoxLayout(self)
        
        # Header
        header_text = f"<b>Válassz egy képzettséget a(z) '{placeholder_id}' helyfoglaló helyére:</b>"
        header_label = QtWidgets.QLabel(header_text)
        header_label.setWordWrap(True)
        layout.addWidget(header_label)
        
        # List of available skills
        self.skill_list = QtWidgets.QListWidget()
        self.skill_list.doubleClicked.connect(self.on_accept)
        
        for res in resolutions:
            display_name = f"{res['skill_name']}"
            if res['parameter']:
                display_name += f" ({res['parameter']})"
            # Category intentionally not shown
            item = QtWidgets.QListWidgetItem(display_name)
            item.setData(QtCore.Qt.UserRole, res['target_skill_id'])
            self.skill_list.addItem(item)
        
        layout.addWidget(self.skill_list)
        
        # Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        btn_ok = QtWidgets.QPushButton("Kiválaszt")
        btn_ok.clicked.connect(self.on_accept)
        btn_cancel = QtWidgets.QPushButton("Mégsem")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
    
    def on_accept(self):
        """Handle OK button or double-click"""
        current_item = self.skill_list.currentItem()
        if current_item:
            self.chosen_skill_id = current_item.data(QtCore.Qt.UserRole)
            self.accept()
        else:
            QtWidgets.QMessageBox.warning(self, "Nincs kiválasztva", "Válassz egy képzettséget a listából!")
    
    def get_chosen_skill(self):
        """Return the chosen skill ID"""
        return self.chosen_skill_id
