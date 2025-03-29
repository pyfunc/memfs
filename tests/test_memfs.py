#!/usr/bin/env python
"""
Tests for memfs module
"""

import os
import io
import pytest
from memfs.memfs import MemoryFS, _FS_DATA, MemoryFile, create_fs


class TestMemoryFS:
    """Test class for MemoryFS."""

    def setup_method(self):
        """Set up test environment."""
        # Reset the filesystem state before each test
        _FS_DATA['files'] = {}
        _FS_DATA['dirs'] = {'/'}
        self.fs = MemoryFS()

    def test_makedirs(self):
        """Test makedirs method."""
        self.fs.makedirs('/foo/bar/baz', exist_ok=False)
        assert self.fs.isdir('/foo')
        assert self.fs.isdir('/foo/bar')
        assert self.fs.isdir('/foo/bar/baz')

    def test_makedirs_exist_ok(self):
        """Test makedirs with exist_ok=True."""
        self.fs.makedirs('/foo/bar', exist_ok=False)
        self.fs.makedirs('/foo/bar', exist_ok=True)  # Should not raise

        with pytest.raises(FileExistsError):
            self.fs.makedirs('/foo/bar', exist_ok=False)

    def test_mkdir(self):
        """Test mkdir method."""
        self.fs.mkdir('/foo')
        assert self.fs.isdir('/foo')

        with pytest.raises(FileExistsError):
            self.fs.mkdir('/foo')

    def test_open_read_write(self):
        """Test open, read, and write methods."""
        with self.fs.open('/test.txt', 'w') as f:
            f.write('Hello, world!')

        with self.fs.open('/test.txt', 'r') as f:
            content = f.read()

        assert content == 'Hello, world!'

    def test_open_binary(self):
        """Test open with binary mode."""
        data = b'\x00\x01\x02\x03'

        with self.fs.open('/binary.bin', 'wb') as f:
            f.write(data)

        with self.fs.open('/binary.bin', 'rb') as f:
            content = f.read()

        assert content == data

    def test_open_nonexistent(self):
        """Test opening a nonexistent file."""
        with pytest.raises(FileNotFoundError):
            with self.fs.open('/nonexistent.txt', 'r'):
                pass

    def test_exists(self):
        """Test exists method."""
        assert self.fs.exists('/')
        assert not self.fs.exists('/foo')

        self.fs.mkdir('/foo')
        assert self.fs.exists('/foo')

        with self.fs.open('/bar.txt', 'w') as f:
            f.write('content')

        assert self.fs.exists('/bar.txt')

    def test_isfile(self):
        """Test isfile method."""
        with self.fs.open('/test.txt', 'w') as f:
            f.write('content')

        assert self.fs.isfile('/test.txt')
        assert not self.fs.isfile('/nonexistent.txt')
        assert not self.fs.isfile('/')

    def test_isdir(self):
        """Test isdir method."""
        assert self.fs.isdir('/')
        assert not self.fs.isdir('/nonexistent')

        self.fs.makedirs('/foo/bar')
        assert self.fs.isdir('/foo')
        assert self.fs.isdir('/foo/bar')
        assert not self.fs.isdir('/foo/baz')

    def test_listdir(self):
        """Test listdir method."""
        # Create some files and directories
        self.fs.makedirs('/foo/bar')
        self.fs.mkdir('/baz')

        with self.fs.open('/test1.txt', 'w') as f:
            f.write('content1')

        with self.fs.open('/test2.txt', 'w') as f:
            f.write('content2')

        with self.fs.open('/foo/test3.txt', 'w') as f:
            f.write('content3')

        # Test root directory
        root_contents = self.fs.listdir('/')
        assert set(root_contents) == {'foo', 'baz', 'test1.txt', 'test2.txt'}

        # Test subdirectory
        foo_contents = self.fs.listdir('/foo')
        assert set(foo_contents) == {'bar', 'test3.txt'}

    def test_listdir_nonexistent(self):
        """Test listdir on a nonexistent directory."""
        with pytest.raises(NotADirectoryError):
            self.fs.listdir('/nonexistent')

    def test_remove(self):
        """Test remove method."""
        with self.fs.open('/test.txt', 'w') as f:
            f.write('content')

        assert self.fs.exists('/test.txt')
        self.fs.remove('/test.txt')
        assert not self.fs.exists('/test.txt')

    def test_remove_nonexistent(self):
        """Test removing a nonexistent file."""
        with pytest.raises(FileNotFoundError):
            self.fs.remove('/nonexistent.txt')

    def test_rmdir(self):
        """Test rmdir method."""
        self.fs.mkdir('/foo')
        assert self.fs.exists('/foo')
        self.fs.rmdir('/foo')
        assert not self.fs.exists('/foo')

    def test_rmdir_non_empty(self):
        """Test removing a non-empty directory."""
        self.fs.makedirs('/foo/bar')

        with pytest.raises(OSError):
            self.fs.rmdir('/foo')

    def test_walk(self):
        """Test walk method."""
        # Create directory structure
        self.fs.makedirs('/a/b/c')
        self.fs.mkdir('/a/d')

        # Create some files
        with self.fs.open('/a/file1.txt', 'w') as f:
            f.write('content1')

        with self.fs.open('/a/b/file2.txt', 'w') as f:
            f.write('content2')

        with self.fs.open('/a/b/c/file3.txt', 'w') as f:
            f.write('content3')

        # Collect walk results
        walk_results = []
        for root, dirs, files in self.fs.walk('/a'):
            walk_results.append((root, sorted(dirs), sorted(files)))

        # Check results
        expected = [
            ('/a', ['b', 'd'], ['file1.txt']),
            ('/a/b', ['c'], ['file2.txt']),
            ('/a/b/c', [], ['file3.txt']),
            ('/a/d', [], [])
        ]

        assert len(walk_results) == len(expected)
        for result, expect in zip(walk_results, expected):
            assert result[0] == expect[0]  # root
            assert result[1] == expect[1]  # dirs
            assert result[2] == expect[2]  # files

    def test_rename_file(self):
        """Test renaming a file."""
        with self.fs.open('/old.txt', 'w') as f:
            f.write('content')

        self.fs.rename('/old.txt', '/new.txt')

        assert not self.fs.exists('/old.txt')
        assert self.fs.exists('/new.txt')

        with self.fs.open('/new.txt', 'r') as f:
            content = f.read()

        assert content == 'content'

    def test_rename_directory(self):
        """Test renaming a directory."""
        self.fs.makedirs('/old/subdir')
        with self.fs.open('/old/file.txt', 'w') as f:
            f.write('content')

        self.fs.rename('/old', '/new')

        assert not self.fs.exists('/old')
        assert self.fs.exists('/new')
        assert self.fs.exists('/new/subdir')
        assert self.fs.exists('/new/file.txt')

        with self.fs.open('/new/file.txt', 'r') as f:
            content = f.read()

        assert content == 'content'

    def test_rename_nonexistent(self):
        """Test renaming a nonexistent file."""
        with pytest.raises(FileNotFoundError):
            self.fs.rename('/nonexistent.txt', '/new.txt')

    def test_rename_target_exists(self):
        """Test renaming when the target already exists."""
        with self.fs.open('/old.txt', 'w') as f:
            f.write('old content')

        with self.fs.open('/new.txt', 'w') as f:
            f.write('new content')

        with pytest.raises(FileExistsError):
            self.fs.rename('/old.txt', '/new.txt')

    def test_writefile_readfile(self):
        """Test writefile and readfile methods."""
        self.fs.writefile('/test.txt', 'content')
        content = self.fs.readfile('/test.txt')
        assert content == 'content'

        self.fs.writefile('/binary.bin', b'\x00\x01\x02\x03')
        content = self.fs.readfile('/binary.bin')
        assert content == b'\x00\x01\x02\x03'

    def test_writefilebytes_readfilebytes(self):
        """Test writefilebytes and readfilebytes methods."""
        self.fs.writefilebytes('/binary.bin', b'\x00\x01\x02\x03')
        content = self.fs.readfilebytes('/binary.bin')
        assert content == b'\x00\x01\x02\x03'

        self.fs.writefile('/text.txt', 'text content')
        content = self.fs.readfilebytes('/text.txt')
        assert content == b'text content'

    def test_create_fs(self):
        """Test create_fs function."""
        fs = create_fs()
        assert isinstance(fs, MemoryFS)


