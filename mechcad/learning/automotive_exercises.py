"""
MechCAD Automobile Engineering Learning Modules
Preloaded real mechanical learning exercises for automotive students.
Constructs parametric CAD models step-by-step using Open CASCADE and SolveSpace.
"""

from typing import Dict, Any, List
from mechcad.core.document import CADDocument


class AutomotiveExercise:
    def __init__(self, exercise_id: str, title: str, category: str, description: str, steps: List[str], hints: List[str]):
        self.exercise_id = exercise_id
        self.title = title
        self.category = category
        self.description = description
        self.steps = steps
        self.hints = hints

    def build_model(self) -> CADDocument:
        """Constructs the reference CAD document with full feature history."""
        raise NotImplementedError


class SteppedShaftExercise(AutomotiveExercise):
    def __init__(self):
        super().__init__(
            exercise_id="shaft_keyway",
            title="Stepped Gearbox Shaft with Keyway",
            category="Transmission Components",
            description="A stepped transmission input shaft featuring bearing seats, gear mounting shoulder, and a DIN 6885 parallel keyway.",
            steps=[
                "1. Create main shaft body: Cylinder dia 35 mm, length 60 mm.",
                "2. Create bearing journal shoulder: Cylinder dia 25 mm, length 40 mm (Union).",
                "3. Create end coupling seat: Cylinder dia 20 mm, length 30 mm (Union).",
                "4. Cut DIN 6885 keyway: Box 6 mm x 25 mm x 3.5 mm depth (Cut).",
                "5. Apply 1.0 mm lead-in chamfers on shaft ends."
            ],
            hints=[
                "Stepped diameters prevent axial migration of bearings and gears.",
                "Keyways should have generous fillet radii to mitigate torsional stress concentration."
            ]
        )

    def build_model(self) -> CADDocument:
        doc = CADDocument(name="Stepped_Shaft_Keyway")
        doc.history.add_feature("cylinder", {"radius": 17.5, "height": 60.0, "x": 0.0, "y": 0.0, "z": 0.0, "operation": "new_body"}, "Main Shaft (Dia 35)")
        doc.history.add_feature("cylinder", {"radius": 12.5, "height": 40.0, "x": 0.0, "y": 0.0, "z": 60.0, "operation": "join"}, "Bearing Seat (Dia 25)")
        doc.history.add_feature("cylinder", {"radius": 10.0, "height": 30.0, "x": 0.0, "y": 0.0, "z": 100.0, "operation": "join"}, "Coupling Journal (Dia 20)")
        # Keyway cut on main shoulder
        doc.history.add_feature("box", {"dx": 6.0, "dy": 4.0, "dz": 25.0, "x": -3.0, "y": 14.5, "z": 15.0, "operation": "cut"}, "Keyway (6x4x25)")
        doc.history.add_feature("chamfer", {"distance": 1.0}, "End Chamfers")
        doc.recompute()
        return doc


class BearingHousingExercise(AutomotiveExercise):
    def __init__(self):
        super().__init__(
            exercise_id="bearing_housing",
            title="Wheel Hub Bearing Retainer Housing",
            category="Chassis & Suspension",
            description="A flanged bearing carrier supporting deep-groove ball bearings with a 4-bolt pitch circle mounting pattern.",
            steps=[
                "1. Extrude rectangular mounting flange plate: 80 x 80 x 12 mm.",
                "2. Create central bearing cylinder boss: dia 60 mm, height 35 mm.",
                "3. Cut central bearing bore: dia 40 mm through-hole.",
                "4. Cut 4x M8 clearance mounting holes (dia 9 mm) in a 60 mm pitch circle.",
                "5. Apply 3.0 mm transition fillets between flange and boss."
            ],
            hints=[
                "Bolt holes are positioned at (±30 mm, ±30 mm) from the hub centre.",
                "Ensure sufficient wall thickness between bearing bore and outer cylinder."
            ]
        )

    def build_model(self) -> CADDocument:
        doc = CADDocument(name="Wheel_Bearing_Housing")
        # Flange base
        doc.history.add_feature("box", {"dx": 80.0, "dy": 80.0, "dz": 12.0, "x": -40.0, "y": -40.0, "z": 0.0, "operation": "new_body"}, "Flange Plate (80x80)")
        # Boss
        doc.history.add_feature("cylinder", {"radius": 30.0, "height": 35.0, "x": 0.0, "y": 0.0, "z": 12.0, "operation": "join"}, "Bearing Boss (Dia 60)")
        # Bore
        doc.history.add_feature("hole", {"diameter": 40.0, "depth": 50.0, "center_x": 0.0, "center_y": 0.0, "through_all": True}, "Bearing Bore (Dia 40)")
        # 4 Mounting bolt holes
        doc.history.add_feature("hole", {"diameter": 9.0, "depth": 15.0, "center_x": 28.0, "center_y": 28.0, "through_all": True}, "Bolt Hole 1")
        doc.history.add_feature("hole", {"diameter": 9.0, "depth": 15.0, "center_x": -28.0, "center_y": 28.0, "through_all": True}, "Bolt Hole 2")
        doc.history.add_feature("hole", {"diameter": 9.0, "depth": 15.0, "center_x": -28.0, "center_y": -28.0, "through_all": True}, "Bolt Hole 3")
        doc.history.add_feature("hole", {"diameter": 9.0, "depth": 15.0, "center_x": 28.0, "center_y": -28.0, "through_all": True}, "Bolt Hole 4")
        doc.history.add_feature("fillet", {"radius": 2.0}, "Flange Fillets")
        doc.recompute()
        return doc


