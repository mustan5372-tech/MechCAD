"""
MechCAD Open CASCADE Solid Modeling Operations
Wraps Open CASCADE Technology (OCCT 7.8) B-Rep solid kernel functions.
"""

import math
from typing import List, Optional, Tuple, Dict, Any

from OCP.gp import gp_Pnt, gp_Vec, gp_Ax1, gp_Ax2, gp_Dir, gp_Trsf
from OCP.BRepPrimAPI import (
    BRepPrimAPI_MakeBox,
    BRepPrimAPI_MakeCylinder,
    BRepPrimAPI_MakeSphere,
    BRepPrimAPI_MakeCone,
    BRepPrimAPI_MakeTorus,
    BRepPrimAPI_MakePrism,
    BRepPrimAPI_MakeRevol,
)
from OCP.BRepAlgoAPI import (
    BRepAlgoAPI_Fuse,
    BRepAlgoAPI_Cut,
    BRepAlgoAPI_Common,
)
from OCP.BRepFilletAPI import (
    BRepFilletAPI_MakeFillet,
    BRepFilletAPI_MakeChamfer,
)
from OCP.BRepBuilderAPI import (
    BRepBuilderAPI_Transform,
    BRepBuilderAPI_Copy,
)
from OCP.BRepBndLib import BRepBndLib
from OCP.Bnd import Bnd_Box
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import (
    TopAbs_FACE,
    TopAbs_EDGE,
    TopAbs_VERTEX,
    TopAbs_SOLID,
    TopAbs_SHELL,
)
from OCP.TopoDS import TopoDS, TopoDS_Shape, TopoDS_Solid, TopoDS_Face, TopoDS_Edge


