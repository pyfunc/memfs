import unittest
import io
from memfs.memfs import MemoryFS, _FS_DATA, MemoryFile
from typing import Union


class TestMemoryFS(unittest.TestCase):

    def setUp(self):
        """Reset the file system before each test."""
        _FS_DATA['files'] = {}
        _FS_DATA['dirs'] = {'/'}
        self.fs = MemoryFS()

    def test_open_read_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            self.fs.open('/nonexistent.txt', 'r')

    def test_open_write_new_file(self):
        with self.fs.open('/newfile.txt', 'w') as f:
            f.write('Hello, world!')
        self.assertTrue(self.fs.isfile('/newfile.txt'))
        self.assertEqual(self.fs.readfile('/newfile.txt'), 'Hello, world!')

    def test_open_read_existing_file(self):
        self.fs.writefile('/existing.txt', 'Content')
        with self.fs.open('/existing.txt', 'r') as f:
            content = f.read()
        self.assertEqual(content, 'Content')

    def test_open_append_existing_file(self):
        self.fs.writefile('/append.txt', 'Initial ')
        with self.fs.open('/append.txt', 'a') as f:
            f.write('Appended')
        self.assertEqual(self.fs.readfile('/append.txt'), 'Initial Appended')

    def test_open_binary_read_write(self):
        data = b'Binary data'
        with self.fs.open('/binary.bin', 'wb') as f:
            f.write(data)
        with self.fs.open('/binary.bin', 'rb') as f:
            read_data = f.read()
        self.assertEqual(read_data, data)

    def test_makedirs_new_directory(self):
        self.fs.makedirs('/a/b/c')
        self.assertTrue(self.fs.isdir('/a/b/c'))
        self.assertTrue(self.fs.isdir('/a/b'))
        self.assertTrue(self.fs.isdir('/a'))

    def test_makedirs_existing_directory(self):
        self.fs.makedirs('/a/b')
        self.fs.makedirs('/a/b', exist_ok=True)
        with self.assertRaises(FileExistsError):
            self.fs.makedirs('/a/b')

    def test_exists(self):
        self.fs.makedirs('/dir')
        self.fs.writefile('/file.txt', 'content')
        self.assertTrue(self.fs.exists('/dir'))
        self.assertTrue(self.fs.exists('/file.txt'))
        self.assertFalse(self.fs.exists('/nonexistent'))

    def test_isfile(self):
        self.fs.writefile('/file.txt', 'content')
        self.assertTrue(self.fs.isfile('/file.txt'))
        self.assertFalse(self.fs.isfile('/'))
        self.assertFalse(self.fs.isfile('/nonexistent'))

    def test_isdir(self):
        self.fs.makedirs('/dir')
        self.assertTrue(self.fs.isdir('/dir'))
        self.assertTrue(self.fs.isdir('/'))
        self.assertFalse(self.fs.isdir('/nonexistent'))
        self.assertFalse(self.fs.isdir('/file.txt'))

    def test_listdir(self):
        self.fs.makedirs('/dir1')
        self.fs.writefile('/dir1/file1.txt', 'content')
        self.fs.writefile('/dir1/file2.txt', 'content')
        self.fs.makedirs('/dir1/dir2')
        self.fs.makedirs('/dir3')
        self.fs.writefile('/file.txt', 'content')

        self.assertEqual(sorted(self.fs.listdir('/dir1')), sorted(['file1.txt', 'file2.txt', 'dir2']))
        self.assertEqual(sorted(self.fs.listdir('/')), sorted(['dir1', 'dir3', 'file.txt']))

        with self.assertRaises(NotADirectoryError):
            self.fs.listdir('/file.txt')

    def test_mkdir(self):
        self.fs.mkdir('/newdir')
        self.assertTrue(self.fs.isdir('/newdir'))
        with self.assertRaises(FileExistsError):
            self.fs.mkdir('/newdir')
        with self.assertRaises(FileNotFoundError):
            self.fs.mkdir('/a/b/c')

    def test_remove(self):
        self.fs.writefile('/file.txt', 'content')
        self.fs.remove('/file.txt')
        self.assertFalse(self.fs.exists('/file.txt'))
        with self.assertRaises(FileNotFoundError):
            self.fs.remove('/file.txt')

    def test_rmdir(self):
        self.fs.mkdir('/dir')
        self.fs.rmdir('/dir')
        self.assertFalse(self.fs.exists('/dir'))
        with self.assertRaises(NotADirectoryError):
            self.fs.rmdir('/file.txt')
        self.fs.mkdir('/dir')
        self.fs.writefile('/dir/file.txt', 'content')
        with self.assertRaises(OSError):
            self.fs.rmdir('/dir')

    def test_walk(self):
        self.fs.makedirs('/a/b/c')
        self.fs.writefile('/a/file1.txt', 'content')
        self.fs.writefile('/a/b/file2.txt', 'content')
        self.fs.writefile('/a/b/c/file3.txt', 'content')

        result = list(self.fs.walk('/a'))
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0][0], '/a')
        self.assertEqual(sorted(result[0][1]), sorted(['b']))
        self.assertEqual(sorted(result[0][2]), sorted(['file1.txt']))
        self.assertEqual(result[1][0], '/a/b')
        self.assertEqual(sorted(result[1][1]), sorted(['c']))
        self.assertEqual(sorted(result[1][2]), sorted(['file2.txt']))
        self.assertEqual(result[2][0], '/a/b/c')
        self.assertEqual(sorted(result[2][1]), sorted([]))
        self.assertEqual(sorted(result[2][2]), sorted(['file3.txt']))

        with self.assertRaises(NotADirectoryError):
            list(self.fs.walk('/a/file1.txt'))

    def test_rename_file(self):
        self.fs.writefile('/old.txt', 'content')
        self.fs.rename('/old.txt', '/new.txt')
        self.assertFalse(self.fs.exists('/old.txt'))
        self.assertTrue(self.fs.isfile('/new.txt'))
        self.assertEqual(self.fs.readfile('/new.txt'), 'content')

    def test_rename_dir(self):
        self.fs.makedirs('/olddir')
        self.fs.writefile('/olddir/file.txt', 'content')
        self.fs.makedirs('/olddir/subdir')
        self.fs.rename('/olddir', '/newdir')
        self.assertFalse(self.fs.exists('/olddir'))
        self.assertTrue(self.fs.isdir('/newdir'))
        self.assertTrue(self.fs.isfile('/newdir/file.txt'))
        self.assertTrue(self.fs.isdir('/newdir/subdir'))

    def test_rename_file_exists(self):
        self.fs.writefile('/old.txt', 'content')
        self.fs.writefile('/new.txt', 'content')
        with self.assertRaises(FileExistsError):
            self.fs.rename('/old.txt', '/new.txt')

    def test_rename_not_exists(self):
        with self.assertRaises(FileNotFoundError):
            self.fs.rename('/old.txt', '/new.txt')

    def test_readfile(self):
        self.fs.writefile('/file.txt', 'content')
        self.assertEqual(self.fs.readfile('/file.txt'), 'content')
        with self.assertRaises(FileNotFoundError):
            self.fs.readfile('/nonexistent.txt')

    def test_writefile(self):
        self.fs.writefile('/file.txt', 'content')
        self.assertEqual(self.fs.readfile('/file.txt'), 'content')
        self.fs.writefile('/file.txt', 'new content')
        self.assertEqual(self.fs.readfile('/file.txt'), 'new content')

    def test_writefile_dir_not_exists(self):
        with self.assertRaises(FileNotFoundError):
            self.fs.writefile('/a/b/file.txt', 'content')

    def test_readfilebytes(self):
        self.fs.writefile('/file.txt', 'content')
        self.assertEqual(self.fs.readfilebytes('/file.txt'), b'content')
        self.fs.writefile('/file2.txt', b'binary')
        self.assertEqual(self.fs.readfilebytes('/file2.txt'), b'binary')

    def test_writefilebytes(self):
        self.fs.writefilebytes('/file.txt', b'binary')
        self.assertEqual(self.fs.readfilebytes('/file.txt'), b'binary')

    def test_memory_file_read_write_seek_tell(self):
        self.fs.writefile('/file.txt', 'abcdef')
        with self.fs.open('/file.txt', 'r+') as f:
            self.assertEqual(f.read(2), 'ab')
            self.assertEqual(f.tell(), 2)
            f.seek(0)
            self.assertEqual(f.read(3), 'abc')
            f.seek(2)
            f.write('XY')
            f.seek(0)
            self.assertEqual(f.read(), 'abXYef')

    def test_memory_file_closed(self):
        f = self.fs.open('/file.txt', 'w')
        f.close()
        with self.assertRaises(ValueError):
            f.read()
        with self.assertRaises(ValueError):
            f.write('abc')
        with self.assertRaises(ValueError):
            f.seek(0)
        with self.assertRaises(ValueError):
            f.tell()

    def test_memory_file_context_manager(self):
        with self.fs.open('/file.txt', 'w') as f:
            f.write('abc')
        self.assertEqual(self.fs.readfile('/file.txt'), 'abc')

    def test_open_dir_not_found(self):
        with self.assertRaises(FileNotFoundError):
            self.fs.open('/a/b/file.txt', 'w')


if __name__ == '__main__':
    unittest.main()
