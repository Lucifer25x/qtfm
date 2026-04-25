import subprocess
from PySide6.QtWidgets import QMenu
from pathlib import Path
import shutil
import os

class ContextMenuBuilder:
  def __init__(self, model, trash_path):
    self.model      = model
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

  def build(self, view, pos, actions):
    index       = view.indexAt(pos)
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
        menu.addAction(actions.restore)
        menu.addAction(actions.delete)
      else:
        # TODO: Restore all
        menu.addAction(actions.empty_trash)
        menu.addSeparator()

    else:
      if is_dir:
        menu.addAction(actions.create_file)
        menu.addAction(actions.create_folder)
        menu.addSeparator()

        if index.isValid():
          menu.addAction(actions.open)
          menu.addAction(actions.open_new_win)

        # menu.addAction(actions.open_terminal)
        term_action = menu.addAction("Open Terminal Here")
        term_action.triggered.connect(lambda: self._open_terminal(target_path))
        menu.addSeparator()

      if index.isValid():
        menu.addAction(actions.rename)
        menu.addSeparator()
        menu.addAction(actions.cut)
        menu.addAction(actions.copy)
        menu.addAction(actions.paste)
        menu.addSeparator()
        menu.addAction(actions.move_to_trash)

      menu.addAction(actions.copy_path)

      if is_dir or not index.isValid():
        menu.addSeparator()
        arrange = menu.addMenu("Arrange Items")
        arrange.addAction(actions.sort_name)
        arrange.addAction(actions.sort_size)
        arrange.addAction(actions.sort_date)
        arrange.addSeparator()
        arrange.addAction(actions.sort_asc)
        arrange.addAction(actions.sort_desc)
        menu.addSeparator()
        zoom = menu.addMenu("Zoom")
        zoom.addAction(actions.zoom_in)
        zoom.addAction(actions.zoom_out)
        zoom.addAction(actions.zoom_reset)

      menu.addSeparator()
      menu.addAction(actions.properties)

    menu.exec(view.viewport().mapToGlobal(pos))