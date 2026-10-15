"""
MechCAD Main Window
Assembles the complete Autodesk Fusion 360-replica mechanical CAD desktop application.
Focuses purely on high-precision 3D Parametric Modeling with exact Fusion 360 commands,
parameters, controls, shortcuts, in-canvas sketching, timeline history, and viewport HUD.
"""

import os
from typing import Optional
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QDockWidget, QFileDialog,
    QMessageBox, QSplitter
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent, QIcon, QPixmap

from mechcad.ui.theme import ThemeColors, FUSION_QSS
from mechcad.ui.app_header import AppHeader
from mechcad.ui.ribbon import CommandRibbon
from mechcad.ui.browser import ModelBrowser
from mechcad.ui.viewport_3d import Viewport3D
from mechcad.ui.property_panel import PropertyPanel
from mechcad.ui.sketch_palette import SketchPalette
from mechcad.ui.timeline import FeatureTimeline
from mechcad.ui.status_bar import StatusBar
from mechcad.ui.learning_panel import LearningPanel
from mechcad.ui.parameters_dialog import ParametersDialog
from mechcad.ui.shortcut_search import ShortcutSearchPopup
from mechcad.core.document import CADDocument
from mechcad.core.project_io import ProjectIO
from mechcad.kernel.occ_solid import SolidOperations
from mechcad.kernel.occ_export import CADExchange
from mechcad.learning.automotive_exercises import AutomotiveExercise


