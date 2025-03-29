#!/usr/bin/env python
"""
Basic usage examples for memfs
"""

from memfs import create_fs


def basic_file_operations():
    """Demonstrate basic file operations."""
    print("\n=== Basic File Operations ===")

    # Create a virtual filesystem
    fs = create_fs()

    # Write to a file
    fs.writefile('/hello.txt', 'Hello, world!')
    print("File written: /hello.txt")

    # Read from a file
    content = fs.readfile('/hello.txt')
    print(f"File content: '{content}'")

    # Check if a file exists
    if fs.exists('/hello.txt'):
        print("File exists!")

    # Get file information
    print(f"Is file: {fs.isfile('/hello.txt')}")
    print(f"Is directory: {fs.isdir('/hello.txt')}")

    # Remove a file
    fs.remove('/hello.txt')
    print("File removed")
    print(f"File exists after removal: {fs.exists('/hello.txt')}")


def directory_operations():
    """Demonstrate directory operations."""
    print("\n=== Directory Operations ===")

    # Create a virtual filesystem
    fs = create_fs()

    # Create directories
    fs.makedirs('/path/to/directory', exist_ok=True)
    print("Created directory: /path/to/directory")

    # Create some files
    fs.writefile('/path/to/file1.txt', 'Content 1')
    fs.writefile('/path/to/file2.txt', 'Content 2')
    fs.writefile('/path/to/directory/file3.txt', 'Content 3')

    # List directory contents
    print("\nListing directory: /path")
    for item in fs.listdir('/path'):
        print(f"  - {item}")

    print("\nListing directory: /path/to")
    for item in fs.listdir('/path/to'):
        print(f"  - {item}")

    # Walk the directory tree
    print("\nWalking directory tree:")
    for root, dirs, files in fs.walk('/'):
        print(f"Directory: {root}")
        if dirs:
            print(f"  Subdirectories: {', '.join(dirs)}")
        if files:
            print(f"  Files: {', '.join(files)}")

    # Rename directory
    fs.rename('/path/to/directory', '/path/to/renamed')
    print("\nRenamed directory /path/to/directory to /path/to/renamed")

    # Check the renamed directory
    print(f"Directory exists: {fs.exists('/path/to/renamed')}")
    print(f"File in renamed directory exists: {fs.exists('/path/to/renamed/file3.txt')}")

    # Remove a directory
    fs.makedirs('/empty/dir')
    print("\nCreated directory: /empty/dir")
    fs.rmdir('/empty/dir')
    print("Removed empty directory: /empty/dir")
    print(f"Directory exists after removal: {fs.exists('/empty/dir')}")


def file_like_objects():
    """Demonstrate using file-like objects."""
    print("\n=== File-Like Objects ===")

    # Create a virtual filesystem
    fs = create_fs()

    # Write using a file-like object
    print("Writing to a file using a file-like object...")
    with fs.open('/data.txt', 'w') as f:
        f.write('Line 1\n')
        f.write('Line 2\n')
        f.write('Line 3\n')

    # Read using a file-like object
    print("\nReading the file line by line:")
    with fs.open('/data.txt', 'r') as f:
        for line in f:
            print(f"  > {line.strip()}")

    # Seek and tell
    print("\nDemonstrating seek and tell:")
    with fs.open('/data.txt', 'r') as f:
        print(f"  Initial position: {f.tell()}")
        f.seek(7)  # Move to position 7 (start of Line 2)
        print(f"  After seek(7): {f.tell()}")
        rest = f.read()
        print(f"  Read from position 7: '{rest}'")

    # Binary mode
    print("\nDemonstrating binary mode:")
    binary_data = bytes([0, 1, 2, 3, 4, 5])
    with fs.open('/binary.bin', 'wb') as f:
        f.write(binary_data)

    with fs.open('/binary.bin', 'rb') as f:
        data = f.read()
        print(f"  Binary data read: {list(data)}")


def main():
    """Run all examples."""
    print("MEMFS EXAMPLES")
    print("==============")

    basic_file_operations()
    directory_operations()
    file_like_objects()


if __name__ == "__main__":
    main()