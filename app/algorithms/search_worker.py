import queue
import threading
from .search import bfs, dfs


class SearchWorker:
  MAX_RESULTS = 500

  def __init__(self, root: str, query: str, use_bfs: bool = True):
    self.root     = root
    self.query    = query.lower()
    self.use_bfs  = use_bfs
    self._stopped = False
    self._queue   = queue.Queue()
    self._thread  = None

  def start(self):
    self._stopped = False
    self._thread  = threading.Thread(target=self._run, daemon=True)
    self._thread.start()

  def _run(self):
    strategy  = bfs if self.use_bfs else dfs
    predicate = lambda path: self.query in path.split('/')[-1].lower()
    count     = 0

    for match in strategy(self.root, predicate):
      if self._stopped or count >= self.MAX_RESULTS:
        break
      self._queue.put(match)
      count += 1

    self._queue.put(None)

  def stop(self):
    self._stopped = True

  def is_running(self) -> bool:
    return self._thread is not None and self._thread.is_alive()

  def drain(self) -> tuple[list[str], bool]:
    results = []
    done    = False
    try:
      while True:
        item = self._queue.get_nowait()
        if item is None:
          done = True
          break
        results.append(item)
    except queue.Empty:
      pass
    return results, done