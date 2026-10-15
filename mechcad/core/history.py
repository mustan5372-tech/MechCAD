"""
MechCAD Parametric Feature History & Dependency Engine
Maintains an ordered timeline of modeling features, dependency graph, rollback, and undo/redo.
"""

from typing import List, Dict, Any, Optional
import copy

from OCP.TopoDS import TopoDS_Shape
from mechcad.kernel.occ_solid import SolidOperations


class Feature:
    """Base class for all parametric CAD features."""

    def __init__(self, feature_id: str, name: str, kind: str, params: Dict[str, Any]):
        self.feature_id = feature_id
        self.name = name
        self.kind = kind.lower()  # 'extrude', 'fillet', 'chamfer', 'hole', 'box', 'cylinder', etc.
        self.params = copy.deepcopy(params)
        self.is_suppressed = False
        self.error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.feature_id,
            "name": self.name,
            "kind": self.kind,
            "params": self.params,
            "is_suppressed": self.is_suppressed,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Feature":
        f = cls(data["id"], data["name"], data["kind"], data["params"])
        f.is_suppressed = data.get("is_suppressed", False)
        return f


class FeatureHistory:
    """Manages the chronological modeling timeline, rollback bar, and recomputations."""

    def __init__(self):
        self.features: List[Feature] = []
        # rollback_index points to the active timeline end. len(features) means at the latest state.
        self.rollback_index: int = 0
        self._counter: int = 0

    def add_feature(self, kind: str, params: Dict[str, Any], name: Optional[str] = None) -> Feature:
        self._counter += 1
        default_name = f"{kind.capitalize()} {self._counter}"
        feat_id = f"feat_{self._counter}"
        feat = Feature(feat_id, name or default_name, kind, params)

        # If rolled back, insert at rollback index
        if self.rollback_index < len(self.features):
            self.features = self.features[:self.rollback_index]
        self.features.append(feat)
        self.rollback_index = len(self.features)
        return feat

    def rollback_to(self, index: int):
        """Sets the rollback bar to a specific position in the feature history."""
        self.rollback_index = max(0, min(index, len(self.features)))

    def step_backward(self):
        if self.rollback_index > 0:
            self.rollback_index -= 1

    def step_forward(self):
        if self.rollback_index < len(self.features):
            self.rollback_index += 1

    def roll_to_end(self):
        self.rollback_index = len(self.features)

    def roll_to_beginning(self):
        self.rollback_index = 0

    def delete_feature(self, feature_id: str):
        idx = -1
        for i, f in enumerate(self.features):
            if f.feature_id == feature_id:
                idx = i
                break
        if idx != -1:
            self.features.pop(idx)
            if self.rollback_index > idx:
                self.rollback_index -= 1

    def get_active_features(self) -> List[Feature]:
        """Returns the features up to current rollback position that are not suppressed."""
        return [f for f in self.features[:self.rollback_index] if not f.is_suppressed]

    def to_list(self) -> List[Dict[str, Any]]:
        return [f.to_dict() for f in self.features]

    def from_list(self, data: List[Dict[str, Any]]):
        self.features = [Feature.from_dict(d) for d in data]
        self.rollback_index = len(self.features)
        self._counter = len(self.features)
