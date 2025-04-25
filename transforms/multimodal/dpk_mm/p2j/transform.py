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
import json

from argparse import ArgumentParser, Namespace
import ast
from typing import Any

import pyarrow as pa
from data_processing.data_access import DataAccessLocal
from data_processing.transform import (
    AbstractBinaryTransform,
    AbstractTransform,
    TransformConfiguration,
)
from data_processing.utils import CLIArgumentProvider, TransformUtils, str2bool

from dpk_mm.util import JsonUtils, Schema

shortname = "p2j"
cli_prefix = f"{shortname}_"

export_columns_key = "export_columns"
export_columns_cli_param = f"{cli_prefix}{export_columns_key}"
export_columns_default = ['id', 'orig_image_fpaths', 'conversations', 'fixed_image_fpaths', 'source']

as_jsonl_key = "as_jsonl"
as_jsonl_cli_param = f"{cli_prefix}{as_jsonl_key}"
as_jsonl_default = True

write_images_key = "write_images"
write_images_cli_param = f"{cli_prefix}{write_images_key}"
write_images_default = False

write_image_path_key = "write_image_path"
write_image_path_cli_param = f"{cli_prefix}{write_image_path_key}"
write_image_path_default = './output_images'

class Parquet2JsonTransform(AbstractBinaryTransform):
    def __init__(self, config: dict):
        """

        Args:
            config: dictionary of configuration data
                supported_langs - dictionary of file extenstions to language names.
                supported_langs_file - if supported_langs, is not provided, then read a map
                    of language names keyed to a list of extensions, from this json file.  The file is read using
                    the DataAccessFactory, under the code2parquet_data_factory key.
        """
        from data_processing.utils import get_logger

        self.logger = get_logger(__name__)
        super().__init__(config)

        self.data_access = config.get("data_access", None)
        if self.data_access is None:
            self.data_access = DataAccessLocal()
        self.export_columns = config.get(export_columns_key,export_columns_default)
        self.as_jsonl = config.get(as_jsonl_key, as_jsonl_default)
        self.write_images = config.get(write_images_key,write_images_default)
        if self.write_images:
            self.write_image_path = config.get(write_image_path_key, write_image_path_default)


    def transform_binary(self, file_name: str, byte_array: bytes) -> tuple[list[tuple[bytes, str]], dict[str, Any]]:
        """
        Converts raw data file (ZIP) to Parquet format
        """
        # We currently only process .zip files
        print(file_name) # for debugging
        if TransformUtils.get_file_extension(file_name)[1] != ".parquet":
            self.logger.warning(f"Got unsupported file type {file_name}, skipping")
            return [], {} # are these always required

        table = JsonUtils.get_table_from_bytes(byte_array)
        del byte_array

        selected_columns = list(set(table.schema.names) & set(self.export_columns))
        if self.write_images:# columns 'image_bins'and 'fixed_image_fpaths' are required for image write
            if 'image_bins' not in selected_columns:
                selected_columns.append('image_bins')

        new_table = table.select(selected_columns)
        # print(selected_columns)

        # select columns in the table
        # print('-'*20)
        # print(self.write_images)
        # print(self.write_image_path)
        # print('-' * 20)

        if self.write_images:
            json_str = JsonUtils.table2json(self, new_table,  as_jsonl=self.as_jsonl, data_access=self.data_access)
        else:
            json_str = JsonUtils.table2json(self, new_table,  as_jsonl=self.as_jsonl, data_access=None)

        tuple_list = [] # Tuples are (byte array of json text , ".json")
        if json_str is not None:
            extension = ".jsonl" if self.as_jsonl else ".json"
            str_bytes = json_str.encode("utf-8")
            tuple_list.append((str_bytes,extension))

        return tuple_list, {}


class Parquet2JsonTransformConfiguration(TransformConfiguration):
    """
    Provides support for configuring and using the associated Transform class include
    configuration with CLI args and combining of metadata.
    """

    def __init__(self):
        super().__init__(
            name=shortname,
            transform_class=Parquet2JsonTransform,
        )
        from data_processing.utils import get_logger
        self.logger = get_logger(__name__)

    def add_input_params(self, parser: ArgumentParser) -> None: # changes here?
        """
        Add Transform-specific arguments to the given parser.
        This will be included in a dictionary used to initialize the ProgLangMatchTransform.
        By convention a common prefix should be used for all mutator-specific CLI args
        (e.g, noop_, pii_, etc.)
        """

        parser.add_argument(
            f"--{export_columns_cli_param}",
            type=ast.literal_eval,
            default=ast.literal_eval(f'"{str(export_columns_default)}"'),
            help=f"Columns need to be exported in json files",
        )
        parser.add_argument(
            f"--{as_jsonl_cli_param}",
            type=lambda x: bool(str2bool(x)),
            default=as_jsonl_default,
            help=f"Set output format to jsonl (True) or json (False)."
        )
        parser.add_argument(
            f"--{write_images_cli_param}",
            type=lambda x: bool(str2bool(x)),
            default=write_images_default,
            help=f"Set to True to also write out the images in the parquet file(s) and adjust paths in json."
        )
        parser.add_argument(
            f"--{write_image_path_cli_param}",
            type=str,
            default=write_image_path_default,
            help=f"Set output path for exported images"
        )

    def apply_input_params(self, args: Namespace) -> bool:
        """
        Validate and apply the arguments that have been parsed
        :param args: user defined arguments.
        :return: True, if validate pass or False otherwise
        """
        captured = CLIArgumentProvider.capture_parameters(args, cli_prefix, False)
        self.params = captured
        return True
