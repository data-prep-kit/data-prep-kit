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
import sys

from data_processing.utils import ParamsUtils
from data_processing_ray.runtime.ray import RayTransformLauncher
from dpk_gneissweb_classification.ray.transform import ClassificationRayTransformConfiguration
from dpk_gneissweb_classification.transform import (
    content_column_name_cli_param,
    model_credential_cli_param,
    model_file_name_cli_param,
    model_url_cli_param,
    output_label_column_name_cli_param,
    output_score_column_name_cli_param,
    n_processes_cli_param
)



print(os.environ)
# create launcher
launcher = RayTransformLauncher(ClassificationRayTransformConfiguration())
# create parameters
s3_cred = {
    "access_key": "localminioaccesskey",
    "secret_key": "localminiosecretkey",
    "url": "http://localhost:9000",
}
s3_conf = {
    "input_folder": "test/gneissweb_classification/input",
    "output_folder": "test/gneissweb_classification/output",
}


worker_options = {"num_cpus": 0.8}
code_location = {"github": "github", "commit_hash": "12345", "path": "path"}
params = {
    # where to run
    "run_locally": True,
    # Data access. Only required parameters are specified
    "data_s3_cred": ParamsUtils.convert_to_ast(s3_cred),
    "data_s3_config": ParamsUtils.convert_to_ast(s3_conf),
    # orchestrator
    "runtime_worker_options": ParamsUtils.convert_to_ast(worker_options),
    "runtime_num_workers": 3,
    "runtime_pipeline_id": "pipeline_id",
    "runtime_job_id": "job_id",
    "runtime_creation_delay": 0,
    "runtime_code_location": ParamsUtils.convert_to_ast(code_location),
    # classification params
    model_credential_cli_param: os.environ.get('HF_READ_ACCESS_TOKEN', "PUT YOUR OWN HUGGINGFACE CREDENTIAL"),
    model_file_name_cli_param: ["fasttext_medical.bin"],
    model_url_cli_param:["ibm-granite/GneissWeb.Med_classifier"],
    content_column_name_cli_param: ["text"],
    output_label_column_name_cli_param: ["ft_label"],
    output_score_column_name_cli_param: ["ft_score"],
    n_processes_cli_param: 1,
}
sys.argv = ParamsUtils.dict_to_req(d=params)
# for arg in sys.argv:
#     print(arg)

# launch
launcher.launch()
