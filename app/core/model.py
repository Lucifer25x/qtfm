from PySide6.QtWidgets import QFileSystemModel
from PySide6.QtCore import QDir
from app.utils.icon_provider import FileIconProvider

class FileModel(QFileSystemModel):
  def __init__(self, parent=None):
    super().__init__(parent)
    self.setRootPath(QDir.rootPath())
    self._show_hidden = True
    self._apply_filter()
    self.setIconProvider(FileIconProvider())

  def _apply_filter(self):
    base = QDir.AllEntries | QDir.NoDotAndDotDot | QDir.System
    if self._show_hidden:
      base |= QDir.Hidden
    self.setFilter(base)

  def set_show_hidden(self, show: bool):
    """Toggle hidden files/dirs. Wires up to a menu action or setting later."""
    self._show_hidden = show
    self._apply_filter()