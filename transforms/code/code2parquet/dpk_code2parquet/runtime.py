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

import os
import sys

from data_processing.runtime.pure_python import PythonTransformLauncher
from data_processing.runtime.pure_python import (
    PythonTransformRuntimeConfiguration,
    Transform,
)
from data_processing.utils import ParamsUtils, get_logger
from dpk_code2parquet.transform import (
    CodeToParquetTransform,
    CodeToParquetTransformConfiguration,
    data_factory_key,
    detect_programming_lang_cli_key,
    detect_programming_lang_default,
    detect_programming_lang_key,
    get_supported_languages,
    supported_langs_file_cli_key,
    supported_langs_file_key,
)


logger = get_logger(__name__)


class CodeToParquetPythonConfiguration(PythonTransformRuntimeConfiguration):
    def __init__(self):
        super().__init__(transform_config=CodeToParquetTransformConfiguration(transform_class=CodeToParquetTransform))


class Code2Parquet(Transform):
    def __init__(self, **kwargs):
        super().__init__(CodeToParquetTransformConfiguration(), **kwargs)
        

if __name__ == "__main__":
    # launcher = NOOPRayLauncher()
    launcher = PythonTransformLauncher(CodeToParquetPythonConfiguration())
    logger.info("Launching noop transform")
    launcher.launch()
