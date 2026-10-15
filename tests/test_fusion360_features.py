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

    def test_primitives_sphere_torus_cone(self):
        """Verifies sphere, torus, and cone parametric features recompute correctly."""
        doc = CADDocument("TestPrimitives")
        # 1. Sphere
        doc.history.add_feature("sphere", {"radius": 15.0})
        ok, err = doc.recompute()
        self.assertTrue(ok, f"Sphere recompute failed: {err}")
        dx, dy, dz = SolidOperations.get_bounding_dimensions(doc.current_solid)
        self.assertAlmostEqual(dx, 30.0, places=1)

        # 2. Torus
        doc.history.features.clear()
        doc.history.add_feature("torus", {"r_major": 25.0, "r_minor": 5.0})
        ok, err = doc.recompute()
        self.assertTrue(ok, f"Torus recompute failed: {err}")
        dx, dy, dz = SolidOperations.get_bounding_dimensions(doc.current_solid)
        self.assertGreaterEqual(dx, 58.0)
        self.assertLessEqual(dx, 66.0)

        # 3. Cone
        doc.history.features.clear()
        doc.history.add_feature("cone", {"r1": 20.0, "r2": 5.0, "height": 30.0})
        ok, err = doc.recompute()
        self.assertTrue(ok, f"Cone recompute failed: {err}")
        dx, dy, dz = SolidOperations.get_bounding_dimensions(doc.current_solid)
        self.assertAlmostEqual(dz, 30.0, places=1)

    def test_construction_plane_and_offset_sketch(self):
        """Verifies construction datum plane creation and sketch coordinate offset mapping."""
        doc = CADDocument("TestConstruction")
        pid = doc.add_construction_plane("offset", base_plane="XY", offset=50.0)
        self.assertEqual(doc.construction_planes[pid]["offset"], 50.0)
        self.assertIn(pid, doc.construction_planes)

        # Create sketch on construction plane
        sk = doc.create_sketch(plane="XY", offset=50.0)
        self.assertEqual(sk.offset, 50.0)
        p = sk.map_to_3d(10.0, 20.0)
        self.assertAlmostEqual(p.X(), 10.0, places=3)
        self.assertAlmostEqual(p.Y(), 20.0, places=3)
        self.assertAlmostEqual(p.Z(), 50.0, places=3)

    def test_transform_shape_move(self):
        """Verifies Move / Copy transformation of a solid body."""
        box = SolidOperations.make_box(20.0, 20.0, 20.0)
        moved = SolidOperations.transform_shape(box, dx=10.0, dy=20.0, dz=30.0, rz=90.0)
        self.assertIsNotNone(moved)
        xmin, ymin, zmin, xmax, ymax, zmax = SolidOperations.get_bounding_box(moved)
        self.assertAlmostEqual(zmin, 30.0, places=2)
        self.assertAlmostEqual(zmax, 50.0, places=2)

    def test_sketch_hit_testing_and_selection(self):
        """Verifies viewport sketch entity hit-testing and selection toggling."""
        window = MainWindow()
        vp = window.viewport
        sk = window.doc.create_sketch(plane="XY")
        p1 = sk.add_point(0.0, 0.0)
        p2 = sk.add_point(40.0, 0.0)
        l1 = sk.add_line(p1, p2)
        c1 = sk.add_circle(20.0, 20.0, 10.0)
        sk.solve()
        vp.set_sketch(sk)

        # Hit-test point
        kind, eid = vp._hit_test_sketch(0.0, 0.5, thresh=2.0)
        self.assertEqual(kind, "point")
        self.assertEqual(eid, p1)

        # Hit-test line segment
        kind, eid = vp._hit_test_sketch(20.0, 0.5, thresh=2.0)
        self.assertEqual(kind, "line")
        self.assertEqual(eid, l1)

        # Hit-test circle circumference
        kind, eid = vp._hit_test_sketch(20.0, 30.0, thresh=2.0)
        self.assertEqual(kind, "circle")
        self.assertEqual(eid, c1)

        # Selection state
        vp.selected_sketch_lines.add(l1)
        self.assertIn(l1, vp.selected_sketch_lines)
        window.close()

    def test_sketch_constraints_dispatch(self):
        """Verifies constraints (horizontal, vertical, parallel, perpendicular) solve on selected entities."""
        window = MainWindow()
        window._create_new_sketch("XY")
        sk = window.doc.get_sketch(window.active_sketch_id)

        # Add 2 lines
        p1 = sk.add_point(0.0, 0.0)
        p2 = sk.add_point(50.0, 5.0)
        l1 = sk.add_line(p1, p2)

        p3 = sk.add_point(0.0, 20.0)
        p4 = sk.add_point(50.0, 22.0)
        l2 = sk.add_line(p3, p4)

        # Select line 1 and apply horizontal constraint
        window.viewport.selected_sketch_lines = {l1}
        window._handle_sketch_constraint("constrain_horizontal")
        sk = window.doc.get_sketch(window.active_sketch_id)
        pt1 = sk.points[p1]
        pt2 = sk.points[p2]
        self.assertAlmostEqual(pt1.v, pt2.v, places=2)

        # Select both lines and apply parallel constraint
        window.viewport.selected_sketch_lines = {l1, l2}
        window._handle_sketch_constraint("constrain_parallel")
        pt3 = sk.points[p3]
        pt4 = sk.points[p4]
        self.assertAlmostEqual(pt3.v, pt4.v, places=2)

        window.close()


if __name__ == "__main__":
    unittest.main()


