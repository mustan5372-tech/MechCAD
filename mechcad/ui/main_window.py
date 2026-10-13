"""
MechCAD Main Window
Assembles the complete Autodesk Fusion 360-style mechanical CAD desktop application.
"""

import os
from typing import Optional
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QDockWidget, QFileDialog, QMessageBox, QSplitter
)
from PySide6.QtCore import Qt

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
from mechcad.core.document import CADDocument
from mechcad.core.project_io import ProjectIO
from mechcad.kernel.occ_solid import SolidOperations
from mechcad.kernel.occ_export import CADExchange
from mechcad.learning.automotive_exercises import AutomotiveExercise


class MainWindow(QMainWindow):
    """Primary application window matching Fusion 360 workspace layout."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MechCAD — Learn. Design. Engineer.")
        self.resize(1280, 800)
        self.setStyleSheet(FUSION_QSS)

        # Active Document & State
        self.doc = CADDocument("Untitled 1")
        self.active_sketch_id: Optional[str] = None

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

        # 1. Top Application Header
        self.header = AppHeader(self)
        main_vlayout.addWidget(self.header)

        # 2. Command Ribbon
        self.ribbon = CommandRibbon(self)
        main_vlayout.addWidget(self.ribbon)

        # 3. Viewport & Canvas Area
        self.viewport = Viewport3D(self)
        main_vlayout.addWidget(self.viewport, stretch=1)

        # 4. Parametric Feature Timeline
        self.timeline = FeatureTimeline(self)
        main_vlayout.addWidget(self.timeline)

        # 5. Bottom Status Bar
        self.status_bar = StatusBar(self)
        main_vlayout.addWidget(self.status_bar)

        # --- Dock Widgets ---

        # Left Dock: Model Browser
        self.dock_browser = QDockWidget("Browser", self)
        self.dock_browser.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.dock_browser.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.browser = ModelBrowser(self.dock_browser)
        self.dock_browser.setWidget(self.browser)
        self.dock_browser.setMinimumWidth(230)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_browser)

        # Right Dock: Contextual Parameters & Learning Panel
        self.dock_properties = QDockWidget("Parameters", self)
        self.dock_properties.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        self.dock_properties.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.property_panel = PropertyPanel(self.dock_properties)
        self.dock_properties.setWidget(self.property_panel)
        self.dock_properties.setMinimumWidth(260)
        self.dock_properties.setVisible(False)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_properties)

        self.dock_learning = QDockWidget("Automobile Engineering Tutorials", self)
        self.dock_learning.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        self.dock_learning.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.learning_panel = LearningPanel(self.dock_learning)
        self.dock_learning.setWidget(self.learning_panel)
        self.dock_learning.setMinimumWidth(320)
        self.dock_learning.setVisible(False)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_learning)

    def _connect_signals(self):
        # Header actions
        self.header.file_action_triggered.connect(self._handle_file_action)
        self.header.undo_triggered.connect(self._handle_undo)
        self.header.redo_triggered.connect(self._handle_redo)
        self.header.new_tab_requested.connect(self._new_design)
        self.header.learning_toggled.connect(self._toggle_learning_mode)

        # Ribbon actions
        self.ribbon.command_triggered.connect(self._handle_ribbon_command)
        self.ribbon.finish_sketch_requested.connect(self._finish_sketch)

        # Viewport signals
        self.viewport.cursor_moved.connect(self.status_bar.set_coordinates)
        self.viewport.selection_changed.connect(self._on_viewport_selection)

        # Browser signals
        self.browser.item_selected.connect(self._on_browser_selection)
        self.browser.edit_sketch_requested.connect(self._edit_sketch)
        self.browser.delete_item_requested.connect(self._delete_item)

        # Timeline signals
        self.timeline.rollback_changed.connect(self._on_rollback_changed)
        self.timeline.feature_delete_requested.connect(self._delete_feature)

        # Property panel signals
        self.property_panel.confirmed.connect(self._on_property_confirmed)
        self.property_panel.cancelled.connect(lambda: self.dock_properties.setVisible(False))

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
        elif action == "exit":
            self.close()

    def _handle_undo(self):
        if self.doc.undo():
            self._refresh_all()

    def _handle_redo(self):
        if self.doc.redo():
            self._refresh_all()

    def _toggle_learning_mode(self, checked: bool):
        self.dock_learning.setVisible(checked)

    # --- Ribbon Command Dispatcher ---

    def _handle_ribbon_command(self, cmd: str):
        # 3D Solid Features
        if cmd == "create_sketch":
            self._create_new_sketch()
        elif cmd == "extrude":
            if not self.doc.sketches:
                QMessageBox.information(self, "Extrude", "Create a sketch profile first using 'Create Sketch'.")
                return
            sk_id = self.active_sketch_id or list(self.doc.sketches.keys())[-1]
            self.property_panel.show_extrude(sk_id)
            self.dock_properties.setVisible(True)
        elif cmd == "revolve":
            if not self.doc.sketches:
                QMessageBox.information(self, "Revolve", "Create a sketch profile first using 'Create Sketch'.")
                return
            sk_id = self.active_sketch_id or list(self.doc.sketches.keys())[-1]
            self.property_panel.show_revolve(sk_id)
            self.dock_properties.setVisible(True)
        elif cmd == "fillet":
            if self.doc.current_solid is None:
                QMessageBox.information(self, "Fillet", "Create a 3D solid first.")
                return
            self.property_panel.show_fillet()
            self.dock_properties.setVisible(True)
        elif cmd == "chamfer":
            if self.doc.current_solid is None:
                QMessageBox.information(self, "Chamfer", "Create a 3D solid first.")
                return
            self.property_panel.show_chamfer()
            self.dock_properties.setVisible(True)
        elif cmd == "hole":
            if self.doc.current_solid is None:
                QMessageBox.information(self, "Hole", "Create a 3D solid first.")
                return
            self.property_panel.show_hole()
            self.dock_properties.setVisible(True)
        elif cmd == "prim_box":
            self.property_panel.show_box()
            self.dock_properties.setVisible(True)
        elif cmd == "prim_cylinder":
            self.property_panel.show_cylinder()
            self.dock_properties.setVisible(True)
        elif cmd == "measure":
            if self.doc.current_solid is not None and not self.doc.current_solid.IsNull():
                dx, dy, dz = SolidOperations.get_bounding_dimensions(self.doc.current_solid)
                counts = SolidOperations.count_topology(self.doc.current_solid)
                info = f"Solid Bounding Extents:\n  dx = {dx:.3f} mm\n  dy = {dy:.3f} mm\n  dz = {dz:.3f} mm\n\nTopology:\n  Faces: {counts['faces']}\n  Edges: {counts['edges']}\n  Vertices: {counts['vertices']}"
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
                except Exception as e:
                    QMessageBox.critical(self, "Import Error", f"Failed to import STEP solid:\n{e}")

        # 2D Sketch Commands
        elif cmd.startswith("sketch_"):
            self._handle_sketch_primitive(cmd)
        elif cmd.startswith("constrain_"):
            self._handle_sketch_constraint(cmd)

    # --- Sketch Mode Workflow ---

    def _create_new_sketch(self, plane: str = "XY"):
        self.doc.push_undo_state()
        sketch = self.doc.create_sketch(plane=plane)
        self.active_sketch_id = sketch.sketch_id

        # Switch to contextual sketch ribbon & viewport sketch mode
        self.ribbon.set_sketch_mode(True)
        self.viewport.set_sketch(sketch)
        self.status_bar.set_solver_status(True, 0, "Sketch Created (XY Plane)")
        self._refresh_all()

    def _edit_sketch(self, sketch_id: str):
        sk = self.doc.get_sketch(sketch_id)
        if not sk:
            return
        self.active_sketch_id = sketch_id
        self.ribbon.set_sketch_mode(True)
        self.viewport.set_sketch(sk)
        self._refresh_all()

    def _finish_sketch(self):
        if self.active_sketch_id:
            sk = self.doc.get_sketch(self.active_sketch_id)
            if sk:
                res = sk.solve()
                self.status_bar.set_solver_status(res.success, res.dof, res.message)

        self.ribbon.set_sketch_mode(False)
        self.viewport.set_sketch(None)
        self.active_sketch_id = None
        self._refresh_all()

    def _handle_sketch_primitive(self, cmd: str):
        if not self.active_sketch_id:
            return
        sk = self.doc.get_sketch(self.active_sketch_id)
        if not sk:
            return

        self.doc.push_undo_state()
        if cmd == "sketch_rect":
            # 2-Point Rectangle 40 x 30 mm
            sk.add_rect(0.0, 0.0, 40.0, 30.0)
            sk.solve()
        elif cmd == "sketch_center_rect":
            # Center Rectangle 50 x 50 mm
            sk.add_center_rect(0.0, 0.0, 50.0, 50.0)
            sk.solve()
        elif cmd == "sketch_circle":
            # Circle dia 30 mm
            sk.add_circle(0.0, 0.0, 15.0)
            sk.solve()
        elif cmd == "sketch_line":
            p1 = sk.add_point(0.0, 0.0)
            p2 = sk.add_point(30.0, 0.0)
            sk.add_line(p1, p2)
            sk.solve()
        elif cmd == "sketch_dimension":
            # Dimension width & height
            if sk.lines:
                lid = list(sk.lines.keys())[0]
                sk.add_constraint("distance", [lid], 25.0)
                sk.solve()

        self._refresh_all()

    def _handle_sketch_constraint(self, cmd: str):
        if not self.active_sketch_id:
            return
        sk = self.doc.get_sketch(self.active_sketch_id)
        if not sk:
            return

        self.doc.push_undo_state()
        c_name = cmd.replace("constrain_", "")
        if c_name in ("horizontal", "vertical") and sk.lines:
            lid = list(sk.lines.keys())[0]
            sk.add_constraint(c_name, [lid])
        elif c_name == "fix" and sk.points:
            pid = list(sk.points.keys())[0]
            sk.add_constraint("fix", [pid])
        elif c_name == "coincident" and len(sk.points) >= 2:
            pids = list(sk.points.keys())[:2]
            sk.add_constraint("coincident", pids)

        sk.solve()
        self._refresh_all()

    # --- Feature Execution ---

    def _on_property_confirmed(self, tool: str, params: dict):
        self.doc.push_undo_state()
        self.dock_properties.setVisible(False)

        # Add feature to parametric history
        self.doc.history.add_feature(tool, params)
        success, err = self.doc.recompute()
        if not success:
            QMessageBox.critical(self, "Feature Failed", f"Operation failed:\n{err}")

        self._refresh_all()
        self.viewport.fit_all()

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

    def _on_viewport_selection(self, item_type: str, item_id: str):
        if item_type == "body" and item_id:
            if self.doc.current_solid is not None:
                dx, dy, dz = SolidOperations.get_bounding_dimensions(self.doc.current_solid)
                self.status_bar.set_selection_info(f"Selected: Body 1  (Extents: {dx:.2f} × {dy:.2f} × {dz:.2f} mm)")
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
