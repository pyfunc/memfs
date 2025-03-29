#!/usr/bin/env python
"""
Tests for memfs.api module
"""

import os
import json
import threading
import time
import tempfile
import grpc
import pytest
from unittest.mock import patch, MagicMock, mock_open
from google.protobuf.struct_pb2 import Struct

from memfs.api import (
    ApiFuncConfig,
    ApiFuncFramework,
    DynamicgRPCComponent,
    PipelineOrchestrator
)
from memfs.memfs import _FS_DATA  # Import directly from memfs.memfs
from memfs import create_fs

# Create a filesystem instance for tests
fs = create_fs()


def simple_transform(data):
    """Simple transformation function for testing."""
    if isinstance(data, dict):
        data['transformed'] = True
    return data


# Fix fixture issue by making these regular functions instead of test functions
def data_to_upper(data):
    """Convert all string values in a dict to uppercase."""
    if isinstance(data, dict):
        return {k.upper(): v.upper() if isinstance(v, str) else v for k, v in data.items()}
    return data


def add_prefix(data):
    """Add prefix to all string values in a dict."""
    if isinstance(data, dict):
        return {k: f"PREFIX_{v}" if isinstance(v, str) else v for k, v in data.items()}
    return data


class TestApiFuncConfig:
    """Test ApiFuncConfig class."""

    def test_init_default(self):
        """Test default initialization."""
        config = ApiFuncConfig()
        assert config.proto_dir == "/proto"
        assert config.generated_dir == "/generated"
        assert config.port == 50051

    def test_init_custom(self):
        """Test custom initialization."""
        config = ApiFuncConfig(
            proto_dir="/custom/proto",
            generated_dir="/custom/generated",
            port=12345
        )
        assert config.proto_dir == "/custom/proto"
        assert config.generated_dir == "/custom/generated"
        assert config.port == 12345


class TestApiFuncFramework:
    """Test ApiFuncFramework class."""

    def setup_method(self):
        """Set up test environment."""
        # Reset the filesystem state
        for key in list(_FS_DATA['files'].keys()):
            del _FS_DATA['files'][key]

        for key in list(_FS_DATA['dirs']):
            if key != '/':
                _FS_DATA['dirs'].remove(key)

        self.config = ApiFuncConfig()
        self.framework = ApiFuncFramework(self.config)
        self.proto_dir = "/test_proto"
        self.generated_dir = "/test_generated"
        fs.makedirs(self.proto_dir, exist_ok=True)
        fs.makedirs(self.generated_dir, exist_ok=True)

    @patch('memfs.api.grpc_tools.protoc.main')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data="# Mock generated content")
    def test_register_function(self, mock_file, mock_exists, mock_protoc):
        """Test registering a function."""
        # Mock protoc and file operations
        mock_protoc.return_value = 0
        mock_exists.return_value = True  # Simulate files existing

        # Test registering a function
        self.framework.register_function(simple_transform, self.proto_dir, self.generated_dir)

        # Check that the function was registered
        assert 'simple_transform' in self.framework.registered_functions

        # Check that proto file was generated
        proto_file_path = fs.path.join(self.proto_dir, "simple_transform.proto")
        assert fs.exists(proto_file_path)

        # Check proto file content
        with fs.open(proto_file_path, 'r') as f:
            content = f.read()
            assert "service SimpleTransform" in content
            assert "rpc Transform" in content

    @patch('memfs.api.grpc_tools.protoc.main')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data="# Mock generated content")
    @patch('memfs.api.grpc.server')
    @patch('memfs.api.importlib.util.spec_from_file_location')
    @patch('memfs.api.importlib.util.module_from_spec')
    def test_start_server(self, mock_module_from_spec, mock_spec_from_file, mock_server,
                          mock_file, mock_exists, mock_protoc):
        """Test starting a server."""
        # Setup mocks
        mock_protoc.return_value = 0
        mock_exists.return_value = True  # Simulate files existing

        mock_server_instance = MagicMock()
        mock_server.return_value = mock_server_instance

        # Setup module loading mocks
        mock_spec_instance = MagicMock()
        mock_spec_from_file.return_value = mock_spec_instance

        mock_module_instance = MagicMock()
        mock_module_instance.SimpleTransformServicer = type('SimpleTransformServicer', (), {})
        mock_module_instance.add_SimpleTransformServicer_to_server = MagicMock()
        mock_module_from_spec.return_value = mock_module_instance

        # Register and start server
        self.framework.register_function(simple_transform, self.proto_dir, self.generated_dir)

        # Start server
        server = self.framework.start_server(simple_transform, self.proto_dir, self.generated_dir, 50051)

        # Check that server was started
        assert server == mock_server_instance
        mock_server_instance.add_insecure_port.assert_called_once_with('[::]:{}'.format(50051))
        mock_server_instance.start.assert_called_once()


