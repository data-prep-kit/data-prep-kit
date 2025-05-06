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
from typing import Any

from data_processing.data_access import DataAccessFactoryBase
from data_processing.utils import ParamsUtils, get_logger
from data_processing_ray.runtime.ray import RayTransformLauncher
from data_processing_ray.runtime.ray.runtime_configuration import (
    DefaultRayTransformRuntime,
    RayTransformRuntimeConfiguration,
)
from dpk_comment_cleanser.transform import (
    CommentCleanserTransformConfiguration,
    COLUMN_KEY,
)
from ray.actor import ActorHandle


logger = get_logger(__name__)


class CommentCleanserRuntime(DefaultRayTransformRuntime):
    """
    Language selector runtime support
    """

    def __init__(self, params: dict[str, Any]):
        """
        Create comment cleanser runtime
        :param params: parameters, that should include
            comment_cleanser_content_column_key: name of the column 
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
        """
        :param data_access_factory - data access factory
        :param statistics - reference to the statistics object
        :param files - list of files to process
        :return: dictionary of filter init params
        """
        return self.params


class CommentCleanserRayConfiguration(RayTransformRuntimeConfiguration):
    def __init__(self):
        super().__init__(transform_config=CommentCleanserTransformConfiguration(), runtime_class=CommentCleanserRuntime)


class CommentCleanser:
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

    def transform(self):
        sys.argv = ParamsUtils.dict_to_req(d=(self.params))
        # create launcher
        launcher = RayTransformLauncher(CommentCleanserRayConfiguration())
        # launch
        return_code = launcher.launch()
        return return_code


if __name__ == "__main__":
    launcher = RayTransformLauncher(CommentCleanserRayConfiguration())
    launcher.launch()