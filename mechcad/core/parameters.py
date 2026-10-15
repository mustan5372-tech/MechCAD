"""
MechCAD Parametric Expression & Parameters Engine
Faithfully replicates Autodesk Fusion 360's "fx Change Parameters" system.
Manages Model Parameters (d1, d2, ...) and User Parameters with dynamic expression evaluation.
"""

import math
import re
from typing import Dict, Any, List, Optional, Callable


class Parameter:
    """Represents a single parametric dimension or variable in the design."""

    def __init__(self, name: str, unit: str = "mm", expression: str = "0.0",
                 comment: str = "", is_user: bool = False, owner: str = ""):
        self.name = name.strip()
        self.unit = unit.strip()
        self.expression = str(expression).strip()
        self.value: float = 0.0
        self.comment = comment.strip()
        self.is_user = is_user
        self.owner = owner  # e.g., 'Sketch 1', 'Extrude 1', or 'User'

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "unit": self.unit,
            "expression": self.expression,
            "value": self.value,
            "comment": self.comment,
            "is_user": self.is_user,
            "owner": self.owner,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Parameter":
        p = cls(
            name=data.get("name", "d1"),
            unit=data.get("unit", "mm"),
            expression=data.get("expression", "0.0"),
            comment=data.get("comment", ""),
            is_user=data.get("is_user", False),
            owner=data.get("owner", "")
        )
        p.value = float(data.get("value", 0.0))
        return p


class ParameterManager:
    """Central registry and evaluator for all parametric variables in a CAD document."""

    def __init__(self):
        self.parameters: Dict[str, Parameter] = {}
        self._param_counter: int = 0
        self._change_listeners: List[Callable[[], None]] = []

    def add_listener(self, callback: Callable[[], None]):
        self._change_listeners.append(callback)

    def _notify_changed(self):
        for cb in self._change_listeners:
            try:
                cb()
            except Exception:
                pass

    def next_model_param_name(self) -> str:
        self._param_counter += 1
        name = f"d{self._param_counter}"
        while name in self.parameters:
            self._param_counter += 1
            name = f"d{self._param_counter}"
        return name

    def register_model_param(self, expression: str, unit: str = "mm",
                             owner: str = "", comment: str = "", name: Optional[str] = None) -> Parameter:
        pname = name or self.next_model_param_name()
        param = Parameter(pname, unit=unit, expression=str(expression), comment=comment, is_user=False, owner=owner)
        self.parameters[pname] = param
        self.evaluate_all()
        return param

    def add_user_param(self, name: str, expression: str, unit: str = "mm", comment: str = "") -> Parameter:
        name = name.strip()
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
            raise ValueError(f"Invalid parameter name '{name}'. Must start with letter or underscore.")
        param = Parameter(name, unit=unit, expression=str(expression), comment=comment, is_user=True, owner="User")
        self.parameters[name] = param
        self.evaluate_all()
        self._notify_changed()
        return param

    def set_expression(self, name: str, new_expression: str) -> float:
        if name not in self.parameters:
            raise KeyError(f"Parameter '{name}' not found")
        self.parameters[name].expression = str(new_expression).strip()
        self.evaluate_all()
        self._notify_changed()
        return self.parameters[name].value

    def delete_parameter(self, name: str) -> bool:
        if name in self.parameters:
            del self.parameters[name]
            self.evaluate_all()
            self._notify_changed()
            return True
        return False

    def evaluate_expression(self, expr_str: str) -> float:
        """Evaluates an algebraic expression containing numbers, math functions, or parameter names."""
        expr_clean = str(expr_str).strip()
        # Strip common unit suffix like 'mm', 'deg', 'in' if appended to literal
        expr_clean = re.sub(r'(\d+(?:\.\d+)?)\s*(?:mm|deg|in|cm)', r'\1', expr_clean)

        # Build safe evaluation context
        safe_dict: Dict[str, Any] = {
            "sin": lambda a: math.sin(math.radians(a)),
            "cos": lambda a: math.cos(math.radians(a)),
            "tan": lambda a: math.tan(math.radians(a)),
            "asin": lambda v: math.degrees(math.asin(v)),
            "acos": lambda v: math.degrees(math.acos(v)),
            "atan": lambda v: math.degrees(math.atan(v)),
            "sqrt": math.sqrt,
            "pi": math.pi,
            "abs": abs,
            "min": min,
            "max": max,
            "round": round,
        }

        # Inject current evaluated parameter values
        for p_name, p in self.parameters.items():
            safe_dict[p_name] = p.value

        try:
            val = float(eval(expr_clean, {"__builtins__": None}, safe_dict))
            return val
        except Exception:
            # Fallback direct float parse
            try:
                # Extract first float
                m = re.search(r"[-+]?(?:\d*\.\d+|\d+)", expr_clean)
                if m:
                    return float(m.group(0))
            except Exception:
                pass
            return 0.0

    def evaluate_all(self):
        """Resolves dependencies between parameters iteratively."""
        # Run up to 4 passes to handle forward references
        for _ in range(4):
            for param in self.parameters.values():
                try:
                    param.value = self.evaluate_expression(param.expression)
                except Exception:
                    pass

    def get_value(self, name_or_expr: Any, default: float = 0.0) -> float:
        """Resolves a parameter name or mathematical expression to its current numeric value."""
        if isinstance(name_or_expr, (int, float)):
            return float(name_or_expr)
        s = str(name_or_expr).strip()
        if not s:
            return default
        if s in self.parameters:
            return self.parameters[s].value
        return self.evaluate_expression(s)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "counter": self._param_counter,
            "params": {k: p.to_dict() for k, p in self.parameters.items()}
        }

    def from_dict(self, data: Dict[str, Any]):
        self._param_counter = data.get("counter", 0)
        self.parameters.clear()
        for k, pdata in data.get("params", {}).items():
            self.parameters[k] = Parameter.from_dict(pdata)
        self.evaluate_all()
