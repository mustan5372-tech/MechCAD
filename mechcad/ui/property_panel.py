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

    confirmed = Signal(str, dict)       # (tool_name, params)
    cancelled = Signal()
    preview_changed = Signal(str, dict) # (tool_name, params) for real-time in-canvas preview

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

        # Error notification banner
        self.lbl_error = QLabel()
        self.lbl_error.setStyleSheet("""
            QLabel {
                background-color: #3b1d1d;
                border: 1px solid #e04040;
                border-radius: 3px;
                color: #ff9b9b;
                font-size: 11px;
                font-weight: 600;
                padding: 6px 8px;
            }
        """)
        self.lbl_error.setWordWrap(True)
        self.lbl_error.setVisible(False)
        self.layout.addWidget(self.lbl_error)

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

    def show_error(self, message: str):
        self.lbl_error.setText(f"⚠ {message}")
        self.lbl_error.setVisible(True)

    def clear_error(self):
        self.lbl_error.setText("")
        self.lbl_error.setVisible(False)

    def hide_panel(self):
        self.clear_error()
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
        line.textChanged.connect(lambda _: self._emit_preview_delayed())
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
        combo.currentTextChanged.connect(lambda _: self._emit_preview_delayed())
        return combo

    def _emit_preview_delayed(self):
        if not self.current_tool:
            return
        params = self._get_current_params()
        self.preview_changed.emit(self.current_tool, params)

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
        self._emit_preview_delayed()

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
        self._emit_preview_delayed()

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
        self._emit_preview_delayed()

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
        self._emit_preview_delayed()

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
        self._emit_preview_delayed()

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
        self._emit_preview_delayed()

    def show_sphere(self):
        self.current_tool = "sphere"
        self.lbl_title.setText("SPHERE")
        self._clear_content()

        self.content_layout.addWidget(self._create_row_label("Radius (mm):"))
        self.txt_sph_r = self._create_expr_input("15.0 mm")
        self.content_layout.addWidget(self.txt_sph_r)

        self.content_layout.addWidget(self._create_row_label("Operation:"))
        self.combo_sph_op = self._create_combo(["New Body", "Join", "Cut", "Intersect"])
        self.content_layout.addWidget(self.combo_sph_op)

        self.extra_data = {}
        self.setVisible(True)
        self._emit_preview_delayed()

    def show_torus(self):
        self.current_tool = "torus"
        self.lbl_title.setText("TORUS")
        self._clear_content()

        self.content_layout.addWidget(self._create_row_label("Major Radius (mm):"))
        self.txt_torus_r1 = self._create_expr_input("20.0 mm")
        self.content_layout.addWidget(self.txt_torus_r1)

        self.content_layout.addWidget(self._create_row_label("Minor Radius (mm):"))
        self.txt_torus_r2 = self._create_expr_input("5.0 mm")
        self.content_layout.addWidget(self.txt_torus_r2)

        self.content_layout.addWidget(self._create_row_label("Operation:"))
        self.combo_torus_op = self._create_combo(["New Body", "Join", "Cut", "Intersect"])
        self.content_layout.addWidget(self.combo_torus_op)

        self.extra_data = {}
        self.setVisible(True)
        self._emit_preview_delayed()

    def show_cone(self):
        self.current_tool = "cone"
        self.lbl_title.setText("CONE")
        self._clear_content()

        self.content_layout.addWidget(self._create_row_label("Base Radius / r1 (mm):"))
        self.txt_cone_r1 = self._create_expr_input("15.0 mm")
        self.content_layout.addWidget(self.txt_cone_r1)

        self.content_layout.addWidget(self._create_row_label("Top Radius / r2 (mm):"))
        self.txt_cone_r2 = self._create_expr_input("5.0 mm")
        self.content_layout.addWidget(self.txt_cone_r2)

        self.content_layout.addWidget(self._create_row_label("Height (mm):"))
        self.txt_cone_h = self._create_expr_input("30.0 mm")
        self.content_layout.addWidget(self.txt_cone_h)

        self.content_layout.addWidget(self._create_row_label("Operation:"))
        self.combo_cone_op = self._create_combo(["New Body", "Join", "Cut", "Intersect"])
        self.content_layout.addWidget(self.combo_cone_op)

        self.extra_data = {}
        self.setVisible(True)
        self._emit_preview_delayed()

    def show_construct_plane(self):
        self.current_tool = "construct_plane"
        self.lbl_title.setText("OFFSET PLANE")
        self._clear_content()

        self.content_layout.addWidget(self._create_row_label("Base Plane:"))
        self.combo_cplane_base = self._create_combo(["XY Plane", "XZ Plane", "YZ Plane"])
        self.content_layout.addWidget(self.combo_cplane_base)

        self.content_layout.addWidget(self._create_row_label("Offset Distance (mm):"))
        self.txt_cplane_dist = self._create_expr_input("25.0 mm")
        self.content_layout.addWidget(self.txt_cplane_dist)

        self.extra_data = {"type": "offset"}
        self.setVisible(True)

    def show_plane_angle(self):
        self.current_tool = "plane_angle"
        self.lbl_title.setText("PLANE AT ANGLE")
        self._clear_content()

        self.content_layout.addWidget(self._create_row_label("Reference Plane:"))
        self.combo_pangle_base = self._create_combo(["XY Plane", "XZ Plane", "YZ Plane"])
        self.content_layout.addWidget(self.combo_pangle_base)

        self.content_layout.addWidget(self._create_row_label("Angle (deg):"))
        self.txt_pangle_val = self._create_expr_input("45.0 deg")
        self.content_layout.addWidget(self.txt_pangle_val)

        self.extra_data = {"type": "angle"}
        self.setVisible(True)

    def show_plane_mid(self):
        self.current_tool = "plane_mid"
        self.lbl_title.setText("MIDPLANE")
        self._clear_content()

        self.content_layout.addWidget(self._create_row_label("Plane 1:"))
        self.combo_pmid_1 = self._create_combo(["XY Plane", "XZ Plane", "YZ Plane"])
        self.content_layout.addWidget(self.combo_pmid_1)

        self.content_layout.addWidget(self._create_row_label("Plane 2 (Offset):"))
        self.txt_pmid_dist = self._create_expr_input("50.0 mm")
        self.content_layout.addWidget(self.txt_pmid_dist)

        self.extra_data = {"type": "midplane"}
        self.setVisible(True)

    def show_move(self):
        self.current_tool = "move"
        self.lbl_title.setText("MOVE / COPY")
        self._clear_content()

        self.content_layout.addWidget(self._create_row_label("Translate X / dx (mm):"))
        self.txt_move_dx = self._create_expr_input("0.0 mm")
        self.content_layout.addWidget(self.txt_move_dx)

        self.content_layout.addWidget(self._create_row_label("Translate Y / dy (mm):"))
        self.txt_move_dy = self._create_expr_input("0.0 mm")
        self.content_layout.addWidget(self.txt_move_dy)

        self.content_layout.addWidget(self._create_row_label("Translate Z / dz (mm):"))
        self.txt_move_dz = self._create_expr_input("0.0 mm")
        self.content_layout.addWidget(self.txt_move_dz)

        self.content_layout.addWidget(self._create_row_label("Rotate Z (deg):"))
        self.txt_move_rz = self._create_expr_input("0.0 deg")
        self.content_layout.addWidget(self.txt_move_rz)

        self.extra_data = {}
        self.setVisible(True)

    def show_sweep(self):
        self.current_tool = "sweep"
        self.lbl_title.setText("SWEEP")
        self._clear_content()

        self.content_layout.addWidget(self._create_row_label("Profile Sketch:"))
        self.combo_sweep_prof = self._create_combo(["Active Sketch", "Sketch 1", "Sketch 2"])
        self.content_layout.addWidget(self.combo_sweep_prof)

        self.content_layout.addWidget(self._create_row_label("Path Sketch (Spine):"))
        self.combo_sweep_path = self._create_combo(["Sketch 2", "Sketch 1", "Active Sketch"])
        self.content_layout.addWidget(self.combo_sweep_path)

        self.content_layout.addWidget(self._create_row_label("Operation:"))
        self.combo_sweep_op = self._create_combo(["New Body", "Join", "Cut"])
        self.content_layout.addWidget(self.combo_sweep_op)

        self.extra_data = {}
        self.setVisible(True)

    def show_loft(self):
        self.current_tool = "loft"
        self.lbl_title.setText("LOFT")
        self._clear_content()

        lbl_desc = QLabel("Select 2 or more closed profiles to transition smoothly.")
        lbl_desc.setStyleSheet("color: #40a9ff; font-size: 10px; padding-bottom: 4px;")
        self.content_layout.addWidget(lbl_desc)

        self.content_layout.addWidget(self._create_row_label("Profile 1:"))
        self.combo_loft_1 = self._create_combo(["Sketch 1", "Sketch 2", "Active Sketch"])
        self.content_layout.addWidget(self.combo_loft_1)

        self.content_layout.addWidget(self._create_row_label("Profile 2:"))
        self.combo_loft_2 = self._create_combo(["Sketch 2", "Sketch 1", "Active Sketch"])
        self.content_layout.addWidget(self.combo_loft_2)

        self.content_layout.addWidget(self._create_row_label("Operation:"))
        self.combo_loft_op = self._create_combo(["New Body", "Join", "Cut"])
        self.content_layout.addWidget(self.combo_loft_op)

        self.extra_data = {}
        self.setVisible(True)

    def show_appearance(self):
        self.current_tool = "appearance"
        self.lbl_title.setText("APPEARANCE / MATERIAL")
        self._clear_content()

        self.content_layout.addWidget(self._create_row_label("Material Preset:"))
        self.combo_mat = self._create_combo([
            "Steel - Polished (#E0E6ED)",
            "Aluminum - Anodized Blue (#0082C8)",
            "Brass - Brushed (#D4AF37)",
            "Copper - Matte (#B87333)",
            "Carbon Fiber - Dark (#22252A)",
            "Polymer - Safety Orange (#FF6600)",
        ])
        self.content_layout.addWidget(self.combo_mat)

        self.extra_data = {}
        self.setVisible(True)

    # --- Actions ---

    def _get_current_params(self) -> dict:
        if not self.current_tool:
            return {}
        params = dict(self.extra_data)
        try:
            if self.current_tool == "extrude":
                params["distance"] = self.txt_dist.text().strip()
                dir_txt = self.combo_dir.currentText()
                params["symmetric"] = (dir_txt == "Symmetric")
                params["direction_type"] = dir_txt
                params["taper_angle"] = self.txt_taper.text().strip()
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
            elif self.current_tool == "sphere":
                params["radius"] = self.txt_sph_r.text().strip()
                params["operation"] = self.combo_sph_op.currentText().lower().replace(" ", "_")
            elif self.current_tool == "torus":
                params["r_major"] = self.txt_torus_r1.text().strip()
                params["r_minor"] = self.txt_torus_r2.text().strip()
                params["operation"] = self.combo_torus_op.currentText().lower().replace(" ", "_")
            elif self.current_tool == "cone":
                params["r1"] = self.txt_cone_r1.text().strip()
                params["r2"] = self.txt_cone_r2.text().strip()
                params["height"] = self.txt_cone_h.text().strip()
                params["operation"] = self.combo_cone_op.currentText().lower().replace(" ", "_")
            elif self.current_tool == "construct_plane":
                bpl = self.combo_cplane_base.currentText()
                params["base_plane"] = "XY" if "XY" in bpl else ("XZ" if "XZ" in bpl else "YZ")
                params["offset"] = self.txt_cplane_dist.text().strip()
                params["type"] = "offset"
            elif self.current_tool == "plane_angle":
                bpl = self.combo_pangle_base.currentText()
                params["base_plane"] = "XY" if "XY" in bpl else ("XZ" if "XZ" in bpl else "YZ")
                params["angle"] = self.txt_pangle_val.text().strip()
                params["type"] = "angle"
            elif self.current_tool == "plane_mid":
                bpl = self.combo_pmid_1.currentText()
                params["base_plane"] = "XY" if "XY" in bpl else ("XZ" if "XZ" in bpl else "YZ")
                params["offset"] = str(float(self.txt_pmid_dist.text().replace("mm", "").strip()) / 2.0)
                params["type"] = "midplane"
            elif self.current_tool == "move":
                params["dx"] = self.txt_move_dx.text().strip()
                params["dy"] = self.txt_move_dy.text().strip()
                params["dz"] = self.txt_move_dz.text().strip()
                params["rz"] = self.txt_move_rz.text().strip()
            elif self.current_tool == "appearance":
                params["material"] = self.combo_mat.currentText()
        except Exception:
            pass
        return params

    # --- Actions ---

    def _on_confirm(self):
        if not self.current_tool:
            self.hide_panel()
            return

        params = self._get_current_params()
        tool_name = self.current_tool
        self.hide_panel()
        self.confirmed.emit(tool_name, params)

    def _on_cancel(self):
        self.hide_panel()
        self.cancelled.emit()
