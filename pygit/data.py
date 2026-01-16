import os
import sys
import hashlib

GIT_DIR = '.pygit'

def init():
  if (os.path.isdir(GIT_DIR)):
    print(f"error: repository already exists", file=sys.stderr)
    sys.exit(1)

  os.makedirs(GIT_DIR)
  os.makedirs(f'{GIT_DIR}/objects')

def hash_object(data: bytes, type_: str = "blob"):
  obj = type_.encode() + b'\x00' + data
  oid = hashlib.sha1(obj).hexdigest()
  with open(f'{GIT_DIR}/objects/{oid}', 'wb') as f:
    f.write(obj)
  
  return oid

def get_object(oid: str, expected: str | None = "blob"):
  with open(f'{GIT_DIR}/objects/{oid}', 'rb') as f:
    obj = f.read()
  
  type_, _, content = obj.partition(b'\x00')
  type_ = type_.decode()

  if expected is not None:
    assert type_ == expected, f'Expected {expected}, got {type_}'
  
  return content

def set_HEAD(oid: str):
  with open(f'{GIT_DIR}/HEAD', "w") as f:
    f.write(oid)

def get_HEAD():
  if os.path.isfile(f'{GIT_DIR}/HEAD'):
    with open(f'{GIT_DIR}/HEAD', "r") as f:
      return f.read().strip()
    
# pyright: strict
