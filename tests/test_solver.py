"""
Automated QA Tests for SolveSpace 2D Geometric Constraint Solver Bridge
Validates sketch constraints, dimensional parameters, and degrees of freedom.
"""

import unittest
from mechcad.sketcher.sketch import Sketch
from mechcad.sketcher.solver import SketchSolver


class TestConstraintSolver(unittest.TestCase):

    def test_solve_rectangle_with_dimensions(self):
        """Tests that a 4-point rectangle with dimensional constraints solves to exact dimensions."""
        sk = Sketch("test_sk_rect", "RectTest")
        # Add 4 points with rough initial estimates
        p1 = sk.add_point(0.0, 0.0, is_fixed=True)
        p2 = sk.add_point(22.0, 1.0)
        p3 = sk.add_point(21.0, 32.0)
        p4 = sk.add_point(1.0, 31.0)

        l1 = sk.add_line(p1, p2)
        l2 = sk.add_line(p2, p3)
        l3 = sk.add_line(p3, p4)
        l4 = sk.add_line(p4, p1)

        # Apply geometric constraints
        sk.add_constraint("horizontal", [l1])
        sk.add_constraint("vertical", [l2])
        sk.add_constraint("horizontal", [l3])
        sk.add_constraint("vertical", [l4])

        # Apply dimensional constraints: width = 20.0 mm, height = 30.0 mm
        sk.add_constraint("distance", [l1], 20.0)
        sk.add_constraint("distance", [l2], 30.0)

        res = sk.solve()
        self.assertTrue(res.success, f"Solve failed: {res.message}")
        self.assertEqual(res.dof, 0, f"Expected 0 DOF (Fully Constrained), got {res.dof}")

        # Check solved point coordinates
        pt1 = sk.points[p1]
        pt2 = sk.points[p2]
        pt3 = sk.points[p3]
        pt4 = sk.points[p4]

        self.assertAlmostEqual(pt1.u, 0.0, places=3)
        self.assertAlmostEqual(pt1.v, 0.0, places=3)

        self.assertAlmostEqual(pt2.u, 20.0, places=3)
        self.assertAlmostEqual(pt2.v, 0.0, places=3)

        self.assertAlmostEqual(pt3.u, 20.0, places=3)
        self.assertAlmostEqual(pt3.v, 30.0, places=3)

        self.assertAlmostEqual(pt4.u, 0.0, places=3)
        self.assertAlmostEqual(pt4.v, 30.0, places=3)

    def test_underconstrained_degrees_of_freedom(self):
        """Tests that removing constraints properly reflects remaining degrees of freedom."""
        sk = Sketch("test_sk_dof", "DOFTest")
        p1 = sk.add_point(0.0, 0.0, is_fixed=True)
        p2 = sk.add_point(25.0, 0.0)
        l1 = sk.add_line(p1, p2)

        # Only 1 horizontal constraint, length is unconstrained
        sk.add_constraint("horizontal", [l1])
        res = sk.solve()
        self.assertTrue(res.success)
        self.assertGreater(res.dof, 0, "Expected underconstrained sketch to have DOF > 0")


if __name__ == "__main__":
    unittest.main()
