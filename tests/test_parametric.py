"""
Automated QA Tests for Parametric Recomputation & History
Tests Acceptance Criteria C and G.
"""

import unittest
from mechcad.core.document import CADDocument
from mechcad.kernel.occ_solid import SolidOperations


class TestParametricEngine(unittest.TestCase):

    def test_criterion_c_upstream_dimension_change_recomputes_downstream(self):
        """
        Criterion C: Modify an upstream dimension and verify downstream features recompute.
        """
        doc = CADDocument("TestDoc_C")
        sk = doc.create_sketch("Profile", plane="XY")
        pts, lines = sk.add_rect(0.0, 0.0, 20.0, 30.0)

        # Add dimensional constraint of 20 mm on width line
        cid = sk.add_constraint("distance", [lines[0]], 20.0)
        sk.solve()

        # Add downstream Extrude feature of 10 mm
        doc.history.add_feature("extrude", {
            "sketch_id": sk.sketch_id,
            "distance": 10.0,
            "operation": "new_body"
        })
        success, _ = doc.recompute()
        self.assertTrue(success)

        dx, dy, dz = SolidOperations.get_bounding_dimensions(doc.current_solid)
        self.assertAlmostEqual(dx, 20.0, places=2)
        self.assertAlmostEqual(dy, 30.0, places=2)
        self.assertAlmostEqual(dz, 10.0, places=2)

        # Upstream Edit: Change dimensional constraint from 20 mm to 55 mm
        for c in sk.constraints:
            if c.constraint_id == cid:
                c.value = 55.0
                break

        # Recompute downstream solid
        recomp_ok, err = doc.recompute()
        self.assertTrue(recomp_ok, f"Downstream recompute failed: {err}")

        # Verify solid dimensions automatically updated
        dx2, dy2, dz2 = SolidOperations.get_bounding_dimensions(doc.current_solid)
        self.assertAlmostEqual(dx2, 55.0, places=2, msg=f"Expected dx=55 after upstream edit, got {dx2}")
        self.assertAlmostEqual(dy2, 30.0, places=2)
        self.assertAlmostEqual(dz2, 10.0, places=2)

    def test_criterion_g_undo_redo_and_failed_operation_recovery(self):
        """
        Criterion G: Verify undo/redo and recovery from a failed modelling operation.
        """
        doc = CADDocument("TestDoc_G")

        # Step 1: Base Box
        doc.push_undo_state()
        doc.history.add_feature("box", {"dx": 20.0, "dy": 20.0, "dz": 20.0})
        doc.recompute()
        self.assertIsNotNone(doc.current_solid)

        # Step 2: Add Cylinder (Join)
        doc.push_undo_state()
        doc.history.add_feature("cylinder", {"radius": 5.0, "height": 15.0, "z": 20.0, "operation": "join"})
        doc.recompute()
        dx, dy, dz = SolidOperations.get_bounding_dimensions(doc.current_solid)
        self.assertAlmostEqual(dz, 35.0, places=2)

        # Test Undo -> Should revert back to 20x20x20 box
        undo_ok = doc.undo()
        self.assertTrue(undo_ok)
        dx_u, dy_u, dz_u = SolidOperations.get_bounding_dimensions(doc.current_solid)
        self.assertAlmostEqual(dz_u, 20.0, places=2, msg=f"Expected dz=20 after undo, got {dz_u}")

        # Test Redo -> Should restore joined cylinder
        redo_ok = doc.redo()
        self.assertTrue(redo_ok)
        dx_r, dy_r, dz_r = SolidOperations.get_bounding_dimensions(doc.current_solid)
        self.assertAlmostEqual(dz_r, 35.0, places=2, msg=f"Expected dz=35 after redo, got {dz_r}")

        # Test Error Recovery: Trigger impossible geometry operation (Fillet with excessive radius)
        doc.push_undo_state()
        feat = doc.history.add_feature("fillet", {"radius": 999.0})
        rec_success, err_msg = doc.recompute()

        # Engine should report error gracefully without crashing
        self.assertFalse(rec_success)
        self.assertIsNotNone(feat.error_message)

        # Recover by undoing the invalid feature
        doc.undo()
        self.assertIsNotNone(doc.current_solid)
        self.assertTrue(SolidOperations.count_topology(doc.current_solid)["solids"] >= 1)


if __name__ == "__main__":
    unittest.main()
