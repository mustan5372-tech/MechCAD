"""
MechCAD Status Bar
Autodesk Fusion 360-style bottom status bar with coordinate tracking, selection readout, and solver diagnostics.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt

from mechcad.ui.theme import ThemeColors


class StatusBar(QWidget):
    """Bottom status bar displaying units, cursor coordinates, and solver status."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("StatusBar")
        self.setFixedHeight(24)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(12)

        # 1. Coordinate Readout
        self.lbl_coords = QLabel("X: 0.00 mm   Y: 0.00 mm   Z: 0.00 mm")
        self.lbl_coords.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(self.lbl_coords)

        # Separator
        sep1 = QLabel("|")
        sep1.setStyleSheet("color: #444; font-size: 10px;")
        layout.addWidget(sep1)

        # 2. Selection Info / Measurements
        self.lbl_selection = QLabel("Ready")
        self.lbl_selection.setStyleSheet(f"color: {ThemeColors.TEXT_PRIMARY}; font-size: 11px;")
        layout.addWidget(self.lbl_selection)

        layout.addStretch()

        # 3. Solver DOF Indicator
        self.lbl_solver = QLabel("● Sketch Solver: Idle")
        self.lbl_solver.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(self.lbl_solver)

        # Separator
        sep2 = QLabel("|")
        sep2.setStyleSheet("color: #444; font-size: 10px;")
        layout.addWidget(sep2)

        # 4. Units Indicator
        self.lbl_units = QLabel("Units: mm")
        self.lbl_units.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 11px; font-weight: 600;")
        layout.addWidget(self.lbl_units)

    def set_coordinates(self, x: float, y: float, z: float):
        self.lbl_coords.setText(f"X: {x:.2f} mm   Y: {y:.2f} mm   Z: {z:.2f} mm")

    def set_selection_info(self, text: str):
        self.lbl_selection.setText(text)

    def set_solver_status(self, success: bool, dof: int, message: str):
        if success:
            if dof == 0:
                color = ThemeColors.ACCENT_GREEN
                text = f"● {message}"
            else:
                color = ThemeColors.ACCENT_AMBER
                text = f"● {message}"
        else:
            color = ThemeColors.ACCENT_RED
            text = f"● {message}"
        self.lbl_solver.setText(text)
        self.lbl_solver.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: 600;")

    def set_units(self, unit_str: str):
        self.lbl_units.setText(f"Units: {unit_str}")
