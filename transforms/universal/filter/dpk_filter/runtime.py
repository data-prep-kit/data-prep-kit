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
from data_processing.utils import ParamsUtils, get_dpk_logger
from dpk_filter.transform import FilterTransformConfiguration


logger = get_dpk_logger()


class FilterPythonTransformConfiguration(PythonTransformRuntimeConfiguration):
    def __init__(self):
        super().__init__(transform_config=FilterTransformConfiguration())


class Filter(Transform):
    def __init__(self, **kwargs):
        super().__init__(FilterPythonTransformConfiguration(), **kwargs)


if __name__ == "__main__":
    launcher = PythonTransformLauncher(FilterPythonTransformConfiguration())
    logger.info("Launching filtering")
    launcher.launch()
