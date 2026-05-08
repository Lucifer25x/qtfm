from PySide6.QtWidgets import (
  QHBoxLayout, QVBoxLayout, QMainWindow, QSplitter,
  QSizePolicy, QWidget, QApplication
)
from PySide6.QtCore import QDir, Qt, QSize
from .core.model import FileModel
from .core.trash import TrashManager
from .utils.file_ops import FileOps
from .ui.sidebar import SidebarWidget
from .ui.toolbar import ToolbarWidget
from .ui.views import FileViews
from .ui.context_menu import ContextMenuBuilder
from .ui.actions import ActionRegistry
from .ui.menubar import AppMenuBar
from .ui.dialogs import PropertiesDialog
from pathlib import Path
import os


class FileManager(QMainWindow):
  ZOOM_SIZES = [32, 48, 64, 72, 96, 128]

  def __init__(self):
    super().__init__()
    self.setWindowTitle("QtFM")
    self.resize(1000, 600)

    self.back_stack  = []
    self.forward_stack = []
    self._windows    = []

    # -------------------------------------------------------------------------
    # 1. Core — no UI dependencies
    # -------------------------------------------------------------------------
    self.model = FileModel()
    self.model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot | QDir.Hidden | QDir.System)
    self.model.setRootPath(QDir.rootPath())

    self.trash      = TrashManager(self)
    self.trash_path = self.trash.trash_path
    self.file_ops   = FileOps(self)

    # -------------------------------------------------------------------------
    # 2. UI widgets
    # -------------------------------------------------------------------------
    sidebar_items = [
      ("Home",        QDir.homePath()),
      ("Desktop",     QDir.homePath() + "/Desktop"),
      ("Documents",   QDir.homePath() + "/Documents"),
      ("Downloads",   QDir.homePath() + "/Downloads"),
      ("Music",       QDir.homePath() + "/Music"),
      ("Pictures",    QDir.homePath() + "/Pictures"),
      ("Videos",      QDir.homePath() + "/Videos"),
      (None, None),
      ("File System", QDir.rootPath()),
      ("Trash",       self.trash_path if os.path.exists(self.trash_path) else ""),
    ]

    self.sidebar = SidebarWidget(self.model)
    self.sidebar.populate(sidebar_items)
    self.sidebar.itemClicked.connect(self.navigate_from_sidebar)

    self.toolbar = ToolbarWidget()
    self.toolbar.navigate_requested.connect(self.navigate_to)
    self.toolbar.search_exited.connect(self._on_search_exited)
    # self.toolbar.search_changed.connect(self._on_search_changed)

    self.file_views = FileViews(self.model)
    self.file_views.connect_double_click(self.on_item_double_clicked)
    self.file_views.connect_context_menu(self.show_context_menu)
    self.file_views.tree_view.selectionModel().selectionChanged.connect(
      self._on_selection_changed
    )
    self.file_views.grid_view.selectionModel().selectionChanged.connect(
      self._on_selection_changed
    )

    self.context_menu = ContextMenuBuilder(self.model, self.trash_path)

    # -------------------------------------------------------------------------
    # 3. Actions — must come after all widgets exist
    # -------------------------------------------------------------------------
    self.actions = ActionRegistry(self)
    self._connect_actions()
    self.setMenuBar(AppMenuBar(self.actions, self))

    # Wire nav button actions after ActionRegistry exists
    self.toolbar.home_btn.setDefaultAction(self.actions.go_home)
    self.toolbar.back_btn.setDefaultAction(self.actions.go_back)
    self.toolbar.forward_btn.setDefaultAction(self.actions.go_forward)
    self.toolbar.up_btn.setDefaultAction(self.actions.go_up)
    self.toolbar.toggle_btn.clicked.connect(self.toggle_view)

    self._on_selection_changed()

    # -------------------------------------------------------------------------
    # 4. Layout
    # -------------------------------------------------------------------------
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
    left_layout.setContentsMargins(5, 5, 5, 0)
    left_layout.setSpacing(2)
    left_layout.addWidget(nav_row)
    left_layout.addWidget(self.sidebar)
    left_widget.setLayout(left_layout)
    left_widget.setMaximumWidth(400)
    left_widget.setMinimumWidth(160)
    left_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

    right_widget = QWidget()
    right_layout = QVBoxLayout()
    right_layout.setContentsMargins(5, 5, 5, 0)
    right_layout.setSpacing(2)
    right_layout.addWidget(self.toolbar.path_bar)
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

    # -------------------------------------------------------------------------
    # 5. Initial navigation
    # -------------------------------------------------------------------------
    self.navigate_to(QDir.homePath(), add_to_history=False)

  # ---------------------------------------------------------------------------
  # Selection
  # ---------------------------------------------------------------------------

  def _on_selection_changed(self):
    has_selection = len(self._current_selection()) > 0
    has_clipboard = bool(self.file_ops.clipboard)
    for action in [
      self.actions.rename,
      self.actions.cut,
      self.actions.copy,
      self.actions.move_to_trash,
      self.actions.restore,
      self.actions.delete,
      self.actions.copy_path,
      self.actions.properties,
      self.actions.open,
      self.actions.open_new_win,
    ]:
      action.setEnabled(has_selection)
    self.actions.paste.setEnabled(has_clipboard)

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
      self.setWindowTitle(f"QtFM — {self.model.fileName(index)}")
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
    if parent != current:
      self.navigate_to(parent)

  def navigate_from_sidebar(self, item):
    self.navigate_to(item.data(Qt.UserRole))

  def on_item_double_clicked(self, index):
    if self.model.isDir(index):
      self.navigate_to(self.model.filePath(index))

  # ---------------------------------------------------------------------------
  # View
  # ---------------------------------------------------------------------------

  def toggle_view(self):
    self.file_views.toggle(self.toolbar.toggle_btn)

  def _set_view(self, index: int):
    self.file_views.stack.setCurrentIndex(index)
    self.actions.view_grid.setChecked(index == 1)
    self.actions.view_tree.setChecked(index == 0)

  # ---------------------------------------------------------------------------
  # Context menu
  # ---------------------------------------------------------------------------

  def show_context_menu(self, pos):
    view  = self.sender()
    index = view.indexAt(pos)
    self.context_menu.build(view, pos, self.actions)

  # ---------------------------------------------------------------------------
  # Helpers
  # ---------------------------------------------------------------------------

  def _current_path(self) -> str:
    return self.model.filePath(self.file_views.tree_view.rootIndex())

  def _current_selection(self) -> list[str]:
    view = self.file_views.current_view
    return [
      self.model.filePath(i)
      for i in view.selectedIndexes()
      if i.column() == 0
    ]

  def _on_selection(self, fn):
    for path in self._current_selection():
      fn(path)

  def _on_rename(self):
    paths = self._current_selection()
    if paths:
      self.file_ops.rename(paths[0])

  def _show_properties(self):
    paths = self._current_selection()
    if not paths:
      return
    dlg = PropertiesDialog(paths[0], self.model, self)
    dlg.exec()

  # ---------------------------------------------------------------------------
  # Zoom
  # ---------------------------------------------------------------------------

  def zoom_in(self):
    current = self.file_views.grid_view.iconSize().width()
    bigger  = [s for s in self.ZOOM_SIZES if s > current]
    if bigger:
      self._set_zoom(bigger[0])

  def zoom_out(self):
    current = self.file_views.grid_view.iconSize().width()
    smaller = [s for s in self.ZOOM_SIZES if s < current]
    if smaller:
      self._set_zoom(smaller[-1])

  def zoom_reset(self):
    self._set_zoom(72)

  def _set_zoom(self, size: int):
    self.file_views.grid_view.setIconSize(QSize(size, size))
    self.file_views.grid_view.setGridSize(QSize(size + 68, size + 24))

  # ---------------------------------------------------------------------------
  # Sort
  # ---------------------------------------------------------------------------

  def sort_by(self, field: str):
    col   = {'name': 0, 'size': 1, 'date': 3}.get(field, 0)
    order = (
      Qt.AscendingOrder
      if self.actions.sort_asc.isChecked()
      else Qt.DescendingOrder
    )
    self.file_views.tree_view.sortByColumn(col, order)
    self.model.sort(col, order)

  def sort_by_order(self, order):
    self.sort_by(
      'name' if self.actions.sort_name.isChecked()
      else 'size' if self.actions.sort_size.isChecked()
      else 'date'
    )

  # ---------------------------------------------------------------------------
  # Search
  # ---------------------------------------------------------------------------

  def _on_search_changed(self, query: str):
    pass

  def _on_search_exited(self):
    pass

  # ---------------------------------------------------------------------------
  # Actions wiring
  # ---------------------------------------------------------------------------

  def _connect_actions(self):
    a = self.actions

    # Navigation
    a.go_home.triggered.connect(lambda: self.navigate_to(QDir.homePath()))
    a.go_up.triggered.connect(self.navigate_up)
    a.go_back.triggered.connect(self.navigate_back)
    a.go_forward.triggered.connect(self.navigate_forward)

    # View
    a.view_grid.triggered.connect(lambda: self._set_view(1))
    a.view_tree.triggered.connect(lambda: self._set_view(0))
    a.zoom_in.triggered.connect(self.zoom_in)
    a.zoom_out.triggered.connect(self.zoom_out)
    a.zoom_reset.triggered.connect(self.zoom_reset)
    a.show_hidden.triggered.connect(
      lambda checked: self.model.set_show_hidden(checked)
    )

    # Sort
    a.sort_name.triggered.connect(lambda: self.sort_by('name'))
    a.sort_size.triggered.connect(lambda: self.sort_by('size'))
    a.sort_date.triggered.connect(lambda: self.sort_by('date'))
    a.sort_asc.triggered.connect(lambda: self.sort_by_order(Qt.AscendingOrder))
    a.sort_desc.triggered.connect(lambda: self.sort_by_order(Qt.DescendingOrder))

    # File ops
    a.rename.triggered.connect(self._on_rename)
    a.move_to_trash.triggered.connect(lambda: self._on_selection(self.trash.move_to_trash))
    a.restore.triggered.connect(lambda: self._on_selection(self.trash.restore))
    a.delete.triggered.connect(lambda: self._on_selection(self.trash.delete_permanently))
    a.empty_trash.triggered.connect(self.trash.empty_trash)
    a.create_file.triggered.connect(lambda: self.file_ops.create_file(self._current_path()))
    a.create_folder.triggered.connect(lambda: self.file_ops.create_folder(self._current_path()))
    a.copy_path.triggered.connect(lambda: QApplication.clipboard().setText(self._current_path()))
    a.copy.triggered.connect(lambda: self.file_ops.copy(self._current_selection()))
    a.cut.triggered.connect(lambda: self.file_ops.cut(self._current_selection()))
    a.paste.triggered.connect(lambda: self.file_ops.paste(self._current_path()))

    a.properties.triggered.connect(self._show_properties)
    a.open_terminal.triggered.connect(
      lambda: self.context_menu._open_terminal(self._current_path())
    )
    a.search.triggered.connect(self.toolbar._enter_search_mode)

  # ---------------------------------------------------------------------------
  # New window
  # ---------------------------------------------------------------------------

  def open_in_new_window(self, path):
    new_window = FileManager()
    new_window.navigate_to(path, add_to_history=False)
    new_window.show()
    self._windows.append(new_window)