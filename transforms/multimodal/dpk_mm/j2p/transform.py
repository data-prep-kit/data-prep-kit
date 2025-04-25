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
import traceback
from argparse import ArgumentParser, Namespace
from typing import Any
import json
import pyarrow as pa

from data_processing.data_access import DataAccessLocal, DataAccessS3
from data_processing.transform import (
    AbstractBinaryTransform,
    TransformConfiguration,
)
from data_processing.utils import CLIArgumentProvider, TransformUtils, ParamsUtils

from data_processing.utils import get_logger

from dpk_mm.util import JsonUtils, Schema

shortname = "j2p"
cli_prefix = f"{shortname}_"

image_path_prefix_alias_key = "image_path_prefix_alias"
image_path_prefix_alias_cli_key = f"{cli_prefix}{image_path_prefix_alias_key}"

image_path_prefix_key = "image_path_prefix"
image_path_prefix_cli_key = f"{cli_prefix}{image_path_prefix_key}"

parquet_size_key = "parquet_size_limit"
parquet_size_key_cli_key = f"{cli_prefix}{parquet_size_key}"

secondary_data_access_config_key = "secondary_data_access_config"
secondary_data_access_config_cli_key = f"{cli_prefix}{secondary_data_access_config_key}"
DEFAULT_CONST = "None"


class Json2ParquetTransform(AbstractBinaryTransform):

    def __init__(self, config: dict):
        """

        :param config:
        """
        super().__init__(config)
        self.logger = get_logger(__name__)
        self.image_path_prefix = config.get(image_path_prefix_key, DEFAULT_CONST)
        self.image_path_prefix_alias = config.get(
            image_path_prefix_alias_key, DEFAULT_CONST
        )
        self.parquet_size_limit = config.get(parquet_size_key, (200 * 1024 * 1024))
        self.data_access = config.get("data_access", None)

        if not self.image_path_prefix_alias.endswith("/"):
            self.image_path_prefix_alias = self.image_path_prefix_alias + "/"

        if not self.image_path_prefix.endswith("/"):
            self.image_path_prefix = self.image_path_prefix + "/"

        if self.data_access is None:
            self.data_access = DataAccessLocal()

        # If secondary_data_access_config is set from cli -> create secondary_data_access
        cos_write_data_access_config = eval(
            str(config.get(secondary_data_access_config_key, DEFAULT_CONST))
        )
        if (
            cos_write_data_access_config
            and cos_write_data_access_config != DEFAULT_CONST
        ):
            self.secondary_data_access = DataAccessS3(
                s3_credentials={
                    "access_key": cos_write_data_access_config["access_key"],
                    "secret_key": cos_write_data_access_config["secret_key"],
                    "url": cos_write_data_access_config["url"],
                    "region": cos_write_data_access_config["region"],
                },
                s3_config={
                    "input_folder": cos_write_data_access_config["output_folder"],
                    "output_folder": cos_write_data_access_config["output_folder"],
                },
            )
        else:
            self.secondary_data_access = None

    def __write_to_secondary_data_access(
        self, file_name: str, tables: list[pa.Table]
    ) -> None:
        """
        Write using self.secondary_data_access.

        :param file_name: Name of file the tables came from. Used to generate parquet names.
        :param tables: list of pa.Tables to write to parquets
        :return: None
        """
        self.logger.info("Using secondary data access to write tables.")
        filename_prefix = ".".join(file_name.split("/")[-1].split(".")[:-1])
        for i, table in enumerate(tables):
            path = (  # Path should be data_access.output_folder/[filename]_[index].parquet
                self.secondary_data_access.output_folder
                + filename_prefix
                + f"_{i}.parquet"
            )
            self.secondary_data_access.save_file(
                path=path, data=TransformUtils.convert_arrow_to_binary(table)
            )
            self.logger.info(f"Wrote table - {path}.")

    def __get_tables(self, datapoints: list[dict]) -> list[pa.Table]:
        """
        Given a list of datapoints, convert to pyarrow tables of less than self.parquet_size_limit.
        Table schema as defined in Schema.LLAVA_PARQUET_SCHEMA in mm_utils.py. Will fail if datapoints
        do not have necessary column name values.

        A datapoint is a dictionary with key-value pairs, where the key is the column name
        and the value is the value for that row , when converted to a table. E.g. -
        [{"key1": value1}, {"key1": value2}] becomes table -
        __________
        | key1   |
        ----------
        | value1 |
        | value2 |

        The tables get broken down into multiple tables with estimated sizes of self.parquet_size_limit
        parquet files.

        :param datapoints: list of dicts where each dict is a datapoint
        :return: list of pa.Table
        """
        # Convert list[dict] to dict[list] - needed for creating pyarrow table.
        dataset_dict = JsonUtils.list_of_dicts_to_dict_of_lists(datapoints=datapoints)
        # Create and resize table
        table = pa.Table.from_pydict(dataset_dict, schema=Schema.LLAVA_PARQUET_SCHEMA)
        tables = JsonUtils.resize_table(
            table=table, parquet_size_limit=self.parquet_size_limit
        )
        self.logger.info(f"Resized to {len(tables)} tables.")
        return tables

    def transform_binary(
        self, file_name: str, byte_array: bytes
    ) -> tuple[list[tuple[bytes, str]], dict[str, Any]]:
        """Converts Llava formatted JSON files to pyarrow tables of size self.parquet_size_limit.
        Can also write using separate DataAccess object if self.secondary_data_access is specified.

        :param file_name: Input JSON file name.
        :param byte_array: JSON file as bytes.
        :return: (list of (pyarrow Table as bytes, file extension), and metadata dictionary),
                list of (pyarrow Table as bytes, file extension) will be empty if self.secondary_data_acess
                is used.
        """
        if TransformUtils.get_file_extension(file_name)[1] != ".json":
            raise ValueError(f"Got unsupported file type {file_name}, skipping")

        # Read json as list of datapoints
        log_dict = {"missed-rows-count": 0}
        datapoints = json.loads(byte_array)
        self.logger.info(
            f"Starting j2p for {len(datapoints)} datapoints from {file_name}."
        )

        extracted_datapoints = []
        for i, datapoint in enumerate(datapoints):
            # For each datapoint in list
            try:
                # Read images, standardize to format in Schema in mm_util.py,
                # and append to list.
                # This step fails if image could not be read or JSON not LLAVA formatted
                extracted_datapoints.append(
                    JsonUtils.read_llava(  # Throws error if file cannot be read
                        data_access=self.data_access,
                        datapoint=datapoint,
                        orig_image_parent_dir=self.image_path_prefix,
                        actual_image_parent_dir=self.image_path_prefix_alias,
                    )
                )
            except Exception as e:
                self.logger.info(
                    f"Failed to read datapoint "
                    f"{datapoint['image']} - \n{traceback.format_exc()}"
                )
                log_dict["missed-rows-count"] += 1

            # Logging per 100 steps.
            if ((i + 1) % 100) == 0:
                self.logger.info(
                    f"Completed - {i+1} row. MISSED - {log_dict['missed-rows-count']}"
                )

        self.logger.info(
            f"Completed - {i+1} row. MISSED - {log_dict['missed-rows-count']}"
        )
        tables = self.__get_tables(datapoints=extracted_datapoints)
        if self.secondary_data_access:  # If using secondary data access
            self.__write_to_secondary_data_access(file_name, tables)
            return [], log_dict

        # else return tuples usual
        return [
            (TransformUtils.convert_arrow_to_binary(table), ".parquet")
            for table in tables
        ], log_dict


