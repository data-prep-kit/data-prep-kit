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
from data_processing.utils import ParamsUtils, get_logger
from data_processing_ray.runtime.ray import RayTransformLauncher
from data_processing_ray.runtime.ray.runtime_configuration import (
    RayTransformRuntimeConfiguration,
)
from dpk_tokenization.transform import TokenizationTransformConfiguration


logger = get_logger(__name__)


class TokenizationRayConfiguration(RayTransformRuntimeConfiguration):
    def __init__(self):
   
        super().__init__(transform_config=TokenizationTransformConfiguration())

class Tokenization:
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
        launcher = RayTransformLauncher(TokenizationRayConfiguration())
        return_code = launcher.launch()
        return return_code
    


if __name__ == "__main__":
    launcher = RayTransformLauncher(TokenizationRayConfiguration())
    logger.info("Launching Tokenization transform")
    launcher.launch()
