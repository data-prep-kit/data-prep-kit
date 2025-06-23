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
from psutil import cpu_count
from dpk_rep_removal.transform import RepRemovalTransform
from data_processing.transform import TransformConfiguration
from data_processing.utils import ParamsUtils, CLIArgumentProvider, get_logger
from argparse import ArgumentParser, Namespace
from data_processing.runtime.pure_python import PythonTransformLauncher
from data_processing.runtime.pure_python.runtime_configuration import (
    PythonTransformRuntimeConfiguration,)

logger = get_logger(__name__)

# defaults - these are the values used
cli_prefix = "rep_removal_"


class RepRemovalTransformConfiguration(TransformConfiguration):
    def __init__(self):
        super().__init__(name='rep_removal', transform_class=RepRemovalTransform)

        self.daf = None

    def add_input_params(self, parser: ArgumentParser) -> None:
        """
        Add Transform-specific arguments to the given parser.
        This will be included in a dictionary used to initialize the BlockListTransform.
        By convention a common prefix should be used for all mutator-specific CLI args
        (e.g, noop_, pii_, etc.)
        """
        # The DataAccess created by the DataAccessFactory below will use this url
        parser.add_argument(
            "--rep_removal_contents_column_name",
            type=str,
            required=False,
            default="contents",
            help="Name of the column holding the document text",
        )
        parser.add_argument(
            "--rep_removal_dedup_level_name",
            type=str,
            required=False,
            default="parquet",
            help="Name of the type of file to process.",
        )
        parser.add_argument(
            "--rep_removal_length_thresh",
            type=int,
            required=False,
            default=50,
            help="Length threshold for processing",
        )
        parser.add_argument(
            "--rep_removal_frequency_threshold",
            type=int,
            required=False,
            default=1,
            help="Frequency threshold for processing.",
        )
        parser.add_argument(
            "--rep_removal_retain_first_copy",
            type=str,
            required=False,
            default=True,
            help="Boolean value for whether to retain first copy",
        )
        parser.add_argument(
            "--rep_removal_tokenize",
            type=str,
            required=False,
            default=True,
            help="Boolean value for whether to tokenize",
        )
        parser.add_argument(
            "--rep_removal_num_threads",
            type=int,
            required=False,
            default=cpu_count(logical=False),
            help="Value for number of threads to use for processing",
        )
        parser.add_argument(
            "--rep_removal_num_cpus",
            type=int,
            required=False,
            default=cpu_count(logical=False),
            help="Value for number of cpus allocated for processing",
        )

    def apply_input_params(self, args: Namespace) -> bool:
        """
        Validate and apply the arguments that have been parsed
        :param args: user defined arguments.
        :return: True, if validate pass or False otherwise
        """
        # Capture the args that are specific to this transform
        captured = CLIArgumentProvider.capture_parameters(args, cli_prefix, True)
        self.params = self.params | captured
        return True


class RepRemovalPythonTransformConfiguration(PythonTransformRuntimeConfiguration):

    def __init__(self):
        super().__init__(transform_config=RepRemovalTransformConfiguration())


class RepRemoval:
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
        launcher = PythonTransformLauncher(RepRemovalPythonTransformConfiguration())
        return_code = launcher.launch()
        return return_code


if __name__ == "__main__":
    launcher = PythonTransformLauncher(RepRemovalPythonTransformConfiguration())
    launcher.launch()
