"""
MechCAD Application Bar (Header)
Exact replica of Autodesk Fusion 360's top Application Bar:
- Data panel toggle (9-dot grid)
- File dropdown menu (New, Open, Save, Export STEP/STL/DXF, Exit)
- Quick Access Toolbar: Save, Undo, Redo
- Document Tabs (with dirty indicator '*' and tab close '×')
- New Design (+) button
- Manage Parameters (fx)
- Design Shortcuts (S)
- Automobile Tutorials toggle
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QToolButton, QMenu, QTabBar, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QAction, QIcon, QFont

from mechcad.ui.theme import ThemeColors
from mechcad.ui.icons import CADIcons


class AppHeader(QWidget):
    """Top application bar matching Fusion 360's application header layout."""

    file_action_triggered = Signal(str)  # 'new', 'open', 'save', 'save_as', 'export_step', 'export_stl', 'export_dxf', 'exit'
    undo_triggered = Signal()
    redo_triggered = Signal()
    new_tab_requested = Signal()
    tab_close_requested = Signal(int)
    learning_toggled = Signal(bool)
    parameters_requested = Signal()
    shortcuts_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AppHeader")
        self.setFixedHeight(34)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 1, 8, 1)
        layout.setSpacing(4)

        # 1. Fusion 360 Data Panel 9-Dot Toggle Button
        self.btn_data_panel = QToolButton()
        self.btn_data_panel.setIcon(CADIcons.get("data_panel", 16))
        self.btn_data_panel.setIconSize(QSize(16, 16))
        self.btn_data_panel.setToolTip("Show Data Panel (Projects & Files)")
        self.btn_data_panel.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: none;
                padding: 4px 6px;
                border-radius: 3px;
            }
            QToolButton:hover {
                background-color: #333940;
            }
        """)
        layout.addWidget(self.btn_data_panel)

        # 2. File Menu Dropdown
        self.file_btn = QToolButton()
        self.file_btn.setText("File ▾")
        self.file_btn.setToolTip("File Menu (Ctrl+N, Ctrl+O, Ctrl+S)")
        self.file_btn.setPopupMode(QToolButton.InstantPopup)
        self.file_btn.setStyleSheet("""
            QToolButton {
                font-weight: 600;
                font-size: 11px;
                color: #e0e0e0;
                background: transparent;
                border: none;
                padding: 4px 8px;
                border-radius: 3px;
            }
            QToolButton:hover {
                background-color: #333940;
                color: #ffffff;
            }
        """)
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
        act_stl = self.file_menu.addAction("Export STL Mesh (.stl)...")
        act_stl.triggered.connect(lambda: self.file_action_triggered.emit("export_stl"))
        act_dxf = self.file_menu.addAction("Export 2D DXF Drawing (.dxf)...")
        act_dxf.triggered.connect(lambda: self.file_action_triggered.emit("export_dxf"))
        act_about = self.file_menu.addAction("About MechCAD...")
        act_about.triggered.connect(lambda: self.file_action_triggered.emit("about"))
        self.file_menu.addSeparator()

        act_exit = self.file_menu.addAction("Exit MechCAD")
        act_exit.triggered.connect(lambda: self.file_action_triggered.emit("exit"))

        self.file_btn.setMenu(self.file_menu)
        layout.addWidget(self.file_btn)

        # 3. Quick Access Icons: Save, Undo, Redo
        self.btn_save = QToolButton()
        self.btn_save.setIcon(CADIcons.get("save", 16))
        self.btn_save.setIconSize(QSize(16, 16))
        self.btn_save.setToolTip("Save Document (Ctrl+S)")
        self.btn_save.setStyleSheet("QToolButton { background: transparent; border: none; padding: 4px; border-radius: 3px; } QToolButton:hover { background-color: #333940; }")
        self.btn_save.clicked.connect(lambda: self.file_action_triggered.emit("save"))
        layout.addWidget(self.btn_save)

        self.btn_undo = QToolButton()
        self.btn_undo.setIcon(CADIcons.get("undo", 16))
        self.btn_undo.setIconSize(QSize(16, 16))
        self.btn_undo.setToolTip("Undo Last Action (Ctrl+Z)")
        self.btn_undo.setStyleSheet("QToolButton { background: transparent; border: none; padding: 4px; border-radius: 3px; } QToolButton:hover { background-color: #333940; }")
        self.btn_undo.clicked.connect(self.undo_triggered.emit)
        layout.addWidget(self.btn_undo)

        self.btn_redo = QToolButton()
        self.btn_redo.setIcon(CADIcons.get("redo", 16))
        self.btn_redo.setIconSize(QSize(16, 16))
        self.btn_redo.setToolTip("Redo Action (Ctrl+Y)")
        self.btn_redo.setStyleSheet("QToolButton { background: transparent; border: none; padding: 4px; border-radius: 3px; } QToolButton:hover { background-color: #333940; }")
        self.btn_redo.clicked.connect(self.redo_triggered.emit)
        layout.addWidget(self.btn_redo)

        # Separator line
        sep = QLabel("|")
        sep.setStyleSheet("color: #44474f; font-size: 11px; padding: 0 4px;")
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
        self.btn_new_tab.setToolTip("New Design Tab (Ctrl+N)")
        self.btn_new_tab.setStyleSheet("""
            QToolButton {
                font-size: 14px;
                font-weight: bold;
                color: #a0a6b0;
                background: transparent;
                border: none;
                padding: 2px 6px;
                border-radius: 3px;
            }
            QToolButton:hover {
                background-color: #333940;
                color: #ffffff;
            }
        """)
        self.btn_new_tab.clicked.connect(self.new_tab_requested.emit)
        layout.addWidget(self.btn_new_tab)

        layout.addStretch()

        # 5. Right Section: Parameters (fx), Shortcuts (S), Learning Mode Toggle & Help
        self.btn_fx = QToolButton()
        self.btn_fx.setIcon(CADIcons.get("parameters", 18))
        self.btn_fx.setIconSize(QSize(18, 18))
        self.btn_fx.setText(" fx")
        self.btn_fx.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.btn_fx.setToolTip("Change Parameters (fx)")
        self.btn_fx.setStyleSheet("""
            QToolButton {
                font-weight: 700;
                font-size: 11px;
                color: #40a9ff;
                background: #252a30;
                border: 1px solid #38414a;
                border-radius: 3px;
                padding: 3px 8px;
            }
            QToolButton:hover {
                background-color: #2e3640;
                border-color: #40a9ff;
            }
        """)
        self.btn_fx.clicked.connect(self.parameters_requested.emit)
        layout.addWidget(self.btn_fx)

        self.btn_shortcuts = QToolButton()
        self.btn_shortcuts.setText("🔍 Shortcuts (S)")
        self.btn_shortcuts.setToolTip("Design Shortcuts Search (S)")
        self.btn_shortcuts.setStyleSheet("""
            QToolButton {
                font-size: 11px;
                color: #c0c6d0;
                background: #252a30;
                border: 1px solid #38414a;
                border-radius: 3px;
                padding: 3px 8px;
            }
            QToolButton:hover {
                background-color: #2e3640;
                color: #ffffff;
            }
        """)
        self.btn_shortcuts.clicked.connect(self.shortcuts_requested.emit)
        layout.addWidget(self.btn_shortcuts)

        self.btn_learning = QToolButton()
        self.btn_learning.setText("Tutorials")
        self.btn_learning.setCheckable(True)
        self.btn_learning.setChecked(False)
        self.btn_learning.setToolTip("Automobile Engineering CAD Tutorials")
        self.btn_learning.setStyleSheet("""
            QToolButton {
                font-size: 11px;
                color: #c0c6d0;
                background: transparent;
                border: 1px solid #38414a;
                border-radius: 3px;
                padding: 3px 8px;
            }
            QToolButton:checked {
                background-color: #0e639c;
                color: #ffffff;
                border-color: #40a9ff;
            }
            QToolButton:hover:!checked {
                background-color: #333940;
            }
        """)
        self.btn_learning.toggled.connect(self.learning_toggled.emit)
        layout.addWidget(self.btn_learning)

    def set_tab_title(self, index: int, title: str, is_dirty: bool = False):
        display_title = title + (" *" if is_dirty else "")
        self.tab_bar.setTabText(index, display_title)
