# MechCAD Automated QA Acceptance Test Report

**Execution Date:** 2026-10-13  
**Target Platform:** Windows 10/11 x64  
**Python Runtime:** Python 3.12.10 (MSVC v.1943 64-bit AMD64)  
**Kernel:** Open CASCADE Technology (OCCT 7.8)  
**Solver:** SolveSpace (SLVS 3.2)  
**UI Framework:** PySide6 6.12.0 (Qt 6) + PyOpenGL  
**Test Suite:** `tests/test_kernel.py`, `tests/test_solver.py`, `tests/test_parametric.py`, `tests/test_document_io.py`, `tests/test_ui.py`  
**Test Result:** **13 of 13 Automated Tests PASSED (0.457s)**

---

## Acceptance Criteria Verification Matrix

| Criterion | Description | Test Case | Status | Verification Notes |
|---|---|---|---|---|
| **A** | Create a 20 mm by 30 mm rectangular sketch and pad it to 10 mm; expected bounding dimensions are 20 x 30 x 10 mm. | `test_criterion_a_sketch_extrude_20x30x10` | **PASS** | Exact bounding box extents verified: `dx = 20.000 mm`, `dy = 30.000 mm`, `dz = 10.000 mm`. |
| **B** | Create a cylindrical solid and cut a through-hole. | `test_criterion_b_cylinder_with_cut_through_hole` | **PASS** | Cylinder radius 10 mm, height 30 mm, cut diameter 8 mm hole; verified topology has 4+ faces with inner cylindrical bore. |
| **C** | Modify an upstream dimension and verify downstream features recompute. | `test_criterion_c_upstream_dimension_change_recomputes_downstream` | **PASS** | Upstream sketch distance modified from 20 mm to 55 mm; downstream extrude recomputed automatically to `dx = 55.000 mm`. |
| **D** | Save and reopen a project with its editable feature history. | `test_criterion_d_save_and_reopen_with_editable_history` | **PASS** | Project serialized to `.mcad` and reloaded; verified feature history and solid dimensions match, and further features can be added. |
| **E** | Export a solid to STEP and reimport it; compare valid geometry and dimensions. | `test_criterion_e_step_export_and_reimport` | **PASS** | Solid exported via `STEPControl_Writer` (AP214/AP203) and reimported via `STEPControl_Reader`; extents matched within 0.001 mm. |
| **F** | Export a solid to STL and verify the resulting mesh is nonempty. | `test_criterion_f_stl_export_nonempty` | **PASS** | Tessellated solid exported via `StlAPI_Writer`; verified nonempty mesh file created (>3800 bytes). |
| **G** | Verify undo/redo and recovery from a failed modelling operation. | `test_criterion_g_undo_redo_and_failed_operation_recovery` | **PASS** | Undo/redo stack verified. Invalid fillet gracefully flagged without crashing and cleanly recovered. |
| **H** | Test viewport navigation and selection. | `test_criterion_h_viewport_navigation_and_selection` | **PASS** | Front, Top, Right, Home standard views, ViewCube orientation sync, and selection toggle tested. |
| **I** | Confirm that unavailable commands are not presented as working tools. | `test_criterion_i_unavailable_tools_marked_or_hidden` | **PASS** | Non-modeled workspaces (Generative Design, Render, CAM) are explicitly marked `(Planned)`. |

---

## Detailed Test Logs

```text
Ran 13 tests in 0.457s

OK
```
