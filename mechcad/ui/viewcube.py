"""
MechCAD Interactive 3D ViewCube
Autodesk Fusion 360-style orientation cube with clickable faces (FRONT, TOP, RIGHT, HOME).
"""

from PySide6.QtWidgets import QWidget, QMenu
from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import (
    QPainter, QColor, QBrush, QPen, QPolygonF, QFont, QLinearGradient, QPainterPath
)
import math


class ViewCube(QWidget):
    """Interactive 3D navigation cube widget positioned in the viewport corner."""

    view_selected = Signal(str)  # 'front', 'top', 'right', 'left', 'back', 'bottom', 'home'
    projection_toggled = Signal(str)  # 'perspective', 'orthographic'
    orbit_delta = Signal(float, float)  # (delta_azimuth, delta_elevation)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(96, 96)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setMouseTracking(True)

        self.azimuth: float = 45.0
        self.elevation: float = 30.0

        self._is_dragging = False
        self._last_mouse_pos = None
        self._hovered_face = None

    def update_orientation(self, azimuth: float, elevation: float):
        """Syncs ViewCube display with current 3D camera angles."""
        self.azimuth = azimuth % 360.0
        self.elevation = max(-89.0, min(89.0, elevation))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w / 2.0, h / 2.0

        # Background subtle circular halo
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(30, 30, 30, 160))
        painter.drawEllipse(QPointF(cx, cy), 44, 44)

        # Home Icon in top-left
        home_rect = QRectF(4, 4, 18, 18)
        painter.setBrush(QColor(50, 50, 50, 200))
        painter.setPen(QColor(100, 100, 100))
        painter.drawRoundedRect(home_rect, 3, 3)
        painter.setPen(QColor(220, 220, 220))
        font_home = QFont("Segoe UI", 8, QFont.Bold)
        painter.setFont(font_home)
        painter.drawText(home_rect, Qt.AlignCenter, "⌂")

        # Draw Isometric Projection of ViewCube
        # Compute 8 cube vertices transformed by azimuth & elevation
        cube_size = 22.0
        rad_az = math.radians(self.azimuth)
        rad_el = math.radians(self.elevation)

        cos_az, sin_az = math.cos(rad_az), math.sin(rad_az)
        cos_el, sin_el = math.cos(rad_el), math.sin(rad_el)

        def project(x, y, z):
            # Rotate Z by azimuth
            rx = x * cos_az - y * sin_az
            ry = x * sin_az + y * cos_az
            rz = z
            # Rotate X by elevation
            px = rx
            py = ry * sin_el - rz * cos_el
            depth = ry * cos_el + rz * sin_el
            return cx + px, cy - py, depth

        # 6 Faces with labels and center depths
        faces = [
            ("TOP", [(-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)], (0, 0, 1)),
            ("BOTTOM", [(-1, -1, -1), (-1, 1, -1), (1, 1, -1), (1, -1, -1)], (0, 0, -1)),
            ("FRONT", [(-1, 1, -1), (1, 1, -1), (1, 1, 1), (-1, 1, 1)], (0, 1, 0)),
            ("BACK", [(-1, -1, -1), (-1, -1, 1), (1, -1, 1), (1, -1, -1)], (0, -1, 0)),
            ("RIGHT", [(1, -1, -1), (1, -1, 1), (1, 1, 1), (1, 1, -1)], (1, 0, 0)),
            ("LEFT", [(-1, -1, -1), (-1, 1, -1), (-1, 1, 1), (-1, -1, 1)], (-1, 0, 0)),
        ]

        # Calculate depths and sort back-to-front
        rendered_faces = []
        for name, corners, normal in faces:
            pts_2d = []
            avg_depth = 0.0
            for c in corners:
                px, py, d = project(c[0] * cube_size, c[1] * cube_size, c[2] * cube_size)
                pts_2d.append(QPointF(px, py))
                avg_depth += d
            avg_depth /= 4.0

            # Normal visibility test
            nx, ny, nz = normal
            rnx = nx * cos_az - ny * sin_az
            rny = nx * sin_az + ny * cos_az
            rnz = nz
            view_normal_z = rny * cos_el + rnz * sin_el

            if view_normal_z > 0.05:  # Facing camera
                rendered_faces.append((avg_depth, name, pts_2d, view_normal_z))

        rendered_faces.sort(key=lambda item: item[0])

        font_label = QFont("Segoe UI", 7, QFont.Bold)
        painter.setFont(font_label)

        for depth, name, pts, normal_z in rendered_faces:
            poly = QPolygonF(pts)
            is_hover = (name == self._hovered_face)

            # Gradient shading based on light source
            light_factor = max(0.4, min(1.0, 0.4 + normal_z * 0.6))
            base_color = QColor(100, 150, 200) if is_hover else QColor(
                int(60 * light_factor), int(65 * light_factor), int(75 * light_factor)
            )

            painter.setBrush(QBrush(base_color))
            painter.setPen(QPen(QColor(180, 180, 180) if is_hover else QColor(100, 100, 100), 1))
            painter.drawPolygon(poly)

            # Draw Label
            painter.setPen(QColor(255, 255, 255))
            poly_center = QPointF(
                sum(p.x() for p in pts) / 4.0,
                sum(p.y() for p in pts) / 4.0
            )
            painter.drawText(QRectF(poly_center.x() - 18, poly_center.y() - 8, 36, 16), Qt.AlignCenter, name)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.position()
            # Check Home click
            if pos.x() <= 24 and pos.y() <= 24:
                self.view_selected.emit("home")
                return

            if self._hovered_face:
                self.view_selected.emit(self._hovered_face.lower())
            else:
                self._is_dragging = True
                self._last_mouse_pos = event.position()

    def mouseMoveEvent(self, event):
        pos = event.position()
        if self._is_dragging and self._last_mouse_pos:
            dx = pos.x() - self._last_mouse_pos.x()
            dy = pos.y() - self._last_mouse_pos.y()
            self._last_mouse_pos = pos
            self.orbit_delta.emit(dx * 1.5, -dy * 1.5)
        else:
            # Check face hover
            old_hover = self._hovered_face
            self._hovered_face = self._detect_face_under_cursor(pos)
            if old_hover != self._hovered_face:
                self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_dragging = False
            self._last_mouse_pos = None

    def _detect_face_under_cursor(self, pos: QPointF) -> str:
        # Check Home button
        if pos.x() <= 24 and pos.y() <= 24:
            return "HOME"
        # Determine dominant quadrant from center
        w, h = self.width(), self.height()
        cx, cy = w / 2.0, h / 2.0
        dx = pos.x() - cx
        dy = pos.y() - cy
        dist = math.sqrt(dx*dx + dy*dy)
        if dist > 38:
            return None

        # Return closest face based on angles
        if self.elevation > 40:
            return "TOP"
        elif self.elevation < -40:
            return "BOTTOM"
        
        az = self.azimuth % 360.0
        if 45 <= az < 135:
            return "FRONT"
        elif 135 <= az < 225:
            return "RIGHT"
        elif 225 <= az < 315:
            return "BACK"
        else:
            return "LEFT"
