import os

from pathlib import Path
from . import data
from . import common_types

OBJ_TYPE = common_types.ObjectType

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
  for path, oid in get_tree(tree_oid, "./").items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
      f.write(data.get_object(oid))

def is_ignored(path: str):
  return ".pygit" in Path(path).parts

#pyright: strict