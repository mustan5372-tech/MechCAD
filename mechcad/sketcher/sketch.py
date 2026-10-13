"""
MechCAD Sketch Container & Open CASCADE Wire/Face Builder
Combines 2D elements, SolveSpace constraints, and conversion to precise 3D OCCT profiles.
"""

from typing import Dict, List, Tuple, Optional, Any
import math

from OCP.gp import gp_Pnt, gp_Vec, gp_Ax2, gp_Dir, gp_Circ, gp_Pln
from OCP.BRepBuilderAPI import (
    BRepBuilderAPI_MakeEdge,
    BRepBuilderAPI_MakeWire,
    BRepBuilderAPI_MakeFace,
)
from OCP.TopoDS import TopoDS_Wire, TopoDS_Face, TopoDS_Shape
from OCP.BRepLib import BRepLib

from mechcad.sketcher.elements import Point2D, Line2D, Circle2D, Arc2D
from mechcad.sketcher.constraints import Constraint
from mechcad.sketcher.solver import SketchSolver, SolverResult


class Sketch:
    """Parametric 2D sketch bound to a reference plane."""

    def __init__(self, sketch_id: str, name: str = "Sketch", plane: str = "XY"):
        self.sketch_id = sketch_id
        self.name = name
        self.plane = plane.upper()  # 'XY', 'XZ', 'YZ'

        self.points: Dict[str, Point2D] = {}
        self.lines: Dict[str, Line2D] = {}
        self.circles: Dict[str, Circle2D] = {}
        self.arcs: Dict[str, Arc2D] = {}
        self.constraints: List[Constraint] = []

        self._pt_counter = 0
        self._elem_counter = 0
        self.last_result: Optional[SolverResult] = None

    def map_to_3d(self, u: float, v: float, offset: float = 0.0) -> gp_Pnt:
        """Transforms 2D plane coordinates (u, v) to 3D world space (x, y, z)."""
        if self.plane == "XY":
            return gp_Pnt(u, v, offset)
        elif self.plane == "XZ":
            return gp_Pnt(u, offset, v)
        elif self.plane == "YZ":
            return gp_Pnt(offset, u, v)
        else:
            return gp_Pnt(u, v, offset)

    def get_plane_normal(self) -> Tuple[float, float, float]:
        """Returns the normal vector of the sketch plane."""
        if self.plane == "XY":
            return (0.0, 0.0, 1.0)
        elif self.plane == "XZ":
            return (0.0, 1.0, 0.0)
        elif self.plane == "YZ":
            return (1.0, 0.0, 0.0)
        return (0.0, 0.0, 1.0)

    # --- Geometry Creation Helpers ---

    def add_point(self, u: float, v: float, is_construction: bool = False, is_fixed: bool = False) -> str:
        self._pt_counter += 1
        pid = f"p{self._pt_counter}"
        self.points[pid] = Point2D(pid, u, v, is_construction=is_construction, is_fixed=is_fixed)
        return pid

    def add_line(self, p1_id: str, p2_id: str, is_construction: bool = False) -> str:
        self._elem_counter += 1
        lid = f"line{self._elem_counter}"
        self.lines[lid] = Line2D(lid, p1_id, p2_id, is_construction=is_construction)
        return lid

    def add_rect(self, u1: float, v1: float, u2: float, v2: float) -> Tuple[List[str], List[str]]:
        """Creates a 2-point rectangle with coincident corner constraints."""
        p1 = self.add_point(u1, v1)
        p2 = self.add_point(u2, v1)
        p3 = self.add_point(u2, v2)
        p4 = self.add_point(u1, v2)

        l1 = self.add_line(p1, p2)
        l2 = self.add_line(p2, p3)
        l3 = self.add_line(p3, p4)
        l4 = self.add_line(p4, p1)

        # Apply structural horizontal and vertical constraints
        self.add_constraint("horizontal", [l1])
        self.add_constraint("vertical", [l2])
        self.add_constraint("horizontal", [l3])
        self.add_constraint("vertical", [l4])

        return ([p1, p2, p3, p4], [l1, l2, l3, l4])

    def add_center_rect(self, cu: float, cv: float, width: float, height: float) -> Tuple[List[str], List[str]]:
        """Creates a center rectangle."""
        hw = width / 2.0
        hh = height / 2.0
        return self.add_rect(cu - hw, cv - hh, cu + hw, cv + hh)

    def add_circle(self, cu: float, cv: float, radius: float) -> str:
        center_id = self.add_point(cu, cv)
        self._elem_counter += 1
        cid = f"circle{self._elem_counter}"
        self.circles[cid] = Circle2D(cid, center_id, radius)
        return cid

    def add_constraint(self, kind: str, entities: List[str], value: Optional[float] = None) -> str:
        cid = f"c{len(self.constraints) + 1}"
        c = Constraint(cid, kind, entities, value)
        self.constraints.append(c)
        return cid

    def solve(self) -> SolverResult:
        """Solves sketch geometry using SolveSpace constraint solver."""
        self.last_result = SketchSolver.solve(self.points, self.lines, self.constraints)
        return self.last_result

    # --- Open CASCADE Profile Conversion ---

    def to_occ_wire(self) -> TopoDS_Wire:
        """Constructs an Open CASCADE closed TopoDS_Wire from sketch entities."""
        wire_builder = BRepBuilderAPI_MakeWire()

        # Handle circles
        if self.circles:
            for cid, circ in self.circles.items():
                if circ.is_construction:
                    continue
                cp = self.points.get(circ.center_id)
                center_pnt = self.map_to_3d(cp.u, cp.v)
                nx, ny, nz = self.get_plane_normal()
                axis = gp_Ax2(center_pnt, gp_Dir(nx, ny, nz))
                occ_circ = gp_Circ(axis, circ.radius)
                edge = BRepBuilderAPI_MakeEdge(occ_circ).Edge()
                wire_builder.Add(edge)
                break
            w = wire_builder.Wire()
            if not wire_builder.IsDone():
                raise RuntimeError("Failed to build circular wire")
            return w

        # Handle line loops
        if self.lines:
            # Build edges in loop order
            for lid, line in self.lines.items():
                if line.is_construction:
                    continue
                p1 = self.points.get(line.p1_id)
                p2 = self.points.get(line.p2_id)
                if p1 and p2:
                    pnt1 = self.map_to_3d(p1.u, p1.v)
                    pnt2 = self.map_to_3d(p2.u, p2.v)
                    edge = BRepBuilderAPI_MakeEdge(pnt1, pnt2).Edge()
                    wire_builder.Add(edge)

            if not wire_builder.IsDone():
                raise RuntimeError("Failed to assemble edges into wire")
            wire = wire_builder.Wire()
            BRepLib.BuildCurves3d_s(wire)
            return wire

        raise ValueError("Sketch contains no non-construction geometry to form a wire")

    def to_occ_face(self) -> TopoDS_Face:
        """Builds a planar TopoDS_Face from the closed sketch wire."""
        wire = self.to_occ_wire()
        face_builder = BRepBuilderAPI_MakeFace(wire, True)
        if not face_builder.IsDone():
            raise RuntimeError("Failed to construct planar face from sketch wire")
        return face_builder.Face()

    def to_dict(self) -> Dict[str, Any]:
        """Serializes sketch data for project persistence."""
        return {
            "id": self.sketch_id,
            "name": self.name,
            "plane": self.plane,
            "points": {pid: pt.to_dict() for pid, pt in self.points.items()},
            "lines": {lid: l.to_dict() for lid, l in self.lines.items()},
            "circles": {cid: c.to_dict() for cid, c in self.circles.items()},
            "constraints": [c.to_dict() for c in self.constraints],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Sketch":
        sk = cls(data["id"], data.get("name", "Sketch"), data.get("plane", "XY"))
        for pid, pdata in data.get("points", {}).items():
            sk.points[pid] = Point2D(
                pdata["id"], pdata["u"], pdata["v"],
                is_construction=pdata.get("is_construction", False),
                is_fixed=pdata.get("is_fixed", False)
            )
        for lid, ldata in data.get("lines", {}).items():
            sk.lines[lid] = Line2D(
                ldata["id"], ldata["p1"], ldata["p2"],
                is_construction=ldata.get("is_construction", False)
            )
        for cid, cdata in data.get("circles", {}).items():
            sk.circles[cid] = Circle2D(
                cdata["id"], cdata["center"], cdata["radius"],
                is_construction=cdata.get("is_construction", False)
            )
        for cdata in data.get("constraints", []):
            sk.constraints.append(Constraint.from_dict(cdata))
        return sk
