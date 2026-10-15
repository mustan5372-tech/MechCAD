"""
MechCAD Document Model & Recomputation Engine
Maintains the CAD model state, active bodies, sketches, feature tree recomputes, and undo/redo.
"""

from typing import Dict, List, Optional, Any, Tuple
import copy
import json

from OCP.TopoDS import TopoDS_Shape
from mechcad.core.units import UnitManager
from mechcad.core.history import FeatureHistory, Feature
from mechcad.core.parameters import ParameterManager
from mechcad.sketcher.sketch import Sketch
from mechcad.kernel.occ_solid import SolidOperations


class CADDocument:
    """Represents an active mechanical CAD project document."""

    def __init__(self, name: str = "Untitled 1"):
        self.name = name
        self.filepath: Optional[str] = None
        self.units = UnitManager("mm")
        self.parameters = ParameterManager()

        self.sketches: Dict[str, Sketch] = {}
        self.history = FeatureHistory()

        self.current_solid: Optional[TopoDS_Shape] = None
        self.is_dirty: bool = False

        # Undo / Redo stacks store serialized document snapshots
        self.undo_stack: List[Dict[str, Any]] = []
        self.redo_stack: List[Dict[str, Any]] = []
        self._max_undo_depth = 50

    def push_undo_state(self):
        """Saves a state snapshot for Undo."""
        state = self.to_dict()
        self.undo_stack.append(state)
        if len(self.undo_stack) > self._max_undo_depth:
            self.undo_stack.pop(0)
        self.redo_stack.clear()
        self.is_dirty = True

    def undo(self) -> bool:
        """Restores previous document state."""
        if not self.undo_stack:
            return False
        current_state = self.to_dict()
        self.redo_stack.append(current_state)
        prev_state = self.undo_stack.pop()
        self.from_dict(prev_state)
        self.recompute()
        return True

    def redo(self) -> bool:
        """Re-applies next document state."""
        if not self.redo_stack:
            return False
        current_state = self.to_dict()
        self.undo_stack.append(current_state)
        next_state = self.redo_stack.pop()
        self.from_dict(next_state)
        self.recompute()
        return True

    # --- Sketch Management ---

    def create_sketch(self, name: Optional[str] = None, plane: str = "XY") -> Sketch:
        sid = f"sketch_{len(self.sketches) + 1}"
        sk_name = name or f"Sketch {len(self.sketches) + 1}"
        sketch = Sketch(sid, name=sk_name, plane=plane)
        self.sketches[sid] = sketch
        self.is_dirty = True
        return sketch

    def get_sketch(self, sketch_id: str) -> Optional[Sketch]:
        return self.sketches.get(sketch_id)

    # --- Parametric Recomputation ---

    def recompute(self) -> Tuple[bool, Optional[str]]:
        """
        Recomputes all active features sequentially through Open CASCADE.
        Returns (success: bool, error_message: Optional[str]).
        """
        # 1. Re-solve all sketches
        for sk in self.sketches.values():
            try:
                sk.solve()
            except Exception as e:
                return (False, f"Sketch '{sk.name}' solve error: {e}")

        # 2. Sequential feature replay
        solid: Optional[TopoDS_Shape] = None
        active_features = self.history.get_active_features()

        for feat in active_features:
            feat.error_message = None
            try:
                k = feat.kind
                p = feat.params

                if k == "box":
                    dx = self.parameters.get_value(p.get("dx", 10.0))
                    dy = self.parameters.get_value(p.get("dy", 10.0))
                    dz = self.parameters.get_value(p.get("dz", 10.0))
                    x = self.parameters.get_value(p.get("x", 0.0))
                    y = self.parameters.get_value(p.get("y", 0.0))
                    z = self.parameters.get_value(p.get("z", 0.0))
                    new_shape = SolidOperations.make_box(dx, dy, dz, x, y, z)
                    solid = self._apply_solid_operation(solid, new_shape, p.get("operation", "new_body"))

                elif k == "cylinder":
                    r = self.parameters.get_value(p.get("radius", 5.0))
                    h = self.parameters.get_value(p.get("height", 10.0))
                    x = self.parameters.get_value(p.get("x", 0.0))
                    y = self.parameters.get_value(p.get("y", 0.0))
                    z = self.parameters.get_value(p.get("z", 0.0))
                    new_shape = SolidOperations.make_cylinder(r, h, x, y, z)
                    solid = self._apply_solid_operation(solid, new_shape, p.get("operation", "new_body"))

                elif k == "sphere":
                    r = self.parameters.get_value(p.get("radius", 5.0))
                    x = self.parameters.get_value(p.get("x", 0.0))
                    y = self.parameters.get_value(p.get("y", 0.0))
                    z = self.parameters.get_value(p.get("z", 0.0))
                    new_shape = SolidOperations.make_sphere(r, x, y, z)
                    solid = self._apply_solid_operation(solid, new_shape, p.get("operation", "new_body"))

                elif k == "cone":
                    r1 = self.parameters.get_value(p.get("r1", 10.0))
                    r2 = self.parameters.get_value(p.get("r2", 5.0))
                    h = self.parameters.get_value(p.get("height", 15.0))
                    new_shape = SolidOperations.make_cone(r1, r2, h)
                    solid = self._apply_solid_operation(solid, new_shape, p.get("operation", "new_body"))

                elif k == "torus":
                    r_maj = self.parameters.get_value(p.get("r_major", 15.0))
                    r_min = self.parameters.get_value(p.get("r_minor", 5.0))
                    new_shape = SolidOperations.make_torus(r_maj, r_min)
                    solid = self._apply_solid_operation(solid, new_shape, p.get("operation", "new_body"))

                elif k == "extrude":
                    sk_id = p.get("sketch_id")
                    dist = self.parameters.get_value(p.get("distance", 10.0))
                    sk = self.sketches.get(sk_id)
                    if not sk:
                        raise ValueError(f"Sketch '{sk_id}' referenced by extrude feature not found")
                    direction = p.get("direction")
                    if direction is None:
                        direction = sk.get_plane_normal()
                    is_sym = bool(p.get("symmetric", False) or (p.get("direction_type") == "Symmetric"))
                    face = sk.to_occ_face()
                    new_shape = SolidOperations.extrude_face(face, dist, direction, symmetric=is_sym)
                    solid = self._apply_solid_operation(solid, new_shape, p.get("operation", "new_body"))

                elif k == "revolve":
                    sk_id = p.get("sketch_id")
                    angle = self.parameters.get_value(p.get("angle", 360.0))
                    axis_pt = p.get("axis_pt", (0.0, 0.0, 0.0))
                    axis_dir = p.get("axis_dir", (0.0, 1.0, 0.0))
                    sk = self.sketches.get(sk_id)
                    if not sk:
                        raise ValueError(f"Sketch '{sk_id}' referenced by revolve feature not found")
                    face = sk.to_occ_face()
                    new_shape = SolidOperations.revolve_face(face, angle, axis_pt, axis_dir)
                    solid = self._apply_solid_operation(solid, new_shape, p.get("operation", "new_body"))

                elif k == "fillet":
                    if solid is None:
                        raise ValueError("No solid exists to fillet")
                    rad = self.parameters.get_value(p.get("radius", 2.0))
                    edge_indices = p.get("edge_indices")
                    solid = SolidOperations.make_fillet(solid, rad, edge_indices)

                elif k == "chamfer":
                    if solid is None:
                        raise ValueError("No solid exists to chamfer")
                    dist = self.parameters.get_value(p.get("distance", 1.0))
                    edge_indices = p.get("edge_indices")
                    solid = SolidOperations.make_chamfer(solid, dist, edge_indices)

                elif k == "shell":
                    if solid is None:
                        raise ValueError("No solid exists to shell")
                    thick = self.parameters.get_value(p.get("thickness", 2.0))
                    face_indices = p.get("face_indices")
                    solid = SolidOperations.make_shell(solid, thick, face_indices)

                elif k == "hole":
                    if solid is None:
                        raise ValueError("No solid exists to cut hole into")
                    diam = self.parameters.get_value(p.get("diameter", 5.0))
                    depth = self.parameters.get_value(p.get("depth", 10.0))
                    cx = self.parameters.get_value(p.get("center_x", 0.0))
                    cy = self.parameters.get_value(p.get("center_y", 0.0))
                    through_all = bool(p.get("through_all", True))
                    solid = SolidOperations.make_hole(solid, diam, depth, cx, cy, through_all=through_all)

                elif k == "pattern_linear":
                    if solid is None:
                        raise ValueError("No solid to pattern")
                    cx = int(self.parameters.get_value(p.get("count_x", 2)))
                    sx = self.parameters.get_value(p.get("spacing_x", 20.0))
                    cy = int(self.parameters.get_value(p.get("count_y", 1)))
                    sy = self.parameters.get_value(p.get("spacing_y", 0.0))
                    solid = SolidOperations.linear_pattern(solid, cx, sx, cy, sy)

                elif k == "pattern_circular":
                    if solid is None:
                        raise ValueError("No solid to pattern")
                    cnt = int(self.parameters.get_value(p.get("count", 3)))
                    solid = SolidOperations.circular_pattern(solid, cnt)

                elif k == "mirror":
                    if solid is None:
                        raise ValueError("No solid to mirror")
                    plane = p.get("plane", "XY")
                    mirrored = SolidOperations.make_mirror(solid, plane)
                    solid = self._apply_solid_operation(solid, mirrored, p.get("operation", "join"))

                elif k == "split_body":
                    if solid is None:
                        raise ValueError("No solid to split")
                    plane = p.get("plane", "XY")
                    offset = self.parameters.get_value(p.get("offset", 0.0))
                    solid = SolidOperations.split_body(solid, plane, offset)

            except Exception as e:
                feat.error_message = str(e)
                # Fail gracefully: don't crash, report broken feature
                return (False, f"Feature '{feat.name}' failed: {e}")

        self.current_solid = solid
        return (True, None)

    def _apply_solid_operation(self, base: Optional[TopoDS_Shape], tool: TopoDS_Shape, operation: str) -> TopoDS_Shape:
        op = str(operation).lower()
        if base is None or op in ("new_body", "new body"):
            return tool
        if op in ("join", "union", "fuse"):
            return SolidOperations.boolean_fuse(base, tool)
        elif op in ("cut", "pocket", "difference"):
            return SolidOperations.boolean_cut(base, tool)
        elif op in ("intersect", "common"):
            return SolidOperations.boolean_common(base, tool)
        return tool

    # --- Serialization ---

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "units": self.units.length_unit,
            "parameters": self.parameters.to_dict(),
            "sketches": {sid: sk.to_dict() for sid, sk in self.sketches.items()},
            "history": self.history.to_list(),
            "rollback_index": self.history.rollback_index,
        }

    def from_dict(self, data: Dict[str, Any]):
        self.name = data.get("name", "Untitled 1")
        self.units = UnitManager(data.get("units", "mm"))
        if "parameters" in data:
            self.parameters.from_dict(data["parameters"])
        self.sketches.clear()
        for sid, sdata in data.get("sketches", {}).items():
            self.sketches[sid] = Sketch.from_dict(sdata)
        self.history.from_list(data.get("history", []))
        self.history.rollback_index = data.get("rollback_index", len(self.history.features))

