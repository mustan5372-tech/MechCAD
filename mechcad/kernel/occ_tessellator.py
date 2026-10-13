"""
MechCAD Open CASCADE Tessellation Service
Extracts triangular meshes and boundary line segments for hardware-accelerated OpenGL rendering.
"""

import math
from typing import Dict, List, Tuple, Any
import numpy as np

from OCP.TopoDS import TopoDS, TopoDS_Shape, TopoDS_Face, TopoDS_Edge
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE, TopAbs_EDGE
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRep import BRep_Tool
from OCP.TopLoc import TopLoc_Location
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GCPnts import GCPnts_UniformDeflection
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib


class ShapeTessellation:
    """Encapsulates OpenGL-ready geometry arrays for a CAD shape."""
    def __init__(self):
        # Triangles for shaded faces
        self.vertices: np.ndarray = np.empty((0, 3), dtype=np.float32)
        self.normals: np.ndarray = np.empty((0, 3), dtype=np.float32)
        # Face sub-meshes for ray picking and face selection
        self.face_meshes: List[Dict[str, Any]] = []
        # Wireframe edges for CAD "Shaded with Visible Edges" display
        self.edge_lines: np.ndarray = np.empty((0, 3), dtype=np.float32)
        # Bounding box
        self.bbox: Tuple[float, float, float, float, float, float] = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        self.center: Tuple[float, float, float] = (0.0, 0.0, 0.0)
        self.diagonal: float = 100.0


class OCCTessellator:
    """Tessellates TopoDS_Shape into OpenGL triangle buffers and boundary wireframes."""

    @staticmethod
    def tessellate(shape: TopoDS_Shape, linear_deflection: float = 0.1, angular_deflection: float = 0.5) -> ShapeTessellation:
        res = ShapeTessellation()
        if shape is None or shape.IsNull():
            return res

        # 1. Compute Bounding Box
        bbox = Bnd_Box()
        BRepBndLib.Add_s(shape, bbox)
        if not bbox.IsVoid():
            pmin = bbox.CornerMin()
            pmax = bbox.CornerMax()
            res.bbox = (pmin.X(), pmin.Y(), pmin.Z(), pmax.X(), pmax.Y(), pmax.Z())
            cx = (pmin.X() + pmax.X()) * 0.5
            cy = (pmin.Y() + pmax.Y()) * 0.5
            cz = (pmin.Z() + pmax.Z()) * 0.5
            res.center = (cx, cy, cz)
            dx = pmax.X() - pmin.X()
            dy = pmax.Y() - pmin.Y()
            dz = pmax.Z() - pmin.Z()
            res.diagonal = max(math.sqrt(dx*dx + dy*dy + dz*dz), 1.0)
            # Adapt deflection based on model size
            linear_deflection = max(res.diagonal * 0.003, 0.02)

        # 2. Tessellate B-Rep shape with incremental mesh
        BRepMesh_IncrementalMesh(shape, float(linear_deflection), False, float(angular_deflection), True)

        # 3. Extract Triangular Faces
        all_verts = []
        all_normals = []
        exp_face = TopExp_Explorer(shape, TopAbs_FACE)
        face_idx = 0

        while exp_face.More():
            face = TopoDS.Face(exp_face.Current())
            loc = TopLoc_Location()
            triangulation = BRep_Tool.Triangulation_s(face, loc)

            if triangulation is not None:
                trsf = loc.Transformation()
                nb_tri = triangulation.NbTriangles()
                face_verts = []
                face_norms = []

                for i in range(1, nb_tri + 1):
                    tri = triangulation.Triangle(i)
                    i1, i2, i3 = tri.Get()
                    p1 = triangulation.Node(i1).Transformed(trsf)
                    p2 = triangulation.Node(i2).Transformed(trsf)
                    p3 = triangulation.Node(i3).Transformed(trsf)

                    v1 = [p1.X(), p1.Y(), p1.Z()]
                    v2 = [p2.X(), p2.Y(), p2.Z()]
                    v3 = [p3.X(), p3.Y(), p3.Z()]

                    # Compute flat face normal for crisp mechanical shading
                    u = [v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2]]
                    v = [v3[0] - v1[0], v3[1] - v1[1], v3[2] - v1[2]]
                    nx = u[1] * v[2] - u[2] * v[1]
                    ny = u[2] * v[0] - u[0] * v[2]
                    nz = u[0] * v[1] - u[1] * v[0]
                    norm_len = math.sqrt(nx*nx + ny*ny + nz*nz)
                    if norm_len > 1e-9:
                        n = [nx / norm_len, ny / norm_len, nz / norm_len]
                    else:
                        n = [0.0, 0.0, 1.0]

                    face_verts.extend([v1, v2, v3])
                    face_norms.extend([n, n, n])

                if face_verts:
                    f_verts_arr = np.array(face_verts, dtype=np.float32)
                    f_norms_arr = np.array(face_norms, dtype=np.float32)
                    res.face_meshes.append({
                        "face_index": face_idx,
                        "vertices": f_verts_arr,
                        "normals": f_norms_arr,
                        "centroid": np.mean(f_verts_arr, axis=0).tolist(),
                    })
                    all_verts.extend(face_verts)
                    all_normals.extend(face_norms)

            face_idx += 1
            exp_face.Next()

        if all_verts:
            res.vertices = np.array(all_verts, dtype=np.float32)
            res.normals = np.array(all_normals, dtype=np.float32)

        # 4. Extract Boundary Edges
        edge_pts = []
        exp_edge = TopExp_Explorer(shape, TopAbs_EDGE)
        while exp_edge.More():
            edge = TopoDS.Edge(exp_edge.Current())
            try:
                adaptor = BRepAdaptor_Curve(edge)
                defl = GCPnts_UniformDeflection(adaptor, float(linear_deflection))
                nb_pts = defl.NbPoints()
                if nb_pts >= 2:
                    pts = []
                    for i in range(1, nb_pts + 1):
                        p = defl.Value(i)
                        pts.append([p.X(), p.Y(), p.Z()])
                    for i in range(len(pts) - 1):
                        edge_pts.append(pts[i])
                        edge_pts.append(pts[i + 1])
            except Exception:
                pass
            exp_edge.Next()

        if edge_pts:
            res.edge_lines = np.array(edge_pts, dtype=np.float32)

        return res