class SolidOperations:
    """Provides precise B-Rep CAD solid modeling operations."""

    @staticmethod
    def get_bounding_box(shape: TopoDS_Shape) -> Tuple[float, float, float, float, float, float]:
        """Returns (xmin, ymin, zmin, xmax, ymax, zmax) of the shape."""
        if shape is None or shape.IsNull():
            return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        bbox = Bnd_Box()
        BRepBndLib.Add_s(shape, bbox)
        if bbox.IsVoid():
            return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        pmin = bbox.CornerMin()
        pmax = bbox.CornerMax()
        return (pmin.X(), pmin.Y(), pmin.Z(), pmax.X(), pmax.Y(), pmax.Z())

    @staticmethod
    def get_bounding_dimensions(shape: TopoDS_Shape) -> Tuple[float, float, float]:
        """Returns (dx, dy, dz) extent of the shape."""
        xmin, ymin, zmin, xmax, ymax, zmax = SolidOperations.get_bounding_box(shape)
        return (abs(xmax - xmin), abs(ymax - ymin), abs(zmax - zmin))

    @staticmethod
    def count_topology(shape: TopoDS_Shape) -> Dict[str, int]:
        """Counts solids, faces, edges, and vertices in shape."""
        if shape is None or shape.IsNull():
            return {"solids": 0, "faces": 0, "edges": 0, "vertices": 0}

        counts = {"solids": 0, "faces": 0, "edges": 0, "vertices": 0}
        exp_solid = TopExp_Explorer(shape, TopAbs_SOLID)
        while exp_solid.More():
            counts["solids"] += 1
            exp_solid.Next()

        exp_face = TopExp_Explorer(shape, TopAbs_FACE)
        while exp_face.More():
            counts["faces"] += 1
            exp_face.Next()

        exp_edge = TopExp_Explorer(shape, TopAbs_EDGE)
        while exp_edge.More():
            counts["edges"] += 1
            exp_edge.Next()

        exp_vertex = TopExp_Explorer(shape, TopAbs_VERTEX)
        while exp_vertex.More():
            counts["vertices"] += 1
            exp_vertex.Next()

        return counts

    # --- 3D Primitives ---

    @staticmethod
    def make_box(dx: float, dy: float, dz: float, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> TopoDS_Shape:
        """Creates a box with dimensions dx, dy, dz at origin (x, y, z)."""
        if dx <= 0 or dy <= 0 or dz <= 0:
            raise ValueError(f"Box dimensions must be positive, got ({dx}, {dy}, {dz})")
        p0 = gp_Pnt(float(x), float(y), float(z))
        maker = BRepPrimAPI_MakeBox(p0, float(dx), float(dy), float(dz))
        maker.Build()
        if not maker.IsDone():
            raise RuntimeError("Failed to build box")
        return maker.Shape()

    @staticmethod
    def make_cylinder(radius: float, height: float, x: float = 0.0, y: float = 0.0, z: float = 0.0,
                      dx: float = 0.0, dy: float = 0.0, dz: float = 1.0) -> TopoDS_Shape:
        """Creates a cylinder with given radius and height along axis (dx, dy, dz)."""
        if radius <= 0 or height <= 0:
            raise ValueError("Cylinder radius and height must be positive")
        axis = gp_Ax2(gp_Pnt(x, y, z), gp_Dir(dx, dy, dz))
        maker = BRepPrimAPI_MakeCylinder(axis, float(radius), float(height))
        maker.Build()
        if not maker.IsDone():
            raise RuntimeError("Failed to build cylinder")
        return maker.Shape()

    @staticmethod
    def make_sphere(radius: float, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> TopoDS_Shape:
        """Creates a sphere with given radius centered at (x, y, z)."""
        if radius <= 0:
            raise ValueError("Sphere radius must be positive")
        p0 = gp_Pnt(x, y, z)
        maker = BRepPrimAPI_MakeSphere(p0, float(radius))
        maker.Build()
        if not maker.IsDone():
            raise RuntimeError("Failed to build sphere")
        return maker.Shape()

    @staticmethod
    def make_cone(r1: float, r2: float, height: float, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> TopoDS_Shape:
        """Creates a conical solid."""
        if r1 < 0 or r2 < 0 or height <= 0 or (r1 == 0 and r2 == 0):
            raise ValueError("Cone dimensions are invalid")
        axis = gp_Ax2(gp_Pnt(x, y, z), gp_Dir(0.0, 0.0, 1.0))
        maker = BRepPrimAPI_MakeCone(axis, float(r1), float(r2), float(height))
        maker.Build()
        if not maker.IsDone():
            raise RuntimeError("Failed to build cone")
        return maker.Shape()

    @staticmethod
    def make_torus(r_major: float, r_minor: float, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> TopoDS_Shape:
        """Creates a torus."""
        if r_major <= 0 or r_minor <= 0 or r_minor >= r_major:
            raise ValueError("Torus dimensions invalid (r_major > r_minor > 0 required)")
        axis = gp_Ax2(gp_Pnt(x, y, z), gp_Dir(0.0, 0.0, 1.0))
        maker = BRepPrimAPI_MakeTorus(axis, float(r_major), float(r_minor))
        maker.Build()
        if not maker.IsDone():
            raise RuntimeError("Failed to build torus")
        return maker.Shape()

    # --- 3D Feature Operations ---

    @staticmethod
    def extrude_face(face: TopoDS_Face, distance: float, direction: Tuple[float, float, float] = (0.0, 0.0, 1.0)) -> TopoDS_Shape:
        """Extrudes a planar face along direction vector by given distance."""
        if distance == 0:
            raise ValueError("Extrude distance cannot be zero")
        vx, vy, vz = direction
        mag = math.sqrt(vx*vx + vy*vy + vz*vz)
        if mag == 0:
            vx, vy, vz = 0.0, 0.0, 1.0
            mag = 1.0
        vec = gp_Vec((vx / mag) * distance, (vy / mag) * distance, (vz / mag) * distance)
        maker = BRepPrimAPI_MakePrism(face, vec)
        maker.Build()
        if not maker.IsDone():
            raise RuntimeError("Extrude prism operation failed")
        return maker.Shape()

    @staticmethod
    def revolve_face(face: TopoDS_Face, angle_deg: float = 360.0,
                     axis_point: Tuple[float, float, float] = (0.0, 0.0, 0.0),
                     axis_dir: Tuple[float, float, float] = (0.0, 1.0, 0.0)) -> TopoDS_Shape:
        """Revolves a planar face around an axis by angle_deg degrees."""
        if angle_deg == 0:
            raise ValueError("Revolve angle cannot be zero")
        rad = math.radians(angle_deg)
        pt = gp_Pnt(*axis_point)
        d = gp_Dir(*axis_dir)
        axis = gp_Ax1(pt, d)
        maker = BRepPrimAPI_MakeRevol(face, axis, rad)
        maker.Build()
        if not maker.IsDone():
            raise RuntimeError("Revolve operation failed")
        return maker.Shape()

    # --- Boolean Operations ---

    @staticmethod
    def boolean_cut(base_shape: TopoDS_Shape, tool_shape: TopoDS_Shape) -> TopoDS_Shape:
        """Subtracts tool_shape from base_shape."""
        maker = BRepAlgoAPI_Cut(base_shape, tool_shape)
        maker.Build()
        if not maker.IsDone():
            raise RuntimeError("Boolean Cut operation failed")
        return maker.Shape()

    @staticmethod
    def boolean_fuse(base_shape: TopoDS_Shape, tool_shape: TopoDS_Shape) -> TopoDS_Shape:
        """Unites base_shape and tool_shape."""
        maker = BRepAlgoAPI_Fuse(base_shape, tool_shape)
        maker.Build()
        if not maker.IsDone():
            raise RuntimeError("Boolean Fuse/Union operation failed")
        return maker.Shape()

    @staticmethod
    def boolean_common(shape_a: TopoDS_Shape, shape_b: TopoDS_Shape) -> TopoDS_Shape:
        """Intersects shape_a and shape_b."""
        maker = BRepAlgoAPI_Common(shape_a, shape_b)
        maker.Build()
        if not maker.IsDone():
            raise RuntimeError("Boolean Common/Intersect operation failed")
        return maker.Shape()

    # --- Modifiers: Fillet & Chamfer ---

    @staticmethod
    def make_fillet(shape: TopoDS_Shape, radius: float, edge_indices: Optional[List[int]] = None) -> TopoDS_Shape:
        """Applies fillet of given radius to specified edge indices (or all edges if None)."""
        if radius <= 0:
            raise ValueError("Fillet radius must be positive")
        fillet = BRepFilletAPI_MakeFillet(shape)
        exp = TopExp_Explorer(shape, TopAbs_EDGE)
        idx = 0
        added = 0
        while exp.More():
            edge = TopoDS.Edge(exp.Current())
            if edge_indices is None or idx in edge_indices:
                fillet.Add(float(radius), edge)
                added += 1
            idx += 1
            exp.Next()

        if added == 0:
            return shape
        fillet.Build()
        if not fillet.IsDone():
            raise RuntimeError(f"Fillet failed with radius {radius} mm")
        return fillet.Shape()

    @staticmethod
    def make_chamfer(shape: TopoDS_Shape, distance: float, edge_indices: Optional[List[int]] = None) -> TopoDS_Shape:
        """Applies chamfer of given distance to specified edge indices."""
        if distance <= 0:
            raise ValueError("Chamfer distance must be positive")
        chamfer = BRepFilletAPI_MakeChamfer(shape)
        exp = TopExp_Explorer(shape, TopAbs_EDGE)
        idx = 0
        added = 0
        while exp.More():
            edge = TopoDS.Edge(exp.Current())
            if edge_indices is None or idx in edge_indices:
                chamfer.Add(float(distance), edge)
                added += 1
            idx += 1
            exp.Next()

        if added == 0:
            return shape
        chamfer.Build()
        if not chamfer.IsDone():
            raise RuntimeError(f"Chamfer failed with distance {distance} mm")
        return chamfer.Shape()

    # --- Hole Feature ---

    @staticmethod
    def make_hole(shape: TopoDS_Shape, diameter: float, depth: float,
                  center_x: float = 0.0, center_y: float = 0.0,
                  axis_dir: Tuple[float, float, float] = (0.0, 0.0, -1.0),
                  through_all: bool = False) -> TopoDS_Shape:
        """Cuts a cylindrical hole into the solid shape."""
        radius = diameter / 2.0
        xmin, ymin, zmin, xmax, ymax, zmax = SolidOperations.get_bounding_box(shape)
        max_extent = max(xmax - xmin, ymax - ymin, zmax - zmin) * 2.0 + 10.0
        effective_depth = max_extent if through_all else depth

        # Start slightly offset above/behind the surface to ensure clean topological cut
        start_z = zmax + 1.0 if axis_dir[2] < 0 else zmin - 1.0
        cyl = SolidOperations.make_cylinder(
            radius=radius,
            height=effective_depth + 2.0,
            x=center_x, y=center_y, z=start_z,
            dx=axis_dir[0], dy=axis_dir[1], dz=axis_dir[2]
        )
        return SolidOperations.boolean_cut(shape, cyl)

    # --- Patterns & Transform ---

    @staticmethod
    def linear_pattern(shape: TopoDS_Shape, count_x: int, spacing_x: float,
                       count_y: int = 1, spacing_y: float = 0.0) -> TopoDS_Shape:
        """Generates a linear rectangular pattern of the shape."""
        fused = shape
        for ix in range(count_x):
            for iy in range(count_y):
                if ix == 0 and iy == 0:
                    continue
                trsf = gp_Trsf()
                trsf.SetTranslation(gp_Vec(ix * spacing_x, iy * spacing_y, 0.0))
                copy_shape = BRepBuilderAPI_Transform(shape, trsf, True).Shape()
                fused = SolidOperations.boolean_fuse(fused, copy_shape)
        return fused

    @staticmethod
    def circular_pattern(shape: TopoDS_Shape, count: int,
                         center: Tuple[float, float, float] = (0.0, 0.0, 0.0),
                         axis_dir: Tuple[float, float, float] = (0.0, 0.0, 1.0)) -> TopoDS_Shape:
        """Generates a circular polar pattern of the shape."""
        if count < 2:
            return shape
        angle_step = 2.0 * math.pi / count
        axis = gp_Ax1(gp_Pnt(*center), gp_Dir(*axis_dir))
        fused = shape
        for i in range(1, count):
            trsf = gp_Trsf()
            trsf.SetRotation(axis, i * angle_step)
            copy_shape = BRepBuilderAPI_Transform(shape, trsf, True).Shape()
            fused = SolidOperations.boolean_fuse(fused, copy_shape)
        return fused
