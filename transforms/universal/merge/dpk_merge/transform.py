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
from pathlib import Path
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
            for input_dir in input_dirs:
                self.input_dirs.append(Path(input_dir))

    def transform(self, table: pa.Table, file_name: str = None) -> tuple[list[pa.Table], dict[str, Any]]:

        self.logger.debug(f"Transforming one table with {len(table)} rows")
        file_path = Path(file_name)
        data_access = self.config.get("data_access")
        parent_path = Path(data_access.get_input_folder())
        relative_path = file_path.relative_to(parent_path)
        added_columns = 0
        for input_path in self.input_dirs:
            merged_file_path = input_path / relative_path
            self.logger.debug(f"merging a table from {merged_file_path}")
            t, _ = data_access.get_table(str(merged_file_path))
            table, i = MergeTransform._copy_columns(table, t)
            added_columns += i
        # Add some sample metadata.
        self.logger.debug(f"Transformed one table with {len(table)} rows, added {added_columns} columns from {len(self.input_dirs)} tables")
        metadata = {
            "nfiles": 1,
            "nrows": len(table),
            "merged_tables": len(self.input_dirs),
            "added_columns": added_columns,
        }
        return [table], metadata

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
        Absolute paths from which the merged content should be taken.
        Note: in the case of S3 storage the absolute path starts from the bucket name.
        """
        parser.add_argument(
            f"--{input_dirs_cli_param}",
            type=str,
            default=None,
            help="Comma-separated list of absolute paths from which the merged content should be taken",
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
