"""
MechCAD Parametric Feature Timeline
Autodesk Fusion 360-style bottom design history bar with vector tokens, playback controls, and rollback handle.
"""

from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QToolButton, QScrollArea, QFrame, QMenu
)
from PySide6.QtCore import Qt, Signal, QRect, QSize
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QIcon, QCursor

from mechcad.ui.theme import ThemeColors
from mechcad.ui.icons import CADIcons
from mechcad.core.history import FeatureHistory, Feature


class TimelineToken(QToolButton):
    """Visual badge for an individual modeling feature in the timeline matching Fusion 360."""

    def __init__(self, feature: Feature, index: int, parent=None):
        super().__init__(parent)
        self.feature = feature
        self.index = index
        self.setFixedSize(32, 24)
        self.setIconSize(QSize(18, 18))
        self.setCheckable(False)

        # Map feature kind to CADIcons name
        icon_map = {
            "sketch": "browser_sketch",
            "extrude": "extrude",
            "revolve": "revolve",
            "hole": "hole",
            "fillet": "fillet",
            "chamfer": "chamfer",
            "shell": "shell",
            "combine": "combine",
            "split_body": "split_body",
            "mirror": "mirror",
            "pattern_linear": "pattern_linear",
            "pattern_circular": "pattern_circular",
            "plane": "construct_plane",
            "box": "extrude",
            "cylinder": "revolve",
        }
        icon_name = icon_map.get(feature.kind, "extrude")
        self.setIcon(CADIcons.get(icon_name, 18))
        self.setToolTip(f"{feature.name} ({feature.kind})\nClick to roll here, Right-click to edit/suppress")
        self._update_style(True)

    def _update_style(self, is_active: bool = True):
        if self.feature.error_message:
            border = "#e04040"
            bg = "#3a1a1a"
        elif not is_active or self.feature.is_suppressed:
            border = "#262b32"
            bg = "#181a1f"
        else:
            border = "#3a424f"
            bg = "#282d36"

        self.setStyleSheet(f"""
            QToolButton {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 2px;
                padding: 1px;
            }}
            QToolButton:hover {{
                background-color: #353c48;
                border: 1px solid #0082c8;
            }}
        """)


