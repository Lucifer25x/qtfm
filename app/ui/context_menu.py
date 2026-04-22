import subprocess
from PySide6.QtWidgets import QMenu, QApplication
from pathlib import Path
import shutil
import os

class ContextMenuBuilder:
  def __init__(self, model, trash_path):
    self.model = model
    self.trash_path = trash_path

  def _open_terminal(self, path: str):
    for term in [
      os.environ.get('TERMINAL'),
      'konsole', 'xfce4-terminal', 'gnome-terminal', 'xterm'
    ]:
      if term and shutil.which(term):
        args = ['--workdir', path]
        if term == 'gnome-terminal':
          args = ['--working-directory', path]
        subprocess.Popen([term] + args)
        return

  # TODO: Have sort etc. in context menu
  def build(self, view, pos, callbacks):
    """
    callbacks is a plain dict of action handlers passed in from FileManager:
    {
      'open':            fn(index),
      'open_new_window': fn(path),
      'move_to_trash':   fn(path),
      'restore':         fn(path),
      'delete':          fn(path),
      'empty_trash':     fn(),
      'create_file':     fn(path),
      'create_folder':   fn(path),
      'rename':          fn(path)
    }
    """
    index = view.indexAt(pos)
    target_path = (
      self.model.filePath(index)
      if index.isValid()
      else self.model.filePath(view.rootIndex())
    )
    is_dir = self.model.isDir(index)

    resolved_target = Path(target_path).resolve()
    resolved_trash  = Path(self.trash_path).resolve()
    in_trash        = resolved_target.is_relative_to(resolved_trash)
    viewing_trash   = in_trash or resolved_target == resolved_trash

    menu = QMenu()
    
    if viewing_trash:
      if index.isValid():
        restore_action = menu.addAction("Restore from Trash")
        restore_action.triggered.connect(lambda: callbacks['restore'](target_path))

        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(lambda: callbacks['delete'](target_path))
      else:
        # TODO: Restore all
        empty_action = menu.addAction("Empty Trash")
        empty_action.triggered.connect(lambda: callbacks['empty_trash']())
        menu.addSeparator()
    else:
      if is_dir:
        new_file_action = menu.addAction("Create New File")
        new_file_action.triggered.connect(lambda: callbacks['create_file'](target_path)) 
        new_folder_action = menu.addAction("Create New Folder")
        new_folder_action.triggered.connect(lambda: callbacks['create_folder'](target_path))

        menu.addSeparator()
        if index.isValid():
          open_action = menu.addAction("Open")
          open_action.triggered.connect(lambda: callbacks['open'](index))

          new_window_action = menu.addAction("Open in New Window")
          new_window_action.triggered.connect(
            lambda: callbacks['open_new_window'](target_path)
          )
        term_action = menu.addAction("Open in Terminal")
        term_action.triggered.connect(lambda: self._open_terminal(target_path))
        menu.addSeparator()
      if index.isValid():
        rename_action = menu.addAction("Rename")
        rename_action.triggered.connect(lambda: callbacks['rename'](target_path))

        trash_action = menu.addAction("Move to Trash")
        trash_action.triggered.connect(lambda: callbacks['move_to_trash'](target_path))

      copy_path_action = menu.addAction("Copy Path")
      copy_path_action.triggered.connect(
        lambda: QApplication.clipboard().setText(target_path)
      )

    menu.exec(view.viewport().mapToGlobal(pos))