"""
MechCAD Browser (Model Tree)
Autodesk Fusion 360-style left hierarchical tree: Document Settings, Origin, Bodies, and Sketches.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem,
    QToolButton, QMenu, QHeaderView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush, QIcon

from mechcad.ui.theme import ThemeColors
from mechcad.core.document import CADDocument


class ModelBrowser(QWidget):
    """Hierarchical model browser matching Fusion 360's left tree panel."""

    item_selected = Signal(str, str)  # (item_type, item_id) e.g. ('sketch', 'sketch_1'), ('body', 'body_1')
    visibility_toggled = Signal(str, str, bool)  # (item_type, item_id, is_visible)
    edit_sketch_requested = Signal(str)  # sketch_id
    delete_item_requested = Signal(str, str)  # (item_type, item_id)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ModelBrowser")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header bar
        header_bar = QWidget()
        header_bar.setStyleSheet(f"background-color: {ThemeColors.BG_PANEL_HEADER}; border-bottom: 1px solid {ThemeColors.BORDER_SUBTLE};")
        h_layout = QHBoxLayout(header_bar)
        h_layout.setContentsMargins(8, 4, 8, 4)

        lbl_title = QLabel("BROWSER")
        lbl_title.setStyleSheet(f"font-weight: 700; font-size: 11px; color: {ThemeColors.TEXT_MUTED}; letter-spacing: 1px;")
        h_layout.addWidget(lbl_title)
        h_layout.addStretch()

        layout.addWidget(header_bar)

        # Tree Widget
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setColumnCount(2)
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        self.tree.itemClicked.connect(self._on_item_clicked)

        layout.addWidget(self.tree)

    def refresh(self, doc: CADDocument):
        """Rebuilds browser tree according to document state."""
        self.tree.clear()

        # Root Component
        root_item = QTreeWidgetItem(self.tree)
        root_item.setText(0, f"●  {doc.name} : 1")
        root_item.setExpanded(True)
        root_item.setForeground(0, QBrush(QColor("#ffffff")))

        # 1. Document Settings
        doc_settings = QTreeWidgetItem(root_item)
        doc_settings.setText(0, f"📐 Document Settings (Units: {doc.units.length_unit})")
        doc_settings.setData(0, Qt.UserRole, ("settings", "units"))

        # 2. Named Views
        views_item = QTreeWidgetItem(root_item)
        views_item.setText(0, "👁 Named Views")
        views_item.setExpanded(False)
        for view_name in ["Top", "Front", "Right", "Home"]:
            v_sub = QTreeWidgetItem(views_item)
            v_sub.setText(0, f"  {view_name}")
            v_sub.setData(0, Qt.UserRole, ("named_view", view_name.lower()))

        # 3. Origin
        origin_item = QTreeWidgetItem(root_item)
        origin_item.setText(0, "🌐 Origin")
        origin_item.setExpanded(True)
        for sub_orig in ["Origin (0,0,0)", "X Axis", "Y Axis", "Z Axis", "XY Plane", "XZ Plane", "YZ Plane"]:
            o_sub = QTreeWidgetItem(origin_item)
            o_sub.setText(0, f"  {sub_orig}")
            o_sub.setText(1, "👁")
            o_sub.setData(0, Qt.UserRole, ("origin", sub_orig))

        # 4. Bodies Folder
        bodies_item = QTreeWidgetItem(root_item)
        bodies_item.setText(0, "📦 Bodies")
        bodies_item.setExpanded(True)
        if doc.current_solid is not None and not doc.current_solid.IsNull():
            b_sub = QTreeWidgetItem(bodies_item)
            b_sub.setText(0, "  Body 1 (Solid)")
            b_sub.setText(1, "👁")
            b_sub.setData(0, Qt.UserRole, ("body", "body_1"))
            b_sub.setForeground(0, QBrush(QColor(ThemeColors.TEXT_PRIMARY)))

        # 5. Sketches Folder
        sketches_item = QTreeWidgetItem(root_item)
        sketches_item.setText(0, "✏ Sketches")
        sketches_item.setExpanded(True)
        for sid, sk in doc.sketches.items():
            sk_sub = QTreeWidgetItem(sketches_item)
            sk_sub.setText(0, f"  {sk.name} ({sk.plane})")
            sk_sub.setText(1, "👁")
            sk_sub.setData(0, Qt.UserRole, ("sketch", sid))
            sk_sub.setForeground(0, QBrush(QColor(ThemeColors.TEXT_ACCENT)))

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        data = item.data(0, Qt.UserRole)
        if not data:
            return
        item_type, item_id = data
        if column == 1:  # Clicked visibility eye
            current_vis = item.text(1) == "👁"
            new_vis = not current_vis
            item.setText(1, "👁" if new_vis else "⊘")
            self.visibility_toggled.emit(item_type, item_id, new_vis)
        else:
            self.item_selected.emit(item_type, item_id)

    def _show_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if not item:
            return
        data = item.data(0, Qt.UserRole)
        if not data:
            return
        item_type, item_id = data

        menu = QMenu(self)
        if item_type == "sketch":
            act_edit = menu.addAction("Edit Sketch")
            act_edit.triggered.connect(lambda: self.edit_sketch_requested.emit(item_id))
            menu.addSeparator()
            act_del = menu.addAction("Delete Sketch")
            act_del.triggered.connect(lambda: self.delete_item_requested.emit("sketch", item_id))
        elif item_type == "body":
            act_del = menu.addAction("Delete Body")
            act_del.triggered.connect(lambda: self.delete_item_requested.emit("body", item_id))

        if menu.actions():
            menu.exec(self.tree.mapToGlobal(pos))
