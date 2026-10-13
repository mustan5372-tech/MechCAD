"""
MechCAD Native Project File Persistence (.mcad)
Saves and loads parametric design history, sketches, dimensions, and dependencies.
"""

import json
import os
from typing import Tuple, Optional
from mechcad.core.document import CADDocument


class ProjectIO:
    """Serializes and deserializes native MechCAD project documents (.mcad)."""

    FORMAT_VERSION = "1.0.0"

    @classmethod
    def save_project(cls, document: CADDocument, filepath: str) -> bool:
        """Saves document state to an editable .mcad file."""
        if not filepath.lower().endswith(".mcad"):
            filepath += ".mcad"

        doc_dict = document.to_dict()
        project_data = {
            "format": "MechCAD_Project",
            "version": cls.FORMAT_VERSION,
            "document": doc_dict,
        }

        temp_path = filepath + ".tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(project_data, f, indent=2)

        if os.path.exists(filepath):
            os.remove(filepath)
        os.rename(temp_path, filepath)

        document.filepath = filepath
        document.is_dirty = False
        return True

    @classmethod
    def open_project(cls, filepath: str) -> CADDocument:
        """Opens and recomputes a .mcad project file."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Project file not found: {filepath}")

        with open(filepath, "r", encoding="utf-8") as f:
            project_data = json.load(f)

        if project_data.get("format") != "MechCAD_Project":
            raise ValueError(f"Invalid MechCAD project file format: {filepath}")

        doc_data = project_data.get("document", {})
        doc = CADDocument(name=doc_data.get("name", os.path.splitext(os.path.basename(filepath))[0]))
        doc.from_dict(doc_data)
        doc.filepath = filepath
        doc.is_dirty = False

        # Recompute to reconstruct exact Open CASCADE solids
        success, err = doc.recompute()
        if not success:
            print(f"Warning on reopening project {filepath}: {err}")

        return doc
