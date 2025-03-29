#!/usr/bin/env python
import sys
import json
from memfs import create_fs

# Wczytaj dane lub utwórz nowy system plików
fs = create_fs()

# Wykonaj operacje
fs.makedirs('/data', exist_ok=True)
fs.writefile('/data/hello.txt', 'Hello, virtual world!')

# Wyświetl zawartość systemu plików
print("Filesystem contents:")
for root, dirs, files in fs.walk('/'):
    print(f"Directory: {root}")
    for d in dirs:
        print(f"  Dir: {d}")
    for f in files:
        print(f"  File: {f}")

# Wyświetl zawartość pliku
print("\nFile content:")
print(fs.readfile('/data/hello.txt'))