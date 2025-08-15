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

from data_processing.utils import ParamsUtils
from data_processing_ibm.data_access.data_access_factory_ibm import DataAccessFactoryIBM
from data_processing_ray.runtime.ray import RayTransformLauncher
from dpk_dom2parquet.transform import (
    default_disable_tab_str,
    default_html_column_name,
    default_text_column_name,
    disable_tab_str_cli_param,
    html_column_name_cli_param,
    text_column_name_cli_param,
)
from dpk_dom2parquet.ray.runtime import (
    CodeDocCleanerRayTransformConfiguration,
)

# create parameters
basedir = os.path.abspath(os.path.dirname(__file__))
if os.path.exists(os.path.join(basedir, "..", "test-data")):
    basedir = os.path.join(basedir, "..")
input_folder = os.path.abspath(os.path.join(basedir, "test-data", "input"))
output_folder = os.path.abspath(os.path.join(basedir, "output_local_ray"))
local_conf = {
    "input_folder": input_folder,
    "output_folder": output_folder,
}

# code doc cleaner parameters
cdc_params = {
    disable_tab_str_cli_param: default_disable_tab_str,
    html_column_name_cli_param: default_html_column_name,
    text_column_name_cli_param: default_text_column_name,
}

# RayTransform parameters
worker_options = {"num_cpus": 0.8}
params = {
    # where to run
    "run_locally": True,
    # Data access. Only required parameters are specified
    "data_local_config": ParamsUtils.convert_to_ast(local_conf),
    # orchestrator
    "runtime_worker_options": ParamsUtils.convert_to_ast(worker_options),
    "runtime_num_workers": 1,
    "runtime_pipeline_id": "pipeline_id",
    "runtime_job_id": "job_id",
    "runtime_creation_delay": 0,
    **cdc_params,
}


if __name__ == "__main__":
    # Set the simulated command line args
    sys.argv = ParamsUtils.dict_to_req(d=params)
    # create launcher
    launcher = RayTransformLauncher(CodeDocCleanerRayTransformConfiguration(), DataAccessFactoryIBM())
    # Launch the ray actor(s) to process the input
    launcher.launch()
