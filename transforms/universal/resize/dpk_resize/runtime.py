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
from data_processing.runtime.pure_python import PythonTransformLauncher
from data_processing.runtime.pure_python import (
    PythonTransformRuntimeConfiguration,
    Transform,
)
from data_processing.utils import ParamsUtils, get_logger
from dpk_resize.transform import ResizeTransformConfiguration


logger = get_logger(__name__)


class ResizePythonTransformConfiguration(PythonTransformRuntimeConfiguration):
    """
    Implements the RayTransformConfiguration for resize as required by the RayTransformLauncher.
    """
    def __init__(self):
        super().__init__(transform_config=ResizeTransformConfiguration())


class Resize(Transform):
    """
    For use with Notebook and python scripts
    """
    def __init__(self, **kwargs):
        super().__init__(ResizeTransformConfiguration(), **kwargs)


if __name__ == "__main__":
    """
    Fur use with Command line and doccker containers
    """
    Transform.launch(ResizeTransformConfiguration())