class MainWindow(QMainWindow):
    """Primary application window matching Fusion 360 workspace layout and workflow."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MechCAD - Professional 3D Parametric CAD")
        self.resize(1360, 850)
        self.setStyleSheet(FUSION_QSS)

        # Set Window Branding Icon
        proj_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        icon_path = os.path.join(proj_root, "assets", "branding", "mechcad.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Active Document & Modeling State
        self.doc = CADDocument("Untitled 1")
        self.active_sketch_id: Optional[str] = None
        self._pending_sketch_tool: Optional[str] = None
        self._editing_feature_id: Optional[str] = None
        self._shortcut_popup: Optional[ShortcutSearchPopup] = None

        self._setup_ui()
        self._connect_signals()

        # Initial refresh
        self._refresh_all()

    def _setup_ui(self):
        # Central Main Layout Container
        central_container = QWidget(self)
        self.setCentralWidget(central_container)
        main_vlayout = QVBoxLayout(central_container)
        main_vlayout.setContentsMargins(0, 0, 0, 0)
        main_vlayout.setSpacing(0)

        # 1. Top Application Header (Fusion 360 App Bar)
        self.header = AppHeader(self)
        main_vlayout.addWidget(self.header)

        # 2. Command Ribbon (SOLID & Contextual SKETCH Tabs)
        self.ribbon = CommandRibbon(self)
        main_vlayout.addWidget(self.ribbon)

        # 3. Viewport & Canvas Area (OpenGL 3D Canvas + ViewCube + Floating NavBar)
        self.viewport = Viewport3D(self)
        main_vlayout.addWidget(self.viewport, stretch=1)

        # 4. Parametric Feature Timeline (Bottom History Track)
        self.timeline = FeatureTimeline(self)
        main_vlayout.addWidget(self.timeline)

        # 5. Bottom Status Bar (Readouts & Diagnostics)
        self.status_bar = StatusBar(self)
        main_vlayout.addWidget(self.status_bar)

        # --- Dock Widgets ---

        # Left Dock: Model Browser (Fusion 360 Hierarchy)
        self.dock_browser = QDockWidget(self)
        self.dock_browser.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.dock_browser.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.dock_browser.setTitleBarWidget(QWidget())
        self.browser = ModelBrowser(self.dock_browser)
        self.dock_browser.setWidget(self.browser)
        self.dock_browser.setMinimumWidth(255)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_browser)

        # Right Dock: Contextual Parameters Palette
        self.dock_properties = QDockWidget(self)
        self.dock_properties.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        self.dock_properties.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.dock_properties.setTitleBarWidget(QWidget())
        self.property_panel = PropertyPanel(self.dock_properties)
        self.dock_properties.setWidget(self.property_panel)
        self.dock_properties.setMinimumWidth(280)
        self.dock_properties.setVisible(False)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_properties)

        # Learning Panel Dock
        self.dock_learning = QDockWidget("Automobile Engineering Tutorials", self)
        self.dock_learning.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        self.dock_learning.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.learning_panel = LearningPanel(self.dock_learning)
        self.dock_learning.setWidget(self.learning_panel)
        self.dock_learning.setMinimumWidth(320)
        self.dock_learning.setVisible(False)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_learning)

        # Floating Sketch Palette on Viewport
        self.sketch_palette = SketchPalette(self.viewport)
        self.sketch_palette.look_at_requested.connect(lambda: self.viewport._on_nav_tool_triggered("look_at"))
        self.sketch_palette.setVisible(False)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "sketch_palette") and hasattr(self, "viewport"):
            self.sketch_palette.move(self.viewport.width() - self.sketch_palette.width() - 16, 50)

    def _toggle_data_panel(self):
        self.dock_browser.setVisible(not self.dock_browser.isVisible())

    def _on_browser_visibility_toggled(self, item_type: str, item_id: str, is_visible: bool):
        if item_type in ("body", "bodies"):
            self.viewport.show_body = is_visible
        elif item_type in ("sketch", "sketches"):
            self.viewport.show_sketches = is_visible
        elif item_type == "origin":
            self.viewport.show_origin = is_visible
        elif item_type == "construction":
            if item_id == "root":
                self.viewport.show_construction = is_visible
            elif hasattr(self.doc, "construction_planes") and item_id in self.doc.construction_planes:
                self.doc.construction_planes[item_id]["is_visible"] = is_visible
        self.viewport.update()

    def _on_sketch_selection_changed(self):
        pts = len(self.viewport.selected_sketch_points)
        lines = len(self.viewport.selected_sketch_lines)
        circs = len(self.viewport.selected_sketch_circles)
        parts = []
        if pts: parts.append(f"{pts} Point{'s' if pts > 1 else ''}")
        if lines: parts.append(f"{lines} Line{'s' if lines > 1 else ''}")
        if circs: parts.append(f"{circs} Circle{'s' if circs > 1 else ''}")
        msg = f"Sketch Selection: {', '.join(parts)}" if parts else "Sketch Active"
        self.status_bar.set_selection_info(msg)

    def _connect_signals(self):
        # Header actions
        self.header.file_action_triggered.connect(self._handle_file_action)
        self.header.undo_triggered.connect(self._handle_undo)
        self.header.redo_triggered.connect(self._handle_redo)
        self.header.new_tab_requested.connect(self._new_design)
        self.header.tab_close_requested.connect(lambda idx: self._new_design())
        self.header.learning_toggled.connect(self._toggle_learning_mode)
        self.header.parameters_requested.connect(self._open_parameters_dialog)
        self.header.shortcuts_requested.connect(self._open_shortcuts_popup)
        self.header.btn_data_panel.clicked.connect(self._toggle_data_panel)

        # Ribbon actions
        self.ribbon.command_triggered.connect(self._handle_ribbon_command)
        self.ribbon.finish_sketch_requested.connect(self._finish_sketch)

        # Viewport signals
        self.viewport.cursor_moved.connect(self.status_bar.set_coordinates)
        self.viewport.selection_changed.connect(self._on_viewport_selection)
        self.viewport.sketch_selection_changed.connect(self._on_sketch_selection_changed)
        self.viewport.plane_picked.connect(self._create_new_sketch)
        self.viewport.sketch_modified.connect(self._on_sketch_geometry_modified)
        self.viewport.command_requested.connect(self._handle_ribbon_command)

        # Browser signals
        self.browser.item_selected.connect(self._on_browser_selection)
        self.browser.visibility_toggled.connect(self._on_browser_visibility_toggled)
        self.browser.edit_sketch_requested.connect(self._edit_sketch)
        self.browser.create_sketch_requested.connect(self._create_new_sketch)
        self.browser.delete_item_requested.connect(self._delete_item)

        # Timeline signals
        self.timeline.rollback_changed.connect(self._on_rollback_changed)
        self.timeline.feature_edit_requested.connect(self._edit_feature)
        self.timeline.feature_suppress_requested.connect(self._toggle_feature_suppression)
        self.timeline.feature_delete_requested.connect(self._delete_feature)

        # Property panel signals
        self.property_panel.preview_changed.connect(self._on_property_preview_changed)
        self.property_panel.confirmed.connect(self._on_property_confirmed)
        self.property_panel.cancelled.connect(self._on_property_cancelled)

        # Learning panel signals
        self.learning_panel.load_model_requested.connect(self._load_learning_exercise)

    # --- UI Refresh Pipeline ---

    def _refresh_all(self):
        """Updates viewport, browser, timeline, and status bar from current document state."""
        self.viewport.update_model(self.doc)
        self.browser.refresh(self.doc)
        self.timeline.refresh(self.doc.history)
        self.header.set_tab_title(0, self.doc.name, self.doc.is_dirty)

        # Update status bar selection & measurements
        if self.doc.current_solid is not None and not self.doc.current_solid.IsNull():
            dx, dy, dz = SolidOperations.get_bounding_dimensions(self.doc.current_solid)
            self.status_bar.set_selection_info(f"1 Solid Body  ({dx:.1f} × {dy:.1f} × {dz:.1f} mm)")
        else:
            self.status_bar.set_selection_info("Ready (Empty Workspace)")

        # Update solver diagnostics if in sketch mode
        if self.active_sketch_id:
            sk = self.doc.get_sketch(self.active_sketch_id)
            if sk and sk.last_result:
                res = sk.last_result
                self.status_bar.set_solver_status(res.success, res.dof, res.message)

    # --- Document & File Actions ---

    def _new_design(self):
        self.doc = CADDocument("Untitled 1")
        self.active_sketch_id = None
        self.ribbon.set_sketch_mode(False)
        self.viewport.set_sketch(None)
        self.dock_properties.setVisible(False)
        self._refresh_all()

    def _handle_file_action(self, action: str):
        if action == "new":
            self._new_design()
        elif action == "open":
            path, _ = QFileDialog.getOpenFileName(self, "Open MechCAD Project", "", "MechCAD Files (*.mcad);;All Files (*.*)")
            if path:
                try:
                    self.doc = ProjectIO.open_project(path)
                    self._refresh_all()
                except Exception as e:
                    QMessageBox.critical(self, "Open Error", f"Failed to open project:\n{e}")
        elif action in ("save", "save_as"):
            if action == "save" and self.doc.filepath:
                ProjectIO.save_project(self.doc, self.doc.filepath)
                self._refresh_all()
            else:
                path, _ = QFileDialog.getSaveFileName(self, "Save MechCAD Project", f"{self.doc.name}.mcad", "MechCAD Files (*.mcad)")
                if path:
                    ProjectIO.save_project(self.doc, path)
                    self._refresh_all()
        elif action == "export_step":
            if self.doc.current_solid is None or self.doc.current_solid.IsNull():
                QMessageBox.warning(self, "Export Warning", "No 3D solid model exists to export.")
                return
            path, _ = QFileDialog.getSaveFileName(self, "Export STEP Solid", f"{self.doc.name}.step", "STEP Files (*.step *.stp)")
            if path:
                try:
                    CADExchange.export_step(self.doc.current_solid, path)
                    QMessageBox.information(self, "Export Complete", f"Successfully exported solid to STEP:\n{path}")
                except Exception as e:
                    QMessageBox.critical(self, "Export Error", f"STEP export failed:\n{e}")
        elif action == "export_stl":
            if self.doc.current_solid is None or self.doc.current_solid.IsNull():
                QMessageBox.warning(self, "Export Warning", "No 3D solid model exists to export.")
                return
            path, _ = QFileDialog.getSaveFileName(self, "Export STL Mesh", f"{self.doc.name}.stl", "STL Files (*.stl)")
            if path:
                try:
                    CADExchange.export_stl(self.doc.current_solid, path)
                    QMessageBox.information(self, "Export Complete", f"Successfully exported 3D printing mesh to STL:\n{path}")
                except Exception as e:
                    QMessageBox.critical(self, "Export Error", f"STL export failed:\n{e}")
        elif action == "export_dxf":
            if not self.doc.sketches:
                QMessageBox.warning(self, "Export Warning", "No sketch exists to export as 2D DXF.")
                return
            path, _ = QFileDialog.getSaveFileName(self, "Export 2D DXF Drawing", f"{self.doc.name}.dxf", "DXF Files (*.dxf)")
            if path:
                try:
                    sk = list(self.doc.sketches.values())[0]
                    elems = []
                    for line in sk.lines.values():
                        p1 = sk.points.get(line.p1_id)
                        p2 = sk.points.get(line.p2_id)
                        if p1 and p2:
                            elems.append({"type": "line", "p1": (p1.u, p1.v), "p2": (p2.u, p2.v)})
                    CADExchange.export_dxf(elems, path)
                    QMessageBox.information(self, "Export Complete", f"Successfully exported 2D drawing to DXF:\n{path}")
                except Exception as e:
                    QMessageBox.critical(self, "Export Error", f"DXF export failed:\n{e}")
        elif action == "about":
            self._show_about_dialog()
        elif action == "exit":
            self.close()

    def _show_about_dialog(self):
        """Displays About MechCAD dialog with branding logo and technical specs."""
        from PySide6.QtWidgets import QDialog, QLabel, QPushButton
        dlg = QDialog(self)
        dlg.setWindowTitle("About MechCAD")
        dlg.setFixedSize(480, 500)
        dlg.setStyleSheet(f"""
            QDialog {{
                background-color: {ThemeColors.PANEL_BG};
                color: {ThemeColors.TEXT_MAIN};
            }}
            QLabel {{
                color: {ThemeColors.TEXT_MAIN};
                font-family: 'Segoe UI', sans-serif;
            }}
            QPushButton {{
                background-color: {ThemeColors.ACCENT_BLUE};
                color: #FFFFFF;
                border: none;
                border-radius: 3px;
                padding: 6px 20px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.HOVER_BLUE};
            }}
        """)
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(12)

        proj_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        logo_path = os.path.join(proj_root, "assets", "branding", "mechcad-emblem.png")
        if os.path.exists(logo_path):
            lbl_logo = QLabel()
            pix = QPixmap(logo_path).scaled(130, 130, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            lbl_logo.setPixmap(pix)
            lbl_logo.setAlignment(Qt.AlignCenter)
            layout.addWidget(lbl_logo)

        lbl_title = QLabel("MechCAD")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: 700; color: #FFFFFF;")
        lbl_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_title)

        lbl_sub = QLabel("Professional 3D Mechanical CAD & Parametric Modeling")
        lbl_sub.setStyleSheet(f"font-size: 11px; color: {ThemeColors.TEXT_MUTED};")
        lbl_sub.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_sub)

        info_text = (
            "<b>Version:</b> 1.0.0 (x64 Production Desktop)<br>"
            "<b>Geometry Kernel:</b> Open CASCADE Technology 7.8 (B-Rep Engine)<br>"
            "<b>2D Constraint Solver:</b> SolveSpace 2D Geometric Solver<br>"
            "<b>Graphics Pipeline:</b> Hardware Accelerated OpenGL 3D Viewport<br>"
            "<b>UI Architecture:</b> PySide6 (Qt for Python 6.12)<br><br>"
            "<b>Official Repository:</b> <a style='color: #0082c8;' href='https://github.com/mustan5372-tech/MechCAD'>github.com/mustan5372-tech/MechCAD</a><br>"
            "Copyright © 2026 MechCAD Contributors. All rights reserved."
        )
        lbl_info = QLabel(info_text)
        lbl_info.setOpenExternalLinks(True)
        lbl_info.setStyleSheet("font-size: 11px; line-height: 140%;")
        lbl_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_info)

        layout.addStretch()

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(dlg.accept)
        btn_box.addWidget(btn_close)
        btn_box.addStretch()
        layout.addLayout(btn_box)

        dlg.exec()

    def _handle_undo(self):
        if self.doc.undo():
            self._refresh_all()

    def _handle_redo(self):
        if self.doc.redo():
            self._refresh_all()

    def _toggle_learning_mode(self, checked: bool):
        self.dock_learning.setVisible(checked)

    # --- Fusion 360 Commands Dispatcher ---

    def _handle_ribbon_command(self, cmd: str):
        # 1. Sketch Creation & Finish
        if cmd == "create_sketch":
            self.viewport.start_plane_selection()
            self.status_bar.set_selection_info("Select a plane or planar face to begin sketch...")
        elif cmd == "finish_sketch":
            self._finish_sketch()

        # 2. 3D Features (Extrude, Revolve, Hole, Fillet, Chamfer, Shell, Combine, Primitives)
        elif cmd == "extrude":
            self._trigger_extrude()
        elif cmd == "revolve":
            self._trigger_revolve()
        elif cmd == "hole":
            if self.doc.current_solid is None:
                QMessageBox.information(self, "Hole", "Create a 3D solid first.")
                return
            self._editing_feature_id = None
            self.property_panel.show_hole()
            self.dock_properties.setVisible(True)
        elif cmd == "fillet":
            if self.doc.current_solid is None:
                QMessageBox.information(self, "Fillet", "Create a 3D solid first.")
                return
            self._editing_feature_id = None
            self.property_panel.show_fillet()
            self.dock_properties.setVisible(True)
        elif cmd == "chamfer":
            if self.doc.current_solid is None:
                QMessageBox.information(self, "Chamfer", "Create a 3D solid first.")
                return
            self._editing_feature_id = None
            self.property_panel.show_chamfer()
            self.dock_properties.setVisible(True)
        elif cmd == "shell":
            if self.doc.current_solid is None:
                QMessageBox.information(self, "Shell", "Create a 3D solid first.")
                return
            self._editing_feature_id = None
            self.property_panel.show_shell()
            self.dock_properties.setVisible(True)
        elif cmd in ("combine", "bool_fuse", "bool_cut", "bool_intersect"):
            self._editing_feature_id = None
            self.property_panel.show_combine()
            self.dock_properties.setVisible(True)
        elif cmd == "split_body":
            if self.doc.current_solid is None:
                QMessageBox.information(self, "Split Body", "Create a 3D solid first.")
                return
            self._editing_feature_id = None
            self.property_panel.show_split_body()
            self.dock_properties.setVisible(True)
        elif cmd == "mirror":
            if self.doc.current_solid is None:
                QMessageBox.information(self, "Mirror", "Create a 3D solid first.")
                return
            self._editing_feature_id = None
            self.property_panel.show_mirror()
            self.dock_properties.setVisible(True)
        elif cmd == "pattern_linear":
            if self.doc.current_solid is None:
                QMessageBox.information(self, "Pattern", "Create a 3D solid first.")
                return
            self._editing_feature_id = None
            self.property_panel.show_pattern_linear()
            self.dock_properties.setVisible(True)
        elif cmd == "pattern_circular":
            if self.doc.current_solid is None:
                QMessageBox.information(self, "Pattern", "Create a 3D solid first.")
                return
            self._editing_feature_id = None
            self.property_panel.show_pattern_circular()
            self.dock_properties.setVisible(True)
        elif cmd == "prim_box":
            self._editing_feature_id = None
            self.property_panel.show_box()
            self.dock_properties.setVisible(True)
        elif cmd == "prim_cylinder":
            self._editing_feature_id = None
            self.property_panel.show_cylinder()
            self.dock_properties.setVisible(True)
        elif cmd == "prim_sphere":
            self._editing_feature_id = None
            self.property_panel.show_sphere()
            self.dock_properties.setVisible(True)
        elif cmd == "prim_torus":
            self._editing_feature_id = None
            self.property_panel.show_torus()
            self.dock_properties.setVisible(True)
        elif cmd == "prim_cone":
            self._editing_feature_id = None
            self.property_panel.show_cone()
            self.dock_properties.setVisible(True)
        elif cmd == "construct_plane":
            self._editing_feature_id = None
            self.property_panel.show_construct_plane()
            self.dock_properties.setVisible(True)
        elif cmd == "plane_angle":
            self._editing_feature_id = None
            self.property_panel.show_plane_angle()
            self.dock_properties.setVisible(True)
        elif cmd == "plane_mid":
            self._editing_feature_id = None
            self.property_panel.show_plane_mid()
            self.dock_properties.setVisible(True)
        elif cmd == "move":
            if self.doc.current_solid is None:
                QMessageBox.information(self, "Move / Copy", "Create a 3D solid body first.")
                return
            self._editing_feature_id = None
            self.property_panel.show_move()
            self.dock_properties.setVisible(True)
        elif cmd == "sweep":
            self._editing_feature_id = None
            self.property_panel.show_sweep()
            self.dock_properties.setVisible(True)
        elif cmd == "loft":
            self._editing_feature_id = None
            self.property_panel.show_loft()
            self.dock_properties.setVisible(True)
        elif cmd == "appearance":
            self._editing_feature_id = None
            self.property_panel.show_appearance()
            self.dock_properties.setVisible(True)
        elif cmd == "parameters":
            self._open_parameters_dialog()
        elif cmd in ("measure", "inspect"):
            if self.doc.current_solid is not None and not self.doc.current_solid.IsNull():
                dx, dy, dz = SolidOperations.get_bounding_dimensions(self.doc.current_solid)
                counts = SolidOperations.count_topology(self.doc.current_solid)
                info = (
                    f"Solid Bounding Extents:\n"
                    f"  dx = {dx:.3f} mm\n  dy = {dy:.3f} mm\n  dz = {dz:.3f} mm\n\n"
                    f"Topology:\n"
                    f"  Faces: {counts['faces']}\n"
                    f"  Edges: {counts['edges']}\n"
                    f"  Vertices: {counts['vertices']}"
                )
                QMessageBox.information(self, "Inspect Measure", info)
            else:
                QMessageBox.information(self, "Inspect Measure", "No solid body selected.")
        elif cmd == "insert_step":
            path, _ = QFileDialog.getOpenFileName(self, "Insert STEP Solid", "", "STEP Files (*.step *.stp)")
            if path:
                try:
                    imported_shape = CADExchange.import_step(path)
                    self.doc.push_undo_state()
                    self.doc.history.add_feature("box", {"dx": 1, "dy": 1, "dz": 1}, name="Imported STEP")
                    self.doc.current_solid = imported_shape
                    self._refresh_all()
                    self.viewport.fit_all()
                    self.status_bar.set_selection_info(f"Imported STEP: {os.path.basename(path)}")
                except Exception as e:
                    QMessageBox.critical(self, "Import Error", f"Failed to import STEP solid:\n{e}")
        elif cmd == "insert_stl":
            path, _ = QFileDialog.getOpenFileName(self, "Insert STL Mesh", "", "STL Files (*.stl)")
            if path:
                try:
                    imported_shape = CADExchange.import_stl(path)
                    self.doc.push_undo_state()
                    self.doc.history.add_feature("box", {"dx": 1, "dy": 1, "dz": 1}, name="Imported STL")
                    self.doc.current_solid = imported_shape
                    self._refresh_all()
                    self.viewport.fit_all()
                    self.status_bar.set_selection_info(f"Imported STL: {os.path.basename(path)}")
                except Exception as e:
                    QMessageBox.critical(self, "Import Error", f"Failed to import STL:\n{e}")
        elif cmd == "insert_dxf":
            path, _ = QFileDialog.getOpenFileName(self, "Insert DXF Drawing", "", "DXF Files (*.dxf)")
            if path:
                try:
                    lines = CADExchange.import_dxf(path)
                    if not self.active_sketch_id:
                        sk = self.doc.create_sketch(plane="XY")
                        self.active_sketch_id = sk.sketch_id
                        self.ribbon.set_sketch_mode(True)
                        self.viewport.set_sketch(sk)
                    else:
                        sk = self.doc.get_sketch(self.active_sketch_id)
                    for (u1, v1), (u2, v2) in lines:
                        p1_id = sk.add_point(u1, v1)
                        p2_id = sk.add_point(u2, v2)
                        sk.add_line(p1_id, p2_id)
                    sk.solve()
                    self._refresh_all()
                    self.viewport.fit_all()
                    self.status_bar.set_selection_info(f"Imported {len(lines)} DXF line segments.")
                except Exception as e:
                    QMessageBox.critical(self, "Import Error", f"Failed to import DXF:\n{e}")
        elif cmd == "new_component":
            QMessageBox.information(self, "New Component", "Active Root Component: Component 1 (Default B-Rep Body Model).")
        elif cmd == "joint":
            QMessageBox.information(self, "Joint", "Joint alignment active: Positioned to current solid coordinate frame.")

        # 3. In-Canvas 2D Sketch Tools
        elif cmd in ("sketch_line", "sketch_rect", "sketch_center_rect", "sketch_circle", "sketch_dimension", "sketch_arc", "sketch_point", "sketch_spline"):
            tool_name = cmd.replace("sketch_", "")
            if not self.active_sketch_id:
                # If not in sketch mode, start plane picker and queue tool
                self._pending_sketch_tool = tool_name
                self.viewport.start_plane_selection()
                self.status_bar.set_selection_info(f"Select plane to begin {tool_name.capitalize()}...")
            else:
                self.viewport.set_sketch_tool(tool_name)
                self.status_bar.set_selection_info(f"Sketch Tool: {tool_name.capitalize()} (Click canvas to draw)")

        elif cmd.startswith("constrain_"):
            self._handle_sketch_constraint(cmd)

    def _trigger_extrude(self):
        if not self.doc.sketches:
            QMessageBox.information(self, "Extrude", "Create a sketch profile first using 'Create Sketch' (L, R, C).")
            return
        sk_id = self.active_sketch_id or list(self.doc.sketches.keys())[-1]
        self._editing_feature_id = None
        self.property_panel.show_extrude(sk_id)
        self.dock_properties.setVisible(True)

    def _trigger_revolve(self):
        if not self.doc.sketches:
            QMessageBox.information(self, "Revolve", "Create a sketch profile first using 'Create Sketch' (L, R, C).")
            return
        sk_id = self.active_sketch_id or list(self.doc.sketches.keys())[-1]
        self._editing_feature_id = None
        self.property_panel.show_revolve(sk_id)
        self.dock_properties.setVisible(True)

    # --- Sketch Mode Workflow ---

    def _create_new_sketch(self, plane: str = "XY"):
        self.doc.push_undo_state()
        offset = 0.0
        base_plane = plane

        if hasattr(self.doc, "construction_planes") and plane in self.doc.construction_planes:
            cp = self.doc.construction_planes[plane]
            base_plane = cp.get("base_plane", "XY")
            offset = float(cp.get("offset", 0.0))

        sketch = self.doc.create_sketch(plane=base_plane, offset=offset)
        self.active_sketch_id = sketch.sketch_id

        # Switch to contextual sketch ribbon & viewport sketch mode
        self.ribbon.set_sketch_mode(True)
        self.viewport.set_sketch(sketch)
        if self._pending_sketch_tool:
            self.viewport.set_sketch_tool(self._pending_sketch_tool)
            self._pending_sketch_tool = None
        else:
            self.viewport.set_sketch_tool("line")

        if hasattr(self, "sketch_palette"):
            self.sketch_palette.move(self.viewport.width() - self.sketch_palette.width() - 16, 50)
            self.sketch_palette.setVisible(True)
            self.sketch_palette.raise_()

        self.status_bar.set_solver_status(True, 0, f"Sketch Active ({plane} Plane)")
        self._refresh_all()

    def _edit_sketch(self, sketch_id: str):
        sk = self.doc.get_sketch(sketch_id)
        if not sk:
            return
        self.active_sketch_id = sketch_id
        self.ribbon.set_sketch_mode(True)
        self.viewport.set_sketch(sk)
        if hasattr(self, "sketch_palette"):
            self.sketch_palette.move(self.viewport.width() - self.sketch_palette.width() - 16, 50)
            self.sketch_palette.setVisible(True)
            self.sketch_palette.raise_()
        self._refresh_all()

    def _on_sketch_geometry_modified(self):
        """Called when user interactively adds lines/rectangles/circles in the viewport."""
        self.doc.push_undo_state()
        if self.active_sketch_id:
            sk = self.doc.get_sketch(self.active_sketch_id)
            if sk and sk.last_result:
                self.status_bar.set_solver_status(sk.last_result.success, sk.last_result.dof, sk.last_result.message)
        self.browser.refresh(self.doc)
        self.viewport.update()

    def _finish_sketch(self):
        if self.active_sketch_id:
            sk = self.doc.get_sketch(self.active_sketch_id)
            if sk:
                res = sk.solve()
                self.status_bar.set_solver_status(res.success, res.dof, res.message)

        self.ribbon.set_sketch_mode(False)
        self.viewport.set_sketch(None)
        if hasattr(self, "sketch_palette"):
            self.sketch_palette.setVisible(False)
        self.active_sketch_id = None
        self.viewport.set_standard_view("home")
        self._refresh_all()

    def _handle_sketch_constraint(self, cmd: str):
        if not self.active_sketch_id:
            return
        sk = self.doc.get_sketch(self.active_sketch_id)
        if not sk:
            return

        self.doc.push_undo_state()
        c_name = cmd.replace("constrain_", "")

        sel_lines = list(self.viewport.selected_sketch_lines)
        sel_points = list(self.viewport.selected_sketch_points)

        if c_name in ("horizontal", "vertical"):
            if sel_lines:
                for lid in sel_lines:
                    sk.add_constraint(c_name, [lid])
            elif len(sel_points) >= 2:
                sk.add_constraint(c_name, sel_points[:2])
            elif sk.lines:
                lid = list(sk.lines.keys())[-1]
                sk.add_constraint(c_name, [lid])

        elif c_name == "fix":
            if sel_points:
                for pid in sel_points:
                    sk.add_constraint("fix", [pid])
            elif sel_lines:
                for lid in sel_lines:
                    sk.add_constraint("fix", [lid])
            elif sk.points:
                pid = list(sk.points.keys())[-1]
                sk.add_constraint("fix", [pid])

        elif c_name == "coincident":
            if len(sel_points) >= 2:
                sk.add_constraint("coincident", sel_points[:2])
            elif len(sk.points) >= 2:
                pids = list(sk.points.keys())[-2:]
                sk.add_constraint("coincident", pids)

        elif c_name in ("parallel", "perpendicular", "equal"):
            if len(sel_lines) >= 2:
                sk.add_constraint(c_name, sel_lines[:2])
            elif len(sk.lines) >= 2:
                lids = list(sk.lines.keys())[-2:]
                sk.add_constraint(c_name, lids)
            else:
                self.status_bar.set_selection_info(f"Select 2 lines to apply {c_name.capitalize()} constraint.")
                return

        res = sk.solve()
        self.status_bar.set_solver_status(res.success, res.dof, res.message)
        self._refresh_all()

    # --- Feature Execution & History ---

    def _on_property_confirmed(self, tool: str, params: dict):
        self.doc.push_undo_state()
        self.dock_properties.setVisible(False)
        self.viewport.set_preview_shape(None)

        if self._editing_feature_id:
            feat = self.doc.history.get_feature(self._editing_feature_id)
            if feat:
                feat.params.update(params)
            self._editing_feature_id = None
        else:
            self.doc.history.add_feature(tool, params)

        success, err = self.doc.recompute()
        if not success:
            QMessageBox.critical(self, "Feature Failed", f"Operation failed:\n{err}")

        self._refresh_all()
        self.viewport.fit_all()

    def _on_property_cancelled(self):
        self.dock_properties.setVisible(False)
        self._editing_feature_id = None
        self.viewport.set_preview_shape(None)

    def _on_property_preview_changed(self, tool: str, params: dict):
        """Generates live interactive B-Rep solid preview in the 3D viewport."""
        try:
            if tool == "extrude":
                sk_id = params.get("sketch_id") or self.active_sketch_id
                if not sk_id and self.doc.sketches:
                    sk_id = list(self.doc.sketches.keys())[-1]
                sk = self.doc.sketches.get(sk_id)
                if sk:
                    dist_raw = params.get("distance", 20.0)
                    dist_val = float(self.doc.parameters.get_value(dist_raw))
                    if abs(dist_val) > 1e-3:
                        direction = sk.get_plane_normal()
                        is_sym = bool(params.get("symmetric", False) or (params.get("direction_type") == "Symmetric"))
                        face = sk.to_occ_face()
                        preview_shape = SolidOperations.extrude_face(face, dist_val, direction, symmetric=is_sym)
                        self.viewport.set_preview_shape(preview_shape)
                        return
            elif tool == "box":
                l = float(self.doc.parameters.get_value(params.get("length", 50.0)))
                w = float(self.doc.parameters.get_value(params.get("width", 50.0)))
                h = float(self.doc.parameters.get_value(params.get("height", 50.0)))
                if l > 0 and w > 0 and h > 0:
                    preview_shape = SolidOperations.make_box(l, w, h)
                    self.viewport.set_preview_shape(preview_shape)
                    return
            elif tool == "cylinder":
                r = float(self.doc.parameters.get_value(params.get("radius", 25.0)))
                h = float(self.doc.parameters.get_value(params.get("height", 50.0)))
                if r > 0 and h > 0:
                    preview_shape = SolidOperations.make_cylinder(r, h)
                    self.viewport.set_preview_shape(preview_shape)
                    return
            elif tool == "fillet":
                if self.doc.current_solid is not None and not self.doc.current_solid.IsNull():
                    rad = float(self.doc.parameters.get_value(params.get("radius", 2.0)))
                    if rad > 0:
                        preview_shape = SolidOperations.make_fillet(self.doc.current_solid, rad)
                        self.viewport.set_preview_shape(preview_shape)
                        return
            elif tool == "chamfer":
                if self.doc.current_solid is not None and not self.doc.current_solid.IsNull():
                    dist = float(self.doc.parameters.get_value(params.get("distance", 2.0)))
                    if dist > 0:
                        preview_shape = SolidOperations.make_chamfer(self.doc.current_solid, dist)
                        self.viewport.set_preview_shape(preview_shape)
                        return
            elif tool == "sphere":
                rad = float(self.doc.parameters.get_value(params.get("radius", 25.0)))
                if rad > 0:
                    preview_shape = SolidOperations.make_sphere(rad)
                    self.viewport.set_preview_shape(preview_shape)
                    return
            elif tool == "torus":
                r1 = float(self.doc.parameters.get_value(params.get("r_major", params.get("r1", 30.0))))
                r2 = float(self.doc.parameters.get_value(params.get("r_minor", params.get("r2", 8.0))))
                if r1 > r2 and r2 > 0:
                    preview_shape = SolidOperations.make_torus(r1, r2)
                    self.viewport.set_preview_shape(preview_shape)
                    return
            elif tool == "cone":
                r1 = float(self.doc.parameters.get_value(params.get("r1", 20.0)))
                r2 = float(self.doc.parameters.get_value(params.get("r2", 5.0)))
                h = float(self.doc.parameters.get_value(params.get("height", 40.0)))
                if h > 0 and (r1 > 0 or r2 > 0):
                    preview_shape = SolidOperations.make_cone(r1, r2, h)
                    self.viewport.set_preview_shape(preview_shape)
                    return
        except Exception:
            pass
        self.viewport.set_preview_shape(None)

    def _toggle_feature_suppression(self, feature_id: str):
        for feat in self.doc.history.features:
            if feat.feature_id == feature_id:
                self.doc.push_undo_state()
                feat.is_suppressed = not feat.is_suppressed
                self.doc.recompute()
                self._refresh_all()
                status_str = "Suppressed" if feat.is_suppressed else "Unsuppressed"
                self.status_bar.set_selection_info(f"Feature '{feat.name}' {status_str}.")
                break

    def _edit_feature(self, feature_id: str):
        feat = self.doc.history.get_feature(feature_id)
        if not feat:
            return
        self._editing_feature_id = feature_id
        k = feat.kind
        p = feat.params

        if k == "extrude":
            sk_id = p.get("sketch_id", "")
            dist = float(self.doc.parameters.get_value(p.get("distance", 20.0)))
            self.property_panel.show_extrude(sk_id, default_dist=dist)
        elif k == "revolve":
            sk_id = p.get("sketch_id", "")
            self.property_panel.show_revolve(sk_id)
        elif k == "hole":
            self.property_panel.show_hole()
        elif k == "fillet":
            self.property_panel.show_fillet()
        elif k == "chamfer":
            self.property_panel.show_chamfer()
        elif k == "shell":
            self.property_panel.show_shell()
        elif k == "combine":
            self.property_panel.show_combine()
        elif k == "split_body":
            self.property_panel.show_split_body()
        elif k == "mirror":
            self.property_panel.show_mirror()
        elif k == "pattern_linear":
            self.property_panel.show_pattern_linear()
        elif k == "pattern_circular":
            self.property_panel.show_pattern_circular()
        elif k == "box":
            self.property_panel.show_box()
        elif k == "cylinder":
            self.property_panel.show_cylinder()
        elif k == "sphere":
            self.property_panel.show_sphere()
        elif k == "torus":
            self.property_panel.show_torus()
        elif k == "cone":
            self.property_panel.show_cone()
        elif k == "construct_plane":
            self.property_panel.show_construct_plane()
        elif k == "plane_angle":
            self.property_panel.show_plane_angle()
        elif k == "plane_mid":
            self.property_panel.show_plane_mid()
        elif k == "move":
            self.property_panel.show_move()
        elif k == "sweep":
            self.property_panel.show_sweep()
        elif k == "loft":
            self.property_panel.show_loft()
        elif k == "appearance":
            self.property_panel.show_appearance()

        self.dock_properties.setVisible(True)

    def _on_rollback_changed(self, new_index: int):
        self.doc.history.rollback_to(new_index)
        self.doc.recompute()
        self._refresh_all()

    def _delete_feature(self, feature_id: str):
        self.doc.push_undo_state()
        self.doc.history.delete_feature(feature_id)
        self.doc.recompute()
        self._refresh_all()

    def _delete_item(self, item_type: str, item_id: str):
        self.doc.push_undo_state()
        if item_type == "sketch" and item_id in self.doc.sketches:
            del self.doc.sketches[item_id]
            self.doc.recompute()
            self._refresh_all()
        elif item_type == "body":
            self.doc.current_solid = None
            self._refresh_all()

    def _on_viewport_selection(self, item_type: str, item_id: str):
        if item_type == "body" and item_id:
            if self.doc.current_solid is not None:
                dx, dy, dz = SolidOperations.get_bounding_dimensions(self.doc.current_solid)
                self.status_bar.set_selection_info(f"Selected: Body 1  ({dx:.2f} × {dy:.2f} × {dz:.2f} mm)")
        else:
            self.status_bar.set_selection_info("Ready")

    def _on_browser_selection(self, item_type: str, item_id: str):
        if item_type == "sketch":
            self.active_sketch_id = item_id
            self.status_bar.set_selection_info(f"Selected: {item_id}")
        elif item_type == "body":
            self.viewport.selected_body = True
            self.viewport.update()
            if self.doc.current_solid is not None:
                dx, dy, dz = SolidOperations.get_bounding_dimensions(self.doc.current_solid)
                self.status_bar.set_selection_info(f"Selected: Body 1  ({dx:.2f} × {dy:.2f} × {dz:.2f} mm)")

    # --- Fusion 360 Parameters & Shortcuts Dialogs ---

    def _open_parameters_dialog(self):
        dlg = ParametersDialog(self.doc.parameters, self)
        dlg.parameters_updated.connect(self._on_parameters_updated)
        dlg.exec()

    def _on_parameters_updated(self):
        self.doc.push_undo_state()
        self.doc.recompute()
        self._refresh_all()

    def _open_shortcuts_popup(self):
        if self._shortcut_popup is None:
            self._shortcut_popup = ShortcutSearchPopup(self)
            self._shortcut_popup.command_selected.connect(self._handle_ribbon_command)
        self._shortcut_popup.show_at_cursor()

    # --- Keyboard Shortcuts (Fusion 360 Parity) ---

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        ctrl = bool(event.modifiers() & Qt.ControlModifier)

        if ctrl and key == Qt.Key_Z:
            self._handle_undo()
            return
        elif ctrl and key == Qt.Key_Y:
            self._handle_redo()
            return
        elif ctrl and key == Qt.Key_S:
            self._handle_file_action("save")
            return
        elif ctrl and key == Qt.Key_N:
            self._new_design()
            return

        if key == Qt.Key_Escape:
            if self.dock_properties.isVisible():
                self._on_property_cancelled()
                return
            if self.viewport.plane_selection_mode:
                self.viewport.cancel_plane_selection()
                self.status_bar.set_selection_info("Ready")
                return
            if self.viewport.is_sketch_mode:
                self.viewport.set_sketch_tool("select")
                self.status_bar.set_selection_info("Sketch: Select mode")
                return
            self.viewport.selected_body = False
            self.viewport.update()
            self.status_bar.set_selection_info("Ready")
            return

        if key == Qt.Key_S:
            self._open_shortcuts_popup()
            return
        elif key == Qt.Key_L:
            self._handle_ribbon_command("sketch_line")
            return
        elif key == Qt.Key_R:
            self._handle_ribbon_command("sketch_rect")
            return
        elif key == Qt.Key_C:
            self._handle_ribbon_command("sketch_circle")
            return
        elif key == Qt.Key_D:
            self._handle_ribbon_command("sketch_dimension")
            return
        elif key == Qt.Key_E:
            self._trigger_extrude()
            return
        elif key == Qt.Key_F:
            self._handle_ribbon_command("fillet")
            return
        elif key == Qt.Key_H:
            self._handle_ribbon_command("hole")
            return
        elif key == Qt.Key_I:
            self._handle_ribbon_command("measure")
            return
        elif key == Qt.Key_F6:
            self.viewport.fit_all()
            return

        super().keyPressEvent(event)

    # --- Automobile Engineering Learning Mode ---

    def _load_learning_exercise(self, exercise: AutomotiveExercise):
        self.doc.push_undo_state()
        try:
            self.doc = exercise.build_model()
            self.active_sketch_id = None
            self.ribbon.set_sketch_mode(False)
            self.viewport.set_sketch(None)
            self._refresh_all()
            self.viewport.fit_all()
            self.status_bar.set_selection_info(f"Loaded: {exercise.title}")
        except Exception as e:
            QMessageBox.critical(self, "Loading Error", f"Failed to build learning exercise model:\n{e}")
