import importlib
import os
import sys
from datetime import datetime
from typing import Any, Dict

import colorama
import yaml
from tabulate import tabulate
from termcolor import colored

from .io import *


REFERENCE_PREFIX = "ref::"
DATA_CATALOG_PREFIX = "data::"


class Villard:
    def __new__(cls):
        """Create a new instance of the class as a singleton."""
        if not hasattr(cls, "instance"):
            cls.instance = super(Villard, cls).__new__(cls)

        cls.data_catalog = dict()
        cls.node_func_map = dict()
        cls.node_output_map = dict()

        cls.supported_data_types = ["DT_PICKLE", "DT_PANDAS_DATAFRAME"]
        cls.supported_data_writer = [PickleWriter, PandasWriter]
        cls.supported_data_reader = [PickleReader, PandasReader]
        cls.type_to_reader_map = {
            k: v for k, v in zip(cls.supported_data_types, cls.supported_data_reader)
        }
        cls.type_to_writer_map = {
            k: v for k, v in zip(cls.supported_data_types, cls.supported_data_writer)
        }

        return cls.instance

    def visit_and_execute_recursively(cls, name, node, stats_table):
        if node["executed"]:
            return

        # Before executing function of current node, execute all the nodes that are
        # dependencies of the current node recursively.
        for prev in node["prevs"]:
            cls.visit_and_execute_recursively(
                prev, cls.execution_nodes[prev], stats_table
            )

        # Convert kwargs ref to actual values before execution
        actual_kwargs = node["kwargs"]
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

        # The actual kwargs is ready, call node function accordingly.
        # Keep track the execution statistics.
        print(colored(f"  Executing `{name}`...", "yellow"))
        tic = datetime.now()
        node["func"](**actual_kwargs)
        node["executed"] = True
        toc = datetime.now()
        print(colored(f"⦿ Completed `{name}`", "green"))

        execution_time = toc - tic
        stats_table.append((name, execution_time, 34))

    def node(cls, name: str):
        def decorator_node(func):
            def inner(*args, **kwargs):
                result = func(*args, **kwargs)
                cls.node_output_map[name] = result
                return result

            cls.node_func_map[name] = inner

        return decorator_node

    def run(cls, config: str):
        colorama.init()

        with open(config, "r") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
            cls.pipeline_definition = config["pipeline_definition"]
            cls.node_definition_modules = config["node_implementation_modules"]

        if "data_catalog" in config:
            cls.data_catalog = config["data_catalog"]

        for module in cls.node_definition_modules:
            try:
                sys.path.append(os.getcwd())
                importlib.import_module(module)
            except ModuleNotFoundError as e:
                msg = f"Cannot import module {module}: {e}. Please check the configuration file."
                print(colored("Error:", "red"), colored(msg, "red"))
                exit(1)

        """ To keep track nodes' incoming and outgoing edge counts """
        execution_nodes_in_out_counter = dict()
        for name in cls.pipeline_definition:
            execution_nodes_in_out_counter[name] = dict()
            execution_nodes_in_out_counter[name]["in"] = 0
            execution_nodes_in_out_counter[name]["out"] = 0

        """ Build execution graph """
        execution_nodes = dict()
        for name, kwargs in cls.pipeline_definition.items():
            execution_node = dict()
            execution_node["func"] = cls.node_func_map[name]
            execution_node["kwargs"] = kwargs
            execution_node["prevs"] = []
            execution_node["executed"] = False

            def check_ref_recursively(kwargs):
                # if "ref" key is detected, it means that the node refers to another node.
                # Add the referenced node into the dependency list (`prevs`) of the current node.
                for k, v in kwargs.items():
                    if k == "ref":
                        execution_node["prevs"].append(v)
                        execution_nodes_in_out_counter[name]["in"] += 1
                        execution_nodes_in_out_counter[v]["out"] += 1
                    elif isinstance(v, dict):
                        check_ref_recursively(v)

            check_ref_recursively(kwargs)
            execution_nodes[name] = execution_node

        """ Output nodes are the ones that have no outging edges """
        output_nodes = {
            node: v
            for node, v in execution_nodes.items()
            if execution_nodes_in_out_counter[node]["out"] == 0
        }

        stats_table = []
        for output_node_name in output_nodes:
            cls.visit_and_execute_recursively(
                output_node_name, execution_nodes[output_node_name], stats_table
            )

        print(
            "\n"
            + tabulate(
                stats_table,
                headers=["Node", "Time", "Output Path"],
                tablefmt="fancy_grid",
            )
        )

    def get_data_info(cls, data_catalog_key):
        try:
            data_info = cls.data_catalog[data_catalog_key]
        except KeyError:
            msg = f"Data catalog key `{data_catalog_key}` is not defined."
            print(colored("Error:", "red"), colored(msg, "red"))
            exit(1)

        return data_info

    def get_data_type(cls, data_info: Dict[str, Any], data_catalog_key: str):
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

    def read_data(cls, data_catalog_key: str):
        data_info = cls.get_data_info(data_catalog_key)
        data_type = cls.get_data_type(data_info, data_catalog_key)

        # Try to get read parameters
        try:
            kwargs = data_info["read_params"]
        except KeyError:
            kwargs = dict()
        ReaderClass = cls.type_to_reader_map[data_type]
        reader = ReaderClass()
        return reader.read_data(data_info["path"], **kwargs)

    def write_data(cls, data_catalog_key: str, data: object):
        data_info = cls.get_data_info(data_catalog_key)
        data_type = cls.get_data_type(data_info, data_catalog_key)

        # Try to get write parameters
        try:
            kwargs = data_info["write_params"]
        except KeyError:
            kwargs = dict()
        WriterClass = cls.type_to_writer_map[data_type]
        writer = WriterClass()
        writer.write_data(data_info["path"], data, **kwargs)
