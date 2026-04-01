from PySide6.QtWidgets import (
  QHBoxLayout, QVBoxLayout, QMainWindow, QSplitter,
  QSizePolicy, QWidget
)
from PySide6.QtCore import QDir, Qt
from .core.model import FileModel
from .core.trash import TrashManager
from .utils.file_ops import FileOps
from .ui.sidebar import SidebarWidget
from .ui.toolbar import ToolbarWidget
from .ui.views import FileViews
from .ui.context_menu import ContextMenuBuilder
from pathlib import Path
import os

class FileManager(QMainWindow):
  def __init__(self):
    super().__init__()
    self.setWindowTitle("QtFM")
    self.resize(1000, 600)

    # History stacks
    self.back_stack = []
    self.forward_stack = []

    # Keep references to extra windows so GC doesn't collect them
    self._windows = []

    # Model
    self.model = FileModel()
    self.model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot | QDir.Hidden | QDir.System)
    self.model.setRootPath(QDir.rootPath())

    # Trash
    self.trash = TrashManager(self)
    self.trash_path = self.trash.trash_path

    # File operations
    self.file_ops = FileOps(self)

    # Sidebar items
    sidebar_items = [
      ("Home",      QDir.homePath()),
      ("Desktop",   QDir.homePath() + "/Desktop"),
      ("Documents", QDir.homePath() + "/Documents"),
      ("Downloads", QDir.homePath() + "/Downloads"),
      ("Music",     QDir.homePath() + "/Music"),
      ("Pictures",  QDir.homePath() + "/Pictures"),
      ("Videos",    QDir.homePath() + "/Videos"),
      (None, None),  # Separator
      ("File System",  QDir.rootPath()),
      ("Trash", self.trash_path if os.path.exists(self.trash_path) else ""),
    ]

    # --- Sidebar ---
    self.sidebar = SidebarWidget(self.model)
    self.sidebar.populate(sidebar_items)
    self.sidebar.itemClicked.connect(self.navigate_from_sidebar)

    # --- Toolbar ---
    self.toolbar = ToolbarWidget()
    self.toolbar.navigate_requested.connect(self.navigate_to)
    self.toolbar.home_btn.clicked.connect(lambda: self.navigate_to(QDir.homePath()))
    self.toolbar.back_btn.clicked.connect(self.navigate_back)
    self.toolbar.forward_btn.clicked.connect(self.navigate_forward)
    self.toolbar.up_btn.clicked.connect(self.navigate_up)
    self.toolbar.toggle_btn.clicked.connect(self.toggle_view)

    # --- File views ---
    self.file_views = FileViews(self.model)
    self.file_views.connect_double_click(self.on_item_double_clicked)
    self.file_views.connect_context_menu(self.show_context_menu)

    # --- Context menu ---
    self.context_menu = ContextMenuBuilder(self.model, self.trash_path)

    # --- Layout ---
    # Left panel: nav buttons row + sidebar
    nav_row = QWidget()
    nav_row.setFixedHeight(30)
    nav_layout = QHBoxLayout()
    nav_layout.setContentsMargins(0, 0, 0, 0)
    nav_layout.setSpacing(2)
    nav_layout.addStretch()
    nav_layout.addWidget(self.toolbar.home_btn)
    nav_layout.addWidget(self.toolbar.back_btn)
    nav_layout.addWidget(self.toolbar.forward_btn)
    nav_layout.addWidget(self.toolbar.up_btn)
    nav_layout.addWidget(self.toolbar.toggle_btn)
    nav_layout.addStretch()
    nav_row.setLayout(nav_layout)

    left_widget = QWidget()
    left_layout = QVBoxLayout()
    left_layout.setContentsMargins(5, 5, 0, 0)
    left_layout.setSpacing(2)
    left_layout.addWidget(nav_row)
    left_layout.addWidget(self.sidebar)
    left_widget.setLayout(left_layout)
    left_widget.setMaximumWidth(400)
    left_widget.setMinimumWidth(160)
    left_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

    # Right panel: breadcrumb/path stack + file views
    right_widget = QWidget()
    right_layout = QVBoxLayout()
    right_layout.setContentsMargins(0, 5, 5, 0)
    right_layout.setSpacing(2)
    right_layout.addWidget(self.toolbar.path_stack)
    right_layout.addWidget(self.file_views, 1)
    right_widget.setLayout(right_layout)

    splitter = QSplitter()
    splitter.setHandleWidth(2)
    splitter.addWidget(left_widget)
    splitter.addWidget(right_widget)
    splitter.setStretchFactor(1, 1)
    splitter.setCollapsible(0, False)
    splitter.setSizes([200, 800])
    self.splitter = splitter

    self.setCentralWidget(splitter)

    # Initial navigation
    self.navigate_to(QDir.homePath(), add_to_history=False)

  # ---------------------------------------------------------------------------
  # Navigation
  # ---------------------------------------------------------------------------

  def navigate_to(self, path, add_to_history=True, clear_forward_stack=True):
    index = self.model.index(path)
    if index.isValid():
      if add_to_history:
        current_path = self.model.filePath(self.file_views.tree_view.rootIndex())
        self.back_stack.append(current_path)
        if clear_forward_stack:
          self.forward_stack.clear()
      self.file_views.set_root(index)
      self.file_views.update_status(path)
      self.setWindowTitle(f"QtFM - {self.model.fileName(index)}")
      self.toolbar.update_nav_buttons(
        can_go_back=len(self.back_stack) > 0,
        can_go_forward=len(self.forward_stack) > 0,
        can_go_up=str(Path(path).parent) != path,
      )
      self.toolbar.set_current_path(path)
      self.toolbar.update_breadcrumbs(path)
      self.sidebar.sync_selection(path)

  def navigate_back(self):
    if self.back_stack:
      last_path = self.back_stack.pop()
      current_path = self.model.filePath(self.file_views.tree_view.rootIndex())
      self.forward_stack.append(current_path)
      self.navigate_to(last_path, add_to_history=False, clear_forward_stack=False)

  def navigate_forward(self):
    if self.forward_stack:
      next_path = self.forward_stack.pop()
      current_path = self.model.filePath(self.file_views.tree_view.rootIndex())
      self.back_stack.append(current_path)
      self.navigate_to(next_path, add_to_history=False, clear_forward_stack=False)

  def navigate_up(self):
    current = self.model.filePath(self.file_views.tree_view.rootIndex())
    parent  = str(Path(current).parent)
    if parent != current:  # already at root when they're equal
      self.navigate_to(parent)

  def navigate_from_sidebar(self, item):
    self.navigate_to(item.data(Qt.UserRole))

  def on_item_double_clicked(self, index):
    if self.model.isDir(index):
      self.navigate_to(self.model.filePath(index))

  # ---------------------------------------------------------------------------
  # View toggle
  # ---------------------------------------------------------------------------
  def toggle_view(self):
    self.file_views.toggle(self.toolbar.toggle_btn)

  # ---------------------------------------------------------------------------
  # Context menu
  # ---------------------------------------------------------------------------

  def show_context_menu(self, pos):
    self.context_menu.build(
      view=self.sender(),
      pos=pos,
      callbacks={
        'open':            self.on_item_double_clicked,
        'open_new_window': self.open_in_new_window,
        'move_to_trash':   self.trash.move_to_trash,
        'restore':         self.trash.restore,
        'delete':          self.trash.delete_permanently,
        'empty_trash':     self.trash.empty_trash,
        'create_file':     self.file_ops.create_file,
        'create_folder':   self.file_ops.create_folder,
      }
    )

  def open_in_new_window(self, path):
    new_window = FileManager()
    new_window.navigate_to(path, add_to_history=False)
    new_window.show()
    self._windows.append(new_window)