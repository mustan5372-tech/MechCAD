"""
MechCAD Automobile Engineering Learning Panel
Interactive learning sidebar with guided mechanical CAD tutorials and reference model loading.
"""

from typing import List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QTextBrowser, QFrame, QSplitter
)
from PySide6.QtCore import Qt, Signal

from mechcad.ui.theme import ThemeColors
from mechcad.learning.automotive_exercises import ALL_EXERCISES, AutomotiveExercise


class LearningPanel(QWidget):
    """Drawer panel displaying automobile engineering exercises and hints."""

    load_model_requested = Signal(object)  # AutomotiveExercise
    start_practice_requested = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LearningPanel")
        self.exercises = ALL_EXERCISES
        self.current_exercise: AutomotiveExercise = self.exercises[0]
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        # Header Title
        lbl_head = QLabel("AUTOMOBILE ENGINEERING TUTORIALS")
        lbl_head.setStyleSheet(f"font-weight: 700; font-size: 11px; color: {ThemeColors.TEXT_MUTED}; letter-spacing: 1px;")
        layout.addWidget(lbl_head)

        lbl_desc = QLabel("Learn real 3D parametric mechanical CAD workflows matching industrial standards.")
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(lbl_desc)

        # Exercise List
        self.list_widget = QListWidget()
        for ex in self.exercises:
            item = QListWidgetItem(f"⚙ {ex.title}")
            item.setToolTip(f"{ex.category}: {ex.description}")
            self.list_widget.addItem(item)
        self.list_widget.setCurrentRow(0)
        self.list_widget.currentRowChanged.connect(self._on_exercise_changed)
        layout.addWidget(self.list_widget)

        # Detailed Guide Viewer
        self.guide_view = QTextBrowser()
        self.guide_view.setStyleSheet("background-color: #1a1a1a; border: 1px solid #333; padding: 6px; font-size: 11px;")
        layout.addWidget(self.guide_view)

        # Action Buttons
        btn_layout = QHBoxLayout()
        self.btn_load = QPushButton("Load Reference Model")
        self.btn_load.setObjectName("PrimaryButton")
        self.btn_load.setToolTip("Loads complete parametric CAD model with design history into the workspace")
        self.btn_load.clicked.connect(self._on_load_model)

        btn_layout.addWidget(self.btn_load)
        layout.addLayout(btn_layout)

        self._update_guide()

    def _on_exercise_changed(self, row: int):
        if 0 <= row < len(self.exercises):
            self.current_exercise = self.exercises[row]
            self._update_guide()

    def _update_guide(self):
        ex = self.current_exercise
        html = f"""
        <h3 style="color: #40a9ff; margin-bottom: 2px;">{ex.title}</h3>
        <p style="color: #888; font-size: 10px; margin-top: 0;"><b>Category:</b> {ex.category}</p>
        <p style="color: #ddd;">{ex.description}</p>
        
        <h4 style="color: #fff; margin-bottom: 4px;">Modeling Steps:</h4>
        <ol style="color: #ccc; padding-left: 18px;">
        """
        for step in ex.steps:
            html += f"<li>{step}</li>"
        html += """
        </ol>
        
        <h4 style="color: #ffb900; margin-bottom: 4px;">Engineering Insights:</h4>
        <ul style="color: #bbb; padding-left: 18px;">
        """
        for hint in ex.hints:
            html += f"<li>{hint}</li>"
        html += "</ul>"
        self.guide_view.setHtml(html)

    def _on_load_model(self):
        self.load_model_requested.emit(self.current_exercise)
