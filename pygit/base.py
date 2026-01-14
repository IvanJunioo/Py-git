import os

from pathlib import Path
from . import data

def write_tree(directory = '.'):
  with os.scandir(directory) as dir:
    for entry in dir:
      fullPath = os.path.join(directory, entry.name)

      if entry.is_file(follow_symlinks = False):
        if (is_ignored(fullPath)): continue

        with open(fullPath, 'rb') as f:
          print(data.hash_object(f.read()), fullPath)
          
      elif entry.is_dir(follow_symlinks = False):
        write_tree(entry)

def is_ignored(path: str):
  return ".pygit" in Path(path).parts
