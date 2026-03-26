from PySide6.QtWidgets import (
  QWidget, QHBoxLayout, QStackedWidget, QMenu,
  QToolButton, QLineEdit, QLabel, QApplication, QStyle
)
from PySide6.QtCore import QDir, Qt, Signal
from PySide6.QtGui import QPalette
from ..core.path_logic import PathLinkedList
import os


class ToolbarWidget(QWidget):
  # emitted when user clicks a breadcrumb or edits path
  navigate_requested = Signal(str)

  def __init__(self, parent=None):
    super().__init__(parent)
    self.palette = QApplication.palette()
    self._setup_nav_buttons()
    self._setup_path_stack()

    layout = QHBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(2)
    layout.addStretch()
    layout.addWidget(self.home_btn)
    layout.addWidget(self.back_btn)
    layout.addWidget(self.forward_btn)
    layout.addWidget(self.toggle_btn)
    layout.addStretch()
    self.setLayout(layout)
    self.setFixedHeight(30)

  def _setup_nav_buttons(self):
    style = QApplication.style()

    self.home_btn = QToolButton()
    self.home_btn.setIcon(style.standardIcon(QStyle.SP_DirHomeIcon))
    self.home_btn.setAutoRaise(True)

    self.back_btn = QToolButton()
    self.back_btn.setIcon(style.standardIcon(QStyle.SP_ArrowBack))
    self.back_btn.setAutoRaise(True)
    self.back_btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
    self.back_btn.setEnabled(False)

    self.forward_btn = QToolButton()
    self.forward_btn.setIcon(style.standardIcon(QStyle.SP_ArrowForward))
    self.forward_btn.setAutoRaise(True)
    self.forward_btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
    self.forward_btn.setEnabled(False)

    self.toggle_btn = QToolButton()
    self.toggle_btn.setIcon(style.standardIcon(
      QStyle.SP_FileDialogDetailedView))
    self.toggle_btn.setText("Grid")
    self.toggle_btn.setAutoRaise(True)

  def _setup_path_stack(self):
    self.path_stack = QStackedWidget()
    self.path_stack.setFixedHeight(30)

    # Page 0 — breadcrumbs
    self.breadcrumb_widget = QWidget()
    self.breadcrumb_layout = QHBoxLayout()
    self.breadcrumb_layout.setContentsMargins(4, 0, 4, 0)
    self.breadcrumb_layout.setSpacing(4)
    self.breadcrumb_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.breadcrumb_widget.setLayout(self.breadcrumb_layout)
    self.breadcrumb_widget.setStyleSheet(f"""
      QWidget {{
        background-color: {self.palette.color(QPalette.Base).name()};
        border-radius: 4px;
      }}
      QToolButton {{
        color: {self.palette.color(QPalette.Text).name()};
        background-color: transparent;
        border: none;
        border-radius: 3px;
        padding: 2px 6px;
      }}
      QToolButton:hover {{
        background-color: {self.palette.color(QPalette.AlternateBase).name()};
      }}
      QLabel {{
        color: {self.palette.color(QPalette.Mid).name()};
      }}
    """)
    self.breadcrumb_widget.mouseDoubleClickEvent = lambda e: self._enter_edit_mode()

    # Page 1 — path edit
    self.path_edit = QLineEdit()
    self.path_edit.returnPressed.connect(self._on_path_edited)
    self.path_edit.focusOutEvent = lambda e: self.path_stack.setCurrentIndex(
      0)

    self.path_stack.addWidget(self.breadcrumb_widget)
    self.path_stack.addWidget(self.path_edit)

  def update_breadcrumbs(self, path):
    while self.breadcrumb_layout.count():
        item = self.breadcrumb_layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()

    home       = QDir.homePath()
    trash_root = home + "/.local/share/Trash"
    trash_files = home + "/.local/share/Trash/files"

    path_list = PathLinkedList(path)
    current   = path_list.head

    crumbs = []
    while current:
        crumbs.append((current.name, current.full_path))
        current = current.next

    # Collapse middle crumbs if too many
    MAX_CRUMBS = 4
    if len(crumbs) > MAX_CRUMBS:
        visible = [crumbs[0]] + crumbs[-(MAX_CRUMBS - 1):]
        hidden  = crumbs[1:-(MAX_CRUMBS - 1)]
    else:
        visible = crumbs
        hidden  = []

    for i, (name, full_path) in enumerate(visible):
        if hidden and i == 1:
            overflow_btn = QToolButton()
            overflow_btn.setText("…")
            overflow_btn.setCursor(Qt.PointingHandCursor)
            overflow_btn.setAutoRaise(True)
            overflow_menu = QMenu(overflow_btn)
            for h_name, h_path in hidden:
                action = overflow_menu.addAction(h_name)
                action.triggered.connect(
                    lambda checked=False, p=h_path: self.navigate_requested.emit(p)
                )
            overflow_btn.setMenu(overflow_menu)
            overflow_btn.setPopupMode(QToolButton.InstantPopup)
            self.breadcrumb_layout.addWidget(overflow_btn)
            self.breadcrumb_layout.addWidget(QLabel('›'))

        btn = QToolButton()
        btn.setCursor(Qt.PointingHandCursor)
        btn.setAutoRaise(True)

        # Special icon for root
        if full_path == QDir.rootPath():
            btn.setIcon(QApplication.style().standardIcon(QStyle.SP_DriveHDIcon))
            btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
        else:
            btn.setText(name)

        btn.clicked.connect(
            lambda checked=False, p=full_path: self.navigate_requested.emit(p)
        )
        self.breadcrumb_layout.addWidget(btn)

        is_last = (i == len(visible) - 1)
        if is_last:
            btn.setStyleSheet(f"""
                font-weight: bold;
                color: {self.palette.color(QPalette.Text).name()};
                background-color: {self.palette.color(QPalette.AlternateBase).name()};
                border-radius: 3px;
                padding: 2px 6px;
            """)
        else:
            self.breadcrumb_layout.addWidget(QLabel('›'))

    self.path_stack.setCurrentIndex(0)

  def update_nav_buttons(self, can_go_back, can_go_forward):
    self.back_btn.setEnabled(can_go_back)
    self.forward_btn.setEnabled(can_go_forward)

  def _enter_edit_mode(self):
      self.path_stack.setCurrentIndex(1)
      self.path_edit.setFocus()
      self.path_edit.selectAll()

  def set_current_path(self, path):
    """Called by FileManager after each navigation so edit mode has the right value."""
    self.path_edit.setText(path)
    self.path_edit.setStyleSheet("")

  def _on_path_edited(self):
    new_path = self.path_edit.text()
    if os.path.exists(new_path) and os.path.isdir(new_path):
      self.navigate_requested.emit(new_path)
      self.path_stack.setCurrentIndex(0)
    else:
      self.path_edit.setStyleSheet("border: 1px solid red;")
