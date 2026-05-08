from PySide6.QtWidgets import QFileIconProvider
from PySide6.QtCore import QFileInfo
from PySide6.QtGui import QIcon

class FileIconProvider(QFileIconProvider):
  def icon(self, arg):
    icon = super().icon(arg)

    if isinstance(arg, QFileInfo):
      if icon.isNull():
        if arg.isDir():
          return QIcon.fromTheme("folder")
        fallback = QIcon.fromTheme("text-plain")
        if fallback.isNull():
          fallback = QIcon.fromTheme("text-x-generic")
        return fallback

    return icon
