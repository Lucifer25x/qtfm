from PySide6.QtWidgets import (
  QWidget, QVBoxLayout, QStackedWidget,
  QTreeView, QListView, QHeaderView
)
from PySide6.QtCore import Qt, QSize


class FileViews(QWidget):
  views_toggled = None

  def __init__(self, model, parent=None):
    super().__init__(parent)
    self.model = model

    # Tree view
    self.tree_view = QTreeView()
    self.tree_view.setIconSize(QSize(32, 32))
    self.tree_view.setUniformRowHeights(True)
    self.tree_view.setIndentation(20)
    self.tree_view.hideColumn(2)

    header = self.tree_view.header()
    header.setSectionResizeMode(0, QHeaderView.Stretch)
    header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
    header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
    header.setStretchLastSection(False)

    # Grid view
    self.grid_view = QListView()
    self.grid_view.setViewMode(QListView.IconMode)
    self.grid_view.setResizeMode(QListView.Adjust)
    self.grid_view.setIconSize(QSize(72, 72))
    self.grid_view.setGridSize(QSize(140, 96))
    self.grid_view.setUniformItemSizes(True)
    self.grid_view.setWordWrap(False)

    # Shared setup
    for view in [self.tree_view, self.grid_view]:
      view.setModel(model)
      view.setContextMenuPolicy(Qt.CustomContextMenu)

    # Stack
    self.stack = QStackedWidget()
    self.stack.addWidget(self.tree_view)
    self.stack.addWidget(self.grid_view)
    self.stack.setCurrentIndex(1)

    layout = QVBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(self.stack)
    self.setLayout(layout)

  def set_root(self, index):
    self.tree_view.setRootIndex(index)
    self.grid_view.setRootIndex(index)

  def toggle(self, toggle_btn):
    """Switches between grid and tree, updates the button label."""
    if self.stack.currentIndex() == 0:
      self.stack.setCurrentIndex(1)
      toggle_btn.setText("Tree View")
    else:
      self.stack.setCurrentIndex(0)
      toggle_btn.setText("Grid View")

  def connect_double_click(self, slot):
    self.tree_view.doubleClicked.connect(slot)
    self.grid_view.doubleClicked.connect(slot)

  def connect_context_menu(self, slot):
    self.tree_view.customContextMenuRequested.connect(slot)
    self.grid_view.customContextMenuRequested.connect(slot)

  @property
  def current_view(self):
    return self.stack.currentWidget()