class FeatureTimeline(QWidget):
    """Chronological parametric timeline container with step controls and rollback bar."""

    rollback_changed = Signal(int)
    feature_edit_requested = Signal(str)      # feature_id
    feature_suppress_requested = Signal(str)  # feature_id
    feature_delete_requested = Signal(str)    # feature_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TimelineContainer")
        self.setFixedHeight(34)
        self._tokens: List[TimelineToken] = []
        self._rollback_index = 0

        self.setStyleSheet("""
            QWidget#TimelineContainer {
                background-color: #20242b;
                border-top: 1px solid #2d333e;
            }
        """)

        self.init_ui()

    def init_ui(self):
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(8, 2, 8, 2)
        root_layout.setSpacing(2)

        # 1. Playback Controls with Vector Icons
        btn_style = """
            QToolButton {
                background: transparent;
                border: 1px solid transparent;
                border-radius: 2px;
                padding: 2px;
            }
            QToolButton:hover {
                background-color: #313742;
                border: 1px solid #414a58;
            }
            QToolButton:pressed {
                background-color: #0082c8;
            }
        """

        self.btn_to_start = QToolButton()
        self.btn_to_start.setIcon(CADIcons.get("time_start", 14))
        self.btn_to_start.setIconSize(QSize(14, 14))
        self.btn_to_start.setFixedSize(22, 22)
        self.btn_to_start.setToolTip("Roll to Beginning")
        self.btn_to_start.setStyleSheet(btn_style)
        self.btn_to_start.clicked.connect(self._roll_to_start)
        root_layout.addWidget(self.btn_to_start)

        self.btn_step_back = QToolButton()
        self.btn_step_back.setIcon(CADIcons.get("time_step_back", 14))
        self.btn_step_back.setIconSize(QSize(14, 14))
        self.btn_step_back.setFixedSize(22, 22)
        self.btn_step_back.setToolTip("Step Backward in Design History")
        self.btn_step_back.setStyleSheet(btn_style)
        self.btn_step_back.clicked.connect(self._step_back)
        root_layout.addWidget(self.btn_step_back)

        self.btn_step_fwd = QToolButton()
        self.btn_step_fwd.setIcon(CADIcons.get("time_step_fwd", 14))
        self.btn_step_fwd.setIconSize(QSize(14, 14))
        self.btn_step_fwd.setFixedSize(22, 22)
        self.btn_step_fwd.setToolTip("Step Forward in Design History")
        self.btn_step_fwd.setStyleSheet(btn_style)
        self.btn_step_fwd.clicked.connect(self._step_forward)
        root_layout.addWidget(self.btn_step_fwd)

        self.btn_to_end = QToolButton()
        self.btn_to_end.setIcon(CADIcons.get("time_end", 14))
        self.btn_to_end.setIconSize(QSize(14, 14))
        self.btn_to_end.setFixedSize(22, 22)
        self.btn_to_end.setToolTip("Roll to End")
        self.btn_to_end.setStyleSheet(btn_style)
        self.btn_to_end.clicked.connect(self._roll_to_end)
        root_layout.addWidget(self.btn_to_end)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedWidth(1)
        sep.setStyleSheet("background-color: #353d49; margin: 4px 4px;")
        root_layout.addWidget(sep)

        # 2. Scrollable Feature Track
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:horizontal {
                height: 4px;
                background: #1e2228;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #414a58;
                min-width: 20px;
                border-radius: 2px;
            }
        """)

        self.track_widget = QWidget()
        self.track_layout = QHBoxLayout(self.track_widget)
        self.track_layout.setContentsMargins(2, 0, 2, 0)
        self.track_layout.setSpacing(3)
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

            # Insert Fusion 360 Rollback Marker (Golden amber indicator bar)
            if idx + 1 == history.rollback_index:
                bar = QLabel()
                bar.setFixedWidth(4)
                bar.setFixedHeight(22)
                bar.setStyleSheet("background-color: #f5a623; border-radius: 1px;")
                bar.setToolTip("Rollback Marker (Active History Position)")
                self.track_layout.addWidget(bar)

        if not history.features or history.rollback_index == 0:
            bar = QLabel()
            bar.setFixedWidth(4)
            bar.setFixedHeight(22)
            bar.setStyleSheet("background-color: #f5a623; border-radius: 1px;")
            bar.setToolTip("Rollback Marker (Start of History)")
            self.track_layout.addWidget(bar)

        self.track_layout.addStretch()

    def _on_token_clicked(self, index: int):
        self.rollback_changed.emit(index + 1)

    def _show_token_menu(self, pos, feature: Feature):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2b3038;
                border: 1px solid #454d59;
                color: #e0e0e0;
                font-family: 'Segoe UI';
                font-size: 11px;
                padding: 4px;
            }
            QMenu::item {
                padding: 5px 22px 5px 20px;
                border-radius: 2px;
            }
            QMenu::item:selected {
                background-color: #0082c8;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background: #3e4652;
                margin: 4px 6px;
            }
        """)

        act_edit = menu.addAction(f"Edit {feature.name}...")
        act_edit.triggered.connect(lambda: self.feature_edit_requested.emit(feature.feature_id))

        act_suppress = menu.addAction("Unsuppress" if feature.is_suppressed else "Suppress")
        act_suppress.triggered.connect(lambda: self.feature_suppress_requested.emit(feature.feature_id))

        menu.addSeparator()
        act_del = menu.addAction("Delete Feature")
        act_del.triggered.connect(lambda: self.feature_delete_requested.emit(feature.feature_id))

        menu.exec(QCursor.pos())

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
