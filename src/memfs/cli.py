#!/usr/bin/env python
"""
Command-line interface for the memfs virtual filesystem.
"""

import argparse
import sys
import json
import os
from memfs import create_fs, __version__


def print_tree(fs, path, indent=""):
    """Print a directory tree."""
    print(f"{indent}{os.path.basename(path) or path}")
    indent += "    "

    # Get directory contents
    try:
        contents = fs.listdir(path)
    except Exception as e:
        print(f"{indent}Error: {e}")
        return

    # First list directories
    for item in sorted(contents):
        item_path = fs.path.join(path, item)
        if fs.isdir(item_path):
            print_tree(fs, item_path, indent)

    # Then list files
    for item in sorted(contents):
        item_path = fs.path.join(path, item)
        if fs.isfile(item_path):
            print(f"{indent}{item}")


def dump_fs(fs, path):
    """Dump the filesystem to a JSON structure."""
    result = {}

    # Add files first
    for root, dirs, files in fs.walk(path):
        for file in files:
            file_path = fs.path.join(root, file)
            try:
                content = fs.readfile(file_path)
                if isinstance(content, bytes):
                    content = content.decode('utf-8', errors='replace')
                result[file_path] = content
            except Exception as e:
                result[file_path] = f"Error: {e}"

    return result


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description="memfs - Virtual Filesystem in Memory")
    parser.add_argument('--version', action='version', version=f'memfs {__version__}')

    subparsers = parser.add_subparsers(dest='command', help='Command')

    # Tree command
    tree_parser = subparsers.add_parser('tree', help='Display filesystem as a tree')
    tree_parser.add_argument('path', nargs='?', default='/', help='Path to display')

    # Touch command
    touch_parser = subparsers.add_parser('touch', help='Create an empty file')
    touch_parser.add_argument('path', help='Path to file')

    # Mkdir command
    mkdir_parser = subparsers.add_parser('mkdir', help='Create a directory')
    mkdir_parser.add_argument('path', help='Path to directory')
    mkdir_parser.add_argument('-p', '--parents', action='store_true', help='Create parent directories as needed')

    # Write command
    write_parser = subparsers.add_parser('write', help='Write content to a file')
    write_parser.add_argument('path', help='Path to file')
    write_parser.add_argument('content', help='Content to write')

    # Read command
    read_parser = subparsers.add_parser('read', help='Read content from a file')
    read_parser.add_argument('path', help='Path to file')

    # Dump command
    dump_parser = subparsers.add_parser('dump', help='Dump filesystem to JSON')
    dump_parser.add_argument('path', nargs='?', default='/', help='Root path to dump')

    args = parser.parse_args()

    # Create filesystem instance
    fs = create_fs()

    try:
        if args.command == 'tree':
            print_tree(fs, args.path)

        elif args.command == 'touch':
            with fs.open(args.path, 'w') as f:
                pass
            print(f"Created file: {args.path}")

        elif args.command == 'mkdir':
            if args.parents:
                fs.makedirs(args.path, exist_ok=True)
            else:
                fs.mkdir(args.path)
            print(f"Created directory: {args.path}")

        elif args.command == 'write':
            with fs.open(args.path, 'w') as f:
                f.write(args.content)
            print(f"Wrote to: {args.path}")

        elif args.command == 'read':
            with fs.open(args.path, 'r') as f:
                content = f.read()
            print(content)

        elif args.command == 'dump':
            data = dump_fs(fs, args.path)
            print(json.dumps(data, indent=2))

        else:
            parser.print_help()
            return 1

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())