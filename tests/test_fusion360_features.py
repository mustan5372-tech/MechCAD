"""
Automated QA Tests for Autodesk Fusion 360 Parity Features
Tests:
- Parameters engine with algebraic expression evaluation
- Shell solid modeling operation
- Mirror solid modeling operation
- Split Body operation
- In-canvas sketch profile polygon extraction
- Fusion 360 UI dialogs (ParametersDialog, ShortcutSearchPopup)
"""

import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"

import unittest
from PySide6.QtWidgets import QApplication

from mechcad.core.document import CADDocument
from mechcad.core.parameters import ParameterManager
from mechcad.kernel.occ_solid import SolidOperations
from mechcad.ui.main_window import MainWindow
from mechcad.ui.parameters_dialog import ParametersDialog
from mechcad.ui.shortcut_search import ShortcutSearchPopup

app = QApplication.instance() or QApplication([])


class TestFusion360Parity(unittest.TestCase):

    def test_parameters_engine_expression_evaluation(self):
        """Verifies algebraic parameter expressions and cross-parameter references."""
        pm = ParameterManager()
        p_len = pm.add_user_param("length", "50.0", "mm", "Base length")
        p_w = pm.add_user_param("width", "length / 2.0", "mm", "Half length")
        p_thick = pm.add_user_param("wall", "sqrt(16.0)", "mm", "Wall thickness")

        self.assertAlmostEqual(p_len.value, 50.0, places=3)
        self.assertAlmostEqual(p_w.value, 25.0, places=3)
        self.assertAlmostEqual(p_thick.value, 4.0, places=3)

        # Update upstream parameter and verify downstream updates
        pm.set_expression("length", "80.0")
        self.assertAlmostEqual(pm.get_value("length"), 80.0, places=3)
        self.assertAlmostEqual(pm.get_value("width"), 40.0, places=3)

    def test_shell_operation(self):
        """Verifies Fusion 360 Shell command hollows out a solid."""
        box = SolidOperations.make_box(40.0, 30.0, 20.0)
        shelled = SolidOperations.make_shell(box, thickness=2.0)
        self.assertIsNotNone(shelled)
        self.assertFalse(shelled.IsNull())

        topo = SolidOperations.count_topology(shelled)
        # A shelled box with 1 open face has 11 faces (5 outer, 5 inner, 1 lip / or 6 outer, 5 inner)
        self.assertGreaterEqual(topo["faces"], 10, "Shelled solid must have inner and outer faces")

    def test_mirror_operation(self):
        """Verifies Mirror solid command across reference planes."""
        box = SolidOperations.make_box(20.0, 15.0, 10.0, x=5.0, y=5.0, z=0.0)
        mirrored = SolidOperations.make_mirror(box, plane="XZ")
        self.assertIsNotNone(mirrored)
        self.assertFalse(mirrored.IsNull())

        xmin, ymin, zmin, xmax, ymax, zmax = SolidOperations.get_bounding_box(mirrored)
        # Mirrored across XZ plane (y=0) should have negative Y coordinates
        self.assertLessEqual(ymin, 0.0)

    def test_split_body_operation(self):
        """Verifies Split Body operation cuts solid at given plane offset."""
        box = SolidOperations.make_box(30.0, 30.0, 30.0, x=0.0, y=0.0, z=0.0)
        split = SolidOperations.split_body(box, plane="XY", offset=15.0)
        self.assertIsNotNone(split)
        self.assertFalse(split.IsNull())

        dx, dy, dz = SolidOperations.get_bounding_dimensions(split)
        self.assertAlmostEqual(dz, 15.0, places=1)

    def test_sketch_profile_polygons(self):
        """Verifies that closed sketch loops produce closed profile polygons for shaded rendering."""
        doc = CADDocument("TestSketchProfile")
        sk = doc.create_sketch("Profile1", plane="XY")
        sk.add_rect(0.0, 0.0, 30.0, 20.0)
        sk.solve()

        polys = sk.get_profile_polygons()
        self.assertGreaterEqual(len(polys), 1, "Closed rectangle must generate shaded profile polygon")
        self.assertGreaterEqual(len(polys[0]), 4, "Rectangle polygon ring must have at least 4 vertices")

    def test_fusion_dialogs_instantiation(self):
        """Verifies that ParametersDialog and ShortcutSearchPopup instantiate without errors."""
        window = MainWindow()
        param_dlg = ParametersDialog(window.doc.parameters, window)
        self.assertIsNotNone(param_dlg)
        self.assertIsNotNone(param_dlg.tree)

        shortcut_popup = ShortcutSearchPopup(window)
        self.assertIsNotNone(shortcut_popup)
        self.assertGreater(shortcut_popup.list_widget.count(), 10)
        window.close()

    def test_extrude_symmetric(self):
        """Verifies symmetric extrusion on sketch face extends equally in both directions."""
        doc = CADDocument("TestExtrudeSymmetric")
        sk = doc.create_sketch("Rect1", plane="XY")
        sk.add_rect(0.0, 0.0, 20.0, 20.0)
        sk.solve()
        face = sk.to_occ_face()

        # Symmetric extrude 15mm
        shape = SolidOperations.extrude_face(face, 15.0, direction=(0.0, 0.0, 1.0), symmetric=True)
        self.assertIsNotNone(shape)
        xmin, ymin, zmin, xmax, ymax, zmax = SolidOperations.get_bounding_box(shape)
        self.assertAlmostEqual(zmin, -15.0, places=2)
        self.assertAlmostEqual(zmax, 15.0, places=2)

    def test_feature_suppression(self):
        """Verifies parametric feature suppression temporarily disables feature without deletion."""
        doc = CADDocument("TestSuppression")
        # Feature 1: Box 40x40x40
        f1 = doc.history.add_feature("box", {"dx": 40.0, "dy": 40.0, "dz": 40.0})
        # Feature 2: Fillet 3mm
        f2 = doc.history.add_feature("fillet", {"radius": 3.0})

        success, _ = doc.recompute()
        self.assertTrue(success)
        topo_active = SolidOperations.count_topology(doc.current_solid)
        # With fillet, box has cylindrical edge faces (typically 26 faces)
        self.assertGreater(topo_active["faces"], 6)

        # Suppress fillet
        f2.is_suppressed = True
        success, _ = doc.recompute()
        self.assertTrue(success)
        topo_suppressed = SolidOperations.count_topology(doc.current_solid)
        # Suppressed fillet reverts back to plain 6-face box
        self.assertEqual(topo_suppressed["faces"], 6)

        # Unsuppress fillet
        f2.is_suppressed = False
        success, _ = doc.recompute()
        self.assertTrue(success)
        topo_restored = SolidOperations.count_topology(doc.current_solid)
        self.assertEqual(topo_restored["faces"], topo_active["faces"])

    def test_viewport_live_preview_and_animation(self):
        """Verifies viewport preview shape management and camera animation transitions."""
        window = MainWindow()
        vp = window.viewport

        # 1. Test live preview shape
        box_preview = SolidOperations.make_box(20.0, 20.0, 20.0)
        vp.set_preview_shape(box_preview)
        self.assertIsNotNone(vp.preview_tessellation)
        self.assertGreater(len(vp.preview_tessellation.vertices), 0)

        # Clear preview
        vp.set_preview_shape(None)
        self.assertIsNone(vp.preview_tessellation)

        # 2. Test smooth camera animation
        vp.animate_to_orientation(90.0, 45.0, target_dist=200.0, duration_ms=100)
        self.assertTrue(vp._camera_anim_timer.isActive())
        # Step animation to completion
        import time
        time.sleep(0.05)
        vp._camera_anim_duration = 20
        vp._on_camera_anim_step()
        self.assertAlmostEqual(vp.azimuth, 90.0, places=1)
        self.assertAlmostEqual(vp.elevation, 45.0, places=1)
        self.assertAlmostEqual(vp.camera_dist, 200.0, places=1)
        self.assertFalse(vp._camera_anim_timer.isActive())

        window.close()


if __name__ == "__main__":
    unittest.main()

