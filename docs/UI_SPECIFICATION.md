# MechCAD UI/UX Specification
**Reference Baseline:** Autodesk Fusion 360 (Modern Desktop CAD Layout)  
**Product Name:** MechCAD  
**Tagline:** Learn. Design. Engineer.  
**Target Platform:** Windows 10/11 x64 (Offline Desktop Application)

---

## 1. Visual Hierarchy & Design System

MechCAD uses a dense, dark engineering-focused palette modelled directly on the Autodesk Fusion 360 desktop interface. It rejects flat dashboard cards, web-app spacing, and oversized touch targets in favour of compact, high-information-density CAD controls.

### Color Palette Tokens
| Token | Hex Value | Usage |
|---|---|---|
| `bg-app-header` | `#1e1e1e` | Top application titlebar and document tab strip |
| `bg-ribbon` | `#252526` | Command toolbar / ribbon container |
| `bg-ribbon-tab-active` | `#2d2d30` | Active ribbon tab header background |
| `bg-ribbon-tab-sketch` | `#107c41` | Active sketch contextual tab accent |
| `bg-panel` | `#252526` | Browser tree and contextual property panels |
| `bg-viewport-top` | `#353a42` | 3D canvas gradient top |
| `bg-viewport-bottom` | `#1e2227` | 3D canvas gradient bottom |
| `bg-timeline` | `#1f1f1f` | Bottom parametric feature history timeline |
| `bg-status-bar` | `#181818` | Bottom status bar |
| `accent-primary` | `#0078d4` | Active selection, primary dialog buttons (OK) |
| `accent-hover` | `#3c3c3c` | Hover state for ribbon buttons |
| `text-primary` | `#e0e0e0` | Standard UI labels and property text |
| `text-secondary` | `#909090` | Subtitles, shortcut hints, units |
| `border-subtle` | `#333333` | Panel borders and group dividers |
| `origin-red-x` | `#e03131` | X-axis indicator and plane accent |
| `origin-green-y` | `#2f9e44` | Y-axis indicator and plane accent |
| `origin-blue-z` | `#1971c2` | Z-axis indicator and plane accent |
| `status-constrained` | `#37b24d` | Fully constrained sketch indicator |
| `status-underconstrained`| `#f59f00` | Under-constrained degrees-of-freedom indicator |

---

