"""
memfs implements a virtual file system in memory. This module provides an interface compatible with the os module and provides operations on files and directories stored in RAM rather than on disk.
"""
# __init__.py
# Version information

# Import only basic package information here
# Avoid importing components directly to prevent circular imports
from memfs.memfs import create_fs, MemoryFS

__version__ = "0.1.3"
__version_tuple__ = (0, 1, 1, 'dev1', 'g4306cca.d20241124')

__all__ = ["create_fs", "MemoryFS"]