#!/usr/bin/env python
# src/memfs/api.py

"""
Moduł api implementuje framework dla funkcji API z wirtualnym systemem plików.
"""

import sys
import inspect
import importlib
import json
from typing import Any, Dict, List, Optional, Callable, Type
import os
import tempfile

import logging
import grpc
from concurrent import futures
import grpc_tools.protoc
from google.protobuf.struct_pb2 import Struct
import google.protobuf
import time
import threading

from memfs import create_fs

# Tworzymy wirtualny system plików - dostępny dla wszystkich użytkowników modułu
fs = create_fs()

class DynamicgRPCComponent:
    """
    Dynamic gRPC component for the pipeline.
    """

    def __init__(self, transform_func: Callable, proto_dir: str, generated_dir: str, port: int):
        """
        Initialize the DynamicgRPCComponent.

        Args:
            transform_func (Callable): The transformation function.
            proto_dir (str): Directory for proto files.
            generated_dir (str): Directory for generated code.
            port (int): The port for the gRPC server.
        """
        self.transform_func = transform_func
        self.proto_dir = proto_dir
        self.generated_dir = generated_dir
        self.logger = logging.getLogger(__name__)
        self.port = port
        self.server = None

        # Musimy wygenerować i skompilować kod gRPC przed załadowaniem modułu
        config = ApiFuncConfig()
        framework = ApiFuncFramework(config)
        framework.register_function(self.transform_func, self.proto_dir, self.generated_dir)

    def process(self, data: Any) -> Any:
        """
        Process the data using the transformation function.

        Args:
            data (Any): The input data.

        Returns:
            Any: The processed data.
        """
        return self.transform_func(data)

    def start_grpc_server(self):
        """
        Start the gRPC server for this component.

        Returns:
            grpc.Server: The started gRPC server.
        """
        config = ApiFuncConfig(port=self.port)
        framework = ApiFuncFramework(config)
        self.server = framework.start_server(self.transform_func, self.proto_dir, self.generated_dir, self.port)
        return self.server


class PipelineOrchestrator:
    """
    Orchestrates the pipeline of components.
    """

    def __init__(self):
        """
        Initialize the PipelineOrchestrator.
        """
        self.components: List[DynamicgRPCComponent] = []
        self.servers: List[grpc.Server] = []

    def add_component(self, component: DynamicgRPCComponent):
        """
        Add a component to the pipeline.

        Args:
            component (DynamicgRPCComponent): The component to add.
        """
        self.components.append(component)
        return self

    def execute_pipeline(self, initial_data: Any):
        """
        Execute the pipeline.

        Args:
            initial_data (Any): The initial data.

        Returns:
            Any: The result of the pipeline.
        """
        current_data = initial_data

        for component in self.components:
            current_data = component.process(current_data)

        return current_data

    def start_servers(self):
        """
        Start all gRPC servers for all components.

        Returns:
            List[grpc.Server]: List of started servers.
        """
        for component in self.components:
            server = component.start_grpc_server()
            self.servers.append(server)
        return self.servers

    def stop_servers(self):
        """
        Stop all gRPC servers.
        """
        for server in self.servers:
            server.stop(0)


def json_to_html(json_data: Dict) -> str:
    """
    Transformacja JSON do HTML

    Args:
        json_data (Dict): Dane JSON

    Returns:
        str: Wygenerowany HTML
    """
    from jinja2 import Template

    html_template = """
    <html>
    <body>
        <h1>Raport</h1>
        <table>
            {% for key, value in data.items() %}
            <tr>
                <td>{{ key }}</td>
                <td>{{ value }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """

    template = Template(html_template)
    return template.render(data=json_data)


def html_to_pdf(html_content: str) -> bytes:
    """
    Konwersja HTML do PDF

    Args:
        html_content (str): Treść HTML

    Returns:
        bytes: Zawartość PDF
    """
    import weasyprint
    return weasyprint.HTML(string=html_content).write_pdf()


