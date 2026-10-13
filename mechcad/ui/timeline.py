"""
MechCAD Parametric Feature Timeline
Autodesk Fusion 360-style bottom design history bar with rollback handle, playback, and token context menus.
"""

from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QToolButton, QScrollArea, QFrame, QMenu
)
from PySide6.QtCore import Qt, Signal, QRect
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont

from mechcad.ui.theme import ThemeColors
from mechcad.core.history import FeatureHistory, Feature


FEATURE_ICONS = {
    "sketch": "✏",
    "extrude": "⬆",
    "revolve": "🔄",
    "fillet": "⌒",
    "chamfer": "⊿",
    "hole": "🕳",
    "box": "📦",
    "cylinder": "🛢",
    "sphere": "⚪",
    "pattern_linear": "⊞",
    "pattern_circular": "❂",
    "bool_fuse": "⚯",
    "bool_cut": "⊖",
}


class TimelineToken(QToolButton):
    """Visual badge for an individual modeling feature in the timeline."""

    def __init__(self, feature: Feature, index: int, parent=None):
        super().__init__(parent)
        self.feature = feature
        self.index = index
        self.setCheckable(False)
        self.setFixedSize(54, 28)
        self.setToolTip(f"{feature.name} ({feature.kind})\nClick to select, Right-click to edit/suppress")

        icon_char = FEATURE_ICONS.get(feature.kind, "⚙")
        self.setText(f"{icon_char} {index + 1}")
        self._update_style()

    def _update_style(self, is_active: bool = True):
        bg = ThemeColors.TIMELINE_TOKEN if is_active else "#1a1a1a"
        color = ThemeColors.TEXT_PRIMARY if is_active else "#666666"
        border = ThemeColors.TIMELINE_TOKEN_BORDER if is_active else "#333333"
        if self.feature.error_message:
            border = ThemeColors.ACCENT_RED
            color = "#ff6b6b"

        self.setStyleSheet(f"""
            QToolButton {{
                background-color: {bg};
                color: {color};
                border: 1px solid {border};
                border-radius: 3px;
                font-size: 10px;
                font-weight: 600;
                padding: 2px;
            }}
            QToolButton:hover {{
                background-color: {ThemeColors.TIMELINE_TOKEN_HOVER};
                border: 1px solid #666;
            }}
        """)


class FeatureTimeline(QWidget):
    """Chronological parametric timeline container with step controls and rollback bar."""

    rollback_changed = Signal(int)
    feature_edit_requested = Signal(str)  # feature_id
    feature_suppress_requested = Signal(str)  # feature_id
    feature_delete_requested = Signal(str)  # feature_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TimelineContainer")
        self.setFixedHeight(38)
        self._tokens: List[TimelineToken] = []
        self._rollback_index = 0
        self.init_ui()

    def init_ui(self):
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(6, 2, 8, 2)
        root_layout.setSpacing(4)

        # 1. Playback Controls
        self.btn_to_start = QToolButton()
        self.btn_to_start.setText("|<")
        self.btn_to_start.setToolTip("Roll to Beginning")
        self.btn_to_start.clicked.connect(self._roll_to_start)
        root_layout.addWidget(self.btn_to_start)

        self.btn_step_back = QToolButton()
        self.btn_step_back.setText("<")
        self.btn_step_back.setToolTip("Step Backward in Design History")
        self.btn_step_back.clicked.connect(self._step_back)
        root_layout.addWidget(self.btn_step_back)

        self.btn_step_fwd = QToolButton()
        self.btn_step_fwd.setText(">")
        self.btn_step_fwd.setToolTip("Step Forward in Design History")
        self.btn_step_fwd.clicked.connect(self._step_forward)
        root_layout.addWidget(self.btn_step_fwd)

        self.btn_to_end = QToolButton()
        self.btn_to_end.setText(">|")
        self.btn_to_end.setToolTip("Roll to End")
        self.btn_to_end.clicked.connect(self._roll_to_end)
        root_layout.addWidget(self.btn_to_end)

        # Separator
        sep = QLabel("|")
        sep.setStyleSheet("color: #444; font-size: 10px;")
        root_layout.addWidget(sep)

        # 2. Scrollable Feature Track
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")

        self.track_widget = QWidget()
        self.track_layout = QHBoxLayout(self.track_widget)
        self.track_layout.setContentsMargins(2, 0, 2, 0)
        self.track_layout.setSpacing(4)
        self.track_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.scroll_area.setWidget(self.track_widget)

        root_layout.addWidget(self.scroll_area)

    def refresh(self, history: FeatureHistory):
        """Rebuilds the timeline tokens and places the rollback handle."""
        self._tokens.clear()
        while self.track_layout.count():
            item = self.track_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._rollback_index = history.rollback_index

        for idx, feat in enumerate(history.features):
            is_active = idx < history.rollback_index
            token = TimelineToken(feat, idx, self.track_widget)
            token._update_style(is_active)
            token.setContextMenuPolicy(Qt.CustomContextMenu)
            token.customContextMenuRequested.connect(lambda pos, f=feat: self._show_token_menu(pos, f))
            token.clicked.connect(lambda checked=False, i=idx: self._on_token_clicked(i))
            self.track_layout.addWidget(token)
            self._tokens.append(token)

            # Insert Rollback Bar Indicator
            if idx + 1 == history.rollback_index:
                bar = QLabel()
                bar.setFixedWidth(4)
                bar.setFixedHeight(26)
                bar.setStyleSheet(f"background-color: {ThemeColors.TIMELINE_ROLLBACK}; border-radius: 2px;")
                bar.setToolTip("Rollback Bar (Current State)")
                self.track_layout.addWidget(bar)

        self.track_layout.addStretch()

    def _on_token_clicked(self, index: int):
        self.rollback_changed.emit(index + 1)

    def _show_token_menu(self, pos, feature: Feature):
        menu = QMenu(self)
        act_edit = menu.addAction(f"Edit {feature.name}...")
        act_edit.triggered.connect(lambda: self.feature_edit_requested.emit(feature.feature_id))

        act_suppress = menu.addAction("Unsuppress" if feature.is_suppressed else "Suppress")
        act_suppress.triggered.connect(lambda: self.feature_suppress_requested.emit(feature.feature_id))

        menu.addSeparator()
        act_del = menu.addAction("Delete")
        act_del.triggered.connect(lambda: self.feature_delete_requested.emit(feature.feature_id))

        menu.exec(self.mapToGlobal(pos))

    def _roll_to_start(self):
        self.rollback_changed.emit(0)

    def _step_back(self):
        if self._rollback_index > 0:
            self.rollback_changed.emit(self._rollback_index - 1)

    def _step_forward(self):
        if self._rollback_index < len(self._tokens):
            self.rollback_changed.emit(self._rollback_index + 1)

    def _roll_to_end(self):
        self.rollback_changed.emit(len(self._tokens))
