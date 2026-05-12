# SPDX-License-Identifier: Apache-2.0
# (C) Copyright IBM Corp. 2024.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#  http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################

import os
import sys
from pathlib import Path

from data_processing.utils import ParamsUtils, get_dpk_logger
from data_processing_ray.runtime.ray import RayTransformLauncher
from dpk_yara.ray.runtime import YaraRayTransformConfiguration


logger = get_dpk_logger()

here = os.path.dirname(__file__)
input_folder = os.path.abspath(os.path.join(here, "..", "..", "test-data", "input"))
output_folder = os.path.abspath(os.path.join(here, "..", "..", "output"))
rules_dir = os.path.abspath(os.path.join(here, "..", "..", "test-rules"))

local_conf = {
    "input_folder": input_folder,
    "output_folder": output_folder,
}
yara_params = {
    "yara_input_column": "binary_contents",
    "yara_rules_dir": rules_dir,
}
worker_options = {"num_cpus": 0.8}
code_location = {"github": "github", "commit_hash": "12345", "path": "path"}
params = {
    "run_locally": True,
    "data_local_config": ParamsUtils.convert_to_ast(local_conf),
    "runtime_worker_options": ParamsUtils.convert_to_ast(worker_options),
    "runtime_num_workers": 3,
    "runtime_pipeline_id": "pipeline_id",
    "runtime_job_id": "job_id",
    "runtime_creation_delay": 0,
    "runtime_code_location": ParamsUtils.convert_to_ast(code_location),
}

if __name__ == "__main__":
    Path(output_folder).mkdir(parents=True, exist_ok=True)
    sys.argv = ParamsUtils.dict_to_req(d=params | yara_params)
    launcher = RayTransformLauncher(YaraRayTransformConfiguration())
    launcher.launch()
