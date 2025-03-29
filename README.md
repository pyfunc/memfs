# memfs - A Python Virtual File System in Memory

A Python module that implements a virtual file system in memory. This module provides an interface compatible with the standard `os` module and enables operations on files and directories stored in RAM rather than on disk.

## Overview

`memfs` is designed to provide a fast, isolated file system environment for applications that need temporary file operations without the overhead of disk I/O. It's particularly useful for testing, data processing pipelines, and applications that need to manipulate files without affecting the host system.

## Features

- Complete in-memory file system implementation
- API compatible with Python's standard `os` module
- File and directory operations (create, read, write, delete, rename)
- Path manipulation and traversal
- File-like objects with context manager support
- gRPC service generation for pipeline components
- Encryption and compression support via extended filesystem
- State persistence between CLI invocations
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

For development setup:

```bash
# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Linux/macOS
# .venv\Scripts\activate  # On Windows

# Install in development mode
pip install --upgrade pip
pip install setuptools wheel
pip install -e .

# Build the package
python -m build
```

## Basic Usage Examples

### Basic File Operations

```python
from memfs import create_fs

# Create a file system instance
fs = create_fs()

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
from memfs import create_fs

fs = create_fs()

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
from memfs import create_fs

fs = create_fs()

# Create nested directories
fs.makedirs('/a/b/c')

# Walk the directory tree
for root, dirs, files in fs.walk('/'):
    print(f"Directory: {root}")
    print(f"Subdirectories: {dirs}")
    print(f"Files: {files}")
```

## Advanced Usage Examples

### Data Processing Pipeline

```python
from memfs import create_fs
import json
import csv

fs = create_fs()

# Create directories
fs.makedirs('/data/raw', exist_ok=True)
fs.makedirs('/data/processed', exist_ok=True)

# Write CSV data
with fs.open('/data/raw/input.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerows([
        ['id', 'name', 'value'],
        [1, 'Alpha', 100],
        [2, 'Beta', 200]
    ])

# Process CSV to JSON
with fs.open('/data/raw/input.csv', 'r', newline='') as f:
    reader = csv.DictReader(f)
    data = [row for row in reader]

# Transform and save the data
for item in data:
    item['value'] = int(item['value'])
    item['double_value'] = item['value'] * 2

with fs.open('/data/processed/output.json', 'w') as f:
    json.dump(data, f, indent=2)
```

### Parallel Processing

```python
from memfs import create_fs
import json
import concurrent.futures

fs = create_fs()
fs.makedirs('/parallel/input', exist_ok=True)
fs.makedirs('/parallel/output', exist_ok=True)

# Create input files
for i in range(10):
    fs.writefile(f'/parallel/input/file_{i}.json', json.dumps({'id': i}))

def process_file(filename):
    with fs.open(f'/parallel/input/{filename}', 'r') as f:
        data = json.loads(f.read())
    
    # Process data
    data['processed'] = True
    
    with fs.open(f'/parallel/output/processed_{filename}', 'w') as f:
        f.write(json.dumps(data, indent=2))
    
    return data['id']

# Process files in parallel
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    futures = {executor.submit(process_file, f): f for f in fs.listdir('/parallel/input')}
    for future in concurrent.futures.as_completed(futures):
        file_id = future.result()
        print(f"Processed file ID: {file_id}")
```

### Encrypted and Compressed Files

```python
from memfs.examples.custom_filesystem import create_extended_fs

# Create extended filesystem with encryption and compression
fs = create_extended_fs()

# Write to an encrypted file
with fs.open_encrypted('/secret.txt', 'w', password='mysecret') as f:
    f.write('This is sensitive information')

# Read from an encrypted file
with fs.open_encrypted('/secret.txt', 'r', password='mysecret') as f:
    content = f.read()
    print(content)

# Write to a compressed file (good for large text)
with fs.open_compressed('/compressed.txt', 'w', compression_level=9) as f:
    f.write('This content will be compressed ' * 1000)

# Check the file sizes
normal_size = len(fs.readfile('/secret.txt'))
compressed_size = len(fs._FS_DATA['files']['/compressed.txt'])
print(f"Compression ratio: {normal_size / compressed_size:.2f}x")
```

### gRPC Service Pipeline

```python
from memfs import create_fs
from memfs.api import DynamicgRPCComponent, PipelineOrchestrator

# Define transformation functions
def transform_data(data):
    if isinstance(data, dict):
        data['transformed'] = True
    return data

def format_data(data):
    if isinstance(data, dict):
        data['formatted'] = True
    return data

# Create virtual directories
fs = create_fs()
fs.makedirs('/proto/transform', exist_ok=True)
fs.makedirs('/proto/format', exist_ok=True)
fs.makedirs('/generated/transform', exist_ok=True)
fs.makedirs('/generated/format', exist_ok=True)

# Create components
transform_component = DynamicgRPCComponent(
    transform_data,
    proto_dir="/proto/transform",
    generated_dir="/generated/transform",
    port=50051
)

format_component = DynamicgRPCComponent(
    format_data,
    proto_dir="/proto/format",
    generated_dir="/generated/format",
    port=50052
)

# Create and execute pipeline
pipeline = PipelineOrchestrator()
pipeline.add_component(transform_component)
pipeline.add_component(format_component)

result = pipeline.execute_pipeline({"input": "data"})
print(result)  # {"input": "data", "transformed": true, "formatted": true}
```