class ConnectingRodExercise(AutomotiveExercise):
    def __init__(self):
        super().__init__(
            exercise_id="connecting_rod",
            title="Engine Connecting Rod & Piston Pin End",
            category="Engine Powertrain",
            description="Internal combustion engine connecting rod featuring small-end pin eye, I-beam beam shank, and crank-journal big end.",
            steps=[
                "1. Big-end crank boss: dia 50 mm, width 24 mm.",
                "2. Small-end piston pin boss: dia 30 mm, width 20 mm at 120 mm center-to-center distance.",
                "3. Connect with rectangular shank body.",
                "4. Cut crank pin bore: dia 38 mm.",
                "5. Cut piston pin bore: dia 20 mm.",
                "6. Add structural fillets."
            ],
            hints=[
                "Connecting rods undergo intense alternating tensile and compressive loads.",
                "Transitions between the shank and the big/small ends must have generous radii."
            ]
        )

    def build_model(self) -> CADDocument:
        doc = CADDocument(name="Connecting_Rod")
        # Big end
        doc.history.add_feature("cylinder", {"radius": 25.0, "height": 24.0, "x": 0.0, "y": 0.0, "z": 0.0, "operation": "new_body"}, "Big End Boss (Dia 50)")
        # Small end (offset by 120 mm in Y)
        doc.history.add_feature("cylinder", {"radius": 15.0, "height": 20.0, "x": 0.0, "y": 120.0, "z": 2.0, "operation": "join"}, "Small End Boss (Dia 30)")
        # Shank
        doc.history.add_feature("box", {"dx": 16.0, "dy": 100.0, "dz": 16.0, "x": -8.0, "y": 10.0, "z": 4.0, "operation": "join"}, "Shank Body")
        # Crank pin bore
        doc.history.add_feature("hole", {"diameter": 36.0, "depth": 30.0, "center_x": 0.0, "center_y": 0.0, "through_all": True}, "Crank Pin Bore (Dia 36)")
        # Small pin bore
        doc.history.add_feature("hole", {"diameter": 18.0, "depth": 30.0, "center_x": 0.0, "center_y": 120.0, "through_all": True}, "Piston Pin Bore (Dia 18)")
        doc.recompute()
        return doc


class EVMotorHousingExercise(AutomotiveExercise):
    def __init__(self):
        super().__init__(
            exercise_id="ev_housing",
            title="Electric Vehicle (EV) Traction Motor Stator Casing",
            category="Electric Powertrain",
            description="Lightweight aluminium alloy motor housing featuring cooling channel ribs and gearbox interface flange.",
            steps=[
                "1. Create stator outer cylinder: dia 160 mm, length 140 mm.",
                "2. Create inner rotor/stator cavity bore: dia 130 mm (Cut).",
                "3. Add gearbox mounting flange: dia 200 mm, thickness 15 mm.",
                "4. Add 8x radial cooling ribs around the perimeter.",
                "5. Cut 6x flange mounting bolt holes (dia 11 mm) on 180 mm pitch circle."
            ],
            hints=[
                "EV traction motors require strict concentricity tolerances between stator and rotor air gap.",
                "External cooling ribs maximize convective surface area."
            ]
        )

    def build_model(self) -> CADDocument:
        doc = CADDocument(name="EV_Motor_Housing")
        # Stator casing outer
        doc.history.add_feature("cylinder", {"radius": 80.0, "height": 140.0, "x": 0.0, "y": 0.0, "z": 0.0, "operation": "new_body"}, "Outer Casing (Dia 160)")
        # Internal stator bore
        doc.history.add_feature("cylinder", {"radius": 65.0, "height": 135.0, "x": 0.0, "y": 0.0, "z": 5.0, "operation": "cut"}, "Stator Bore (Dia 130)")
        # Mounting flange
        doc.history.add_feature("cylinder", {"radius": 100.0, "height": 15.0, "x": 0.0, "y": 0.0, "z": 0.0, "operation": "join"}, "Gearbox Flange (Dia 200)")
        doc.recompute()
        return doc


ALL_EXERCISES = [
    SteppedShaftExercise(),
    BearingHousingExercise(),
    ConnectingRodExercise(),
    EVMotorHousingExercise(),
]
