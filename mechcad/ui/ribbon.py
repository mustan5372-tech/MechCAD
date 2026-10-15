"""
MechCAD Command Ribbon
Exact replica of Autodesk Fusion 360's command ribbon toolbar.
Features authentic tool groupings (CREATE, MODIFY, ASSEMBLE, CONSTRUCT, INSPECT, INSERT, SELECT),
vector CAD icons, and contextual SKETCH mode with prominent [✔ FINISH SKETCH] button.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QToolButton, QTabBar, QMenu, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QAction, QIcon, QFont

from mechcad.ui.theme import ThemeColors
from mechcad.ui.icons import CADIcons


class CommandRibbon(QWidget):
    """Dense horizontal command ribbon with Fusion 360 tool groups and contextual tabs."""

    command_triggered = Signal(str)  # Tool identifier
    finish_sketch_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CommandRibbon")
        self.is_sketch_active = False
        self.init_ui()

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # --- Top Row: Workspace Selector & Ribbon Mode Tabs ---
        top_bar = QWidget()
        top_bar.setStyleSheet(f"""
            QWidget {{
                background-color: #23272d;
                border-bottom: 1px solid #333842;
                min-height: 28px;
                max-height: 28px;
            }}
        """)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(8, 0, 8, 0)
        top_layout.setSpacing(10)

        # Workspace Dropdown: DESIGN
        self.ws_btn = QToolButton()
        self.ws_btn.setText("DESIGN ▾")
        self.ws_btn.setStyleSheet("""
            QToolButton {
                font-weight: 700;
                font-size: 11px;
                color: #ffffff;
                background-color: #1a1d21;
                border: 1px solid #3a414c;
                border-radius: 2px;
                padding: 3px 8px;
            }
            QToolButton:hover {
                background-color: #282f38;
                border-color: #0078d4;
            }
        """)
        self.ws_menu = QMenu(self)
        self.ws_menu.addAction("Design (Active)")
        self.ws_menu.addAction("Generative Design (Planned)")
        self.ws_menu.addAction("Render (Planned)")
        self.ws_menu.addAction("Manufacture / CAM (Planned)")
        self.ws_menu.addAction("Drawing (2D Sheets)")
        self.ws_btn.setMenu(self.ws_menu)
        self.ws_btn.setPopupMode(QToolButton.InstantPopup)
        top_layout.addWidget(self.ws_btn)

        # Mode Tab Bar (SOLID, SURFACE, MESH, SHEET METAL, PLASTIC, UTILITIES)
        self.tab_bar = QTabBar()
        self.tab_bar.setObjectName("RibbonTabBar")
        self.tab_bar.addTab("SOLID")
        self.tab_bar.addTab("SURFACE")
        self.tab_bar.addTab("MESH")
        self.tab_bar.addTab("SHEET METAL")
        self.tab_bar.addTab("UTILITIES")
        self.tab_bar.setStyleSheet("""
            QTabBar::tab {
                background-color: transparent;
                color: #8b939e;
                font-weight: 600;
                font-size: 11px;
                padding: 6px 14px;
                border: none;
            }
            QTabBar::tab:selected {
                color: #ffffff;
                border-bottom: 2px solid #0078d4;
            }
            QTabBar::tab:hover:!selected {
                color: #e0e6ed;
            }
        """)
        self.tab_bar.currentChanged.connect(self._on_tab_changed)
        top_layout.addWidget(self.tab_bar)

        top_layout.addStretch()

        # Contextual Finish Sketch Button (Visible only during sketch mode)
        self.btn_finish_sketch = QToolButton()
        self.btn_finish_sketch.setObjectName("FinishSketchBtn")
        self.btn_finish_sketch.setIcon(CADIcons.get("finish_sketch", 16))
        self.btn_finish_sketch.setIconSize(QSize(16, 16))
        self.btn_finish_sketch.setText(" FINISH SKETCH")
        self.btn_finish_sketch.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.btn_finish_sketch.setToolTip("Exit Sketch Mode and Return to 3D Solid Modeling (Enter / Esc)")
        self.btn_finish_sketch.setStyleSheet("""
            QToolButton {
                background-color: #107c41;
                color: #ffffff;
                font-weight: 700;
                font-size: 11px;
                padding: 3px 12px;
                border-radius: 3px;
                border: 1px solid #1f9455;
            }
            QToolButton:hover {
                background-color: #138a49;
                border-color: #40df85;
            }
        """)
        self.btn_finish_sketch.clicked.connect(self.finish_sketch_requested.emit)
        self.btn_finish_sketch.setVisible(False)
        top_layout.addWidget(self.btn_finish_sketch)

        root_layout.addWidget(top_bar)

        # --- Bottom Row: Dense Command Panels ---
        self.panel_container = QWidget()
        self.panel_container.setStyleSheet("""
            QWidget {
                background-color: #282c34;
                border-bottom: 1px solid #1e2227;
                min-height: 84px;
                max-height: 84px;
            }
        """)
        self.panel_layout = QHBoxLayout(self.panel_container)
        self.panel_layout.setContentsMargins(6, 2, 6, 2)
        self.panel_layout.setSpacing(4)

        root_layout.addWidget(self.panel_container)

        self._build_solid_panels()

    def _create_panel_divider(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Plain)
        line.setStyleSheet("color: #383e4a; margin: 4px 2px;")
        return line

    def _create_tool_button(self, icon_name: str, label: str, tooltip: str, cmd_id: str) -> QToolButton:
        btn = QToolButton()
        btn.setIcon(CADIcons.get(icon_name, 24))
        btn.setIconSize(QSize(24, 24))
        btn.setText(label)
        btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        btn.setToolTip(tooltip)
        btn.setFixedSize(52, 48)
        btn.setStyleSheet("""
            QToolButton {
                background-color: transparent;
                color: #e0e6ed;
                font-size: 9.5px;
                font-weight: 500;
                border: 1px solid transparent;
                border-radius: 3px;
                padding: 1px;
            }
            QToolButton:hover {
                background-color: #343a45;
                border: 1px solid #4a5363;
                color: #ffffff;
            }
            QToolButton:pressed {
                background-color: #0e639c;
                border: 1px solid #0078d4;
            }
        """)
        btn.clicked.connect(lambda: self.command_triggered.emit(cmd_id))
        return btn

    def _create_group_box(self, title: str, tools: list, menu_actions: list = None) -> QWidget:
        box = QWidget()
        v_layout = QVBoxLayout(box)
        v_layout.setContentsMargins(2, 2, 2, 2)
        v_layout.setSpacing(2)

        # Tools row
        h_tools = QHBoxLayout()
        h_tools.setContentsMargins(0, 0, 0, 0)
        h_tools.setSpacing(2)
        for t in tools:
            h_tools.addWidget(t)
        v_layout.addLayout(h_tools)

        # Bottom label with optional dropdown arrow
        lbl_btn = QToolButton()
        arrow_str = " ▾" if menu_actions else ""
        lbl_btn.setText(f"{title.upper()}{arrow_str}")
        lbl_btn.setFixedHeight(14)
        lbl_btn.setStyleSheet("""
            QToolButton {
                color: #8b939e;
                font-size: 8.5px;
                font-weight: 700;
                letter-spacing: 0.5px;
                background: transparent;
                border: none;
                padding: 0 2px;
            }
            QToolButton:hover {
                color: #ffffff;
            }
        """)
        if menu_actions:
            lbl_btn.setPopupMode(QToolButton.InstantPopup)
            m = QMenu(self)
            for act_name, cmd_id in menu_actions:
                if act_name == "---":
                    m.addSeparator()
                else:
                    m.addAction(act_name).triggered.connect(lambda _, c=cmd_id: self.command_triggered.emit(c))
            lbl_btn.setMenu(m)
        v_layout.addWidget(lbl_btn, alignment=Qt.AlignCenter)

        return box

    def _build_solid_panels(self):
        while self.panel_layout.count():
            item = self.panel_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 1. CREATE Group (Fusion 360 Parity)
        btn_sketch = self._create_tool_button("create_sketch", "Sketch", "Create a new 2D sketch on plane or face (L, R, C)", "create_sketch")
        btn_extrude = self._create_tool_button("extrude", "Extrude", "Extrude sketch profile into 3D solid (E)", "extrude")
        btn_revolve = self._create_tool_button("revolve", "Revolve", "Revolve sketch profile around an axis", "revolve")
        btn_hole = self._create_tool_button("hole", "Hole", "Create a drilled, counterbore, or countersink hole (H)", "hole")

        create_menu = [
            ("Box...", "prim_box"),
            ("Cylinder...", "prim_cylinder"),
            ("Sphere...", "prim_sphere"),
            ("Torus...", "prim_torus"),
            ("---", ""),
            ("Sweep Profile...", "sweep"),
            ("Loft Profiles...", "loft"),
            ("---", ""),
            ("Rectangular Pattern...", "pattern_linear"),
            ("Circular Pattern...", "pattern_circular"),
            ("Mirror...", "mirror"),
        ]
        create_grp = self._create_group_box("Create", [btn_sketch, btn_extrude, btn_revolve, btn_hole], create_menu)
        self.panel_layout.addWidget(create_grp)
        self.panel_layout.addWidget(self._create_panel_divider())

        # 2. MODIFY Group
        btn_press_pull = self._create_tool_button("extrude", "Press Pull", "Press Pull / Offset Faces (Q)", "extrude")
        btn_fillet = self._create_tool_button("fillet", "Fillet", "Round interior or exterior solid edges (F)", "fillet")
        btn_chamfer = self._create_tool_button("chamfer", "Chamfer", "Apply beveled mechanical edge (Chamfer)", "chamfer")
        btn_shell = self._create_tool_button("shell", "Shell", "Hollow out solid body with uniform wall thickness", "shell")
        btn_combine = self._create_tool_button("combine", "Combine", "Boolean Join, Cut, or Intersect solids", "combine")

        modify_menu = [
            ("Split Body...", "split_body"),
            ("Move / Copy...", "move"),
            ("Appearance / Material...", "appearance"),
        ]
        modify_grp = self._create_group_box("Modify", [btn_press_pull, btn_fillet, btn_chamfer, btn_shell, btn_combine], modify_menu)
        self.panel_layout.addWidget(modify_grp)
        self.panel_layout.addWidget(self._create_panel_divider())

        # 3. ASSEMBLE Group
        btn_comp = self._create_tool_button("extrude", "New Comp", "Create New Component", "new_component")
        btn_joint = self._create_tool_button("revolve", "Joint", "Create Mechanical Joint (J)", "joint")
        assemble_grp = self._create_group_box("Assemble", [btn_comp, btn_joint])
        self.panel_layout.addWidget(assemble_grp)
        self.panel_layout.addWidget(self._create_panel_divider())

        # 4. CONSTRUCT Group
        btn_plane = self._create_tool_button("construct_plane", "Offset Pln", "Create datum plane offset from face or plane", "construct_plane")
        construct_menu = [
            ("Plane at Angle...", "plane_angle"),
            ("Midplane...", "plane_mid"),
        ]
        construct_grp = self._create_group_box("Construct", [btn_plane], construct_menu)
        self.panel_layout.addWidget(construct_grp)
        self.panel_layout.addWidget(self._create_panel_divider())

        # 5. INSPECT Group
        btn_measure = self._create_tool_button("measure", "Measure", "Measure distances, angles, radii (I)", "measure")
        btn_params = self._create_tool_button("parameters", "Parameters", "Manage Model and User Parameters (fx)", "parameters")
        inspect_grp = self._create_group_box("Inspect", [btn_measure, btn_params])
        self.panel_layout.addWidget(inspect_grp)
        self.panel_layout.addWidget(self._create_panel_divider())

        # 6. INSERT Group
        btn_step = self._create_tool_button("save", "Insert STEP", "Import standard STEP AP203/AP214 Solid CAD file", "insert_step")
        insert_menu = [
            ("Insert STL Mesh...", "insert_stl"),
            ("Insert DXF Drawing...", "insert_dxf"),
        ]
        insert_grp = self._create_group_box("Insert", [btn_step], insert_menu)
        self.panel_layout.addWidget(insert_grp)

        self.panel_layout.addStretch()

    def _build_sketch_panels(self):
        while self.panel_layout.count():
            item = self.panel_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 1. CREATE Group (In-Canvas 2D Sketch Tools)
        btn_line = self._create_tool_button("sketch_line", "Line", "Create sketch line segments with live HUD (L)", "sketch_line")
        btn_rect = self._create_tool_button("sketch_rect", "2-Pt Rect", "Create 2-point rectangle with live dimensions (R)", "sketch_rect")
        btn_crect = self._create_tool_button("sketch_center_rect", "Center Rect", "Create rectangle from center point", "sketch_center_rect")
        btn_circle = self._create_tool_button("sketch_circle", "Circle", "Create center-diameter circle (C)", "sketch_circle")
        btn_dim = self._create_tool_button("sketch_dimension", "Dimension", "Add precise dimension constraint (D)", "sketch_dimension")

        create_menu = [
            ("Center Diameter Circle (C)", "sketch_circle"),
            ("3-Point Arc...", "sketch_arc"),
            ("Spline Curve...", "sketch_spline"),
            ("Point...", "sketch_point"),
        ]
        create_grp = self._create_group_box("Create", [btn_line, btn_rect, btn_crect, btn_circle, btn_dim], create_menu)
        self.panel_layout.addWidget(create_grp)
        self.panel_layout.addWidget(self._create_panel_divider())

        # 2. CONSTRAINTS Group
        btn_c_hv = self._create_tool_button("sketch_line", "Horiz/Vert", "Constrain line horizontal or vertical", "constrain_horizontal")
        btn_c_coin = self._create_tool_button("sketch_line", "Coincident", "Constrain points to coincide", "constrain_coincident")
        btn_c_par = self._create_tool_button("sketch_rect", "Parallel", "Constrain lines parallel", "constrain_parallel")
        btn_c_perp = self._create_tool_button("sketch_rect", "Perpend", "Constrain lines perpendicular", "constrain_perpendicular")
        btn_c_eq = self._create_tool_button("sketch_dimension", "Equal", "Constrain entities equal length", "constrain_equal")
        btn_c_fix = self._create_tool_button("solid_combine", "Fix/Lock", "Lock point position in place", "constrain_fix")

        c_grp = self._create_group_box("Constraints", [btn_c_hv, btn_c_coin, btn_c_par, btn_c_perp, btn_c_eq, btn_c_fix])
        self.panel_layout.addWidget(c_grp)
        self.panel_layout.addWidget(self._create_panel_divider())

        # 3. INSPECT Group
        btn_meas = self._create_tool_button("measure", "Measure", "Measure distances (I)", "measure")
        btn_fx = self._create_tool_button("parameters", "Parameters", "Manage Parameters (fx)", "parameters")
        inspect_grp = self._create_group_box("Inspect", [btn_meas, btn_fx])
        self.panel_layout.addWidget(inspect_grp)

        self.panel_layout.addStretch()

    def set_sketch_mode(self, active: bool):
        self.is_sketch_active = active
        self.btn_finish_sketch.setVisible(active)
        if active:
            if self.tab_bar.tabText(self.tab_bar.count() - 1) != "SKETCH":
                idx = self.tab_bar.addTab("SKETCH")
                self.tab_bar.setCurrentIndex(idx)
            else:
                self.tab_bar.setCurrentIndex(self.tab_bar.count() - 1)
            self._build_sketch_panels()
        else:
            if self.tab_bar.tabText(self.tab_bar.count() - 1) == "SKETCH":
                self.tab_bar.removeTab(self.tab_bar.count() - 1)
            self.tab_bar.setCurrentIndex(0)
            self._build_solid_panels()

    def _on_tab_changed(self, index: int):
        tab_text = self.tab_bar.tabText(index)
        if tab_text == "SKETCH":
            self._build_sketch_panels()
        else:
            self._build_solid_panels()
