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
from collections import defaultdict
from typing import Any

import pyarrow as pa
from data_processing.data_access import DataAccessFactory
from data_processing.transform import (
    AbstractBinaryTransform,
    TransformConfiguration,
)
from data_processing.utils import CLIArgumentProvider, TransformUtils

from data_processing.utils import get_logger
from dpk_mm.util import JsonUtils

shortname = "j2j"
cli_prefix = f"{shortname}_"

datapoints_per_file_key = "datapoints_per_file"
datapoints_per_file_key_cli_key = f"{cli_prefix}{datapoints_per_file_key}"
datapoints_per_file_default = 1000


class Json2JsonTransform(AbstractBinaryTransform):
    def __init__(self, config: dict):
        """

        Args:
            config: dictionary of configuration data
                supported_langs - dictionary of file extensions to language names.
                supported_langs_file - if supported_langs, is not provided, then read a map
                    of language names keyed to a list of extensions, from this json file.  The file is read using
                    the DataAccessFactory, under the code2parquet_data_factory key.
        """
        self.logger = get_logger(__name__)
        super().__init__(config)
        self.datapoints_per_file = config.get(
            datapoints_per_file_key, datapoints_per_file_default
        )
        self.data_access = config.get("data_access", None)
        if self.data_access is None:
            self.data_access = DataAccessFactory()

    def transform_binary(
        self, file_name: str, byte_array: bytes
    ) -> tuple[list[tuple[bytes, str]], dict[str, Any]]:
        """Converts JSONL file with the LLAVA formatted json lines to pyarrow tables.

        Rows per table is determined by the self.rows_per_file cli arg.

        Args:
            file_name (str): File name
            byte_array (bytes): JSON file as bytes

        Raises:
            ValueError: _description_

        Returns:
            tuple[list[tuple[bytes, str]], dict[str, Any]]:
                        tuple of (JSON string bytes, file extension) and (metadata dictionary)
        """

        # Only works with .json files
        if TransformUtils.get_file_extension(file_name)[1] != ".json":
            raise ValueError(f"Got unsupported file type {file_name}, skipping")

        # Read json as list of datapoints
        datapoints = [
            d.update({"orig_json_path": file_name, "index": i}) or d
            for i, d in enumerate(json.loads(byte_array))
        ]
        batched_datapoints = JsonUtils.batch(
            datapoints=datapoints, len_per_batch=self.datapoints_per_file
        )
        self.logger.info(
            f"Done splitting {len(datapoints)} datapoints in "
            f"JSON file {file_name} to {len(batched_datapoints)} parts."
        )
        tuple_list = []
        for batch in batched_datapoints:
            json_str = json.dumps(batch, indent=2)
            tuple_list.append((json_str.encode("utf-8"), f".json"))
        return tuple_list, {"num-output-files": len(datapoints)}


class Json2JsonTransformConfiguration(TransformConfiguration):
    """
    Provides support for configuring and using the associated Transform class include
    configuration with CLI args and combining of metadata.
    """

    def __init__(self):
        super().__init__(
            name=shortname,
            transform_class=Json2JsonTransform,
        )
        from data_processing.utils import get_logger

        self.logger = get_logger(__name__ + "config")

    def add_input_params(self, parser: ArgumentParser) -> None:
        """
        Add Transform-specific arguments to the given parser.
        This will be included in a dictionary used to initialize the ProgLangMatchTransform.
        By convention a common prefix should be used for all mutator-specific CLI args
        (e.g, noop_, pii_, etc.)
        """
        parser.add_argument(
            f"--{datapoints_per_file_key_cli_key}",
            type=int,
            default=datapoints_per_file_default,
            help="Maximum number of datapoints per output json file."
            " The total number of files generated is equal to"
            " the number of total datapoint / this number rounded up",
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
