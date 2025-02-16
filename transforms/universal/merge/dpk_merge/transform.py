# (C) Copyright IBM Corp. 2024.
# Licensed under the Apache License, Version 2.0 (the “License”);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#  http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################

from argparse import ArgumentParser, Namespace
from typing import Any

import pyarrow as pa
from data_processing.transform import AbstractTableTransform, TransformConfiguration
from data_processing.utils import CLIArgumentProvider


short_name = "merge"
cli_prefix = f"{short_name}_"
input_dirs_key = "input_dirs"
input_dirs_cli_param = f"{cli_prefix}{input_dirs_key}"


class MergeTransform(AbstractTableTransform):
    """
    Implements a simple copy of a pyarrow Table.
    """

    def __init__(self, config: dict[str, Any]):
        """
        Initialize based on the dictionary of configuration information.
        This is generally called with configuration parsed from the CLI arguments defined
        by the companion runtime, MergeTransformRuntime.  If running inside the RayMutatingDriver,
        these will be provided by that class with help from the RayMutatingDriver.
        """
        # Make sure that the param name corresponds to the name used in apply_input_params method
        # of MergeTransformConfiguration class
        super().__init__(config)
        input_dirs = config.get(input_dirs_cli_param)
        self.input_dirs = []
        if input_dirs == None:
            # For backwards compatibility after we started encouraging the use of cli prefix in the configuration keys
            input_dirs = config.get(input_dirs_key)
        if input_dirs is not None:
            input_dirs = input_dirs.split(",")
            self.data_access = config.get("data_access")
            main_input_folder = self.data_access.get_input_folder()
            for input_for_merge in input_dirs:
                self.input_dirs.append(MergeTransform._input_path(main_input_folder, input_for_merge))

    def transform(self, table: pa.Table, file_name: str = None) -> tuple[list[pa.Table], dict[str, Any]]:
        self.logger.debug(f"Transforming one table with {len(table)} rows")
        added_columns = 0
        for input_dir in self.input_dirs:
            data_access_input_folder = self.data_access.get_input_folder()
            if not data_access_input_folder.endswith("/"):
                data_access_input_folder += "/"
            new_file_name = file_name.replace(data_access_input_folder, input_dir)
            t, _ = self.data_access.get_table(new_file_name)
            table, i = MergeTransform._copy_columns(table, t)
            added_columns += i
        # Add some sample metadata.
        self.logger.debug(f"Transformed one table with {len(table)} rows")
        metadata = {"nfiles": 1, "nrows": len(table), "added_columns": added_columns}
        return [table], metadata

    @staticmethod
    def _input_path(main_input_path: str, merged_input_path: str) -> str:
        if not main_input_path.endswith("/"):
            main_input_path += "/"
        if not merged_input_path.endswith("/"):
            merged_input_path += "/"
        main_splits = main_input_path.split("/")
        merged_splits = merged_input_path.split("/")
        # TODO check that the merged input path is not longer then the main input path
        for i in range(-1, -len(merged_splits) - 1, -1):
            main_splits[i] = merged_splits[i]
        return "/".join(main_splits)

    @staticmethod
    def _copy_columns(main_table: pa.Table, merged_table: pa.Table):
        main_t_columns = set(MergeTransform._convert_to_list(main_table.column_names))
        merged_t_columns = set(MergeTransform._convert_to_list(merged_table.column_names))
        i = 0
        # Add missing columns from merged_table main_table
        for col in merged_t_columns - main_t_columns:
            main_table = main_table.append_column(col, merged_table[col])
            i += 1
        return main_table, i

    @staticmethod
    def _convert_to_list(value):
        """Ensure the return value is always a list of strings."""
        if isinstance(value, str):
            return [value]  # Wrap single string in a list
        if isinstance(value, list):
            return value  # Return as-is if it's already a list
        # just in case
        raise TypeError(f"Expected a string or a list of strings, received {type(value)}")  # Handle unexpected types


class MergeTransformConfiguration(TransformConfiguration):
    """
    Provides support for configuring and using the associated Transform class include
    configuration with CLI args.
    """

    def __init__(self):
        super().__init__(name=short_name, transform_class=MergeTransform)
        from data_processing.utils import get_logger

        self.logger = get_logger(__name__)

    def add_input_params(self, parser: ArgumentParser) -> None:
        """
        Add Transform-specific arguments to the given  parser.
        This will be included in a dictionary used to initialize the MergeTransform.
        By convention a common prefix should be used for all transform-specific CLI args
        (e.g, merge_, pii_, etc.)
        """
        parser.add_argument(
            f"--{input_dirs_cli_param}",
            type=str,
            default=None,
            help="Comma-separated list of strings",
        )

    def apply_input_params(self, args: Namespace) -> bool:
        """
        Validate and apply the arguments that have been parsed
        :param args: user defined arguments.
        :return: True, if validate pass or False otherwise
        """
        captured = CLIArgumentProvider.capture_parameters(args, cli_prefix, False)
        self.params = self.params | captured
        self.logger.info(f"merge parameters are : {self.params}")
        return True
