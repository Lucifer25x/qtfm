from PySide6.QtWidgets import (
  QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
  QLabel, QGridLayout, QDialogButtonBox, QSizePolicy, QFrame
)
from PySide6.QtCore import Qt, QDateTime, QThread, Signal
import os
import stat


class SizeWorker(QThread):
  result = Signal(float)

  def __init__(self, path):
    super().__init__()
    self.path = path

  def run(self):
    if not os.path.isdir(self.path):
      self.result.emit(float(os.lstat(self.path).st_size))
      return

    total = 0
    for dirpath, dirs, files in os.walk(self.path):
      for name in files + dirs + [dirpath]:
        try:
          total += os.lstat(os.path.join(dirpath, name)).st_blocks * 512
        except (FileNotFoundError, PermissionError, OSError):
          continue
    self.result.emit(float(total))


def human_size(size: float) -> str:
  for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
    if size < 1024 or unit == 'TB':
      return f"{size:.2f} {unit}"
    size /= 1024


def fmt_time(ts: float) -> str:
  return QDateTime.fromSecsSinceEpoch(int(ts)).toString("yyyy-MM-dd  hh:mm:ss")


class PropertiesDialog(QDialog):
  def __init__(self, path: str, model, parent=None):
    super().__init__(parent)
    self.path  = path
    self.model = model
    self.setWindowTitle(f"Properties — {os.path.basename(path)}")
    self.setMinimumWidth(420)
    self.setMinimumHeight(340)
    self._worker = None
    self._build()

  def _build(self):
    layout = QVBoxLayout()
    layout.setSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)

    # --- Header ---
    header = QWidget()
    header.setObjectName("prop_header")
    header_layout = QHBoxLayout()
    header_layout.setContentsMargins(16, 14, 16, 14)
    header_layout.setSpacing(14)

    icon_label = QLabel()
    icon = self.model.fileIcon(self.model.index(self.path))
    icon_label.setPixmap(icon.pixmap(48, 48))
    icon_label.setFixedSize(48, 48)

    name_label = QLabel(os.path.basename(self.path))
    name_label.setStyleSheet("font-size: 15px; font-weight: 600;")
    name_label.setWordWrap(True)

    header_layout.addWidget(icon_label)
    header_layout.addWidget(name_label, 1)
    header.setLayout(header_layout)

    # Divider
    divider = QFrame()
    divider.setFrameShape(QFrame.HLine)
    divider.setFrameShadow(QFrame.Sunken)

    # --- Tabs ---
    tabs = QTabWidget()
    tabs.setDocumentMode(True)
    tabs.addTab(self._general_tab(), "General")
    tabs.addTab(self._permissions_tab(), "Permissions")

    # --- Buttons ---
    buttons = QDialogButtonBox(QDialogButtonBox.Ok)
    buttons.setContentsMargins(12, 8, 12, 12)
    buttons.accepted.connect(self.accept)

    layout.addWidget(header)
    layout.addWidget(divider)
    layout.addWidget(tabs, 1)
    layout.addWidget(buttons)
    self.setLayout(layout)

  def _row(self, grid, row, label, value):
    lbl = QLabel(label)
    lbl.setStyleSheet("font-size: 12px; font-weight: 600;")
    lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

    val = QLabel(str(value))
    val.setTextInteractionFlags(Qt.TextSelectableByMouse)
    val.setWordWrap(True)
    val.setStyleSheet("font-size: 12px;")

    grid.addWidget(lbl, row, 0)
    grid.addWidget(val, row, 1)

  def _general_tab(self):
    widget = QWidget()
    grid   = QGridLayout()
    grid.setContentsMargins(16, 16, 16, 16)
    grid.setHorizontalSpacing(16)
    grid.setVerticalSpacing(10)
    grid.setColumnStretch(1, 1)
    grid.setColumnMinimumWidth(0, 90)

    stats    = os.stat(self.path)
    is_dir   = os.path.isdir(self.path)
    mimetype = "Folder" if is_dir else self._mime_type()

    self._row(grid, 0, "Type",     mimetype)
    self._row(grid, 1, "Location", os.path.dirname(self.path))
    self._row(grid, 2, "Modified", fmt_time(stats.st_mtime))
    self._row(grid, 3, "Accessed", fmt_time(stats.st_atime))
    self._row(grid, 4, "Created",  fmt_time(stats.st_ctime))

    # Size row
    self._size_label = QLabel("Computing…" if is_dir else human_size(stats.st_size))
    self._size_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
    size_lbl = QLabel("Size")
    size_lbl.setStyleSheet("font-size: 12px; font-weight: 600;")
    size_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    grid.addWidget(size_lbl,        5, 0)
    grid.addWidget(self._size_label, 5, 1)

    if is_dir:
      self._worker = SizeWorker(self.path)
      self._worker.result.connect(
        lambda n: self._size_label.setText(human_size(n))
      )
      self._worker.start()

    grid.setRowStretch(6, 1)
    widget.setLayout(grid)
    return widget

  def _permissions_tab(self):
    widget = QWidget()
    grid   = QGridLayout()
    grid.setContentsMargins(16, 16, 16, 16)
    grid.setHorizontalSpacing(16)
    grid.setVerticalSpacing(10)
    grid.setColumnStretch(1, 1)
    grid.setColumnMinimumWidth(0, 90)

    mode  = os.stat(self.path).st_mode
    owner = self._owner()

    self._row(grid, 0, "Owner",  owner)
    self._row(grid, 1, "Octal", str(oct(stat.S_IMODE(mode)))[2:])
    self._row(grid, 2, "Owner",  self._perm_str(mode, stat.S_IRUSR, stat.S_IWUSR, stat.S_IXUSR))
    self._row(grid, 3, "Group",  self._perm_str(mode, stat.S_IRGRP, stat.S_IWGRP, stat.S_IXGRP))
    self._row(grid, 4, "Others", self._perm_str(mode, stat.S_IROTH, stat.S_IWOTH, stat.S_IXOTH))

    grid.setRowStretch(5, 1)
    widget.setLayout(grid)
    return widget

  def _perm_str(self, mode, r, w, x) -> str:
    parts = []
    if mode & r: parts.append("Read")
    if mode & w: parts.append("Write")
    if mode & x: parts.append("Execute")
    return ", ".join(parts) if parts else "None"

  def _owner(self) -> str:
    try:
      import pwd
      return pwd.getpwuid(os.stat(self.path).st_uid).pw_name
    except Exception:
      return str(os.stat(self.path).st_uid)

  def _mime_type(self) -> str:
    import mimetypes
    mime, _ = mimetypes.guess_type(self.path)
    return mime or "Unknown"

  def closeEvent(self, event):
    if self._worker and self._worker.isRunning():
      self._worker.terminate()
      self._worker.wait()
    super().closeEvent(event)