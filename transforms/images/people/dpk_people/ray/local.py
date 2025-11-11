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

from people_ray.people_transform_ray import PeopleRayTransformConfiguration

# create parameters
# When we have real test data we should switch to this
input_folder = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                            "../../../../../data-processing-lib/python/src/data_processing/multimodal/ray", "..", "test-data", "faces", "input"))
# for test.parquet in proto/python dir
#input_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
# For your own local files
#input_folder = "/Users/dawood/Downloads"
output_folder = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                             "../../../../../data-processing-lib/python/src/data_processing/multimodal/ray", "..", "output"))
local_conf = {
    "input_folder": input_folder,
    "output_folder": output_folder,
}
code_location = {"github": "github", "commit_hash": "12345", "path": "path"}
params = {
    # Ray Config
    "run_locally": True,
    # Data access. Only required parameters are specified
    "data_local_config": ParamsUtils.convert_to_ast(local_conf),
    # execution info
    "runtime_pipeline_id": "pipeline_id",
    "runtime_job_id": "job_id",
    "runtime_code_location": ParamsUtils.convert_to_ast(code_location),
    # People config
    "people_model_path": os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                      "../../../../../data-processing-lib/python/src/data_processing/multimodal/ray", "..", "models", "yolov8m-seg.pt"))
}
if __name__ == "__main__":
    # Set the simulated command line args
    sys.argv = ParamsUtils.dict_to_req(d=params)
    # create launcher
    launcher = RayTransformLauncher(PeopleRayTransformConfiguration())
    # Launch the ray actor(s) to process the input
    launcher.launch()
