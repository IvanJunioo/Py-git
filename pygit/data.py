import os
import sys
import hashlib

GIT_DIR = '.pygit'

def init():
  """
  Initializes an empty pygit repository.

  Creates the repository directory structure inside `.pygit`.
  Fails if the repository already exists.

  Side effects:
    - Creates `.pygit`
    - Creates `.pygit/objects`
  """
  if (os.path.isdir(GIT_DIR)):
    print(f"error: repository already exists", file=sys.stderr)
    sys.exit(1)

  os.makedirs(GIT_DIR)
  os.makedirs(f'{GIT_DIR}/objects')

def hash_object(data: bytes, type_: str = "blob"):
  """
  Stores an object in the object database and return its object ID.

  Object is stored as:
      `<type>\\0<content>`
  
  The object ID (OID) is the SHA-1 hash of its byte sequence.
  """
  obj = type_.encode() + b'\x00' + data
  oid = hashlib.sha1(obj).hexdigest()
  with open(f'{GIT_DIR}/objects/{oid}', 'wb') as f:
    f.write(obj)
  
  return oid

def get_object(oid: str, expected: str | None = "blob"):
  """
  Retrieves, and validates an object from the object database.
  
  Args:
    - `oid` The object ID (SHA-1 hex string).
    - `expected` Expected object type. If None, type checking is skipped.

  Returns:
    The raw content of the object (excluding the type header).

  Raises:
    AssertionError: If the object type does not match `expected`.
    FileNotFoundError: If the object does not exist.
  """
  with open(f'{GIT_DIR}/objects/{oid}', 'rb') as f:
    obj = f.read()
  
  type_, _, content = obj.partition(b'\x00')
  type_ = type_.decode()

  if expected is not None:
    assert type_ == expected, f'Expected {expected}, got {type_}'
  
  return content

def update_ref(ref: str, oid: str):
  """
  Updates a reference to point to a given `oid`.

  Creates parent directories for the reference if they do not exist.
  """
  path = f"{GIT_DIR}/{ref}"
  os.makedirs(os.path.dirname(path), exist_ok=True)

  with open(path, "w") as f:
    f.write(oid)

def get_ref(ref: str):
  """
  Returns the referenced hash key of an object
  
  :param ref: Description
  :type ref: str
  """
  if os.path.isfile(f'{GIT_DIR}/{ref}'):
    with open(f'{GIT_DIR}/{ref}', "r") as f:
      return f.read().strip()
  
def iter_refs():
  refs: list[str] = ["HEAD"]
  for root, _, filenames in os.walk(os.path.join(GIT_DIR, "refs")):
    root = os.path.relpath(root, GIT_DIR)
    refs.extend(f'{root}/{name}' for name in filenames)
  
  for refname in refs:
    yield refname, get_ref(refname)
# pyright: strict
