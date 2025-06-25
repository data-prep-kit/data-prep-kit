# SPDX-License-Identifier: Apache-2.0
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
import pyarrow.compute as pc

import ast

from data_processing.transform import AbstractTableTransform, TransformConfiguration
from data_processing.utils import CLIArgumentProvider, TransformUtils
from data_processing.utils import get_logger
logger = get_logger(__name__,"DEBUG")


short_name = "collapse"
cli_prefix = f"{short_name}_"
input_columns = f"{cli_prefix}input_columns"
output_column = f"{cli_prefix}output_column"
field_seperator = f"{cli_prefix}field_seperator"
retain_all = f"{cli_prefix}retain_all"

class CollapseTransform(AbstractTableTransform):
    """
    Implements a simple copy of a pyarrow Table.
    """

    def __init__(self, config: dict[str, Any]):
        """
        Initialize based on the dictionary of configuration information.
        This is generally called with configuration parsed from the CLI arguments defined
        by the companion runtime, ClassificationTransformRuntime.  If running inside the RayMutatingDriver,
        these will be provided by that class with help from the RayMutatingDriver.
        """
        # Make sure that the param name corresponds to the name used in apply_input_params method
        # of ClassificationTransformConfiguration class
        super().__init__(config)
        
        self.input_columns = config.get(input_columns)
        self.output_column = config.get(output_column)
        self.field_seperator = config.get(field_seperator,"\n")
        self.retain_all = config.get(retain_all, False)
        logger.debug(f"input columns: {self.input_columns} "
                    f"output column: {self.output_column} "
                    f"field seperator: '{self.field_seperator}' "
                    f"retain all: {self.retain_all} ")

    def transform(self, table: pa.Table, file_name: str | None = None) -> tuple[list[pa.Table], dict[str, Any]]:  # pylint:disable=unused-argument
        """
        Put Transform-specific to convert one Table to 0 or more tables. It also returns
        a dictionary of execution statistics - arbitrary dictionary
        This implementation makes no modifications so effectively implements a copy of the
        input parquet to the output folder, without modification.
        """        
        TransformUtils.validate_columns(table, self.input_columns)
        #logger.debug(table.column_names)
        t1=table.select(self.input_columns)
        #logger.debug(t1.column_names)
        output_list=[]
        for col in t1.columns:
            output_list.append(col.cast(pa.string()))
        collapsed_column=[self.field_seperator.join([row[i].as_py() or "" for i in range(t1.num_columns)]) for row in zip(*output_list)]

        if not self.retain_all:
            table=table.select([col for col in table.column_names if col not in self.input_columns])
        table = TransformUtils.add_column(table=table, name=self.output_column, content=collapsed_column)
        metadata = {"nrows": len(table), "ncols": len(table.columns)}

        return [table], metadata


class CollapseTransformConfiguration(TransformConfiguration):
    """
    Provides support for configuring and using the associated Transform class include
    configuration with CLI args.
    """

    def __init__(self):
        super().__init__(
            name=short_name,
            transform_class=CollapseTransform,
        )
        from data_processing.utils import get_logger

        self.logger = get_logger(__name__)

    def add_input_params(self, parser: ArgumentParser) -> None:
        """
        Add Transform-specific arguments to the given  parser.
        This will be included in a dictionary used to initialize the ClassificationTransform.
        By convention a common prefix should be used for all transform-specific CLI args
        (e.g, noop_, pii_, etc.)
        """

        parser.add_argument(
            f"--{input_columns}",
            required=True,
            type=ast.literal_eval,
            help="List of text columns that will be joined",
        )
        parser.add_argument(
            f"--{output_column}",
            type=str,
            required=True,
            default="contents",
            help="Name of new column that will hold concatenated text",
        )
        parser.add_argument(
            f"--{field_seperator}",
            type=str,
            default="\n",
            help="Delimiter used to seperate concatenated content"
        )
        parser.add_argument(
            f"--{retain_all}",
            type=bool,
            help="Delimiter used to seperate concatenated content"
        )

    def apply_input_params(self, args: Namespace) -> bool:
        """
        Validate and apply the arguments that have been parsed
        :param args: user defined arguments.
        :return: True, if validate pass or False otherwise
        """
        captured = CLIArgumentProvider.capture_parameters(args, cli_prefix, True)
        self.params = self.params | captured
        self.logger.info(f"parameters are : {self.params}")
        return True
