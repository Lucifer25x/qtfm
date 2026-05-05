from PySide6.QtWidgets import QMenuBar, QMessageBox
from PySide6.QtCore import Qt

class AppMenuBar(QMenuBar):
  def __init__(self, actions, parent=None):
    super().__init__(parent)
    self._build(actions)

  def _build(self, a):
    # File
    file_menu = self.addMenu("File")
    file_menu.addAction(a.create_file)
    file_menu.addAction(a.create_folder)
    file_menu.addSeparator()
    file_menu.addAction(a.rename)
    file_menu.addAction(a.copy_path)
    file_menu.addSeparator()
    file_menu.addAction(a.move_to_trash)
    file_menu.addAction(a.empty_trash)
    file_menu.addAction(a.delete)
    file_menu.addSeparator()
    file_menu.addAction(a.properties)

    # Edit
    edit_menu = self.addMenu("Edit")
    edit_menu.addAction(a.cut)
    edit_menu.addAction(a.copy)
    edit_menu.addAction(a.paste)

    # View
    view_menu = self.addMenu("View")
    view_menu.addAction(a.view_grid)
    view_menu.addAction(a.view_tree)
    view_menu.addSeparator()
    view_menu.addAction(a.show_hidden)
    view_menu.addSeparator()
    arrange = view_menu.addMenu("Arrange Items")
    arrange.addAction(a.sort_name)
    arrange.addAction(a.sort_size)
    arrange.addAction(a.sort_date)
    arrange.addSeparator()
    arrange.addAction(a.sort_asc)
    arrange.addAction(a.sort_desc)
    view_menu.addSeparator()
    view_menu.addAction(a.zoom_in)
    view_menu.addAction(a.zoom_out)
    view_menu.addAction(a.zoom_reset)
    view_menu.addSeparator()
    view_menu.addAction(a.search)

    # Go
    go_menu = self.addMenu("Go")
    go_menu.addAction(a.go_home)
    go_menu.addAction(a.go_up)
    go_menu.addAction(a.go_back)
    go_menu.addAction(a.go_forward)
    go_menu.addSeparator()
    go_menu.addAction(a.open_terminal)

    # Help — placeholder for now
    help_menu = self.addMenu("Help")
    about = help_menu.addAction("About QtFM")
    about.triggered.connect(self._show_about)

  def _show_about(self):
    box = QMessageBox(self.parent())
    box.setWindowTitle("About QtFM")
    box.setText("<b>QtFM</b>")
    box.setInformativeText(
      "A lightweight file manager built with Python and PySide6.<br><br>"
      "Written as a university project, featuring algorithms and "
      "data structures.<br><br>"
      "<small>Built with PySide6 &amp; Qt</small>"
    )
    box.setIcon(QMessageBox.Information)
    box.setStandardButtons(QMessageBox.Ok)
    box.exec()