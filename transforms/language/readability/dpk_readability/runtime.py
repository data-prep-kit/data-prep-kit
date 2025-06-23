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

import argparse
import ast
import sys
from argparse import ArgumentParser, Namespace

from data_processing.data_access import DataAccessFactory
from data_processing.runtime.pure_python import PythonTransformLauncher
from data_processing.runtime.pure_python.runtime_configuration import (
    PythonTransformRuntimeConfiguration,
)
from data_processing.transform import TransformConfiguration
from data_processing.utils import CLIArgumentProvider, ParamsUtils, get_logger, str2bool
from dpk_readability.common import (
    automated_readability_index_textstat,
    cli_prefix,
    coleman_liau_index_textstat,
    contents_column_name_cli_param,
    contents_column_name_default,
    dale_chall_readability_score_textstat,
    difficult_words_textstat,
    flesch_ease_textstat,
    flesch_kincaid_textstat,
    gunning_fog_textstat,
    linsear_write_formula_textstat,
    mcalpine_eflaw_textstat,
    reading_time_textstat,
    score_list_cli_param,
    score_list_default,
    short_name,
    smog_index_textstat,
    spache_readability_textstat,
    text_standard_textstat,
)
from dpk_readability.transform import ReadabilityTransform


logger = get_logger(__name__)


class ReadabilityTransformConfiguration(TransformConfiguration):
    """
    Provides support for configuring and using the associated Transform class include
    configuration with CLI args and combining of metadata.
    """

    def __init__(self):
        super().__init__(
            name=short_name,
            transform_class=ReadabilityTransform,
        )
        self.daf = None

    def add_input_params(self, parser: ArgumentParser) -> None:
        """
        Add Transform-specific arguments to the given  parser.
        This will be included in a dictionary used to initialize the NOOPTransform.
        By convention a common prefix should be used for all transform-specific CLI args
        (e.g, noop_, pii_, etc.)
        """
        valid_values = {
            flesch_ease_textstat,
            flesch_kincaid_textstat,
            gunning_fog_textstat,
            smog_index_textstat,
            coleman_liau_index_textstat,
            automated_readability_index_textstat,
            dale_chall_readability_score_textstat,
            difficult_words_textstat,
            linsear_write_formula_textstat,
            text_standard_textstat,
            spache_readability_textstat,
            mcalpine_eflaw_textstat,
            reading_time_textstat,
        }

        def validate_scores(x):
            if x.startswith("[") and x.endswith("]"):
                scores = ast.literal_eval(x)
                if not all(score in valid_values for score in scores):
                    raise argparse.ArgumentTypeError(f"Invalid scores in list. Allowed scores: {valid_values}")
                return scores
            elif x in valid_values:
                return x
            else:
                raise argparse.ArgumentTypeError(f"Invalid score: {x}. Allowed scores: {valid_values}")

        parser.add_argument(
            f"--{contents_column_name_cli_param}",
            type=str,
            required=False,
            default=contents_column_name_default,
            help="contents column name for input parquet table to transform",
        )

        parser.add_argument(
            f"--{score_list_cli_param}",
            type=validate_scores,
            required=False,
            default=score_list_default,
            help=f"list of readability scores to be computed by the transform; valid values: {valid_values}",
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

        logger.info(f"Readability parameters are : {self.params}")
        # Add the DataAccessFactory to the transform's configuration parameters.
        return True


class ReadabilityPythonTransformConfiguration(PythonTransformRuntimeConfiguration):
    """
    Implements the PythonTransformConfiguration for PII as required by the PythonTransformLauncher.
    PII does not use a RayRuntime class so the superclass only needs the base
    python-only configuration.
    """

    def __init__(self):
        """
        Initialization
        :param base_configuration - base configuration class
        """
        super().__init__(transform_config=ReadabilityTransformConfiguration())


class Readability:
    def __init__(self, **kwargs):
        self.params = {}
        for key in kwargs:
            self.params[key] = kwargs[key]
        try:
            local_conf = {k: self.params[k] for k in ("input_folder", "output_folder")}
            self.params["data_local_config"] = ParamsUtils.convert_to_ast(local_conf)
            del self.params["input_folder"], self.params["output_folder"]
        except:
            pass
        try:
            worker_options = {k: self.params[k] for k in ("num_cpus", "memory")}
            self.params["runtime_worker_options"] = ParamsUtils.convert_to_ast(worker_options)
            del self.params["num_cpus"], self.params["memory"]
        except:
            pass

    def transform(self):
        sys.argv = ParamsUtils.dict_to_req(d=self.params)
        launcher = PythonTransformLauncher(ReadabilityPythonTransformConfiguration())
        return_code = launcher.launch()
        return return_code


if __name__ == "__main__":
    launcher = PythonTransformLauncher(ReadabilityPythonTransformConfiguration())
    logger.info("Launching Readability transform")
    launcher.launch()
