# memfs

A Python module that implements a virtual file system in memory.
This module provides an interface compatible with the standard `os` module and enables operations on files and directories stored in RAM rather than on disk.

## Overview

`memfs` is designed to provide a fast, isolated file system environment for applications that need temporary file operations without the overhead of disk I/O. It's particularly useful for testing, data processing pipelines, and applications that need to manipulate files without affecting the host system.

## Features

- Complete in-memory file system implementation
- API compatible with Python's standard `os` module
- File and directory operations (create, read, write, delete, rename)
- Path manipulation and traversal
- File-like objects with context manager support
- No disk I/O overhead
- Isolated from the host file system

## Installation

```bash
pip install memfs
```

Or install from source:

```bash
git clone https://github.com/pyfunc/memfs.git
cd memfs
pip install -e .
```

## Usage Examples

### Basic File Operations

```python
from memfs.memfs import MemoryFS

# Create a file system instance
fs = MemoryFS()

# Write to a file
fs.writefile('/hello.txt', 'Hello, world!')

# Read from a file
content = fs.readfile('/hello.txt')
print(content)  # Outputs: Hello, world!

# Check if a file exists
if fs.exists('/hello.txt'):
    print('File exists!')

# Create directories
fs.makedirs('/path/to/directory')

# List directory contents
files = fs.listdir('/path/to')
```

### Using File-Like Objects

```python
from memfs.memfs import MemoryFS

fs = MemoryFS()

# Write using a file-like object
with fs.open('/data.txt', 'w') as f:
    f.write('Line 1\n')
    f.write('Line 2\n')

# Read using a file-like object
with fs.open('/data.txt', 'r') as f:
    for line in f:
        print(line.strip())
```

### Directory Operations

```python
from memfs.memfs import MemoryFS

fs = MemoryFS()

# Create nested directories
fs.makedirs('/a/b/c')

# Walk the directory tree
for root, dirs, files in fs.walk('/'):
    print(f"Directory: {root}")
    print(f"Subdirectories: {dirs}")
    print(f"Files: {files}")
```

## API Reference

The `MemoryFS` class provides the following methods:

- `open(path, mode)` - Open a file and return a file-like object
- `exists(path)` - Check if a path exists
- `isfile(path)` - Check if a path is a file
- `isdir(path)` - Check if a path is a directory
- `listdir(path)` - List contents of a directory
- `mkdir(path)` - Create a directory
- `makedirs(path, exist_ok=False)` - Create directories recursively
- `remove(path)` - Remove a file
- `rmdir(path)` - Remove an empty directory
- `rename(src, dst)` - Rename a file or directory
- `readfile(path)` - Read a file's contents as a string
- `writefile(path, content)` - Write content to a file
- `readfilebytes(path)` - Read a file's contents as bytes
- `writefilebytes(path, content)` - Write binary content to a file
- `walk(path)` - Walk a directory tree (similar to os.walk)

## Use Cases

- Unit testing file operations without touching the disk
- Temporary data processing pipelines
- Sandboxed environments
- Mock file systems for testing
- Fast data manipulation without disk I/O overhead

## License

Apache-2.0

