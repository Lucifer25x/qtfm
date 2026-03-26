from PySide6.QtWidgets import QInputDialog, QMessageBox
import os

class FileOps:
  def __init__(self, parent_widget):
    self.parent = parent_widget

  def create_file(self, target_path: str):
    file_name, ok = QInputDialog.getText(self.parent, "Create New File", "Enter file name:")
    if not ok or not file_name:
      return
    new_path = os.path.join(target_path, file_name)
    if os.path.exists(new_path):
      QMessageBox.warning(self.parent, "Error", "A file with that name already exists.")
      return
    with open(new_path, 'w'):
      pass

  def create_folder(self, target_path: str):
    folder_name, ok = QInputDialog.getText(self.parent, "Create New Folder", "Enter folder name:")
    if not ok or not folder_name:
      return
    new_path = os.path.join(target_path, folder_name)
    if os.path.exists(new_path):
      QMessageBox.warning(self.parent, "Error", "A folder with that name already exists.")
      return
    os.makedirs(new_path)

  def rename(self, path: str):
    old_name = os.path.basename(path)
    new_name, ok = QInputDialog.getText(
      self.parent, "Rename", "Enter new name:", text=old_name
    )
    if not ok or not new_name or new_name == old_name:
      return
    new_path = os.path.join(os.path.dirname(path), new_name)
    if os.path.exists(new_path):
      QMessageBox.warning(self.parent, "Error", "A file with that name already exists.")
      return
    try:
      os.rename(path, new_path)
    except Exception as e:
      QMessageBox.critical(self.parent, "Error", f"Failed to rename: {str(e)}")