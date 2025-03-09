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
from noop_transform_python import NOOPPythonTransformConfiguration


short_name = "noop"
cli_prefix = f"{short_name}_"
sleep_key = "sleep_sec"
pwd_key = "pwd"
sleep_cli_param = f"{cli_prefix}{sleep_key}"
pwd_cli_param = f"{cli_prefix}{pwd_key}"

class NOOPComponent(Component):
    display_name = "Noop"
    description = "DPK noop."
    icon = "noop"
    name = "noop"

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
        IntInput(
            name="noop_sleep_sec",
            display_name="noop_sleep_sec",
            info="noop sleep parameter.",
            value=1
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
        # from dpk_noop.transform_python import NOOPPythonTransformConfiguration
        from data_processing.transform import AbstractTableTransform, TransformConfiguration

        # create parameters
        input_folder = self.input_folder
        output_folder = self.output_folder
        sleep_sec = self.noop_sleep_sec
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
            # noop params
            "noop_sleep_sec": sleep_sec,
        }
        # Set the simulated command line args
        sys.argv = ParamsUtils.dict_to_req(d=params)
        # create launcher
        launcher = PythonTransformLauncher(runtime_config=NOOPPythonTransformConfiguration())
        print(f"************************noop************************")
        launcher.launch()
        return output_folder
