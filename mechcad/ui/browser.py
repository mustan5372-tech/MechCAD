"""
MechCAD Browser (Model Tree Panel)
Autodesk Fusion 360-style left hierarchical tree: Document Settings, Named Views, Origin, Bodies, and Sketches.
All nodes rendered with crisp vector CAD icons and real-time visibility toggles.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem,
    QToolButton, QMenu, QHeaderView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush, QIcon

from mechcad.ui.theme import ThemeColors
from mechcad.ui.icons import CADIcons
from mechcad.core.document import CADDocument


class ModelBrowser(QWidget):
    """Hierarchical model browser matching Autodesk Fusion 360's left tree panel."""

    item_selected = Signal(str, str)             # (item_type, item_id) e.g. ('sketch', 'sketch_1'), ('body', 'body_1')
    visibility_toggled = Signal(str, str, bool)  # (item_type, item_id, is_visible)
    edit_sketch_requested = Signal(str)          # sketch_id
    create_sketch_requested = Signal(str)        # plane e.g. 'XY'
    delete_item_requested = Signal(str, str)      # (item_type, item_id)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ModelBrowser")
        self._visibility_state = {}  # (item_type, item_id) -> bool
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header bar
        header_bar = QWidget()
        header_bar.setStyleSheet("""
            QWidget {
                background-color: #252930;
                border-bottom: 1px solid #333a45;
            }
        """)
        h_layout = QHBoxLayout(header_bar)
        h_layout.setContentsMargins(10, 5, 8, 5)

        lbl_title = QLabel("BROWSER")
        lbl_title.setStyleSheet("font-weight: 700; font-size: 11px; color: #8a9ba8; letter-spacing: 0.8px;")
        h_layout.addWidget(lbl_title)
        h_layout.addStretch()

        btn_collapse = QToolButton()
        btn_collapse.setText("◀")
        btn_collapse.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: none;
                color: #657383;
                font-size: 9px;
            }
            QToolButton:hover {
                color: #ffffff;
            }
        """)
        btn_collapse.clicked.connect(self._toggle_collapse)
        h_layout.addWidget(btn_collapse)

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
        self.tree.setIndentation(14)

        self.tree.setStyleSheet("""
            QTreeWidget {
                background-color: #1e2228;
                border: none;
                color: #c8cdd5;
                font-family: 'Segoe UI';
                font-size: 11px;
                outline: none;
            }
            QTreeWidget::item {
                height: 22px;
                border-bottom: 1px solid #242931;
                padding-left: 2px;
                padding-right: 4px;
            }
            QTreeWidget::item:hover {
                background-color: #272d36;
                color: #ffffff;
            }
            QTreeWidget::item:selected {
                background-color: #0082c8;
                color: #ffffff;
            }
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {
                image: none;
            }
        """)

        layout.addWidget(self.tree)

    def _toggle_collapse(self):
        self.setVisible(not self.isVisible())

    def refresh(self, doc: CADDocument):
        """Rebuilds browser tree according to document state."""
        self.tree.clear()

        # 1. Root Component (Active)
        root_item = QTreeWidgetItem(self.tree)
        root_item.setIcon(0, CADIcons.get("component", 16))
        root_item.setText(0, f"{doc.name} : 1")
        root_item.setExpanded(True)
        root_item.setForeground(0, QBrush(QColor("#ffffff")))

        # 2. Document Settings
        doc_settings = QTreeWidgetItem(root_item)
        doc_settings.setIcon(0, CADIcons.get("doc_settings", 16))
        doc_settings.setText(0, f"Document Settings (Units: {doc.units.length_unit})")
        doc_settings.setData(0, Qt.UserRole, ("settings", "units"))

        # 3. Named Views
        views_item = QTreeWidgetItem(root_item)
        views_item.setIcon(0, CADIcons.get("named_views", 16))
        views_item.setText(0, "Named Views")
        views_item.setExpanded(False)
        for view_name in ["Top", "Front", "Right", "Home"]:
            v_sub = QTreeWidgetItem(views_item)
            v_sub.setIcon(0, CADIcons.get("named_views", 14))
            v_sub.setText(0, view_name)
            v_sub.setData(0, Qt.UserRole, ("named_view", view_name.lower()))

        # 4. Origin
        origin_item = QTreeWidgetItem(root_item)
        origin_item.setIcon(0, CADIcons.get("origin", 16))
        origin_item.setText(0, "Origin")
        origin_item.setExpanded(True)
        self._set_eye(origin_item, "origin", "root", True)

        origin_subitems = [
            ("Origin (0,0,0)", "origin_pt"),
            ("X Axis", "axis_x"),
            ("Y Axis", "axis_y"),
            ("Z Axis", "axis_z"),
            ("XY Plane", "plane_xy"),
            ("XZ Plane", "plane_xz"),
            ("YZ Plane", "plane_yz"),
        ]
        for label, tag in origin_subitems:
            o_sub = QTreeWidgetItem(origin_item)
            o_sub.setIcon(0, CADIcons.get("plane" if "Plane" in label else "origin", 14))
            o_sub.setText(0, label)
            o_sub.setData(0, Qt.UserRole, ("origin", label))
            is_vis = self._visibility_state.get(("origin", label), True)
            self._set_eye(o_sub, "origin", label, is_vis)

        # 5. Bodies Folder
        bodies_item = QTreeWidgetItem(root_item)
        bodies_item.setIcon(0, CADIcons.get("folder", 16))
        bodies_item.setText(0, "Bodies")
        bodies_item.setExpanded(True)
        self._set_eye(bodies_item, "bodies", "root", True)

        if doc.current_solid is not None and not doc.current_solid.IsNull():
            b_sub = QTreeWidgetItem(bodies_item)
            b_sub.setIcon(0, CADIcons.get("browser_body", 16))
            b_sub.setText(0, "Body 1")
            b_sub.setData(0, Qt.UserRole, ("body", "body_1"))
            b_sub.setForeground(0, QBrush(QColor("#e0e6ed")))
            is_vis = self._visibility_state.get(("body", "body_1"), True)
            self._set_eye(b_sub, "body", "body_1", is_vis)

        # 6. Sketches Folder
        sketches_item = QTreeWidgetItem(root_item)
        sketches_item.setIcon(0, CADIcons.get("folder", 16))
        sketches_item.setText(0, "Sketches")
        sketches_item.setExpanded(True)
        self._set_eye(sketches_item, "sketches", "root", True)

        for sid, sk in doc.sketches.items():
            sk_sub = QTreeWidgetItem(sketches_item)
            sk_sub.setIcon(0, CADIcons.get("browser_sketch", 16))
            sk_sub.setText(0, f"{sk.name} ({sk.plane})")
            sk_sub.setData(0, Qt.UserRole, ("sketch", sid))
            sk_sub.setForeground(0, QBrush(QColor("#00a0ff")))
            is_vis = self._visibility_state.get(("sketch", sid), True)
            self._set_eye(sk_sub, "sketch", sid, is_vis)

        # 7. Construction Planes Folder
        if hasattr(doc, "construction_planes") and doc.construction_planes:
            const_item = QTreeWidgetItem(root_item)
            const_item.setIcon(0, CADIcons.get("construct_plane", 16))
            const_item.setText(0, "Construction")
            const_item.setExpanded(True)
            self._set_eye(const_item, "construction", "root", True)
            for pid, cp in doc.construction_planes.items():
                cp_sub = QTreeWidgetItem(const_item)
                cp_sub.setIcon(0, CADIcons.get("plane", 14))
                cp_sub.setText(0, cp["name"])
                cp_sub.setData(0, Qt.UserRole, ("construction", pid))
                cp_sub.setForeground(0, QBrush(QColor("#f5a623")))
                is_vis = self._visibility_state.get(("construction", pid), cp.get("is_visible", True))
                self._set_eye(cp_sub, "construction", pid, is_vis)

    def _set_eye(self, item: QTreeWidgetItem, item_type: str, item_id: str, is_visible: bool):
        icon_name = "eye_on" if is_visible else "eye_off"
        item.setIcon(1, CADIcons.get(icon_name, 14))
        item.setData(1, Qt.UserRole, is_visible)

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        data = item.data(0, Qt.UserRole)
        if not data:
            return
        item_type, item_id = data
        if column == 1:  # Clicked visibility eye
            curr_vis = item.data(1, Qt.UserRole)
            if curr_vis is None:
                curr_vis = True
            new_vis = not curr_vis
            self._visibility_state[(item_type, item_id)] = new_vis
            self._set_eye(item, item_type, item_id, new_vis)
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
        menu.setStyleSheet("""
            QMenu {
                background-color: #2b3038;
                border: 1px solid #454d59;
                color: #e0e0e0;
                font-family: 'Segoe UI';
                font-size: 11px;
                padding: 4px;
            }
            QMenu::item {
                padding: 5px 22px 5px 20px;
                border-radius: 2px;
            }
            QMenu::item:selected {
                background-color: #0082c8;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background: #3e4652;
                margin: 4px 6px;
            }
        """)

        if item_type == "origin" and "Plane" in str(item_id):
            pl_code = "XY" if "XY" in str(item_id) else ("XZ" if "XZ" in str(item_id) else "YZ")
            act_sketch = menu.addAction(f"Create Sketch on {pl_code} Plane")
            act_sketch.setIcon(CADIcons.get("create_sketch", 16))
            act_sketch.triggered.connect(lambda: self.create_sketch_requested.emit(pl_code))
        elif item_type == "sketch":
            act_edit = menu.addAction("Edit Sketch")
            act_edit.setIcon(CADIcons.get("sketch_line", 16))
            act_edit.triggered.connect(lambda: self.edit_sketch_requested.emit(item_id))
            menu.addSeparator()
            act_del = menu.addAction("Delete Sketch")
            act_del.triggered.connect(lambda: self.delete_item_requested.emit("sketch", item_id))
        elif item_type == "body":
            act_del = menu.addAction("Delete Body")
            act_del.triggered.connect(lambda: self.delete_item_requested.emit("body", item_id))
        elif item_type == "construction":
            act_sketch = menu.addAction("Create Sketch on this Plane")
            act_sketch.setIcon(CADIcons.get("create_sketch", 16))
            act_sketch.triggered.connect(lambda: self.create_sketch_requested.emit(item_id))
            menu.addSeparator()
            act_del = menu.addAction("Delete Construction Plane")
            act_del.triggered.connect(lambda: self.delete_item_requested.emit("construction", item_id))
        elif item_type == "named_view":
            act_apply = menu.addAction("Orient to View")
            act_apply.triggered.connect(lambda: self.item_selected.emit("named_view", item_id))

        if menu.actions():
            menu.exec(self.tree.mapToGlobal(pos))
