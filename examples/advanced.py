#!/usr/bin/env python
"""
Advanced usage examples for memfs
"""

import time
import json
import csv
import io

from memfs import create_fs
from memfs.api import DynamicgRPCComponent, PipelineOrchestrator


def data_processing_pipeline():
    """Demonstrate a data processing pipeline using memfs."""
    print("\n=== Data Processing Pipeline ===")

    # Create a virtual filesystem
    fs = create_fs()

    # 1. Create a CSV file in memory
    print("1. Creating CSV data in virtual filesystem...")
    csv_data = [
        ['id', 'name', 'value'],
        [1, 'Alpha', 100],
        [2, 'Beta', 200],
        [3, 'Gamma', 300],
        [4, 'Delta', 400]
    ]

    with fs.open('/data/raw/input.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(csv_data)

    # 2. Process CSV to JSON
    print("2. Processing CSV to JSON...")
    with fs.open('/data/raw/input.csv', 'r', newline='') as f:
        reader = csv.DictReader(f)
        json_data = [row for row in reader]

    with fs.open('/data/processed/output.json', 'w') as f:
        json.dump(json_data, f, indent=2)

    # 3. Transform JSON data
    print("3. Transforming JSON data...")
    with fs.open('/data/processed/output.json', 'r') as f:
        data = json.load(f)

    # Add calculated field
    for item in data:
        item['value'] = int(item['value'])  # Convert string to int
        item['double_value'] = item['value'] * 2

    # 4. Save transformed data
    print("4. Saving transformed data...")
    with fs.open('/data/processed/transformed.json', 'w') as f:
        json.dump(data, f, indent=2)

    # 5. Generate a report
    print("5. Generating report...")
    with fs.open('/data/reports/report.txt', 'w') as f:
        f.write("DATA PROCESSING REPORT\n")
        f.write("=====================\n\n")
        f.write(f"Processed {len(data)} records\n\n")

        total_value = sum(item['value'] for item in data)
        f.write(f"Total value: {total_value}\n")
        f.write(f"Average value: {total_value / len(data)}\n\n")

        f.write("Records:\n")
        for item in data:
            f.write(f"  - {item['name']}: {item['value']} (doubled: {item['double_value']})\n")

    # 6. Show the directory structure
    print("\nFinal directory structure:")
    for root, dirs, files in fs.walk('/'):
        print(f"Directory: {root}")
        if dirs:
            print(f"  Subdirectories: {', '.join(dirs)}")
        if files:
            print(f"  Files: {', '.join(files)}")

    # 7. Display the report
    print("\nGenerated report content:")
    print("-" * 30)
    with fs.open('/data/reports/report.txt', 'r') as f:
        print(f.read())
    print("-" * 30)


def concurrent_file_access():