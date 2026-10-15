"""
Automated QA Tests for Project Document Persistence (.mcad)
Tests Acceptance Criterion D.
"""

import unittest
import os
import tempfile

from mechcad.core.document import CADDocument
from mechcad.core.project_io import ProjectIO
from mechcad.kernel.occ_solid import SolidOperations


class TestDocumentIO(unittest.TestCase):

    def test_criterion_d_save_and_reopen_with_editable_history(self):
        """
        Criterion D: Save and reopen a project with its editable feature history.
        """
        doc = CADDocument("Project_EngineShaft")

        # Create sketch with center rectangle
        sk = doc.create_sketch("BaseSketch", plane="XY")
        pts, lines = sk.add_center_rect(0.0, 0.0, 30.0, 40.0)
        sk.solve()

        # Add Extrude feature
        doc.history.add_feature("extrude", {
            "sketch_id": sk.sketch_id,
            "distance": 15.0,
            "operation": "new_body"
        })

        # Add Fillet feature
        doc.history.add_feature("fillet", {"radius": 2.0})

        recomp_ok, _ = doc.recompute()
        self.assertTrue(recomp_ok)
        orig_dx, orig_dy, orig_dz = SolidOperations.get_bounding_dimensions(doc.current_solid)

        with tempfile.TemporaryDirectory() as tmp_dir:
            project_path = os.path.join(tmp_dir, "test_shaft.mcad")

            # 1. Save Project
            saved_ok = ProjectIO.save_project(doc, project_path)
            self.assertTrue(saved_ok)
            self.assertTrue(os.path.exists(project_path))

            # 2. Reopen Project
            loaded_doc = ProjectIO.open_project(project_path)
            self.assertEqual(loaded_doc.name, "Project_EngineShaft")
            self.assertEqual(len(loaded_doc.history.features), 2)
            self.assertEqual(len(loaded_doc.sketches), 1)

            # Verify solid geometry matches
            load_dx, load_dy, load_dz = SolidOperations.get_bounding_dimensions(loaded_doc.current_solid)
            self.assertAlmostEqual(load_dx, orig_dx, places=2)
            self.assertAlmostEqual(load_dy, orig_dy, places=2)
            self.assertAlmostEqual(load_dz, orig_dz, places=2)

            # 3. Verify History Remains Fully Editable:
            # Add downstream hole to reopened model and recompute
            loaded_doc.history.add_feature("hole", {
                "diameter": 10.0,
                "depth": 20.0,
                "center_x": 0.0, "center_y": 0.0,
                "through_all": True
            })
            post_edit_ok, err = loaded_doc.recompute()
            self.assertTrue(post_edit_ok, f"Recompute after editing reopened project failed: {err}")
            self.assertEqual(len(loaded_doc.history.features), 3)


if __name__ == "__main__":
    unittest.main()
