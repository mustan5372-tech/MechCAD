"""
MechCAD Contextual Property Panel
Autodesk Fusion 360-style parameter dialogs for Extrude, Revolve, Fillet, Chamfer, Hole, and Primitives.
"""

from typing import Dict, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox, QComboBox,
    QPushButton, QCheckBox, QSlider, QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal

from mechcad.ui.theme import ThemeColors


class PropertyPanel(QWidget):
    """Contextual parameters panel displaying tool settings."""

    confirmed = Signal(str, dict)  # (tool_name, params)
    cancelled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PropertyPanel")
        self.current_tool: Optional[str] = None
        self._init_ui()

    def _init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 8, 10, 8)
        self.layout.setSpacing(8)

        # Header Title
        self.lbl_title = QLabel("PARAMETERS")
        self.lbl_title.setStyleSheet(f"font-weight: 700; font-size: 11px; color: {ThemeColors.TEXT_MUTED}; letter-spacing: 1px;")
        self.layout.addWidget(self.lbl_title)

        # Dynamic Content Container
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 4, 0, 4)
        self.content_layout.setSpacing(6)
        self.layout.addWidget(self.content_widget)

        self.layout.addStretch()

        # Action Buttons (OK / Cancel)
        self.btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self._on_cancel)
        self.btn_ok = QPushButton("OK")
        self.btn_ok.setObjectName("PrimaryButton")
        self.btn_ok.clicked.connect(self._on_confirm)

        self.btn_layout.addWidget(self.btn_cancel)
        self.btn_layout.addWidget(self.btn_ok)
        self.layout.addLayout(self.btn_layout)

        self.hide_panel()

    def hide_panel(self):
        self.current_tool = None
        self.setVisible(False)

    def _clear_content(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # --- Tool Setups ---

    def show_extrude(self, sketch_id: str, default_dist: float = 10.0):
        self.current_tool = "extrude"
        self.lbl_title.setText("EXTRUDE")
        self._clear_content()

        # Profile selection readout
        lbl_prof = QLabel("Profile:  1 Profile Selected")
        lbl_prof.setStyleSheet("color: #40a9ff; font-weight: 500;")
        self.content_layout.addWidget(lbl_prof)

        # Distance input
        lbl_dist = QLabel("Distance (mm):")
        self.spin_dist = QDoubleSpinBox()
        self.spin_dist.setRange(0.1, 10000.0)
        self.spin_dist.setValue(default_dist)
        self.spin_dist.setSingleStep(1.0)
        self.content_layout.addWidget(lbl_dist)
        self.content_layout.addWidget(self.spin_dist)

        # Operation dropdown
        lbl_op = QLabel("Operation:")
        self.combo_op = QComboBox()
        self.combo_op.addItems(["Join", "Cut", "New Body", "Intersect"])
        self.content_layout.addWidget(lbl_op)
        self.content_layout.addWidget(self.combo_op)

        self.extra_data = {"sketch_id": sketch_id}
        self.setVisible(True)

    def show_revolve(self, sketch_id: str):
        self.current_tool = "revolve"
        self.lbl_title.setText("REVOLVE")
        self._clear_content()

        lbl_prof = QLabel("Profile:  1 Profile Selected")
        lbl_prof.setStyleSheet("color: #40a9ff; font-weight: 500;")
        self.content_layout.addWidget(lbl_prof)

        lbl_angle = QLabel("Angle (°):")
        self.spin_angle = QDoubleSpinBox()
        self.spin_angle.setRange(1.0, 360.0)
        self.spin_angle.setValue(360.0)
        self.content_layout.addWidget(lbl_angle)
        self.content_layout.addWidget(self.spin_angle)

        lbl_axis = QLabel("Axis:")
        self.combo_axis = QComboBox()
        self.combo_axis.addItems(["Y Axis (Default)", "Z Axis", "X Axis"])
        self.content_layout.addWidget(lbl_axis)
        self.content_layout.addWidget(self.combo_axis)

        lbl_op = QLabel("Operation:")
        self.combo_op = QComboBox()
        self.combo_op.addItems(["Join", "Cut", "New Body"])
        self.content_layout.addWidget(lbl_op)
        self.content_layout.addWidget(self.combo_op)

        self.extra_data = {"sketch_id": sketch_id}
        self.setVisible(True)

    def show_fillet(self):
        self.current_tool = "fillet"
        self.lbl_title.setText("FILLET")
        self._clear_content()

        lbl_rad = QLabel("Radius (mm):")
        self.spin_radius = QDoubleSpinBox()
        self.spin_radius.setRange(0.1, 500.0)
        self.spin_radius.setValue(2.0)
        self.spin_radius.setSingleStep(0.5)
        self.content_layout.addWidget(lbl_rad)
        self.content_layout.addWidget(self.spin_radius)

        self.extra_data = {}
        self.setVisible(True)

    def show_chamfer(self):
        self.current_tool = "chamfer"
        self.lbl_title.setText("CHAMFER")
        self._clear_content()

        lbl_dist = QLabel("Distance (mm):")
        self.spin_dist = QDoubleSpinBox()
        self.spin_dist.setRange(0.1, 500.0)
        self.spin_dist.setValue(1.0)
        self.spin_dist.setSingleStep(0.5)
        self.content_layout.addWidget(lbl_dist)
        self.content_layout.addWidget(self.spin_dist)

        self.extra_data = {}
        self.setVisible(True)

    def show_hole(self):
        self.current_tool = "hole"
        self.lbl_title.setText("HOLE")
        self._clear_content()

        lbl_diam = QLabel("Diameter (mm):")
        self.spin_diam = QDoubleSpinBox()
        self.spin_diam.setRange(0.5, 500.0)
        self.spin_diam.setValue(8.0)
        self.content_layout.addWidget(lbl_diam)
        self.content_layout.addWidget(self.spin_diam)

        lbl_depth = QLabel("Depth (mm):")
        self.spin_depth = QDoubleSpinBox()
        self.spin_depth.setRange(1.0, 1000.0)
        self.spin_depth.setValue(20.0)
        self.content_layout.addWidget(lbl_depth)
        self.content_layout.addWidget(self.spin_depth)

        self.chk_through = QCheckBox("Through All")
        self.chk_through.setChecked(True)
        self.content_layout.addWidget(self.chk_through)

        lbl_cx = QLabel("Center X (mm):")
        self.spin_cx = QDoubleSpinBox()
        self.spin_cx.setRange(-1000.0, 1000.0)
        self.spin_cx.setValue(0.0)
        self.content_layout.addWidget(lbl_cx)
        self.content_layout.addWidget(self.spin_cx)

        lbl_cy = QLabel("Center Y (mm):")
        self.spin_cy = QDoubleSpinBox()
        self.spin_cy.setRange(-1000.0, 1000.0)
        self.spin_cy.setValue(0.0)
        self.content_layout.addWidget(lbl_cy)
        self.content_layout.addWidget(self.spin_cy)

        self.extra_data = {}
        self.setVisible(True)

    def show_box(self):
        self.current_tool = "box"
        self.lbl_title.setText("BOX")
        self._clear_content()

        lbl_dx = QLabel("Length dx (mm):")
        self.spin_dx = QDoubleSpinBox()
        self.spin_dx.setRange(1.0, 5000.0)
        self.spin_dx.setValue(40.0)
        self.content_layout.addWidget(lbl_dx)
        self.content_layout.addWidget(self.spin_dx)

        lbl_dy = QLabel("Width dy (mm):")
        self.spin_dy = QDoubleSpinBox()
        self.spin_dy.setRange(1.0, 5000.0)
        self.spin_dy.setValue(30.0)
        self.content_layout.addWidget(lbl_dy)
        self.content_layout.addWidget(self.spin_dy)

        lbl_dz = QLabel("Height dz (mm):")
        self.spin_dz = QDoubleSpinBox()
        self.spin_dz.setRange(1.0, 5000.0)
        self.spin_dz.setValue(20.0)
        self.content_layout.addWidget(lbl_dz)
        self.content_layout.addWidget(self.spin_dz)

        lbl_op = QLabel("Operation:")
        self.combo_op = QComboBox()
        self.combo_op.addItems(["New Body", "Join", "Cut"])
        self.content_layout.addWidget(lbl_op)
        self.content_layout.addWidget(self.combo_op)

        self.extra_data = {}
        self.setVisible(True)

    def show_cylinder(self):
        self.current_tool = "cylinder"
        self.lbl_title.setText("CYLINDER")
        self._clear_content()

        lbl_rad = QLabel("Radius (mm):")
        self.spin_rad = QDoubleSpinBox()
        self.spin_rad.setRange(0.5, 5000.0)
        self.spin_rad.setValue(15.0)
        self.content_layout.addWidget(lbl_rad)
        self.content_layout.addWidget(self.spin_rad)

        lbl_h = QLabel("Height (mm):")
        self.spin_h = QDoubleSpinBox()
        self.spin_h.setRange(1.0, 5000.0)
        self.spin_h.setValue(40.0)
        self.content_layout.addWidget(lbl_h)
        self.content_layout.addWidget(self.spin_h)

        lbl_op = QLabel("Operation:")
        self.combo_op = QComboBox()
        self.combo_op.addItems(["New Body", "Join", "Cut"])
        self.content_layout.addWidget(lbl_op)
        self.content_layout.addWidget(self.combo_op)

        self.extra_data = {}
        self.setVisible(True)

    def _on_confirm(self):
        if not self.current_tool:
            return
        params = {}
        if self.current_tool == "extrude":
            params = {
                "sketch_id": self.extra_data.get("sketch_id"),
                "distance": self.spin_dist.value(),
                "operation": self.combo_op.currentText().lower().replace(" ", "_"),
            }
        elif self.current_tool == "revolve":
            axis_map = {
                "Y Axis (Default)": (0.0, 1.0, 0.0),
                "Z Axis": (0.0, 0.0, 1.0),
                "X Axis": (1.0, 0.0, 0.0),
            }
            params = {
                "sketch_id": self.extra_data.get("sketch_id"),
                "angle": self.spin_angle.value(),
                "axis_dir": axis_map.get(self.combo_axis.currentText(), (0.0, 1.0, 0.0)),
                "operation": self.combo_op.currentText().lower().replace(" ", "_"),
            }
        elif self.current_tool == "fillet":
            params = {"radius": self.spin_radius.value()}
        elif self.current_tool == "chamfer":
            params = {"distance": self.spin_dist.value()}
        elif self.current_tool == "hole":
            params = {
                "diameter": self.spin_diam.value(),
                "depth": self.spin_depth.value(),
                "through_all": self.chk_through.isChecked(),
                "center_x": self.spin_cx.value(),
                "center_y": self.spin_cy.value(),
            }
        elif self.current_tool == "box":
            params = {
                "dx": self.spin_dx.value(),
                "dy": self.spin_dy.value(),
                "dz": self.spin_dz.value(),
                "operation": self.combo_op.currentText().lower().replace(" ", "_"),
            }
        elif self.current_tool == "cylinder":
            params = {
                "radius": self.spin_rad.value(),
                "height": self.spin_h.value(),
                "operation": self.combo_op.currentText().lower().replace(" ", "_"),
            }

        tool = self.current_tool
        self.hide_panel()
        self.confirmed.emit(tool, params)

    def _on_cancel(self):
        self.hide_panel()
        self.cancelled.emit()
