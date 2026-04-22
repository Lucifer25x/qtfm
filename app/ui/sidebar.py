from PySide6.QtWidgets import QListWidget, QListWidgetItem, QWidget
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication, QStyle
import os

class SidebarWidget(QListWidget):
	def __init__(self, model, parent=None):
		super().__init__(parent)
		self.model = model
		self.palette = QApplication.palette()

		self.setMaximumWidth(400)
		self.setMinimumWidth(140)
		self.setStyleSheet("""
			QListWidget {
				outline: none;
				border: none;
			}
			QListWidget:hover {
				border: none;
			}
			QListWidget::item {
				padding: 6px 8px;
			}
		""")

	def populate(self, items):
		"""items: list of (name, path). (None, None) - separator"""
		for name, path in items:
			if not name and not path:
				self._add_separator()
			else:
				self.add_item(name, path)

	def _add_separator(self):
		separator = QListWidgetItem()
		separator.setFlags(Qt.NoItemFlags)
		separator.setSizeHint(QSize(0, 10))
		self.addItem(separator)

		line = QWidget()
		line.setFixedHeight(1)
		line.setStyleSheet(
			f"background-color: {self.palette.color(QPalette.Mid).name()};"
		)
		self.setItemWidget(separator, line)

	def add_item(self, name, path):
		if not os.path.exists(path):
			return
		item = QListWidgetItem(name)
		item.setIcon(self._resolve_icon(name, path))
		item.setData(Qt.UserRole, path)
		self.addItem(item)

	def _resolve_icon(self, name, path):
		style = QApplication.style()
		match name.lower():
			case "home":
				return style.standardIcon(QStyle.SP_DirHomeIcon)
			case "root":
				return style.standardIcon(QStyle.SP_ComputerIcon)
			case "trash":
				return style.standardIcon(QStyle.SP_TrashIcon)
			case _:
				return self.model.fileIcon(self.model.index(path))

	def sync_selection(self, path):
		self.blockSignals(True)
		self.clearSelection()
		for i in range(self.count()):
			item = self.item(i)
			if item.data(Qt.UserRole) == path:
				item.setSelected(True)
				self.setCurrentItem(item)
				break
		self.blockSignals(False)
