"""
Skill Editor List Panel
Handles the skill list panel on the left side with tree view
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTreeWidget, QTreeWidgetItem, 
    QTreeWidgetItemIterator, QHeaderView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class SkillListPanel:
    """Manages the skill list panel with tree view"""
    
    def __init__(self, parent, on_skill_selected, on_new_skill, on_duplicate_skill, on_delete_skill):
        """
        Initialize the skill list panel
        
        Args:
            parent: Parent widget (splitter)
            on_skill_selected: Callback when skill is selected (receives skill index)
            on_new_skill: Callback for new skill button
            on_duplicate_skill: Callback for duplicate skill button
            on_delete_skill: Callback for delete skill button
        """
        self.on_skill_selected = on_skill_selected
        self.on_new_skill = on_new_skill
        self.on_duplicate_skill = on_duplicate_skill
        self.on_delete_skill = on_delete_skill
        
        # Store all skills for index mapping
        self.all_skills = []
        
        self.list_widget = QWidget()
        self.create_ui(parent)
    
    def create_ui(self, parent):
        """Create the skill list panel UI with tree view"""
        list_layout = QVBoxLayout()
        self.list_widget.setLayout(list_layout)
        
        # Header
        header_label = QLabel("Képzettségek")
        header_font = QFont()
        header_font.setPointSize(12)
        header_font.setBold(True)
        header_label.setFont(header_font)
        list_layout.addWidget(header_label)
        
        # Skill tree
        self.skill_tree = QTreeWidget()
        self.skill_tree.setColumnCount(2)
        self.skill_tree.setHeaderLabels(["Kategória / Név", "Azonosító"])
        self.skill_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.skill_tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.skill_tree.currentItemChanged.connect(self.on_tree_item_selected)
        list_layout.addWidget(self.skill_tree)
        
        # Action buttons
        btn_layout = QVBoxLayout()
        
        btn_new = QPushButton("Új képzettség")
        btn_new.clicked.connect(self.on_new_skill)
        btn_layout.addWidget(btn_new)
        
        btn_duplicate = QPushButton("Képzettség másolása")
        btn_duplicate.clicked.connect(self.on_duplicate_skill)
        btn_layout.addWidget(btn_duplicate)
        
        btn_delete = QPushButton("Törlés")
        btn_delete.clicked.connect(self.on_delete_skill)
        btn_layout.addWidget(btn_delete)
        
        btn_layout.addStretch()
        list_layout.addLayout(btn_layout)
        
        parent.addWidget(self.list_widget)
    
    def populate(self, skills):
        """
        Populate the skill tree with hierarchical structure
        
        Args:
            skills: List of skill dictionaries
        """
        self.skill_tree.clear()
        self.all_skills = skills
        
        # Build category/subcategory hierarchy
        cat_items = {}
        subcat_items = {}
        
        for idx, skill in enumerate(skills):
            main_cat = skill.get("main_category", "Egyéb")
            sub_cat = skill.get("sub_category", "")
            skill_name = skill.get("name", "Névtelen")
            skill_id = skill.get("id", "")
            param = skill.get("parameter", "")
            
            # Create or get main category item
            if main_cat not in cat_items:
                cat_item = QTreeWidgetItem([main_cat, ""])
                cat_item.setFirstColumnSpanned(True)
                font = QFont()
                font.setBold(True)
                cat_item.setFont(0, font)
                self.skill_tree.addTopLevelItem(cat_item)
                cat_items[main_cat] = cat_item
            
            parent = cat_items[main_cat]
            
            # Create or get subcategory item if exists
            if sub_cat:
                key = (main_cat, sub_cat)
                if key not in subcat_items:
                    subcat_item = QTreeWidgetItem([sub_cat, ""])
                    subcat_item.setFirstColumnSpanned(True)
                    font = QFont()
                    font.setItalic(True)
                    subcat_item.setFont(0, font)
                    parent.addChild(subcat_item)
                    subcat_items[key] = subcat_item
                parent = subcat_items[key]
            
            # Create skill leaf item
            display_name = f"{skill_name} ({param})" if param else skill_name
            skill_item = QTreeWidgetItem([display_name, skill_id])
            
            # Store the skill index in UserRole for easy retrieval
            skill_item.setData(0, Qt.ItemDataRole.UserRole, idx)
            
            parent.addChild(skill_item)
        
        # Expand all categories by default
        self.skill_tree.expandAll()
    
    def on_tree_item_selected(self, current, previous):
        """Handle tree item selection"""
        if not current:
            return
        
        # Only process leaf items (actual skills, not categories)
        skill_index = current.data(0, Qt.ItemDataRole.UserRole)
        if skill_index is not None:
            self.on_skill_selected(skill_index)
    
    def get_current_row(self):
        """Get the currently selected skill index"""
        current_item = self.skill_tree.currentItem()
        if current_item:
            skill_index = current_item.data(0, Qt.ItemDataRole.UserRole)
            if skill_index is not None:
                return skill_index
        return -1
    
    def set_current_row(self, row):
        """Set the current skill by index"""
        if row < 0 or row >= len(self.all_skills):
            return
        
        # Find the tree item with this index
        iterator = QTreeWidgetItemIterator(self.skill_tree)
        while iterator.value():
            item = iterator.value()
            skill_index = item.data(0, Qt.ItemDataRole.UserRole)
            if skill_index == row:
                self.skill_tree.setCurrentItem(item)
                # Ensure the item is visible
                self.skill_tree.scrollToItem(item)
                return
            iterator += 1
