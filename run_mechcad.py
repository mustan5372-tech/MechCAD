"""
MechCAD Windows Desktop Launcher Script
Run this script with the virtual environment Python interpreter:
    d:\\MasterCAD\\.venv\\Scripts\\python.exe run_mechcad.py
"""

import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from mechcad.app import main

if __name__ == "__main__":
    sys.exit(main())
