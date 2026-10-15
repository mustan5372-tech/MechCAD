"""
MechCAD Design Shortcuts Search Popup
Exact replica of Autodesk Fusion 360's "S" key shortcuts search.
Provides instant keyboard search and quick access buttons for all modeling and sketch tools.
"""

from typing import List, Dict, Tuple
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QToolButton, QFrame
)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QFont, QCursor

from mechcad.ui.theme import ThemeColors


class ShortcutSearchPopup(QDialog):
    """Floating Fusion 360 Design Shortcuts modal popup triggered by pressing 'S'."""

    command_selected = Signal(str)

    ALL_COMMANDS: List[Tuple[str, str, str]] = [
        # (id, display_label, shortcut_key)
        ("create_sketch", "Create Sketch", "L / R / C"),
        ("extrude", "Extrude", "E"),
        ("revolve", "Revolve", ""),
        ("fillet", "Fillet", "F"),
        ("chamfer", "Chamfer", ""),
        ("shell", "Shell (Hollow Solid)", ""),
        ("hole", "Hole", "H"),
        ("combine", "Combine (Join / Cut / Intersect)", ""),
        ("split_body", "Split Body", ""),
        ("sweep", "Sweep Profile", ""),
        ("loft", "Loft Profiles", ""),
        ("pattern_linear", "Rectangular Pattern", ""),
        ("pattern_circular", "Circular Pattern", ""),
        ("mirror", "Mirror Solid", ""),
        ("construct_plane", "Offset Plane", ""),
        ("measure", "Measure (Inspect)", "I"),
        ("parameters", "Change Parameters", "fx"),
        ("prim_box", "Box (Primitive)", ""),
        ("prim_cylinder", "Cylinder (Primitive)", ""),
        ("prim_sphere", "Sphere (Primitive)", ""),
        ("prim_torus", "Torus (Primitive)", ""),
        ("sketch_line", "Sketch Line", "L"),
        ("sketch_rect", "2-Point Rectangle", "R"),
        ("sketch_center_rect", "Center Rectangle", ""),
        ("sketch_circle", "Center Diameter Circle", "C"),
        ("sketch_dimension", "Sketch Dimension", "D"),
        ("insert_step", "Insert STEP CAD File", ""),
        ("export_step", "Export STEP Solid", ""),
        ("export_stl", "Export STL (3D Printing)", ""),
    ]

    def __init__(self, parent=None):
        super().__init__(parent, Qt.FramelessWindowHint | Qt.Popup)
        self.setFixedSize(320, 360)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: #252526;
                border: 1px solid #0078d4;
                border-radius: 6px;
            }}
            QLineEdit {{
                background-color: #1e1e1e;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 13px;
                color: #ffffff;
            }}
            QLineEdit:focus {{
                border: 1px solid #0078d4;
            }}
            QListWidget {{
                background-color: #1e1e1e;
                border: 1px solid #333333;
                border-radius: 4px;
                color: #e0e0e0;
                font-size: 12px;
            }}
            QListWidget::item {{
                padding: 6px 10px;
                border-bottom: 1px solid #282828;
            }}
            QListWidget::item:hover {{
                background-color: #2a2d2e;
            }}
            QListWidget::item:selected {{
                background-color: #094771;
                color: #ffffff;
            }}
            QToolButton {{
                background-color: #2d2d30;
                color: #e0e0e0;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: 600;
            }}
            QToolButton:hover {{
                background-color: #383838;
                border: 1px solid #0078d4;
            }}
        """)

        self._init_ui()

    def _init_ui(self):
        vlayout = QVBoxLayout(self)
        vlayout.setContentsMargins(10, 10, 10, 10)
        vlayout.setSpacing(8)

        # Header Title
        lbl = QLabel("DESIGN SHORTCUTS (S)")
        lbl.setStyleSheet("color: #858585; font-size: 10px; font-weight: 700; letter-spacing: 1px;")
        vlayout.addWidget(lbl)

        # Search Bar
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Search tools, features, commands...")
        self.txt_search.textChanged.connect(self._filter_commands)
        self.txt_search.returnPressed.connect(self._on_enter_pressed)
        vlayout.addWidget(self.txt_search)

        # Quick Pin Favorites Row (Like Fusion 360 top row)
        fav_layout = QHBoxLayout()
        fav_layout.setSpacing(6)
        favs = [
            ("Extrude (E)", "extrude"),
            ("Fillet (F)", "fillet"),
            ("Hole (H)", "hole"),
            ("Sketch", "create_sketch"),
            ("fx Params", "parameters"),
        ]
        for label, cmd_id in favs:
            btn = QToolButton()
            btn.setText(label)
            btn.clicked.connect(lambda _, c=cmd_id: self._trigger_command(c))
            fav_layout.addWidget(btn)
        vlayout.addLayout(fav_layout)

        # Commands List
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        vlayout.addWidget(self.list_widget)

        self._populate_list(self.ALL_COMMANDS)

    def _populate_list(self, commands):
        self.list_widget.clear()
        for cmd_id, label, shortcut in commands:
            item = QListWidgetItem()
            text = f"{label}  ({shortcut})" if shortcut else label
            item.setText(text)
            item.setData(Qt.UserRole, cmd_id)
            self.list_widget.addItem(item)
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _filter_commands(self, query: str):
        q = query.lower().strip()
        if not q:
            self._populate_list(self.ALL_COMMANDS)
            return

        filtered = [
            (cid, lbl, sc) for cid, lbl, sc in self.ALL_COMMANDS
            if q in lbl.lower() or q in cid.lower() or q in sc.lower()
        ]
        self._populate_list(filtered)

    def _trigger_command(self, cmd_id: str):
        self.command_selected.emit(cmd_id)
        self.close()

    def _on_enter_pressed(self):
        curr = self.list_widget.currentItem()
        if curr:
            cmd_id = curr.data(Qt.UserRole)
            self._trigger_command(cmd_id)

    def _on_item_double_clicked(self, item: QListWidgetItem):
        cmd_id = item.data(Qt.UserRole)
        self._trigger_command(cmd_id)

    def show_at_cursor(self):
        pos = QCursor.pos()
        # Ensure it stays within screen
        self.move(pos.x() - 100, pos.y() - 50)
        self.txt_search.clear()
        self.txt_search.setFocus()
        self.show()
