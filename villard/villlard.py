import importlib
import os
import sys
from datetime import datetime
from typing import Any, Dict, List

import colorama
import yaml
from tabulate import tabulate
from termcolor import colored

from .io import *

# Following prefixes are used to identify if the value is a reference
# to another node's output or to one of data in catalog.
REFERENCE_PREFIX = "ref::"
DATA_CATALOG_PREFIX = "data::"


class Villard:
    def __new__(cls):
        # Create a new instance of the class as a singleton.
        if not hasattr(cls, "instance"):
            cls.instance = super(Villard, cls).__new__(cls)

        cls.data_catalog = dict()
        cls.node_func_map = dict()
        cls.node_output_map = dict()
        cls.execution_nodes_in_out_counter = dict()
        cls.execution_nodes = dict()

        cls.supported_data_types = ["DT_PICKLE", "DT_PANDAS_DATAFRAME"]
        cls.supported_data_writers = [PickleWriter, PandasWriter]
        cls.supported_data_readers = [PickleReader, PandasReader]

        # Following dictionaries are to map catalog's data type string to the
        # suitable writer/reader.
        cls.type_to_reader_map = {
            k: v for k, v in zip(cls.supported_data_types, cls.supported_data_readers)
        }
        cls.type_to_writer_map = {
            k: v for k, v in zip(cls.supported_data_types, cls.supported_data_writers)
        }

        # For terminal output coloring
        colorama.init()

        return cls.instance

    def _visit_and_execute_recursively(cls, name: str, node, stats_table: List) -> None:
        """Traverse the execution graph recursively and execute the nodes.

        Args:
            name: Name of the node.
            node: A dict representing an "execution node".
            stats_table: A list of lists to store the execution stats.

            Returns:
                None

        """

        if node["executed"]:
            return

        # Before executing function of current node, execute all the nodes that are
        # dependencies of the current node recursively.
        for prev in node["prevs"]:
            cls._visit_and_execute_recursively(
                prev, cls.execution_nodes[prev], stats_table
            )

        # This kwargs is based on the definition in the config file.
        # So, some values might be not the actual values (e.g., reference to
        # catalog's data or other node's output). We need to convert them to
        # the actual values accordingly.
        kwargs = node["kwargs"]

        # Convert kwargs ref to actual values before execution
        actual_kwargs = kwargs
        for k, v in actual_kwargs.items():
            if isinstance(v, str):
                # When referencing output of another node
                if v.startswith(REFERENCE_PREFIX):
                    actual_kwargs[k] = cls.node_output_map[
                        v.lstrip(REFERENCE_PREFIX).strip()
                    ]

                # When referencing data from the data catalog
                if v.startswith(DATA_CATALOG_PREFIX):
                    data_catalog_key = v.lstrip(DATA_CATALOG_PREFIX).strip()
                    actual_kwargs[k] = cls.read_data(data_catalog_key=data_catalog_key)

        # ---------------------- ACTUAL EXECUTION ----------------------
        # The actual kwargs is ready, call node function accordingly.
        # Keep track current run's statistics.
        print(colored(f"  Executing `{name}`...", "yellow"))
        tic = datetime.now()
        node["func"](**actual_kwargs)
        node["executed"] = True
        toc = datetime.now()
        print(colored(f"⦿ Completed `{name}`", "green"))
        # --------------------------------------------------------------

        execution_time = toc - tic
        dependencies = node["prevs"]

        stats_table.append((name, dependencies, execution_time))

    def _get_catalog_data_info(cls, data_catalog_key) -> Dict:
        try:
            data_info = cls.data_catalog[data_catalog_key]
        except KeyError:
            msg = f"Data catalog key `{data_catalog_key}` is not defined."
            print(colored("Error:", "red"), colored(msg, "red"))
            exit(1)

        return data_info

    def _get_catalog_data_type(
        cls, data_info: Dict[str, Any], data_catalog_key: str
    ) -> str:
        try:
            data_type = data_info["type"]
        except KeyError:
            msg = f"Cannot determine the type of data `{data_catalog_key}`."
            print(colored("Error:", "red"), colored(msg, "red"))
            exit(1)

        if not data_type in cls.supported_data_types:
            msg = f"Data type `{data_type}` is not supported."
            print(colored("Error:", "red"), colored(msg, "red"))
            exit(1)

        return data_type

    def node(cls, name: str):
        """This decorator registers a python function as a node."""

        def decorator_node(func):
            def inner(*args, **kwargs):
                result = func(*args, **kwargs)
                cls.node_output_map[name] = result
                return result

            cls.node_func_map[name] = inner

        return decorator_node

    def run(cls, config: str):
        """
        Execute a single experiment run. Each run result will be stored in a predefined
        location.

        The flow of execution is based on a directed graph. Each node is a python function.
        Each node has a list of dependencies. The dependencies are the names of the nodes that
        are executed before the current node. The graph is traversed in topological order.
        The graph structure is defined based on config's `pipeline_definition`.

        Args:
            config: Path to the config file.

        """

        # Load configurations to initialize pipeline definitions and node implementation
        # modules
        with open(config, "r") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
            cls.pipeline_definition = config["pipeline_definition"]
            cls.node_implementation_modules = config["node_implementation_modules"]

        if "data_catalog" in config:
            cls.data_catalog = config["data_catalog"]

        # import the modules containing the definition of each node.
        # The definitions will be referred by the matching ones in the
        # configuration.
        for module in cls.node_implementation_modules:
            try:
                sys.path.append(os.getcwd())
                importlib.import_module(module)
            except ModuleNotFoundError as e:
                msg = f"Cannot import module {module}: {e}. Please check the configuration file."
                print(colored("Error:", "red"), colored(msg, "red"))
                exit(1)

        # To keep track nodes' incoming and outgoing edge counts
        for name in cls.pipeline_definition:
            cls.execution_nodes_in_out_counter[name] = dict()
            cls.execution_nodes_in_out_counter[name]["in"] = 0
            cls.execution_nodes_in_out_counter[name]["out"] = 0

        # Build execution graph
        for name, kwargs in cls.pipeline_definition.items():
            execution_node = {
                "func": cls.node_func_map[name],
                "kwargs": kwargs,
                "prevs": [],
                "executed": False,
            }

            def check_ref_recursively(kwargs):
                # if value starts with REFERENCE_PREFIX, key is detected. It means that
                # the node refers to another node. Add the referenced node into the
                # dependency list (`prevs`) of the current node.
                for k, v in kwargs.items():
                    if isinstance(v, str):
                        if v.startswith(REFERENCE_PREFIX):
                            prev_name = v.lstrip(REFERENCE_PREFIX)
                            execution_node["prevs"].append(prev_name)
                            cls.execution_nodes_in_out_counter[name]["in"] += 1
                            cls.execution_nodes_in_out_counter[prev_name]["out"] += 1
                    elif isinstance(v, dict):
                        check_ref_recursively(v)

            check_ref_recursively(kwargs)
            cls.execution_nodes[name] = execution_node

        # Collect output nodes: the ones that have no outging edges
        output_nodes = {
            node: v
            for node, v in cls.execution_nodes.items()
            if cls.execution_nodes_in_out_counter[node]["out"] == 0
        }

        # Keep track execution statistics. This will be displayed as table in the end
        # of the execution.
        stats_table = []
        stats_table_headers = ["Node", "Dependencies", "Execution Time"]

        for output_node_name in output_nodes:
            cls._visit_and_execute_recursively(
                output_node_name, cls.execution_nodes[output_node_name], stats_table
            )

        # Print the execution statistics
        print(
            "\n"
            + tabulate(
                stats_table,
                headers=stats_table_headers,
                tablefmt="fancy_grid",
            )
        )

    def read_data(cls, data_catalog_key: str) -> Any:
        """
        Read data based on the data catalog.

        Args:
            data_catalog_key: There key referencing a data in the data catalog.

        Returns:
            The data. It's type depends on the defined data type in the catalog.
        """
        data_info = cls._get_catalog_data_info(data_catalog_key)
        data_type = cls._get_catalog_data_type(data_info, data_catalog_key)
        data_path = data_info["path"]

        # Try to get read parameters. If not defined, use empty dict as the
        # default value.
        try:
            kwargs = data_info["read_params"]
        except KeyError:
            kwargs = dict()

        # The data reader class is determined by the data type.
        ReaderClass = cls.type_to_reader_map[data_type]
        reader = ReaderClass()
        data = reader.read_data(data_path, **kwargs)

        return data

    def write_data(cls, data_catalog_key: str, data: object) -> None:
        """
        Write data based on the data catalog.

        Args:
            data_catalog_key: There key referencing a data in the data catalog.
            data: The data to be written.

        """
        data_info = cls._get_catalog_data_info(data_catalog_key)
        data_type = cls._get_catalog_data_type(data_info, data_catalog_key)

        # Try to get write parameters
        try:
            kwargs = data_info["write_params"]
        except KeyError:
            kwargs = dict()
        WriterClass = cls.type_to_writer_map[data_type]
        writer = WriterClass()
        writer.write_data(data_info["path"], data, **kwargs)
