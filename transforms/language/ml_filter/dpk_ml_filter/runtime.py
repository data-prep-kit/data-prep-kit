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
import argparse, sys, os, json
from data_processing.runtime.pure_python import PythonTransformLauncher
from data_processing.runtime.pure_python.runtime_configuration import (
    PythonTransformRuntimeConfiguration,
)

from data_processing.transform import TransformConfiguration
from data_processing.utils import get_logger, CLIArgumentProvider, UnrecoverableException, ParamsUtils
from dpk_ml_filter.transform import MLFilterTransform, get_transform_params, short_name

logger = get_logger(__name__)

class MLFilterConfiguration(TransformConfiguration):
    """
    Provides support for configuring and using the associated Transform class include
    configuration with CLI args and combining of metadata.
    """
    def __init__(self):
        super().__init__(
            name=short_name,
            transform_class=MLFilterTransform,
        )
        from data_processing.utils import get_logger
        self.logger = get_logger(__name__)

    def add_input_params(self, parser: argparse.ArgumentParser) -> None:
        """
        Add Transform-specific arguments to the given  parser.
        This will be included in a dictionary used to initialize the NOOPTransform.
        By convention a common prefix should be used for all transform-specific CLI args
        (e.g, noop_, pii_, etc.)
        """
        for key, key_type, key_default, key_help in get_transform_params():
            parser.add_argument(f"--{short_name}_{key}", type=key_type, default=key_default, help=key_help)

    def apply_input_params(self, args: argparse.Namespace) -> bool:
        """
        Validate and apply the arguments that have been parsed
        :param args: user defined arguments.
        :return: True, if validate pass or False otherwise
        """
        captured = CLIArgumentProvider.capture_parameters(args, f"{short_name}_", False)

        self.params = self.params | captured
        self.logger.info(f"Filtering parameters are: {json.dumps(self.params)}")
        return True


class MLFilterRuntime(PythonTransformRuntimeConfiguration):
    def __init__(self):
        super().__init__(transform_config=MLFilterConfiguration())


class MLFilter:
    def __init__(self, **kwargs):
        self.params = {}
        for key in kwargs:
            self.params[key] = kwargs[key]
        # if input_folder and output_folder are specified, then assume it is data_local_config
        try:
            local_conf = {k: self.params[k] for k in ("input_folder", "output_folder")}
            self.params["data_local_config"] = ParamsUtils.convert_to_ast(local_conf)
            del self.params["input_folder"]
            del self.params["output_folder"]
        except:
            pass

    def transform(self):
        sys.argv = ParamsUtils.dict_to_req(d=(self.params))
        launcher = PythonTransformLauncher(MLFilterRuntime())
        return_code = launcher.launch()
        return return_code

if __name__ == "__main__":
    launcher = PythonTransformLauncher(MLFilterRuntime())
    logger.info("Launching language dependent filtering transform")
    launcher.launch()
