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

## Download & Install

### Latest Release
Download the latest Windows x64 installer from the **[GitHub Releases](https://github.com/mustan5372-tech/MechCAD/releases/latest)** page:

| Artifact | Description |
|---|---|
| `MechCAD-Setup-vX.Y.Z-x64.exe` | Windows x64 installer (Inno Setup) |
| `SHA256SUMS.txt` | SHA-256 checksum for integrity verification |

### Installation Steps
1. Download **`MechCAD-Setup-vX.Y.Z-x64.exe`** from the latest release.
2. Run the installer and follow the setup wizard.
3. Launch MechCAD from the **Start Menu** or **Desktop** shortcut.

### Verify Installer Integrity
```powershell
certutil -hashfile MechCAD-Setup-vX.Y.Z-x64.exe SHA256
```
Compare the output hash with the value in **SHA256SUMS.txt** from the same release.

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

### Fusion 360 Commands & Shortcuts Reference
- **S Key Design Shortcuts Search:** Press `S` anywhere in the modeling canvas to open the instant floating command search popup with quick tool badges.
- **Create Sketch:** Click `✏ Create Sketch` or press `L`/`R`/`C`. The viewport highlights the 3 Origin Planes (`XY`, `XZ`, `YZ`). Click a plane to align camera and enter 2D sketch mode.
- **In-Canvas Interactive Drawing:**
  - **Line (`L`):** Click point 1, drag with live Length and Angle Heads-Up Display (HUD), click point 2. Continuous chaining with automatic snapping to origin and endpoints.
  - **2-Point Rectangle (`R`):** Click corner 1, drag with Width & Height HUD, click corner 2. Automatically applies coincident corners and horizontal/vertical constraints.
  - **Center Rectangle:** Click center, drag corner.
  - **Center Diameter Circle (`C`):** Click center, drag with diameter HUD, click to place.
  - **Sketch Dimension (`D`):** Click line or two points, drag out witness lines, enter exact dimension.
  - **Finish Sketch:** Click prominent `[✔ FINISH SKETCH]` in top-right to return to 3D mode with shaded closed profiles.
- **3D Parametric Features:**
  - **Extrude (`E`):** Distance, Direction (One Side, Two Sides, Symmetric), Operation (Join, Cut, New Body, Intersect).
  - **Revolve:** Axis (X, Y, Z), Angle (360° or partial), Operation.
  - **Hole (`H`):** Diameter, Depth, Through All, Counterbore / Countersink.
  - **Fillet (`F`):** Constant radius fillet on mechanical edges.
  - **Chamfer:** Equal distance chamfer on edges.
  - **Shell:** Hollow out solid body with uniform wall thickness.
  - **Combine:** Boolean Join (Union), Cut (Subtract), Intersect (Common).
  - **Split Body:** Cut body with reference plane.
  - **Pattern:** Rectangular Pattern (X & Y counts/spacings) and Circular Polar Pattern.
  - **Mirror:** Mirror solid body across XY, XZ, or YZ plane.
- **Manage Parameters (`fx`):** Click `fx` in header, ribbon, or press `S` to manage Model Parameters (`d1`, `d2`, ...) and custom User Parameters. Supports algebraic formulas (`length / 2`, `sqrt(...)`, `d1 * 2`).
- **Viewport Navigation:**
  - **Orbit 3D Canvas:** `Shift + Middle Mouse Drag` (with orbit pivot marker)
  - **Pan Canvas:** `Middle Mouse Drag`
  - **Zoom Canvas:** `Mouse Wheel` (centered on cursor)
  - **Fit to Window:** Double-Click Middle Mouse Button or `F6`
  - **Interactive ViewCube:** Click faces (`FRONT`, `TOP`, `RIGHT`), corners (isometric angles), or Home icon (`⌂`).
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

## Releasing a New Version (Developers)

MechCAD uses **automated GitHub Actions releases**. To publish a new version:

```powershell
# 1. Ensure all changes are committed and pushed to main
git add -A && git commit -m "feat: describe your changes" && git push origin main

# 2. Tag the release with semantic versioning
git tag -a v0.2.0 -m "MechCAD v0.2.0 — description of this release"
git push origin v0.2.0
```

This triggers the [Release workflow](.github/workflows/release.yml) which:
1. ✅ Installs dependencies from `requirements.txt`
2. ✅ Runs the automated test suite
3. ✅ Builds the standalone EXE via PyInstaller
4. ✅ Packages the installer via Inno Setup 6
5. ✅ Generates SHA-256 checksums
6. ✅ Publishes the GitHub Release with all artifacts

The release appears at [github.com/mustan5372-tech/MechCAD/releases](https://github.com/mustan5372-tech/MechCAD/releases).

### Versioning Convention
- `v0.Y.Z` — Development / pre-release versions
- `v1.0.0` — First stable production release
- Tags containing `alpha`, `beta`, or `rc` are automatically marked as pre-releases

---

## Documentation Links

- [UI Specification](file:///d:/MasterCAD/docs/UI_SPECIFICATION.md)
- [Architecture Document](file:///d:/MasterCAD/docs/ARCHITECTURE.md)
- [Acceptance Test Report](file:///d:/MasterCAD/docs/ACCEPTANCE_TEST_REPORT.md)
- [Known Limitations](file:///d:/MasterCAD/docs/KNOWN_LIMITATIONS.md)
