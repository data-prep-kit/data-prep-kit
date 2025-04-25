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
import json
import os
import sys

from data_processing.runtime.pure_python import PythonTransformLauncher
from data_processing.utils import ParamsUtils

from dpk_mm.p2j.transform_python import Parquet2JsonPythonTransformConfiguration

# create parameters
input_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "test-data", "j2p", "expected"))
output_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output"))
local_conf = {
    "input_folder": input_folder,
    "output_folder": output_folder,
}
code_location = {"github": "github", "commit_hash": "12345", "path": "path"}

# Need to change parameter setup, for selecting columns in parquet
params = {
    # Data access. Only required parameters are specified
    "data_local_config": ParamsUtils.convert_to_ast(local_conf),
    "data_files_to_use": '[".parquet"]', # no use
    # execution info
    "runtime_pipeline_id": "pipeline_id",
    "runtime_job_id": "job_id",
    "runtime_code_location": ParamsUtils.convert_to_ast(code_location),
    # transform config
    "p2j_as_jsonl": False,
    "p2j_write_images": True, # add write image para

    "p2j_write_image_path": 'images', # add write image path, need to change to cooperate with cos
    "p2j_export_columns": ['id', 'orig_image_fpaths', 'conversations', 'fixed_image_fpaths', 'image_bins'], # add customized columns to export

    #"p2j_write_image_path": 'blurred_images', # add write image path, need to change to cooperate with cos
    #"p2j_export_columns": ['id', 'orig_image_fpaths', 'conversations', 'fixed_image_fpaths', 'blurred_images'],
    # add customized columns to export
}
if __name__ == "__main__":
    # Set the simulated command line args

    sys.argv = ParamsUtils.dict_to_req(d=params)
    # sys.argv = [ "python", "--help"]
    # create launcher
    launcher = PythonTransformLauncher(runtime_config=Parquet2JsonPythonTransformConfiguration())
    # Launch the ray actor(s) to process the input
    launcher.launch()
    # fname = output_folder + "/sample.json"
    # with open(fname) as f:
    #     d = json.load(f)
    #     print(str(d))
