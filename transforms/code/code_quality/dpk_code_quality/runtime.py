# SPDX-License-Identifier: Apache-2.0
# (C) Copyright IBM Corp. 2024.
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################

CODE_QUALITY_PARAMS = "code_quality"
import sys
from argparse import ArgumentParser, Namespace
from dpk_code_quality.transform import CodeQualityTransformConfiguration
from dpk_code_quality.transform import CodeQualityTransform
from data_processing.runtime.pure_python import (
    PythonTransformLauncher,
    PythonTransformRuntimeConfiguration,
    Transform
)

from data_processing.transform import TransformConfiguration
from data_processing.utils import ParamsUtils, CLIArgumentProvider, get_logger
from data_processing.runtime.pure_python import PythonTransformLauncher
from data_processing.runtime.pure_python.runtime_configuration import (
    PythonTransformRuntimeConfiguration,
)

logger = get_logger(__name__)



class CodeQualityConfiguration(TransformConfiguration):
    def __init__(self):
        super().__init__(name="code_quality", transform_class=CodeQualityTransform)

    def add_input_params(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--cq_contents_column_name",
            required=False,
            type=str,
            dest="contents_column_name",
            default="contents",
            help="Name of the column holds the data to process",
        )
        parser.add_argument(
            "--cq_language_column_name",
            required=False,
            type=str,
            dest="language_column_name",
            default="language",
            help="Name of the column holds the programming language details.",
        )
        parser.add_argument(
            "--cq_tokenizer",
            required=False,
            type=str,
            dest="tokenizer",
            default="codeparrot/codeparrot",
            help="Name or path to the tokenizer.",
        )
        parser.add_argument(
            "--cq_hf_token",
            required=False,
            type=str,
            dest="hf_token",
            default="",
            help="Huggingface auth token to download and use the tokenizer.",
        )

    def apply_input_params(self, args: Namespace) -> bool:
        dargs = vars(args)

        self.params = {
            CODE_QUALITY_PARAMS: {
                "contents_column_name": dargs.get("contents_column_name"),
                "language_column_name": dargs.get("language_column_name"),
                "tokenizer": dargs.get("tokenizer"),
                "hf_token": dargs.get("hf_token"),
            }
        }

        return True

class CodeQualityRuntime(PythonTransformRuntimeConfiguration):
    def __init__(self):
        super().__init__(transform_config=CodeQualityConfiguration())
        

class CodeQuality(Transform):
    def __init__(self, **kwargs):
        super().__init__(CodeQualityTransformConfiguration(), **kwargs)
    

class CodeQualityPythonTransformConfiguration(PythonTransformRuntimeConfiguration):
    def __init__(self):
        super().__init__(transform_config=CodeQualityTransformConfiguration())


if __name__ == "__main__":
    launcher = PythonTransformLauncher(CodeQualityPythonTransformConfiguration())
    launcher.launch()