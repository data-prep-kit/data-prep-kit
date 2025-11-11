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

from data_processing.utils import get_dpk_logger
from data_processing_ray.runtime.ray import RayTransformLauncher
from data_processing_ray.runtime.ray import (
    RayTransformRuntimeConfiguration,
    Transform
)
from dpk_faces.transform import FacesTransformConfiguration

logger = get_dpk_logger()


class FacesRayTransformConfiguration(RayTransformRuntimeConfiguration):
    """
    Implements the RayTransformConfiguration for Proto as required by the RayTransformLauncher.
    Proto does not use a RayRuntime class so the superclass only needs the base
    python-only configuration.
    """

    def __init__(self):
        """
        Initialization
        :param base_configuration - base configuration class
        """
        super().__init__(transform_config=FacesTransformConfiguration())


class Faces(Transform):
    def __init__(self, **kwargs):
        super().__init__(FacesTransformConfiguration(), **kwargs)


if __name__ == "__main__":
    launcher = RayTransformLauncher(FacesRayTransformConfiguration())
    launcher.launch()
