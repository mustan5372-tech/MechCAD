"""
MechCAD Professional Dark Engineering Theme
Faithful styling based on Autodesk Fusion 360 desktop design tokens.
"""

from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtCore import Qt

class ThemeColors:
    # App Header & Window
    BG_WINDOW = "#1e1e1e"
    BG_HEADER = "#1f1f1f"
    BG_HEADER_TAB = "#2d2d30"
    BG_HEADER_TAB_ACTIVE = "#383838"
    
    # Ribbon & Toolbars
    BG_RIBBON = "#252526"
    BG_RIBBON_TAB = "#252526"
    BG_RIBBON_TAB_ACTIVE = "#2d2d30"
    BG_RIBBON_BTN_HOVER = "#3c3c3c"
    BG_RIBBON_BTN_PRESSED = "#0e639c"
    
    # Contextual Sketch Tab
    BG_SKETCH_TAB = "#107c41"  # Fusion green accent for active sketch
    BG_SKETCH_TAB_HOVER = "#138a49"
    
    # Panels & Browser
    BG_PANEL = "#252526"
    BG_PANEL_HEADER = "#2d2d30"
    BG_PANEL_ITEM_HOVER = "#2a2d2e"
    BG_PANEL_ITEM_SELECTED = "#094771"
    
    # 3D Viewport
    VIEWPORT_TOP = "#353a42"
    VIEWPORT_BOTTOM = "#1e2227"
    SOLID_SURFACE = "#9aa0a6"      # Shaded solid metallic grey
    SOLID_EDGE = "#1a1a1a"         # Crisp black mechanical edges
    SOLID_HOVER = "#40a9ff"        # Cyan edge/face highlight on hover
    SOLID_SELECTED = "#0078d4"     # Fusion active blue selection
    
    # Timeline
    BG_TIMELINE = "#1e1e1e"
    TIMELINE_TOKEN = "#2d2d30"
    TIMELINE_TOKEN_HOVER = "#3e3e42"
    TIMELINE_TOKEN_BORDER = "#454545"
    TIMELINE_ROLLBACK = "#ffb900"  # Yellow rollback bar
    
    # Status Bar
    BG_STATUS = "#181818"
    TEXT_STATUS = "#9d9d9d"
    
    # Typography & Accents
    TEXT_PRIMARY = "#e0e0e0"
    TEXT_MUTED = "#858585"
    TEXT_ACCENT = "#40a9ff"
    BORDER_SUBTLE = "#333333"
    BORDER_FOCUS = "#0078d4"
    ACCENT_BLUE = "#0078d4"
    ACCENT_GREEN = "#2ea44f"
    ACCENT_AMBER = "#d29922"
    ACCENT_RED = "#cf222e"


