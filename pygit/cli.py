import argparse as ap
import os
import sys
import textwrap

from . import data
from . import base

def main ():
  args = parse_args()
  args.func(args)

def parse_args():
  parser = ap.ArgumentParser()
  
  commands = parser.add_subparsers(dest="command")
  commands.required = True

  oid = base.get_oid

  # init command
  init_parser = commands.add_parser("init")
  init_parser.set_defaults(func=init)

  # hasher
  hash_object_parser = commands.add_parser("hash-object")
  hash_object_parser.set_defaults(func=hash_object)
  hash_object_parser.add_argument("file", type=oid)

  # hash reader
  cat_file_parser = commands.add_parser("cat-file")
  cat_file_parser.set_defaults(func=cat_file)
  cat_file_parser.add_argument("object", type=oid)

  # tree writer
  write_tree_parser = commands.add_parser("write-tree")
  write_tree_parser.set_defaults(func=write_tree)

  # tree reader
  read_tree_parser = commands.add_parser("read-tree")
  read_tree_parser.set_defaults(func=read_tree)
  read_tree_parser.add_argument("tree", type=oid)

  # commit command
  commit_parser = commands.add_parser("commit")
  commit_parser.set_defaults(func=commit)
  commit_parser.add_argument("-m", "--message", required=True)

  # commit getter
  log_parser = commands.add_parser("log")
  log_parser.set_defaults(func=log)
  log_parser.add_argument("oid", default= "@", type=oid, nargs="?")

  # checkout
  checkout_parser = commands.add_parser("checkout")
  checkout_parser.set_defaults(func=checkout)
  checkout_parser.add_argument("oid", type=oid)

  # tag
  tag_parser = commands.add_parser("tag")
  tag_parser.set_defaults(func=tag)
  tag_parser.add_argument("tag")
  tag_parser.add_argument("oid", default= "@", type=oid, nargs="?")

  # gitk (see all refs)
  k_parser = commands.add_parser("k")
  k_parser.set_defaults(func=k)
  
  return parser.parse_args()

def init(args: ap.Namespace):
  data.init()
  print(f'Initialized an empty pygit repository in {os.getcwd()}/{data.GIT_DIR}')

def hash_object(args: ap.Namespace):
  with open(args.file, 'rb') as f:
    print(data.hash_object(f.read()))

def cat_file(args: ap.Namespace):
  obj: bytes = data.get_object(args.object, expected = None)

  sys.stdout.flush()
  if obj.startswith(b'\xff\xfe') or obj.startswith(b'\xfe\xff'):
    text: str = obj.decode(encoding = "utf-16")
    sys.stdout.write(text)
  else:
    try:
      sys.stdout.write(obj.decode())
    except UnicodeDecodeError:
      sys.stdout.buffer.write(obj)

def write_tree(_: ap.Namespace):
  print(base.write_tree())

def read_tree(args: ap.Namespace):
  base.read_tree(args.tree)

def commit(args: ap.Namespace):
  print(base.commit(args.message))

def log(args: ap.Namespace):
  oid: str | None = args.oid

  while oid:
    commit = base.get_commit(oid)
    print(f"commit {oid}")
    print(textwrap.indent(commit.message, "\t"))
    print()
    
    oid = commit.parent

def checkout(args: ap.Namespace):
  base.checkout(args.oid)

def tag(args: ap.Namespace):
  oid: str | None = args.oid

  assert oid, f"There should be at least one commit made in the repository!"
  base.create_tag(args.tag, args.oid)

def k(_: ap.Namespace):
  for refname, ref in data.iter_refs():
    print(refname, ref)
    
# pyright: strict