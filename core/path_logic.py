import os

class PathNode:
  def __init__(self, name, full_path):
    self.name = name
    self.full_path = full_path
    self.next = None

class PathLinkedList:
  def __init__(self, path_string):
    self.head = None
    self.build_from_path(path_string)

  def build_from_path(self, path_string):
    # Example: /home/user/Documents -> ["", "home", "user", "Documents"]
    parts = path_string.split(os.sep)
    current_path = ""
    last_node = None

    for part in parts:
      # Handle root path
      if part == "" and current_path == "":
        display_name = os.sep
        current_path = os.sep
      elif part == "":
        continue
      else:
        display_name = part
        current_path = os.path.join(current_path, part)
      
      new_node = PathNode(display_name, current_path)
      if not self.head:
        self.head = new_node
      if last_node:
        last_node.next = new_node
      last_node = new_node