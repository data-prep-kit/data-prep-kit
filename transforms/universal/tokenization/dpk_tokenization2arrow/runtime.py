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

import sys

from data_processing.runtime.pure_python import (
    PythonTransformLauncher,
    PythonTransformRuntimeConfiguration,
    Transform,
)
from data_processing.utils import ParamsUtils
from dpk_tokenization2arrow.transform import Tokenization2ArrowTransformConfiguration


class Tokenization2ArrowPythonConfiguration(PythonTransformRuntimeConfiguration):
    def __init__(self):
        super().__init__(transform_config=Tokenization2ArrowTransformConfiguration())


class Tokenization2Arrow(Transform):
    def __init__(self, **kwargs):
        super().__init__(Tokenization2ArrowPythonConfiguration(), **kwargs)


if __name__ == "__main__":
    launcher = PythonTransformLauncher(Tokenization2ArrowPythonConfiguration())
    launcher.launch()
