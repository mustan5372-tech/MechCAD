"""
MechCAD Sketcher Constraints Data Model
Defines dimensional and geometric constraint definitions for SolveSpace.
"""

from typing import Dict, Any, Optional, List


class Constraint:
    def __init__(self, constraint_id: str, kind: str, entities: List[str], value: Optional[float] = None):
        self.constraint_id = constraint_id
        self.kind = kind.lower()
        self.entities = entities  # List of entity IDs (e.g. ['p1', 'p2'] or ['line1'])
        self.value = value        # For dimensional constraints (distance, angle, radius)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.constraint_id,
            "kind": self.kind,
            "entities": self.entities,
            "value": self.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Constraint":
        return cls(
            constraint_id=data["id"],
            kind=data["kind"],
            entities=data["entities"],
            value=data.get("value"),
        )