## 2. Window Layout & Component Hierarchy

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
| BROWSER        _  | 3D VIEWPORT CANVAS                              [  VIEWCUBE  ]  | PROPERTIES        |
| > MechCAD Doc     |                                                 [ (FRONT/TOP)]  | Extrude 1         |
|   > Doc Settings  |                                                                 | Profile: [1]      |
|     Units: mm     |                                                                 | Distance: 10 mm   |
|   > Named Views   |                                                                 | Taper: 0.0 deg    |
|     (Top/Front/Rt)|                                                                 | Operation: [Join] |
|   > Origin        |                                                                 | [ OK ] [ Cancel ] |
|     (X, Y, Z, Pln)|                                                                 |                   |
|   v Bodies        |                                                                 |                   |
|     [o] Body 1    |                                                                 |                   |
|   v Sketches      |                                                                 |                   |
|     [o] Sketch 1  |                                                                 |                   |
|                   |                    [  FLOATING NAVIGATION BAR  ]                |                   |
|                   |                    [Orbit][Look][Pan][Zoom][Fit][Vis][Grid]     |                   |
+-------------------+-----------------------------------------------------------------+-------------------+
| TIMELINE: [|<][<][>][>|]  [ (Sketch 1) -> (Extrude 1) -> (Fillet 1) ] |======(Rollback Bar)=====>          |
+---------------------------------------------------------------------------------------------------------+
| X: 0.00 mm  Y: 0.00 mm  Z: 0.00 mm | Units: mm | 1 Body Selected (20 x 30 x 10 mm) | Ready              |
+---------------------------------------------------------------------------------------------------------+
```

---

## 3. Detailed Component Specifications

### 3.1 Application Header
- **Identity & Title:** Clean branded badge `MechCAD` with document name and modified flag (`*`).
- **Quick Access Toolbar:** File dropdown, Save (`Ctrl+S`), Undo (`Ctrl+Z`), Redo (`Ctrl+Y`).
- **Document Strip:** Tabs for open models with close (`×`) and new tab (`+`).
- **Right Utilities:** Learning Mode toggle (Automobile Engineering Tutorials), Help, and Window controls.

### 3.2 Workspace & Command Ribbon
- **Workspace Selector:** Dropdown displaying `DESIGN`.
- **Mode Tabs:** `SOLID` (default), `SURFACE`, `MESH`, `SHEET METAL`, `UTILITIES`.
- **Contextual Sketch Mode:** When active, switches ribbon to `SKETCH` with green accent tab and displays:
  - Create: Line (`L`), 2-Point Rect (`R`), Center Rect, Circle (`C`), Arc, Polygon, Slot, Dimension (`D`).
  - Modify: Fillet, Trim (`T`), Extend, Offset (`O`).
  - Constraints: Coincident, Horizontal/Vertical, Parallel, Perpendicular, Tangent, Equal, Concentric, Midpoint, Symmetry, Fix.
  - Far Right: **Finish Sketch** button with green checkmark.
- **Solid Command Groups:**
  - Create: Create Sketch, Extrude (`E`), Revolve, Hole (`H`), Sweep, Loft, Box, Cylinder, Sphere, Torus, Pattern, Mirror.
  - Modify: Fillet (`F`), Chamfer, Shell, Draft, Combine (Boolean Union, Cut, Intersect), Split Body.
  - Construct: Offset Plane, Plane at Angle, Midplane.
  - Inspect: Measure (`I`), Section View.
  - Insert: Import STEP, Import STL, Import DXF.

### 3.3 Browser (Model Tree)
- Positioned docked to the left of the canvas.
- Collapsible toggle tab on canvas edge.
- Standard tree nodes:
  - Root Component radio activation button.
  - `Document Settings` (display active units, double click to change).
  - `Named Views` (Home, Top, Front, Right).
  - `Origin` (Origin Point, X/Y/Z Axes, XY/XZ/YZ Planes) with eye icon visibility toggles.
  - `Bodies` folder containing all parametric solid bodies.
  - `Sketches` folder containing all 2D sketches.
  - Context menu on items: Edit, Rename, Suppress, Delete, Export STEP/STL.

### 3.4 3D Viewport Canvas
- Hardware-accelerated OpenGL rendering of Open CASCADE B-Rep tessellations and boundary curves.
- Dark gradient background `#353a42` to `#1e2227`.
- Dynamic millimeter ground grid with major/minor divisions.
- Standard CAD mouse navigation:
  - **Orbit:** `Shift + Middle Click Drag`
  - **Pan:** `Middle Click Drag`
  - **Zoom:** `Mouse Wheel`
  - **Select:** `Left Click` (faces, edges, sketches, bodies).
- **Interactive ViewCube (Top-Right):**
  - Clickable faces (`FRONT`, `TOP`, `RIGHT`, `LEFT`, `BACK`, `BOTTOM`).
  - Clickable edges and corners for axonometric angles.
  - Home button to reset to isometric view.
  - Projection dropdown: Perspective vs. Orthographic.
- **Floating Navigation Bar (Bottom-Center):**
  - Orbit, Look At, Pan, Zoom, Fit Window (`F6`), Visual Styles (Shaded with Edges, Wireframe), Grid Snap.

### 3.5 Contextual Property Dialogs (Right Panel)
- Docked or floating over canvas when a tool is triggered.
- Exact parameter inputs:
  - **Extrude:** Profile selection, Distance input (spinbox + slider), Direction (One Side, Two Sides, Symmetric), Operation (Join, Cut, Intersect, New Body).
  - **Revolve:** Profile, Axis, Angle (0-360°), Operation.
  - **Fillet:** Edge selection, Radius (mm).
  - **Chamfer:** Edge selection, Distance (mm).
  - **Hole:** Face selection, Diameter, Depth / Through All.
  - Primary button: Blue `OK` button; Secondary button: `Cancel`.

### 3.6 Parametric Feature Timeline (Bottom)
- Chronological ordered feature tokens (Sketch 1, Extrude 1, Fillet 1, etc.).
- Rollback bar draggable back in history to insert or modify past operations.
- Step controls: Step to Start, Step Back, Play, Step Forward, Roll to End.
- Context menu: Edit Feature, Suppress Feature, Delete Feature.

### 3.7 Status Bar (Bottom)
- Real-time XYZ coordinate readout under cursor.
- Active selection details and measured dimensions.
- Sketch solver status: `Fully Constrained` (green) or `N Degrees of Freedom` (amber).
