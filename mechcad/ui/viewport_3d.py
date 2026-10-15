"""
MechCAD Interactive 3D OpenGL Viewport
Autodesk Fusion 360-replica CAD canvas with:
- Origin plane picking mode ("Select a plane or planar face")
- In-canvas interactive sketch drawing: Line (L), 2-Pt Rect (R), Center Rect, Circle (C), Dimension (D)
- Heads-Up Display (HUD) dimension readouts next to cursor
- Point snapping (Origin, endpoints, horizontal/vertical alignment)
- Shaded closed sketch profiles (Fusion 360 translucent blue)
- In-canvas 3D extrude distance arrow manipulator
- Smooth camera controls: MMB pan, Shift+MMB orbit, Wheel zoom at cursor, double-click MMB fit
- Integrated ViewCube and Floating Navigation Bar
"""

import math
from typing import Optional, Tuple, List, Dict, Any
import numpy as np

from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import Qt, Signal, QPoint, QRect, QRectF, QTimer, QElapsedTimer
from PySide6.QtWidgets import QMenu, QInputDialog
from PySide6.QtGui import (
    QMouseEvent, QWheelEvent, QColor, QPainter, QFont, QPen, QBrush, QCursor, QKeyEvent
)

from OpenGL.GL import *
from OpenGL.GLU import *

from mechcad.ui.theme import ThemeColors
from mechcad.ui.viewcube import ViewCube
from mechcad.ui.nav_bar import FloatingNavBar
from mechcad.kernel.occ_tessellator import OCCTessellator, ShapeTessellation
from mechcad.core.document import CADDocument
from mechcad.sketcher.sketch import Sketch


