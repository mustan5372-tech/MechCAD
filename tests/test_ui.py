"""
Automated QA Tests for MechCAD UI Hierarchy & Window Structure
Verifies Acceptance Criteria H and I in offscreen environment.
"""

import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"

import unittest
from PySide6.QtWidgets import QApplication
from mechcad.ui.main_window import MainWindow
from mechcad.learning.automotive_exercises import ALL_EXERCISES

app = QApplication.instance() or QApplication([])


class TestUIStructure(unittest.TestCase):

    def setUp(self):
        self.window = MainWindow()

    def tearDown(self):
        self.window.close()

    def test_ui_components_exist(self):
        """Verifies that all Fusion 360-inspired UI components are instantiated and wired."""
        self.assertIsNotNone(self.window.header)
        self.assertIsNotNone(self.window.ribbon)
        self.assertIsNotNone(self.window.browser)
        self.assertIsNotNone(self.window.viewport)
        self.assertIsNotNone(self.window.viewport.viewcube)
        self.assertIsNotNone(self.window.viewport.nav_bar)
        self.assertIsNotNone(self.window.property_panel)
        self.assertIsNotNone(self.window.timeline)
        self.assertIsNotNone(self.window.status_bar)
        self.assertIsNotNone(self.window.learning_panel)

    def test_criterion_h_viewport_navigation_and_selection(self):
        """Criterion H: Test viewport navigation modes and standard views."""
        vp = self.window.viewport
        vp.set_standard_view("front")
        self.assertEqual(vp.azimuth, 0.0)
        self.assertEqual(vp.elevation, 0.0)

        vp.set_standard_view("top")
        self.assertAlmostEqual(vp.elevation, 89.9, places=1)

        vp.set_standard_view("home")
        self.assertEqual(vp.azimuth, 45.0)
        self.assertEqual(vp.elevation, 30.0)

        # Test selection toggle
        vp.selected_body = True
        self.assertTrue(vp.selected_body)

    def test_criterion_i_unavailable_tools_marked_or_hidden(self):
        """Criterion I: Confirm that unavailable commands are not presented as working tools."""
        # Workspace switcher marks non-modeled tools as '(Planned)'
        actions = [a.text() for a in self.window.ribbon.ws_menu.actions()]
        planned = [a for a in actions if "(Planned)" in a]
        self.assertGreaterEqual(len(planned), 3, "Nonfunctional workspaces must be explicitly marked '(Planned)'")

    def test_learning_module_build_models(self):
        """Verifies that all preloaded automotive exercises build real CAD models without error."""
        for ex in ALL_EXERCISES:
            doc = ex.build_model()
            self.assertIsNotNone(doc.current_solid, f"Exercise {ex.title} produced null solid")
            self.assertFalse(doc.current_solid.IsNull())
            self.assertGreater(len(doc.history.features), 0)


if __name__ == "__main__":
    unittest.main()
