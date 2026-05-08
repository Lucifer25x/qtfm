from PySide6.QtWidgets import QInputDialog, QMessageBox
import os
import shutil

class FileOps:
  def __init__(self, parent_widget):
    self.parent = parent_widget
    self.clipboard = []
    self.operation = None

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

  def copy(self, paths: list[str]):
    self.clipboard = paths[:]
    self.operation = "copy"

  def cut(self, paths: list[str]):
    self.clipboard = paths[:]
    self.operation = "cut"

  # TODO: Maybe use QProgressDialog
  def paste(self, target_path: str):
    # FIXME: Target shows the current directory
    # FIXME: Can't see paste option inside folder (can see for selection)
    print(f"Pasting {self.clipboard} to {target_path} with operation {self.operation}")
    if not self.clipboard or not self.operation:
      return
    for src in self.clipboard:
      base_name = os.path.basename(src)
      dst = os.path.join(target_path, base_name)

      if src == dst:
        continue
      if os.path.commonpath([src, dst]) == src:
        QMessageBox.warning(self.parent, "Error", f"Cannot paste '{base_name}' into itself or its subdirectory.")
        continue

      # TODO: Maybe add option to replace or add suffix if exists
      if os.path.exists(dst):
        QMessageBox.warning(self.parent, "Error", f"'{base_name}' already exists in the target location.")
        continue
      try:
        if self.operation == "copy":
          if os.path.isdir(src):
            shutil.copytree(src, dst)
          else:
            shutil.copy2(src, dst)
        elif self.operation == "cut":
          shutil.move(src, dst)
      except Exception as e:
        QMessageBox.critical(self.parent, "Error", f"Failed to paste '{base_name}': {str(e)}")
    if self.operation == "cut":
      self.clipboard.clear()
      self.operation = None