class Viewport3D(QOpenGLWidget):
    """Interactive 3D mechanical CAD viewport canvas matching Fusion 360."""

    cursor_moved = Signal(float, float, float)  # (x, y, z) in mm
    selection_changed = Signal(str, str)        # (type, id) e.g. ('body', 'body_1')
    sketch_selection_changed = Signal()         # Emitted when sketch point/line/circle selection changes
    plane_picked = Signal(str)                  # 'XY', 'XZ', 'YZ' or construction plane id
    profile_selected = Signal(str)              # sketch_id
    sketch_modified = Signal()                  # Emitted after user adds sketch geometry
    extrude_dragged = Signal(float)             # Live distance in mm from in-canvas arrow
    command_requested = Signal(str)             # e.g. 'extrude', 'fillet', 'create_sketch' from marking menu

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
        self.projection_mode: str = "perspective"
        self.display_style: str = "shaded_edges"
        self.show_grid: bool = True

        # Visibility toggles (synchronized with browser eye icons)
        self.show_body: bool = True
        self.show_sketches: bool = True
        self.show_origin: bool = True
        self.show_construction: bool = True
        self.current_doc: Optional[CADDocument] = None

        # Navigation state
        self._last_mouse_pos = QPoint()
        self._active_nav_mode = "none"  # 'orbit', 'pan', 'zoom', 'none'
        self._temp_tool_override: Optional[str] = None

        # Mode States
        self.plane_selection_mode: bool = False
        self.hovered_plane: Optional[str] = None  # 'XY', 'XZ', 'YZ' or 'cplane_...'

        # In-Canvas Sketch Drawing State
        self.is_sketch_mode: bool = False
        self.active_sketch: Optional[Sketch] = None
        self.active_sketch_tool: str = "select"  # 'select', 'line', 'rect', 'center_rect', 'circle', 'dimension', 'point', 'arc'
        self._sketch_start_pt: Optional[Tuple[float, float]] = None
        self._sketch_current_pt: Optional[Tuple[float, float]] = None
        self._snap_pt: Optional[Tuple[float, float]] = None
        self._snap_type: str = "none"  # 'origin', 'point', 'axis_h', 'axis_v'

        # Interactive sketch entity selection sets
        self.selected_sketch_points = set()
        self.selected_sketch_lines = set()
        self.selected_sketch_circles = set()

        # Multi-point arc drawing state
        self._arc_pts = []

        # Rendered CAD geometry
        self.tessellation: Optional[ShapeTessellation] = None
        self.selected_body: bool = False

        # Live Feature Operation Preview Shape
        self.preview_shape = None
        self.preview_tessellation: Optional[ShapeTessellation] = None

        # Smooth Camera Transition Animator
        self._camera_anim_timer = QTimer(self)
        self._camera_anim_timer.setInterval(16)
        self._camera_anim_timer.timeout.connect(self._on_camera_anim_step)
        self._camera_anim_elapsed = QElapsedTimer()
        self._camera_anim_duration: int = 260
        self._anim_start_az: float = 45.0
        self._anim_start_el: float = 30.0
        self._anim_target_az: float = 45.0
        self._anim_target_el: float = 30.0
        self._anim_delta_az: float = 0.0
        self._anim_start_dist: float = 180.0
        self._anim_target_dist: float = 180.0
        self._anim_start_target = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self._anim_target_target = np.array([0.0, 0.0, 0.0], dtype=np.float32)

        # In-canvas 3D Extrude Arrow Manipulator
        self.show_extrude_arrow: bool = False
        self.extrude_arrow_dist: float = 20.0
        self._dragging_extrude_arrow: bool = False

        # HUD Overlay Widgets
        self.viewcube = ViewCube(self)
        self.viewcube.view_selected.connect(lambda v: self.set_standard_view(v, animated=True))
        self.viewcube.orbit_delta.connect(self._on_viewcube_orbit)
        self.viewcube.projection_toggled.connect(self.set_projection_mode)
        self.viewcube.fit_requested.connect(lambda: self.fit_all(animated=True))

        self.nav_bar = FloatingNavBar(self)
        self.nav_bar.nav_tool_triggered.connect(self._on_nav_tool_triggered)
        self.nav_bar.display_style_changed.connect(self._on_display_style_changed)
        self.nav_bar.grid_toggled.connect(self._on_grid_toggled)

    # --- Overlay Layout ---

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        self.viewcube.move(w - self.viewcube.width() - 14, 14)
        nb_w = self.nav_bar.width()
        self.nav_bar.move(int((w - nb_w) / 2.0), h - self.nav_bar.height() - 12)

    # --- OpenGL Initialization & Render Loop ---

    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Smooth Shading & Dual Mechanical Key/Fill Lighting
        glShadeModel(GL_SMOOTH)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHT1)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

        # Key Light (warm metallic highlight)
        glLightfv(GL_LIGHT0, GL_POSITION, [1.5, 1.2, 2.5, 0.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.88, 0.88, 0.88, 1.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.28, 0.28, 0.28, 1.0])
        glLightfv(GL_LIGHT0, GL_SPECULAR, [0.45, 0.45, 0.45, 1.0])

        # Fill Light (cool ambient)
        glLightfv(GL_LIGHT1, GL_POSITION, [-1.2, -1.5, 0.8, 0.0])
        glLightfv(GL_LIGHT1, GL_DIFFUSE, [0.35, 0.38, 0.42, 1.0])
        glLightfv(GL_LIGHT1, GL_AMBIENT, [0.12, 0.12, 0.14, 1.0])

        glEnable(GL_NORMALIZE)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)

    def paintGL(self):
        # 1. Clean Gradient Engineering Clear
        glClearColor(0.13, 0.15, 0.17, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # 2. Camera Matrices
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        w, h = max(self.width(), 1), max(self.height(), 1)
        aspect = w / float(h)

        if self.projection_mode == "perspective":
            gluPerspective(self.fov, aspect, 1.0, 20000.0)
        else:
            ortho_size = self.camera_dist * 0.5
            glOrtho(-ortho_size * aspect, ortho_size * aspect, -ortho_size, ortho_size, -10000.0, 10000.0)

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

        # 3. Reference Grid
        if self.show_grid:
            self._render_grid()

        # 4. Trihedron at World Origin
        if self.show_origin:
            self._render_trihedron()

        # 5. Origin Plane Tiles for "Create Sketch" selection
        if self.plane_selection_mode:
            self._render_origin_plane_tiles()

        # 5b. Construction Planes
        if self.show_construction:
            self._render_construction_planes()

        # 6. Render 3D CAD Solid Geometry
        if self.show_body and self.tessellation and len(self.tessellation.vertices) > 0:
            self._render_solid()

        # 6b. Render Live Feature Operation Preview Solid (if active)
        if self.preview_tessellation and len(self.preview_tessellation.vertices) > 0:
            self._render_preview_solid()

        # 7. Render Sketch Geometry & Shaded Profiles (if sketch active)
        if self.show_sketches and self.active_sketch:
            self._render_sketch(self.active_sketch)

        # 8. Render In-Canvas 3D Extrude Arrow Manipulator
        if self.show_extrude_arrow:
            self._render_extrude_arrow()

    def paintEvent(self, event):
        # OpenGL Render
        super().paintEvent(event)

        # 2D HUD Overlays on top of OpenGL Canvas
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # A. Plane Selection Mode Prompt
        if self.plane_selection_mode:
            self._draw_hud_plane_prompt(painter)

        # B. Live Sketch HUD: Dimension readouts, tool crosshairs, snapping badges
        if self.is_sketch_mode:
            self._draw_hud_sketch_info(painter)

        painter.end()

    # --- OpenGL Scene Elements ---

    def _render_grid(self):
        glDisable(GL_LIGHTING)
        grid_size = max(int(self.camera_dist * 0.8), 80)
        step = 10.0  # 10 mm major grid spacing

        glLineWidth(1.0)
        glBegin(GL_LINES)
        for i in range(-grid_size, grid_size + 1, int(step)):
            if i == 0:
                continue
            glColor4f(0.24, 0.27, 0.30, 0.45)
            # Lines along X
            glVertex3f(-grid_size, i, 0.0)
            glVertex3f(grid_size, i, 0.0)
            # Lines along Y
            glVertex3f(i, -grid_size, 0.0)
            glVertex3f(i, grid_size, 0.0)

        # Red X and Green Y Axes
        glColor3f(0.85, 0.22, 0.22)
        glVertex3f(-grid_size, 0.0, 0.0)
        glVertex3f(grid_size, 0.0, 0.0)

        glColor3f(0.22, 0.75, 0.30)
        glVertex3f(0.0, -grid_size, 0.0)
        glVertex3f(0.0, grid_size, 0.0)
        glEnd()
        glEnable(GL_LIGHTING)

    def _render_trihedron(self):
        glDisable(GL_LIGHTING)
        glLineWidth(2.2)
        axis_len = 16.0
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
        glColor3f(0.15, 0.55, 0.95)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(0.0, 0.0, axis_len)
        glEnd()
        glEnable(GL_LIGHTING)

    def _render_origin_plane_tiles(self):
        """Renders the 3 Fusion 360 origin work planes (XY, XZ, YZ) for sketch plane selection."""
        glDisable(GL_LIGHTING)
        sz = 35.0

        # XY Plane (Orange / Red-Green)
        is_hov_xy = (self.hovered_plane == "XY")
        glColor4f(0.95, 0.55, 0.15, 0.45 if is_hov_xy else 0.20)
        glBegin(GL_QUADS)
        glVertex3f(-sz, -sz, 0.0)
        glVertex3f(sz, -sz, 0.0)
        glVertex3f(sz, sz, 0.0)
        glVertex3f(-sz, sz, 0.0)
        glEnd()
        glLineWidth(2.0 if is_hov_xy else 1.0)
        glColor3f(1.0, 0.6, 0.1 if is_hov_xy else 0.4)
        glBegin(GL_LINE_LOOP)
        glVertex3f(-sz, -sz, 0.0)
        glVertex3f(sz, -sz, 0.0)
        glVertex3f(sz, sz, 0.0)
        glVertex3f(-sz, sz, 0.0)
        glEnd()

        # XZ Plane (Cyan / Red-Blue)
        is_hov_xz = (self.hovered_plane == "XZ")
        glColor4f(0.15, 0.65, 0.95, 0.45 if is_hov_xz else 0.20)
        glBegin(GL_QUADS)
        glVertex3f(-sz, 0.0, -sz)
        glVertex3f(sz, 0.0, -sz)
        glVertex3f(sz, 0.0, sz)
        glVertex3f(-sz, 0.0, sz)
        glEnd()
        glLineWidth(2.0 if is_hov_xz else 1.0)
        glColor3f(0.2, 0.7, 1.0 if is_hov_xz else 0.5)
        glBegin(GL_LINE_LOOP)
        glVertex3f(-sz, 0.0, -sz)
        glVertex3f(sz, 0.0, -sz)
        glVertex3f(sz, 0.0, sz)
        glVertex3f(-sz, 0.0, sz)
        glEnd()

        # YZ Plane (Green / Green-Blue)
        is_hov_yz = (self.hovered_plane == "YZ")
        glColor4f(0.20, 0.85, 0.45, 0.45 if is_hov_yz else 0.20)
        glBegin(GL_QUADS)
        glVertex3f(0.0, -sz, -sz)
        glVertex3f(0.0, sz, -sz)
        glVertex3f(0.0, sz, sz)
        glVertex3f(0.0, -sz, sz)
        glEnd()
        glLineWidth(2.0 if is_hov_yz else 1.0)
        glColor3f(0.3, 0.9, 0.5 if is_hov_yz else 0.4)
        glBegin(GL_LINE_LOOP)
        glVertex3f(0.0, -sz, -sz)
        glVertex3f(0.0, sz, -sz)
        glVertex3f(0.0, sz, sz)
        glVertex3f(0.0, -sz, sz)
        glEnd()

        glEnable(GL_LIGHTING)

    def _render_construction_planes(self):
        """Renders user-created construction datum planes with amber translucency and boundaries."""
        if not self.current_doc or not hasattr(self.current_doc, "construction_planes"):
            return
        if not self.current_doc.construction_planes:
            return

        glDisable(GL_LIGHTING)
        sz = 40.0

        for pid, cp in self.current_doc.construction_planes.items():
            if not cp.get("is_visible", True):
                continue

            base = cp.get("base_plane", "XY")
            offset = float(cp.get("offset", 0.0))
            is_hov = (self.hovered_plane == pid)

            # Translucent amber construction quad
            glColor4f(0.96, 0.65, 0.14, 0.35 if is_hov else 0.18)
            glBegin(GL_QUADS)
            if base == "XY":
                glVertex3f(-sz, -sz, offset)
                glVertex3f(sz, -sz, offset)
                glVertex3f(sz, sz, offset)
                glVertex3f(-sz, sz, offset)
            elif base == "XZ":
                glVertex3f(-sz, offset, -sz)
                glVertex3f(sz, offset, -sz)
                glVertex3f(sz, offset, sz)
                glVertex3f(-sz, offset, sz)
            elif base == "YZ":
                glVertex3f(offset, -sz, -sz)
                glVertex3f(offset, sz, -sz)
                glVertex3f(offset, sz, sz)
                glVertex3f(offset, -sz, sz)
            glEnd()

            # Boundary line loop
            glLineWidth(2.4 if is_hov else 1.2)
            glColor4f(1.0, 0.78, 0.20, 0.95 if is_hov else 0.65)
            glBegin(GL_LINE_LOOP)
            if base == "XY":
                glVertex3f(-sz, -sz, offset)
                glVertex3f(sz, -sz, offset)
                glVertex3f(sz, sz, offset)
                glVertex3f(-sz, sz, offset)
            elif base == "XZ":
                glVertex3f(-sz, offset, -sz)
                glVertex3f(sz, offset, -sz)
                glVertex3f(sz, offset, sz)
                glVertex3f(-sz, offset, sz)
            elif base == "YZ":
                glVertex3f(offset, -sz, -sz)
                glVertex3f(offset, sz, -sz)
                glVertex3f(offset, sz, sz)
                glVertex3f(offset, -sz, sz)
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
            glPolygonOffset(1.0, 1.0)

            if self.selected_body:
                glColor3f(0.18, 0.48, 0.88)
            else:
                glColor3f(0.62, 0.65, 0.68)  # Metallic engineering grey

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
                glColor3f(0.08, 0.18, 0.45)
            else:
                glColor3f(0.08, 0.08, 0.10)  # Crisp dark boundary edges

            glEnableClientState(GL_VERTEX_ARRAY)
            glVertexPointer(3, GL_FLOAT, 0, tess.edge_lines)
            glDrawArrays(GL_LINES, 0, len(tess.edge_lines))
            glDisableClientState(GL_VERTEX_ARRAY)
            glEnable(GL_LIGHTING)

    def set_preview_shape(self, shape):
        """Sets an interactive 3D solid preview (e.g. live extrusion/fillet) in the canvas."""
        self.preview_shape = shape
        if shape is not None:
            try:
                self.preview_tessellation = OCCTessellator.tessellate(shape, linear_deflection=0.25, angular_deflection=0.5)
            except Exception:
                self.preview_tessellation = None
        else:
            self.preview_tessellation = None
        self.update()

    def _render_preview_solid(self):
        """Renders live interactive modeling preview solid with translucent shading and highlight edges."""
        tess = self.preview_tessellation
        if not tess or len(tess.vertices) == 0:
            return

        verts = tess.vertices
        norms = tess.normals

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_LIGHTING)
        glEnable(GL_POLYGON_OFFSET_FILL)
        glPolygonOffset(-1.0, -1.0)

        # Translucent warm Fusion amber preview
        glColor4f(1.0, 0.65, 0.15, 0.60)

        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, verts)
        glNormalPointer(GL_FLOAT, 0, norms)
        glDrawArrays(GL_TRIANGLES, 0, len(verts))
        glDisableClientState(GL_NORMAL_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)
        glDisable(GL_POLYGON_OFFSET_FILL)

        # Highlight preview wireframe edges
        if len(tess.edge_lines) > 0:
            glDisable(GL_LIGHTING)
            glLineWidth(2.2)
            glColor4f(1.0, 0.85, 0.20, 0.95)
            glEnableClientState(GL_VERTEX_ARRAY)
            glVertexPointer(3, GL_FLOAT, 0, tess.edge_lines)
            glDrawArrays(GL_LINES, 0, len(tess.edge_lines))
            glDisableClientState(GL_VERTEX_ARRAY)
            glEnable(GL_LIGHTING)

    def _render_sketch(self, sketch: Sketch):
        """Renders 2D sketch geometry, closed shaded profiles, and rubber-band drawing previews."""
        glDisable(GL_LIGHTING)

        # 1. Shaded Closed Profiles (Fusion 360 translucent profile fill)
        try:
            polys = sketch.get_profile_polygons()
            for pts in polys:
                if len(pts) >= 3:
                    # Shaded Profile Blue
                    glColor4f(0.0, 0.60, 0.95, 0.28)
                    glBegin(GL_POLYGON)
                    for px, py, pz in pts:
                        glVertex3f(px, py, pz)
                    glEnd()
        except Exception:
            pass

        # 2. Sketch Curves (Lines & Arcs)
        is_constrained = sketch.last_result and sketch.last_result.dof == 0
        normal_color = (0.15, 0.85, 0.35) if is_constrained else (0.0, 0.70, 0.95)

        for line in sketch.lines.values():
            p1 = sketch.points.get(line.p1_id)
            p2 = sketch.points.get(line.p2_id)
            if p1 and p2:
                pt1 = sketch.map_to_3d(p1.u, p1.v)
                pt2 = sketch.map_to_3d(p2.u, p2.v)
                is_sel = line.line_id in self.selected_sketch_lines
                if is_sel:
                    glLineWidth(4.0)
                    glColor3f(0.0, 1.0, 1.0)  # Fusion glowing cyan selection
                else:
                    glLineWidth(2.2)
                    glColor3f(*normal_color)
                glBegin(GL_LINES)
                glVertex3f(pt1.X(), pt1.Y(), pt1.Z())
                glVertex3f(pt2.X(), pt2.Y(), pt2.Z())
                glEnd()

        # Circles
        for circ in sketch.circles.values():
            cp = sketch.points.get(circ.center_id)
            if cp:
                is_sel = circ.circle_id in self.selected_sketch_circles
                if is_sel:
                    glLineWidth(3.8)
                    glColor3f(0.0, 1.0, 1.0)
                else:
                    glLineWidth(2.0)
                    glColor3f(*normal_color)
                glBegin(GL_LINE_LOOP)
                for i in range(48):
                    ang = 2.0 * math.pi * (i / 48.0)
                    u = cp.u + circ.radius * math.cos(ang)
                    v = cp.v + circ.radius * math.sin(ang)
                    p3d = sketch.map_to_3d(u, v)
                    glVertex3f(p3d.X(), p3d.Y(), p3d.Z())
                glEnd()

        # Arcs
        if hasattr(sketch, "arcs"):
            for arc in sketch.arcs.values():
                cp = sketch.points.get(arc.center_id)
                if cp:
                    glLineWidth(2.2)
                    glColor3f(*normal_color)
                    glBegin(GL_LINE_STRIP)
                    steps = 32
                    a1 = arc.start_angle
                    a2 = arc.end_angle
                    if a2 < a1:
                        a2 += 2.0 * math.pi
                    for i in range(steps + 1):
                        cur_a = a1 + (a2 - a1) * (i / float(steps))
                        u = cp.u + arc.radius * math.cos(cur_a)
                        v = cp.v + arc.radius * math.sin(cur_a)
                        p3d = sketch.map_to_3d(u, v)
                        glVertex3f(p3d.X(), p3d.Y(), p3d.Z())
                    glEnd()

        # 3. Sketch Points
        for pt in sketch.points.values():
            p = sketch.map_to_3d(pt.u, pt.v)
            is_sel = pt.point_id in self.selected_sketch_points
            if is_sel:
                glPointSize(10.0)
                glColor3f(0.0, 1.0, 1.0)  # Selected cyan
            else:
                glPointSize(6.0)
                glColor3f(1.0, 0.75, 0.2)
            glBegin(GL_POINTS)
            glVertex3f(p.X(), p.Y(), p.Z())
            glEnd()

        # 4. Rubber-band preview during active drawing
        if self._sketch_start_pt and self._sketch_current_pt:
            u1, v1 = self._sketch_start_pt
            u2, v2 = self._sketch_current_pt

            glColor4f(1.0, 0.85, 0.2, 0.9)  # Active tool amber
            glLineWidth(2.0)

            if self.active_sketch_tool == "line":
                p1 = sketch.map_to_3d(u1, v1)
                p2 = sketch.map_to_3d(u2, v2)
                glBegin(GL_LINES)
                glVertex3f(p1.X(), p1.Y(), p1.Z())
                glVertex3f(p2.X(), p2.Y(), p2.Z())
                glEnd()

            elif self.active_sketch_tool == "rect":
                pts = [
                    sketch.map_to_3d(u1, v1),
                    sketch.map_to_3d(u2, v1),
                    sketch.map_to_3d(u2, v2),
                    sketch.map_to_3d(u1, v2),
                ]
                # Translucent fill preview
                glColor4f(0.1, 0.6, 1.0, 0.2)
                glBegin(GL_QUADS)
                for p in pts:
                    glVertex3f(p.X(), p.Y(), p.Z())
                glEnd()
                # Boundary outline preview
                glColor4f(1.0, 0.85, 0.2, 0.9)
                glBegin(GL_LINE_LOOP)
                for p in pts:
                    glVertex3f(p.X(), p.Y(), p.Z())
                glEnd()

            elif self.active_sketch_tool == "center_rect":
                hw = abs(u2 - u1)
                hh = abs(v2 - v1)
                pts = [
                    sketch.map_to_3d(u1 - hw, v1 - hh),
                    sketch.map_to_3d(u1 + hw, v1 - hh),
                    sketch.map_to_3d(u1 + hw, v1 + hh),
                    sketch.map_to_3d(u1 - hw, v1 + hh),
                ]
                glColor4f(0.1, 0.6, 1.0, 0.2)
                glBegin(GL_QUADS)
                for p in pts:
                    glVertex3f(p.X(), p.Y(), p.Z())
                glEnd()
                glColor4f(1.0, 0.85, 0.2, 0.9)
                glBegin(GL_LINE_LOOP)
                for p in pts:
                    glVertex3f(p.X(), p.Y(), p.Z())
                glEnd()

            elif self.active_sketch_tool == "circle":
                rad = math.sqrt((u2 - u1)**2 + (v2 - v1)**2)
                glColor4f(0.1, 0.6, 1.0, 0.2)
                glBegin(GL_POLYGON)
                for i in range(36):
                    ang = 2.0 * math.pi * (i / 36.0)
                    p = sketch.map_to_3d(u1 + rad * math.cos(ang), v1 + rad * math.sin(ang))
                    glVertex3f(p.X(), p.Y(), p.Z())
                glEnd()
                glColor4f(1.0, 0.85, 0.2, 0.9)
                glBegin(GL_LINE_LOOP)
                for i in range(36):
                    ang = 2.0 * math.pi * (i / 36.0)
                    p = sketch.map_to_3d(u1 + rad * math.cos(ang), v1 + rad * math.sin(ang))
                    glVertex3f(p.X(), p.Y(), p.Z())
                glEnd()

        # 5. Snap indicator
        if self._snap_pt:
            su, sv = self._snap_pt
            sp = sketch.map_to_3d(su, sv)
            glPointSize(10.0)
            glColor3f(0.1, 1.0, 0.3)
            glBegin(GL_POINTS)
            glVertex3f(sp.X(), sp.Y(), sp.Z())
            glEnd()

        glEnable(GL_LIGHTING)

    def _render_extrude_arrow(self):
        """Renders 3D yellow distance arrow manipulator above the active extrusion profile."""
        glDisable(GL_LIGHTING)
        glLineWidth(3.0)
        glColor3f(1.0, 0.8, 0.1)

        d = self.extrude_arrow_dist
        glBegin(GL_LINES)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(0.0, 0.0, d)
        # Arrowhead
        glVertex3f(0.0, 0.0, d)
        glVertex3f(-2.0, 0.0, d - 4.0 if d > 0 else d + 4.0)
        glVertex3f(0.0, 0.0, d)
        glVertex3f(2.0, 0.0, d - 4.0 if d > 0 else d + 4.0)
        glEnd()
        glEnable(GL_LIGHTING)

    # --- 2D Heads-Up Display (HUD) Overlays ---

    def _draw_hud_plane_prompt(self, painter: QPainter):
        """Displays floating prompt banner when user needs to pick a work plane."""
        w = self.width()
        banner_rect = QRect(int(w / 2) - 150, 20, 300, 34)
        painter.setBrush(QColor(25, 25, 28, 220))
        painter.setPen(QPen(QColor(ThemeColors.ACCENT_BLUE), 1.5))
        painter.drawRoundedRect(banner_rect, 6, 6)

        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        text = "Select a plane or planar face to sketch"
        if self.hovered_plane:
            text = f"Click to sketch on {self.hovered_plane} Plane"
        painter.drawText(banner_rect, Qt.AlignCenter, text)

    def _draw_hud_sketch_info(self, painter: QPainter):
        """Displays dimension readouts next to cursor during sketching."""
        # Top-right FINISH SKETCH button overlay
        btn_rect = QRect(self.width() - 150, 115, 136, 32)
        painter.setBrush(QColor(16, 124, 65, 230))
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawRoundedRect(btn_rect, 4, 4)
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.drawText(btn_rect, Qt.AlignCenter, "✔ FINISH SKETCH")

        if self._sketch_start_pt and self._sketch_current_pt:
            u1, v1 = self._sketch_start_pt
            u2, v2 = self._sketch_current_pt
            pos = self._last_mouse_pos

            du = u2 - u1
            dv = v2 - v1
            length = math.sqrt(du*du + dv*dv)
            angle = math.degrees(math.atan2(dv, du)) % 360.0

            hud_rect = QRect(pos.x() + 18, pos.y() - 36, 140, 42)
            painter.setBrush(QColor(20, 20, 22, 210))
            painter.setPen(QPen(QColor(ThemeColors.BORDER_FOCUS), 1))
            painter.drawRoundedRect(hud_rect, 4, 4)

            painter.setPen(QColor(240, 240, 240))
            painter.setFont(QFont("Segoe UI", 8))

            if self.active_sketch_tool == "line":
                painter.drawText(hud_rect.adjusted(6, 4, -6, -20), Qt.AlignLeft, f"Length: {length:.2f} mm")
                painter.drawText(hud_rect.adjusted(6, 20, -6, -4), Qt.AlignLeft, f"Angle:  {angle:.1f}°")
            elif self.active_sketch_tool in ("rect", "center_rect"):
                w_val = abs(du) * (2.0 if self.active_sketch_tool == "center_rect" else 1.0)
                h_val = abs(dv) * (2.0 if self.active_sketch_tool == "center_rect" else 1.0)
                painter.drawText(hud_rect.adjusted(6, 4, -6, -20), Qt.AlignLeft, f"Width:  {w_val:.2f} mm")
                painter.drawText(hud_rect.adjusted(6, 20, -6, -4), Qt.AlignLeft, f"Height: {h_val:.2f} mm")
            elif self.active_sketch_tool == "circle":
                dia = length * 2.0
                painter.drawText(hud_rect.adjusted(6, 4, -6, -20), Qt.AlignLeft, f"Diameter: {dia:.2f} mm")
                painter.drawText(hud_rect.adjusted(6, 20, -6, -4), Qt.AlignLeft, f"Radius:   {length:.2f} mm")

    # --- Raycasting & Unprojection Helpers ---

    def _unproject_screen_to_ray(self, sx: int, sy: int) -> Tuple[np.ndarray, np.ndarray]:
        """Calculates 3D world ray origin and direction vector from screen pixel coordinate."""
        self.makeCurrent()
        viewport = glGetIntegerv(GL_VIEWPORT)
        mv_matrix = glGetDoublev(GL_MODELVIEW_MATRIX)
        proj_matrix = glGetDoublev(GL_PROJECTION_MATRIX)
        win_y = float(viewport[3] - sy)

        try:
            p_near = np.array(gluUnProject(float(sx), win_y, 0.0, mv_matrix, proj_matrix, viewport), dtype=np.float32)
            p_far = np.array(gluUnProject(float(sx), win_y, 1.0, mv_matrix, proj_matrix, viewport), dtype=np.float32)
            ray_dir = p_far - p_near
            ray_dir /= max(np.linalg.norm(ray_dir), 1e-9)
            return p_near, ray_dir
        except Exception:
            return np.array([0, 0, 100], dtype=np.float32), np.array([0, 0, -1], dtype=np.float32)

    def _intersect_ray_with_plane(self, p_near: np.ndarray, ray_dir: np.ndarray,
                                  p_plane: np.ndarray, normal: np.ndarray) -> Optional[np.ndarray]:
        denom = float(np.dot(normal, ray_dir))
        if abs(denom) < 1e-6:
            return None
        t = float(np.dot(p_plane - p_near, normal) / denom)
        if t < 0:
            return None
        return p_near + t * ray_dir

    def _get_sketch_plane_coords(self, sx: int, sy: int) -> Tuple[float, float]:
        """Maps 2D mouse pixel coordinates to 2D sketch plane coordinates (u, v) in mm."""
        p_near, ray_dir = self._unproject_screen_to_ray(sx, sy)
        if not self.active_sketch:
            return (0.0, 0.0)

        pl = self.active_sketch.plane
        offset = float(getattr(self.active_sketch, "offset", 0.0))
        n = np.array(self.active_sketch.get_plane_normal(), dtype=np.float32)
        p0 = n * offset

        hit = self._intersect_ray_with_plane(p_near, ray_dir, p0, n)
        if hit is None:
            return (0.0, 0.0)

        if pl == "XY":
            return (float(hit[0]), float(hit[1]))
        elif pl == "XZ":
            return (float(hit[0]), float(hit[2]))
        elif pl == "YZ":
            return (float(hit[1]), float(hit[2]))
        return (float(hit[0]), float(hit[1]))

    def _test_hover_origin_planes(self, sx: int, sy: int) -> Optional[str]:
        """Detects if ray from mouse hits one of the 3 origin plane selection tiles or a construction plane."""
        p_near, ray_dir = self._unproject_screen_to_ray(sx, sy)
        sz = 35.0

        # Construction planes
        if self.current_doc and hasattr(self.current_doc, "construction_planes"):
            for pid, cp in self.current_doc.construction_planes.items():
                if not cp.get("is_visible", True):
                    continue
                base = cp.get("base_plane", "XY")
                off = float(cp.get("offset", 0.0))
                if base == "XY":
                    hit = self._intersect_ray_with_plane(p_near, ray_dir, np.array([0, 0, off], dtype=np.float32), np.array([0, 0, 1], dtype=np.float32))
                    if hit is not None and -sz <= hit[0] <= sz and -sz <= hit[1] <= sz:
                        return pid
                elif base == "XZ":
                    hit = self._intersect_ray_with_plane(p_near, ray_dir, np.array([0, off, 0], dtype=np.float32), np.array([0, 1, 0], dtype=np.float32))
                    if hit is not None and -sz <= hit[0] <= sz and -sz <= hit[2] <= sz:
                        return pid
                elif base == "YZ":
                    hit = self._intersect_ray_with_plane(p_near, ray_dir, np.array([off, 0, 0], dtype=np.float32), np.array([1, 0, 0], dtype=np.float32))
                    if hit is not None and -sz <= hit[1] <= sz and -sz <= hit[2] <= sz:
                        return pid

        # XY Plane (z = 0)
        hit_xy = self._intersect_ray_with_plane(p_near, ray_dir, np.array([0,0,0], dtype=np.float32), np.array([0,0,1], dtype=np.float32))
        if hit_xy is not None and -sz <= hit_xy[0] <= sz and -sz <= hit_xy[1] <= sz:
            return "XY"

        # XZ Plane (y = 0)
        hit_xz = self._intersect_ray_with_plane(p_near, ray_dir, np.array([0,0,0], dtype=np.float32), np.array([0,1,0], dtype=np.float32))
        if hit_xz is not None and -sz <= hit_xz[0] <= sz and -sz <= hit_xz[2] <= sz:
            return "XZ"

        # YZ Plane (x = 0)
        hit_yz = self._intersect_ray_with_plane(p_near, ray_dir, np.array([0,0,0], dtype=np.float32), np.array([1,0,0], dtype=np.float32))
        if hit_yz is not None and -sz <= hit_yz[1] <= sz and -sz <= hit_yz[2] <= sz:
            return "YZ"

        return None

    def _calculate_snap(self, u: float, v: float) -> Tuple[float, float, str]:
        """Calculates snapping to origin, existing sketch points, and horizontal/vertical alignments."""
        if not self.active_sketch:
            return (u, v, "none")

        snap_thresh = max(self.camera_dist * 0.03, 3.0)

        # 1. Snap to Origin (0, 0)
        if math.sqrt(u*u + v*v) < snap_thresh:
            return (0.0, 0.0, "origin")

        # 2. Snap to existing sketch points
        for pt in self.active_sketch.points.values():
            d = math.sqrt((pt.u - u)**2 + (pt.v - v)**2)
            if d < snap_thresh:
                return (pt.u, pt.v, "point")

        # 3. Horizontal / Vertical alignment with start point
        if self._sketch_start_pt:
            su, sv = self._sketch_start_pt
            if abs(u - su) < snap_thresh:
                return (su, v, "axis_v")
            if abs(v - sv) < snap_thresh:
                return (u, sv, "axis_h")

        return (u, v, "none")

    def _hit_test_sketch(self, u: float, v: float, thresh: float = 4.0) -> Tuple[Optional[str], Optional[str]]:
        """Hit-tests points, lines, and circles in active sketch near (u, v)."""
        if not self.active_sketch:
            return None, None

        # 1. Test Points
        for pid, pt in self.active_sketch.points.items():
            if math.hypot(pt.u - u, pt.v - v) <= thresh:
                return "point", pid

        # 2. Test Lines (perpendicular distance to line segment)
        for lid, line in self.active_sketch.lines.items():
            p1 = self.active_sketch.points.get(line.p1_id)
            p2 = self.active_sketch.points.get(line.p2_id)
            if p1 and p2:
                du = p2.u - p1.u
                dv = p2.v - p1.v
                l2 = du * du + dv * dv
                if l2 > 1e-9:
                    t = max(0.0, min(1.0, ((u - p1.u) * du + (v - p1.v) * dv) / l2))
                    proj_u = p1.u + t * du
                    proj_v = p1.v + t * dv
                    if math.hypot(u - proj_u, v - proj_v) <= thresh:
                        return "line", lid

        # 3. Test Circles (distance to circumference)
        for cid, circ in self.active_sketch.circles.items():
            cp = self.active_sketch.points.get(circ.center_id)
            if cp:
                dist_to_center = math.hypot(u - cp.u, v - cp.v)
                if abs(dist_to_center - circ.radius) <= thresh:
                    return "circle", cid

        return None, None

    # --- Mouse & Keyboard Interactions ---

    def mousePressEvent(self, event: QMouseEvent):
        self._last_mouse_pos = event.pos()
        pos = event.pos()

        # Check Click on Top-Right "Finish Sketch" overlay button
        if self.is_sketch_mode:
            finish_rect = QRect(self.width() - 150, 115, 136, 32)
            if finish_rect.contains(pos):
                self.set_sketch(None)
                self.set_standard_view("home")
                self.command_requested.emit("finish_sketch")
                return

        # Plane Selection Mode Click
        if self.plane_selection_mode:
            if event.button() == Qt.LeftButton and self.hovered_plane:
                chosen_plane = self.hovered_plane
                self.plane_selection_mode = False
                self.hovered_plane = None
                self.plane_picked.emit(chosen_plane)
                self.update()
                return

        is_shift = bool(event.modifiers() & Qt.ShiftModifier)
        is_ctrl = bool(event.modifiers() & Qt.ControlModifier)

        # Middle Mouse = Navigation
        if event.button() == Qt.MiddleButton:
            self._active_nav_mode = "orbit" if is_shift else "pan"
            return

        # Left Click in Sketch Mode
        if event.button() == Qt.LeftButton:
            if self._temp_tool_override:
                self._active_nav_mode = self._temp_tool_override
                return
            if is_shift and not self.is_sketch_mode:
                self._active_nav_mode = "orbit"
                return

            if self.is_sketch_mode and self.active_sketch:
                raw_u, raw_v = self._get_sketch_plane_coords(pos.x(), pos.y())
                u, v, snap = self._calculate_snap(raw_u, raw_v)
                hit_thresh = max(self.camera_dist * 0.025, 2.5)

                if self.active_sketch_tool == "select":
                    kind, entity_id = self._hit_test_sketch(raw_u, raw_v, hit_thresh)
                    if not (is_shift or is_ctrl):
                        self.selected_sketch_points.clear()
                        self.selected_sketch_lines.clear()
                        self.selected_sketch_circles.clear()

                    if kind == "point":
                        if entity_id in self.selected_sketch_points:
                            self.selected_sketch_points.remove(entity_id)
                        else:
                            self.selected_sketch_points.add(entity_id)
                    elif kind == "line":
                        if entity_id in self.selected_sketch_lines:
                            self.selected_sketch_lines.remove(entity_id)
                        else:
                            self.selected_sketch_lines.add(entity_id)
                    elif kind == "circle":
                        if entity_id in self.selected_sketch_circles:
                            self.selected_sketch_circles.remove(entity_id)
                        else:
                            self.selected_sketch_circles.add(entity_id)

                    self.sketch_selection_changed.emit()
                    self.update()
                    return

                elif self.active_sketch_tool == "dimension":
                    kind, entity_id = self._hit_test_sketch(raw_u, raw_v, hit_thresh)
                    if kind == "line":
                        line = self.active_sketch.lines[entity_id]
                        p1 = self.active_sketch.points[line.p1_id]
                        p2 = self.active_sketch.points[line.p2_id]
                        cur_len = math.hypot(p2.u - p1.u, p2.v - p1.v)
                        val, ok = QInputDialog.getDouble(self, "Sketch Dimension", "Distance (mm):", cur_len, 0.01, 10000.0, 2)
                        if ok:
                            self.active_sketch.add_constraint("distance", [entity_id], value=val)
                            self.active_sketch.solve()
                            self.sketch_modified.emit()
                            self.update()
                        return
                    elif kind == "circle":
                        circ = self.active_sketch.circles[entity_id]
                        cur_dia = circ.radius * 2.0
                        val, ok = QInputDialog.getDouble(self, "Circle Dimension", "Diameter (mm):", cur_dia, 0.01, 10000.0, 2)
                        if ok:
                            circ.radius = val / 2.0
                            self.active_sketch.solve()
                            self.sketch_modified.emit()
                            self.update()
                        return
                    elif kind == "point":
                        if self.selected_sketch_points and entity_id not in self.selected_sketch_points:
                            prev_pid = next(iter(self.selected_sketch_points))
                            p1 = self.active_sketch.points[prev_pid]
                            p2 = self.active_sketch.points[entity_id]
                            cur_d = math.hypot(p2.u - p1.u, p2.v - p1.v)
                            val, ok = QInputDialog.getDouble(self, "Distance Dimension", "Distance (mm):", cur_d, 0.01, 10000.0, 2)
                            if ok:
                                self.active_sketch.add_constraint("distance", [prev_pid, entity_id], value=val)
                                self.active_sketch.solve()
                                self.sketch_modified.emit()
                                self.selected_sketch_points.clear()
                                self.update()
                            return
                        else:
                            self.selected_sketch_points.add(entity_id)
                            self.update()
                            return

                elif self.active_sketch_tool in ("point", "sketch_point"):
                    self.active_sketch.add_point(u, v)
                    self.active_sketch.solve()
                    self.sketch_modified.emit()
                    self.update()
                    return

                elif self.active_sketch_tool in ("arc", "sketch_arc"):
                    self._arc_pts.append((u, v))
                    if len(self._arc_pts) >= 3:
                        (u1, v1), (u2, v2), (u3, v3) = self._arc_pts[:3]
                        p1_id = self.active_sketch.add_point(u1, v1)
                        p2_id = self.active_sketch.add_point(u2, v2)
                        p3_id = self.active_sketch.add_point(u3, v3)
                        self.active_sketch.add_arc(p1_id, p2_id, p3_id)
                        self.active_sketch.solve()
                        self.sketch_modified.emit()
                        self._arc_pts.clear()
                    self.update()
                    return

                # Interactive Drawing: First Point
                if self._sketch_start_pt is None:
                    self._sketch_start_pt = (u, v)
                    self._sketch_current_pt = (u, v)
                    self.update()
                else:
                    # Second Point: Commit Geometry
                    u1, v1 = self._sketch_start_pt
                    u2, v2 = u, v

                    if self.active_sketch_tool == "line":
                        p1_id = self.active_sketch.add_point(u1, v1)
                        p2_id = self.active_sketch.add_point(u2, v2)
                        self.active_sketch.add_line(p1_id, p2_id)
                        self.active_sketch.solve()
                        self.sketch_modified.emit()
                        # Continuous chaining like Fusion 360
                        self._sketch_start_pt = (u2, v2)
                        self._sketch_current_pt = (u2, v2)

                    elif self.active_sketch_tool == "rect":
                        self.active_sketch.add_rect(u1, v1, u2, v2)
                        self.active_sketch.solve()
                        self.sketch_modified.emit()
                        self._sketch_start_pt = None
                        self._sketch_current_pt = None

                    elif self.active_sketch_tool == "center_rect":
                        hw = abs(u2 - u1)
                        hh = abs(v2 - v1)
                        self.active_sketch.add_rect(u1 - hw, v1 - hh, u1 + hw, v1 + hh)
                        self.active_sketch.solve()
                        self.sketch_modified.emit()
                        self._sketch_start_pt = None
                        self._sketch_current_pt = None

                    elif self.active_sketch_tool == "circle":
                        radius = math.sqrt((u2 - u1)**2 + (v2 - v1)**2)
                        self.active_sketch.add_circle(u1, v1, radius)
                        self.active_sketch.solve()
                        self.sketch_modified.emit()
                        self._sketch_start_pt = None
                        self._sketch_current_pt = None

                    self.update()

            else:
                # 3D Solid Selection
                self.selected_body = not self.selected_body
                self.selection_changed.emit("body", "body_1" if self.selected_body else "")
                self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = event.pos()
        dx = pos.x() - self._last_mouse_pos.x()
        dy = pos.y() - self._last_mouse_pos.y()
        self._last_mouse_pos = pos

        # Update cursor world readout
        rad_az = math.radians(self.azimuth)
        world_x = self.camera_target[0] + dx * 0.1 * math.sin(rad_az)
        world_y = self.camera_target[1] + dy * 0.1 * math.cos(rad_az)
        self.cursor_moved.emit(world_x, world_y, 0.0)

        # Plane Selection Hover Test
        if self.plane_selection_mode:
            new_hov = self._test_hover_origin_planes(pos.x(), pos.y())
            if new_hov != self.hovered_plane:
                self.hovered_plane = new_hov
                self.update()

        # In-Canvas Sketch Live Tracking
        if self.is_sketch_mode and self.active_sketch:
            raw_u, raw_v = self._get_sketch_plane_coords(pos.x(), pos.y())
            su, sv, stype = self._calculate_snap(raw_u, raw_v)
            self._snap_pt = (su, sv) if stype != "none" else None
            self._snap_type = stype

            if self._sketch_start_pt:
                self._sketch_current_pt = (su, sv)
            self.update()

        # Camera Navigation
        if self._active_nav_mode == "orbit":
            self.azimuth = (self.azimuth + dx * 0.5) % 360.0
            self.elevation = max(-89.0, min(89.0, self.elevation - dy * 0.5))
            self.viewcube.update_orientation(self.azimuth, self.elevation)
            self.update()

        elif self._active_nav_mode == "pan":
            pan_speed = self.camera_dist * 0.0015
            rad_az = math.radians(self.azimuth)
            right_x = math.cos(rad_az)
            right_y = math.sin(rad_az)
            self.camera_target[0] -= dx * pan_speed * right_x
            self.camera_target[1] -= dx * pan_speed * right_y
            self.camera_target[2] += dy * pan_speed
            self.update()

        elif self._active_nav_mode == "zoom":
            factor = 1.0 - dy * 0.01
            self.camera_dist = max(5.0, min(20000.0, self.camera_dist * factor))
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._active_nav_mode = "none"
        self._temp_tool_override = None

    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y()
        zoom_factor = 0.88 if delta > 0 else 1.14
        self.camera_dist = max(5.0, min(25000.0, self.camera_dist * zoom_factor))
        self.update()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MiddleButton:
            self.fit_all()

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key == Qt.Key_Escape:
            # Cancel active drawing chain
            self._sketch_start_pt = None
            self._sketch_current_pt = None
            self.plane_selection_mode = False
            self.active_sketch_tool = "select"
            self.update()
        super().keyPressEvent(event)

    # --- Document & Camera API ---

    def update_model(self, doc: CADDocument):
        """Tessellates current solid and re-renders viewport."""
        self.current_doc = doc
        if doc.current_solid is not None and not doc.current_solid.IsNull():
            self.tessellation = OCCTessellator.tessellate(doc.current_solid)
        else:
            self.tessellation = None
        self.update()

    def start_plane_selection(self):
        """Prompts user to select a work plane to begin a new sketch."""
        self.plane_selection_mode = True
        self.hovered_plane = None
        self.update()

    def cancel_plane_selection(self):
        """Cancels work plane selection mode."""
        self.plane_selection_mode = False
        self.hovered_plane = None
        self.update()

    def animate_to_orientation(self, target_az: float, target_el: float,
                               target_dist: Optional[float] = None,
                               target_target: Optional[np.ndarray] = None,
                               duration_ms: int = 240):
        """Smoothly interpolates camera orientation, zoom, and target point using cosine easing."""
        self._anim_start_az = self.azimuth
        self._anim_start_el = self.elevation
        self._anim_target_az = target_az % 360.0
        self._anim_target_el = max(-89.9, min(89.9, target_el))

        # Shortest angular route for azimuth
        d_az = (self._anim_target_az - self._anim_start_az) % 360.0
        if d_az > 180.0:
            d_az -= 360.0
        self._anim_delta_az = d_az

        self._anim_start_dist = self.camera_dist
        self._anim_target_dist = float(target_dist) if target_dist is not None else self.camera_dist

        self._anim_start_target = np.copy(self.camera_target)
        if target_target is not None:
            self._anim_target_target = np.array(target_target, dtype=np.float32)
        else:
            self._anim_target_target = np.copy(self.camera_target)

        self._camera_anim_duration = max(50, duration_ms)
        self._camera_anim_elapsed.start()
        self._camera_anim_timer.start()

    def _on_camera_anim_step(self):
        """Timer callback performing cosine-eased camera interpolation at 60 FPS."""
        elapsed = self._camera_anim_elapsed.elapsed()
        t = min(1.0, elapsed / float(self._camera_anim_duration))
        # Cosine ease-in-out: 0.5 * (1 - cos(pi * t))
        ease = 0.5 * (1.0 - math.cos(math.pi * t))

        # Interpolate
        self.azimuth = (self._anim_start_az + self._anim_delta_az * ease) % 360.0
        self.elevation = self._anim_start_el + (self._anim_target_el - self._anim_start_el) * ease
        self.camera_dist = self._anim_start_dist + (self._anim_target_dist - self._anim_start_dist) * ease
        self.camera_target = self._anim_start_target + (self._anim_target_target - self._anim_start_target) * ease

        self.viewcube.update_orientation(self.azimuth, self.elevation)
        self.update()

        if t >= 1.0:
            self._camera_anim_timer.stop()
            self.azimuth = self._anim_target_az
            self.elevation = self._anim_target_el
            self.camera_dist = self._anim_target_dist
            self.camera_target = np.copy(self._anim_target_target)
            self.viewcube.update_orientation(self.azimuth, self.elevation)
            self.update()

    def set_sketch(self, sketch: Optional[Sketch], animated: bool = False):
        """Switches canvas into or out of 2D sketch mode."""
        self.active_sketch = sketch
        self.is_sketch_mode = (sketch is not None)
        self.plane_selection_mode = False
        self._sketch_start_pt = None
        self._sketch_current_pt = None
        self._snap_pt = None
        self.selected_sketch_points.clear()
        self.selected_sketch_lines.clear()
        self.selected_sketch_circles.clear()
        self._arc_pts.clear()

        if self.is_sketch_mode and sketch:
            target_az = 0.0
            target_el = 0.0
            if sketch.plane == "XY":
                target_az, target_el = 0.0, 89.9
            elif sketch.plane == "XZ":
                target_az, target_el = 0.0, 0.0
            elif sketch.plane == "YZ":
                target_az, target_el = 90.0, 0.0

            if animated:
                self.animate_to_orientation(target_az, target_el, duration_ms=280)
            else:
                self.azimuth, self.elevation = target_az, target_el
                self.viewcube.update_orientation(self.azimuth, self.elevation)
        self.update()

    def set_sketch_tool(self, tool_name: str):
        """Sets active sketch drawing tool: 'line', 'rect', 'center_rect', 'circle', 'dimension'."""
        self.active_sketch_tool = tool_name
        self._sketch_start_pt = None
        self._sketch_current_pt = None
        self.update()

    def fit_all(self, animated: bool = False):
        """Fits camera to solid model or sketch bounds."""
        if self.tessellation and self.tessellation.diagonal > 0:
            cx, cy, cz = self.tessellation.center
            target_center = np.array([cx, cy, cz], dtype=np.float32)
            target_dist = max(self.tessellation.diagonal * 1.8, 50.0)
        else:
            target_center = np.array([0.0, 0.0, 0.0], dtype=np.float32)
            target_dist = 160.0

        if animated:
            self.animate_to_orientation(self.azimuth, self.elevation, target_dist, target_center, duration_ms=240)
        else:
            self.camera_target = target_center
            self.camera_dist = target_dist
            self.update()

    def set_standard_view(self, view_name: str, animated: bool = False):
        v = view_name.lower()
        target_az = self.azimuth
        target_el = self.elevation
        target_dist = None
        target_center = None

        if v == "front":
            target_az, target_el = 0.0, 0.0
        elif v == "back":
            target_az, target_el = 180.0, 0.0
        elif v == "top":
            target_az, target_el = 0.0, 89.9
        elif v == "bottom":
            target_az, target_el = 0.0, -89.9
        elif v == "right":
            target_az, target_el = 90.0, 0.0
        elif v == "left":
            target_az, target_el = 270.0, 0.0
        elif v == "home":
            target_az, target_el = 45.0, 30.0
            if self.tessellation and self.tessellation.diagonal > 0:
                target_center = np.array(self.tessellation.center, dtype=np.float32)
                target_dist = max(self.tessellation.diagonal * 1.8, 50.0)
            else:
                target_center = np.array([0.0, 0.0, 0.0], dtype=np.float32)
                target_dist = 160.0

        if animated:
            self.animate_to_orientation(target_az, target_el, target_dist, target_center, duration_ms=260)
        else:
            self.azimuth = target_az
            self.elevation = target_el
            if target_dist is not None:
                self.camera_dist = target_dist
            if target_center is not None:
                self.camera_target = target_center
            self.viewcube.update_orientation(self.azimuth, self.elevation)
            self.update()

    def set_projection_mode(self, mode: str):
        if mode in ("perspective", "orthographic"):
            self.projection_mode = mode
            self.viewcube.set_projection_mode(mode)
            self.update()

    def _on_viewcube_orbit(self, d_az: float, d_el: float):
        self.azimuth = (self.azimuth + d_az) % 360.0
        self.elevation = max(-89.0, min(89.0, self.elevation + d_el))
        self.viewcube.update_orientation(self.azimuth, self.elevation)
        self.update()

    def _on_nav_tool_triggered(self, tool: str):
        if tool == "fit":
            self.fit_all(animated=True)
        elif tool == "look_at":
            if self.is_sketch_mode and self.active_sketch:
                if self.active_sketch.plane == "XY":
                    self.set_standard_view("top", animated=True)
                elif self.active_sketch.plane == "XZ":
                    self.set_standard_view("front", animated=True)
                elif self.active_sketch.plane == "YZ":
                    self.set_standard_view("right", animated=True)
            else:
                self.set_standard_view("top", animated=True)
        else:
            self._temp_tool_override = tool

    def _on_display_style_changed(self, style: str):
        self.display_style = style
        self.update()

    def _on_grid_toggled(self, checked: bool):
        self.show_grid = checked
        self.update()

    def contextMenuEvent(self, event):
        """Fusion 360-style right-click context menu / marking menu."""
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {ThemeColors.PANEL_BG};
                color: {ThemeColors.TEXT_MAIN};
                border: 1px solid {ThemeColors.BORDER_LIGHT};
                border-radius: 4px;
                padding: 4px 2px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 11px;
            }}
            QMenu::item {{
                padding: 6px 24px 6px 14px;
                border-radius: 2px;
            }}
            QMenu::item:selected {{
                background-color: {ThemeColors.HOVER_BG};
                color: #FFFFFF;
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {ThemeColors.BORDER_DARK};
                margin: 4px 8px;
            }}
        """)

        if self.is_sketch_mode:
            act_finish = menu.addAction("Finish Sketch")
            act_finish.triggered.connect(lambda: self.command_requested.emit("finish_sketch"))
            menu.addSeparator()
            act_line = menu.addAction("Line (L)")
            act_line.triggered.connect(lambda: self.set_sketch_tool("line"))
            act_rect = menu.addAction("2-Point Rectangle (R)")
            act_rect.triggered.connect(lambda: self.set_sketch_tool("rect"))
            act_circ = menu.addAction("Center Diameter Circle (C)")
            act_circ.triggered.connect(lambda: self.set_sketch_tool("circle"))
            act_dim = menu.addAction("Sketch Dimension (D)")
            act_dim.triggered.connect(lambda: self.set_sketch_tool("dimension"))
            menu.addSeparator()
        else:
            act_presspull = menu.addAction("Press Pull (Extrude) [E]")
            act_presspull.triggered.connect(lambda: self.command_requested.emit("extrude"))

            act_sketch = menu.addAction("Create Sketch")
            act_sketch.triggered.connect(lambda: self.command_requested.emit("create_sketch"))

            menu.addSeparator()

            act_fillet = menu.addAction("Fillet [F]")
            act_fillet.triggered.connect(lambda: self.command_requested.emit("fillet"))

            act_chamfer = menu.addAction("Chamfer")
            act_chamfer.triggered.connect(lambda: self.command_requested.emit("chamfer"))

            act_hole = menu.addAction("Hole [H]")
            act_hole.triggered.connect(lambda: self.command_requested.emit("hole"))

            act_shell = menu.addAction("Shell")
            act_shell.triggered.connect(lambda: self.command_requested.emit("shell"))

            menu.addSeparator()

            act_inspect = menu.addAction("Measure / Inspect [I]")
            act_inspect.triggered.connect(lambda: self.command_requested.emit("measure"))

            act_param = menu.addAction("Change Parameters")
            act_param.triggered.connect(lambda: self.command_requested.emit("parameters"))

            menu.addSeparator()

        act_fit = menu.addAction("Fit [Zoom All]")
        act_fit.triggered.connect(self.fit_all)

        act_home = menu.addAction("Home View")
        act_home.triggered.connect(lambda: self.set_standard_view("home"))

        menu.exec(event.globalPos())

