"""
MechCAD Floating Navigation Bar
Exact replica of Autodesk Fusion 360's bottom-center canvas navigation capsule.
Provides Orbit, Look At, Pan, Zoom, Window Zoom, Fit (F6), Display Settings, and Grid toggles.
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QToolButton, QMenu, QLabel, QFrame
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QAction

from mechcad.ui.theme import ThemeColors
from mechcad.ui.icons import CADIcons


class FloatingNavBar(QWidget):
    """Bottom-center floating navigation capsule for viewport camera controls."""

    nav_tool_triggered = Signal(str)  # 'orbit', 'look_at', 'pan', 'zoom', 'fit'
    display_style_changed = Signal(str)  # 'shaded_edges', 'shaded', 'wireframe'
    grid_toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("FloatingNavBar")
        self.setFixedHeight(30)
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            #FloatingNavBar {
                background-color: rgba(33, 37, 43, 0.88);
                border: 1px solid #3d4450;
                border-radius: 15px;
            }
            QToolButton {
                background: transparent;
                border: none;
                border-radius: 12px;
                padding: 3px 6px;
            }
            QToolButton:hover {
                background-color: #38404d;
            }
            QToolButton:pressed {
                background-color: #0e639c;
            }
            QToolButton:checked {
                background-color: #0e639c;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 1, 10, 1)
        layout.setSpacing(4)

        # 1. Orbit Tool
        self.btn_orbit = QToolButton()
        self.btn_orbit.setIcon(CADIcons.get("nav_orbit", 16))
        self.btn_orbit.setIconSize(QSize(16, 16))
        self.btn_orbit.setToolTip("Orbit (Shift + Middle Mouse Drag)")
        self.btn_orbit.clicked.connect(lambda: self.nav_tool_triggered.emit("orbit"))
        layout.addWidget(self.btn_orbit)

        # 2. Look At Tool
        self.btn_look_at = QToolButton()
        self.btn_look_at.setIcon(CADIcons.get("nav_look", 16))
        self.btn_look_at.setIconSize(QSize(16, 16))
        self.btn_look_at.setToolTip("Look At (Align camera normal to face or plane)")
        self.btn_look_at.clicked.connect(lambda: self.nav_tool_triggered.emit("look_at"))
        layout.addWidget(self.btn_look_at)

        # 3. Pan Tool
        self.btn_pan = QToolButton()
        self.btn_pan.setIcon(CADIcons.get("nav_pan", 16))
        self.btn_pan.setIconSize(QSize(16, 16))
        self.btn_pan.setToolTip("Pan (Middle Mouse Drag)")
        self.btn_pan.clicked.connect(lambda: self.nav_tool_triggered.emit("pan"))
        layout.addWidget(self.btn_pan)

        # 4. Zoom Tool
        self.btn_zoom = QToolButton()
        self.btn_zoom.setIcon(CADIcons.get("nav_zoom", 16))
        self.btn_zoom.setIconSize(QSize(16, 16))
        self.btn_zoom.setToolTip("Zoom (Mouse Wheel or Drag)")
        self.btn_zoom.clicked.connect(lambda: self.nav_tool_triggered.emit("zoom"))
        layout.addWidget(self.btn_zoom)

        # 5. Fit to Window (F6)
        self.btn_fit = QToolButton()
        self.btn_fit.setIcon(CADIcons.get("nav_fit", 16))
        self.btn_fit.setIconSize(QSize(16, 16))
        self.btn_fit.setToolTip("Fit to Window / Zoom Extents (F6 / Double-Click MMB)")
        self.btn_fit.clicked.connect(lambda: self.nav_tool_triggered.emit("fit"))
        layout.addWidget(self.btn_fit)

        # Separator line
        sep = QLabel("|")
        sep.setStyleSheet("color: #48505e; font-size: 11px;")
        layout.addWidget(sep)

        # 6. Display Settings Dropdown
        self.btn_display = QToolButton()
        self.btn_display.setIcon(CADIcons.get("nav_display", 16))
        self.btn_display.setIconSize(QSize(16, 16))
        self.btn_display.setText(" ▾")
        self.btn_display.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.btn_display.setToolTip("Display Settings & Visual Styles")
        self.btn_display.setPopupMode(QToolButton.InstantPopup)
        display_menu = QMenu(self)

        act_shaded_edges = display_menu.addAction("Shaded with Visible Edges (Default)")
        act_shaded_edges.triggered.connect(lambda: self.display_style_changed.emit("shaded_edges"))

        act_shaded = display_menu.addAction("Shaded")
        act_shaded.triggered.connect(lambda: self.display_style_changed.emit("shaded"))

        act_wireframe = display_menu.addAction("Wireframe")
        act_wireframe.triggered.connect(lambda: self.display_style_changed.emit("wireframe"))

        self.btn_display.setMenu(display_menu)
        layout.addWidget(self.btn_display)

        # 7. Grid & Snaps Toggle
        self.btn_grid = QToolButton()
        self.btn_grid.setIcon(CADIcons.get("nav_grid", 16))
        self.btn_grid.setIconSize(QSize(16, 16))
        self.btn_grid.setCheckable(True)
        self.btn_grid.setChecked(True)
        self.btn_grid.setToolTip("Toggle Ground Grid & Snaps")
        self.btn_grid.toggled.connect(self.grid_toggled.emit)
        layout.addWidget(self.btn_grid)
