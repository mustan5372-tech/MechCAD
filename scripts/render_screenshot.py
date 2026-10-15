"""
Render full high-fidelity screenshot of MechCAD MainWindow.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase, QPixmap, QPainter
from PySide6.QtCore import Qt

from mechcad.ui.main_window import MainWindow
from mechcad.learning.automotive_exercises import ALL_EXERCISES

def main():
    app = QApplication.instance() or QApplication(sys.argv)

    font_path = "C:/Windows/Fonts/segoeui.ttf"
    if os.path.exists(font_path):
        QFontDatabase.addApplicationFont(font_path)
    font_bold = "C:/Windows/Fonts/segoeuib.ttf"
    if os.path.exists(font_bold):
        QFontDatabase.addApplicationFont(font_bold)

    window = MainWindow()
    window.resize(1360, 850)

    # Load 3D model with features
    ex = ALL_EXERCISES[0]
    window._load_learning_exercise(ex)

    window.show()
    app.processEvents()

    pix = QPixmap(1360, 850)
    pix.fill(Qt.transparent)
    window.render(pix)

    out_path = r"C:\Users\sanaw\.gemini\antigravity-ide\brain\076950b5-a136-4b41-9db9-861e35bb0a1d\fusion360_mechcad_full.png"
    pix.save(out_path)
    print("Screenshot saved to:", out_path)

if __name__ == "__main__":
    main()
