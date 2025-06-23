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

from data_processing.transform import TransformConfiguration
from data_processing.utils import CLIArgumentProvider
from data_processing.utils import get_logger
from dpk_web2parquet.transform import Web2ParquetTransform

short_name = "web2parquet"
cli_prefix = f"{short_name}_"
urls_cli_param = f"{cli_prefix}urls"
depth_cli_param = f"{cli_prefix}depth"
downloads_cli_param = f"{cli_prefix}downloads"
folder_cli_param = f"{cli_prefix}folder"


logger = get_logger(__name__,"DEBUG")
    
class Web2ParquetTransformConfiguration(TransformConfiguration):

    """
    Provides support for configuring and using the associated Transform class include
    configuration with CLI args.
    """

    def __init__(self):
        super().__init__(
            name=short_name,
            transform_class=Web2ParquetTransform
        )

    def add_input_params(self, parser: ArgumentParser) -> None:
        """
        Add Transform-specific arguments to the given  parser.
        This will be included in a dictionary used to initialize the Web2ParquetTransform.
        By convention a common prefix should be used for all transform-specific CLI args
        (e.g, noop_, pii_, etc.)
        """
        parser.add_argument(f"--{depth_cli_param}", type=int, default=1,
            help="maxumum depth relative to seed URL",
        )
        parser.add_argument(f"--{downloads_cli_param}", type=int, default=1,
            help="maxumum number of downloaded URLs",
        )
        parser.add_argument(f"--{folder_cli_param}", type=str, default=None,
            help="Folder where to store downloaded files",
        )
        parser.add_argument(f"--{urls_cli_param}", type=str, default=None,
            help="List of Seed URLs for the crawler",
        )

    def apply_input_params(self, args: Namespace) -> bool:
        """
        Validate and apply the arguments that have been parsed
        :param args: user defined arguments.
        :return: True, if validate pass or False otherwise
        """
        captured = CLIArgumentProvider.capture_parameters(args, cli_prefix, False)
        if captured.get("urls") is None:
            logger.error(f"Parameter web2parquet_urls must specify a seed URL")
            return False

        self.params = self.params | captured
        logger.info(f"web2parquet parameters are : {self.params}")
        return True





