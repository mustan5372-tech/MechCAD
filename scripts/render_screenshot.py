import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase, QPixmap, QPainter, QImage
from PySide6.QtCore import Qt, QPoint

from mechcad.ui.main_window import MainWindow
from mechcad.learning.automotive_exercises import ALL_EXERCISES

def composite_screenshot(window: MainWindow) -> QPixmap:
    pix = QPixmap(window.size())
    pix.fill(Qt.transparent)
    window.render(pix)

    # Composite OpenGL 3D Viewport framebuffer
    vp_img = window.viewport.grabFramebuffer()
    if not vp_img.isNull():
        painter = QPainter(pix)
        vp_pos = window.viewport.mapTo(window, QPoint(0, 0))
        painter.drawImage(vp_pos, vp_img)

        # Composite HUD overlays (ViewCube and FloatingNavBar)
        vc_pos = window.viewport.viewcube.mapTo(window, QPoint(0, 0))
        window.viewport.viewcube.render(painter, vc_pos)

        nb_pos = window.viewport.nav_bar.mapTo(window, QPoint(0, 0))
        window.viewport.nav_bar.render(painter, nb_pos)

        painter.end()

    return pix


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

    # 1. Full Solid Model View
    pix1 = composite_screenshot(window)
    out_path1 = r"C:\Users\sanaw\.gemini\antigravity-ide\brain\076950b5-a136-4b41-9db9-861e35bb0a1d\fusion360_mechcad_full.png"
    pix1.save(out_path1)
    print("Screenshot 1 saved to:", out_path1)

    # 2. Extrude Dialog & Live Amber Preview View
    sk = window.doc.create_sketch("Mount_Flange_Sketch", plane="XY")
    sk.add_rect(-30.0, -30.0, 30.0, 30.0)
    sk.solve()
    window.active_sketch_id = sk.sketch_id
    window.property_panel.show_extrude(sk.sketch_id, default_dist=25.0)
    window.dock_properties.setVisible(True)
    window._on_property_preview_changed("extrude", {"sketch_id": sk.sketch_id, "distance": 25.0, "symmetric": False})
    window._refresh_all()
    app.processEvents()

    pix2 = composite_screenshot(window)
    out_path2 = r"C:\Users\sanaw\.gemini\antigravity-ide\brain\076950b5-a136-4b41-9db9-861e35bb0a1d\fusion360_mechcad_extrude_preview.png"
    pix2.save(out_path2)
    print("Screenshot 2 saved to:", out_path2)

    window.close()

if __name__ == "__main__":
    main()



