import os
from collections import deque
from typing import Callable, Generator

def dfs(root: str, predicate: Callable[[str], bool]) -> Generator[str, None, None]:
  stack = [root]
  while stack:
    current = stack.pop()
    try:
      entries = list(os.scandir(current))
    except PermissionError:
      continue
    for entry in entries:
      if predicate(entry.path):
        yield entry.path
      if entry.is_dir(follow_symlinks=False):
        stack.append(entry.path)

def bfs(root: str, predicate: Callable[[str], bool]) -> Generator[str, None, None]:
  queue = deque([root])
  while queue:
    current = queue.popleft()
    try:
      entries = list(os.scandir(current))
    except PermissionError:
      continue
    for entry in entries:
      if predicate(entry.path):
        yield entry.path
      if entry.is_dir(follow_symlinks=False):
        queue.append(entry.path)