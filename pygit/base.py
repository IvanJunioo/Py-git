import os
import datetime as dt
import itertools
import operator

from dataclasses import dataclass

from pathlib import Path
from . import data
from . import common_types

OBJ_TYPE = common_types.ObjectType

@dataclass(frozen=True)
class Commit:
  parent: str | None
  tree: str
  message: str

def write_tree(directory: str = '.') -> str:
  entries: list[tuple[str, str, str]] = []

  with os.scandir(directory) as dir:
    for entry in dir:
      fullPath = os.path.join(directory, entry.name)

      if entry.is_file(follow_symlinks = False):
        if (is_ignored(fullPath)): continue

        type_: str = OBJ_TYPE.BLOB.value
        with open(fullPath, 'rb') as f:
          oid: str = data.hash_object(f.read())

      elif entry.is_dir(follow_symlinks = False):
        type_: str = OBJ_TYPE.TREE.value
        oid: str = write_tree(fullPath)
      
      else:
        continue # ignore everything else
      
      entries.append((entry.name, oid, type_))
  
  tree: str = ''.join(f'{type_} {oid} {name}\n' for name, oid, type_ in sorted(entries))
  return data.hash_object(tree.encode(), "tree")

def iter_tree(oid: str):
  if not oid: return

  tree: bytes = data.get_object(oid, "tree")

  for object in tree.decode().splitlines():
    type_, ooid, name = object.split(" ", 2)
    yield type_, ooid, name

def get_tree(oid: str, base_path: str = ""):
  result: dict[str, str] = {}
  
  for type_, oid, name in iter_tree(oid):
    path = base_path + name
    if type_ == "blob":
      result[path] = oid
    elif type_ == "tree":
      result.update(get_tree(oid, f'{path}/'))
    else:
      assert False, f'Expected a tree type but got {type_}'
  
  return result

def read_tree(tree_oid: str):
  empty_current_directory()

  for path, oid in get_tree(tree_oid, "./").items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
      f.write(data.get_object(oid))

def commit(message: str):
  """
  Commit sample output
  
  tree 6d4f078c8940ef4d654295790f6dd62e155fa793\n
  This is a commit message!
  """
  commit = f'tree {write_tree()}\n'

  HEAD = data.get_ref("HEAD")
  if HEAD:
    commit += f'parent {HEAD}\n'

  oid: str = data.hash_object(f"{commit}\n{message}\n".encode(), 'commit')

  data.update_ref("HEAD", oid)

  return oid

def get_commit(oid: str) -> Commit:
  parent, tree = None, ""

  commit = data.get_object(oid, "commit").decode()
  lines = iter(commit.splitlines())
  
  for line in itertools.takewhile(operator.truth, lines):
    key, value = line.split(" ", 1)

    if key == "tree":
      tree = value
    elif key == "parent":
      parent = value
    else:
      assert False, f'Unknown field {key}'
  
  message = '\n'.join(lines)

  return Commit(tree = tree, parent = parent, message = message)

def checkout(oid: str):
  commit = get_commit(oid)
  read_tree(commit.tree)
  data.update_ref("HEAD", oid)

def create_tag(tag_name: str, oid: str):
  path: str = os.path.join("refs", "tags", tag_name)
  data.update_ref(path, oid)

def get_oid(name: str):
  return data.get_ref(name) or name

def is_ignored(path: str):
  return ".pygit" in Path(path).parts

def empty_current_directory():
  for root, dirnames, filenames in os.walk(".", topdown=False):
    for filename in filenames:
      path = os.path.relpath(os.path.join(root, filename))

      if is_ignored(path) or not os.path.isfile(path):
        continue

      os.remove(path)
    
    for dirname in dirnames:
      path = os.path.relpath(os.path.join(root, dirname))
      
      if is_ignored(path):
        continue
      
      try:
        os.rmdir(path)
      except (FileNotFoundError, OSError):
        pass

def get_curr_time() -> str:
  return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#pyright: strict