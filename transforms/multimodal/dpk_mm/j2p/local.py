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

from data_processing.runtime.pure_python import PythonTransformLauncher
from data_processing.utils import ParamsUtils

from dpk_mm.j2p.transform_python import Json2ParquetPythonTransformConfiguration

# create parameters
input_folder = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "test-data", "j2j", "expected")
)
output_folder = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "output")
)
image_path_prefix_alias = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__), "..", "..", "test-data", "j2j", "input", "images"
    )
)  # Parent directory containing the image subdirectories and original json file.

local_conf = {
    "input_folder": input_folder,
    "output_folder": output_folder,
}
code_location = {"github": "github", "commit_hash": "12345", "path": "path"}

params = {
    # Data access. Only required parameters are specified
    "data_files_to_use": '[".json"]',
    "data_local_config": ParamsUtils.convert_to_ast(local_conf),
    # Data access. Only required parameters are specified
    # "data_s3_cred": ParamsUtils.convert_to_ast(s3_cred),
    # "data_s3_config": ParamsUtils.convert_to_ast(s3_conf),
    # execution info
    "runtime_pipeline_id": "pipeline_id",
    "runtime_job_id": "job_id",
    "runtime_code_location": ParamsUtils.convert_to_ast(code_location),
    # j2p args
    "j2p_image_path_prefix": "/proj/mmfm/data/DocLayNet_v2_kv_instruct",  # Need to have the trailing slash prefix
    "j2p_image_path_prefix_alias": image_path_prefix_alias,  # Need to have the slash COS Prefix alias
    "j2p_parquet_size_limit": (200 * 1024 * 1024),  # 200 MB
    # "j2p_secondary_data_access_config": ParamsUtils.convert_to_ast(cos_config),
    # Sample cos_config = {"access_key": "...", "secret_key": "...", "url": "...", "region": "..", "output_folder": "..",
}


if __name__ == "__main__":
    # Set the simulated command line args
    sys.argv = ParamsUtils.dict_to_req(d=params)
    # sys.argv = [ "python", "--help"]
    # create launcher
    launcher = PythonTransformLauncher(
        runtime_config=Json2ParquetPythonTransformConfiguration()
    )
    # Launch the ray actor(s) to process the input
    launcher.launch()
