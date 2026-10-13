"""
MechCAD Application Header
Autodesk Fusion 360-style top application bar: File menu, Save/Undo/Redo, Document tabs, and Learning Mode.
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QToolButton, QMenu, QTabBar, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QIcon

from mechcad.ui.theme import ThemeColors


class AppHeader(QWidget):
    """Top application header matching Fusion 360's application bar layout."""

    file_action_triggered = Signal(str)  # 'new', 'open', 'save', 'save_as', 'export_step', 'export_stl', 'export_dxf', 'exit'
    undo_triggered = Signal()
    redo_triggered = Signal()
    new_tab_requested = Signal()
    tab_close_requested = Signal(int)
    learning_toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AppHeader")
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 8, 2)
        layout.setSpacing(6)

        # 1. MechCAD Logo & Brand Badge
        self.brand_lbl = QLabel("MechCAD")
        self.brand_lbl.setObjectName("BrandBadge")
        layout.addWidget(self.brand_lbl)

        # 2. File Menu Dropdown
        self.file_btn = QToolButton()
        self.file_btn.setText("File ▾")
        self.file_btn.setPopupMode(QToolButton.InstantPopup)
        self.file_menu = QMenu(self)

        act_new = self.file_menu.addAction("New Design (Ctrl+N)")
        act_new.triggered.connect(lambda: self.file_action_triggered.emit("new"))
        act_open = self.file_menu.addAction("Open Project... (Ctrl+O)")
        act_open.triggered.connect(lambda: self.file_action_triggered.emit("open"))
        self.file_menu.addSeparator()

        act_save = self.file_menu.addAction("Save (Ctrl+S)")
        act_save.triggered.connect(lambda: self.file_action_triggered.emit("save"))
        act_saveas = self.file_menu.addAction("Save As...")
        act_saveas.triggered.connect(lambda: self.file_action_triggered.emit("save_as"))
        self.file_menu.addSeparator()

        act_step = self.file_menu.addAction("Export STEP Solid (.step)...")
        act_step.triggered.connect(lambda: self.file_action_triggered.emit("export_step"))
        act_stl = self.file_menu.addAction("Export STL Mesh for 3D Printing (.stl)...")
        act_stl.triggered.connect(lambda: self.file_action_triggered.emit("export_stl"))
        act_dxf = self.file_menu.addAction("Export 2D DXF Drawing (.dxf)...")
        act_dxf.triggered.connect(lambda: self.file_action_triggered.emit("export_dxf"))
        self.file_menu.addSeparator()

        act_exit = self.file_menu.addAction("Exit MechCAD")
        act_exit.triggered.connect(lambda: self.file_action_triggered.emit("exit"))

        self.file_btn.setMenu(self.file_menu)
        layout.addWidget(self.file_btn)

        # 3. Quick Access Icons: Save, Undo, Redo
        self.btn_save = QToolButton()
        self.btn_save.setText("💾")
        self.btn_save.setToolTip("Save Document (Ctrl+S)")
        self.btn_save.clicked.connect(lambda: self.file_action_triggered.emit("save"))
        layout.addWidget(self.btn_save)

        self.btn_undo = QToolButton()
        self.btn_undo.setText("↩")
        self.btn_undo.setToolTip("Undo Last Action (Ctrl+Z)")
        self.btn_undo.clicked.connect(self.undo_triggered.emit)
        layout.addWidget(self.btn_undo)

        self.btn_redo = QToolButton()
        self.btn_redo.setText("↪")
        self.btn_redo.setToolTip("Redo Action (Ctrl+Y)")
        self.btn_redo.clicked.connect(self.redo_triggered.emit)
        layout.addWidget(self.btn_redo)

        # Separator line
        sep = QLabel("|")
        sep.setStyleSheet("color: #444;")
        layout.addWidget(sep)

        # 4. Document Tab Bar
        self.tab_bar = QTabBar()
        self.tab_bar.setTabsClosable(True)
        self.tab_bar.setMovable(True)
        self.tab_bar.addTab("Untitled 1")
        self.tab_bar.tabCloseRequested.connect(self.tab_close_requested.emit)
        layout.addWidget(self.tab_bar)

        # New Tab (+) Button
        self.btn_new_tab = QToolButton()
        self.btn_new_tab.setText("+")
        self.btn_new_tab.setToolTip("New Design Tab")
        self.btn_new_tab.clicked.connect(self.new_tab_requested.emit)
        layout.addWidget(self.btn_new_tab)

        layout.addStretch()

        # 5. Right Section: Learning Mode Toggle & Help
        self.btn_learning = QToolButton()
        self.btn_learning.setText("🎓 Automobile Learning Mode")
        self.btn_learning.setCheckable(True)
        self.btn_learning.setChecked(False)
        self.btn_learning.setToolTip("Toggle Guided Automobile Engineering CAD Tutorials")
        self.btn_learning.toggled.connect(self.learning_toggled.emit)
        layout.addWidget(self.btn_learning)

        self.tagline_lbl = QLabel("Learn. Design. Engineer.")
        self.tagline_lbl.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 11px; font-style: italic; padding-right: 4px;")
        layout.addWidget(self.tagline_lbl)

    def set_tab_title(self, index: int, title: str, is_dirty: bool = False):
        display_title = title + (" *" if is_dirty else "")
        self.tab_bar.setTabText(index, display_title)
