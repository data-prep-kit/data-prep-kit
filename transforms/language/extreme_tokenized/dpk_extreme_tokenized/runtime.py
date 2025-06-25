# SPDX-License-Identifier: Apache-2.0
# (C) Copyright IBM Corp. 2025.
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

import sys
from argparse import ArgumentParser, Namespace

from data_processing.data_access import DataAccessFactory
from data_processing.runtime.pure_python import (
    PythonTransformLauncher,
    PythonTransformRuntimeConfiguration,
)
from data_processing.transform import TransformConfiguration
from data_processing.utils import CLIArgumentProvider, ParamsUtils
from dpk_extreme_tokenized.common import (
    arrow_path_cli_param,
    arrow_path_default,
    cli_prefix,
    contents_column_name_cli_param,
    contents_column_name_default,
    extreme_tokenized_data_access_key,
    extreme_tokenized_data_factory_key,
    logger,
    short_name,
)
from dpk_extreme_tokenized.transform import ExtremeTokenizedTransform


class ExtremeTokenizedTransformConfiguration(TransformConfiguration):
    """
    Provides support for configuring and using the associated Transform class include
    configuration with CLI args and combining of metadata.
    """

    def __init__(self):
        super().__init__(
            name=short_name,
            transform_class=ExtremeTokenizedTransform,
            remove_from_metadata=[extreme_tokenized_data_access_key, extreme_tokenized_data_factory_key],
        )
        self.daf = None

    def add_input_params(self, parser: ArgumentParser) -> None:
        """
        Add Transform-specific arguments to the given parser.
        This will be included in a dictionary used to initialize the BlockListTransform.
        By convention a common prefix should be used for all mutator-specific CLI args
        (e.g, noop_, pii_, etc.)
        """

        parser.add_argument(
            f"--{contents_column_name_cli_param}",
            type=str,
            required=False,
            default=contents_column_name_default,
            help="Name of the column holding the document text",
        )
        parser.add_argument(
            f"--{arrow_path_cli_param}",
            type=str,
            required=True,
            default=arrow_path_default,
            help=" Arrow folder location.",
        )
        self.daf = DataAccessFactory(cli_prefix, False)
        # Add the DataAccessFactory parameters to the transform's configuration parameters.
        self.daf.add_input_params(parser)
        self.params[extreme_tokenized_data_access_key] = self.daf.create_data_access()

    def apply_input_params(self, args: Namespace) -> bool:
        """
        Validate and apply the arguments that have been parsed
        :param args: user defined arguments.
        :return: True, if validate pass or False otherwise
        """
        # Capture the args that are specific to this transform
        captured = CLIArgumentProvider.capture_parameters(args, cli_prefix, True)
        self.params = self.params | captured
        # Add the DataAccessFactory to the transform's configuration parameters.
        self.params[extreme_tokenized_data_factory_key] = self.daf
        # # Validate and populate the transform's DataAccessFactory
        return self.daf.apply_input_params(args)
        # return True


class ExtremeTokenizedPythonTransformConfiguration(PythonTransformRuntimeConfiguration):
    def __init__(self):
        super().__init__(transform_config=ExtremeTokenizedTransformConfiguration())


class ExtremeTokenized:
    def __init__(self, **kwargs):
        self.params = {}
        for key in kwargs:
            self.params[key] = kwargs[key]
        # if input_folder and output_folder are specified, then assume it is represent data_local_config
        try:
            local_conf = {k: self.params[k] for k in ("input_folder", "output_folder")}
            self.params["data_local_config"] = ParamsUtils.convert_to_ast(local_conf)
            del self.params["input_folder"]
            del self.params["output_folder"]
        except:
            pass

    def transform(self):
        sys.argv = ParamsUtils.dict_to_req(d=self.params)
        launcher = PythonTransformLauncher(ExtremeTokenizedPythonTransformConfiguration())
        return_code = launcher.launch()
        return return_code


if __name__ == "__main__":
    launcher = PythonTransformLauncher(ExtremeTokenizedPythonTransformConfiguration())
    logger.info("Launching Extreme Tokenized Annotator transform")
    launcher.launch()
