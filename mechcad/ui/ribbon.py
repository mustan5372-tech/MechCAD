"""
MechCAD Command Ribbon
Dense horizontal toolbar modeled on Autodesk Fusion 360's command ribbon.
Supports SOLID mode and contextual SKETCH mode.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QToolButton, QTabBar, QMenu, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QIcon

from mechcad.ui.theme import ThemeColors


class CommandRibbon(QWidget):
    """Dense horizontal command ribbon with tool groups and contextual tabs."""

    command_triggered = Signal(str)  # Tool name or identifier
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
        top_bar.setStyleSheet(f"background-color: {ThemeColors.BG_RIBBON}; border-bottom: 1px solid {ThemeColors.BORDER_SUBTLE};")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(8, 0, 8, 0)
        top_layout.setSpacing(12)

        # Workspace Dropdown: DESIGN
        self.ws_btn = QToolButton()
        self.ws_btn.setText("DESIGN ▾")
        self.ws_btn.setStyleSheet(f"font-weight: 700; color: #ffffff; padding: 6px 10px; font-size: 11px;")
        self.ws_menu = QMenu(self)
        self.ws_menu.addAction("Design (Active)")
        self.ws_menu.addAction("Generative Design (Planned)")
        self.ws_menu.addAction("Render (Planned)")
        self.ws_menu.addAction("Manufacture / CAM (Planned)")
        self.ws_menu.addAction("Drawing (2D Sheets)")
        self.ws_btn.setMenu(self.ws_menu)
        self.ws_btn.setPopupMode(QToolButton.InstantPopup)
        top_layout.addWidget(self.ws_btn)

        # Mode Tab Bar
        self.tab_bar = QTabBar()
        self.tab_bar.setObjectName("RibbonTabBar")
        self.tab_bar.addTab("SOLID")
        self.tab_bar.addTab("SURFACE")
        self.tab_bar.addTab("MESH")
        self.tab_bar.addTab("SHEET METAL")
        self.tab_bar.addTab("UTILITIES")
        self.tab_bar.currentChanged.connect(self._on_tab_changed)
        top_layout.addWidget(self.tab_bar)

        top_layout.addStretch()

        # Contextual Finish Sketch Button (Visible only during sketch mode)
        self.btn_finish_sketch = QToolButton()
        self.btn_finish_sketch.setObjectName("FinishSketchBtn")
        self.btn_finish_sketch.setText("✔ FINISH SKETCH")
        self.btn_finish_sketch.setToolTip("Exit Sketch Mode and Return to 3D Solid Modeling")
        self.btn_finish_sketch.clicked.connect(self.finish_sketch_requested.emit)
        self.btn_finish_sketch.setVisible(False)
        top_layout.addWidget(self.btn_finish_sketch)

        root_layout.addWidget(top_bar)

        # --- Bottom Row: Dense Command Panels ---
        self.panel_container = QWidget()
        self.panel_container.setStyleSheet(f"background-color: {ThemeColors.BG_RIBBON}; min-height: 64px; max-height: 68px;")
        self.panel_layout = QHBoxLayout(self.panel_container)
        self.panel_layout.setContentsMargins(6, 4, 6, 4)
        self.panel_layout.setSpacing(6)

        root_layout.addWidget(self.panel_container)

        self._build_solid_panels()

    def _create_panel_divider(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet(f"color: {ThemeColors.BORDER_SUBTLE};")
        return line

    def _create_group_box(self, title: str, tools: list) -> QWidget:
        box = QWidget()
        v_layout = QVBoxLayout(box)
        v_layout.setContentsMargins(2, 0, 2, 0)
        v_layout.setSpacing(2)

        # Top tools row
        h_tools = QHBoxLayout()
        h_tools.setContentsMargins(0, 0, 0, 0)
        h_tools.setSpacing(2)
        for t in tools:
            h_tools.addWidget(t)
        v_layout.addLayout(h_tools)

        # Bottom group label
        lbl = QLabel(title.upper())
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 9px; font-weight: 600; padding-top: 1px;")
        v_layout.addWidget(lbl)

        return box

    def _build_solid_panels(self):
        # Clear existing
        while self.panel_layout.count():
            item = self.panel_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 1. CREATE Group
        btn_sketch = QToolButton()
        btn_sketch.setText("✏\nCreate Sketch")
        btn_sketch.setToolTip("Create a new 2D sketch on a plane or face (L, R, C)")
        btn_sketch.clicked.connect(lambda: self.command_triggered.emit("create_sketch"))

        btn_extrude = QToolButton()
        btn_extrude.setText("⬆\nExtrude")
        btn_extrude.setToolTip("Extrude sketch profile into a 3D solid (E)")
        btn_extrude.clicked.connect(lambda: self.command_triggered.emit("extrude"))

        btn_revolve = QToolButton()
        btn_revolve.setText("🔄\nRevolve")
        btn_revolve.setToolTip("Revolve sketch profile around an axis")
        btn_revolve.clicked.connect(lambda: self.command_triggered.emit("revolve"))

        btn_hole = QToolButton()
        btn_hole.setText("🕳\nHole")
        btn_hole.setToolTip("Create a counterbore, countersink, or drilled hole (H)")
        btn_hole.clicked.connect(lambda: self.command_triggered.emit("hole"))

        # Primitives dropdown
        btn_prim = QToolButton()
        btn_prim.setText("📦\nPrimitives ▾")
        btn_prim.setPopupMode(QToolButton.InstantPopup)
        prim_menu = QMenu(self)
        prim_menu.addAction("Box...").triggered.connect(lambda: self.command_triggered.emit("prim_box"))
        prim_menu.addAction("Cylinder...").triggered.connect(lambda: self.command_triggered.emit("prim_cylinder"))
        prim_menu.addAction("Sphere...").triggered.connect(lambda: self.command_triggered.emit("prim_sphere"))
        prim_menu.addAction("Cone...").triggered.connect(lambda: self.command_triggered.emit("prim_cone"))
        prim_menu.addAction("Torus...").triggered.connect(lambda: self.command_triggered.emit("prim_torus"))
        prim_menu.addSeparator()
        prim_menu.addAction("Linear Pattern...").triggered.connect(lambda: self.command_triggered.emit("pattern_linear"))
        prim_menu.addAction("Circular Pattern...").triggered.connect(lambda: self.command_triggered.emit("pattern_circular"))
        btn_prim.setMenu(prim_menu)

        create_grp = self._create_group_box("Create", [btn_sketch, btn_extrude, btn_revolve, btn_hole, btn_prim])
        self.panel_layout.addWidget(create_grp)
        self.panel_layout.addWidget(self._create_panel_divider())

        # 2. MODIFY Group
        btn_fillet = QToolButton()
        btn_fillet.setText("⌒\nFillet")
        btn_fillet.setToolTip("Round interior or exterior solid edges (F)")
        btn_fillet.clicked.connect(lambda: self.command_triggered.emit("fillet"))

        btn_chamfer = QToolButton()
        btn_chamfer.setText("⊿\nChamfer")
        btn_chamfer.setToolTip("Apply a beveled edge to solid edges")
        btn_chamfer.clicked.connect(lambda: self.command_triggered.emit("chamfer"))

        btn_combine = QToolButton()
        btn_combine.setText("⚯\nCombine ▾")
        btn_combine.setPopupMode(QToolButton.InstantPopup)
        combine_menu = QMenu(self)
        combine_menu.addAction("Join (Boolean Union)").triggered.connect(lambda: self.command_triggered.emit("bool_fuse"))
        combine_menu.addAction("Cut (Boolean Subtract)").triggered.connect(lambda: self.command_triggered.emit("bool_cut"))
        combine_menu.addAction("Intersect (Common)").triggered.connect(lambda: self.command_triggered.emit("bool_intersect"))
        btn_combine.setMenu(combine_menu)

        modify_grp = self._create_group_box("Modify", [btn_fillet, btn_chamfer, btn_combine])
        self.panel_layout.addWidget(modify_grp)
        self.panel_layout.addWidget(self._create_panel_divider())

        # 3. CONSTRUCT Group
        btn_plane = QToolButton()
        btn_plane.setText("📐\nOffset Plane")
        btn_plane.setToolTip("Create a datum plane offset from a planar face or reference plane")
        btn_plane.clicked.connect(lambda: self.command_triggered.emit("construct_plane"))

        construct_grp = self._create_group_box("Construct", [btn_plane])
        self.panel_layout.addWidget(construct_grp)
        self.panel_layout.addWidget(self._create_panel_divider())

        # 4. INSPECT Group
        btn_measure = QToolButton()
        btn_measure.setText("📏\nMeasure")
        btn_measure.setToolTip("Measure distances, angles, radii, and bounding boxes (I)")
        btn_measure.clicked.connect(lambda: self.command_triggered.emit("measure"))

        inspect_grp = self._create_group_box("Inspect", [btn_measure])
        self.panel_layout.addWidget(inspect_grp)
        self.panel_layout.addWidget(self._create_panel_divider())

        # 5. INSERT Group
        btn_step = QToolButton()
        btn_step.setText("📥\nInsert STEP")
        btn_step.setToolTip("Import external standard STEP AP203/AP214 CAD file")
        btn_step.clicked.connect(lambda: self.command_triggered.emit("insert_step"))

        insert_grp = self._create_group_box("Insert", [btn_step])
        self.panel_layout.addWidget(insert_grp)

        self.panel_layout.addStretch()

    def _build_sketch_panels(self):
        # Clear existing
        while self.panel_layout.count():
            item = self.panel_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 1. CREATE Group
        btn_line = QToolButton()
        btn_line.setText("╱\nLine (L)")
        btn_line.setToolTip("Create sketch line segments (L)")
        btn_line.clicked.connect(lambda: self.command_triggered.emit("sketch_line"))

        btn_rect = QToolButton()
        btn_rect.setText("▭\n2-Pt Rect (R)")
        btn_rect.setToolTip("Create 2-point rectangle (R)")
        btn_rect.clicked.connect(lambda: self.command_triggered.emit("sketch_rect"))

        btn_crect = QToolButton()
        btn_crect.setText("⊞\nCenter Rect")
        btn_crect.setToolTip("Create center rectangle")
        btn_crect.clicked.connect(lambda: self.command_triggered.emit("sketch_center_rect"))

        btn_circle = QToolButton()
        btn_circle.setText("⚪\nCircle (C)")
        btn_circle.setToolTip("Create center-diameter circle (C)")
        btn_circle.clicked.connect(lambda: self.command_triggered.emit("sketch_circle"))

        btn_dim = QToolButton()
        btn_dim.setText("↔\nDimension (D)")
        btn_dim.setToolTip("Add length, distance, or diameter constraint (D)")
        btn_dim.clicked.connect(lambda: self.command_triggered.emit("sketch_dimension"))

        create_grp = self._create_group_box("Create", [btn_line, btn_rect, btn_crect, btn_circle, btn_dim])
        self.panel_layout.addWidget(create_grp)
        self.panel_layout.addWidget(self._create_panel_divider())

        # 2. CONSTRAINTS Group
        btn_c_coin = QToolButton()
        btn_c_coin.setText("⌖\nCoincident")
        btn_c_coin.setToolTip("Constrain two points together")
        btn_c_coin.clicked.connect(lambda: self.command_triggered.emit("constrain_coincident"))

        btn_c_h = QToolButton()
        btn_c_h.setText("━\nHorizontal")
        btn_c_h.setToolTip("Make line horizontal")
        btn_c_h.clicked.connect(lambda: self.command_triggered.emit("constrain_horizontal"))

        btn_c_v = QToolButton()
        btn_c_v.setText("┃\nVertical")
        btn_c_v.setToolTip("Make line vertical")
        btn_c_v.clicked.connect(lambda: self.command_triggered.emit("constrain_vertical"))

        btn_c_par = QToolButton()
        btn_c_par.setText("∥\nParallel")
        btn_c_par.setToolTip("Constrain two lines parallel")
        btn_c_par.clicked.connect(lambda: self.command_triggered.emit("constrain_parallel"))

        btn_c_perp = QToolButton()
        btn_c_perp.setText("⟂\nPerpendicular")
        btn_c_perp.setToolTip("Constrain two lines perpendicular")
        btn_c_perp.clicked.connect(lambda: self.command_triggered.emit("constrain_perpendicular"))

        btn_c_eq = QToolButton()
        btn_c_eq.setText("=\nEqual")
        btn_c_eq.setToolTip("Constrain equal length")
        btn_c_eq.clicked.connect(lambda: self.command_triggered.emit("constrain_equal"))

        btn_c_fix = QToolButton()
        btn_c_fix.setText("⚓\nFix/Lock")
        btn_c_fix.setToolTip("Lock point position")
        btn_c_fix.clicked.connect(lambda: self.command_triggered.emit("constrain_fix"))

        c_grp = self._create_group_box("Constraints", [btn_c_coin, btn_c_h, btn_c_v, btn_c_par, btn_c_perp, btn_c_eq, btn_c_fix])
        self.panel_layout.addWidget(c_grp)

        self.panel_layout.addStretch()

    def set_sketch_mode(self, active: bool):
        """Switches ribbon between SOLID modeling and contextual SKETCH mode."""
        self.is_sketch_active = active
        self.btn_finish_sketch.setVisible(active)
        if active:
            # Add or activate SKETCH tab
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
