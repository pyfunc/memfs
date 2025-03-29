#!/usr/bin/env python
# src/memfs/memfs.py

"""
Moduł memfs implementuje wirtualny system plików w pamięci.
Ten moduł zapewnia interfejs zgodny z modułem os i zapewnia operacje
na plikach i katalogach przechowywanych w pamięci RAM, a nie na dysku.
"""

import os
import io
import posixpath
from io import StringIO, BytesIO
from typing import Dict, List, Union, Optional, Any, BinaryIO, TextIO, Set


class MemoryPath:
    """Implementacja ścieżek w wirtualnym systemie plików."""

    def __init__(self):
        """Inicjalizacja modułu path."""
        pass

    def join(self, *paths) -> str:
        """Łączy ścieżki, używając '/' jako separatora."""
        return posixpath.join(*paths)

    def abspath(self, path) -> str:
        """Zwraca bezwzględną ścieżkę."""
        if not path.startswith('/'):
            path = '/' + path
        return posixpath.normpath(path)

    def basename(self, path) -> str:
        """Zwraca nazwę pliku z ścieżki."""
        return posixpath.basename(path)

    def dirname(self, path) -> str:
        """Zwraca nazwę katalogu z ścieżki."""
        return posixpath.dirname(path)

    def exists(self, path) -> bool:
        """Sprawdza, czy ścieżka istnieje w wirtualnym systemie plików."""
        return path in _FS_DATA['files'] or path in _FS_DATA['dirs']

    def isfile(self, path) -> bool:
        """Sprawdza, czy ścieżka jest plikiem."""
        return path in _FS_DATA['files']

    def isdir(self, path) -> bool:
        """Sprawdza, czy ścieżka jest katalogiem."""
        return path in _FS_DATA['dirs']

    def normpath(self, path) -> str:
        """Normalizuje ścieżkę."""
        return posixpath.normpath(path)


# Inicjalizacja struktury danych dla wirtualnego systemu plików
_FS_DATA: Dict[str, Union[Dict[str, Union[str, bytes]], Set[str]]] = {
    'files': {},  # Pliki: ścieżka -> zawartość
    'dirs': {'/'}  # Katalogi: zbiór ścieżek
}


class MemoryFile:
    """Klasa reprezentująca plik w pamięci."""

    def __init__(self, path: str, mode: str):
        """
        Inicjalizacja pliku w pamięci.

        Args:
            path: Ścieżka do pliku
            mode: Tryb otwarcia pliku ('r', 'w', 'a', 'rb', 'wb', 'ab')
        """
        self.path = path
        self.mode = mode
        self.closed = False

        is_binary = 'b' in mode
        is_read = 'r' in mode
        is_write = 'w' in mode
        is_append = 'a' in mode

        # Utwórz lub pobierz zawartość pliku
        if is_read and path not in _FS_DATA['files']:
            raise FileNotFoundError(f"Nie znaleziono pliku: {path}")

        if is_write:
            _FS_DATA['files'][path] = b'' if is_binary else ''
        elif is_append:
            if path not in _FS_DATA['files']:
                _FS_DATA['files'][path] = b'' if is_binary else ''

        # Utwórz obiekt IO
        content = _FS_DATA['files'].get(path, b'' if is_binary else '')

        if is_binary:
            self.io = BytesIO(content if isinstance(content, bytes) else content.encode('utf-8'))
        else:
            self.io = StringIO(content if isinstance(content, str) else content.decode('utf-8'))

        # Dla trybu 'a', przejdź na koniec pliku
        if is_append:
            self.io.seek(0, io.SEEK_END)

    def read(self, size: int = -1) -> Union[str, bytes]:
        """Odczytuje dane z pliku."""
        if self.closed:
            raise ValueError("I/O operation on closed file")
        return self.io.read(size)

    def write(self, data: Union[str, bytes]) -> int:
        """Zapisuje dane do pliku."""
        if self.closed:
            raise ValueError("I/O operation on closed file")
        result = self.io.write(data)
        _FS_DATA['files'][self.path] = self.io.getvalue()
        return result

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        """Przemieszcza wskaźnik w pliku."""
        if self.closed:
            raise ValueError("I/O operation on closed file")
        return self.io.seek(offset, whence)

    def tell(self) -> int:
        """Zwraca aktualną pozycję w pliku."""
        if self.closed:
            raise ValueError("I/O operation on closed file")
        return self.io.tell()

    def close(self) -> None:
        """Zamyka plik."""
        if not self.closed:
            # Zapisz zawartość z powrotem do wirtualnego systemu plików
            _FS_DATA['files'][self.path] = self.io.getvalue()
            self.io.close()
            self.closed = True

    def __enter__(self):
        """Obsługa kontekstu (with)."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Zamyka plik przy wyjściu z kontekstu."""
        self.close()


