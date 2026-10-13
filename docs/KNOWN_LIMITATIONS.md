# MechCAD Known Limitations & Architectural Notes

## 1. Scope & Design Intention
MechCAD is engineered as a personal-use educational CAD application for mechanical and automobile engineering students to master real parametric 3D modeling workflows before transitioning to industrial software like Autodesk Fusion 360. It prioritizes exact parametric solids, constraint solving, feature history, and standard file exchange over proprietary commercial cloud features.

## 2. Geometry Kernel
- **Kernel:** Open CASCADE Technology (OCCT 7.8) via official `cadquery-ocp` (`OCP`).
- **Exact Tolerances:** Real B-Rep solids, wires, and topological entities are maintained with sub-micrometer precision.
- **Complex Fillet Topologies:** Extreme fillet radii that exceed topological face limits are caught gracefully by the recompute engine and reported as feature errors without crashing the application.
- **Mesh vs. Solid Exports:** As in industrial CAD software, exporting to STL converts B-Rep solids into triangular surface meshes (using user-defined linear deflection) and does not preserve the parametric feature history tree. For lossless parametric solid exchange, STEP AP203/AP214 (`.step`) must be used.

## 3. Sketch Constraint Solver
- **Solver Engine:** SolveSpace C numerical geometric constraint solver (`slvs`).
- **Degrees of Freedom:** Evaluates underconstrained states and detects conflicting/overconstrained dimensions.
- **Supported 2D Entities:** Points, Lines, Circles, Arcs, Rectangles, Center Rectangles.
- **Supported Constraints:** Coincident, Horizontal, Vertical, Distance, Angle, Parallel, Perpendicular, Equal, Midpoint, Fix.

## 4. UI/UX Workflow
- **Desktop Reference:** Follows Autodesk Fusion 360 visual hierarchy and workspace organization (Application Bar, dense Ribbon with SOLID / SKETCH tabs, Model Browser, 3D Canvas with ViewCube and floating NavBar, contextual Property Panel, parametric Timeline with rollback handle, and Status Bar).
- **Offline Operation:** 100% offline and local. No user accounts, telemetry, or cloud storage required.
- **Assemblies & CAM:** Multi-body modeling and Boolean operations are implemented. Advanced kinematics and CNC toolpath generation are marked as Planned in the workspace dropdown.
