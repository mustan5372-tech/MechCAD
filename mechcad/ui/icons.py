"""
MechCAD Professional Vector CAD Icon Engine
Generates crisp, high-resolution Autodesk Fusion 360-style engineering icons.
Renders directly via QPainter to guarantee pixel-perfect rendering across all displays and DPIs.
"""

from typing import Dict, Optional
from PySide6.QtGui import (
    QIcon, QPixmap, QPainter, QColor, QPen, QBrush, QPainterPath, QFont
)
from PySide6.QtCore import Qt, QPointF, QRectF

from mechcad.ui.theme import ThemeColors


class CADIcons:
    """Factory for vector-drawn engineering tool icons."""

    _cache: Dict[str, QIcon] = {}

    @classmethod
    def get(cls, name: str, size: int = 24) -> QIcon:
        key = f"{name}_{size}"
        if key in cls._cache:
            return cls._cache[key]
        icon = cls._render_icon(name, size)
        cls._cache[key] = icon
        return icon

    @classmethod
    def _render_icon(cls, name: str, size: int) -> QIcon:
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        p = QPainter(pixmap)
        p.setRenderHint(QPainter.Antialiasing)

        s = float(size)
        c_white = QColor(240, 240, 240)
        c_blue = QColor(0, 150, 240)
        c_orange = QColor(255, 160, 0)
        c_green = QColor(40, 190, 80)
        c_red = QColor(235, 60, 60)
        c_steel = QColor(100, 125, 150)
        c_steel_dark = QColor(65, 85, 105)
        c_steel_light = QColor(140, 170, 200)

        # -------------------------------------------------------------
        # 1. 3D SOLID MODELING ICONS
        # -------------------------------------------------------------
        if name in ("extrude", "solid_extrude"):
            # Isometric cube
            p.setPen(QPen(c_white, 1.2))
            p.setBrush(QBrush(c_steel_light))
            p.drawPolygon([QPointF(s*0.5, s*0.12), QPointF(s*0.88, s*0.3), QPointF(s*0.5, s*0.48), QPointF(s*0.12, s*0.3)])
            p.setBrush(QBrush(c_steel_dark))
            p.drawPolygon([QPointF(s*0.12, s*0.3), QPointF(s*0.5, s*0.48), QPointF(s*0.5, s*0.88), QPointF(s*0.12, s*0.7)])
            p.setBrush(QBrush(c_steel))
            p.drawPolygon([QPointF(s*0.88, s*0.3), QPointF(s*0.5, s*0.48), QPointF(s*0.5, s*0.88), QPointF(s*0.88, s*0.7)])
            # Upward orange extrude arrow
            p.setPen(QPen(c_orange, 2.0))
            p.drawLine(QPointF(s*0.5, s*0.7), QPointF(s*0.5, s*0.18))
            p.drawPolyline([QPointF(s*0.4, s*0.32), QPointF(s*0.5, s*0.18), QPointF(s*0.6, s*0.32)])

        elif name in ("revolve", "solid_revolve"):
            # Revolved cylinder profile with circular arrow
            p.setPen(QPen(c_white, 1.2))
            p.setBrush(QBrush(c_steel))
            p.drawEllipse(QRectF(s*0.2, s*0.55, s*0.6, s*0.3))
            p.drawRect(QRectF(s*0.2, s*0.25, s*0.6, s*0.45))
            p.setBrush(QBrush(c_steel_light))
            p.drawEllipse(QRectF(s*0.2, s*0.1, s*0.6, s*0.3))
            # Curved revolution arrow
            p.setPen(QPen(c_orange, 2.0))
            p.setBrush(Qt.NoBrush)
            p.drawArc(QRectF(s*0.08, s*0.15, s*0.84, s*0.7), 45*16, 270*16)
            p.drawLine(QPointF(s*0.88, s*0.5), QPointF(s*0.75, s*0.4))

        elif name in ("hole", "solid_hole"):
            # Metal block with counterbore hole
            p.setPen(QPen(c_white, 1.2))
            p.setBrush(QBrush(c_steel))
            p.drawRoundedRect(QRectF(s*0.15, s*0.15, s*0.7, s*0.7), 2, 2)
            p.setBrush(QBrush(QColor(30, 30, 35)))
            p.drawEllipse(QRectF(s*0.3, s*0.3, s*0.4, s*0.4))
            p.setBrush(QBrush(QColor(10, 10, 15)))
            p.drawEllipse(QRectF(s*0.4, s*0.4, s*0.2, s*0.2))
            p.setPen(QPen(c_orange, 1.2, Qt.DashLine))
            p.drawLine(QPointF(s*0.5, s*0.1), QPointF(s*0.5, s*0.9))

        elif name in ("fillet", "solid_fillet"):
            # 90 deg corner with rounded fillet radius
            p.setPen(QPen(c_white, 1.5))
            p.setBrush(QBrush(c_steel_dark))
            path = QPainterPath()
            path.moveTo(s*0.15, s*0.85)
            path.lineTo(s*0.85, s*0.85)
            path.lineTo(s*0.85, s*0.45)
            path.arcTo(QRectF(s*0.15, s*0.15, s*0.7, s*0.7), 0, 90)
            path.lineTo(s*0.15, s*0.85)
            p.drawPath(path)
            p.setPen(QPen(c_orange, 2.0))
            p.drawArc(QRectF(s*0.15, s*0.15, s*0.7, s*0.7), 0*16, 90*16)

        elif name in ("chamfer", "solid_chamfer"):
            # 90 deg corner with 45 deg chamfer bevel
            p.setPen(QPen(c_white, 1.5))
            p.setBrush(QBrush(c_steel_dark))
            path = QPainterPath()
            path.moveTo(s*0.15, s*0.85)
            path.lineTo(s*0.85, s*0.85)
            path.lineTo(s*0.85, s*0.45)
            path.lineTo(s*0.45, s*0.15)
            path.lineTo(s*0.15, s*0.15)
            path.closeSubpath()
            p.drawPath(path)
            p.setPen(QPen(c_orange, 2.2))
            p.drawLine(QPointF(s*0.85, s*0.45), QPointF(s*0.45, s*0.15))

        elif name in ("shell", "solid_shell"):
            # Cube hollowed with wall thickness
            p.setPen(QPen(c_white, 1.2))
            p.setBrush(QBrush(c_steel))
            p.drawRect(QRectF(s*0.12, s*0.12, s*0.76, s*0.76))
            p.setBrush(QBrush(QColor(25, 25, 30)))
            p.drawRect(QRectF(s*0.28, s*0.28, s*0.44, s*0.44))
            p.setPen(QPen(c_orange, 1.4))
            p.drawRect(QRectF(s*0.28, s*0.28, s*0.44, s*0.44))

        elif name in ("combine", "solid_combine"):
            # Boolean union / intersect
            p.setPen(QPen(c_blue, 1.4))
            p.setBrush(QBrush(QColor(0, 150, 240, 120)))
            p.drawEllipse(QRectF(s*0.12, s*0.25, s*0.5, s*0.5))
            p.setPen(QPen(c_orange, 1.4))
            p.setBrush(QBrush(QColor(255, 160, 0, 120)))
            p.drawEllipse(QRectF(s*0.38, s*0.25, s*0.5, s*0.5))

        elif name in ("split_body", "solid_split"):
            # Solid cube sliced by a diagonal red plane
            p.setPen(QPen(c_white, 1.2))
            p.setBrush(QBrush(c_steel))
            p.drawRect(QRectF(s*0.2, s*0.2, s*0.6, s*0.6))
            p.setPen(QPen(c_red, 2.0))
            p.drawLine(QPointF(s*0.1, s*0.75), QPointF(s*0.9, s*0.25))

        elif name in ("mirror", "solid_mirror"):
            # Symmetrical shapes across mirror plane
            p.setPen(QPen(c_blue, 1.2, Qt.DashLine))
            p.drawLine(QPointF(s*0.5, s*0.1), QPointF(s*0.5, s*0.9))
            p.setPen(QPen(c_white, 1.2))
            p.setBrush(QBrush(c_steel))
            p.drawRect(QRectF(s*0.15, s*0.3, s*0.25, s*0.4))
            p.setBrush(QBrush(c_steel_light))
            p.drawRect(QRectF(s*0.6, s*0.3, s*0.25, s*0.4))

        elif name in ("pattern_linear", "solid_pattern"):
            # 2x2 grid of patterned cubes
            p.setPen(QPen(c_orange, 1.2))
            p.setBrush(QBrush(c_steel))
            sz_box = s * 0.28
            p.drawRect(QRectF(s*0.15, s*0.15, sz_box, sz_box))
            p.drawRect(QRectF(s*0.57, s*0.15, sz_box, sz_box))
            p.drawRect(QRectF(s*0.15, s*0.57, sz_box, sz_box))
            p.drawRect(QRectF(s*0.57, s*0.57, sz_box, sz_box))

        elif name in ("pattern_circular", "solid_circ_pattern"):
            # Circular array of dots around center
            p.setPen(QPen(c_orange, 1.5))
            p.setBrush(QBrush(c_orange))
            p.drawEllipse(QPointF(s*0.5, s*0.5), 2.5, 2.5)
            p.setBrush(QBrush(c_blue))
            for ang_deg in [0, 60, 120, 180, 240, 300]:
                rad = math.radians(ang_deg)
                px = s*0.5 + s*0.32 * math.cos(rad)
                py = s*0.5 + s*0.32 * math.sin(rad)
                p.drawEllipse(QPointF(px, py), 2.5, 2.5)

        elif name in ("construct_plane", "plane"):
            # Translucent offset plane
            p.setPen(QPen(c_orange, 1.4))
            p.setBrush(QBrush(QColor(255, 160, 0, 70)))
            p.drawPolygon([QPointF(s*0.2, s*0.3), QPointF(s*0.8, s*0.15), QPointF(s*0.8, s*0.7), QPointF(s*0.2, s*0.85)])
            p.setPen(QPen(c_blue, 1.8))
            p.drawLine(QPointF(s*0.5, s*0.5), QPointF(s*0.5, s*0.2))
            p.drawPolyline([QPointF(s*0.42, s*0.28), QPointF(s*0.5, s*0.2), QPointF(s*0.58, s*0.28)])

        # -------------------------------------------------------------
        # 2. SKETCH ICONS
        # -------------------------------------------------------------
        elif name in ("create_sketch", "sketch"):
            # Grid plane with pencil drawing line
            p.setPen(QPen(QColor(120, 120, 130), 1.0))
            p.drawLine(s*0.1, s*0.7, s*0.8, s*0.7)
            p.drawLine(s*0.1, s*0.4, s*0.8, s*0.4)
            p.drawLine(s*0.3, s*0.2, s*0.3, s*0.9)
            p.drawLine(s*0.6, s*0.2, s*0.6, s*0.9)
            # Pencil
            p.setPen(QPen(c_orange, 2.2))
            p.drawLine(s*0.25, s*0.75, s*0.75, s*0.25)
            p.setBrush(QBrush(c_orange))
            p.drawEllipse(QPointF(s*0.25, s*0.75), 2.5, 2.5)

        elif name == "sketch_line":
            p.setPen(QPen(c_orange, 2.0))
            p.drawLine(QPointF(s*0.2, s*0.8), QPointF(s*0.8, s*0.2))
            p.setBrush(QBrush(c_white))
            p.drawEllipse(QPointF(s*0.2, s*0.8), 2.5, 2.5)
            p.drawEllipse(QPointF(s*0.8, s*0.2), 2.5, 2.5)

        elif name == "sketch_rect":
            p.setPen(QPen(c_orange, 1.8))
            p.setBrush(QBrush(QColor(0, 150, 240, 60)))
            p.drawRect(QRectF(s*0.18, s*0.22, s*0.64, s*0.56))
            p.setBrush(QBrush(c_white))
            p.drawEllipse(QPointF(s*0.18, s*0.22), 2.5, 2.5)
            p.drawEllipse(QPointF(s*0.82, s*0.78), 2.5, 2.5)

        elif name == "sketch_center_rect":
            p.setPen(QPen(c_orange, 1.8))
            p.setBrush(QBrush(QColor(0, 150, 240, 60)))
            p.drawRect(QRectF(s*0.18, s*0.22, s*0.64, s*0.56))
            p.setPen(QPen(c_blue, 1.2))
            p.drawLine(s*0.5, s*0.35, s*0.5, s*0.65)
            p.drawLine(s*0.35, s*0.5, s*0.65, s*0.5)

        elif name == "sketch_circle":
            p.setPen(QPen(c_orange, 1.8))
            p.setBrush(QBrush(QColor(0, 150, 240, 60)))
            p.drawEllipse(QRectF(s*0.18, s*0.18, s*0.64, s*0.64))
            p.setBrush(QBrush(c_white))
            p.drawEllipse(QPointF(s*0.5, s*0.5), 2.5, 2.5)

        elif name == "sketch_dimension":
            # Dimension arrows with witness lines
            p.setPen(QPen(c_white, 1.0))
            p.drawLine(s*0.15, s*0.2, s*0.15, s*0.8)
            p.drawLine(s*0.85, s*0.2, s*0.85, s*0.8)
            p.setPen(QPen(c_orange, 1.8))
            p.drawLine(s*0.15, s*0.5, s*0.85, s*0.5)
            p.drawPolyline([QPointF(s*0.28, s*0.42), QPointF(s*0.15, s*0.5), QPointF(s*0.28, s*0.58)])
            p.drawPolyline([QPointF(s*0.72, s*0.42), QPointF(s*0.85, s*0.5), QPointF(s*0.72, s*0.58)])

        elif name == "finish_sketch":
            # Big green checkmark
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(c_green))
            p.drawEllipse(QRectF(s*0.08, s*0.08, s*0.84, s*0.84))
            p.setPen(QPen(c_white, 2.4))
            p.drawPolyline([QPointF(s*0.28, s*0.5), QPointF(s*0.44, s*0.68), QPointF(s*0.72, s*0.34)])

        # -------------------------------------------------------------
        # 3. INSPECT & UTILITY ICONS
        # -------------------------------------------------------------
        elif name in ("measure", "inspect_measure"):
            # Caliper / ruler
            p.setPen(QPen(c_orange, 1.8))
            p.drawLine(s*0.15, s*0.8, s*0.85, s*0.2)
            p.drawLine(s*0.15, s*0.8, s*0.35, s*0.95)
            p.drawLine(s*0.85, s*0.2, s*0.65, s*0.05)

        elif name in ("parameters", "fx"):
            # fx symbol
            p.setPen(QPen(c_blue, 2.0))
            p.setFont(QFont("Segoe UI", int(s*0.45), QFont.Bold))
            p.drawText(QRectF(0, 0, s, s), Qt.AlignCenter, "fx")

        elif name == "data_panel":
            # 9-dot grid
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(c_white))
            rad = s * 0.08
            for ix in [0.25, 0.5, 0.75]:
                for iy in [0.25, 0.5, 0.75]:
                    p.drawEllipse(QPointF(s*ix, s*iy), rad, rad)

        elif name == "save":
            # Floppy disk
            p.setPen(QPen(c_white, 1.2))
            p.setBrush(QBrush(c_steel_dark))
            p.drawRect(QRectF(s*0.18, s*0.18, s*0.64, s*0.64))
            p.setBrush(QBrush(c_white))
            p.drawRect(QRectF(s*0.3, s*0.18, s*0.4, s*0.25))

        elif name == "undo":
            p.setPen(QPen(c_white, 2.0))
            p.setBrush(Qt.NoBrush)
            p.drawArc(QRectF(s*0.2, s*0.25, s*0.6, s*0.6), 45*16, 200*16)
            p.drawLine(QPointF(s*0.25, s*0.3), QPointF(s*0.4, s*0.2))
            p.drawLine(QPointF(s*0.25, s*0.3), QPointF(s*0.3, s*0.45))

        elif name == "redo":
            p.setPen(QPen(c_white, 2.0))
            p.setBrush(Qt.NoBrush)
            p.drawArc(QRectF(s*0.2, s*0.25, s*0.6, s*0.6), -45*16, -200*16)
            p.drawLine(QPointF(s*0.75, s*0.3), QPointF(s*0.6, s*0.2))
            p.drawLine(QPointF(s*0.75, s*0.3), QPointF(s*0.7, s*0.45))

        # -------------------------------------------------------------
        # 4. NAVIGATION BAR ICONS
        # -------------------------------------------------------------
        elif name == "nav_orbit":
            p.setPen(QPen(c_white, 1.5))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(QRectF(s*0.2, s*0.2, s*0.6, s*0.6))
            p.setPen(QPen(c_orange, 1.8))
            p.drawLine(s*0.2, s*0.5, s*0.8, s*0.5)

        elif name == "nav_look":
            p.setPen(QPen(c_white, 1.5))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(QRectF(s*0.15, s*0.3, s*0.7, s*0.4))
            p.setBrush(QBrush(c_blue))
            p.drawEllipse(QPointF(s*0.5, s*0.5), 3, 3)

        elif name == "nav_pan":
            p.setPen(QPen(c_white, 1.5))
            p.setBrush(QBrush(c_steel))
            p.drawRoundedRect(QRectF(s*0.25, s*0.35, s*0.5, s*0.45), 3, 3)

        elif name == "nav_zoom":
            p.setPen(QPen(c_white, 1.8))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(QRectF(s*0.2, s*0.2, s*0.45, s*0.45))
            p.drawLine(s*0.55, s*0.55, s*0.8, s*0.8)

        elif name == "nav_fit":
            p.setPen(QPen(c_white, 1.8))
            d_l = s * 0.22
            p.drawPolyline([QPointF(s*0.15, s*0.15 + d_l), QPointF(s*0.15, s*0.15), QPointF(s*0.15 + d_l, s*0.15)])
            p.drawPolyline([QPointF(s*0.85 - d_l, s*0.15), QPointF(s*0.85, s*0.15), QPointF(s*0.85, s*0.15 + d_l)])
            p.drawPolyline([QPointF(s*0.15, s*0.85 - d_l), QPointF(s*0.15, s*0.85), QPointF(s*0.15 + d_l, s*0.85)])
            p.drawPolyline([QPointF(s*0.85 - d_l, s*0.85), QPointF(s*0.85, s*0.85), QPointF(s*0.85, s*0.85 - d_l)])

        elif name == "nav_display":
            p.setPen(QPen(c_white, 1.2))
            p.setBrush(QBrush(c_steel_dark))
            p.drawRect(QRectF(s*0.18, s*0.18, s*0.64, s*0.5))
            p.drawLine(s*0.4, s*0.8, s*0.6, s*0.8)
            p.drawLine(s*0.5, s*0.68, s*0.5, s*0.8)

        elif name == "nav_grid":
            p.setPen(QPen(c_white, 1.2))
            p.drawRect(QRectF(s*0.18, s*0.18, s*0.64, s*0.64))
            p.drawLine(s*0.5, s*0.18, s*0.5, s*0.82)
            p.drawLine(s*0.18, s*0.5, s*0.82, s*0.5)

        # -------------------------------------------------------------
        # 5. BROWSER HIERARCHY & TREE ICONS
        # -------------------------------------------------------------
        elif name == "folder":
            p.setPen(QPen(c_white, 1.0))
            p.setBrush(QBrush(c_steel_light))
            p.drawPolygon([QPointF(s*0.15, s*0.25), QPointF(s*0.45, s*0.25), QPointF(s*0.55, s*0.38), QPointF(s*0.85, s*0.38), QPointF(s*0.85, s*0.8), QPointF(s*0.15, s*0.8)])

        elif name == "component":
            # Fusion component cube with active pin
            p.setPen(QPen(c_white, 1.0))
            p.setBrush(QBrush(c_steel_light))
            p.drawPolygon([QPointF(s*0.5, s*0.15), QPointF(s*0.85, s*0.35), QPointF(s*0.5, s*0.55), QPointF(s*0.15, s*0.35)])
            p.setBrush(QBrush(c_steel))
            p.drawPolygon([QPointF(s*0.15, s*0.35), QPointF(s*0.5, s*0.55), QPointF(s*0.5, s*0.85), QPointF(s*0.15, s*0.65)])
            p.drawPolygon([QPointF(s*0.85, s*0.35), QPointF(s*0.5, s*0.55), QPointF(s*0.5, s*0.85), QPointF(s*0.85, s*0.65)])

        elif name == "browser_body":
            # Solid body cylinder
            p.setPen(QPen(c_white, 1.0))
            p.setBrush(QBrush(c_steel))
            p.drawEllipse(QRectF(s*0.2, s*0.55, s*0.6, s*0.3))
            p.drawRect(QRectF(s*0.2, s*0.25, s*0.6, s*0.45))
            p.setBrush(QBrush(c_steel_light))
            p.drawEllipse(QRectF(s*0.2, s*0.1, s*0.6, s*0.3))

        elif name == "browser_sketch":
            # Sketch icon
            p.setPen(QPen(c_orange, 1.5))
            p.drawLine(s*0.2, s*0.8, s*0.8, s*0.2)
            p.setBrush(QBrush(c_white))
            p.drawEllipse(QPointF(s*0.2, s*0.8), 2.0, 2.0)
            p.drawEllipse(QPointF(s*0.8, s*0.2), 2.0, 2.0)

        elif name == "origin":
            # 3D Origin Triad
            p.setPen(QPen(c_red, 1.8))
            p.drawLine(s*0.5, s*0.5, s*0.85, s*0.5)
            p.setPen(QPen(c_green, 1.8))
            p.drawLine(s*0.5, s*0.5, s*0.5, s*0.15)
            p.setPen(QPen(c_blue, 1.8))
            p.drawLine(s*0.5, s*0.5, s*0.25, s*0.75)
            p.setBrush(QBrush(c_white))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(s*0.5, s*0.5), 2.2, 2.2)

        elif name == "eye_on":
            # Visible eye
            p.setPen(QPen(QColor(200, 210, 220), 1.3))
            p.setBrush(Qt.NoBrush)
            p.drawArc(QRectF(s*0.1, s*0.2, s*0.8, s*0.6), 40*16, 100*16)
            p.drawArc(QRectF(s*0.1, s*0.2, s*0.8, s*0.6), 220*16, 100*16)
            p.setBrush(QBrush(c_blue))
            p.drawEllipse(QPointF(s*0.5, s*0.5), s*0.16, s*0.16)

        elif name == "eye_off":
            # Hidden / slashed eye
            p.setPen(QPen(QColor(100, 110, 120, 160), 1.2))
            p.setBrush(Qt.NoBrush)
            p.drawArc(QRectF(s*0.15, s*0.25, s*0.7, s*0.5), 40*16, 100*16)
            p.drawArc(QRectF(s*0.15, s*0.25, s*0.7, s*0.5), 220*16, 100*16)
            p.setPen(QPen(QColor(180, 70, 70), 1.4))
            p.drawLine(s*0.2, s*0.2, s*0.8, s*0.8)

        elif name == "doc_settings":
            # Gear / Settings
            p.setPen(QPen(c_white, 1.2))
            p.setBrush(QBrush(c_steel))
            p.drawEllipse(QRectF(s*0.25, s*0.25, s*0.5, s*0.5))
            p.setBrush(QBrush(QColor(30, 35, 42)))
            p.drawEllipse(QRectF(s*0.4, s*0.4, s*0.2, s*0.2))

        elif name == "named_views":
            # Camera
            p.setPen(QPen(c_white, 1.2))
            p.setBrush(QBrush(c_steel))
            p.drawRoundedRect(QRectF(s*0.18, s*0.3, s*0.64, s*0.45), 2, 2)
            p.drawRect(QRectF(s*0.35, s*0.2, s*0.3, s*0.12))
            p.setBrush(QBrush(c_blue))
            p.drawEllipse(QPointF(s*0.5, s*0.52), s*0.14, s*0.14)

        # -------------------------------------------------------------
        # 6. TIMELINE PLAYBACK ICONS
        # -------------------------------------------------------------
        elif name == "time_start":
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(c_white))
            p.drawRect(QRectF(s*0.2, s*0.25, s*0.12, s*0.5))
            p.drawPolygon([QPointF(s*0.75, s*0.25), QPointF(s*0.4, s*0.5), QPointF(s*0.75, s*0.75)])

        elif name == "time_step_back":
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(c_white))
            p.drawPolygon([QPointF(s*0.65, s*0.25), QPointF(s*0.35, s*0.5), QPointF(s*0.65, s*0.75)])

        elif name == "time_step_fwd":
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(c_white))
            p.drawPolygon([QPointF(s*0.35, s*0.25), QPointF(s*0.65, s*0.5), QPointF(s*0.35, s*0.75)])

        elif name == "time_end":
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(c_white))
            p.drawPolygon([QPointF(s*0.25, s*0.25), QPointF(s*0.6, s*0.5), QPointF(s*0.25, s*0.75)])
            p.drawRect(QRectF(s*0.68, s*0.25, s*0.12, s*0.5))

        elif name == "time_play":
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(c_green))
            p.drawPolygon([QPointF(s*0.3, s*0.2), QPointF(s*0.8, s*0.5), QPointF(s*0.3, s*0.8)])

        else:
            # Fallback CAD gear
            p.setPen(QPen(c_white, 1.2))
            p.setBrush(QBrush(c_steel))
            p.drawEllipse(QRectF(s*0.25, s*0.25, s*0.5, s*0.5))

        p.end()
        return QIcon(pixmap)
