#!/usr/bin/env python
"""
Advanced usage examples for memfs
"""

import time
import json
import csv
import io
import threading
import concurrent.futures

from memfs import create_fs
from memfs.api import DynamicgRPCComponent, PipelineOrchestrator


def data_processing_pipeline():
    """Demonstrate a data processing pipeline using memfs."""
    print("\n=== Data Processing Pipeline ===")

    # Create a virtual filesystem
    fs = create_fs()

    # Create necessary directories
    fs.makedirs('/data/raw', exist_ok=True)
    fs.makedirs('/data/processed', exist_ok=True)
    fs.makedirs('/data/reports', exist_ok=True)

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
    """Demonstrate concurrent access to the virtual filesystem."""
    print("\n=== Concurrent File Access ===")

    # Create a virtual filesystem
    fs = create_fs()

    # Create a file to be accessed concurrently
    fs.writefile('/shared.txt', 'Initial content\n')

    def worker(worker_id, iterations=5):
        """Worker function that appends to the shared file."""
        for i in range(iterations):
            # Read current content
            with fs.open('/shared.txt', 'r') as f:
                content = f.read()

            # Append to the file
            with fs.open('/shared.txt', 'a') as f:
                f.write(f"Worker {worker_id}, iteration {i}\n")

            # Simulate some processing
            time.sleep(0.01)

    # Start multiple threads
    print("Starting 5 concurrent workers...")
    threads = []
    for i in range(5):
        thread = threading.Thread(target=worker, args=(i,))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Show final content
    print("\nFinal file content:")
    print("-" * 30)
    with fs.open('/shared.txt', 'r') as f:
        print(f.read())
    print("-" * 30)


def grpc_service_pipeline():
    """Demonstrate using gRPC service pipeline with memfs."""
    print("\n=== gRPC Service Pipeline ===")

    # Define transformation functions
    def json_to_html(json_data):
        """Convert JSON data to HTML."""
        if not isinstance(json_data, dict):
            # Convert string to dict if necessary
            json_data = json.loads(json_data) if isinstance(json_data, str) else json_data

        html = """
        <html>
        <head>
            <title>Data Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                h1 { color: #333; }
            </style>
        </head>
        <body>
            <h1>Data Report</h1>
            <table>
                <tr>
                    <th>Key</th>
                    <th>Value</th>
                </tr>
        """

        for key, value in json_data.items():
            html += f"""
                <tr>
                    <td>{key}</td>
                    <td>{value}</td>
                </tr>
            """

        html += """
            </table>
        </body>
        </html>
        """

        return html

    def add_metadata(data):
        """Add metadata to the data."""
        if isinstance(data, dict):
            data['timestamp'] = time.time()
            data['generated_by'] = 'memfs example'
        return data

    # Create virtual filesystem
    fs = create_fs()

    # Create virtual directories for services
    fs.makedirs('/proto/metadata', exist_ok=True)
    fs.makedirs('/proto/converter', exist_ok=True)
    fs.makedirs('/generated/metadata', exist_ok=True)
    fs.makedirs('/generated/converter', exist_ok=True)

    # Create data
    sample_data = {
        "name": "Example Report",
        "value": 1000,
        "category": "Demo"
    }

    try:
        # Create components
        print("Creating pipeline components...")
        metadata_component = DynamicgRPCComponent(
            add_metadata,
            proto_dir="/proto/metadata",
            generated_dir="/generated/metadata",
            port=50051
        )

        converter_component = DynamicgRPCComponent(
            json_to_html,
            proto_dir="/proto/converter",
            generated_dir="/generated/converter",
            port=50052
        )

        # Create pipeline
        pipeline = PipelineOrchestrator()
        pipeline.add_component(metadata_component)
        pipeline.add_component(converter_component)

        # Execute pipeline
        print("Executing pipeline...")
        result = pipeline.execute_pipeline(sample_data)

        # Save result
        fs.writefile('/output/result.html', result)

        # Show result summary
        print("\nPipeline execution completed")
        print(f"Input data: {sample_data}")
        print(f"Output type: {type(result)}")
        print(f"Output length: {len(result)} characters")
        print("Output sample (first 100 chars):")
        print(result[:100] + "...")

    except Exception as e:
        print(f"Error during pipeline execution: {e}")


def parallel_processing():
    """Demonstrate parallel processing with memfs."""
    print("\n=== Parallel Processing ===")

    # Create a virtual filesystem
    fs = create_fs()

    # Create test data
    fs.makedirs('/parallel/input', exist_ok=True)
    fs.makedirs('/parallel/output', exist_ok=True)

    # Create 10 data files
    for i in range(10):
        data = {
            "id": i,
            "name": f"Item {i}",
            "values": [j * i for j in range(5)]
        }
        fs.writefile(f'/parallel/input/data_{i}.json', json.dumps(data))

    def process_file(filename):
        """Process a single file."""
        # Read input file
        input_path = f'/parallel/input/{filename}'
        with fs.open(input_path, 'r') as f:
            data = json.loads(f.read())

        # Process data
        data['processed'] = True
        data['sum'] = sum(data['values'])
        data['average'] = data['sum'] / len(data['values']) if data['values'] else 0

        # Write output file
        output_path = f'/parallel/output/processed_{filename}'
        with fs.open(output_path, 'w') as f:
            f.write(json.dumps(data, indent=2))

        return data['id'], data['sum']

    # Get all input files
    input_files = fs.listdir('/parallel/input')

    # Process files in parallel
    print(f"Processing {len(input_files)} files in parallel...")
    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_to_file = {executor.submit(process_file, filename): filename for filename in input_files}
        for future in concurrent.futures.as_completed(future_to_file):
            filename = future_to_file[future]
            try:
                file_id, file_sum = future.result()
                results.append((file_id, file_sum))
                print(f"Processed file {filename}: id={file_id}, sum={file_sum}")
            except Exception as e:
                print(f"Error processing {filename}: {e}")

    # Show results
    print("\nAll files processed.")
    print(f"Files in output directory: {fs.listdir('/parallel/output')}")

    # Compute grand total
    total_sum = sum(result[1] for result in results)
    print(f"Total sum across all files: {total_sum}")


def main():
    """Run all examples."""
    print("MEMFS ADVANCED EXAMPLES")
    print("======================")

    # Uncomment the examples you want to run
    data_processing_pipeline()
    concurrent_file_access()
    # Uncomment the following if you have all dependencies installed
    # grpc_service_pipeline()
    parallel_processing()


if __name__ == "__main__":
    main()