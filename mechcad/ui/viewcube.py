"""
MechCAD Interactive 3D ViewCube
Autodesk Fusion 360-style orientation cube with:
- Clickable 3D faces (TOP, BOTTOM, FRONT, BACK, RIGHT, LEFT)
- Dynamic Compass Ring with rotating N, S, E, W cardinal directions
- Directional 90-degree flip arrows (Up, Down, Left, Right)
- Screen-plane 90-degree roll arrows (CW, CCW)
- Home button with isometric reset
- View options context menu (Orthographic / Perspective, Standard Views, Fit All)
- Direct drag-to-orbit navigation
"""

import math
from PySide6.QtWidgets import QWidget, QMenu
from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import (
    QPainter, QColor, QBrush, QPen, QPolygonF, QFont, QLinearGradient, QPainterPath, QAction
)


class ViewCube(QWidget):
    """Interactive 3D navigation cube widget matching Autodesk Fusion 360."""

    view_selected = Signal(str)          # 'front', 'top', 'right', 'left', 'back', 'bottom', 'home'
    projection_toggled = Signal(str)     # 'perspective', 'orthographic'
    orbit_delta = Signal(float, float)   # (delta_azimuth, delta_elevation)
    fit_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(118, 118)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setMouseTracking(True)

        self.azimuth: float = 45.0
        self.elevation: float = 30.0
        self.projection_mode: str = "perspective"

        self._is_dragging: bool = False
        self._drag_start_pos = None
        self._last_mouse_pos = None
        self._hovered_element: str = None  # 'face:FRONT', 'home', 'menu', 'arrow:up', etc.

        # Cached geometries for hit testing
        self._rendered_faces = []
        self._action_rects = {}

    def update_orientation(self, azimuth: float, elevation: float):
        """Syncs ViewCube display with current 3D camera angles."""
        self.azimuth = azimuth % 360.0
        self.elevation = max(-89.9, min(89.9, elevation))
        self.update()

    def set_projection_mode(self, mode: str):
        if mode in ("perspective", "orthographic"):
            self.projection_mode = mode
            self.update()

    def _project(self, x: float, y: float, z: float, cx: float, cy: float, scale: float):
        """Projects 3D point in world space into 2D screen coordinates and depth."""
        rad_az = math.radians(self.azimuth)
        rad_el = math.radians(self.elevation)

        cos_az, sin_az = math.cos(rad_az), math.sin(rad_az)
        cos_el, sin_el = math.cos(rad_el), math.sin(rad_el)

        # Camera basis vectors:
        # Screen Right:  (cos_az, sin_az, 0)
        # Screen Up:     (-sin_az * sin_el, cos_az * sin_el, cos_el)
        # Depth forward: (sin_az * cos_el, -cos_az * cos_el, sin_el)
        px = x * cos_az + y * sin_az
        py = -x * sin_az * sin_el + y * cos_az * sin_el + z * cos_el
        depth = x * sin_az * cos_el - y * cos_az * cos_el + z * sin_el

        return cx + px * scale, cy - py * scale, depth

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        w, h = self.width(), self.height()
        cx, cy = w / 2.0, h / 2.0
        scale = 19.0

        self._action_rects.clear()

        # 1. Subtle Circular Compass Halo
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(24, 27, 32, 190))
        painter.drawEllipse(QPointF(cx, cy), 53, 53)

        painter.setPen(QPen(QColor(60, 68, 78, 140), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), 51, 51)

        # 2. Dynamic Rotating Compass Ring (N, E, S, W)
        rad_az = math.radians(self.azimuth)
        rad_el = math.radians(self.elevation)
        comp_r = 46.0

        # Compass is in XY plane at z = -1.2
        comp_points = [
            ("N", 0.0, 1.0, QColor(230, 75, 75)),   # North highlighted in subtle red
            ("E", 1.0, 0.0, QColor(160, 170, 180)),
            ("S", 0.0, -1.0, QColor(160, 170, 180)),
            ("W", -1.0, 0.0, QColor(160, 170, 180)),
        ]

        font_comp = QFont("Segoe UI", 6, QFont.Bold)
        painter.setFont(font_comp)

        for label, nx, ny, color in comp_points:
            # Position along compass ring
            sx, sy, d = self._project(nx * 2.3, ny * 2.3, -1.0, cx, cy, scale)
            # Subtle tick
            painter.setPen(QPen(color, 1.2))
            painter.drawText(QRectF(sx - 8, sy - 8, 16, 16), Qt.AlignCenter, label)

        # 3. 3D Orientation Cube Faces
        faces_def = [
            ("TOP", [(-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)], (0, 0, 1)),
            ("BOTTOM", [(-1, 1, -1), (1, 1, -1), (1, -1, -1), (-1, -1, -1)], (0, 0, -1)),
            ("FRONT", [(-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1)], (0, -1, 0)),
            ("BACK", [(1, 1, -1), (-1, 1, -1), (-1, 1, 1), (1, 1, 1)], (0, 1, 0)),
            ("RIGHT", [(1, -1, -1), (1, 1, -1), (1, 1, 1), (1, -1, 1)], (1, 0, 0)),
            ("LEFT", [(-1, 1, -1), (-1, -1, -1), (-1, -1, 1), (-1, 1, 1)], (-1, 0, 0)),
        ]

        cos_az, sin_az = math.cos(rad_az), math.sin(rad_az)
        cos_el, sin_el = math.cos(rad_el), math.sin(rad_el)

        visible_faces = []
        for name, corners, normal in faces_def:
            nx, ny, nz = normal
            # Normal depth component
            n_view = nx * sin_az * cos_el - ny * cos_az * cos_el + nz * sin_el
            if n_view > 0.04:  # Facing camera
                pts_2d = []
                avg_depth = 0.0
                for c in corners:
                    px, py, d = self._project(c[0], c[1], c[2], cx, cy, scale)
                    pts_2d.append(QPointF(px, py))
                    avg_depth += d
                avg_depth /= 4.0
                visible_faces.append((avg_depth, name, pts_2d, n_view))

        # Sort back to front (painter's algorithm)
        visible_faces.sort(key=lambda item: item[0])
        self._rendered_faces = visible_faces

        font_label = QFont("Segoe UI", 7, QFont.Bold)
        painter.setFont(font_label)

        for depth, name, pts, normal_z in visible_faces:
            poly = QPolygonF(pts)
            is_hover = (self._hovered_element == f"face:{name}")

            # Precise Fusion 360 metallic shading
            if is_hover:
                # Fusion cyan accent
                grad = QLinearGradient(pts[0], pts[2])
                grad.setColorAt(0.0, QColor(0, 140, 220))
                grad.setColorAt(1.0, QColor(0, 105, 180))
                painter.setBrush(QBrush(grad))
                painter.setPen(QPen(QColor(120, 200, 255), 1.2))
            else:
                # Base slate gray shaded by lighting angle
                light_val = int(48 + normal_z * 32)
                c_top = QColor(light_val + 14, light_val + 16, light_val + 20)
                c_bot = QColor(light_val, light_val + 2, light_val + 5)
                grad = QLinearGradient(pts[0], pts[2])
                grad.setColorAt(0.0, c_top)
                grad.setColorAt(1.0, c_bot)
                painter.setBrush(QBrush(grad))
                painter.setPen(QPen(QColor(85, 95, 108), 1.0))

            painter.drawPolygon(poly)

            # Draw Face Title
            poly_center = QPointF(
                sum(p.x() for p in pts) / 4.0,
                sum(p.y() for p in pts) / 4.0
            )
            painter.setPen(QColor(255, 255, 255) if is_hover else QColor(220, 225, 230))
            painter.drawText(QRectF(poly_center.x() - 18, poly_center.y() - 8, 36, 16), Qt.AlignCenter, name)

        # 4. Directional Flip Arrows (Up, Down, Left, Right)
        arrow_color = QColor(190, 200, 210, 220)
        arrow_hover = QColor(0, 160, 255)

        # Up Arrow
        up_rect = QRectF(cx - 7, cy - 47, 14, 10)
        self._action_rects["arrow:up"] = up_rect
        is_u = (self._hovered_element == "arrow:up")
        p_up = QPolygonF([QPointF(cx, cy - 47), QPointF(cx - 5, cy - 39), QPointF(cx + 5, cy - 39)])
        painter.setBrush(arrow_hover if is_u else arrow_color)
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(p_up)

        # Down Arrow
        dn_rect = QRectF(cx - 7, cy + 37, 14, 10)
        self._action_rects["arrow:down"] = dn_rect
        is_d = (self._hovered_element == "arrow:down")
        p_dn = QPolygonF([QPointF(cx, cy + 47), QPointF(cx - 5, cy + 39), QPointF(cx + 5, cy + 39)])
        painter.setBrush(arrow_hover if is_d else arrow_color)
        painter.drawPolygon(p_dn)

        # Left Arrow
        lt_rect = QRectF(cx - 47, cy - 7, 10, 14)
        self._action_rects["arrow:left"] = lt_rect
        is_l = (self._hovered_element == "arrow:left")
        p_lt = QPolygonF([QPointF(cx - 47, cy), QPointF(cx - 39, cy - 5), QPointF(cx - 39, cy + 5)])
        painter.setBrush(arrow_hover if is_l else arrow_color)
        painter.drawPolygon(p_lt)

        # Right Arrow
        rt_rect = QRectF(cx + 37, cy - 7, 10, 14)
        self._action_rects["arrow:right"] = rt_rect
        is_r = (self._hovered_element == "arrow:right")
        p_rt = QPolygonF([QPointF(cx + 47, cy), QPointF(cx + 39, cy - 5), QPointF(cx + 39, cy + 5)])
        painter.setBrush(arrow_hover if is_r else arrow_color)
        painter.drawPolygon(p_rt)

        # 5. Screen Plane 90° Roll Curved Arrows (Top Right)
        # Roll CCW
        ccw_rect = QRectF(w - 24, 6, 16, 16)
        self._action_rects["roll:ccw"] = ccw_rect
        is_ccw = (self._hovered_element == "roll:ccw")
        painter.setPen(QPen(arrow_hover if is_ccw else arrow_color, 1.6))
        painter.setBrush(Qt.NoBrush)
        painter.drawArc(QRectF(w - 22, 8, 12, 12), 45 * 16, 180 * 16)
        # Arrowhead for CCW
        painter.setBrush(arrow_hover if is_ccw else arrow_color)
        painter.setPen(Qt.NoPen)
        p_head_ccw = QPolygonF([QPointF(w - 22, 14), QPointF(w - 25, 11), QPointF(w - 19, 11)])
        painter.drawPolygon(p_head_ccw)

        # 6. Home Button (Top Left)
        home_rect = QRectF(5, 5, 18, 18)
        self._action_rects["home"] = home_rect
        is_home = (self._hovered_element == "home")
        painter.setBrush(QColor(60, 68, 78, 220) if is_home else QColor(40, 44, 52, 190))
        painter.setPen(QPen(QColor(0, 160, 255) if is_home else QColor(70, 80, 92), 1))
        painter.drawRoundedRect(home_rect, 3, 3)

        # Draw Isometric House Outline
        painter.setPen(QPen(QColor(255, 255, 255) if is_home else QColor(200, 205, 215), 1.2))
        painter.setBrush(Qt.NoBrush)
        hx, hy = home_rect.center().x(), home_rect.center().y()
        house_roof = QPolygonF([QPointF(hx, hy - 4.5), QPointF(hx - 4.5, hy), QPointF(hx + 4.5, hy)])
        painter.drawPolyline(house_roof)
        painter.drawRect(QRectF(hx - 3.5, hy, 7, 4.5))

        # 7. View Options Dropdown Trigger Chevron (Bottom Right)
        menu_rect = QRectF(w - 18, h - 18, 14, 14)
        self._action_rects["menu"] = menu_rect
        is_menu = (self._hovered_element == "menu")
        painter.setBrush(QColor(60, 68, 78, 200) if is_menu else QColor(36, 40, 48, 160))
        painter.setPen(QPen(QColor(0, 160, 255) if is_menu else QColor(65, 75, 88), 1))
        painter.drawRoundedRect(menu_rect, 2.5, 2.5)

        # Chevron down
        painter.setPen(QPen(QColor(255, 255, 255) if is_menu else QColor(180, 185, 195), 1.2))
        mx, my = menu_rect.center().x(), menu_rect.center().y()
        p_chev = QPolygonF([QPointF(mx - 3, my - 1.5), QPointF(mx, my + 1.5), QPointF(mx + 3, my - 1.5)])
        painter.drawPolyline(p_chev)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.position()
            self._drag_start_pos = pos
            elem = self._detect_element(pos)

            if elem == "home":
                self.view_selected.emit("home")
                return
            elif elem == "menu":
                self._show_view_menu(event.globalPosition().toPoint())
                return
            elif elem == "arrow:up":
                self._flip_view_vertical(1)
                return
            elif elem == "arrow:down":
                self._flip_view_vertical(-1)
                return
            elif elem == "arrow:left":
                self.orbit_delta.emit(-90.0, 0.0)
                return
            elif elem == "arrow:right":
                self.orbit_delta.emit(90.0, 0.0)
                return
            elif elem == "roll:ccw":
                self.orbit_delta.emit(-90.0, 0.0)
                return
            elif elem and elem.startswith("face:"):
                face_name = elem.split(":")[1].lower()
                self.view_selected.emit(face_name)
                return

            # Default: initiate drag orbit
            self._is_dragging = True
            self._last_mouse_pos = pos

        elif event.button() == Qt.RightButton:
            self._show_view_menu(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        pos = event.position()
        if self._is_dragging and self._last_mouse_pos:
            dx = pos.x() - self._last_mouse_pos.x()
            dy = pos.y() - self._last_mouse_pos.y()
            self._last_mouse_pos = pos
            self.orbit_delta.emit(dx * 1.5, -dy * 1.5)
        else:
            old_hover = self._hovered_element
            self._hovered_element = self._detect_element(pos)
            if old_hover != self._hovered_element:
                self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_dragging = False
            self._last_mouse_pos = None

    def _flip_view_vertical(self, direction: int):
        """Flips camera up or down 90 degrees."""
        if abs(self.elevation) < 45.0:
            new_el = 89.9 if direction > 0 else -89.9
            self.update_orientation(self.azimuth, new_el)
            self.orbit_delta.emit(0.0, new_el - self.elevation)
        else:
            # From TOP/BOTTOM to side
            new_el = 0.0
            new_az = (self.azimuth + (180.0 if direction < 0 else 0.0)) % 360.0
            self.update_orientation(new_az, new_el)
            self.orbit_delta.emit(new_az - self.azimuth, -self.elevation)

    def _detect_element(self, pos: QPointF) -> str:
        # Check action rects first
        for name, rect in self._action_rects.items():
            if rect.contains(pos):
                return name

        # Check 3D faces from front to back
        for depth, name, pts, normal_z in reversed(self._rendered_faces):
            poly = QPolygonF(pts)
            if poly.containsPoint(pos, Qt.OddEvenFill):
                return f"face:{name}"

        return None

    def _show_view_menu(self, global_pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2b3038;
                border: 1px solid #454d59;
                color: #e0e0e0;
                font-family: 'Segoe UI';
                font-size: 11px;
                padding: 4px;
            }
            QMenu::item {
                padding: 5px 22px 5px 20px;
                border-radius: 2px;
            }
            QMenu::item:selected {
                background-color: #0082c8;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background: #3e4652;
                margin: 4px 6px;
            }
        """)

        act_home = menu.addAction("Go Home")
        act_home.triggered.connect(lambda: self.view_selected.emit("home"))

        menu.addSeparator()

        act_ortho = menu.addAction("Orthographic")
        act_ortho.setCheckable(True)
        act_ortho.setChecked(self.projection_mode == "orthographic")
        act_ortho.triggered.connect(lambda: self._set_proj("orthographic"))

        act_persp = menu.addAction("Perspective")
        act_persp.setCheckable(True)
        act_persp.setChecked(self.projection_mode == "perspective")
        act_persp.triggered.connect(lambda: self._set_proj("perspective"))

        menu.addSeparator()

        views = [
            ("Top", "top"), ("Bottom", "bottom"),
            ("Front", "front"), ("Back", "back"),
            ("Right", "right"), ("Left", "left")
        ]
        for label, code in views:
            act = menu.addAction(label)
            act.triggered.connect(lambda checked=False, c=code: self.view_selected.emit(c))

        menu.addSeparator()
        act_fit = menu.addAction("Fit All")
        act_fit.triggered.connect(self.fit_requested.emit)

        menu.exec(global_pos)

    def _set_proj(self, mode: str):
        self.set_projection_mode(mode)
        self.projection_toggled.emit(mode)
