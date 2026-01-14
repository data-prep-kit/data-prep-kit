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
import shutil

from data_processing.runtime.pure_python import PythonTransformLauncher
from data_processing.utils import ParamsUtils
from dpk_text_encoder.transform import (
    model_name_cli_param,
    content_column_name_cli_param,
    output_embeddings_column_name_cli_param,
)
from dpk_text_encoder.runtime import TextEncoderPythonTransformConfiguration


# create parameters
input_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "test-data", "input"))
output_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "output"))
local_conf = {
    "input_folder": input_folder,
    "output_folder": output_folder,
}
code_location = {"github": "github", "commit_hash": "12345", "path": "path"}
params = {
    # Data access. Only required parameters are specified
    "data_local_config": ParamsUtils.convert_to_ast(local_conf),
    # execution info
    "runtime_pipeline_id": "pipeline_id",
    "runtime_job_id": "job_id",
    "runtime_code_location": ParamsUtils.convert_to_ast(code_location),
    "data_checkpointing": False,
    # text_encoder params
    model_name_cli_param: "ibm-granite/granite-embedding-small-english-r2",
    content_column_name_cli_param: "contents",
    output_embeddings_column_name_cli_param: "embeddings",
}
if __name__ == "__main__":
    # Set the simulated command line args
    sys.argv = ParamsUtils.dict_to_req(d=params)
    # rm output_folder if exists already
    if os.path.exists(output_folder):
        shutil.rmtree(output_folder) 
    os.makedirs(output_folder)
    # create launcher
    launcher = PythonTransformLauncher(runtime_config=TextEncoderPythonTransformConfiguration())
    # Launch the ray actor(s) to process the input
    launcher.launch()
