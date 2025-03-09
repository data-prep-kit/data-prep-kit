from langflow.custom import Component
from langflow.io import DataInput, MessageTextInput, Output
from argparse import ArgumentParser, Namespace
from langflow.schema import Data
from data_processing.utils import CLIArgumentProvider
from typing import Any
import pyarrow as pa
from data_processing.runtime.pure_python.runtime_configuration import (
    PythonTransformRuntimeConfiguration,
)
import time


class DocIdComponent(Component):
    display_name = "DocId"
    description = "docid transform"
    icon = "docid"
    name = "docid"

    inputs = [
        StrInput(
            name="input_folder",
            display_name="input folder",
            input_types=["StrInput", "str", "Text"],
            info="input folder to process.",
        ),
        StrInput(
            name="output_folder",
            display_name="output folder",
            input_types=["StrInput", "str", "Text"],
            info="output folder to store processed files.",
        ),
        StrInput(
            name="doc_id_doc_column",
            display_name="doc column",
            info="document column name",
            value="contents",
        ),
        StrInput(
            name="doc_id_hash_column",
            display_name="doc_id_hash_column",
            info="hash column name",
            value="hash_column",
        ),
        StrInput(
            name="doc_id_int_column",
            display_name="doc_id_int_column",
            info="Compute unique integer id and place in the given named column",
            value="int_id_column",
        ),
        IntInput(
            name="doc_id_start_id",
            display_name="doc_id_start_id",
            info="starting integer id",
            value=5,
        ),
    ]

    outputs = [
        Output(display_name="Filtered Data", name="filtered_data", method="filter_data"),
    ]


    def filter_data(self) -> str:
        import os
        import sys
        
        from data_processing.runtime.pure_python import PythonTransformLauncher
        from data_processing.utils import ParamsUtils
        from dpk_doc_id.transform import (
            doc_column_name_cli_param,
            hash_column_name_cli_param,
            int_column_name_cli_param,
            start_id_cli_param,
        )
        from dpk_doc_id.transform_python import DocIDPythonTransformRuntimeConfiguration

        # create parameters
        input_folder = self.input_folder
        output_folder = self.output_folder
        doc_column = self.doc_id_doc_column
        hash_column = self.doc_id_hash_column
        int_column = self.doc_id_int_column
        start_id = self.doc_id_start_id
        local_conf = {
            "input_folder": input_folder,
            "output_folder": output_folder,
        }
        code_location = {"github": "github", "commit_hash": "12345", "path": "path"}
        params = {
            # Data access. Only required parameters are specified
            "data_local_config": ParamsUtils.convert_to_ast(local_conf),
            # execution info
            "runtime_pipeline_id": "pipeline_id",
            "runtime_job_id": "job_id",
            "runtime_code_location": ParamsUtils.convert_to_ast(code_location),
            # doc id params
            doc_column_name_cli_param: doc_column,
            hash_column_name_cli_param: hash_column,
            int_column_name_cli_param: int_column,
            start_id_cli_param: start_id,
        }
        # Set the simulated command line args
        sys.argv = ParamsUtils.dict_to_req(d=params)
        # create launcher
        launcher = PythonTransformLauncher(runtime_config=DocIDPythonTransformRuntimeConfiguration())
        print(f"************************doc id************************")
        launcher.launch()
        return output_folder
