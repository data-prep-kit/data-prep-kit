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
from data_processing_ray.runtime.ray import (
    DefaultRayTransformRuntime,
    RayTransformLauncher,
)
from data_processing_ray.runtime.ray.runtime_configuration import (
    RayTransformRuntimeConfiguration,
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


class Blocklist:
    def __init__(self, **kwargs):
        self.params = {}
        for key in kwargs:
            self.params[key] = kwargs[key]
        # if input_folder and output_folder are specified, then assume it is represent data_local_config
        try:
            local_conf = {k: self.params[k] for k in ("input_folder", "output_folder")}
            self.params["data_local_config"] = ParamsUtils.convert_to_ast(local_conf)
            del self.params["input_folder"]
            del self.params["output_folder"]
        except:
            pass
        try:
            worker_options = {k: self.params[k] for k in ("num_cpus", "memory")}
            self.params["runtime_worker_options"] = ParamsUtils.convert_to_ast(worker_options)
            del self.params["num_cpus"]
            del self.params["memory"]
        except:
            pass

    def transform(self):
        sys.argv = ParamsUtils.dict_to_req(d=(self.params))
        launcher = RayTransformLauncher(BlockListConfiguration())
        return_code = launcher.launch()
        return return_code


class BlockListRuntime(DefaultRayTransformRuntime):
    """
    BlockList runtime runtime support
    """

    def __init__(self, params: dict[str, Any]):
        """
        Create filter runtime
        :param params: parameters, that should include
            ls_lang_column_key: name of the column with language
            ls_allowed_langs_file_key: location of the allowed languages file
            ls_known_selector: A flag on whether return rows with valid or invalid languages
        """
        super().__init__(params)
        from data_processing.utils import get_logger

        self.logger = get_logger(__name__)

    def get_transform_config(
        self,
        data_access_factory: DataAccessFactoryBase,
        statistics: ActorHandle,
        files: list[str],
    ) -> dict[str, Any]:

        return self.params


class BlockListRayConfiguration(RayTransformRuntimeConfiguration):
    def __init__(self):
        super().__init__(transform_config=BlockListConfiguration(), runtime_class=BlockListRuntime)


if __name__ == "__main__":
    launcher = RayTransformLauncher(BlockListRayConfiguration())
    launcher.launch()
