"""
MechCAD Parameters Dialog
Faithful replica of Autodesk Fusion 360's "fx Change Parameters" dialog.
Allows mechanical engineers to manage Model Parameters (d1, d2, ...) and add custom User Parameters.
"""

from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTreeWidget, QTreeWidgetItem, QHeaderView, QMessageBox,
    QComboBox, QInputDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush, QFont

from mechcad.ui.theme import ThemeColors
from mechcad.core.parameters import ParameterManager, Parameter


class ParametersDialog(QDialog):
    """Fusion 360-style Parameters Management Dialog."""

    parameters_updated = Signal()

    def __init__(self, param_mgr: ParameterManager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Parameters")
        self.setMinimumSize(680, 480)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {ThemeColors.BG_WINDOW};
                color: {ThemeColors.TEXT_PRIMARY};
            }}
            QTreeWidget {{
                background-color: {ThemeColors.BG_PANEL};
                border: 1px solid {ThemeColors.BORDER_SUBTLE};
                border-radius: 4px;
                color: {ThemeColors.TEXT_PRIMARY};
            }}
            QHeaderView::section {{
                background-color: {ThemeColors.BG_PANEL_HEADER};
                color: {ThemeColors.TEXT_MUTED};
                font-weight: 600;
                font-size: 11px;
                padding: 4px 8px;
                border: none;
                border-bottom: 1px solid {ThemeColors.BORDER_SUBTLE};
            }}
            QLineEdit {{
                background-color: #1e1e1e;
                border: 1px solid {ThemeColors.BORDER_SUBTLE};
                border-radius: 3px;
                padding: 4px 8px;
                color: #ffffff;
            }}
            QLineEdit:focus {{
                border: 1px solid {ThemeColors.BORDER_FOCUS};
            }}
        """)

        self.param_mgr = param_mgr
        self._init_ui()
        self._populate_tree()

    def _init_ui(self):
        vlayout = QVBoxLayout(self)
        vlayout.setContentsMargins(12, 12, 12, 12)
        vlayout.setSpacing(10)

        # Top Bar: Search Filter & Add User Parameter
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)

        lbl_filter = QLabel("Search:")
        top_bar.addWidget(lbl_filter)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Filter by parameter name...")
        self.txt_search.textChanged.connect(self._filter_tree)
        top_bar.addWidget(self.txt_search)

        self.btn_add_user = QPushButton("+ User Parameter")
        self.btn_add_user.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.ACCENT_BLUE};
                color: white;
                font-weight: 600;
                padding: 5px 12px;
                border-radius: 3px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: #1084d8;
            }}
        """)
        self.btn_add_user.clicked.connect(self._add_user_parameter)
        top_bar.addWidget(self.btn_add_user)

        vlayout.addLayout(top_bar)

        # Tree Widget for Hierarchical Parameters Table
        self.tree = QTreeWidget()
        self.tree.setColumnCount(5)
        self.tree.setHeaderLabels(["Parameter", "Unit", "Expression", "Value", "Comments"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(4, QHeaderView.Stretch)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        vlayout.addWidget(self.tree)

        # Bottom Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_close = QPushButton("OK")
        self.btn_close.setFixedWidth(90)
        self.btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.ACCENT_BLUE};
                color: white;
                font-weight: 600;
                padding: 6px 16px;
                border-radius: 3px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: #1084d8;
            }}
        """)
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_close)

        vlayout.addLayout(btn_layout)

    def _populate_tree(self):
        self.tree.clear()

        # Group 1: User Parameters
        user_root = QTreeWidgetItem(self.tree)
        user_root.setText(0, "User Parameters")
        user_root.setExpanded(True)
        user_root.setForeground(0, QBrush(QColor("#40a9ff")))
        f = user_root.font(0)
        f.setBold(True)
        user_root.setFont(0, f)

        # Group 2: Model Parameters
        model_root = QTreeWidgetItem(self.tree)
        model_root.setText(0, "Model Parameters")
        model_root.setExpanded(True)
        model_root.setForeground(0, QBrush(QColor("#40a9ff")))
        model_root.setFont(0, f)

        user_count = 0
        model_count = 0

        for name, param in self.param_mgr.parameters.items():
            item = QTreeWidgetItem()
            item.setText(0, param.name)
            item.setText(1, param.unit)
            item.setText(2, param.expression)
            item.setText(3, f"{param.value:.3f} {param.unit}")
            item.setText(4, param.comment or (param.owner if not param.is_user else ""))
            item.setData(0, Qt.UserRole, param.name)

            if param.is_user:
                item.setForeground(0, QBrush(QColor("#ffffff")))
                user_root.addChild(item)
                user_count += 1
            else:
                item.setForeground(0, QBrush(QColor("#d0d0d0")))
                model_root.addChild(item)
                model_count += 1

        user_root.setText(0, f"User Parameters ({user_count})")
        model_root.setText(0, f"Model Parameters ({model_count})")

    def _filter_tree(self, text: str):
        query = text.lower().strip()
        for i in range(self.tree.topLevelItemCount()):
            root = self.tree.topLevelItem(i)
            root_visible = False
            for j in range(root.childCount()):
                child = root.child(j)
                name = child.text(0).lower()
                expr = child.text(2).lower()
                match = (query in name) or (query in expr)
                child.setHidden(not match)
                if match:
                    root_visible = True
            root.setHidden(not root_visible and bool(query))

    def _add_user_parameter(self):
        # Quick modal to ask name and expression
        name, ok1 = QInputDialog.getText(self, "Add User Parameter", "Parameter Name (e.g., width, wall_thick):")
        if not ok1 or not name.strip():
            return
        expr, ok2 = QInputDialog.getText(self, "Add User Parameter", f"Expression for '{name}' (e.g., 25.0, length * 2):")
        if not ok2 or not expr.strip():
            return

        try:
            self.param_mgr.add_user_param(name.strip(), expr.strip(), unit="mm", comment="User defined")
            self._populate_tree()
            self.parameters_updated.emit()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not create parameter:\n{e}")

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        pname = item.data(0, Qt.UserRole)
        if not pname or pname not in self.param_mgr.parameters:
            return

        param = self.param_mgr.parameters[pname]
        new_expr, ok = QInputDialog.getText(
            self, "Edit Parameter Expression",
            f"Enter new expression for '{param.name}':",
            QLineEdit.Normal, param.expression
        )
        if ok and new_expr.strip():
            try:
                self.param_mgr.set_expression(param.name, new_expr.strip())
                self._populate_tree()
                self.parameters_updated.emit()
            except Exception as e:
                QMessageBox.critical(self, "Evaluation Error", f"Failed to evaluate expression:\n{e}")
