"""
MechCAD Real 2D Geometric Constraint Solver Bridge
Interfaces SolveSpace (slvs) C-library for exact numerical CAD constraint solving.
"""

from typing import Dict, List, Tuple, Any, Optional
import slvs

from mechcad.sketcher.elements import Point2D, Line2D, Circle2D, Arc2D
from mechcad.sketcher.constraints import Constraint


class SolverResult:
    def __init__(self, success: bool, dof: int, message: str, points: Dict[str, Tuple[float, float]]):
        self.success = success
        self.dof = dof
        self.message = message
        self.points = points  # {point_id: (u, v)}


class SketchSolver:
    """Manages SolveSpace 2D constraint systems."""

    @staticmethod
    def solve(points: Dict[str, Point2D],
              lines: Dict[str, Line2D],
              constraints: List[Constraint]) -> SolverResult:
        """
        Solves the 2D geometric constraint system and updates point coordinates.
        Returns a SolverResult detailing DOF and status.
        """
        slvs.clear_sketch()
        group_base = 1
        group_sketch = 2

        wp = slvs.add_base_2d(group_base)

        # 1. Register Points
        slvs_pts = {}
        for pid, pt in points.items():
            s_pt = slvs.add_point_2d(group_sketch, pt.u, pt.v, wp)
            slvs_pts[pid] = s_pt
            if pt.is_fixed:
                # Fix point by adding fixed reference point and coincident constraint
                ref_pt = slvs.add_point_2d(group_base, pt.u, pt.v, wp)
                slvs.coincident(group_sketch, s_pt, ref_pt, wp)

        # 2. Register Lines
        slvs_lines = {}
        for lid, line in lines.items():
            p1 = slvs_pts.get(line.p1_id)
            p2 = slvs_pts.get(line.p2_id)
            if p1 and p2:
                slvs_lines[lid] = slvs.add_line_2d(group_sketch, p1, p2, wp)

        # 3. Apply Constraints
        for c in constraints:
            kind = c.kind.lower()
            try:
                if kind == "coincident":
                    if len(c.entities) >= 2:
                        pA = slvs_pts.get(c.entities[0])
                        pB = slvs_pts.get(c.entities[1])
                        if pA and pB:
                            slvs.coincident(group_sketch, pA, pB, wp)

                elif kind == "horizontal":
                    if len(c.entities) >= 1:
                        target = slvs_lines.get(c.entities[0])
                        if target:
                            slvs.horizontal(group_sketch, target, wp)
                        elif len(c.entities) >= 2:
                            # Two points horizontal
                            pA = slvs_pts.get(c.entities[0])
                            pB = slvs_pts.get(c.entities[1])
                            if pA and pB:
                                temp_line = slvs.add_line_2d(group_sketch, pA, pB, wp)
                                slvs.horizontal(group_sketch, temp_line, wp)

                elif kind == "vertical":
                    if len(c.entities) >= 1:
                        target = slvs_lines.get(c.entities[0])
                        if target:
                            slvs.vertical(group_sketch, target, wp)
                        elif len(c.entities) >= 2:
                            # Two points vertical
                            pA = slvs_pts.get(c.entities[0])
                            pB = slvs_pts.get(c.entities[1])
                            if pA and pB:
                                temp_line = slvs.add_line_2d(group_sketch, pA, pB, wp)
                                slvs.vertical(group_sketch, temp_line, wp)

                elif kind == "distance":
                    if c.value is not None:
                        val = float(c.value)
                        if len(c.entities) == 1 and c.entities[0] in slvs_lines:
                            # Distance of line = length
                            l_obj = lines[c.entities[0]]
                            pA = slvs_pts.get(l_obj.p1_id)
                            pB = slvs_pts.get(l_obj.p2_id)
                            if pA and pB:
                                slvs.distance(group_sketch, pA, pB, val, wp)
                        elif len(c.entities) >= 2:
                            pA = slvs_pts.get(c.entities[0])
                            pB = slvs_pts.get(c.entities[1])
                            if pA and pB:
                                slvs.distance(group_sketch, pA, pB, val, wp)

                elif kind == "parallel":
                    if len(c.entities) >= 2:
                        lA = slvs_lines.get(c.entities[0])
                        lB = slvs_lines.get(c.entities[1])
                        if lA and lB:
                            slvs.parallel(group_sketch, lA, lB, wp)

                elif kind == "perpendicular":
                    if len(c.entities) >= 2:
                        lA = slvs_lines.get(c.entities[0])
                        lB = slvs_lines.get(c.entities[1])
                        if lA and lB:
                            slvs.perpendicular(group_sketch, lA, lB, wp)

                elif kind == "equal":
                    if len(c.entities) >= 2:
                        lA = slvs_lines.get(c.entities[0])
                        lB = slvs_lines.get(c.entities[1])
                        if lA and lB:
                            slvs.equal(group_sketch, lA, lB, wp)

                elif kind == "angle":
                    if len(c.entities) >= 2 and c.value is not None:
                        lA = slvs_lines.get(c.entities[0])
                        lB = slvs_lines.get(c.entities[1])
                        if lA and lB:
                            slvs.angle(group_sketch, lA, lB, float(c.value), wp)

                elif kind == "midpoint":
                    if len(c.entities) >= 3:
                        mid_p = slvs_pts.get(c.entities[0])
                        pA = slvs_pts.get(c.entities[1])
                        pB = slvs_pts.get(c.entities[2])
                        if mid_p and pA and pB:
                            slvs.midpoint(group_sketch, mid_p, pA, pB, wp)

                elif kind == "fix":
                    if len(c.entities) >= 1:
                        pA = slvs_pts.get(c.entities[0])
                        pt_obj = points.get(c.entities[0])
                        if pA and pt_obj:
                            ref = slvs.add_point_2d(group_base, pt_obj.u, pt_obj.v, wp)
                            slvs.coincident(group_sketch, pA, ref, wp)
            except Exception as e:
                # Log constraint addition error
                pass

        # 4. Solve system
        sys_res, bad_constraints = slvs.solve_sketch(group_sketch, True)
        res_code = sys_res.get("result", -1)
        dof = sys_res.get("dof", 0)

        # 5. Extract solved positions
        solved_points = {}
        for pid, s_pt in slvs_pts.items():
            try:
                u = slvs.get_param_value(s_pt["param"][0])
                v = slvs.get_param_value(s_pt["param"][1])
                solved_points[pid] = (float(u), float(v))
                # Update Point2D entity in place
                if pid in points:
                    points[pid].u = float(u)
                    points[pid].v = float(v)
            except Exception:
                solved_points[pid] = (points[pid].u, points[pid].v)

        # 6. Format status message
        if res_code == 0:
            if dof == 0:
                msg = "Fully Constrained"
            else:
                msg = f"{dof} Degree{'s' if dof != 1 else ''} of Freedom"
            success = True
        elif res_code == 1:
            msg = "Overconstrained / Conflicting Constraints"
            success = False
        else:
            msg = f"Solver Warning (code {res_code})"
            success = False

        return SolverResult(success=success, dof=dof, message=msg, points=solved_points)