## Command-line Interface

`memfs` provides a command-line interface for basic file operations. The CLI maintains state between invocations by default, storing filesystem data in `~/.memfs_state.json`.

### Basic CLI Usage

```bash
# Initialize a new filesystem (clears any existing state)
memfs init

# Display filesystem as a tree
memfs tree /

# Create a directory with parents
memfs mkdir -p /data/subdir

# Create an empty file
memfs touch /data/hello.txt

# Write content to a file
memfs write /data/hello.txt "Hello, virtual world!"

# Read file content
memfs read /data/hello.txt

# Dump filesystem content as JSON
memfs dump
```

### Interactive Shell Mode

For a more interactive experience, you can use the shell mode:

```bash
memfs shell
```

This launches an interactive shell where you can run multiple commands without restarting the CLI:

```
memfs> mkdir -p /data
memfs> touch /data/hello.txt
memfs> write /data/hello.txt "Hello from shell mode!"
memfs> tree /
memfs> exit
```

### CLI State Management

The CLI stores state in `~/.memfs_state.json`. If you're experiencing issues with state persistence:

```bash
# Check if state file exists
ls -la ~/.memfs_state.json

# Reset state by initializing a new filesystem
memfs init

# Or manually create an empty state file
echo '{"files": {}, "dirs": ["/"]}' > ~/.memfs_state.json
```

### Creating a Custom CLI Command

You can create a custom script to use memfs in a single process:

```python
#!/usr/bin/env python
from memfs import create_fs

fs = create_fs()
fs.makedirs('/data', exist_ok=True)
fs.writefile('/data/hello.txt', 'Hello, world!')

print("Filesystem contents:")
for root, dirs, files in fs.walk('/'):
    print(f"Directory: {root}")
    for d in dirs:
        print(f"  Dir: {d}")
    for f in files:
        print(f"  File: {f}")
```

## Project Structure

```
memfs/
├── setup.py          # Package installation configuration
├── setup.cfg         # Setup configuration
├── README.md         # Project documentation
├── src/              # Source code
│   └── memfs/        # Main package
│       ├── __init__.py     # Basic component imports
│       ├── _version.py     # Version information
│       ├── memfs.py        # Virtual filesystem implementation
│       ├── api.py          # gRPC service generation module
│       └── cli.py          # Command-line interface
├── tests/            # Unit tests
│   ├── __init__.py
│   ├── test_memfs.py       # Tests for memfs module
│   └── test_api.py         # Tests for API module
└── examples/         # Usage examples
    ├── basic_usage.py      # Basic operations
    └── advanced_usage.py   # Advanced scenarios
```

## API Reference

### MemoryFS Class

- `open(path, mode='r')` - Open a file
- `makedirs(path, exist_ok=False)` - Create directories recursively
- `mkdir(path, mode=0o777)` - Create a directory
- `exists(path)` - Check if a path exists
- `isfile(path)` - Check if a path is a file
- `isdir(path)` - Check if a path is a directory
- `listdir(path)` - List directory contents
- `walk(top)` - Walk through directories recursively
- `remove(path)` - Remove a file
- `rmdir(path)` - Remove an empty directory
- `rename(src, dst)` - Rename a file or directory
- `readfile(path)` - Read an entire file
- `writefile(path, data)` - Write data to a file
- `readfilebytes(path)` - Read a file's contents as bytes
- `writefilebytes(path, data)` - Write binary content to a file

### Extended MemoryFS Class

- `open_encrypted(path, mode='r', password='')` - Open an encrypted file
- `open_compressed(path, mode='r', compression_level=9)` - Open a compressed file
- `set_metadata(path, metadata)` - Set metadata for a file
- `get_metadata(path)` - Get metadata for a file
- `find(pattern, start_path='/')` - Find files matching a pattern
- `search_content(text, extensions=None, start_path='/')` - Search for files containing text
- `backup(path, backup_dir='/backup')` - Create a backup of a file or directory

### API Module

- `DynamicgRPCComponent` - Create a gRPC service from a function
- `PipelineOrchestrator` - Orchestrate multiple components into a pipeline
- `ApiFuncConfig` - Configuration for gRPC services
- `ApiFuncFramework` - Framework for creating gRPC services

## Use Cases

- **Unit testing** - Test file operations without touching the disk
- **Data processing pipelines** - Process data through multiple stages in memory
- **Microservices** - Create gRPC services from Python functions
- **Sandboxed environments** - Run file operations in an isolated environment
- **Performance optimization** - Avoid disk I/O overhead for temporary operations
- **Secure storage** - Encrypt sensitive data in memory
- **Containerized applications** - Reduce container size by using in-memory storage

## License

Apache-2.0