from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QDir
from send2trash import send2trash
from pathlib import Path
from urllib.parse import unquote
import shutil
import os


class TrashManager:
  def __init__(self, parent_widget):
    self.parent     = parent_widget
    self.trash_path = QDir.homePath() + "/.local/share/Trash/files"
    self._info_dir  = QDir.homePath() + "/.local/share/Trash/info"

  def is_in_trash(self, path: str) -> bool:
    return Path(path).resolve().is_relative_to(Path(self.trash_path).resolve())

  def _trashinfo_path(self, name: str) -> str:
    """Returns the expected .trashinfo path for a given filename."""
    return os.path.join(self._info_dir, name + ".trashinfo")

  def _read_original_path(self, trashinfo_path: str) -> str | None:
    try:
      with open(trashinfo_path, 'r') as f:
        for line in f:
          if line.startswith("Path="):
            raw = line[5:].strip()
            # Percent-decode (e.g. %20 → space, %C3%A9 → é)
            decoded = unquote(raw)
            if not os.path.isabs(decoded):
              decoded = os.path.join(QDir.homePath(), decoded)
            return decoded
    except OSError:
      pass
    return None

  def _remove_trashinfo(self, name: str):
    """Removes the .trashinfo file for a given filename if it exists."""
    info_path = self._trashinfo_path(name)
    if os.path.exists(info_path):
      os.remove(info_path)

  def _confirm(self, title: str, message: str) -> bool:
    reply = QMessageBox.question(
      self.parent, title, message,
      QMessageBox.Yes | QMessageBox.No
    )
    return reply == QMessageBox.Yes

  def move_to_trash(self, path: str):
    if not self._confirm(
      "Confirm Move to Trash",
      f"Move '{os.path.basename(path)}' to the trash?"
    ):
      return
    send2trash(path)

  def restore(self, path: str):
    name          = os.path.basename(path)
    info_path     = self._trashinfo_path(name)
    original_path = self._read_original_path(info_path)

    if not original_path:
      # Fallback: reconstruct from trash path structure
      original_path = os.path.join(
        QDir.homePath(), os.path.relpath(path, self.trash_path)
      )

    if os.path.exists(original_path):
      QMessageBox.warning(
        self.parent, "Restore Failed",
        f"'{os.path.basename(original_path)}' already exists in the original location."
      )
      return

    try:
      os.makedirs(os.path.dirname(original_path), exist_ok=True)
      os.rename(path, original_path)
      self._remove_trashinfo(name)
      QMessageBox.information(
        self.parent, "Restored",
        f"'{name}' has been restored to '{original_path}'."
      )
    except Exception as e:
      QMessageBox.critical(self.parent, "Error", f"Failed to restore: {str(e)}")

  def delete_permanently(self, path: str):
    name = os.path.basename(path)

    if os.path.isdir(path):
      n = sum(len(files) + len(dirs) for _, dirs, files in os.walk(path))
      msg = (
        f"'{name}' contains {n} item(s). Permanently delete everything?"
        if n > 0
        else f"Permanently delete '{name}'?"
      )
    else:
      msg = f"Permanently delete '{name}'? This cannot be undone."

    if not self._confirm("Confirm Permanent Deletion", msg):
      return

    try:
      shutil.rmtree(path) if os.path.isdir(path) else os.remove(path)
      self._remove_trashinfo(name)
      QMessageBox.information(
        self.parent, "Deleted",
        f"'{name}' has been permanently deleted."
      )
    except Exception as e:
      QMessageBox.critical(self.parent, "Error", f"Failed to delete: {str(e)}")

  def empty_trash(self):
    if not os.path.exists(self.trash_path) or not os.listdir(self.trash_path):
      QMessageBox.information(self.parent, "Trash", "Trash is already empty.")
      return

    entries = os.listdir(self.trash_path)
    n = len(entries)

    if not self._confirm(
      "Empty Trash",
      f"Permanently delete all {n} item(s) in the trash? This cannot be undone."
    ):
      return

    try:
      # Delete each entry individually and its matching .trashinfo
      # Avoids nuking unrelated entries from other mount points
      for name in entries:
        entry_path = os.path.join(self.trash_path, name)
        shutil.rmtree(entry_path) if os.path.isdir(entry_path) else os.remove(entry_path)
        self._remove_trashinfo(name)

      QMessageBox.information(self.parent, "Trash", f"{n} item(s) permanently deleted.")
    except Exception as e:
      QMessageBox.critical(self.parent, "Error", f"Failed to empty trash: {str(e)}")