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
from typing import Any

from data_processing.data_access import DataAccess
from data_processing.utils import CLIArgumentProvider, get_logger
from data_processing_ray.runtime.ray import (
    DefaultRayTransformRuntime,
    RayTransformLauncher,
    RayTransformRuntimeConfiguration,
)
from dpk_fdedup.get_duplicate_list.transform import (
    GetDuplicateListTransformConfiguration,
    subfolder_key,
)


logger = get_logger(__name__)


class GetDuplicateListRayRuntime(DefaultRayTransformRuntime):
    """
    Get duplicate list runtime support for Ray
    """

    def __init__(self, params: dict[str, Any]):
        super().__init__(params=params)
        self.logger = get_logger(__name__)

    def get_folders(self, data_access: DataAccess) -> list[str]:
        """
        Return the set of folders that will be processed by this transform
        :param data_access - data access object
        :return: list of folder paths
        """
        return [self.params[subfolder_key]]


class GetDuplicateListRayTransformConfiguration(RayTransformRuntimeConfiguration):
    """
    Implements the RayTransformConfiguration for Fuzzy Dedup Get Duplicate List
    as required by the RayTransformLauncher.
    """

    def __init__(self):
        """
        Initialization
        """
        super().__init__(
            transform_config=GetDuplicateListTransformConfiguration(),
            runtime_class=GetDuplicateListRayRuntime,
        )


if __name__ == "__main__":
    launcher = RayTransformLauncher(GetDuplicateListRayTransformConfiguration())
    logger.info("Launching fuzzy dedup get duplicate list ray transform")
    launcher.launch()
