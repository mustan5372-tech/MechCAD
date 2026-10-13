"""
MechCAD Application Entrypoint
Initializes Qt application lifecycle, high-DPI settings, and main window.
"""

import sys
import os

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QCoreApplication

from mechcad.ui.main_window import MainWindow


def main():
    # Enable High-DPI display support on Windows 10/11
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    app.setApplicationName("MechCAD")
    app.setApplicationDisplayName("MechCAD")
    app.setOrganizationName("MechCAD")

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
