from PySide6.QtWidgets import (
  QWidget, QVBoxLayout, QStackedWidget,
  QTreeView, QListView, QListWidget, QListWidgetItem,
  QHeaderView, QLabel, QHBoxLayout, QAbstractItemView
)
from PySide6.QtCore import Qt, QSize, Signal
import shutil
import os


class SearchResultsView(QListWidget):
  result_activated = Signal(str)

  def __init__(self, parent=None):
    super().__init__(parent)
    self.setAlternatingRowColors(True)
    self.itemDoubleClicked.connect(self._on_double_click)

  def add_result(self, path: str):
    name     = os.path.basename(path)
    location = os.path.dirname(path)
    item     = QListWidgetItem(f"{name}   —   {location}")
    item.setData(Qt.UserRole, path)
    self.addItem(item)

  def _on_double_click(self, item: QListWidgetItem):
    path = item.data(Qt.UserRole)
    if path:
      self.result_activated.emit(path)


class FileViews(QWidget):
  def __init__(self, model, parent=None):
    super().__init__(parent)
    self.model      = model
    self._last_view = 1  # remember grid/tree before search (1=grid, 0=tree)

    # --- Tree view ---
    self.tree_view = QTreeView()
    self.tree_view.setIconSize(QSize(32, 32))
    self.tree_view.setUniformRowHeights(True)
    self.tree_view.setIndentation(20)

    # --- Grid view ---
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
      view.setSelectionMode(QAbstractItemView.ExtendedSelection)

    self.tree_view.hideColumn(2)
    header = self.tree_view.header()
    header.setSectionResizeMode(0, QHeaderView.Stretch)
    header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
    header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
    header.setStretchLastSection(False)

    # --- Search results view ---
    self.search_results = SearchResultsView()

    # --- Stack: 0=tree, 1=grid, 2=search ---
    self.stack = QStackedWidget()
    self.stack.addWidget(self.tree_view)       # 0
    self.stack.addWidget(self.grid_view)       # 1
    self.stack.addWidget(self.search_results)  # 2
    self.stack.setCurrentIndex(1)

    # --- Status bar ---
    self._setup_statusbar()

    layout = QVBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    layout.addWidget(self.stack)
    layout.addWidget(self.status_bar)
    self.setLayout(layout)

  # ---------------------------------------------------------------------------
  # Root
  # ---------------------------------------------------------------------------

  def set_root(self, index):
    self.tree_view.setRootIndex(index)
    self.grid_view.setRootIndex(index)

  # ---------------------------------------------------------------------------
  # Search
  # ---------------------------------------------------------------------------

  def show_search(self):
    # self._last_view = self.stack.currentIndex()
    if self.stack.currentIndex() != 2:
      self._last_view = self.stack.currentIndex()
    self.search_results.clear()
    self.stack.setCurrentIndex(2)

  def hide_search(self):
    self.search_results.clear()
    self.stack.setCurrentIndex(self._last_view)

  def is_searching(self) -> bool:
    return self.stack.currentIndex() == 2

  # ---------------------------------------------------------------------------
  # View toggle
  # ---------------------------------------------------------------------------

  def toggle(self, toggle_btn):
    if self.stack.currentIndex() == 0:
      self.stack.setCurrentIndex(1)
      self._last_view = 1
      toggle_btn.setText("Tree View")
    else:
      self.stack.setCurrentIndex(0)
      self._last_view = 0
      toggle_btn.setText("Grid View")

  # ---------------------------------------------------------------------------
  # Status bar
  # ---------------------------------------------------------------------------

  def _setup_statusbar(self):
    self.status_bar = QWidget()
    self.status_bar.setFixedHeight(24)

    layout = QHBoxLayout()
    layout.setContentsMargins(8, 2, 8, 0)
    layout.setSpacing(16)

    self.status_items = QLabel()
    self.status_space = QLabel()

    layout.addWidget(self.status_items)
    layout.addStretch()
    layout.addWidget(self.status_space)
    self.status_bar.setLayout(layout)

  def update_status(self, path: str):
    try:
      files   = 0
      folders = 0
      for e in os.scandir(path):
        if e.is_dir(follow_symlinks=False):
          folders += 1
        else:
          files += 1
      parts = []
      if folders:
        parts.append(f"{folders} folder{'s' if folders != 1 else ''}")
      if files:
        parts.append(f"{files} file{'s' if files != 1 else ''}")
      self.status_items.setText(", ".join(parts) if parts else "Empty folder")

      usage = shutil.disk_usage(path)
      free  = usage.free
      for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if free < 1024 or unit == 'TB':
          break
        free /= 1024
      self.status_space.setText(f"{free:.1f} {unit} free")

    except PermissionError:
      self.status_items.setText("Permission denied")
      self.status_space.setText("")

  def update_status_text(self, text: str):
    self.status_items.setText(text)
    self.status_space.setText("")

  # ---------------------------------------------------------------------------
  # Signal wiring
  # ---------------------------------------------------------------------------

  def connect_double_click(self, slot):
    self.tree_view.doubleClicked.connect(slot)
    self.grid_view.doubleClicked.connect(slot)

  def connect_context_menu(self, slot):
    self.tree_view.customContextMenuRequested.connect(slot)
    self.grid_view.customContextMenuRequested.connect(slot)

  @property
  def current_view(self):
    idx = self.stack.currentIndex()
    if idx == 2:
      return self.search_results
    return self.stack.currentWidget()