def example_usage(output_file: str = 'raport.pdf'):
    """
    Przykładowe użycie modularnego frameworka pipeline

    Args:
        output_file (str, optional): Nazwa pliku wyjściowego. Defaults to 'raport.pdf'.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info("Starting the apifunc example pipeline with two services...")

    sample_data = {
        "nazwa": "Przykładowy Raport",
        "data": "2023-11-20",
        "wartość": 123.45
    }

    # Tworzymy wirtualne ścieżki
    proto_dir_json_html = "/proto/json_html"
    generated_dir_json_html = "/generated/json_html"
    proto_dir_html_pdf = "/proto/html_pdf"
    generated_dir_html_pdf = "/generated/html_pdf"

    # Upewniamy się, że katalogi istnieją w wirtualnym systemie plików
    fs.makedirs(proto_dir_json_html, exist_ok=True)
    fs.makedirs(generated_dir_json_html, exist_ok=True)
    fs.makedirs(proto_dir_html_pdf, exist_ok=True)
    fs.makedirs(generated_dir_html_pdf, exist_ok=True)

    logger.info(f"Proto files directory: {proto_dir_json_html}")
    logger.info(f"Generated code directory: {generated_dir_json_html}")
    logger.info(f"Proto files directory: {proto_dir_html_pdf}")
    logger.info(f"Generated code directory: {generated_dir_html_pdf}")

    # Tworzenie komponentów
    json_to_html_component = DynamicgRPCComponent(json_to_html, proto_dir=proto_dir_json_html,
                                                  generated_dir=generated_dir_json_html, port=50051)
    html_to_pdf_component = DynamicgRPCComponent(html_to_pdf, proto_dir=proto_dir_html_pdf,
                                                 generated_dir=generated_dir_html_pdf, port=50052)

    # Tworzenie orkiestratora
    pipeline = PipelineOrchestrator()

    # Dodawanie komponentów do potoku
    pipeline.add_component(json_to_html_component).add_component(html_to_pdf_component)

    # Wykonanie potoku
    result = pipeline.execute_pipeline(sample_data)

    # Zapisujemy wynik w wirtualnym systemie plików
    virtual_output_path = f"/output/{output_file}"
    fs.makedirs("/output", exist_ok=True)

    with fs.open(virtual_output_path, 'wb') as f:
        f.write(result)

    logger.info(f"Raport zapisany do wirtualnego pliku: {virtual_output_path}")

    # Opcjonalnie możemy zapisać do rzeczywistego systemu plików
    with open(output_file, 'wb') as f:
        f.write(result)

    logger.info(f"Raport zapisany do rzeczywistego pliku: {output_file}")

    # Wyświetlamy zawartość wirtualnego systemu plików
    logger.info("Zawartość wirtualnego systemu plików:")
    for root, dirs, files in fs.walk("/"):
        logger.info(f"Katalog: {root}")
        for d in dirs:
            logger.info(f"  Podkatalog: {d}")
        for f in files:
            logger.info(f"  Plik: {f}")

    # Start the servers in separate threads
    logger.info("Starting gRPC servers...")
    pipeline.start_servers()

    logger.info(f"Starting JSON-to-HTML server on port 50051")
    logger.info(f"Starting HTML-to-PDF server on port 50052")

    # Run the servers in background threads
    def run_server(server, name):
        try:
            server.wait_for_termination()
        except Exception as e:
            logger.error(f"{name} server error: {e}")

    threads = []
    for i, server in enumerate(pipeline.servers):
        thread = threading.Thread(target=run_server, args=(server, f"Server {i + 1}"))
        threads.append(thread)
        thread.start()
        logger.info(f"Server {i + 1} running in background thread")

    try:
        # Keep the main thread alive for a few seconds to demonstrate
        time.sleep(5)
        logger.info("Shutting down servers after demonstration period...")
    except KeyboardInterrupt:
        logger.info("Interrupted, shutting down services...")
    finally:
        pipeline.stop_servers()
        for thread in threads:
            thread.join()
        logger.info("All services have been shut down.")
        """
        Moduł api implementuje framework dla funkcji API z wirtualnym systemem plików.
        """


import sys
import inspect
import importlib
import json
from typing import Any, Dict, List, Optional, Callable, Type
import os
import tempfile

import logging
import grpc
from concurrent import futures
import grpc_tools.protoc
from google.protobuf.struct_pb2 import Struct
import google.protobuf
import time
import threading

from memfs import create_fs

# Tworzymy wirtualny system plików
fs = create_fs()


class ApiFuncConfig:
    """Configuration class for ApiFuncFramework."""

    def __init__(self, proto_dir: str = None, generated_dir: str = None, port: int = 50051):
        """
        Initialize ApiFuncConfig.

        Args:
            proto_dir (str): Directory for proto files.
            generated_dir (str): Directory for generated code.
            port (int): Port for the gRPC server.
        """
        # Używamy wirtualnych ścieżek
        self.proto_dir = proto_dir or "/proto"
        self.generated_dir = generated_dir or "/generated"
        self.port = port


class ApiFuncFramework:
    """Framework for creating gRPC services from functions."""

    def __init__(self, config: ApiFuncConfig):
        """
        Initialize ApiFuncFramework.

        Args:
            config (ApiFuncConfig): Configuration object.
        """
        self.config = config
        self.registered_functions = {}
        self.logger = logging.getLogger(__name__)

    def register_function(self, func: Callable, proto_dir: str, generated_dir: str):
        """
        Register a function to be exposed as a gRPC service.

        Args:
            func (Callable): The function to register.
            proto_dir (str): Directory for proto files.
            generated_dir (str): Directory for generated code.
        """
        self.logger.info(f"Registering function: {func.__module__}.{func.__name__}")

        self.registered_functions[func.__name__] = func
        self._generate_proto(func, proto_dir)
        self._compile_proto(func, proto_dir, generated_dir)

    def _generate_proto(self, func: Callable, proto_dir: str):
        """
        Generate a .proto file for the given function.

        Args:
            func (Callable): The function to generate a .proto file for.
            proto_dir (str): Directory for proto files.
        """
        # Tworzymy katalog w wirtualnym systemie plików
        fs.makedirs(proto_dir, exist_ok=True)
        proto_file_path = fs.path.join(proto_dir, f"{func.__name__}.proto")
        self.logger.info(f"Generated proto file: {proto_file_path}")

        # Zapisujemy plik w wirtualnym systemie plików
        with fs.open(proto_file_path, "w") as f:
            f.write(self._generate_proto_content(func))

    def _generate_proto_content(self, func: Callable) -> str:
        """
        Generate the content of the .proto file.

        Args:
            func (Callable): The function to generate a .proto file for.

        Returns:
            str: The content of the .proto file.
        """
        service_name = func.__name__.title().replace("_", "")
        proto_content = f"""
        syntax = "proto3";
        package apifunc;

        import "google/protobuf/struct.proto";

        service {service_name} {{
            rpc Transform (google.protobuf.Struct) returns (google.protobuf.Struct) {{}}
        }}
        """
        return proto_content

    def _compile_proto(self, func: Callable, proto_dir: str, generated_dir: str):
        """
        Compile the .proto file to generate gRPC code.

        Args:
            func (Callable): The function to compile the .proto file for.
            proto_dir (str): Directory for proto files.
            generated_dir (str): Directory for generated code.
        """
        # Ścieżki w wirtualnym systemie plików
        proto_file_path = fs.path.join(proto_dir, f"{func.__name__}.proto")
        fs.makedirs(generated_dir, exist_ok=True)
        self.logger.info(f"Generated gRPC code for: {func.__name__}")

        # Aby skompilować plik proto, musimy tymczasowo zapisać go na rzeczywistym dysku
        # ponieważ grpc_tools.protoc pracuje na rzeczywistym systemie plików
        with tempfile.TemporaryDirectory() as temp_proto_dir, tempfile.TemporaryDirectory() as temp_generated_dir:
            # Kopiujemy zawartość pliku proto z wirtualnego systemu plików do rzeczywistego
            with fs.open(proto_file_path, "r") as vfile:
                proto_content = vfile.read()
                temp_file_path = os.path.join(temp_proto_dir, f"{func.__name__}.proto")
                with open(temp_file_path, "w") as rfile:
                    rfile.write(proto_content)

            # Get the path to the directory containing struct.proto
            protobuf_include = os.path.dirname(google.protobuf.__file__)

            protoc_args = [
                'grpc_tools.protoc',
                f'-I{temp_proto_dir}',  # Tymczasowy katalog fizyczny
                f'-I{protobuf_include}',
                f'--python_out={temp_generated_dir}',
                f'--grpc_python_out={temp_generated_dir}',
                temp_file_path
            ]

            # Execute protoc command
            try:
                grpc_tools.protoc.main(protoc_args)
            except SystemExit as e:
                if e.code != 0:
                    raise RuntimeError(f"protoc failed with exit code {e.code}") from e

            # Kopiujemy wygenerowane pliki z powrotem do wirtualnego systemu plików
            generated_files = [
                f"{func.__name__}_pb2.py",
                f"{func.__name__}_pb2_grpc.py"
            ]

            for file in generated_files:
                with open(os.path.join(temp_generated_dir, file), "r") as rfile:
                    with fs.open(fs.path.join(generated_dir, file), "w") as vfile:
                        vfile.write(rfile.read())

    def _create_server(self):
        """
        Create a gRPC server.

        Returns:
            grpc.Server: The created gRPC server.
        """
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        return server

    def start_server(self, func: Callable, proto_dir: str, generated_dir: str, port: int):
        """
        Start the gRPC server.

        Args:
            func (Callable): The function to start the server for.
            proto_dir (str): Directory for proto files.
            generated_dir (str): Directory for generated code.
            port (int): The port to listen on.
        """
        self.logger.info(f"Starting server for: {func.__name__}")
        server = self._create_server()
        self._add_servicer_to_server(server, func, generated_dir)
        server.add_insecure_port(f'[::]:{port}')
        server.start()
        return server

    def _add_servicer_to_server(self, server, func: Callable, generated_dir: str):
        """
        Add the servicer to the gRPC server.

        Args:
            server (grpc.Server): The gRPC server.
            func (Callable): The function to add the servicer for.
            generated_dir (str): Directory for generated code.
        """
        # Musimy tymczasowo skopiować wygenerowane pliki do rzeczywistego systemu plików
        with tempfile.TemporaryDirectory() as temp_module_dir:
            # Kopiujemy pliki z wirtualnego systemu plików do tymczasowego katalogu
            generated_files = [
                f"{func.__name__}_pb2.py",
                f"{func.__name__}_pb2_grpc.py"
            ]

            for file in generated_files:
                virtual_path = fs.path.join(generated_dir, file)
                real_path = os.path.join(temp_module_dir, file)

                with fs.open(virtual_path, "r") as vfile:
                    with open(real_path, "w") as rfile:
                        rfile.write(vfile.read())

            # Add the temporary directory to sys.path
            sys.path.insert(0, temp_module_dir)

            # Importujemy wygenerowany moduł
            module_name = f"{func.__name__}_pb2_grpc"
            module_path = os.path.join(temp_module_dir, f"{func.__name__}_pb2_grpc.py")
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            servicer_class_name = f"{func.__name__.title().replace('_', '')}Servicer"
            servicer_class = getattr(module, servicer_class_name)

            add_to_server_func_name = f"add_{func.__name__.title().replace('_', '')}Servicer_to_server"
            add_to_server_func = getattr(module, add_to_server_func_name)

            class Servicer(servicer_class):
                def Transform(self, request, context):
                    input_data = json.loads(request.SerializeToString())
                    output_data = func(input_data)
                    response = Struct()
                    response.update(output_data)
                    return response

            add_to_server_func(Servicer(), server)