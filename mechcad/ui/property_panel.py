"""
MechCAD Contextual Feature Parameters Dialog Panel
Faithful replica of Autodesk Fusion 360 command palettes:
- Extrude (E)
- Revolve
- Hole (H)
- Fillet (F)
- Chamfer
- Shell (Hollow solid)
- Combine (Join, Cut, Intersect)
- Split Body
- Patterns & Mirror
- Primitives (Box, Cylinder, Sphere, Torus, Cone)
"""

from typing import Dict, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox, QComboBox,
    QPushButton, QCheckBox, QLineEdit, QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal

from mechcad.ui.theme import ThemeColors


class PropertyPanel(QWidget):
    """Contextual parameters panel displaying Fusion 360 tool settings."""

    confirmed = Signal(str, dict)  # (tool_name, params)
    cancelled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PropertyPanel")
        self.current_tool: Optional[str] = None
        self.extra_data: Dict[str, Any] = {}
        self._init_ui()

    def _init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 10, 12, 10)
        self.layout.setSpacing(10)

        # Header Title
        self.lbl_title = QLabel("PARAMETERS")
        self.lbl_title.setStyleSheet(f"""
            font-weight: 700;
            font-size: 11px;
            color: #ffffff;
            letter-spacing: 1px;
            background-color: {ThemeColors.BG_PANEL_HEADER};
            padding: 6px 8px;
            border-radius: 3px;
        """)
        self.layout.addWidget(self.lbl_title)

        # Dynamic Content Container inside ScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 4, 0, 4)
        self.content_layout.setSpacing(8)
        scroll.setWidget(self.content_widget)
        self.layout.addWidget(scroll)

        self.layout.addStretch()

        # Action Buttons (OK / Cancel)
        self.btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: #e0e0e0;
                padding: 6px 14px;
                border-radius: 3px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #444444;
            }
        """)
        self.btn_cancel.clicked.connect(self._on_cancel)

        self.btn_ok = QPushButton("OK")
        self.btn_ok.setObjectName("PrimaryButton")
        self.btn_ok.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.ACCENT_BLUE};
                color: #ffffff;
                padding: 6px 18px;
                border-radius: 3px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: #1084d8;
            }}
        """)
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

    def _create_row_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 11px; font-weight: 600;")
        return lbl

    def _create_expr_input(self, default_val: str = "10.0 mm") -> QLineEdit:
        line = QLineEdit(str(default_val))
        line.setStyleSheet(f"""
            QLineEdit {{
                background-color: #1e1e1e;
                border: 1px solid {ThemeColors.BORDER_SUBTLE};
                border-radius: 3px;
                padding: 5px 8px;
                color: #ffffff;
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border: 1px solid {ThemeColors.BORDER_FOCUS};
            }}
        """)
        return line

    def _create_combo(self, items: list) -> QComboBox:
        combo = QComboBox()
        combo.addItems(items)
        combo.setStyleSheet(f"""
            QComboBox {{
                background-color: #1e1e1e;
                border: 1px solid {ThemeColors.BORDER_SUBTLE};
                border-radius: 3px;
                padding: 4px 8px;
                color: #ffffff;
                font-size: 11px;
            }}
        """)
        return combo

    # --- Tool Setups (Fusion 360 Parity) ---

    def show_extrude(self, sketch_id: str, default_dist: float = 20.0):
        self.current_tool = "extrude"
        self.lbl_title.setText("EXTRUDE")
        self._clear_content()

        # Profile selection
        lbl_prof = QLabel("Profile:  1 Profile Selected")
        lbl_prof.setStyleSheet("color: #40a9ff; font-weight: 600; padding: 4px 0;")
        self.content_layout.addWidget(lbl_prof)

        # Direction
        self.content_layout.addWidget(self._create_row_label("Direction:"))
        self.combo_dir = self._create_combo(["One Side", "Two Sides", "Symmetric"])
        self.content_layout.addWidget(self.combo_dir)

        # Extent / Distance
        self.content_layout.addWidget(self._create_row_label("Distance (mm):"))
        self.txt_dist = self._create_expr_input(f"{default_dist:.1f} mm")
        self.content_layout.addWidget(self.txt_dist)

        # Taper Angle
        self.content_layout.addWidget(self._create_row_label("Taper Angle:"))
        self.txt_taper = self._create_expr_input("0.0 deg")
        self.content_layout.addWidget(self.txt_taper)

        # Operation
        self.content_layout.addWidget(self._create_row_label("Operation:"))
        self.combo_op = self._create_combo(["Join", "Cut", "New Body", "Intersect"])
        self.content_layout.addWidget(self.combo_op)

        self.extra_data = {"sketch_id": sketch_id}
        self.setVisible(True)

    def show_revolve(self, sketch_id: str):
        self.current_tool = "revolve"
        self.lbl_title.setText("REVOLVE")
        self._clear_content()

        lbl_prof = QLabel("Profile:  1 Profile Selected")
        lbl_prof.setStyleSheet("color: #40a9ff; font-weight: 600; padding: 4px 0;")
        self.content_layout.addWidget(lbl_prof)

        # Axis
        self.content_layout.addWidget(self._create_row_label("Axis:"))
        self.combo_axis = self._create_combo(["Y Axis (Default)", "Z Axis", "X Axis"])
        self.content_layout.addWidget(self.combo_axis)

        # Angle
        self.content_layout.addWidget(self._create_row_label("Angle (°):"))
        self.txt_angle = self._create_expr_input("360.0 deg")
        self.content_layout.addWidget(self.txt_angle)

        # Operation
        self.content_layout.addWidget(self._create_row_label("Operation:"))
        self.combo_op = self._create_combo(["Join", "Cut", "New Body"])
        self.content_layout.addWidget(self.combo_op)

        self.extra_data = {"sketch_id": sketch_id}
        self.setVisible(True)

    def show_hole(self):
        self.current_tool = "hole"
        self.lbl_title.setText("HOLE")
        self._clear_content()

        self.content_layout.addWidget(self._create_row_label("Hole Type:"))
        self.combo_hole_type = self._create_combo(["Simple", "Counterbore", "Countersink"])
        self.content_layout.addWidget(self.combo_hole_type)

        self.content_layout.addWidget(self._create_row_label("Diameter (mm):"))
        self.txt_hole_dia = self._create_expr_input("8.0 mm")
        self.content_layout.addWidget(self.txt_hole_dia)

        self.content_layout.addWidget(self._create_row_label("Depth (mm):"))
        self.txt_hole_depth = self._create_expr_input("20.0 mm")
        self.content_layout.addWidget(self.txt_hole_depth)

        self.chk_through = QCheckBox("Through All")
        self.chk_through.setChecked(True)
        self.chk_through.setStyleSheet("color: #ffffff; padding: 4px 0;")
        self.content_layout.addWidget(self.chk_through)

        self.extra_data = {}
        self.setVisible(True)

    def show_fillet(self):
        self.current_tool = "fillet"
        self.lbl_title.setText("FILLET")
        self._clear_content()

        self.content_layout.addWidget(self._create_row_label("Type:"))
        self.combo_fillet_type = self._create_combo(["Constant Radius", "Chord Length"])
        self.content_layout.addWidget(self.combo_fillet_type)

        self.content_layout.addWidget(self._create_row_label("Radius (mm):"))
        self.txt_radius = self._create_expr_input("2.0 mm")
        self.content_layout.addWidget(self.txt_radius)

        self.extra_data = {}
        self.setVisible(True)

    def show_chamfer(self):
        self.current_tool = "chamfer"
        self.lbl_title.setText("CHAMFER")
        self._clear_content()

        self.content_layout.addWidget(self._create_row_label("Chamfer Type:"))
        self.combo_cham_type = self._create_combo(["Equal Distance", "Two Distances", "Distance and Angle"])
        self.content_layout.addWidget(self.combo_cham_type)

        self.content_layout.addWidget(self._create_row_label("Distance (mm):"))
        self.txt_cham_dist = self._create_expr_input("1.5 mm")
        self.content_layout.addWidget(self.txt_cham_dist)

        self.extra_data = {}
        self.setVisible(True)

    def show_shell(self):
        self.current_tool = "shell"
        self.lbl_title.setText("SHELL")
        self._clear_content()

        lbl_info = QLabel("Hollows out solid with uniform wall thickness")
        lbl_info.setStyleSheet("color: #40a9ff; font-size: 10px; padding-bottom: 4px;")
        self.content_layout.addWidget(lbl_info)

        self.content_layout.addWidget(self._create_row_label("Inside Thickness (mm):"))
        self.txt_shell_thick = self._create_expr_input("2.0 mm")
        self.content_layout.addWidget(self.txt_shell_thick)

        self.extra_data = {}
        self.setVisible(True)

    def show_combine(self):
        self.current_tool = "combine"
        self.lbl_title.setText("COMBINE")
        self._clear_content()

        self.content_layout.addWidget(self._create_row_label("Operation:"))
        self.combo_combine_op = self._create_combo(["Join", "Cut", "Intersect"])
        self.content_layout.addWidget(self.combo_combine_op)

        self.chk_keep_tools = QCheckBox("Keep Tools")
        self.chk_keep_tools.setStyleSheet("color: #ffffff; padding: 4px 0;")
        self.content_layout.addWidget(self.chk_keep_tools)

        self.extra_data = {}
        self.setVisible(True)

    def show_split_body(self):
        self.current_tool = "split_body"
        self.lbl_title.setText("SPLIT BODY")
        self._clear_content()

        self.content_layout.addWidget(self._create_row_label("Splitting Tool (Plane):"))
        self.combo_split_plane = self._create_combo(["XY Plane", "XZ Plane", "YZ Plane"])
        self.content_layout.addWidget(self.combo_split_plane)

        self.content_layout.addWidget(self._create_row_label("Plane Offset (mm):"))
        self.txt_split_offset = self._create_expr_input("0.0 mm")
        self.content_layout.addWidget(self.txt_split_offset)

        self.extra_data = {}
        self.setVisible(True)

    def show_mirror(self):
        self.current_tool = "mirror"
        self.lbl_title.setText("MIRROR")
        self._clear_content()

        self.content_layout.addWidget(self._create_row_label("Mirror Plane:"))
        self.combo_mirror_plane = self._create_combo(["XY Plane", "XZ Plane", "YZ Plane"])
        self.content_layout.addWidget(self.combo_mirror_plane)

        self.content_layout.addWidget(self._create_row_label("Operation:"))
        self.combo_mirror_op = self._create_combo(["Join", "New Body"])
        self.content_layout.addWidget(self.combo_mirror_op)

        self.extra_data = {}
        self.setVisible(True)

    def show_pattern_linear(self):
        self.current_tool = "pattern_linear"
        self.lbl_title.setText("RECTANGULAR PATTERN")
        self._clear_content()

        self.content_layout.addWidget(self._create_row_label("Direction 1 (X) Quantity:"))
        self.txt_pat_cx = self._create_expr_input("3")
        self.content_layout.addWidget(self.txt_pat_cx)

        self.content_layout.addWidget(self._create_row_label("Direction 1 (X) Distance (mm):"))
        self.txt_pat_sx = self._create_expr_input("25.0 mm")
        self.content_layout.addWidget(self.txt_pat_sx)

        self.content_layout.addWidget(self._create_row_label("Direction 2 (Y) Quantity:"))
        self.txt_pat_cy = self._create_expr_input("1")
        self.content_layout.addWidget(self.txt_pat_cy)

        self.content_layout.addWidget(self._create_row_label("Direction 2 (Y) Distance (mm):"))
        self.txt_pat_sy = self._create_expr_input("0.0 mm")
        self.content_layout.addWidget(self.txt_pat_sy)

        self.extra_data = {}
        self.setVisible(True)

    def show_pattern_circular(self):
        self.current_tool = "pattern_circular"
        self.lbl_title.setText("CIRCULAR PATTERN")
        self._clear_content()

        self.content_layout.addWidget(self._create_row_label("Axis:"))
        self.combo_circ_axis = self._create_combo(["Z Axis (Default)", "Y Axis", "X Axis"])
        self.content_layout.addWidget(self.combo_circ_axis)

        self.content_layout.addWidget(self._create_row_label("Quantity:"))
        self.txt_circ_cnt = self._create_expr_input("4")
        self.content_layout.addWidget(self.txt_circ_cnt)

        self.extra_data = {}
        self.setVisible(True)

    def show_box(self):
        self.current_tool = "box"
        self.lbl_title.setText("BOX")
        self._clear_content()

        self.content_layout.addWidget(self._create_row_label("Length / dx (mm):"))
        self.txt_box_dx = self._create_expr_input("30.0 mm")
        self.content_layout.addWidget(self.txt_box_dx)

        self.content_layout.addWidget(self._create_row_label("Width / dy (mm):"))
        self.txt_box_dy = self._create_expr_input("20.0 mm")
        self.content_layout.addWidget(self.txt_box_dy)

        self.content_layout.addWidget(self._create_row_label("Height / dz (mm):"))
        self.txt_box_dz = self._create_expr_input("15.0 mm")
        self.content_layout.addWidget(self.txt_box_dz)

        self.extra_data = {}
        self.setVisible(True)

    def show_cylinder(self):
        self.current_tool = "cylinder"
        self.lbl_title.setText("CYLINDER")
        self._clear_content()

        self.content_layout.addWidget(self._create_row_label("Radius (mm):"))
        self.txt_cyl_r = self._create_expr_input("10.0 mm")
        self.content_layout.addWidget(self.txt_cyl_r)

        self.content_layout.addWidget(self._create_row_label("Height (mm):"))
        self.txt_cyl_h = self._create_expr_input("25.0 mm")
        self.content_layout.addWidget(self.txt_cyl_h)

        self.extra_data = {}
        self.setVisible(True)

    # --- Actions ---

    def _on_confirm(self):
        if not self.current_tool:
            self.hide_panel()
            return

        params = dict(self.extra_data)

        if self.current_tool == "extrude":
            params["distance"] = self.txt_dist.text().strip()
            params["operation"] = self.combo_op.currentText().lower().replace(" ", "_")
        elif self.current_tool == "revolve":
            params["angle"] = self.txt_angle.text().strip()
            axis_txt = self.combo_axis.currentText()
            if "X" in axis_txt:
                params["axis_dir"] = (1.0, 0.0, 0.0)
            elif "Z" in axis_txt:
                params["axis_dir"] = (0.0, 0.0, 1.0)
            else:
                params["axis_dir"] = (0.0, 1.0, 0.0)
            params["operation"] = self.combo_op.currentText().lower().replace(" ", "_")
        elif self.current_tool == "hole":
            params["diameter"] = self.txt_hole_dia.text().strip()
            params["depth"] = self.txt_hole_depth.text().strip()
            params["through_all"] = self.chk_through.isChecked()
        elif self.current_tool == "fillet":
            params["radius"] = self.txt_radius.text().strip()
        elif self.current_tool == "chamfer":
            params["distance"] = self.txt_cham_dist.text().strip()
        elif self.current_tool == "shell":
            params["thickness"] = self.txt_shell_thick.text().strip()
        elif self.current_tool == "combine":
            params["operation"] = self.combo_combine_op.currentText().lower()
        elif self.current_tool == "split_body":
            plane_txt = self.combo_split_plane.currentText()
            params["plane"] = "XY" if "XY" in plane_txt else ("XZ" if "XZ" in plane_txt else "YZ")
            params["offset"] = self.txt_split_offset.text().strip()
        elif self.current_tool == "mirror":
            plane_txt = self.combo_mirror_plane.currentText()
            params["plane"] = "XY" if "XY" in plane_txt else ("XZ" if "XZ" in plane_txt else "YZ")
            params["operation"] = self.combo_mirror_op.currentText().lower().replace(" ", "_")
        elif self.current_tool == "pattern_linear":
            params["count_x"] = self.txt_pat_cx.text().strip()
            params["spacing_x"] = self.txt_pat_sx.text().strip()
            params["count_y"] = self.txt_pat_cy.text().strip()
            params["spacing_y"] = self.txt_pat_sy.text().strip()
        elif self.current_tool == "pattern_circular":
            params["count"] = self.txt_circ_cnt.text().strip()
        elif self.current_tool == "box":
            params["dx"] = self.txt_box_dx.text().strip()
            params["dy"] = self.txt_box_dy.text().strip()
            params["dz"] = self.txt_box_dz.text().strip()
        elif self.current_tool == "cylinder":
            params["radius"] = self.txt_cyl_r.text().strip()
            params["height"] = self.txt_cyl_h.text().strip()

        tool_name = self.current_tool
        self.hide_panel()
        self.confirmed.emit(tool_name, params)

    def _on_cancel(self):
        self.hide_panel()
        self.cancelled.emit()
