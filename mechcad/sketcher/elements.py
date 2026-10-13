"""
MechCAD Sketcher Elements Data Model
Represents 2D geometric primitives in sketch plane coordinates (u, v).
"""

from typing import Tuple, Dict, Any, List
import math

class SketchEntity:
    def __init__(self, entity_id: str, is_construction: bool = False):
        self.entity_id = entity_id
        self.is_construction = is_construction

    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError


class Point2D(SketchEntity):
    def __init__(self, entity_id: str, u: float, v: float, is_construction: bool = False, is_fixed: bool = False):
        super().__init__(entity_id, is_construction)
        self.u = float(u)
        self.v = float(v)
        self.is_fixed = is_fixed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "point",
            "id": self.entity_id,
            "u": self.u,
            "v": self.v,
            "is_construction": self.is_construction,
            "is_fixed": self.is_fixed,
        }


class Line2D(SketchEntity):
    def __init__(self, entity_id: str, p1_id: str, p2_id: str, is_construction: bool = False):
        super().__init__(entity_id, is_construction)
        self.p1_id = p1_id
        self.p2_id = p2_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "line",
            "id": self.entity_id,
            "p1": self.p1_id,
            "p2": self.p2_id,
            "is_construction": self.is_construction,
        }


class Circle2D(SketchEntity):
    def __init__(self, entity_id: str, center_id: str, radius: float, is_construction: bool = False):
        super().__init__(entity_id, is_construction)
        self.center_id = center_id
        self.radius = float(radius)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "circle",
            "id": self.entity_id,
            "center": self.center_id,
            "radius": self.radius,
            "is_construction": self.is_construction,
        }


class Arc2D(SketchEntity):
    def __init__(self, entity_id: str, center_id: str, start_id: str, end_id: str, radius: float, is_construction: bool = False):
        super().__init__(entity_id, is_construction)
        self.center_id = center_id
        self.start_id = start_id
        self.end_id = end_id
        self.radius = float(radius)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "arc",
            "id": self.entity_id,
            "center": self.center_id,
            "start": self.start_id,
            "end": self.end_id,
            "radius": self.radius,
            "is_construction": self.is_construction,
        }
