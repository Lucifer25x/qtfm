from PySide6.QtCore import QThread, Signal
from .search import bfs, dfs


class SearchWorker(QThread):
  result_found = Signal(str)
  finished     = Signal()

  def __init__(self, root: str, query: str, use_bfs: bool = True):
    super().__init__()
    self.root    = root
    self.query   = query.lower()
    self.use_bfs = use_bfs
    self._stopped = False

  def run(self):
    strategy = bfs if self.use_bfs else dfs
    predicate = lambda path: self.query in path.split('/')[-1].lower()

    for match in strategy(self.root, predicate):
      if self._stopped:
        break
      self.result_found.emit(match)

    self.finished.emit()

  def stop(self):
    self._stopped = True