class Json2ParquetTransformConfiguration(TransformConfiguration):
    """
    Provides support for configuring and using the associated Transform class include
    configuration with CLI args and combining of metadata.
    """

    def __init__(self):
        super().__init__(
            name=shortname,
            transform_class=Json2ParquetTransform,
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
            f"--{image_path_prefix_alias_cli_key}",
            type=str,
            required=True,
            help="Absolute path of parent directory containing all the images used in the JSON file.",
        )
        parser.add_argument(
            f"--{image_path_prefix_cli_key}",
            type=str,
            required=True,
            help="Original source directory path in the 'image' field which needs to be replaced by the"
            " image_path_prefix_alias_cli_key"
            " JSON files current contain absolute paths in their 'image' columns which"
            " may not be correct. This variable should contain the path substring which needs to be "
            " replaced by the correct path in order to get to the actual image."
            " The original absolute path in 'image' is still preserved under 'orig_image_fpaths'."
            " The 'fixed_image_paths' variable contains the relative path remaining after removing"
            " this part of the path from the absolute 'image' path.",
        )
        parser.add_argument(
            f"--{parquet_size_key_cli_key}",
            type=int,
            default=(200 * 1024 * 1024),  # 200 MB
            help="Max size per parquet in bytes.",
        )
        parser.add_argument(
            f"--{secondary_data_access_config_cli_key}",
            type=str,
            default=DEFAULT_CONST,
            help="COS credentials and output directory for secondary data access object."
            "\nExample, { 'access_key': '...', 'secret_key': '...', 'url': 'https://s3.us-east....', 'region': 'us-east'"
            "   'input_folder': 'some/bucket', 'output_folder': 'some/other/bucket' }",
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
