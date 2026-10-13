# MechCAD
> **Learn. Design. Engineer.**  
> A personal-use Windows desktop CAD learning application inspired by the professional workflow of Autodesk Fusion 360.

---

## Overview

MechCAD is an offline, engineering-grade mechanical 3D CAD application built for Windows 10/11 x64. Its primary purpose is to allow mechanical and automobile engineering students to learn and practice real parametric 3D modeling, sketch constraints, and feature history before transitioning to commercial CAD software.

Unlike superficial mockups or mesh viewers, MechCAD is built on:
- **Geometry Kernel:** Open CASCADE Technology (OCCT 7.8) B-Rep solid modeler.
- **Constraint Solver:** SolveSpace (`slvs`) 2D geometric constraint solver.
- **Desktop UI:** PySide6 (Qt 6) with an Autodesk Fusion 360-style dense dark engineering interface.
- **Parametric History:** Directed Acyclic Graph (DAG) feature tree with timeline rollback and undo/redo.
- **Standard File Exchange:** Lossless STEP (AP203/AP214), STL for 3D printing, and 2D DXF.
- **Automobile Curriculum:** Preloaded guided exercises for transmission shafts, wheel hub bearing housings, connecting rods, and EV motor casings.

---

## System Requirements

- **Operating System:** Windows 10 / Windows 11 x64.
- **Hardware:** Optimized for Intel Core i5 (11th Gen or newer), NVIDIA GeForce / Intel Iris Xe graphics, 8+ GB RAM (20 GB tested).
- **Network:** 100% Offline operation. No accounts, telemetry, or cloud dependencies.

---

## Quick Start & Launching

### Option 1: Double-Click Launcher
Double-click `launch_mechcad.bat` in the project root folder.

### Option 2: Command Line
Activate the bundled virtual environment and run the launcher:
```powershell
d:\MasterCAD\.venv\Scripts\python.exe run_mechcad.py
```

---

## User Interface Layout (Fusion 360 Reference)

```
+---------------------------------------------------------------------------------------------------------+
| [M] MechCAD - [Untitled 1.mcad *]         [Save][Undo][Redo]    [Tabs: Untitled 1 * | + ]   [Learn] [?] |_|x|
+---------------------------------------------------------------------------------------------------------+
| [DESIGN v] | SOLID | SURFACE | MESH | SHEET METAL | UTILITIES | (SKETCH)            [ FINISH SKETCH v ] |
| +-------------+-------------------+-----------------+-------------+------------+--------------------+---|
| |   CREATE    |      MODIFY       |    ASSEMBLE     |  CONSTRUCT  |  INSPECT   |       INSERT       |...|
| | [Sketch][E] | [PressPull][F][Ch]| [NewComp][Joint]| [OffsetPln] | [Measure]  | [Insert STEP/DXF]  |   |
| +-------------+-------------------+-----------------+-------------+------------+--------------------+---|
+-------------------+-----------------------------------------------------------------+-------------------+
| BROWSER        _  | 3D VIEWPORT CANVAS                              [  VIEWCUBE  ]  | PARAMETERS        |
| > MechCAD Doc     |                                                 [ (FRONT/TOP)]  | Extrude 1         |
|   > Doc Settings  |                                                                 | Distance: 10 mm   |
|     Units: mm     |                                                                 | Operation: [Join] |
|   > Named Views   |                                                                 | [ OK ] [ Cancel ] |
|   > Origin        |                                                                 |                   |
|     (X, Y, Z, Pln)|                                                                 |                   |
|   v Bodies        |                                                                 |                   |
|     [o] Body 1    |                                                                 |                   |
|   v Sketches      |                                                                 |                   |
|     [o] Sketch 1  |                    [  FLOATING NAVIGATION BAR  ]                |                   |
|                   |                    [Orbit][Look][Pan][Zoom][Fit][Vis][Grid]     |                   |
+-------------------+-----------------------------------------------------------------+-------------------+
| TIMELINE: [|<][<][>][>|]  [ (Sketch 1) -> (Extrude 1) -> (Fillet 1) ] |======(Rollback Bar)=====>          |
+---------------------------------------------------------------------------------------------------------+
| X: 0.00 mm  Y: 0.00 mm  Z: 0.00 mm | Units: mm | 1 Body Selected (20 x 30 x 10 mm) | Ready              |
+---------------------------------------------------------------------------------------------------------+
```

### Key Controls
- **Orbit 3D Canvas:** `Shift + Middle Mouse Drag` (or Orbit tool in NavBar / ViewCube)
- **Pan Canvas:** `Middle Mouse Drag` (or Pan tool in NavBar)
- **Zoom Canvas:** `Mouse Wheel`
- **Fit to Window:** `F6` or Fit icon in floating NavBar
- **Standard Views:** Click faces on the interactive ViewCube (`TOP`, `FRONT`, `RIGHT`, `HOME`)
- **Undo / Redo:** `Ctrl + Z` / `Ctrl + Y`

---

## Automated QA Tests

MechCAD includes an automated test suite verifying all geometry kernel, constraint solver, parametric recompute, and file exchange criteria:

```powershell
d:\MasterCAD\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

### Verified Acceptance Criteria:
- **A.** 20 × 30 mm sketch extruded to 10 mm verified exact bounding box (`20.000 × 30.000 × 10.000 mm`).
- **B.** Cylindrical solid with through-hole cut verified topology.
- **C.** Upstream sketch dimension change dynamically recomputes downstream 3D features.
- **D.** Project save and reopen with editable design history (`.mcad`).
- **E.** STEP lossless solid export and reimport comparison.
- **F.** Nonempty STL mesh export for 3D printing.
- **G.** Multi-step undo/redo and graceful recovery from invalid modeling operations.
- **H.** Viewport navigation and selection ray-picking.
- **I.** Nonfunctional tools clearly marked as planned.

---

## Automobile Engineering Learning Modules

Click **🎓 Automobile Learning Mode** in the top application header to open the interactive curriculum:
1. **Stepped Gearbox Shaft with Keyway:** Multi-diameter transmission input shaft with DIN 6885 keyway.
2. **Wheel Hub Bearing Retainer Housing:** Flanged housing with central bearing bore and 4-bolt pitch circle mounting.
3. **Engine Connecting Rod:** Small-end piston pin boss, I-beam shank, and big-end crank pin bore.
4. **EV Traction Motor Stator Casing:** Radial cooling fins, rotor cavity, and mounting spigot.

Click **Load Reference Model** on any exercise to immediately load the complete parametric CAD model with full feature history into the 3D workspace.

---

## Documentation Links

- [UI Specification](file:///d:/MasterCAD/docs/UI_SPECIFICATION.md)
- [Architecture Document](file:///d:/MasterCAD/docs/ARCHITECTURE.md)
- [Acceptance Test Report](file:///d:/MasterCAD/docs/ACCEPTANCE_TEST_REPORT.md)
- [Known Limitations](file:///d:/MasterCAD/docs/KNOWN_LIMITATIONS.md)
