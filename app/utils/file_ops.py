from PySide6.QtWidgets import QInputDialog, QMessageBox
import os
import shutil

class FileOps:
  def __init__(self, parent_widget):
    self.parent    = parent_widget
    self.clipboard = []
    self.operation = None  # 'copy' or 'cut'

  # ---------------------------------------------------------------------------
  # Create
  # ---------------------------------------------------------------------------

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

  # ---------------------------------------------------------------------------
  # Rename
  # ---------------------------------------------------------------------------

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

  # ---------------------------------------------------------------------------
  # Clipboard
  # ---------------------------------------------------------------------------

  def copy(self, paths: list[str]):
    if not paths:
      return
    self.clipboard = paths[:]
    self.operation = 'copy'

  def cut(self, paths: list[str]):
    if not paths:
      return
    self.clipboard = paths[:]
    self.operation = 'cut'

  def has_clipboard(self) -> bool:
    return bool(self.clipboard) and self.operation is not None

  # ---------------------------------------------------------------------------
  # Paste
  # ---------------------------------------------------------------------------

  def paste(self, target_path: str):
    """
    Pastes clipboard contents into target_path.
    target_path must be a directory. If it's a file, we paste into its parent.
    """
    if not self.has_clipboard():
      return

    # Always paste into a directory
    if not os.path.isdir(target_path):
      target_path = os.path.dirname(target_path)

    errors = []
    pasted = []

    for src in self.clipboard:
      if not os.path.exists(src):
        errors.append(f"'{os.path.basename(src)}' no longer exists.")
        continue

      base_name = os.path.basename(src)
      dst       = os.path.join(target_path, base_name)

      # Skip if source and destination are the same
      if os.path.abspath(src) == os.path.abspath(dst):
        if self.operation == 'copy':
          # Copying into same folder — generate unique name
          dst = self._unique_name(target_path, base_name)
        else:
          continue

      # Prevent pasting a folder into itself or a subfolder
      if os.path.isdir(src):
        try:
          if os.path.commonpath([os.path.abspath(src), os.path.abspath(dst)]) == os.path.abspath(src):
            errors.append(f"Cannot paste '{base_name}' into itself.")
            continue
        except ValueError:
          pass

      if os.path.exists(dst):
        reply = QMessageBox.question(
          self.parent, "File Exists",
          f"A file named '{base_name}' already exists in the destination. Do you want to replace it?",
          QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
          QMessageBox.Cancel
        )
        # Yes = Replace, No = Keep both (unique name), Cancel = skip
        if reply == QMessageBox.Cancel:
          continue
        elif reply == QMessageBox.No:
          dst = self._unique_name(target_path, base_name)
        else:
          # Replace — remove existing first
          try:
            shutil.rmtree(dst) if os.path.isdir(dst) else os.remove(dst)
          except Exception as e:
            errors.append(f"Could not replace '{base_name}': {str(e)}")
            continue

      try:
        if self.operation == 'copy':
          if os.path.isdir(src):
            shutil.copytree(src, dst)
          else:
            shutil.copy2(src, dst)
        elif self.operation == 'cut':
          shutil.move(src, dst)
        pasted.append(src)
      except Exception as e:
        errors.append(f"Failed to paste '{base_name}': {str(e)}")

    # After cut, clear only successfully moved items
    if self.operation == 'cut':
      self.clipboard = [p for p in self.clipboard if p not in pasted]
      if not self.clipboard:
        self.operation = None

    if errors:
      QMessageBox.warning(
        self.parent, "Paste Errors",
        "\n".join(errors)
      )

  # ---------------------------------------------------------------------------
  # Helpers
  # ---------------------------------------------------------------------------

  def _unique_name(self, folder: str, name: str) -> str:
    """Generates a unique filename like 'file (copy).txt', 'file (copy 2).txt'."""
    base, ext = os.path.splitext(name)
    candidate = os.path.join(folder, f"{base} (copy){ext}")
    counter   = 2
    while os.path.exists(candidate):
      candidate = os.path.join(folder, f"{base} (copy {counter}){ext}")
      counter  += 1
    return candidate