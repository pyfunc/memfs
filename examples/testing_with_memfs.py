#!/usr/bin/env python
"""
Examples of using memfs for testing
"""

import unittest
import json
import os
from memfs import create_fs


class FileProcessor:
    """Example class that processes files."""

    def __init__(self, fs=None):
        """
        Initialize with a filesystem.

        Args:
            fs: Filesystem to use. If None, uses the real OS filesystem.
        """
        self.fs = fs

    def process_config(self, config_path):
        """
        Process a configuration file.

        Args:
            config_path: Path to the configuration file

        Returns:
            dict: Processed configuration
        """
        # Determine which filesystem to use
        if self.fs:
            # Use the provided filesystem (memfs)
            exists = self.fs.exists(config_path)
            if not exists:
                raise FileNotFoundError(f"Config file not found: {config_path}")

            with self.fs.open(config_path, 'r') as f:
                config = json.load(f)
        else:
            # Use the real filesystem
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Config file not found: {config_path}")

            with open(config_path, 'r') as f:
                config = json.load(f)

        # Process the configuration
        if 'debug' not in config:
            config['debug'] = False

        if 'max_items' not in config:
            config['max_items'] = 100

        return config

    def write_output(self, data, output_path):
        """
        Write processed data to an output file.

        Args:
            data: Data to write
            output_path: Path to write to
        """
        # Determine which filesystem to use
        if self.fs:
            # Create directory if it doesn't exist
            output_dir = self.fs.path.dirname(output_path)
            if output_dir and not self.fs.exists(output_dir):
                self.fs.makedirs(output_dir, exist_ok=True)

            # Write to the file
            with self.fs.open(output_path, 'w') as f:
                if isinstance(data, dict):
                    json.dump(data, f, indent=2)
                else:
                    f.write(str(data))
        else:
            # Create directory if it doesn't exist
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            # Write to the file
            with open(output_path, 'w') as f:
                if isinstance(data, dict):
                    json.dump(data, f, indent=2)
                else:
                    f.write(str(data))


class TestFileProcessor(unittest.TestCase):
    """Test cases for FileProcessor using memfs."""

    def setUp(self):
        """Set up the test environment."""
        # Create a virtual filesystem for testing
        self.fs = create_fs()

        # Create test data
        self.config_data = {
            "name": "Test Config",
            "version": "1.0",
            "settings": {
                "timeout": 30,
                "retry": 3
            }
        }

        # Write test configuration to virtual filesystem
        self.fs.makedirs('/config', exist_ok=True)
        with self.fs.open('/config/test.json', 'w') as f:
            json.dump(self.config_data, f)

        # Create processor with virtual filesystem
        self.processor = FileProcessor(fs=self.fs)

    def test_process_config(self):
        """Test processing a configuration file."""
        # Process the config
        result = self.processor.process_config('/config/test.json')

        # Check that the original data is preserved
        self.assertEqual(result["name"], "Test Config")
        self.assertEqual(result["version"], "1.0")
        self.assertEqual(result["settings"]["timeout"], 30)

        # Check that defaults were added
        self.assertFalse(result["debug"])
        self.assertEqual(result["max_items"], 100)

    def test_process_missing_config(self):
        """Test processing a missing configuration file."""
        with self.assertRaises(FileNotFoundError):
            self.processor.process_config('/config/nonexistent.json')

    def test_write_output(self):
        """Test writing output to a file."""
        # Process the config
        config = self.processor.process_config('/config/test.json')

        # Write the processed config
        self.processor.write_output(config, '/output/processed.json')

        # Check that the file was created
        self.assertTrue(self.fs.exists('/output/processed.json'))

        # Verify the content
        with self.fs.open('/output/processed.json', 'r') as f:
            saved_config = json.load(f)

        self.assertEqual(saved_config["name"], "Test Config")
        self.assertEqual(saved_config["debug"], False)
        self.assertEqual(saved_config["max_items"], 100)


def main():
    """Run the demonstration."""
    print("=== Testing with MemFS ===")

    # Run the unit tests
    unittest.main(argv=['first-arg-is-ignored'], exit=False)

    # Show additional example using memfs without unittest
    print("\n=== Manual Testing Example ===")

    # Create virtual filesystem
    fs = create_fs()

    # Create test data
    fs.makedirs('/test/input', exist_ok=True)

    # Create a test configuration
    config = {
        "name": "Manual Test",
        "settings": {
            "value": 42
        }
    }

    with fs.open('/test/input/config.json', 'w') as f:
        json.dump(config, f)

    # Create processor and process the config
    processor = FileProcessor(fs=fs)

    try:
        processed = processor.process_config('/test/input/config.json')
        print(f"Processed config: {processed}")

        # Write output
        processor.write_output(processed, '/test/output/result.json')
        print(f"Output written to: /test/output/result.json")

        # Show the directory structure
        print("\nVirtual filesystem contents:")
        for root, dirs, files in fs.walk('/'):
            print(f"Directory: {root}")
            if dirs:
                print(f"  Subdirectories: {', '.join(dirs)}")
            if files:
                print(f"  Files: {', '.join(files)}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()