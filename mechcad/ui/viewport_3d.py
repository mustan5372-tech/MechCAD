"""
MechCAD Interactive 3D OpenGL Viewport
Hardware-accelerated CAD canvas with Shaded with Visible Edges, ground grid, trihedron, and Fusion 360 navigation.
"""

import math
from typing import Optional, Tuple, List, Dict, Any
import numpy as np

from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import Qt, Signal, QPoint, QRect
from PySide6.QtGui import QMouseEvent, QWheelEvent, QColor, QPainter

from OpenGL.GL import *
from OpenGL.GLU import *

from mechcad.ui.theme import ThemeColors
from mechcad.ui.viewcube import ViewCube
from mechcad.ui.nav_bar import FloatingNavBar
from mechcad.kernel.occ_tessellator import OCCTessellator, ShapeTessellation
from mechcad.core.document import CADDocument
from mechcad.sketcher.sketch import Sketch


class Viewport3D(QOpenGLWidget):
    """Interactive 3D mechanical CAD viewport canvas."""

    cursor_moved = Signal(float, float, float)  # (x, y, z) in mm
    selection_changed = Signal(str, str)  # (type, id) e.g. ('body', 'body_1')

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

        # Camera state
        self.camera_target = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self.camera_dist: float = 180.0
        self.azimuth: float = 45.0      # Orbit angle around Z (deg)
        self.elevation: float = 30.0    # Pitch angle above XY (deg)
        self.fov: float = 45.0
        self.projection_mode: str = "perspective"  # 'perspective' or 'orthographic'
        self.display_style: str = "shaded_edges"   # 'shaded_edges', 'shaded', 'wireframe'
        self.show_grid: bool = True

        # Mouse interaction state
        self._last_mouse_pos = QPoint()
        self._active_nav_mode = "none"  # 'orbit', 'pan', 'zoom', 'none'
        self._temp_tool_override: Optional[str] = None

        # Rendered geometry
        self.tessellation: Optional[ShapeTessellation] = None
        self.active_sketch: Optional[Sketch] = None
        self.is_sketch_mode: bool = False
        self.selected_body: bool = False

        # Embedded HUD Overlays: ViewCube (Top-Right) & NavBar (Bottom-Center)
        self.viewcube = ViewCube(self)
        self.viewcube.view_selected.connect(self.set_standard_view)
        self.viewcube.orbit_delta.connect(self._on_viewcube_orbit)

        self.nav_bar = FloatingNavBar(self)
        self.nav_bar.nav_tool_triggered.connect(self._on_nav_tool_triggered)
        self.nav_bar.display_style_changed.connect(self._on_display_style_changed)
        self.nav_bar.grid_toggled.connect(self._on_grid_toggled)

    # --- Viewport Resizing & Child Overlay Layout ---

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        # Position ViewCube in top-right corner
        self.viewcube.move(w - self.viewcube.width() - 14, 14)
        # Position NavBar in bottom-center
        nb_w = self.nav_bar.width()
        self.nav_bar.move(int((w - nb_w) / 2.0), h - self.nav_bar.height() - 12)

    # --- OpenGL Pipeline Lifecycle ---

    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)

        # Smooth Shading & Lighting
        glShadeModel(GL_SMOOTH)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHT1)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

        # Key Light
        glLightfv(GL_LIGHT0, GL_POSITION, [1.0, 1.0, 2.0, 0.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.85, 0.85, 0.85, 1.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.25, 0.25, 0.25, 1.0])
        glLightfv(GL_LIGHT0, GL_SPECULAR, [0.4, 0.4, 0.4, 1.0])

        # Fill Light
        glLightfv(GL_LIGHT1, GL_POSITION, [-1.0, -1.0, 1.0, 0.0])
        glLightfv(GL_LIGHT1, GL_DIFFUSE, [0.35, 0.35, 0.35, 1.0])
        glLightfv(GL_LIGHT1, GL_AMBIENT, [0.1, 0.1, 0.1, 1.0])

        glEnable(GL_NORMALIZE)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)

    def paintGL(self):
        # 1. Background Gradient Clear
        glClearColor(0.14, 0.16, 0.18, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # 2. Setup Matrices
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        w, h = max(self.width(), 1), max(self.height(), 1)
        aspect = w / float(h)

        if self.projection_mode == "perspective":
            gluPerspective(self.fov, aspect, 1.0, 10000.0)
        else:
            ortho_size = self.camera_dist * 0.5
            glOrtho(-ortho_size * aspect, ortho_size * aspect, -ortho_size, ortho_size, -5000.0, 5000.0)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # Camera Orbit Transformation
        rad_az = math.radians(self.azimuth)
        rad_el = math.radians(self.elevation)
        cx = self.camera_target[0] + self.camera_dist * math.cos(rad_el) * math.sin(rad_az)
        cy = self.camera_target[1] - self.camera_dist * math.cos(rad_el) * math.cos(rad_az)
        cz = self.camera_target[2] + self.camera_dist * math.sin(rad_el)
        up_z = 1.0 if math.cos(rad_el) >= 0 else -1.0

        gluLookAt(cx, cy, cz,
                  self.camera_target[0], self.camera_target[1], self.camera_target[2],
                  0.0, 0.0, up_z)

        # 3. Render Ground Reference Grid
        if self.show_grid:
            self._render_grid()

        # 4. Render World Origin Trihedron
        self._render_trihedron()

        # 5. Render Active Sketch Geometry (if in sketch mode)
        if self.is_sketch_mode and self.active_sketch:
            self._render_sketch(self.active_sketch)

        # 6. Render 3D CAD Solid Geometry
        if self.tessellation and len(self.tessellation.vertices) > 0:
            self._render_solid()

    def _render_grid(self):
        glDisable(GL_LIGHTING)
        grid_size = max(int(self.camera_dist * 0.8), 60)
        step = 10.0  # 10 mm major grid spacing

        glLineWidth(1.0)
        glBegin(GL_LINES)
        for i in range(-grid_size, grid_size + 1, int(step)):
            if i == 0:
                continue
            glColor4f(0.25, 0.27, 0.30, 0.5)
            # Lines along X
            glVertex3f(-grid_size, i, 0.0)
            glVertex3f(grid_size, i, 0.0)
            # Lines along Y
            glVertex3f(i, -grid_size, 0.0)
            glVertex3f(i, grid_size, 0.0)

        # Origin Axes on grid
        # X Axis = Red
        glColor3f(0.88, 0.22, 0.22)
        glVertex3f(-grid_size, 0.0, 0.0)
        glVertex3f(grid_size, 0.0, 0.0)
        # Y Axis = Green
        glColor3f(0.20, 0.70, 0.28)
        glVertex3f(0.0, -grid_size, 0.0)
        glVertex3f(0.0, grid_size, 0.0)
        glEnd()
        glEnable(GL_LIGHTING)

    def _render_trihedron(self):
        glDisable(GL_LIGHTING)
        glLineWidth(2.5)
        axis_len = 15.0
        glBegin(GL_LINES)
        # X: Red
        glColor3f(0.9, 0.2, 0.2)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(axis_len, 0.0, 0.0)
        # Y: Green
        glColor3f(0.2, 0.8, 0.3)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(0.0, axis_len, 0.0)
        # Z: Blue
        glColor3f(0.1, 0.5, 0.9)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(0.0, 0.0, axis_len)
        glEnd()
        glEnable(GL_LIGHTING)

    def _render_solid(self):
        tess = self.tessellation
        if not tess:
            return

        verts = tess.vertices
        norms = tess.normals

        # A. Shaded Triangles
        if self.display_style in ("shaded_edges", "shaded"):
            glEnable(GL_LIGHTING)
            glEnable(GL_POLYGON_OFFSET_FILL)
            glPolygonOffset(1.0, 1.0)  # Prevents z-fighting with edges

            # Metallic Mechanical Grey surface color or Selection Blue
            if self.selected_body:
                glColor3f(0.15, 0.45, 0.85)
            else:
                glColor3f(0.60, 0.63, 0.66)

            glEnableClientState(GL_VERTEX_ARRAY)
            glEnableClientState(GL_NORMAL_ARRAY)
            glVertexPointer(3, GL_FLOAT, 0, verts)
            glNormalPointer(GL_FLOAT, 0, norms)
            glDrawArrays(GL_TRIANGLES, 0, len(verts))
            glDisableClientState(GL_NORMAL_ARRAY)
            glDisableClientState(GL_VERTEX_ARRAY)
            glDisable(GL_POLYGON_OFFSET_FILL)

        # B. Boundary Visible Mechanical Edges
        if self.display_style in ("shaded_edges", "wireframe") and len(tess.edge_lines) > 0:
            glDisable(GL_LIGHTING)
            glLineWidth(1.4)
            if self.selected_body:
                glColor3f(0.1, 0.2, 0.5)
            else:
                glColor3f(0.10, 0.10, 0.12)  # Crisp dark mechanical edges

            glEnableClientState(GL_VERTEX_ARRAY)
            glVertexPointer(3, GL_FLOAT, 0, tess.edge_lines)
            glDrawArrays(GL_LINES, 0, len(tess.edge_lines))
            glDisableClientState(GL_VERTEX_ARRAY)
            glEnable(GL_LIGHTING)

    def _render_sketch(self, sketch: Sketch):
        """Renders 2D sketch lines, points, and constraints in the 3D plane."""
        glDisable(GL_LIGHTING)
        glLineWidth(2.0)

        # Sketch curves: Green if solved, Cyan/Blue if underconstrained
        is_constrained = sketch.last_result and sketch.last_result.dof == 0
        if is_constrained:
            glColor3f(0.2, 0.8, 0.3)  # Constrained green
        else:
            glColor3f(0.25, 0.65, 0.95)  # Underconstrained cyan

        glBegin(GL_LINES)
        for line in sketch.lines.values():
            p1 = sketch.points.get(line.p1_id)
            p2 = sketch.points.get(line.p2_id)
            if p1 and p2:
                pt1 = sketch.map_to_3d(p1.u, p1.v)
                pt2 = sketch.map_to_3d(p2.u, p2.v)
                glVertex3f(pt1.X(), pt1.Y(), pt1.Z())
                glVertex3f(pt2.X(), pt2.Y(), pt2.Z())
        glEnd()

        # Sketch Points
        glPointSize(6.0)
        glColor3f(1.0, 0.8, 0.2)
        glBegin(GL_POINTS)
        for pt in sketch.points.values():
            p = sketch.map_to_3d(pt.u, pt.v)
            glVertex3f(p.X(), p.Y(), p.Z())
        glEnd()

        glEnable(GL_LIGHTING)

    # --- Document Geometry Update ---

    def update_model(self, doc: CADDocument):
        """Tessellates current solid and re-renders viewport."""
        if doc.current_solid is not None and not doc.current_solid.IsNull():
            self.tessellation = OCCTessellator.tessellate(doc.current_solid)
        else:
            self.tessellation = None
        self.update()

    def set_sketch(self, sketch: Optional[Sketch]):
        self.active_sketch = sketch
        self.is_sketch_mode = sketch is not None
        if self.is_sketch_mode and sketch:
            # Align camera normal to sketch plane
            if sketch.plane == "XY":
                self.azimuth, self.elevation = 0.0, 89.9
            elif sketch.plane == "XZ":
                self.azimuth, self.elevation = 0.0, 0.0
            elif sketch.plane == "YZ":
                self.azimuth, self.elevation = 90.0, 0.0
            self.viewcube.update_orientation(self.azimuth, self.elevation)
        self.update()

    # --- Camera Navigation & Standard Views ---

    def fit_all(self):
        """Fits viewport view to model bounding box."""
        if self.tessellation and self.tessellation.diagonal > 0:
            cx, cy, cz = self.tessellation.center
            self.camera_target = np.array([cx, cy, cz], dtype=np.float32)
            self.camera_dist = max(self.tessellation.diagonal * 1.8, 50.0)
        else:
            self.camera_target = np.array([0.0, 0.0, 0.0], dtype=np.float32)
            self.camera_dist = 160.0
        self.update()

    def set_standard_view(self, view_name: str):
        v = view_name.lower()
        if v == "front":
            self.azimuth, self.elevation = 0.0, 0.0
        elif v == "back":
            self.azimuth, self.elevation = 180.0, 0.0
        elif v == "top":
            self.azimuth, self.elevation = 0.0, 89.9
        elif v == "bottom":
            self.azimuth, self.elevation = 0.0, -89.9
        elif v == "right":
            self.azimuth, self.elevation = 90.0, 0.0
        elif v == "left":
            self.azimuth, self.elevation = 270.0, 0.0
        elif v == "home":
            self.azimuth, self.elevation = 45.0, 30.0
            self.fit_all()

        self.viewcube.update_orientation(self.azimuth, self.elevation)
        self.update()

    def _on_viewcube_orbit(self, d_az: float, d_el: float):
        self.azimuth = (self.azimuth + d_az) % 360.0
        self.elevation = max(-89.0, min(89.0, self.elevation + d_el))
        self.viewcube.update_orientation(self.azimuth, self.elevation)
        self.update()

    def _on_nav_tool_triggered(self, tool: str):
        if tool == "fit":
            self.fit_all()
        elif tool == "look_at":
            self.set_standard_view("top")
        else:
            self._temp_tool_override = tool

    def _on_display_style_changed(self, style: str):
        self.display_style = style
        self.update()

    def _on_grid_toggled(self, checked: bool):
        self.show_grid = checked
        self.update()

    # --- Mouse & Keyboard Event Handlers ---

    def mousePressEvent(self, event: QMouseEvent):
        self._last_mouse_pos = event.pos()

        # Determine navigation mode based on modifiers or active tool override
        is_shift = bool(event.modifiers() & Qt.ShiftModifier)
        is_ctrl = bool(event.modifiers() & Qt.ControlModifier)

        if event.button() == Qt.MiddleButton:
            if is_shift:
                self._active_nav_mode = "orbit"
            else:
                self._active_nav_mode = "pan"
        elif event.button() == Qt.LeftButton:
            if self._temp_tool_override:
                self._active_nav_mode = self._temp_tool_override
            elif is_shift:
                self._active_nav_mode = "orbit"
            else:
                # Left Click Selection
                self.selected_body = not self.selected_body
                self.selection_changed.emit("body", "body_1" if self.selected_body else "")
                self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = event.pos()
        dx = pos.x() - self._last_mouse_pos.x()
        dy = pos.y() - self._last_mouse_pos.y()
        self._last_mouse_pos = pos

        # Update cursor world coordinate readout
        rad_az = math.radians(self.azimuth)
        world_x = self.camera_target[0] + dx * 0.1 * math.sin(rad_az)
        world_y = self.camera_target[1] + dy * 0.1 * math.cos(rad_az)
        self.cursor_moved.emit(world_x, world_y, 0.0)

        if self._active_nav_mode == "orbit":
            self.azimuth = (self.azimuth + dx * 0.5) % 360.0
            self.elevation = max(-89.0, min(89.0, self.elevation - dy * 0.5))
            self.viewcube.update_orientation(self.azimuth, self.elevation)
            self.update()

        elif self._active_nav_mode == "pan":
            pan_speed = self.camera_dist * 0.0015
            rad_az = math.radians(self.azimuth)
            # Lateral movement along camera right vector
            right_x = math.cos(rad_az)
            right_y = math.sin(rad_az)
            self.camera_target[0] -= dx * pan_speed * right_x
            self.camera_target[1] -= dx * pan_speed * right_y
            # Vertical movement along camera up vector
            self.camera_target[2] += dy * pan_speed
            self.update()

        elif self._active_nav_mode == "zoom":
            factor = 1.0 - dy * 0.01
            self.camera_dist = max(5.0, min(10000.0, self.camera_dist * factor))
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._active_nav_mode = "none"
        self._temp_tool_override = None

    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y()
        zoom_factor = 0.9 if delta > 0 else 1.1
        self.camera_dist = max(5.0, min(10000.0, self.camera_dist * zoom_factor))
        self.update()
