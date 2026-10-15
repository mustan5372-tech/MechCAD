# MechCAD v1.0.0 — Production Release

**Release Tag:** `v1.0.0`  
**Official Repository:** [https://github.com/mustan5372-tech/MechCAD](https://github.com/mustan5372-tech/MechCAD)  
**Distribution Target:** Windows 10 / Windows 11 (64-bit)

---

## Overview

**MechCAD** is a professional desktop 3D parametric computer-aided design (CAD) application engineered to match the industry-standard workflow, user interface, and interaction model of Autodesk Fusion 360. 

Powered by a hybrid architecture combining the **OpenCASCADE Technology (OCCT)** boundary-representation (B-Rep) solid modeling kernel and the **SolveSpace** 2D geometric constraint solver, MechCAD delivers industrial-grade parametric modeling without cloud dependencies or subscription lock-in.

---

## Key Features & Highlights

### 1. Autodesk Fusion 360 Desktop Experience
- **Top Application Bar:** Document title with dirty state tracking (`*`), standard File menu, undo/redo controls, and About MechCAD dialog.
- **Parametric Workspace Toolbar:** Grouped toolbars organized into **Sketch**, **Create** (Extrude, Revolve, Box, Cylinder, Sphere), **Modify** (Fillet, Chamfer, Shell, Combine), **Construct** (Offset Plane, Angled Plane, Midplane), **Pattern** (Rectangular, Circular), **Inspect** (Measure, Section Analysis), and **Select**.
- **Interactive ViewCube:** Custom 3D orientation cube in the upper-right corner supporting clicking Top, Front, Right, and Isometric faces with animated 60 FPS camera rotation transitions.
- **Viewport Navigation Bar:** Floating bottom toolbar featuring Orbit, Pan, Zoom to Fit, Visual Styles (Shaded with Visible Edges, Shaded, Wireframe), Camera Projection (Orthographic / Perspective), and Grid Snapping toggle.
- **Parametric Timeline:** Interactive bottom timeline tracking feature history with rollback markers, feature suppression/unsuppression, and edit operations.
- **Fusion Marking Menu:** Right-click radial marking menu offering instant access to Extrude, Sketch, Fillet, Pan, Orbit, and Zoom.
- **Live Amber Solid Preview:** Real-time visual feedback for Extrude and Revolve operations rendering an amber solid (`#f5a623`) with highlighted silhouette edges before committing features.

### 2. Dual B-Rep & Geometric Constraint Engine
- **OpenCASCADE B-Rep Solids:** Native support for exact analytical CAD topology (faces, edges, vertices) with Boolean operations (Join, Cut, Intersect), constant-radius fillets, distance chamfers, thin-walled shells, and construction planes.
- **Sketch Normal Alignment:** Full support for sketching and extruding along `XY`, `XZ`, and `YZ` primary planes with true 3D normal orientation and symmetric extrusion modes.
- **SolveSpace 2D Solver:** Fully integrated parametric sketcher solving dimensional constraints (length, distance, radius) and geometric constraints (horizontal, vertical, coincident, parallel, perpendicular, tangent).

### 3. Official Branding
- High-resolution metallic "M" and precision gear cog branding derived from the official artwork.
- Multi-resolution Windows application icon embedded into all executables, dialogs, taskbar, Start Menu, and installer packages.

---

## Distributable Packages

MechCAD is distributed as two official, standalone Windows installers that run on any standard 64-bit Windows installation without requiring Python or external runtimes:

| Package | Format | Architecture | Size | Description |
|---|---|---|---|---|
| **`MechCAD-Setup-x64.exe`** | Inno Setup 6 Installer | `x64` (64-bit) | ~83.4 MB | Recommended Windows setup wizard with desktop shortcut, Start Menu entry, and uninstaller. |
| **`MechCAD-Setup-x64.msi`** | Windows Installer (.msi) | `x64` (64-bit) | ~114.7 MB | Enterprise-ready MSI package suitable for per-machine silent deployment (`msiexec /i`) and corporate environments. |

---

## SHA-256 Checksums

To verify the integrity of your downloaded installation files:

```text
c05d996b0845bf9445f1ad84806f97b0ea68ce044aaaca9d509dae809b4e2744  MechCAD-Setup-x64.exe
f234a476301719e89ae32ae41d59243ffa7c894b066e5391713f04e125025c20  MechCAD-Setup-x64.msi
```

Verification command in Windows PowerShell:
```powershell
Get-FileHash -Path .\MechCAD-Setup-x64.exe -Algorithm SHA256
Get-FileHash -Path .\MechCAD-Setup-x64.msi -Algorithm SHA256
```

---

## Installation & Deployment

### Standard Installation (EXE)
1. Double-click `MechCAD-Setup-x64.exe`.
2. Follow the setup wizard to select the destination folder (defaults to `C:\Program Files\MechCAD`).
3. Select whether to create a Desktop shortcut.
4. Click **Install**.
5. Launch MechCAD from the Start Menu, Desktop shortcut, or by opening any `.mcad` project file.

### Enterprise / Silent Installation (MSI)
Run the following from an elevated command prompt or PowerShell:

```cmd
msiexec /i MechCAD-Setup-x64.msi /qn /norestart
```

To install with a detailed verbose log:
```cmd
msiexec /i MechCAD-Setup-x64.msi /qn /l*v install.log
```

To uninstall cleanly:
```cmd
msiexec /x MechCAD-Setup-x64.msi /qn
```

---

## System Requirements

- **Operating System:** Windows 10 (version 1809 or higher) / Windows 11 (64-bit)
- **Processor:** 64-bit Intel or AMD multi-core processor (x86_64)
- **Memory (RAM):** 4 GB minimum (8 GB or more recommended for complex models)
- **Graphics:** OpenGL 3.3 or higher compatible GPU
- **Disk Space:** ~450 MB free space for full installation
