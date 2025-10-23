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

from typing import Any

from data_processing.data_access import DataAccessFactoryBase
from data_processing.utils import get_dpk_logger
from data_processing_ray.runtime.ray import (
    DefaultRayTransformRuntime,
    RayTransformLauncher,
    RayTransformRuntimeConfiguration,
    Transform,
)
from dpk_blocklist.transform import (
    BlockListConfiguration,
    _get_domain_list,
    annotation_column_name_key,
    blocked_domain_list_path_key,
    blocklist_data_factory_key,
    source_url_column_name_key,
)
from ray.actor import ActorHandle

logger = get_dpk_logger()


class BlockListRuntime(DefaultRayTransformRuntime):
    """
    BlockList runtime support
    """

    def __init__(self, params: dict[str, Any]):
        """
        Create blocklist runtime
        :param params: parameters, that should include
            blocked_domain_list_path_key: path to domain blocklist files
            annotation_column_name_key: name of the annotation column
            source_url_column_name_key: name of the source URL column
        """
        super().__init__(params)
        self.logger = get_dpk_logger()

    def get_transform_config(
        self,
        data_access_factory: DataAccessFactoryBase,
        statistics: ActorHandle,
        files: list[str],
    ) -> dict[str, Any]:
        """
        Set environment for blocklist execution
        :param data_access_factory - data access factory
        :param statistics - reference to the statistics object
        :param files - list of files to process
        :return: dictionary of blocklist init params
        """
        return self.params


class BlockListRayConfiguration(RayTransformRuntimeConfiguration):
    def __init__(self):
        super().__init__(transform_config=BlockListConfiguration(), runtime_class=BlockListRuntime)


class Blocklist(Transform):
    def __init__(self, **kwargs):
        super().__init__(BlockListConfiguration(), **kwargs)


if __name__ == "__main__":
    launcher = RayTransformLauncher(BlockListRayConfiguration())
    launcher.launch()
