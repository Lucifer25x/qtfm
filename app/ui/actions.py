from PySide6.QtGui import QAction, QKeySequence, QActionGroup
from PySide6.QtWidgets import QApplication, QStyle


class ActionRegistry:
  def __init__(self, parent):
    self.parent = parent
    self._build()

  def _action(self, label, icon=None, shortcut=None, checkable=False):
    act = QAction(label, self.parent)
    if icon:
      act.setIcon(QApplication.style().standardIcon(icon))
    if shortcut:
      act.setShortcut(QKeySequence(shortcut))
    if checkable:
      act.setCheckable(True)
    return act

  def _build(self):
    # --- Navigation ---
    self.go_home    = self._action("Home",          QStyle.SP_DirHomeIcon,  "Alt+Home")
    self.go_up      = self._action("Parent Folder", QStyle.SP_ArrowUp,      "Alt+Up")
    self.go_back    = self._action("Back",          QStyle.SP_ArrowBack,    "Alt+Left")
    self.go_forward = self._action("Forward",       QStyle.SP_ArrowForward, "Alt+Right")

    # --- View ---
    self.view_grid = self._action("Grid View", checkable=True)
    self.view_tree = self._action("Tree View", checkable=True)
    self.view_grid.setChecked(True)

    self.view_group = QActionGroup(self.parent)
    self.view_group.setExclusive(True)
    self.view_group.addAction(self.view_grid)
    self.view_group.addAction(self.view_tree)

    self.zoom_in     = self._action("Zoom In",           QStyle.SP_ArrowUp,   "Ctrl+=")
    self.zoom_out    = self._action("Zoom Out",          QStyle.SP_ArrowDown, "Ctrl+-")
    self.zoom_reset  = self._action("Normal Size",       None,                "Ctrl+0")
    self.show_hidden = self._action("Show Hidden Files", None,                "Ctrl+H", checkable=True)
    self.show_hidden.setChecked(True)

    # --- Sort ---
    self.sort_group = QActionGroup(self.parent)
    self.sort_group.setExclusive(True)

    self.sort_name = self._action("By Name", checkable=True)
    self.sort_size = self._action("By Size", checkable=True)
    self.sort_date = self._action("By Date", checkable=True)
    self.sort_name.setChecked(True)

    for a in [self.sort_name, self.sort_size, self.sort_date]:
      self.sort_group.addAction(a)

    self.sort_asc  = self._action("Ascending",  checkable=True)
    self.sort_desc = self._action("Descending", checkable=True)
    self.sort_asc.setChecked(True)

    self.order_group = QActionGroup(self.parent)
    self.order_group.setExclusive(True)
    self.order_group.addAction(self.sort_asc)
    self.order_group.addAction(self.sort_desc)

    # --- File operations ---
    self.open          = self._action("Open")
    self.open_new_win  = self._action("Open in New Window", QStyle.SP_ArrowRight)
    self.cut           = self._action("Cut",                None, "Ctrl+X")
    self.copy          = self._action("Copy",               None, "Ctrl+C")
    self.paste         = self._action("Paste",              None, "Ctrl+V")
    self.rename        = self._action("Rename",             None,                "F2")
    self.move_to_trash = self._action("Move to Trash",      QStyle.SP_TrashIcon, "Delete")
    self.restore       = self._action("Restore from Trash")
    self.delete        = self._action("Delete",             None,                "Shift+Delete")
    self.empty_trash   = self._action("Empty Trash",        QStyle.SP_TrashIcon)
    self.create_file   = self._action("Create New File",    QStyle.SP_FileIcon)
    self.create_folder = self._action("Create New Folder",  QStyle.SP_DirIcon)
    self.copy_path     = self._action("Copy Path")
    self.properties    = self._action("Properties",         None, "Alt+Return")
    self.compress_huffman = self._action("Compress with Huffman", None)
    self.decompress_huffman = self._action("Decompress with Huffman", None)

    # --- Search ---
    self.search = self._action("Search", None, "Ctrl+F")

    self.search_bfs = self._action("BFS — Breadth First", checkable=True)
    self.search_dfs = self._action("DFS — Depth First",   checkable=True)
    self.search_bfs.setChecked(True)

    self.search_strategy_group = QActionGroup(self.parent)
    self.search_strategy_group.setExclusive(True)
    self.search_strategy_group.addAction(self.search_bfs)
    self.search_strategy_group.addAction(self.search_dfs)

    self.search_here = self._action("Search in Current Folder", checkable=True)
    self.search_fs   = self._action("Search in File System",    checkable=True)
    self.search_here.setChecked(True)

    self.search_scope_group = QActionGroup(self.parent)
    self.search_scope_group.setExclusive(True)
    self.search_scope_group.addAction(self.search_here)
    self.search_scope_group.addAction(self.search_fs)

    # --- Terminal ---
    self.open_terminal = self._action("Open Terminal Here", QStyle.SP_ComputerIcon)