FUSION_QSS = f"""
/* Global Reset & Base */
QWidget {{
    background-color: {ThemeColors.BG_WINDOW};
    color: {ThemeColors.TEXT_PRIMARY};
    font-family: "Segoe UI", "Inter", -apple-system, sans-serif;
    font-size: 12px;
    selection-background-color: {ThemeColors.ACCENT_BLUE};
    selection-color: #ffffff;
}}

/* Main Window */
QMainWindow {{
    background-color: {ThemeColors.BG_WINDOW};
}}

/* Toolbars & Ribbon */
QToolBar {{
    background-color: {ThemeColors.BG_RIBBON};
    border: none;
    spacing: 2px;
    padding: 2px 4px;
}}

/* Top Application Header */
#AppHeader {{
    background-color: {ThemeColors.BG_HEADER};
    border-bottom: 1px solid {ThemeColors.BORDER_SUBTLE};
    min-height: 38px;
    max-height: 38px;
}}

#HeaderTitle {{
    font-size: 13px;
    font-weight: 600;
    color: #ffffff;
    padding-left: 6px;
}}

#BrandBadge {{
    background-color: {ThemeColors.ACCENT_BLUE};
    color: #ffffff;
    font-weight: bold;
    font-size: 11px;
    padding: 2px 6px;
    border-radius: 2px;
}}

/* Document Tab Bar */
QTabBar::tab {{
    background-color: {ThemeColors.BG_HEADER_TAB};
    color: {ThemeColors.TEXT_MUTED};
    padding: 6px 14px;
    margin-right: 2px;
    border-top-left-radius: 3px;
    border-top-right-radius: 3px;
    border: 1px solid transparent;
}}

QTabBar::tab:selected {{
    background-color: {ThemeColors.BG_HEADER_TAB_ACTIVE};
    color: #ffffff;
    border-bottom: 2px solid {ThemeColors.ACCENT_BLUE};
}}

QTabBar::tab:hover:!selected {{
    background-color: #333333;
    color: {ThemeColors.TEXT_PRIMARY};
}}

/* Command Ribbon Tabs */
#RibbonTabBar::tab {{
    background-color: transparent;
    color: {ThemeColors.TEXT_MUTED};
    font-weight: 600;
    font-size: 11px;
    padding: 7px 14px;
    text-transform: uppercase;
    border: none;
}}

#RibbonTabBar::tab:selected {{
    background-color: {ThemeColors.BG_RIBBON_TAB_ACTIVE};
    color: #ffffff;
    border-bottom: 2px solid {ThemeColors.ACCENT_BLUE};
}}

#RibbonTabBar::tab:hover:!selected {{
    color: #ffffff;
}}

/* Ribbon Command Buttons */
QToolButton {{
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 3px;
    color: {ThemeColors.TEXT_PRIMARY};
    padding: 4px 6px;
    font-size: 11px;
}}

QToolButton:hover {{
    background-color: {ThemeColors.BG_RIBBON_BTN_HOVER};
    border: 1px solid #4a4a4a;
}}

QToolButton:pressed {{
    background-color: {ThemeColors.BG_RIBBON_BTN_PRESSED};
    border: 1px solid {ThemeColors.ACCENT_BLUE};
}}

QToolButton:checked {{
    background-color: #1e3a5f;
    border: 1px solid {ThemeColors.ACCENT_BLUE};
    color: #ffffff;
}}

/* Finish Sketch Button */
#FinishSketchBtn {{
    background-color: {ThemeColors.BG_SKETCH_TAB};
    color: #ffffff;
    font-weight: bold;
    border-radius: 3px;
    padding: 5px 12px;
    border: 1px solid #149952;
}}

#FinishSketchBtn:hover {{
    background-color: {ThemeColors.BG_SKETCH_TAB_HOVER};
}}

/* Dock Widgets & Panels */
QDockWidget {{
    titlebar-close-icon: url(none);
    titlebar-normal-icon: url(none);
    border: 1px solid {ThemeColors.BORDER_SUBTLE};
}}

QDockWidget::title {{
    background-color: {ThemeColors.BG_PANEL_HEADER};
    padding: 6px 8px;
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    color: {ThemeColors.TEXT_MUTED};
    border-bottom: 1px solid {ThemeColors.BORDER_SUBTLE};
}}

/* Tree View / Browser */
QTreeView {{
    background-color: {ThemeColors.BG_PANEL};
    border: none;
    font-size: 12px;
    padding: 4px;
}}

QTreeView::item {{
    padding: 4px 6px;
    border-radius: 2px;
}}

QTreeView::item:hover {{
    background-color: {ThemeColors.BG_PANEL_ITEM_HOVER};
}}

QTreeView::item:selected {{
    background-color: {ThemeColors.BG_PANEL_ITEM_SELECTED};
    color: #ffffff;
}}

/* Scrollbars */
QScrollBar:vertical {{
    background-color: {ThemeColors.BG_PANEL};
    width: 10px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: #424242;
    min-height: 20px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: #555555;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background-color: {ThemeColors.BG_PANEL};
    height: 10px;
}}

QScrollBar::handle:horizontal {{
    background-color: #424242;
    min-width: 20px;
    border-radius: 5px;
}}

/* Input Controls */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background-color: #1a1a1a;
    border: 1px solid {ThemeColors.BORDER_SUBTLE};
    border-radius: 3px;
    padding: 4px 8px;
    color: #ffffff;
    font-size: 12px;
}}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border: 1px solid {ThemeColors.ACCENT_BLUE};
}}

QComboBox::drop-down {{
    border: none;
    width: 18px;
}}

/* Primary & Secondary Buttons in Dialogs */
QPushButton {{
    background-color: #333333;
    border: 1px solid #444444;
    border-radius: 3px;
    padding: 5px 14px;
    color: #ffffff;
    font-weight: 500;
}}

QPushButton:hover {{
    background-color: #444444;
}}

QPushButton:pressed {{
    background-color: #222222;
}}

#PrimaryButton {{
    background-color: {ThemeColors.ACCENT_BLUE};
    border: 1px solid #005a9e;
    color: #ffffff;
    font-weight: 600;
}}

#PrimaryButton:hover {{
    background-color: #1084d8;
}}

/* Timeline Container */
#TimelineContainer {{
    background-color: {ThemeColors.BG_TIMELINE};
    border-top: 1px solid {ThemeColors.BORDER_SUBTLE};
    min-height: 36px;
    max-height: 40px;
}}

/* Floating Navigation Capsule */
#FloatingNavBar {{
    background-color: rgba(30, 30, 30, 0.88);
    border: 1px solid rgba(80, 80, 80, 0.6);
    border-radius: 18px;
    padding: 2px 8px;
}}

/* Status Bar */
QStatusBar {{
    background-color: {ThemeColors.BG_STATUS};
    color: {ThemeColors.TEXT_STATUS};
    border-top: 1px solid {ThemeColors.BORDER_SUBTLE};
    font-size: 11px;
    min-height: 22px;
}}
"""
