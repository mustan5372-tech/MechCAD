"""
MechCAD Units Management Module
Standard internal unit is Millimeter (mm) for length and Degree (deg) for angles.
"""

from typing import Tuple

LENGTH_UNITS = {
    "mm": 1.0,
    "cm": 10.0,
    "m": 1000.0,
    "in": 25.4,
    "ft": 304.8,
}

ANGLE_UNITS = {
    "deg": 1.0,
    "rad": 57.29577951308232,
}

class UnitManager:
    def __init__(self, length_unit: str = "mm", angle_unit: str = "deg"):
        self.length_unit = length_unit if length_unit in LENGTH_UNITS else "mm"
        self.angle_unit = angle_unit if angle_unit in ANGLE_UNITS else "deg"

    def to_internal_length(self, value: float, from_unit: str = None) -> float:
        unit = from_unit or self.length_unit
        factor = LENGTH_UNITS.get(unit, 1.0)
        return float(value) * factor

    def from_internal_length(self, value: float, to_unit: str = None) -> float:
        unit = to_unit or self.length_unit
        factor = LENGTH_UNITS.get(unit, 1.0)
        return float(value) / factor

    def format_length(self, value_mm: float, precision: int = 3) -> str:
        val = self.from_internal_length(value_mm)
        return f"{val:.{precision}f} {self.length_unit}"

    def format_angle(self, value_deg: float, precision: int = 2) -> str:
        return f"{value_deg:.{precision}f}°"

    def parse_length(self, text: str) -> float:
        text = text.strip().lower()
        for unit in LENGTH_UNITS.keys():
            if text.endswith(unit):
                num_part = text[:-len(unit)].strip()
                try:
                    return float(num_part) * LENGTH_UNITS[unit]
                except ValueError:
                    break
        try:
            val = float(text)
            return self.to_internal_length(val)
        except ValueError:
            return 0.0
