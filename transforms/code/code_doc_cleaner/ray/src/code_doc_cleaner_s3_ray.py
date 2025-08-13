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
from data_processing_ibm.utils import DPKConfigIBM
from data_processing_ray.runtime.ray import RayTransformLauncher
from code_doc_cleaner_transform import (
    default_disable_tab_str,
    default_html_column_name,
    default_text_column_name,
    disable_tab_str_cli_param,
    html_column_name_cli_param,
    text_column_name_cli_param,
)
from code_doc_cleaner_transform_ray_ibm import (
    CodeDocCleanerRayTransformConfiguration,
)


# create parameters
s3_cred = {
    "access_key": os.environ.get("DPL_S3_ACCESS_KEY") or DPKConfigIBM.S3_ACCESS_KEY,
    "secret_key": os.environ.get("DPL_S3_SECRET_KEY") or DPKConfigIBM.S3_SECRET_KEY,
    "url": "https://s3.us-east.cloud-object-storage.appdomain.cloud",
}

# Configure s3 folders
s3_conf = {
    "input_folder": "cos-optimal-llm-pile/test/mmuraoka/code_doc_clean/input/",
    "output_folder": "cos-optimal-llm-pile/test/mmuraoka/code_doc_clean/output_s3_ray/",
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
    "data_s3_cred": ParamsUtils.convert_to_ast(s3_cred),
    "data_s3_config": ParamsUtils.convert_to_ast(s3_conf),
    # orchestrator
    "runtime_worker_options": ParamsUtils.convert_to_ast(worker_options),
    "runtime_num_workers": 1,
    "runtime_pipeline_id": "pipeline_id",
    "runtime_job_id": "job_id",
    "runtime_creation_delay": 0,
    **cdc_params,
}


if __name__ == "__main__":
    # Set the similated command line args
    sys.argv = ParamsUtils.dict_to_req(d=params)
    # create launcher
    launcher = RayTransformLauncher(CodeDocCleanerRayTransformConfiguration(), DataAccessFactoryIBM())
    # launch the ray actor(s) to process the input
    launcher.launch()
