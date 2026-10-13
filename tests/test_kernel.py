"""
Automated QA Tests for MechCAD Geometry Kernel
Tests Acceptance Criteria A, B, E, and F.
"""

import unittest
import os
import tempfile
import math

from mechcad.core.document import CADDocument
from mechcad.kernel.occ_solid import SolidOperations
from mechcad.kernel.occ_export import CADExchange
from mechcad.sketcher.sketch import Sketch


class TestCADKernel(unittest.TestCase):

    def test_criterion_a_sketch_extrude_20x30x10(self):
        """
        Criterion A: Create a 20 mm by 30 mm rectangular sketch and pad it to 10 mm;
        expected bounding dimensions are 20 x 30 x 10 mm.
        """
        doc = CADDocument("TestDoc_A")
        sk = doc.create_sketch("RectSketch", plane="XY")
        sk.add_rect(0.0, 0.0, 20.0, 30.0)
        res = sk.solve()
        self.assertTrue(res.success, f"Sketch solve failed: {res.message}")

        doc.history.add_feature("extrude", {
            "sketch_id": sk.sketch_id,
            "distance": 10.0,
            "direction": (0.0, 0.0, 1.0),
            "operation": "new_body"
        })

        success, err = doc.recompute()
        self.assertTrue(success, f"Recompute failed: {err}")
        self.assertIsNotNone(doc.current_solid)

        dx, dy, dz = SolidOperations.get_bounding_dimensions(doc.current_solid)
        self.assertAlmostEqual(dx, 20.0, places=3, msg=f"Expected dx=20, got {dx}")
        self.assertAlmostEqual(dy, 30.0, places=3, msg=f"Expected dy=30, got {dy}")
        self.assertAlmostEqual(dz, 10.0, places=3, msg=f"Expected dz=10, got {dz}")

    def test_criterion_b_cylinder_with_cut_through_hole(self):
        """
        Criterion B: Create a cylindrical solid and cut a through-hole.
        """
        doc = CADDocument("TestDoc_B")
        # Cylinder dia 20mm (r=10), height 30mm
        doc.history.add_feature("cylinder", {
            "radius": 10.0,
            "height": 30.0,
            "x": 0.0, "y": 0.0, "z": 0.0,
            "operation": "new_body"
        })

        # Cut through-hole dia 8mm (r=4)
        doc.history.add_feature("hole", {
            "diameter": 8.0,
            "depth": 30.0,
            "center_x": 0.0, "center_y": 0.0,
            "through_all": True
        })

        success, err = doc.recompute()
        self.assertTrue(success, f"Recompute failed: {err}")
        self.assertIsNotNone(doc.current_solid)

        # Verify solid dimensions remain dia 20, height 30
        dx, dy, dz = SolidOperations.get_bounding_dimensions(doc.current_solid)
        self.assertAlmostEqual(dx, 20.0, places=2)
        self.assertAlmostEqual(dy, 20.0, places=2)
        self.assertAlmostEqual(dz, 30.0, places=2)

        # Verify topology has inner cylindrical face (at least 3 faces: outer, inner, top, bottom annular)
        topo = SolidOperations.count_topology(doc.current_solid)
        self.assertGreaterEqual(topo["faces"], 4, "Through-hole cylinder should have at least 4 topological faces")

    def test_criterion_e_step_export_and_reimport(self):
        """
        Criterion E: Export a solid to STEP and reimport it; compare valid geometry and dimensions.
        """
        doc = CADDocument("TestDoc_E")
        doc.history.add_feature("box", {"dx": 25.0, "dy": 45.0, "dz": 15.0})
        doc.recompute()
        orig_solid = doc.current_solid
        orig_dx, orig_dy, orig_dz = SolidOperations.get_bounding_dimensions(orig_solid)

        with tempfile.TemporaryDirectory() as tmp_dir:
            step_file = os.path.join(tmp_dir, "roundtrip.step")
            # Export
            export_ok = CADExchange.export_step(orig_solid, step_file)
            self.assertTrue(export_ok)
            self.assertTrue(os.path.exists(step_file))
            self.assertGreater(os.path.getsize(step_file), 0)

            # Reimport
            imported_shape = CADExchange.import_step(step_file)
            self.assertIsNotNone(imported_shape)
            self.assertFalse(imported_shape.IsNull())

            imp_dx, imp_dy, imp_dz = SolidOperations.get_bounding_dimensions(imported_shape)
            self.assertAlmostEqual(imp_dx, orig_dx, places=3)
            self.assertAlmostEqual(imp_dy, orig_dy, places=3)
            self.assertAlmostEqual(imp_dz, orig_dz, places=3)

    def test_criterion_f_stl_export_nonempty(self):
        """
        Criterion F: Export a solid to STL and verify the resulting mesh is nonempty.
        """
        doc = CADDocument("TestDoc_F")
        doc.history.add_feature("cylinder", {"radius": 15.0, "height": 25.0})
        doc.recompute()

        with tempfile.TemporaryDirectory() as tmp_dir:
            stl_file = os.path.join(tmp_dir, "mesh.stl")
            stl_ok = CADExchange.export_stl(doc.current_solid, stl_file, linear_deflection=0.1)
            self.assertTrue(stl_ok)
            self.assertTrue(os.path.exists(stl_file))
            file_size = os.path.getsize(stl_file)
            self.assertGreater(file_size, 1000, f"Expected non-trivial STL mesh file size, got {file_size} bytes")


if __name__ == "__main__":
    unittest.main()
