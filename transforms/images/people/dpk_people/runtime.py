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

import time

from data_processing.runtime.pure_python import PythonTransformLauncher
from data_processing.runtime.pure_python import (
    PythonTransformRuntimeConfiguration,
    Transform
)
from data_processing.utils import get_dpk_logger

from dpk_people.transform import PeopleTransformConfiguration

logger = get_dpk_logger()


class PeoplePythonTransformConfiguration(PythonTransformRuntimeConfiguration):
    """
    Implements the PythonTransformConfiguration for People as required by the PythonTransformLauncher.
    People does not use a RayRuntime class so the superclass only needs the base
    python-only configuration.
    """

    def __init__(self):
        """
        Initialization
        :param base_configuration - base configuration class
        """
        super().__init__(transform_config=PeopleTransformConfiguration())


class People(Transform):
    def __init__(self, **kwargs):
        super().__init__(PeopleTransformConfiguration(), **kwargs)


if __name__ == "__main__":
    launcher = PythonTransformLauncher(PeoplePythonTransformConfiguration())
    launcher.launch()
