import subprocess
import sys
from PySide6.QtWidgets import (
  QApplication, QHBoxLayout, QMainWindow, QSplitter, QListWidget, QListWidgetItem,
  QStackedWidget, QFileSystemModel, QTreeView, QListView, QStyle, QLineEdit, QToolButton, QLabel,
  QWidget, QHeaderView, QStyledItemDelegate, QMenu
)
from PySide6.QtCore import QDir, Qt, QSize
from core.path_logic import PathLinkedList
import os

class FileManager(QMainWindow):
  def __init__(self):
    super().__init__()
    self.setWindowTitle("QtFM")
    self.resize(1000, 600)

    # History Stack
    self.back_stack = []
    self.forward_stack = []

    # Model
    self.model = QFileSystemModel()
    self.model.setRootPath(QDir.rootPath())

    # Sidebar items
    sidebar_items = [
        ("Root", QDir.rootPath()),
        ("Home", QDir.homePath()),
        ("Desktop", QDir.homePath() + "/Desktop"),
        ("Documents", QDir.homePath() + "/Documents"),
        ("Downloads", QDir.homePath() + "/Downloads"),
        ("Music", QDir.homePath() + "/Music"),
        ("Pictures", QDir.homePath() + "/Pictures"),
        ("Videos", QDir.homePath() + "/Videos")
    ]

    # Sidebar
    self.sidebar = QListWidget()
    self.sidebar.setMaximumWidth(500)
    self.sidebar.setStyleSheet("""
      QListWidget {
        outline: none;
      }
      QListWidget::item {
        padding: 6px 8px;
      }
    """)
    for name, path in sidebar_items:
        self.add_sidebar_item(name, path)
    
    # Navigation logic
    self.sidebar.itemClicked.connect(self.navigate_from_sidebar)

    # Main view
    self.tree_view = QTreeView()
    self.grid_view = QListView()
    self.grid_view.setViewMode(QListView.IconMode)
    self.grid_view.setResizeMode(QListView.Adjust)

    for view in [self.tree_view, self.grid_view]:
      view.setModel(self.model)
      view.setRootIndex(self.model.index(QDir.homePath()))
      view.doubleClicked.connect(self.on_item_double_clicked)
      view.setContextMenuPolicy(Qt.CustomContextMenu)
      view.customContextMenuRequested.connect(self.show_context_menu)

    # Grid view appearance
    self.grid_view.setIconSize(QSize(72, 72))
    self.grid_view.setGridSize(QSize(140, 96))
    self.grid_view.setUniformItemSizes(True)
    self.grid_view.setWordWrap(False)

    # Stack & Splitter
    self.stack = QStackedWidget()
    self.stack.addWidget(self.tree_view)
    self.stack.addWidget(self.grid_view)
    self.stack.setCurrentIndex(1)

    splitter = QSplitter()
    splitter.addWidget(self.sidebar)
    splitter.addWidget(self.stack)
    splitter.setStretchFactor(1, 1)

    self.setCentralWidget(splitter)
    self.setup_toolbar()

    self.splitter = splitter
    self.splitter.setCollapsible(0, False)
    self.sidebar.setMinimumWidth(180)
    self.splitter.setSizes([200, 800])

    # Build initial view and breadcrumbs on startup
    self.navigate_to(QDir.homePath(), add_to_history=False)
  
    # Tree view: name column should stretch; other columns kept minimal
    self.tree_view.setIconSize(QSize(32, 32))
    self.tree_view.setUniformRowHeights(True)
    self.tree_view.setIndentation(20)

    # Hide "Type" column
    self.tree_view.hideColumn(2)

    # Column resizing
    header = self.tree_view.header()
    header.setSectionResizeMode(0, QHeaderView.Stretch) # Stretch "Name" column
    header.setSectionResizeMode(1, QHeaderView.ResizeToContents) # Size "Size" column to content
    header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # Size "Modified" column to content
    header.setStretchLastSection(False)

    # Delegate: elide text normally, show full text when the item is selected
    class ElideDelegate(QStyledItemDelegate):
      def paint(self, painter, option, index):
        opt = option
        self.initStyleOption(opt, index)
        if opt.state & QStyle.State_Selected:
          opt.textElideMode = Qt.ElideNone
        else:
          opt.textElideMode = Qt.ElideRight
        QStyledItemDelegate.paint(self, painter, opt, index)

    delegate = ElideDelegate(self)
    self.tree_view.setItemDelegate(delegate)
    self.grid_view.setItemDelegate(delegate)

  def show_context_menu(self, pos):
    view = self.sender()
    index = view.indexAt(pos)
    target_path = self.model.filePath(index) if index.isValid() else self.model.filePath(view.rootIndex())
    is_dir = self.model.isDir(index)

    menu = QMenu()
    menu.setStyleSheet("""
      QMenu {
        background-color: #141618;
        border: 1px solid #555;
        padding: 1px;
      }
      QMenu::item {
        padding: 4px 12px;
        background-color: transparent;  
      }
      QMenu::item:selected {
        background-color: #6c53a6;
        color: white;
      }
      QMenu::separator {
        height: 1px;
        background-color: #555;
        margin: 4px 0;
      }
    """)

    if index.isValid():
      # Actions for files/folders
      open_action = menu.addAction("Open")
      open_action.triggered.connect(lambda: self.on_item_double_clicked(index))

    # TODO: Create common actions like "Create New Folder", "Create New File", "Delete", "Rename" etc. and add them here
    new_file_action = menu.addAction("Create New File")
    new_folder_action = menu.addAction("Create New Folder")

    copy_path_action = menu.addAction("Copy Path")
    copy_path_action.triggered.connect(lambda: QApplication.clipboard().setText(target_path))

    if is_dir:
      # Seperator
      menu.addSeparator()

      term_action = menu.addAction("Open in Terminal")
      term_action.triggered.connect(lambda: subprocess.Popen(['konsole', '--workdir', target_path]))

    menu.exec(view.viewport().mapToGlobal(pos))

  def setup_toolbar(self):
    toolbar = self.addToolBar("Navigation")
    toolbar.setMovable(False)
    toolbar.setFloatable(False)

    # Home Button
    home_icon = self.style().standardIcon(QStyle.SP_DirHomeIcon)
    home_action = toolbar.addAction(home_icon, "")
    home_action.triggered.connect(lambda: self.navigate_to(QDir.homePath()))
    
    # Navigation Buttons
    back_icon = self.style().standardIcon(QStyle.SP_ArrowBack)
    self.back_action = toolbar.addAction(back_icon, "")
    self.back_action.triggered.connect(self.navigate_back)
    self.back_action.setEnabled(False)

    forward_icon = self.style().standardIcon(QStyle.SP_ArrowForward)
    self.forward_action = toolbar.addAction(forward_icon, "")
    self.forward_action.triggered.connect(self.navigate_forward)
    self.forward_action.setEnabled(False)

    # Toggle / View Button
    view_icon = self.style().standardIcon(QStyle.SP_FileDialogDetailedView)
    self.toggle_action = toolbar.addAction(view_icon, "Grid")
    self.toggle_action.triggered.connect(self.toggle_view)

    # Spacer
    spacer = QWidget()
    spacer.setFixedWidth(12)
    toolbar.addWidget(spacer)
    
    # Path container stack
    self.path_stack = QStackedWidget()
    self.path_stack.setFixedHeight(30)

    # Page 1: Breadcrumbs
    self.breadcrumb_widget = QWidget()
    self.breadcrumb_layout = QHBoxLayout()
    self.breadcrumb_layout.setContentsMargins(4, 0, 4, 0)
    self.breadcrumb_layout.setSpacing(4)
    self.breadcrumb_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    self.breadcrumb_widget.setLayout(self.breadcrumb_layout)
    self.breadcrumb_widget.setStyleSheet("""
      QWidget {
        background-color: #141618;
        border-radius: 4px;
      }
      QToolButton {
        color: #e0e0e0;
        background-color: transparent;
        border: none;
        border-radius: 3px;
        padding: 2px 6px;
        margin: 2px 0px;
        font-weight: 500;
      }
      QToolButton:hover {
        background-color: #32363a;
      }
      QToolButton:pressed {
        background-color: #454a4f;
      }
      QLabel {
        color: #666; /* The separator color */
        font-size: 16px;
      }
    """)

    # Page 2: Path Input
    self.path_edit = QLineEdit()
    self.path_edit.returnPressed.connect(self.on_path_edited)

    self.path_stack.addWidget(self.breadcrumb_widget)
    self.path_stack.addWidget(self.path_edit)

    toolbar.addWidget(self.path_stack)

    # Double click on breadcrumb area to edit
    self.breadcrumb_widget.mouseDoubleClickEvent = lambda e: self.enter_path_edit_mode()

  def update_nav_buttons(self):
    # Update the enabled state
    self.back_action.setEnabled(len(self.back_stack) > 0)
    self.forward_action.setEnabled(len(self.forward_stack) > 0)

  def update_breadcrumbs(self, path):
    while self.breadcrumb_layout.count():
      item = self.breadcrumb_layout.takeAt(0)
      if item.widget():
        item.widget().deleteLater()

    path_list = PathLinkedList(path)
    current = path_list.head

    while current:
      btn = QToolButton()
      btn.setText(current.name)
      btn.setCursor(Qt.PointingHandCursor)
      btn.clicked.connect(lambda checked=False, p=current.full_path: self.navigate_to(p))
      
      self.breadcrumb_layout.addWidget(btn)

      if current.next:
        sep = QLabel('\u203A') # Chevron symbol
        self.breadcrumb_layout.addWidget(sep)
      else:
        # Style the current (last) directory
        btn.setStyleSheet("font-weight: bold; color: #ffffff;")

      current = current.next

  def enter_path_edit_mode(self):
    current_path = self.model.filePath(self.tree_view.rootIndex())
    self.path_edit.setText(current_path)
    self.path_stack.setCurrentIndex(1)
    self.path_edit.setFocus()

  def on_path_edited(self):
    new_path = self.path_edit.text()
    if os.path.exists(new_path) and os.path.isdir(new_path):
      self.navigate_to(new_path)
      self.path_stack.setCurrentIndex(0)
    else:
      self.path_edit.setStyleSheet("border: 1px solid red;")

  def navigate_to(self, path, add_to_history=True, clear_forward_stack=True):
    index = self.model.index(path)
    if index.isValid():
      if add_to_history:
        current_path = self.model.filePath(self.tree_view.rootIndex())
        self.back_stack.append(current_path)
        if clear_forward_stack:
          self.forward_stack.clear()
      self.tree_view.setRootIndex(index)
      self.grid_view.setRootIndex(index)
      self.setWindowTitle(f"QtFM - {self.model.fileName(index)}")
      self.update_nav_buttons()
      self.sync_sidebar_selection(path)
      self.update_breadcrumbs(path)
      self.path_stack.setCurrentIndex(0)
  
  def navigate_forward(self):
    if self.forward_stack:
      next_path = self.forward_stack.pop()
      current_path = self.model.filePath(self.tree_view.rootIndex())
      self.back_stack.append(current_path)
      self.navigate_to(next_path, add_to_history=False, clear_forward_stack=False)

  def navigate_back(self):
    if self.back_stack:
      last_path = self.back_stack.pop()
      current_path = self.model.filePath(self.tree_view.rootIndex())
      self.forward_stack.append(current_path)
      self.navigate_to(last_path, add_to_history=False, clear_forward_stack=False)

  def toggle_view(self):
    if self.stack.currentIndex() == 0:
      self.stack.setCurrentIndex(1)
      self.toggle_action.setText("Tree View")
    else:
      self.stack.setCurrentIndex(0)
      self.toggle_action.setText("Grid View")

  def sync_sidebar_selection(self, path):
    self.sidebar.blockSignals(True)
    self.sidebar.clearSelection()
    for i in range(self.sidebar.count()):
      item = self.sidebar.item(i)
      if item.data(Qt.UserRole) == path:
        item.setSelected(True)
        self.sidebar.setCurrentItem(item)
        break
    self.sidebar.blockSignals(False)

  def navigate_from_sidebar(self, item):
    self.navigate_to(item.data(Qt.UserRole))

  def on_item_double_clicked(self, index):
    if self.model.isDir(index):
      self.navigate_to(self.model.filePath(index))

  def add_sidebar_item(self, name, path):
    item = QListWidgetItem(name)
    item.setData(Qt.UserRole, path)
    item.setIcon(self.model.fileIcon(self.model.index(path)))
    self.sidebar.addItem(item)

if __name__ == "__main__":
  app = QApplication(sys.argv)
  window = FileManager()
  window.show()
  sys.exit(app.exec())