class TestDynamicgRPCComponent:
    """Test DynamicgRPCComponent class."""

    def setup_method(self):
        """Set up test environment."""
        # Reset the filesystem state
        for key in list(_FS_DATA['files'].keys()):
            del _FS_DATA['files'][key]

        for key in list(_FS_DATA['dirs']):
            if key != '/':
                _FS_DATA['dirs'].remove(key)

        self.proto_dir = "/test_proto_component"
        self.generated_dir = "/test_generated_component"
        fs.makedirs(self.proto_dir, exist_ok=True)
        fs.makedirs(self.generated_dir, exist_ok=True)

    @patch('memfs.api.ApiFuncFramework.register_function')
    def test_init(self, mock_register):
        """Test initialization."""
        # Initialize component
        component = DynamicgRPCComponent(
            simple_transform,
            self.proto_dir,
            self.generated_dir,
            50051
        )

        # Check component properties
        assert component.transform_func == simple_transform
        assert component.proto_dir == self.proto_dir
        assert component.generated_dir == self.generated_dir
        assert component.port == 50051

        # Check that register_function was called
        mock_register.assert_called_once()

    def test_process(self):
        """Test processing data."""
        # Initialize component with mocked register_function
        with patch('memfs.api.ApiFuncFramework.register_function'):
            component = DynamicgRPCComponent(
                simple_transform,
                self.proto_dir,
                self.generated_dir,
                50051
            )

        # Process data
        data = {'key': 'value'}
        result = component.process(data)

        # Check result
        assert result == {'key': 'value', 'transformed': True}

    @patch('memfs.api.ApiFuncFramework.start_server')
    def test_start_grpc_server(self, mock_start_server):
        """Test starting gRPC server."""
        # Setup mock
        mock_server = MagicMock()
        mock_start_server.return_value = mock_server

        # Initialize component with mocked register_function
        with patch('memfs.api.ApiFuncFramework.register_function'):
            component = DynamicgRPCComponent(
                simple_transform,
                self.proto_dir,
                self.generated_dir,
                50051
            )

        # Start server
        server = component.start_grpc_server()

        # Check that server was started
        assert server == mock_server
        mock_start_server.assert_called_once()


class TestPipelineOrchestrator:
    """Test PipelineOrchestrator class."""

    def setup_method(self):
        """Set up test environment."""
        self.orchestrator = PipelineOrchestrator()

        # Create mocked components
        self.component1 = MagicMock()
        self.component1.process.side_effect = data_to_upper

        self.component2 = MagicMock()
        self.component2.process.side_effect = add_prefix

    def test_add_component(self):
        """Test adding a component."""
        # Add components
        result = self.orchestrator.add_component(self.component1)

        # Check that component was added
        assert self.orchestrator.components == [self.component1]

        # Check that method returns self for chaining
        assert result == self.orchestrator

    def test_execute_pipeline(self):
        """Test executing the pipeline."""
        # Add components
        self.orchestrator.add_component(self.component1)
        self.orchestrator.add_component(self.component2)

        # Execute pipeline
        data = {'name': 'test', 'value': 123}
        result = self.orchestrator.execute_pipeline(data)

        # Check that components were called in sequence
        self.component1.process.assert_called_once_with(data)
        self.component2.process.assert_called_once()

        # Check result - should be uppercase then prefixed
        assert result == {'NAME': 'PREFIX_TEST', 'VALUE': 123}

    def test_start_servers(self):
        """Test starting servers."""
        # Add components
        self.orchestrator.add_component(self.component1)
        self.orchestrator.add_component(self.component2)

        # Setup mocks
        server1 = MagicMock()
        server2 = MagicMock()
        self.component1.start_grpc_server.return_value = server1
        self.component2.start_grpc_server.return_value = server2

        # Start servers
        servers = self.orchestrator.start_servers()

        # Check that servers were started
        self.component1.start_grpc_server.assert_called_once()
        self.component2.start_grpc_server.assert_called_once()
        assert self.orchestrator.servers == [server1, server2]
        assert servers == [server1, server2]

    def test_stop_servers(self):
        """Test stopping servers."""
        # Add mock servers
        server1 = MagicMock()
        server2 = MagicMock()
        self.orchestrator.servers = [server1, server2]

        # Stop servers
        self.orchestrator.stop_servers()

        # Check that servers were stopped
        server1.stop.assert_called_once_with(0)
        server2.stop.assert_called_once_with(0)