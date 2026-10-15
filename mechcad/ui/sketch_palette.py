"""
MechCAD Sketch Palette
Autodesk Fusion 360-style floating sketch options palette: Construction, Grid, Constraints display.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QToolButton, QFrame
)
from PySide6.QtCore import Qt, Signal

from mechcad.ui.theme import ThemeColors


class SketchPalette(QWidget):
    """Floating options panel for active 2D sketching."""

    look_at_requested = Signal()
    construction_toggled = Signal(bool)
    show_constraints_toggled = Signal(bool)
    show_dimensions_toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SketchPalette")
        self.setFixedWidth(190)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        self.setStyleSheet("""
            #SketchPalette {
                background-color: rgba(32, 32, 34, 0.94);
                border: 1px solid #444444;
                border-radius: 4px;
            }
        """)

        # Header Title
        lbl_head = QLabel("SKETCH PALETTE")
        lbl_head.setStyleSheet(f"font-weight: 700; font-size: 11px; color: {ThemeColors.TEXT_MUTED}; letter-spacing: 1px;")
        layout.addWidget(lbl_head)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"color: {ThemeColors.BORDER_SUBTLE};")
        layout.addWidget(line)

        # Options Checkboxes
        self.chk_construct = QCheckBox("Construction (X)")
        self.chk_construct.toggled.connect(self.construction_toggled.emit)
        layout.addWidget(self.chk_construct)

        self.btn_look_at = QToolButton()
        self.btn_look_at.setText("👁 Look At")
        self.btn_look_at.clicked.connect(self.look_at_requested.emit)
        layout.addWidget(self.btn_look_at)

        self.chk_grid = QCheckBox("Sketch Grid")
        self.chk_grid.setChecked(True)
        layout.addWidget(self.chk_grid)

        self.chk_snap = QCheckBox("Snap")
        self.chk_snap.setChecked(True)
        layout.addWidget(self.chk_snap)

        self.chk_constraints = QCheckBox("Show Constraints")
        self.chk_constraints.setChecked(True)
        self.chk_constraints.toggled.connect(self.show_constraints_toggled.emit)
        layout.addWidget(self.chk_constraints)

        self.chk_dims = QCheckBox("Show Dimensions")
        self.chk_dims.setChecked(True)
        self.chk_dims.toggled.connect(self.show_dimensions_toggled.emit)
        layout.addWidget(self.chk_dims)

        self.setVisible(False)
