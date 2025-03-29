# memfs
Moduł memfs implementuje wirtualny system plików w pamięci. Ten moduł zapewnia interfejs zgodny z modułem os i zapewnia operacje na plikach i katalogach przechowywanych w pamięci RAM, a nie na dysku.


# Modularny Framework Pipeline z Wirtualnym Systemem Plików

Ten projekt implementuje modularny framework pipeline z automatycznym generowaniem usług gRPC w Pythonie, używając wirtualnego systemu plików w pamięci RAM zamiast operacji na dysku fizycznym.

## Główne funkcje

- Tworzenie dynamicznych komponentów przetwarzania
- Automatyczne generowanie definicji protokołu gRPC
- Kompilacja kodu gRPC
- Orkiestracja komponentów pipeline
- Wirtualny system plików w pamięci RAM
- Przykładowe komponenty transformacji (JSON → HTML → PDF)

## Struktura projektu

- `memfs.py` - implementacja wirtualnego systemu plików w pamięci
- `api_framework.py` - główny kod frameworka z integracją memfs
- `requirements.txt` - zależności projektu

## Wirtualny system plików (memfs)

Zamiast tradycyjnego zapisywania plików na dysku, projekt używa wirtualnego systemu plików w pamięci, co zapewnia:

- Szybszy dostęp do plików (brak operacji I/O na dysku)
- Tymczasowe przechowywanie danych bez zajmowania miejsca na dysku
- Izolację od systemu plików hosta
- Możliwość symulacji różnych struktur katalogów

## Instalacja

1. Sklonuj repozytorium
2. Zainstaluj zależności:

```bash
pip install -r requirements.txt
```

## Przykład użycia

```python
from api_framework import DynamicgRPCComponent, PipelineOrchestrator, example_usage

# Uruchom przykład
example_usage()
```

## Komponenty

### ApiFuncFramework

Framework do tworzenia usług gRPC z funkcji Python.

### DynamicgRPCComponent

Komponent pipeline z dynamicznym interfejsem gRPC.

### PipelineOrchestrator

Orkiestrator pipeline, który zarządza komponentami i przepływem danych.

### Moduł memfs

Implementacja wirtualnego systemu plików w pamięci.

## Przejście z fizycznego na wirtualny system plików

Główne zmiany w porównaniu do wersji używającej fizycznego systemu plików:

1. Operacje na systemie plików używają teraz `fs` zamiast `os`
2. Ścieżki są względne do korzenia wirtualnego systemu plików (`/`)
3. Dane są przechowywane w pamięci RAM, nie na dysku
4. Dodano logikę do tymczasowego kopiowania plików na dysk fizyczny podczas kompilacji proto (wymagane przez gRPC)

## Licencja

