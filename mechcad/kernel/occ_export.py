"""
MechCAD STEP, STL, and 2D DXF Exchange Services
Supports STEP AP214/AP203 lossless solid exchange and STL mesh export for 3D printing.
"""

import os
from typing import Optional
from OCP.TopoDS import TopoDS_Shape
from OCP.STEPControl import (
    STEPControl_Writer,
    STEPControl_Reader,
    STEPControl_AsIs,
)
from OCP.IFSelect import IFSelect_ReturnStatus
from OCP.StlAPI import StlAPI_Writer, StlAPI_Reader
from OCP.BRepMesh import BRepMesh_IncrementalMesh
import ezdxf


class CADExchange:
    """Handles standard CAD file imports and exports."""

    @staticmethod
    def export_step(shape: TopoDS_Shape, filepath: str) -> bool:
        """Exports an Open CASCADE solid shape to STEP format (ISO 10303)."""
        if shape is None or shape.IsNull():
            raise ValueError("Cannot export empty or null shape to STEP")
        writer = STEPControl_Writer()
        status = writer.Transfer(shape, STEPControl_AsIs)
        if status != IFSelect_ReturnStatus.IFSelect_RetDone:
            raise RuntimeError(f"STEP transfer failed with status: {status}")
        write_status = writer.Write(filepath)
        if write_status != IFSelect_ReturnStatus.IFSelect_RetDone or not os.path.exists(filepath):
            raise RuntimeError(f"Failed to write STEP file: {filepath}")
        if os.path.getsize(filepath) == 0:
            raise RuntimeError("Exported STEP file is 0 bytes")
        return True

    @staticmethod
    def import_step(filepath: str) -> TopoDS_Shape:
        """Reads a STEP file and returns the TopoDS_Shape."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"STEP file not found: {filepath}")
        reader = STEPControl_Reader()
        status = reader.ReadFile(filepath)
        if status != IFSelect_ReturnStatus.IFSelect_RetDone:
            raise RuntimeError(f"Failed to read STEP file, status: {status}")
        reader.TransferRoots()
        shape = reader.OneShape()
        if shape.IsNull():
            raise RuntimeError("Imported STEP shape is null")
        return shape

    @staticmethod
    def export_stl(shape: TopoDS_Shape, filepath: str,
                   linear_deflection: float = 0.05,
                   angular_deflection: float = 0.5) -> bool:
        """
        Tessellates the B-Rep solid shape and exports it to STL format for 3D printing.
        Preserves metric dimensions in millimetres.
        """
        if shape is None or shape.IsNull():
            raise ValueError("Cannot export empty shape to STL")
        # Generate triangular mesh with specified precision
        BRepMesh_IncrementalMesh(shape, float(linear_deflection), False, float(angular_deflection), True)
        writer = StlAPI_Writer()
        success = writer.Write(shape, filepath)
        if not success or not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            raise RuntimeError(f"Failed to write STL mesh file: {filepath}")
        return True

    @staticmethod
    def export_dxf(sketch_elements: list, filepath: str) -> bool:
        """Exports 2D sketch geometry to DXF format via ezdxf."""
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()
        for elem in sketch_elements:
            kind = elem.get("type")
            if kind == "line":
                p1 = elem["p1"]
                p2 = elem["p2"]
                msp.add_line((p1[0], p1[1]), (p2[0], p2[1]))
            elif kind == "circle":
                c = elem["center"]
                r = elem["radius"]
                msp.add_circle((c[0], c[1]), r)
            elif kind == "arc":
                c = elem["center"]
                r = elem["radius"]
                a1 = elem.get("start_angle", 0.0)
                a2 = elem.get("end_angle", 360.0)
                msp.add_arc((c[0], c[1]), r, a1, a2)
        doc.saveas(filepath)
        return os.path.exists(filepath) and os.path.getsize(filepath) > 0
