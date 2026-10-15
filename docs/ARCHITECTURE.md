# MechCAD Architecture & Engineering Design

## 1. Executive Architecture Summary

MechCAD is a modular, standalone mechanical 3D CAD application built for Windows 10/11 x64. It is engineered specifically for mechanical and automobile engineering students to learn real parametric 3D CAD workflows matching industrial standards (such as Autodesk Fusion 360).

### Core Components
1. **Geometry Kernel**: Open CASCADE Technology (OCCT 7.8) via official `cadquery-ocp` (`OCP`).
   - Precise Boundary Representation (B-Rep) geometry (solids, shells, faces, wires, edges, vertices).
   - High-precision geometric operations: Prisms/Extrude, Revolve, Cuts/Pockets, Fillets, Chamfers, Booleans, STEP/STL exchange.
2. **Sketch Constraint Solver**: SolveSpace 2D/3D Geometric Constraint Solver (`slvs`).
   - Exact numerical constraint solver with degrees-of-freedom (DOF) diagnostics.
   - Solves coincident, horizontal, vertical, distance, angle, diameter, radius, tangent, parallel, perpendicular, midpoint, symmetry.
3. **Parametric Feature History Engine**:
   - Directed Acyclic Graph (DAG) dependency manager.
   - Recomputes downstream features upon upstream dimension changes.
   - Interactive timeline rollback and undo/redo stacks.
4. **Desktop UI & 3D Viewport**:
   - `PySide6` (Qt 6) application shell.
   - Hardware-accelerated OpenGL 3D viewport with CAD-standard mouse navigation (Orbit, Pan, Zoom).
   - Interactive 3D ViewCube orientation widget and floating Navigation Bar.
   - Fusion 360-style dense dark engineering theme.
5. **Engineering Learning Modules**:
   - Interactive automobile engineering exercises: Stepped transmission shafts, bearing retainers, mounting brackets, connecting rods, EV motor housing.

---

## 2. Directory Structure

```
d:\MasterCAD\
├── docs\
│   ├── ARCHITECTURE.md
│   ├── UI_SPECIFICATION.md
│   └── KNOWN_LIMITATIONS.md
├── mechcad\
│   ├── __init__.py
│   ├── app.py                     # High-DPI application lifecycle
│   ├── core\
│   │   ├── document.py            # CAD Document, body collection, active items
│   │   ├── history.py             # Feature DAG, recompute engine, rollback
│   │   ├── units.py               # Units conversion (mm, inch, deg)
│   │   └── project_io.py          # Native .mcad serialization (JSON/BRep)
│   ├── kernel\
│   │   ├── occ_solid.py           # OCCT primitives, extrude, cut, fillet, chamfer, booleans
│   │   ├── occ_export.py          # STEP import/export, STL export, DXF export
│   │   └── occ_tessellator.py     # Rapid triangulation & edge extraction for OpenGL
│   ├── sketcher\
│   │   ├── solver.py              # Real SLVS constraint solver bridge
│   │   ├── elements.py            # 2D Points, Lines, Circles, Arcs
│   │   ├── constraints.py         # 2D Constraints data model
│   │   └── sketch.py              # Sketch container, profile wire generator
│   ├── ui\
│   │   ├── main_window.py         # Main CAD window assembly
│   │   ├── theme.py               # Fusion 360 dark styling & QSS
│   │   ├── app_header.py          # Top header & document tabs
│   │   ├── ribbon.py              # Dense tool ribbon (Solid / Sketch tabs)
│   │   ├── browser.py             # Model browser tree
│   │   ├── viewport_3d.py         # OpenGL CAD canvas
│   │   ├── viewcube.py            # 3D interactive ViewCube
│   │   ├── nav_bar.py             # Floating bottom-center nav bar
│   │   ├── property_panel.py      # Contextual parameter dialogs
│   │   ├── sketch_palette.py      # Sketch options palette
│   │   ├── timeline.py            # Parametric feature timeline
│   │   ├── status_bar.py          # Coordinate & solver status bar
│   │   └── learning_panel.py      # Automotive learning exercise panel
│   └── learning\
│       └── automotive_exercises.py # Automobile engineering CAD tutorials
├── tests\
│   ├── test_kernel.py             # Acceptance criteria tests
│   ├── test_solver.py             # Geometric constraint solver tests
│   ├── test_parametric.py         # Upstream edit & recompute tests
│   └── test_document_io.py        # STEP/STL export/import tests
├── run_mechcad.py                 # Desktop launcher
└── README.md
```

---

## 3. Parametric Data Flow

```
[2D Sketch (Lines, Arcs)]
         |
         v
[SLVS Constraint Solver] ----> Validates DOF & Computes Exact 2D Coordinates
         |
         v
[OCCT Wire & Face Builder] --> Constructs TopoDS_Wire & TopoDS_Face
         |
         v
[OCCT Feature Engine] -------> Extrude / Pocket / Revolve / Fillet / Chamfer
         |
         v
[TopoDS_Shape Solid] --------> Precise B-Rep Solid Geometry
         |
         +---------------------------------------+
         |                                       |
         v                                       v
[Tessellator & OpenGL Canvas]           [STEP / STL Exporters]
  - Triangulation (Shaded faces)          - STEPControl_Writer (Lossless CAD exchange)
  - Boundary Discretisation (Edges)       - StlAPI_Writer (3D Printing meshes)
```
