# MemFS - Virtual Memory Filesystem

MemFS implements a virtual file system in memory. This module provides an interface compatible with the os module and provides operations on files and directories stored in RAM rather than on disk.

## Features

- In-memory file operations
- OS-compatible API
- Integration with gRPC services
- Seamless API function service generation
- Temporary file copying to physical disk when needed

## Installation

```bash
pip install memfs
```

## Basic Usage

```python
from memfs import create_fs

# Create a virtual filesystem
fs = create_fs()

# Create directories
fs.makedirs("/data/reports", exist_ok=True)

# Write files
with fs.open("/data/reports/report.txt", "w") as f:
    f.write("This is a virtual file in memory!")

# Read files
with fs.open("/data/reports/report.txt", "r") as f:
    content = f.read()
    print(content)

# List directories
files = fs.listdir("/data/reports")
print(files)  # ['report.txt']

# Walk through directories
for root, dirs, files in fs.walk("/"):
    print(f"Directory: {root}")
    print(f"  Subdirectories: {dirs}")
    print(f"  Files: {files}")
```

## Advanced Usage with gRPC API Services

MemFS includes a framework for creating gRPC services from functions:

```python
from memfs.api import DynamicgRPCComponent, PipelineOrchestrator

# Define transformation functions
def json_to_html(json_data):
    # Convert JSON to HTML
    return html_content

def html_to_pdf(html_content):
    # Convert HTML to PDF
    return pdf_content

# Create virtual filesystem paths
proto_dir_json_html = "/proto/json_html"
generated_dir_json_html = "/generated/json_html"

# Create components
json_to_html_component = DynamicgRPCComponent(
    json_to_html, 
    proto_dir=proto_dir_json_html,
    generated_dir=generated_dir_json_html,
    port=50051
)

# Create an orchestrator
pipeline = PipelineOrchestrator()
pipeline.add_component(json_to_html_component)

# Execute the pipeline
result = pipeline.execute_pipeline(input_data)

# Start gRPC servers
pipeline.start_servers()
```

## Command-line Interface

MemFS provides a command-line interface for basic file operations:

```bash
# Display filesystem tree
memfs tree /

# Create a file
memfs touch /data/hello.txt

# Create directories
memfs mkdir -p /data/subdirectory

# Write content to a file
memfs write /data/hello.txt "Hello, virtual world!"

# Read file content
memfs read /data/hello.txt

# Dump filesystem content as JSON
memfs dump
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

### ApiFuncFramework Class

- `register_function(func, proto_dir, generated_dir)` - Register a function as a gRPC service
- `start_server(func, proto_dir, generated_dir, port)` - Start a gRPC server for a function

### DynamicgRPCComponent Class

- `process(data)` - Process data through the component
- `start_grpc_server()` - Start the gRPC server for the component

### PipelineOrchestrator Class

- `add_component(component)` - Add a component to the pipeline
- `execute_pipeline(initial_data)` - Execute the pipeline
- `start_servers()` - Start all gRPC servers
- `stop_servers()` - Stop all gRPC servers

## Benefits of In-Memory Filesystem

- **Performance**: Faster file operations compared to disk I/O
- **Testing**: Easy to mock file operations in tests
- **Isolation**: File operations don't affect the actual filesystem
- **Concurrency**: Reduces file locking issues in multi-threaded applications
- **Ephemeral Data**: Perfect for temporary files that don't need persistence

## Use Cases

- Temporary file processing
- Unit testing file operations
- Fast file manipulation without disk I/O
- Service-based architecture with gRPC
- Function-as-a-Service implementations
- Microservice orchestration

## License

Apache-2.0