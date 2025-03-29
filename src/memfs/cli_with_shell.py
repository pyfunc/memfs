#!/usr/bin/env python
"""
Command-line interface for the memfs virtual filesystem with state persistence and shell mode.
"""

import argparse
import sys
import json
import os
import base64
import cmd
import readline
from memfs import create_fs, __version__
from memfs.memfs import _FS_DATA  # Importujemy bezpośrednio strukturę danych

# Ścieżka do pliku stanu
STATE_FILE = os.path.expanduser("~/.memfs_state.json")


def save_state():
    """Zapisz stan systemu plików do pliku."""
    state = {
        'files': {},
        'dirs': list(_FS_DATA['dirs'])
    }

    # Konwertuj zawartość plików na format, który można zapisać jako JSON
    for path, content in _FS_DATA['files'].items():
        if isinstance(content, bytes):
            # Dla plików binarnych używamy base64
            state['files'][path] = {
                'type': 'binary',
                'content': base64.b64encode(content).decode('ascii')
            }
        else:
            state['files'][path] = {
                'type': 'text',
                'content': content
            }

    # Upewnij się, że katalog istnieje
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)

    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)


def load_state():
    """Załaduj stan systemu plików z pliku."""
    if not os.path.exists(STATE_FILE):
        return False

    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)

        # Wyczyść obecny stan
        _FS_DATA['files'].clear()
        _FS_DATA['dirs'] = {'/'}

        # Załaduj katalogi
        for dir_path in state.get('dirs', []):
            _FS_DATA['dirs'].add(dir_path)

        # Załaduj pliki
        for path, file_info in state.get('files', {}).items():
            if file_info.get('type') == 'binary':
                _FS_DATA['files'][path] = base64.b64decode(file_info['content'])
            else:
                _FS_DATA['files'][path] = file_info.get('content', '')

        return True
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error loading state: {e}", file=sys.stderr)
        return False


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


class MemfsShell(cmd.Cmd):
    """Interactive shell for memfs."""

    intro = "memfs shell. Type help or ? to list commands.\n"
    prompt = "memfs> "

    def __init__(self):
        super().__init__()
        # Load existing state or create a new filesystem
        load_state()
        self.fs = create_fs()

    def do_exit(self, arg):
        """Exit the shell."""
        print("Goodbye!")
        save_state()
        return True

    def do_quit(self, arg):
        """Exit the shell (alias for exit)."""
        return self.do_exit(arg)

    def do_tree(self, arg):
        """Display filesystem as a tree."""
        path = arg.strip() or '/'
        print_tree(self.fs, path)

    def do_touch(self, arg):
        """Create an empty file."""
        if not arg:
            print("Error: Path required")
            return

        try:
            with self.fs.open(arg, 'w') as f:
                pass
            print(f"Created file: {arg}")
            save_state()
        except Exception as e:
            print(f"Error: {e}")

    def do_mkdir(self, arg):
        """Create a directory. Use -p to create parent directories."""
        if not arg:
            print("Error: Path required")
            return

        args = arg.split()
        create_parents = False

        if '-p' in args:
            create_parents = True
            args.remove('-p')

        if not args:
            print("Error: Path required")
            return

        path = args[0]

        try:
            if create_parents:
                self.fs.makedirs(path, exist_ok=True)
            else:
                self.fs.mkdir(path)
            print(f"Created directory: {path}")
            save_state()
        except Exception as e:
            print(f"Error: {e}")

    def do_write(self, arg):
        """Write content to a file."""
        args = arg.split(maxsplit=1)

        if len(args) < 2:
            print("Error: Both path and content required")
            return

        path, content = args

        try:
            with self.fs.open(path, 'w') as f:
                f.write(content)
            print(f"Wrote to: {path}")
            save_state()
        except Exception as e:
            print(f"Error: {e}")

    def do_read(self, arg):
        """Read content from a file."""
        if not arg:
            print("Error: Path required")
            return

        try:
            with self.fs.open(arg, 'r') as f:
                content = f.read()
            print(content)
        except Exception as e:
            print(f"Error: {e}")

    def do_dump(self, arg):
        """Dump filesystem to JSON."""
        path = arg.strip() or '/'

        try:
            data = dump_fs(self.fs, path)
            print(json.dumps(data, indent=2))
        except Exception as e:
            print(f"Error: {e}")

    def do_ls(self, arg):
        """List directory contents."""
        path = arg.strip() or '/'

        try:
            contents = self.fs.listdir(path)

            for item in sorted(contents):
                item_path = self.fs.path.join(path, item)
                if self.fs.isdir(item_path):
                    print(f"{item}/")
                else:
                    print(item)
        except Exception as e:
            print(f"Error: {e}")

    def do_rm(self, arg):
        """Remove a file."""
        if not arg:
            print("Error: Path required")
            return

        try:
            self.fs.remove(arg)
            print(f"Removed file: {arg}")
            save_state()
        except Exception as e:
            print(f"Error: {e}")

    def do_rmdir(self, arg):
        """Remove an empty directory."""
        if not arg:
            print("Error: Path required")
            return

        try:
            self.fs.rmdir(arg)
            print(f"Removed directory: {arg}")
            save_state()
        except Exception as e:
            print(f"Error: {e}")

    def do_rename(self, arg):
        """Rename a file or directory."""
        args = arg.split()

        if len(args) != 2:
            print("Error: Both source and destination paths required")
            return

        src, dst = args

        try:
            self.fs.rename(src, dst)
            print(f"Renamed {src} to {dst}")
            save_state()
        except Exception as e:
            print(f"Error: {e}")

    def do_init(self, arg):
        """Initialize a new filesystem (clear all data)."""
        global _FS_DATA
        _FS_DATA['files'] = {}
        _FS_DATA['dirs'] = {'/'}
        print("Initialized new filesystem")
        save_state()

    def do_cat(self, arg):
        """Cat a file (alias for read)."""
        return self.do_read(arg)

    def default(self, line):
        """Handle unknown commands."""
        print(f"Unknown command: {line.split()[0]}")
        print("Type 'help' for a list of commands.")


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description="memfs - Virtual Filesystem in Memory")
    parser.add_argument('--version', action='version', version=f'memfs {__version__}')

    # Shell mode
    parser.add_argument('--shell', action='store_true', help='Start interactive shell')

    subparsers = parser.add_subparsers(dest='command', help='Command')

    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize a new filesystem')

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

    # Shell command
    shell_parser = subparsers.add_parser('shell', help='Start interactive shell')

    args = parser.parse_args()

    # Handle shell mode
    if args.shell or args.command == 'shell':
        try:
            MemfsShell().cmdloop()
            return 0
        except KeyboardInterrupt:
            print("\nExiting...")
            return 0

    # Handle init command specially
    if args.command == 'init':
        # Create a new filesystem
        _FS_DATA['files'] = {}
        _FS_DATA['dirs'] = {'/'}
        save_state()
        print("Initialized new filesystem")
        return 0

    # Load existing state if available
    state_loaded = load_state()

    # Create filesystem instance
    fs = create_fs()

    try:
        if args.command == 'tree':
            print_tree(fs, args.path)

        elif args.command == 'touch':
            with fs.open(args.path, 'w') as f:
                pass
            print(f"Created file: {args.path}")
            save_state()

        elif args.command == 'mkdir':
            if args.parents:
                fs.makedirs(args.path, exist_ok=True)
            else:
                fs.mkdir(args.path)
            print(f"Created directory: {args.path}")
            save_state()

        elif args.command == 'write':
            with fs.open(args.path, 'w') as f:
                f.write(args.content)
            print(f"Wrote to: {args.path}")
            save_state()

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