class MemoryFS:
    """Główna klasa implementująca wirtualny system plików."""

    def __init__(self):
        """Inicjalizacja wirtualnego systemu plików."""
        self.path = MemoryPath()

    def open(self, path: str, mode: str = 'r') -> Union[BinaryIO, TextIO]:
        """
        Otwiera plik w wirtualnym systemie plików.

        Args:
            path: Ścieżka do pliku
            mode: Tryb otwarcia pliku

        Returns:
            Obiekt pliku
        """
        # Normalizuj ścieżkę
        path = self.path.normpath(path)

        # Upewnij się, że katalog istnieje
        dir_path = self.path.dirname(path)
        if dir_path and not self.path.isdir(dir_path):
            raise FileNotFoundError(f"Nie znaleziono katalogu: {dir_path}")

        # Utwórz plik
        return MemoryFile(path, mode)

    def makedirs(self, path: str, exist_ok: bool = False) -> None:
        """
        Tworzy katalogi rekurencyjnie.

        Args:
            path: Ścieżka katalogu
            exist_ok: Czy ignorować istniejące katalogi
        """
        # Normalizuj ścieżkę
        path = self.path.normpath(path)

        if path in _FS_DATA['dirs'] and not exist_ok:
            raise FileExistsError(f"Katalog już istnieje: {path}")

        # Utwórz katalogi na ścieżce
        parts = path.split('/')
        current_path = ""

        for part in parts:
            if not part:
                continue

            current_path = current_path + '/' + part if current_path else '/' + part

            if current_path not in _FS_DATA['dirs']:
                _FS_DATA['dirs'].add(current_path)

    def exists(self, path: str) -> bool:
        """Sprawdza, czy ścieżka istnieje."""
        path = self.path.normpath(path)
        return path in _FS_DATA['files'] or path in _FS_DATA['dirs']

    def isfile(self, path: str) -> bool:
        """Sprawdza, czy ścieżka jest plikiem."""
        path = self.path.normpath(path)
        return path in _FS_DATA['files']

    def isdir(self, path: str) -> bool:
        """Sprawdza, czy ścieżka jest katalogiem."""
        path = self.path.normpath(path)
        return path in _FS_DATA['dirs']

    def listdir(self, path: str) -> List[str]:
        """Zwraca zawartość katalogu."""
        path = self.path.normpath(path)

        if not self.isdir(path):
            raise NotADirectoryError(f"Nie jest katalogiem: {path}")

        result = []

        # Normalizacja ścieżki
        if not path.endswith('/') and path != '/':
            path += '/'

        path_len = len(path) if path != '/' else 1

        # Szukaj bezpośrednich elementów w katalogu
        for file_path in _FS_DATA['files']:
            if file_path.startswith(path) and '/' not in file_path[path_len:]:
                result.append(self.path.basename(file_path))

        for dir_path in _FS_DATA['dirs']:
            if dir_path != path and dir_path.startswith(path) and '/' not in dir_path[path_len:]:
                result.append(self.path.basename(dir_path))

        return result

    def mkdir(self, path: str, mode: int = 0o777) -> None:
        """Tworzy katalog."""
        path = self.path.normpath(path)

        if self.exists(path):
            raise FileExistsError(f"Plik lub katalog już istnieje: {path}")

        parent_dir = self.path.dirname(path)
        if parent_dir and not self.isdir(parent_dir):
            raise FileNotFoundError(f"Katalog nadrzędny nie istnieje: {parent_dir}")

        _FS_DATA['dirs'].add(path)

    def remove(self, path: str) -> None:
        """Usuwa plik."""
        path = self.path.normpath(path)

        if not self.isfile(path):
            raise FileNotFoundError(f"Nie znaleziono pliku: {path}")

        del _FS_DATA['files'][path]

    def rmdir(self, path: str) -> None:
        """Usuwa pusty katalog."""
        path = self.path.normpath(path)

        if not self.isdir(path):
            raise NotADirectoryError(f"Nie jest katalogiem: {path}")

        # Sprawdź, czy katalog jest pusty
        path_prefix = path + '/' if not path.endswith('/') else path

        for file_path in _FS_DATA['files']:
            if file_path.startswith(path_prefix):
                raise OSError(f"Katalog nie jest pusty: {path}")

        for dir_path in _FS_DATA['dirs']:
            if dir_path != path and dir_path.startswith(path_prefix):
                raise OSError(f"Katalog nie jest pusty: {path}")

        _FS_DATA['dirs'].remove(path)

    def walk(self, top: str):
        """
        Przechodzi przez katalogi rekurencyjnie, zgodnie z os.walk.

        Zwraca krotki (root, dirs, files) dla każdego katalogu w drzewie katalogów,
        zaczynając od top (włącznie).
        """
        top = self.path.normpath(top)

        if not self.isdir(top):
            raise NotADirectoryError(f"Nie jest katalogiem: {top}")

        # Najpierw wygeneruj wyniki dla głównego katalogu
        dirs = []
        files = []

        # Normalizacja ścieżki
        path_with_slash = top
        if not path_with_slash.endswith('/') and path_with_slash != '/':
            path_with_slash += '/'

        path_len = len(path_with_slash) if path_with_slash != '/' else 1

        # Znajdź bezpośrednie elementy w katalogu
        for dir_path in _FS_DATA['dirs']:
            if dir_path != top and dir_path.startswith(path_with_slash):
                rel_path = dir_path[path_len:]
                if '/' not in rel_path:  # Tylko bezpośrednie podkatalogi
                    dirs.append(self.path.basename(dir_path))

        for file_path in _FS_DATA['files']:
            if file_path.startswith(path_with_slash):
                rel_path = file_path[path_len:]
                if '/' not in rel_path:  # Tylko bezpośrednie pliki
                    files.append(self.path.basename(file_path))

        # Sortuj listy dla spójności
        dirs.sort()
        files.sort()

        # Zwróć wyniki dla głównego katalogu
        yield top, dirs, files

        # Potem rekurencyjnie przejdź przez podkatalogi
        for d in dirs:
            dir_path = self.path.join(top, d)
            yield from self.walk(dir_path)

    def rename(self, src: str, dst: str) -> None:
        """Zmienia nazwę pliku lub katalogu."""
        src = self.path.normpath(src)
        dst = self.path.normpath(dst)

        if not self.exists(src):
            raise FileNotFoundError(f"Nie znaleziono pliku lub katalogu: {src}")

        if self.exists(dst):
            raise FileExistsError(f"Plik lub katalog docelowy już istnieje: {dst}")

        if self.isfile(src):
            _FS_DATA['files'][dst] = _FS_DATA['files'][src]
            del _FS_DATA['files'][src]
        else:  # isdir
            # Usuń stary katalog
            _FS_DATA['dirs'].remove(src)
            # Dodaj nowy katalog
            _FS_DATA['dirs'].add(dst)

            # Przenieś wszystkie pliki i podkatalogi
            src_prefix = src + '/' if not src.endswith('/') else src
            dst_prefix = dst + '/' if not dst.endswith('/') else dst
            src_len = len(src_prefix)

            # Przenieś pliki
            files_to_move = {}
            for file_path in list(_FS_DATA['files'].keys()):
                if file_path.startswith(src_prefix):
                    rel_path = file_path[src_len:]
                    new_path = dst_prefix + rel_path
                    files_to_move[new_path] = _FS_DATA['files'][file_path]
                    del _FS_DATA['files'][file_path]

            # Zapisz przeniesione pliki
            _FS_DATA['files'].update(files_to_move)

            # Przenieś katalogi
            dirs_to_add = set()
            for dir_path in list(_FS_DATA['dirs']):
                if dir_path.startswith(src_prefix):
                    rel_path = dir_path[src_len:]
                    new_path = dst_prefix + rel_path
                    dirs_to_add.add(new_path)
                    _FS_DATA['dirs'].remove(dir_path)

            # Dodaj przeniesione katalogi
            _FS_DATA['dirs'].update(dirs_to_add)

    def readfile(self, path: str) -> Union[str, bytes]:
        """Odczytuje całą zawartość pliku."""
        path = self.path.normpath(path)

        if not self.isfile(path):
            raise FileNotFoundError(f"Nie znaleziono pliku: {path}")

        return _FS_DATA['files'][path]

    def writefile(self, path: str, data: Union[str, bytes]) -> None:
        """Zapisuje dane do pliku."""
        path = self.path.normpath(path)

        # Upewnij się, że katalog istnieje
        dir_path = self.path.dirname(path)
        if dir_path and not self.isdir(dir_path):
            raise FileNotFoundError(f"Katalog nie istnieje: {dir_path}")

        # Zapisz dane
        _FS_DATA['files'][path] = data

    def readfilebytes(self, path: str) -> bytes:
        """Odczytuje całą zawartość pliku jako bytes."""
        data = self.readfile(path)
        if isinstance(data, str):
            return data.encode('utf-8')
        return data

    def writefilebytes(self, path: str, data: bytes) -> None:
        """Zapisuje bytes do pliku."""
        self.writefile(path, data)


def create_fs():
    """Tworzy i zwraca instancję wirtualnego systemu plików."""
    return MemoryFS()