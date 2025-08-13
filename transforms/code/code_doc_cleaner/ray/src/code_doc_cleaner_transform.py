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
from functools import partial
from typing import Any

import pyarrow as pa
from data_processing.transform import (
    AbstractTableTransform,
    TransformConfiguration,
)
from data_processing.utils import CLIArgumentProvider, get_logger, str2bool
from clean_by_resiliparse import extract_and_clean_html


logger = get_logger(__name__)

short_name = "cdc"
cli_prefix = f"{short_name}_"

disable_tab_str_key = "disable_table_structure"
html_column_name_key = "contents_column_name"
text_column_name_key = "clean_text_column_name"
disable_tab_str_cli_param = f"{cli_prefix}{disable_tab_str_key}"
html_column_name_cli_param = f"{cli_prefix}{html_column_name_key}"
text_column_name_cli_param = f"{cli_prefix}{text_column_name_key}"

default_disable_tab_str = False
default_html_column_name = "contents"
default_text_column_name = "contents"


class CodeDocCleanerTransform(AbstractTableTransform):
    """
    Implements a transform to clean text from code document.
    """
    def __init__(self, config: dict[str, Any]):
        """
        Initialize based on the dictionary of configuration information.
        This is generally called with configuration parsed from the CLI arguments.
        If running inside the RayMutatingDriver,
        these will be provided by that class with help from the RayMutatingDriver.
        """
        # Make sure that the param name corresponds to the name used in apply_input_params method
        # of CodeDocCleanerTransformConfiguration class
        super().__init__(config)
        self.disable_table_structure = config.get(disable_tab_str_key, default_disable_tab_str)
        self.html_column_name = config.get(html_column_name_key, default_html_column_name)
        self.text_column_name = config.get(text_column_name_key, default_text_column_name)

    def transform(self, table: pa.Table, file_name: str = None) -> tuple[list[pa.Table], dict[str, Any]]:
        """
        Put Transform-specific to convert one Table to 0 or more tables. It also returns
        a dictionary of execution statistics - arbitrary dictionary.
        """
        func = partial(extract_and_clean_html, disable_table_structure=self.disable_table_structure)
        transformed = pa.array(
            map(func, table[self.html_column_name].to_pylist()),
            type=table[self.html_column_name].type,
        )
        table = table.append_column("html_contents", table[self.html_column_name])
        if self.text_column_name in table.column_names:
            table = table.drop_columns(self.text_column_name)
        table = table.append_column(self.text_column_name, transformed)
        metadata = {}
        return [table], metadata


class CodeDocCleanerTransformConfiguration(TransformConfiguration):
    """
    Provides support for configuring and using the associated Transform class include
    configuration with CLI args.
    """

    def __init__(self):
        super().__init__(
            name=short_name,
            transform_class=CodeDocCleanerTransform,
        )

    def add_input_params(self, parser: ArgumentParser) -> None:
        """
        Add Transform-specific arguments to the given  parser.
        This will be included in a dictionary used to initialize the PrFilterTransform.
        By convention a common prefix should be used for all transform-specific CLI args
        (e.g, noop_, pii_, etc.)
        """
        def add_default(help_msg):
            return help_msg + ' Default: %(default)s'

        parser.add_argument(
            f"--{disable_tab_str_cli_param}",
            default=False,
            type=str2bool,
            help=add_default("Disable to keep table structure if True."),
        )
        parser.add_argument(
            f"--{html_column_name_cli_param}",
            default=default_html_column_name,
            help=add_default("The column name to get HTML strings."),
        )
        parser.add_argument(
            f"--{text_column_name_cli_param}",
            default=default_text_column_name,
            help=add_default("The column name to write cleaned texts."),
        )

    def apply_input_params(self, args: Namespace) -> bool:
        """
        Validate and apply the arguments that have been parsed
        :param args: user defined arguments.
        :return: True, if validate pass or False otherwise
        """
        captured = CLIArgumentProvider.capture_parameters(args, cli_prefix, False)
        self.params = self.params | captured
        logger.info(f"issues parameters are : {self.params}")
        return True