class TestMemoryFile:
    """Test class for MemoryFile."""

    def setup_method(self):
        """Set up test environment."""
        # Reset the filesystem state before each test
        _FS_DATA['files'] = {}
        _FS_DATA['dirs'] = {'/'}
        self.fs = MemoryFS()

    def test_file_context_manager(self):
        """Test file context manager."""
        with self.fs.open('/test.txt', 'w') as f:
            f.write('Hello')
            f.write(', world!')

        assert _FS_DATA['files']['/test.txt'] == 'Hello, world!'

        with self.fs.open('/test.txt', 'r') as f:
            content = f.read()

        assert content == 'Hello, world!'

    def test_file_seek_tell(self):
        """Test file seek and tell methods."""
        with self.fs.open('/test.txt', 'w') as f:
            f.write('Hello, world!')

        with self.fs.open('/test.txt', 'r') as f:
            assert f.tell() == 0
            f.seek(7)
            assert f.tell() == 7
            content = f.read()
            assert content == 'world!'
            assert f.tell() == 13

    def test_file_read_size(self):
        """Test file read with size parameter."""
        with self.fs.open('/test.txt', 'w') as f:
            f.write('Hello, world!')

        with self.fs.open('/test.txt', 'r') as f:
            content = f.read(5)
            assert content == 'Hello'
            content = f.read(2)
            assert content == ', '
            content = f.read()
            assert content == 'world!'

    def test_file_append(self):
        """Test file append mode."""
        with self.fs.open('/test.txt', 'w') as f:
            f.write('Hello')

        with self.fs.open('/test.txt', 'a') as f:
            f.write(', world!')

        with self.fs.open('/test.txt', 'r') as f:
            content = f.read()
            assert content == 'Hello, world!'

    def test_file_binary(self):
        """Test file binary mode."""
        data = b'\x00\x01\x02\x03'

        with self.fs.open('/binary.bin', 'wb') as f:
            f.write(data)

        assert isinstance(_FS_DATA['files']['/binary.bin'], bytes)

        with self.fs.open('/binary.bin', 'rb') as f:
            content = f.read()
            assert content == data

    def test_file_closed(self):
        """Test file closed property."""
        f = self.fs.open('/test.txt', 'w')
        assert not f.closed
        f.close()
        assert f.closed

        with pytest.raises(ValueError):
            f.write('data')

        with pytest.raises(ValueError):
            f.read()